# src/modules/pessoa.py

from src.utils.database_manager import DatabaseManager
from src.utils.models import Pessoa 
from datetime import datetime
from typing import Optional

class PessoaService:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def registrar_pessoa(self, pessoa: Pessoa):
        """Registra uma nova pessoa/consulente no banco de dados."""
        # Garante que data_cadastro seja preenchido se o modelo for usado fora do dataclass padrão
        data_cadastro = pessoa.data_cadastro or datetime.now().strftime("%Y-%m-%d")
        
        query = "INSERT INTO pessoas (nome, telefone, data_cadastro) VALUES (?, ?, ?) RETURNING id"
        params = (pessoa.nome, pessoa.telefone, data_cadastro)
        return self.db.execute_query(query, params, commit=True) 
    
    def buscar_pessoas(self, nome: Optional[str] = None):
        """Busca pessoas (opcionalmente por nome) e as retorna como objetos Pessoa."""
        query = "SELECT id, nome, telefone, data_cadastro FROM pessoas"
        params = None
        
        if nome:
            # Adicionando um toque de inteligência: busca parcial com LIKE
            query += " WHERE nome LIKE ?" 
            params = (f'%{nome}%',)

        columns, results = self.db.execute_query(query, params, fetch_all=True)
        
        # A Transmutação de Dados para objetos Pessoa
        if results:
            return [Pessoa(**dict(zip(columns, row))) for row in results]
        return []

    def editar_pessoa(self, pessoa_id: int, nome: str, telefone: Optional[str]):
        # ...
        query = "UPDATE pessoas SET nome = ?, telefone = ? WHERE id = ?"
        params = (nome, telefone, pessoa_id)
        return self.db.execute_query(query, params, commit=True)

    def deletar_pessoa(self, pessoa_id: int):
        # ...
        query = "DELETE FROM pessoas WHERE id = ?"
        params = (pessoa_id,)
        return self.db.execute_query(query, params, commit=True)