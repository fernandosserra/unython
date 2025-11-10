# src/modules/categoria.py

from typing import Optional, List
from src.utils.database_manager import DatabaseManager
from src.utils.models import Categoria # Importa o dataclass Categoria

class CategoriaService:
    """
    Gerencia a lógica de negócio para a entidade Categoria (Catálogo de Produtos).
    """
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    # -----------------------------------------------------------
    # 1. CORE LOGIC (UPSERT)
    # -----------------------------------------------------------
        
    def registrar_categoria(self, categoria: Categoria) -> Optional[int]:
        """Registra uma nova categoria ou atualiza se já existir pelo nome (UPSERT Lógico)."""
        
        categoria_existente = self.buscar_categoria_por_nome(categoria.nome)
        
        if categoria_existente:
            # Se existir, atualiza a descrição e o status.
            self.editar_categoria(
                categoria_existente.id, 
                categoria.nome, 
                categoria.descricao, 
                categoria.status
            )
            print(f" (Alerta Washu: Categoria '{categoria.nome}' atualizada. Usando ID: {categoria_existente.id})")
            return categoria_existente.id
        
        # Se não existe, insere
        query = "INSERT INTO categorias (nome, descricao, status) VALUES (%s, %s, %s) RETURNING id"
        params = (categoria.nome, categoria.descricao, categoria.status)
        return self.db.execute_query(query, params, commit=True)
    
    def editar_categoria(self, id_categoria: int, nome: str, descricao: Optional[str], status: str) -> bool:
        """Atualiza os dados de uma categoria existente."""
        query = "UPDATE categorias SET nome = %s, descricao = %s, status = %s WHERE id = %s"
        params = (nome, descricao, status, id_categoria)
        return self.db.execute_query(query, params, commit=True)

    # -----------------------------------------------------------
    # 2. BUSCA E CONSULTA
    # -----------------------------------------------------------
    
    def buscar_categoria_por_nome(self, nome: str) -> Optional[Categoria]:
        """Busca uma categoria pelo nome (para lógica UPSERT)."""
        query = "SELECT id, nome, descricao, status FROM categorias WHERE nome = %s"
        columns, data = self.db.execute_query(query, (nome,), fetch_one=True)
        if data:
            return Categoria(**dict(zip(columns, data)))
        return None
    
    def buscar_todas_categorias(self) -> List[Categoria]:
        """Lista todas as categorias ativas."""
        query = "SELECT id, nome, descricao, status FROM categorias WHERE status = 'Ativo' ORDER BY nome"
        columns, results = self.db.execute_query(query, fetch_all=True)
        if results:
            return [Categoria(**dict(zip(columns, row))) for row in results]
        return []

    # -----------------------------------------------------------
    # 3. LÓGICA DE SEGURANÇA E FLUXO
    # -----------------------------------------------------------

    def deletar_categoria(self, id_categoria: int) -> bool:
        """
        Deleta uma categoria APENAS se não houver itens vinculados (FK Check).
        """
        # CRÍTICO: Checa a integridade na tabela 'itens'.
        check_query = "SELECT COUNT(id) FROM itens WHERE id_categoria = %s"
        _, (count,) = self.db.execute_query(check_query, (id_categoria,), fetch_one=True)
        
        if count > 0:
            print(f" (Alerta Washu: Categoria ID {id_categoria} não pode ser deletada. {count} item(s) vinculado(s).")
            return False
            
        # Se não houver vínculo, deleta.
        query = "DELETE FROM categorias WHERE id = %s"
        return self.db.execute_query(query, (id_categoria,), commit=True)
        
    def inativar_categoria(self, id_categoria: int) -> bool:
        """Inativa uma categoria, mantendo a integridade histórica."""
        query = "UPDATE categorias SET status = 'Inativo' WHERE id = %s"
        return self.db.execute_query(query, (id_categoria,), commit=True)