from typing import List, Optional
from src.utils.database_manager import DatabaseManager
from src.utils.models import Item

class ItemService:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def registrar_item(self, item: Item) -> Optional[int]:
        """Registra um novo item e retorna o ID (O Protocolo de Inserção Genial)."""
        query = "INSERT INTO itens (nome, valor_compra, valor_venda, status) VALUES (?, ?, ?, ?)"
        values = (item.nome, item.valor_compra, item.valor_venda, item.status)
        # Retorna o lastrowid!
        return self.db.execute_query(query, values, commit=True)
    
    def buscar_item_por_nome(self, nome: str) -> Item:
        query = "SELECT id, nome, valor_compra, valor_venda FROM itens WHERE nome = ?"
        values = (nome,)
        columns, data = self.db.execute_query(query, values, fetch_one=True)
        if data:
            return Item(**dict(zip(columns, data)))
        return None
    
    def buscar_todos_itens(self) -> List[Item]:
        """Busca todos os itens e os converte em objetos Item."""
        query = "SELECT id, nome, valor_compra, valor_venda, status FROM itens"
        columns, results = self.db.execute_query(query, fetch_all=True)
        if results:
            return [Item(**dict(zip(columns, row))) for row in results]
        return []
    
    def editar_item(self, item_id: int, nome: str, valor_compra: float, valor_venda: float):
        query = "UPDATE itens SET nome = ?, valor_compra = ?, valor_venda = ? WHERE id = ?"
        values = (nome, valor_compra, valor_venda, item_id)
        self.db.execute_query(query, values)
        return True
    
    def deletar_item(self, item_id: int) -> bool:
        """
        Deleta um item APENAS se não houver vendas vinculadas.
        Isto é o Protocolo de Segurança Quântica da Washu.
        """
        # 1. Consulta de Bloqueio (Checar o Caos): 
        # Existe alguma entrada em ItemVenda com este ID?
        check_query = "SELECT COUNT(id) FROM itens_venda WHERE id_item = ?"
        _, (count,) = self.db.execute_query(check_query, (item_id,), fetch_one=True)
        
        if count > 0:
            # Não é possível deletar, a história é imutável!
            print(f" (Alerta Washu: Item ID {item_id} não pode ser deletado. {count} venda(s) vinculada(s).")
            return False
            
        # 2. Execução Segura (Se não houver vínculo, está livre para ir):
        query = "DELETE FROM itens WHERE id = ?"
        self.db.execute_query(query, (item_id,), commit=True)
        return True
    
    def inativar_item(self, item_id: int) -> bool:
        """Inativa um item, mantendo a história da venda intacta."""
        query = "UPDATE itens SET status = 'Inativo' WHERE id = ?"
        return self.db.execute_query(query, (item_id,), commit=True)