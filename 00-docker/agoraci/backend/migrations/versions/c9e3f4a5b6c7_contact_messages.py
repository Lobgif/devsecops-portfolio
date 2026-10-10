"""contact messages

Revision ID: c9e3f4a5b6c7
Revises: b8d2e3f4a5b6
Create Date: 2026-08-30
"""
from alembic import op
import sqlalchemy as sa

revision = "c9e3f4a5b6c7"
down_revision = "b8d2e3f4a5b6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "contact_messages",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=120), server_default="", nullable=False),
        sa.Column("email", sa.String(length=255), server_default="", nullable=False),
        sa.Column("subject", sa.String(length=200), server_default="", nullable=False),
        sa.Column("message", sa.Text(), server_default="", nullable=False),
        sa.Column("status", sa.String(length=20), server_default="new", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("contact_messages")
