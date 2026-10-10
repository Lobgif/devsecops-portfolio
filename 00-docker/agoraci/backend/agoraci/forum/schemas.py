"""Schémas Pydantic du service Forum."""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class GroupCreate(BaseModel):
    name: str = Field(min_length=3, max_length=120)
    description: str = ""
    category: str
    is_private: bool = False


class MemberPreview(BaseModel):
    """Aperçu léger d'un membre (pour les avatars empilés sur les cartes de groupe)."""
    username: str
    avatar_url: str | None = None


class GroupOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    description: str
    category: str
    is_featured: bool
    is_private: bool = False
    member_count: int
    discussion_count: int
    badges: list[str] = []
    my_role: str | None = None   # rôle de l'utilisateur courant dans ce groupe (None = non membre)
    last_activity_at: datetime | None = None  # dernière activité (affiché « il y a … »)
    preview_members: list[MemberPreview] = []  # jusqu'à 3 membres pour les avatars empilés
    deletion_at: datetime | None = None       # suppression programmée (préavis super-admin)
    deletion_reason: str | None = None


class AddAdminRequest(BaseModel):
    user_id: uuid.UUID


class DiscussionCreate(BaseModel):
    group_id: uuid.UUID
    title: str = Field(min_length=5, max_length=255)
    body: str = Field(min_length=1)


class DiscussionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    group_id: uuid.UUID
    title: str
    body: str


class PostCreate(BaseModel):
    discussion_id: uuid.UUID
    is_ai: bool = False
    body: str = Field(min_length=1)


class PostOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    discussion_id: uuid.UUID
    is_ai: bool
    body: str
    likes: int
    dislikes: int
    score: int


class VoteCreate(BaseModel):
    post_id: uuid.UUID
    value: int = Field(ge=-1, le=1)


class ProposalCreate(BaseModel):
    target_type: str = Field(pattern="^(post|discussion|user)$")
    target_id: uuid.UUID
    action: str = Field(pattern="^(delete|hide|pin|ban|admit|promote_mod)$")
    threshold: int = Field(default=3, ge=1, le=100)


class ProposalVote(BaseModel):
    value: int = Field(ge=-1, le=1)


class ProposalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    group_id: uuid.UUID
    target_type: str
    target_id: uuid.UUID
    action: str
    status: str
    votes_for: int
    votes_against: int
    threshold: int


class ReputationOut(BaseModel):
    user_id: uuid.UUID
    points: int
