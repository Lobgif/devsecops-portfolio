"""group is_private

Revision ID: b2d4f6a8c0e1
Revises: a1c2e3f4d5b6
Create Date: 2026-06-05 08:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = 'b2d4f6a8c0e1'
down_revision = 'a1c2e3f4d5b6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'groups',
        sa.Column('is_private', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        schema='forum',
    )


def downgrade() -> None:
    op.drop_column('groups', 'is_private', schema='forum')
