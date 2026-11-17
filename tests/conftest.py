import os
import sys
from pathlib import Path

import pytest

# Garante que o diretório raiz esteja no PYTHONPATH para os imports "src.*"
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.utils.database_manager import DatabaseManager  # noqa: E402
from src.utils.database_urls import parse_test_database_url  # noqa: E402

_TEST_DB_CONFIG = None


def pytest_sessionstart(session):
    global _TEST_DB_CONFIG
    try:
        _TEST_DB_CONFIG = parse_test_database_url(os.getenv("TEST_DATABASE_URL"))
    except ValueError as exc:
        pytest.exit(str(exc), returncode=4)


@pytest.fixture(scope="session")
def db_manager():
    """
    Abre conexão com o banco de testes previamente migrado.
    """
    db = DatabaseManager(db_config=_TEST_DB_CONFIG, create_database=False)
    db.connect()
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
            atividades_atendimento,
            facilitadores,
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
            atividades_atendimento,
            facilitadores,
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
