"""ingest_jobs

Revision ID: c3e5f7a9b1d2
Revises: b2d4f6a8c0e1
Create Date: 2026-06-06 09:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = 'c3e5f7a9b1d2'
down_revision = 'b2d4f6a8c0e1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'ingest_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('kind', sa.String(length=20), nullable=False),
        sa.Column('source', sa.Text(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('source_type', sa.String(length=50), server_default='loi', nullable=False),
        sa.Column('crawl_filter', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=20), server_default='pending', nullable=False),
        sa.Column('total', sa.Integer(), server_default='0', nullable=False),
        sa.Column('done', sa.Integer(), server_default='0', nullable=False),
        sa.Column('chunks', sa.Integer(), server_default='0', nullable=False),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        schema='rag',
    )


def downgrade() -> None:
    op.drop_table('ingest_jobs', schema='rag')
