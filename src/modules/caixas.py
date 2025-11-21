# src/modules/caixa.py

from typing import Optional, List, Dict, Any
from src.utils.database_manager import DatabaseManager
from src.utils.models import Caixa, MovimentoCaixa
from datetime import datetime
from decimal import Decimal

class CaixaService:
    """Gerencia a abertura, fechamento e controle de Caixas e seus Movimentos."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    # -----------------------------------------------------------
    # 1. GESTÃO DE CAIXAS FÍSICOS (CRIAÇÃO/BUSCA)
    # -----------------------------------------------------------

    def registrar_caixa(self, caixa: Caixa) -> Optional[int]:
        """Registra um novo Caixa Físico (UPSERT Lógico pelo nome)."""
        caixa_existente = self.buscar_caixa_por_nome(caixa.nome)
        
        if caixa_existente:
            print(f" (Alerta Washu: Caixa '{caixa.nome}' já existe. Usando ID: {caixa_existente.id})")
            return caixa_existente.id
        
        query = "INSERT INTO caixas (nome, descricao, status) VALUES (%s, %s, %s) RETURNING id"
        params = (caixa.nome, caixa.descricao, caixa.status)
        return self.db.execute_query(query, params, commit=True)
        
    def buscar_caixa_por_nome(self, nome: str) -> Optional[Caixa]:
        """Busca um Caixa Físico pelo nome."""
        query = "SELECT id, nome, descricao, status FROM caixas WHERE nome = %s"
        columns, data = self.db.execute_query(query, (nome,), fetch_one=True)
        if data:
            return Caixa(**dict(zip(columns, data)))
        return None

    # -----------------------------------------------------------
    # 2. GESTÃO DE MOVIMENTO DE CAIXA (Abertura/Fechamento)
    # -----------------------------------------------------------

    def abrir_movimento(self, id_caixa: int, id_usuario_abertura: int, valor_abertura: Decimal) -> Optional[int]:
        """
        Abre uma nova sessão de Movimento de Caixa para um Caixa específico.
        Só permite abertura se não houver outro movimento ABERTO para o mesmo Caixa.
        """
        movimento_ativo = self.buscar_movimento_ativo(id_caixa)
        if movimento_ativo:
            print(f" (Alerta Washu: Movimento ID {movimento_ativo.id} já está ATIVO para o Caixa {id_caixa})")
            return movimento_ativo.id

        query = """
        INSERT INTO movimentos_caixa 
            (id_caixa, id_usuario_abertura, valor_abertura, status) 
        VALUES 
            (%s, %s, %s, 'Aberto') 
        RETURNING id
        """
        params = (id_caixa, id_usuario_abertura, valor_abertura)
        return self.db.execute_query(query, params, commit=True)

    def fechar_movimento(self, id_movimento: int) -> bool:
        """Fecha um Movimento de Caixa existente."""
        query = "UPDATE movimentos_caixa SET status = 'Fechado', data_fechamento = %s WHERE id = %s AND status = 'Aberto'"
        params = (datetime.now(), id_movimento)
        # Retorna True se 1 linha foi afetada, False caso contrário
        return self.db.execute_query(query, params, commit=True, return_rowcount=True) == 1

    def buscar_movimento_ativo(self, id_caixa: int) -> Optional[MovimentoCaixa]:
        """Busca o movimento ATIVO para um Caixa específico."""
        query = """
        SELECT id, id_caixa, id_usuario_abertura, valor_abertura, status, data_abertura, data_fechamento 
        FROM movimentos_caixa 
        WHERE id_caixa = %s AND status = 'Aberto' 
        ORDER BY data_abertura DESC 
        LIMIT 1
        """
        columns, data = self.db.execute_query(query, (id_caixa,), fetch_one=True)
        if data:
            return MovimentoCaixa(**dict(zip(columns, data)))
        return None