# src/modules/estoque.py (Versão Corrigida)

from src.utils.models import MovimentoEstoque
from typing import List, Optional
from src.utils.database_manager import DatabaseManager


class EstoqueService:    
    # --- MÉTODOS AUXILIARES DE BUSCA (Ajustados para retornar Modelos) ---
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def _transmutar_movimento(self, columns, results) -> List[MovimentoEstoque]:
        """Transmuta tuplas SQL em objetos MovimentoEstoque."""
        if not results:
            return []
        return [MovimentoEstoque(**dict(zip(columns, row))) for row in results]
    
    def buscar_movimentos(self) -> List[MovimentoEstoque]:
        """Busca todos os movimentos de estoque."""
        query = "SELECT * FROM estoque"
        columns, results = self.db.execute_query(query, fetch_all=True)
        return self._transmutar_movimento(columns, results)
    
    def buscar_movimentos_por_item(self, id_item: int) -> List[MovimentoEstoque]:
        """Busca movimentos de estoque por ID de item."""
        query = "SELECT * FROM estoque WHERE id_item = ?"
        columns, results = self.db.execute_query(query, (id_item,), fetch_all=True)
        return self._transmutar_movimento(columns, results)

    # --- MÉTODO PRINCIPAL ---
    
    def registrar_movimento(self, movimento: MovimentoEstoque) -> Optional[int]:
        """Registra um movimento de estoque (Entrada ou Saída)."""
        query = """
        INSERT INTO estoque 
        (id_item, quantidade, tipo_movimento, origem_recurso, id_usuario, id_evento, data_movimento) 
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            movimento.id_item, 
            movimento.quantidade, 
            movimento.tipo_movimento, 
            movimento.origem_recurso, 
            movimento.id_usuario, 
            movimento.id_evento,
            movimento.data_movimento # Adicionado para garantir a persistência
        )
        return self.db.execute_query(query, params, commit=True)
        
    # --- HELPERS (Funções de Alto Nível) ---
    
    def entrada_item(self, id_item: int, quantidade: int, origem_recurso: str, id_usuario: int, id_evento: int) -> Optional[int]:
        """Função simplificada para registrar uma entrada de estoque."""
        movimento = MovimentoEstoque(
            id_item=id_item, 
            quantidade=quantidade, 
            tipo_movimento='Entrada', 
            origem_recurso=origem_recurso,
            id_usuario=id_usuario,
            id_evento=id_evento
        )
        return self.registrar_movimento(movimento)

    def saida_item(self, id_item: int, quantidade: int, id_usuario: int, id_evento: int) -> Optional[int]:
        """Função simplificada para registrar uma saída de estoque (Ex: Consumo Interno)."""
        movimento = MovimentoEstoque(
            id_item=id_item, 
            quantidade=quantidade, 
            tipo_movimento='Saída', 
            origem_recurso='Consumo Interno', # Saídas que não são vendas
            id_usuario=id_usuario,
            id_evento=id_evento
        )
        return self.registrar_movimento(movimento)
    
    def calcular_saldo_item(self, id_item: int) -> int:
        """
        Calcula o saldo atual de um item (Soma das Entradas - Soma das Saídas).
        """
        query = """
        SELECT
            SUM(CASE WHEN tipo_movimento = 'Entrada' THEN quantidade ELSE -quantidade END)
        FROM 
            estoque
        WHERE 
            id_item = ?;
        """
        
        try:
            _, result = self.db.execute_query(query, (id_item,), fetch_one=True)
            
            # O resultado é uma tupla (saldo,). Retorna 0 se for None.
            saldo = result[0] if result and result[0] is not None else 0
            return int(saldo)
        except Exception as e:
            print(f" (Alerta Washu Saldo): Falha ao calcular saldo: {e}")
            return 0