"""profil expert : profession + candidature validee par l'admin

Revision ID: e5a1b2c3d4e5
Revises: d4f6a8c0e2f3
Create Date: 2026-08-30

- profession : renseignee par TOUS a l'inscription (texte libre)
- expert_status : none | pending | approved | rejected (validation admin)
- expert_domain : domaine d'expertise revendique
- expert_evidence : justificatif (texte/lien ; document facultatif au debut)
- expert_applied_at : date de candidature
"""
import sqlalchemy as sa

from alembic import op

revision = "e5a1b2c3d4e5"
down_revision = "d4f6a8c0e2f3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("profession", sa.String(120), server_default="", nullable=False), schema="auth")
    op.add_column("users", sa.Column("expert_status", sa.String(20), server_default="none", nullable=False), schema="auth")
    op.add_column("users", sa.Column("expert_domain", sa.String(120), server_default="", nullable=False), schema="auth")
    op.add_column("users", sa.Column("expert_evidence", sa.Text(), server_default="", nullable=False), schema="auth")
    op.add_column("users", sa.Column("expert_applied_at", sa.DateTime(timezone=True), nullable=True), schema="auth")


def downgrade() -> None:
    for col in ("expert_applied_at", "expert_evidence", "expert_domain", "expert_status", "profession"):
        op.drop_column("users", col, schema="auth")
