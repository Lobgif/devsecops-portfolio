"""Modèles du service Forum (schéma `forum`)."""
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from agoraci.common import Base

SCHEMA = "forum"

# Rôles d'adhésion à un groupe
ROLE_MEMBER = "member"
ROLE_ADMIN = "admin"
ROLE_CREATOR = "creator"


class Group(Base):
    """Forum / groupe thématique (mariage, héritage, politique...)."""
    __tablename__ = "groups"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    category: Mapped[str] = mapped_column(String(60), index=True)
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))  # user_id (auth-service)

    is_featured: Mapped[bool] = mapped_column(Boolean, default=False)  # badge « vedette » (super-admin)
    is_private: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")  # contenu réservé aux membres
    member_count: Mapped[int] = mapped_column(Integer, default=1)
    discussion_count: Mapped[int] = mapped_column(Integer, default=0)
    last_activity_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    # Suppression programmée par le super-admin (préavis) — supprimé au balayage après cette date
    deletion_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deletion_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class GroupMembership(Base):
    """Adhésion d'un utilisateur à un groupe, avec rôle (creator/admin/member)."""
    __tablename__ = "group_memberships"
    __table_args__ = (
        UniqueConstraint("group_id", "user_id", name="uq_membership"),
        {"schema": SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    group_id: Mapped[uuid.UUID] = mapped_column(ForeignKey(f"{SCHEMA}.groups.id"), index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    role: Mapped[str] = mapped_column(String(20), default=ROLE_MEMBER)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Discussion(Base):
    """Question / sujet de discussion dans un groupe."""
    __tablename__ = "discussions"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    group_id: Mapped[uuid.UUID] = mapped_column(ForeignKey(f"{SCHEMA}.groups.id"), index=True)
    author_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    title: Mapped[str] = mapped_column(String(255))
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Post(Base):
    """Réponse à une discussion (humaine ou IA)."""
    __tablename__ = "posts"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    discussion_id: Mapped[uuid.UUID] = mapped_column(ForeignKey(f"{SCHEMA}.discussions.id"), index=True)
    author_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    is_ai: Mapped[bool] = mapped_column(Boolean, default=False)
    body: Mapped[str] = mapped_column(Text)
    likes: Mapped[int] = mapped_column(Integer, default=0)       # nb de votes +1
    dislikes: Mapped[int] = mapped_column(Integer, default=0)    # nb de votes -1
    score: Mapped[int] = mapped_column(Integer, default=0)       # likes - dislikes
    is_hidden: Mapped[bool] = mapped_column(Boolean, default=False)  # masqué par modération
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Vote(Base):
    """Vote (+1 / -1) d'un utilisateur sur un post."""
    __tablename__ = "votes"
    __table_args__ = (
        UniqueConstraint("post_id", "user_id", name="uq_vote_post_user"),
        {"schema": SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    post_id: Mapped[uuid.UUID] = mapped_column(ForeignKey(f"{SCHEMA}.posts.id"), index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    value: Mapped[int] = mapped_column(Integer)  # +1 ou -1


class Reputation(Base):
    """Points de réputation d'un utilisateur, calculés sur les j'aime reçus."""
    __tablename__ = "reputation"
    __table_args__ = {"schema": SCHEMA}

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    points: Mapped[int] = mapped_column(Integer, default=0)


class ModerationProposal(Base):
    """Proposition de décision de modération soumise au vote des membres du groupe."""
    __tablename__ = "moderation_proposals"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    group_id: Mapped[uuid.UUID] = mapped_column(ForeignKey(f"{SCHEMA}.groups.id"), index=True)
    target_type: Mapped[str] = mapped_column(String(20))   # post | discussion | user
    target_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    action: Mapped[str] = mapped_column(String(30))         # delete | hide | pin | ban
    proposed_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    status: Mapped[str] = mapped_column(String(20), default="open")  # open|approved|rejected
    votes_for: Mapped[int] = mapped_column(Integer, default=0)
    votes_against: Mapped[int] = mapped_column(Integer, default=0)
    threshold: Mapped[int] = mapped_column(Integer, default=3)       # net requis pour décider
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ModerationVote(Base):
    """Vote d'un membre sur une proposition de modération."""
    __tablename__ = "moderation_votes"
    __table_args__ = (
        UniqueConstraint("proposal_id", "user_id", name="uq_modvote"),
        {"schema": SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    proposal_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(f"{SCHEMA}.moderation_proposals.id"), index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    value: Mapped[int] = mapped_column(Integer)  # +1 ou -1


class Report(Base):
    """Signalement d'un contenu par un utilisateur (file de modération humaine)."""
    __tablename__ = "reports"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    post_id: Mapped[uuid.UUID] = mapped_column(ForeignKey(f"{SCHEMA}.posts.id"), index=True)
    reporter_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    reason: Mapped[str] = mapped_column(String(255), default="")
    status: Mapped[str] = mapped_column(String(20), default="open")  # open|resolved|dismissed
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Follow(Base):
    """Abonnement d'un utilisateur à un groupe ou une discussion (→ notifications)."""
    __tablename__ = "follows"
    __table_args__ = (
        UniqueConstraint("user_id", "target_type", "target_id", name="uq_follow"),
        {"schema": SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    target_type: Mapped[str] = mapped_column(String(20))   # group | discussion
    target_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class GroupProposal(Base):
    """Proposition de création d'un groupe : créé automatiquement au seuil de soutiens."""
    __tablename__ = "group_proposals"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(120))
    category: Mapped[str] = mapped_column(String(60))
    description: Mapped[str] = mapped_column(Text, default="", server_default="")
    motivation: Mapped[str] = mapped_column(Text, default="", server_default="")
    proposed_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    status: Mapped[str] = mapped_column(String(20), default="open", server_default="open")  # open|created|rejected
    support_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    created_group_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class GroupProposalSupport(Base):
    """Un soutien (unique) à une proposition de groupe = « je veux rejoindre »."""
    __tablename__ = "group_proposal_supports"
    __table_args__ = (
        UniqueConstraint("proposal_id", "user_id", name="uq_proposal_support"),
        {"schema": SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    proposal_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(f"{SCHEMA}.group_proposals.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
