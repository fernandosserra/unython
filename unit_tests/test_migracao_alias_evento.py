from io import StringIO
import logging.config

from alembic import command
from alembic.config import Config

from src.utils.database_manager import DatabaseManager


def test_migracao_alias_evento_offline(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/unython")
    monkeypatch.setattr(logging.config, "fileConfig", lambda *args, **kwargs: None)
    output = StringIO()
    config = Config("alembic.ini", output_buffer=output)
    command.upgrade(config, "20261117_02:20261117_03", sql=True)
    assert "ADD COLUMN IF NOT EXISTS alias_evento VARCHAR(50) NOT NULL DEFAULT 'Evento'" in output.getvalue()

    output.seek(0)
    output.truncate()
    command.downgrade(config, "20261117_03:20261117_02", sql=True)
    assert "DROP COLUMN IF EXISTS alias_evento" in output.getvalue()


def test_bootstrap_cria_e_atualiza_alias_evento(monkeypatch):
    queries = []
    monkeypatch.setattr(DatabaseManager, "execute_query", lambda self, query, **kwargs: queries.append(query))
    DatabaseManager().create_tables()
    assert any("alias_evento VARCHAR(50) NOT NULL DEFAULT 'Evento'" in query
               for query in queries if "CREATE TABLE IF NOT EXISTS organizacao_config" in query)
    assert any("ADD COLUMN IF NOT EXISTS alias_evento VARCHAR(50) NOT NULL DEFAULT 'Evento'" in query
               for query in queries)
