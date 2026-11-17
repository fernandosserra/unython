"""Add operational audit trail.

Revision ID: 20261117_02
Revises: 20261117_01
"""
from alembic import op


revision = "20261117_02"
down_revision = "20261117_01"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE TABLE audit_logs (
            id BIGSERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES usuarios(id),
            acao VARCHAR(100) NOT NULL,
            entidade VARCHAR(100) NOT NULL,
            entidade_id INTEGER NOT NULL,
            detalhes JSONB NOT NULL DEFAULT '{}'::jsonb,
            request_id VARCHAR(128) NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)
    op.execute("CREATE INDEX ix_audit_logs_created_at ON audit_logs (created_at)")
    op.execute("CREATE INDEX ix_audit_logs_entidade ON audit_logs (entidade, entidade_id)")


def downgrade():
    op.execute("DROP TABLE audit_logs")
