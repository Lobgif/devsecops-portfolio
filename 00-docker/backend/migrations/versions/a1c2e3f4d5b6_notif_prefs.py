"""notif_prefs

Revision ID: a1c2e3f4d5b6
Revises: 35dbdcffe6bb
Create Date: 2026-06-05 07:30:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = 'a1c2e3f4d5b6'
down_revision = '35dbdcffe6bb'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'users',
        sa.Column('notif_prefs', postgresql.JSONB(astext_type=sa.Text()),
                  server_default='{}', nullable=False),
        schema='auth',
    )


def downgrade() -> None:
    op.drop_column('users', 'notif_prefs', schema='auth')
