"""Add configurable event terminology.

Revision ID: 20261117_03
Revises: 20261117_02
"""
from alembic import op


revision = "20261117_03"
down_revision = "20261117_02"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "ALTER TABLE organizacao_config ADD COLUMN IF NOT EXISTS "
        "alias_evento VARCHAR(50) NOT NULL DEFAULT 'Evento'"
    )


def downgrade():
    op.execute("ALTER TABLE organizacao_config DROP COLUMN IF EXISTS alias_evento")
