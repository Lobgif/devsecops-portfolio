"""Modèles transverses : paramètres du site (dynamiques) + glossaire juridique.

Tables dans le schéma `public` (configuration globale, non rattachée à un domaine métier).
"""
import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from agoraci.common import Base


class SiteSetting(Base):
    """Paramètre clé/valeur éditable depuis l'admin (email, pied de page, réseaux…)."""
    __tablename__ = "site_settings"

    key: Mapped[str] = mapped_column(String(80), primary_key=True)
    value: Mapped[str] = mapped_column(Text, default="")


class GlossaryTerm(Base):
    """Terme du glossaire juridique."""
    __tablename__ = "glossary_terms"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    term: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    category: Mapped[str] = mapped_column(String(60), index=True, default="Général")
    definition: Mapped[str] = mapped_column(Text)


class Article(Base):
    """Actualité civique (loi, droit, élections…)."""
    __tablename__ = "articles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255))
    summary: Mapped[str] = mapped_column(Text, default="")
    content: Mapped[str] = mapped_column(Text, default="")
    category: Mapped[str] = mapped_column(String(60), index=True, default="Nouvelles lois")
    source: Mapped[str] = mapped_column(String(120), default="")
    published_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ContactMessage(Base):
    """Message envoyé depuis le formulaire de contact public (consulté en admin)."""
    __tablename__ = "contact_messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(120), default="")
    email: Mapped[str] = mapped_column(String(255), default="")
    subject: Mapped[str] = mapped_column(String(200), default="")
    message: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(20), default="new", server_default="new")  # new|read|archived
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
