"""gouvernance : suppression programmee d'un groupe (preavis super-admin)

Revision ID: b8d2e3f4a5b6
Revises: a7c1d2e3f4a5
Create Date: 2026-08-30
"""
import sqlalchemy as sa

from alembic import op

revision = "b8d2e3f4a5b6"
down_revision = "a7c1d2e3f4a5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("groups", sa.Column("deletion_at", sa.DateTime(timezone=True), nullable=True), schema="forum")
    op.add_column("groups", sa.Column("deletion_reason", sa.String(255), nullable=True), schema="forum")


def downgrade() -> None:
    op.drop_column("groups", "deletion_reason", schema="forum")
    op.drop_column("groups", "deletion_at", schema="forum")
