"""Modèles du service Auth (schéma `auth`)."""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from agoraci.common import Base

SCHEMA = "auth"


class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    hashed_password: Mapped[str | None] = mapped_column(String(255), nullable=True)
    preferred_language: Mapped[str] = mapped_column(String(10), default="fr")
    oauth_provider: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Profil
    full_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    profession: Mapped[str] = mapped_column(String(120), default="", server_default="")

    # Statut d'expert (validé par l'admin) : none | pending | approved | rejected
    expert_status: Mapped[str] = mapped_column(String(20), default="none", server_default="none")
    expert_domain: Mapped[str] = mapped_column(String(120), default="", server_default="")
    expert_evidence: Mapped[str] = mapped_column(Text, default="", server_default="")
    expert_applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    @property
    def is_expert(self) -> bool:
        return self.expert_status == "approved"

    # Statuts / rôles
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)  # email vérifié
    is_moderator: Mapped[bool] = mapped_column(Boolean, default=False)
    is_superadmin: Mapped[bool] = mapped_column(Boolean, default=False)  # créateur plateforme

    # Suspension temporaire (avertissement / blocage par le super-admin)
    suspended_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    suspended_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Préférences de notification (opt-out : clé absente = activé)
    notif_prefs: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")

    # Affichage public du nom : username (défaut) | fullname | firstname
    display_pref: Mapped[str] = mapped_column(String(20), default="username", server_default="username")

    def display_name(self) -> str:
        if self.display_pref == "fullname" and self.full_name:
            return self.full_name
        if self.display_pref == "firstname" and self.full_name:
            return self.full_name.split()[0]
        return self.username

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
