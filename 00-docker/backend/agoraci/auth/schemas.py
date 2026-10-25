"""Schémas Pydantic du service Auth."""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8, max_length=128)
    preferred_language: str = "fr"
    profession: str = Field(default="", max_length=120)  # renseignée par tous (texte libre)
    hp: str = ""  # honeypot anti-spam : doit rester vide (rempli seulement par les bots)
    turnstile_token: str = ""  # jeton Cloudflare Turnstile (vérifié si la clé secrète est configurée)


class ExpertApplyRequest(BaseModel):
    domain: str = Field(min_length=2, max_length=120)   # domaine d'expertise (Droit, Santé…)
    evidence: str = Field(default="", max_length=2000)  # justificatif : texte/lien (document facultatif)


class ExpertReviewRequest(BaseModel):
    approve: bool
    note: str = Field(default="", max_length=255)


class ExpertApplicationOut(BaseModel):
    user_id: str
    username: str
    email: EmailStr
    profession: str
    domain: str
    evidence: str
    status: str
    applied_at: datetime | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class VerifyEmailRequest(BaseModel):
    email: EmailStr
    code: str = Field(min_length=4, max_length=8)


class ResendCodeRequest(BaseModel):
    email: EmailStr


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    code: str = Field(min_length=4, max_length=8)
    new_password: str = Field(min_length=8, max_length=128)


class ProfileUpdate(BaseModel):
    full_name: str | None = Field(default=None, max_length=120)
    bio: str | None = None
    avatar_url: str | None = None
    preferred_language: str | None = None
    display_pref: str | None = Field(default=None, pattern="^(username|fullname|firstname)$")


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    username: str
    full_name: str | None = None
    bio: str | None = None
    avatar_url: str | None = None
    preferred_language: str
    display_pref: str = "username"
    is_verified: bool
    is_moderator: bool
    is_superadmin: bool
