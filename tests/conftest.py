import sys
from pathlib import Path

import pytest

# Garante que o diretório raiz esteja no PYTHONPATH para os imports "src.*"
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.utils.database_manager import DatabaseManager  # noqa: E402


@pytest.fixture(scope="session")
def db_manager():
    """
    Abre conexão e garante que as tabelas existam.
    Útil apenas em ambiente de desenvolvimento, onde o DB é descartável.
    """
    db = DatabaseManager()
    db.connect()
    db.create_tables()
    yield db
    db.disconnect()


@pytest.fixture(autouse=True)
def cleanup_db(db_manager):
    """
    Isola cada teste limpando as tabelas antes e depois.
    Usa TRUNCATE ... CASCADE para respeitar FKs e RESTART IDENTITY para resetar IDs.
    """
    cursor = db_manager.conn.cursor()
    cursor.execute(
        """
        TRUNCATE TABLE
            itens_venda,
            vendas,
            estoque,
            movimentos_financeiros,
            agendamentos,
            eventos,
            pessoas,
            usuarios,
            itens,
            categorias,
            movimentos_caixa,
            caixas
        RESTART IDENTITY CASCADE;
        """
    )
    db_manager.conn.commit()
    yield
    cursor.execute(
        """
        TRUNCATE TABLE
            itens_venda,
            vendas,
            estoque,
            movimentos_financeiros,
            agendamentos,
            eventos,
            pessoas,
            usuarios,
            itens,
            categorias,
            movimentos_caixa,
            caixas
        RESTART IDENTITY CASCADE;
        """
    )
    db_manager.conn.commit()
