"""user_suspension

Revision ID: 35dbdcffe6bb
Revises: 1a4e153c413f
Create Date: 2026-06-05 06:40:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = '35dbdcffe6bb'
down_revision = '1a4e153c413f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'users',
        sa.Column('suspended_until', sa.DateTime(timezone=True), nullable=True),
        schema='auth',
    )
    op.add_column(
        'users',
        sa.Column('suspended_reason', sa.String(length=255), nullable=True),
        schema='auth',
    )


def downgrade() -> None:
    op.drop_column('users', 'suspended_reason', schema='auth')
    op.drop_column('users', 'suspended_until', schema='auth')
