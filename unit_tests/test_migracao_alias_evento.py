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


def test_migracao_limita_eventos_abertos(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/unython")
    monkeypatch.setattr(logging.config, "fileConfig", lambda *args, **kwargs: None)
    output = StringIO()
    config = Config("alembic.ini", output_buffer=output)
    command.upgrade(config, "20261117_05:20261117_06", sql=True)
    assert "CREATE UNIQUE INDEX ux_eventos_unico_aberto ON eventos ((status)) WHERE status = 'Aberto'" in output.getvalue()


def test_bootstrap_cria_e_atualiza_alias_evento(monkeypatch):
    queries = []
    monkeypatch.setattr(DatabaseManager, "execute_query", lambda self, query, **kwargs: queries.append(query))
    DatabaseManager().create_tables()
    assert any("alias_evento VARCHAR(50) NOT NULL DEFAULT 'Evento'" in query
               for query in queries if "CREATE TABLE IF NOT EXISTS organizacao_config" in query)
    assert any("ADD COLUMN IF NOT EXISTS alias_evento VARCHAR(50) NOT NULL DEFAULT 'Evento'" in query
               for query in queries)


def test_migracao_config_organizacao_offline(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/unython")
    monkeypatch.setattr(logging.config, "fileConfig", lambda *args, **kwargs: None)
    output = StringIO()
    config = Config("alembic.ini", output_buffer=output)
    command.upgrade(config, "20261117_03:20261117_04_org", sql=True)
    sql = output.getvalue()
    assert "ADD COLUMN IF NOT EXISTS exigir_documento_atendimento BOOLEAN NOT NULL DEFAULT FALSE" in sql
    assert "ADD COLUMN IF NOT EXISTS habilitar_pdv BOOLEAN NOT NULL DEFAULT TRUE" in sql
    output.seek(0)
    output.truncate()
    command.downgrade(config, "20261117_04_org:20261117_03", sql=True)
    assert "DROP COLUMN IF EXISTS exigir_documento_atendimento" in output.getvalue()


def test_bootstrap_config_organizacao(monkeypatch):
    queries = []
    monkeypatch.setattr(DatabaseManager, "execute_query", lambda self, query, **kwargs: queries.append(query))
    DatabaseManager().create_tables()
    assert any("exigir_documento_atendimento BOOLEAN NOT NULL DEFAULT FALSE" in query
               for query in queries if "CREATE TABLE IF NOT EXISTS organizacao_config" in query)
    assert any("ADD COLUMN IF NOT EXISTS exigir_documento_atendimento BOOLEAN NOT NULL DEFAULT FALSE" in query
               for query in queries)
