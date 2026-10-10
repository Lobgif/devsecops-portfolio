"""fraicheur : date d'indexation des chunks (recul sur l'age des reponses communautaires)

Revision ID: f6b2c3d4e5f6
Revises: e5a1b2c3d4e5
Create Date: 2026-08-30
"""
import sqlalchemy as sa

from alembic import op

revision = "f6b2c3d4e5f6"
down_revision = "e5a1b2c3d4e5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "chunks",
        sa.Column("indexed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        schema="rag",
    )


def downgrade() -> None:
    op.drop_column("chunks", "indexed_at", schema="rag")
