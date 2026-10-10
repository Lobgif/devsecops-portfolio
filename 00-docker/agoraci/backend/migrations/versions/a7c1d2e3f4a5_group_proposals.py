"""gouvernance : propositions de groupe + soutiens (creation par la demande)

Revision ID: a7c1d2e3f4a5
Revises: f6b2c3d4e5f6
Create Date: 2026-08-30

Un membre propose un groupe ; les autres le soutiennent ; au seuil de soutiens,
le groupe est cree automatiquement (proposeur = fondateur, soutiens = membres).
"""
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

revision = "a7c1d2e3f4a5"
down_revision = "f6b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "group_proposals",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("category", sa.String(60), nullable=False),
        sa.Column("description", sa.Text(), server_default="", nullable=False),
        sa.Column("motivation", sa.Text(), server_default="", nullable=False),
        sa.Column("proposed_by", UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(20), server_default="open", nullable=False),  # open|created|rejected
        sa.Column("support_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_group_id", UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        schema="forum",
    )
    op.create_table(
        "group_proposal_supports",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("proposal_id", UUID(as_uuid=True),
                  sa.ForeignKey("forum.group_proposals.id", ondelete="CASCADE"), index=True, nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("proposal_id", "user_id", name="uq_proposal_support"),
        schema="forum",
    )


def downgrade() -> None:
    op.drop_table("group_proposal_supports", schema="forum")
    op.drop_table("group_proposals", schema="forum")
