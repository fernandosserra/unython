"""Add organization configuration and document policy.

Revision ID: 20261117_04_org
Revises: 20261117_03
"""
from alembic import op


revision = "20261117_04_org"
down_revision = "20261117_03"
branch_labels = None
depends_on = None


def upgrade():
    for column in (
        "subtitulo TEXT",
        "registro TEXT",
        "cidade_uf TEXT",
        "telefone_contato TEXT",
        "termo_atendente_plural VARCHAR(50) NOT NULL DEFAULT 'Médiuns / Cambones'",
        "termo_atividade_plural VARCHAR(50) NOT NULL DEFAULT 'Entidades / Serviços'",
        "alias_evento_plural VARCHAR(50) NOT NULL DEFAULT 'Eventos'",
        "habilitar_pdv BOOLEAN NOT NULL DEFAULT TRUE",
        "habilitar_atendimentos BOOLEAN NOT NULL DEFAULT TRUE",
        "habilitar_doacoes BOOLEAN NOT NULL DEFAULT TRUE",
        "exigir_documento_atendimento BOOLEAN NOT NULL DEFAULT FALSE",
    ):
        op.execute(f"ALTER TABLE organizacao_config ADD COLUMN IF NOT EXISTS {column}")


def downgrade():
    for column in (
        "subtitulo", "registro", "cidade_uf", "telefone_contato",
        "termo_atendente_plural", "termo_atividade_plural", "alias_evento_plural",
        "habilitar_pdv", "habilitar_atendimentos", "habilitar_doacoes",
        "exigir_documento_atendimento",
    ):
        op.execute(f"ALTER TABLE organizacao_config DROP COLUMN IF EXISTS {column}")
