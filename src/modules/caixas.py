# src/modules/caixas.py
from typing import List, Optional
from decimal import Decimal

from src.utils.database_manager import DatabaseManager
from src.utils.models import Caixa, MovimentoCaixa


class CaixaService:
    """Gerencia abertura, fechamento e controle de Caixas e Movimentos."""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    # -----------------------------------------------------------
    # 1. Gestão de Caixas físicos (CRUD)
    # -----------------------------------------------------------

    def registrar_caixa(self, caixa: Caixa) -> Optional[int]:
        """Registra um novo Caixa físico (UPSERT lógico pelo nome)."""
        caixa_existente = self.buscar_caixa_por_nome(caixa.nome)
        if caixa_existente:
            print(f"(Alerta: Caixa '{caixa.nome}' já existe. Usando ID: {caixa_existente.id})")
            return caixa_existente.id

        query = "INSERT INTO caixas (nome, descricao, status) VALUES (%s, %s, %s) RETURNING id"
        params = (caixa.nome, caixa.descricao, caixa.status)
        return self.db.execute_query(query, params, commit=True)

    def buscar_caixa_por_nome(self, nome: str) -> Optional[Caixa]:
        """Busca um Caixa físico pelo nome."""
        query = "SELECT id, nome, descricao, status FROM caixas WHERE nome = %s"
        columns, data = self.db.execute_query(query, (nome,), fetch_one=True)
        if data:
            return Caixa(**dict(zip(columns, data)))
        return None

    def buscar_todos_caixas(self) -> List[Caixa]:
        """Lista todos os Caixas físicos ativos (útil para a UI/API)."""
        query = "SELECT id, nome, descricao, status FROM caixas WHERE status = 'Ativo' ORDER BY nome"
        columns, results = self.db.execute_query(query, fetch_all=True)
        if results:
            return [Caixa(**dict(zip(columns, row))) for row in results]
        return []

    # -----------------------------------------------------------
    # 2. Gestão de Movimento de Caixa (Abertura/Fechamento)
    # -----------------------------------------------------------

    def abrir_movimento(self, id_caixa: int, id_usuario_abertura: int, valor_abertura: Decimal) -> Optional[int]:
        """
        Abre uma nova sessão de Movimento de Caixa.
        Só permite abertura se não houver outro movimento ABERTO para o mesmo Caixa.
        """
        movimento_ativo = self.buscar_movimento_ativo(id_caixa)
        if movimento_ativo:
            print(f"(Alerta: Movimento ID {movimento_ativo.id} já está ATIVO para o Caixa {id_caixa})")
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
        """
        Fecha um Movimento de Caixa existente.
        Retorna True se a operação foi bem-sucedida (1 linha afetada).
        """
        query = "UPDATE movimentos_caixa SET status = 'Fechado', data_fechamento = NOW() WHERE id = %s AND status = 'Aberto'"
        params = (id_movimento,)
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
