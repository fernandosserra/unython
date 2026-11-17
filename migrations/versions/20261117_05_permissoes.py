"""Add per-user module permissions.

Revision ID: 20261117_05
Revises: 20261117_04_org
"""
from alembic import op


revision = "20261117_05"
down_revision = "20261117_04_org"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "ALTER TABLE usuarios ADD COLUMN permissoes JSONB "
        "CHECK (permissoes IS NULL OR jsonb_typeof(permissoes) = 'array')"
    )


def downgrade():
    op.execute("ALTER TABLE usuarios DROP COLUMN permissoes")
