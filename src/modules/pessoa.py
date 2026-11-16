# src/modules/pessoa.py

from src.utils.database_manager import DatabaseManager
from src.utils.models import Pessoa
from datetime import datetime
from typing import Optional, List


class PessoaService:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def registrar_pessoa(self, pessoa: Pessoa) -> Optional[int]:
        """Registra uma nova pessoa/assistido no banco de dados."""
        data_cadastro = pessoa.data_cadastro or datetime.now().strftime("%Y-%m-%d")

        query = """
            INSERT INTO pessoas (nome, telefone, documento, preferencial, observacoes, data_cadastro)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """
        params = (
            pessoa.nome,
            pessoa.telefone,
            pessoa.documento,
            bool(pessoa.preferencial),
            pessoa.observacoes,
            data_cadastro,
        )
        return self.db.execute_query(query, params, commit=True)

    def buscar_pessoas(self, termo: Optional[str] = None) -> List[Pessoa]:
        """Busca pessoas por nome, telefone ou documento."""
        query = """
            SELECT id, nome, telefone, documento, preferencial, observacoes, data_cadastro
            FROM pessoas
        """
        params = None

        if termo:
            query += " WHERE nome ILIKE %s OR telefone ILIKE %s OR documento ILIKE %s"
            like_term = f"%{termo}%"
            params = (like_term, like_term, like_term)

        query += " ORDER BY nome ASC"

        columns, results = self.db.execute_query(query, params, fetch_all=True)
        if results:
            return [Pessoa(**dict(zip(columns, row))) for row in results]
        return []

    def buscar_por_id(self, pessoa_id: int) -> Optional[Pessoa]:
        """Busca pessoa por id específico."""
        query = """
            SELECT id, nome, telefone, documento, preferencial, observacoes, data_cadastro
            FROM pessoas
            WHERE id = %s
        """
        columns, results = self.db.execute_query(query, (pessoa_id,), fetch_one=True)
        if results:
            return Pessoa(**dict(zip(columns, results)))
        return None

    def editar_pessoa(
        self,
        pessoa_id: int,
        nome: str,
        telefone: Optional[str] = None,
        documento: Optional[str] = None,
        preferencial: bool = False,
        observacoes: Optional[str] = None,
    ) -> bool:
        query = """
            UPDATE pessoas
            SET nome = %s, telefone = %s, documento = %s, preferencial = %s, observacoes = %s
            WHERE id = %s
        """
        params = (nome, telefone, documento, preferencial, observacoes, pessoa_id)
        return bool(self.db.execute_query(query, params, commit=True))

    def deletar_pessoa(self, pessoa_id: int) -> bool:
        query = "DELETE FROM pessoas WHERE id = %s"
        return bool(self.db.execute_query(query, (pessoa_id,), commit=True))
