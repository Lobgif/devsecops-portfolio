"""Modèles de la messagerie privée 1-à-1 (schéma `chat`)."""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from agoraci.common import Base

SCHEMA = "chat"


class Conversation(Base):
    """Conversation 1-à-1. La paire (user_low, user_high) est canonique (triée)."""
    __tablename__ = "conversations"
    __table_args__ = (
        UniqueConstraint("user_low", "user_high", name="uq_conversation_pair"),
        {"schema": SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_low: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    user_high: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    last_message_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Message(Base):
    __tablename__ = "messages"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(f"{SCHEMA}.conversations.id"), index=True
    )
    sender_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    body: Mapped[str] = mapped_column(Text)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)  # lu par le destinataire
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
