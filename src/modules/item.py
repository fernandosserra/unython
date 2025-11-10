# src/modules/item.py

from typing import List, Optional
from src.utils.database_manager import DatabaseManager
from src.utils.models import Item # Assumindo que Item agora tem 'id_categoria'

class ItemService:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    # -----------------------------------------------------------
    # 1. CRUD E CORE LOGIC
    # -----------------------------------------------------------
    
    def registrar_item(self, item: Item) -> Optional[int]:
        """Registra um item ou retorna o ID se o nome já existir (UPSERT LÓGICO)."""
        item_existente = self.buscar_item_por_nome(item.nome)
        
        if item_existente:
            # Item já existe, atualiza os valores e retorna o ID existente.
            self.editar_item(
                item_existente.id, 
                item.nome, 
                item.valor_compra, 
                item.valor_venda, 
                item.status, 
                item.id_categoria
            ) 
            print(f" (Alerta Washu: Item '{item.nome}' atualizado e usando ID: {item_existente.id})")
            return item_existente.id
        
        # Se não existe, insere um novo (Incluindo id_categoria)
        query = "INSERT INTO itens (nome, valor_compra, valor_venda, status, id_categoria) VALUES (%s, %s, %s, %s, %s) RETURNING id"
        values = (item.nome, item.valor_compra, item.valor_venda, item.status, item.id_categoria)
        return self.db.execute_query(query, values, commit=True)
    
    def editar_item(self, item_id: int, nome: str, valor_compra: float, valor_venda: float, status: str, id_categoria: Optional[int]):
        """Atualiza os dados de um item existente, incluindo o status e a categoria."""
        # A query UPDATE deve ser completa para garantir a consistência de dados.
        query = """
        UPDATE itens SET 
            nome = %s, 
            valor_compra = %s, 
            valor_venda = %s, 
            status = %s, 
            id_categoria = %s 
        WHERE id = %s
        """
        values = (nome, valor_compra, valor_venda, status, id_categoria, item_id)
        # Usamos commit=True aqui para a operação atômica de atualização.
        return self.db.execute_query(query, values, commit=True)
    
    # -----------------------------------------------------------
    # 2. BUSCA E CONSULTA (Queries atualizadas para incluir id_categoria)
    # -----------------------------------------------------------

    def buscar_item_por_nome(self, nome: str) -> Optional[Item]:
        """Busca um item pelo nome e retorna o objeto Item."""
        query = "SELECT id, nome, valor_compra, valor_venda, status, id_categoria FROM itens WHERE nome = %s"
        columns, data = self.db.execute_query(query, (nome,), fetch_one=True)
        if data:
            return Item(**dict(zip(columns, data)))
        return None
    
    def buscar_item_por_id(self, item_id: int) -> Optional[Item]:
        """Busca um item pelo ID e retorna o objeto Item."""
        query = "SELECT id, nome, valor_compra, valor_venda, status, id_categoria FROM itens WHERE id = %s"
        columns, data = self.db.execute_query(query, (item_id,), fetch_one=True)
        if data:
            return Item(**dict(zip(columns, data)))
        return None
    
    def buscar_todos_itens(self) -> List[Item]:
        """Busca todos os itens e os converte em objetos Item."""
        query = "SELECT id, nome, valor_compra, valor_venda, status, id_categoria FROM itens"
        columns, results = self.db.execute_query(query, fetch_all=True)
        if results:
            return [Item(**dict(zip(columns, row))) for row in results]
        return []
    
    # -----------------------------------------------------------
    # 3. LÓGICA DE SEGURANÇA E FLUXO
    # -----------------------------------------------------------
    
    def deletar_item(self, item_id: int) -> bool:
        """
        Deleta um item APENAS se não houver vendas vinculadas.
        Protocolo de Segurança Quântica (Foreign Key Check).
        """
        # 1. Consulta de Bloqueio (Checar o Caos): 
        check_query = "SELECT COUNT(id) FROM itens_venda WHERE id_item = %s"
        _, (count,) = self.db.execute_query(check_query, (item_id,), fetch_one=True)
        
        if count > 0:
            print(f" (Alerta Washu: Item ID {item_id} não pode ser deletado. {count} venda(s) vinculada(s).")
            return False
            
        # 2. Execução Segura (Se não houver vínculo, está livre para ir):
        query = "DELETE FROM itens WHERE id = %s"
        self.db.execute_query(query, (item_id,), commit=True)
        return True
    
    def inativar_item(self, item_id: int) -> bool:
        """Inativa um item, mantendo a história da venda intacta."""
        query = "UPDATE itens SET status = 'Inativo' WHERE id = %s"
        return self.db.execute_query(query, (item_id,), commit=True)