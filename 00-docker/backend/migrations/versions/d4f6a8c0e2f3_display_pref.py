"""user display_pref

Revision ID: d4f6a8c0e2f3
Revises: c3e5f7a9b1d2
Create Date: 2026-06-06 10:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = 'd4f6a8c0e2f3'
down_revision = 'c3e5f7a9b1d2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'users',
        sa.Column('display_pref', sa.String(length=20), server_default='username', nullable=False),
        schema='auth',
    )


def downgrade() -> None:
    op.drop_column('users', 'display_pref', schema='auth')
