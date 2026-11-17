"""Ensure at most one operational event is open.

Revision ID: 20261117_06
Revises: 20261117_05
"""
from alembic import op

revision = "20261117_06"
down_revision = "20261117_05"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE UNIQUE INDEX ux_eventos_unico_aberto ON eventos ((status)) WHERE status = 'Aberto'")


def downgrade():
    op.execute("DROP INDEX ux_eventos_unico_aberto")
