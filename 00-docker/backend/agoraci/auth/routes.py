"""Routes du service Auth : inscription, vérification email, connexion, OAuth, profil."""
import secrets
import uuid
from datetime import UTC, datetime, timedelta

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from agoraci.common import get_redis, get_session, get_settings, limiter
from agoraci.common.auth_deps import CurrentUser, get_current_user, require_superadmin
from agoraci.common.messaging import get_event_bus
from agoraci.common.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)

from .models import User
from .oauth import oauth
from .schemas import (
    ExpertApplicationOut,
    ExpertApplyRequest,
    ExpertReviewRequest,
    ForgotPasswordRequest,
    LoginRequest,
    ProfileUpdate,
    RefreshRequest,
    RegisterRequest,
    ResendCodeRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserResponse,
    VerifyEmailRequest,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])
settings = get_settings()


def _access_claims(user: User) -> dict:
    return {"is_superadmin": user.is_superadmin, "is_verified": user.is_verified}


def _ensure_not_suspended(user: User) -> None:
    """Bloque l'accès si le compte est suspendu (avertissement temporaire)."""
    until = user.suspended_until
    if until:
        if until.tzinfo is None:
            until = until.replace(tzinfo=UTC)
        if until > datetime.now(UTC):
            when = until.strftime("%d/%m/%Y à %Hh%M")
            reason = f" Motif : {user.suspended_reason}" if user.suspended_reason else ""
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                f"Compte suspendu jusqu'au {when}.{reason}",
            )


def _set_auth_cookies(resp: Response, access: str, refresh: str) -> None:
    """Pose les JWT en cookies httpOnly (protégés du JS → anti-XSS)."""
    secure = settings.env == "production"
    base = {"httponly": True, "samesite": "lax", "secure": secure, "path": "/"}
    resp.set_cookie("access_token", access, max_age=settings.access_token_expire_minutes * 60, **base)
    resp.set_cookie("refresh_token", refresh, max_age=settings.refresh_token_expire_days * 86400, **base)


def _clear_auth_cookies(resp: Response) -> None:
    resp.delete_cookie("access_token", path="/")
    resp.delete_cookie("refresh_token", path="/")


# Suppression en cascade d'un compte (ordre des dépendances FK respecté).
_PURGE_SQL = [
    # Votes : ceux de l'utilisateur + ceux portant sur ses contenus
    "DELETE FROM forum.votes WHERE user_id = :u",
    "DELETE FROM forum.votes WHERE post_id IN (SELECT id FROM forum.posts WHERE author_id = :u)",
    "DELETE FROM forum.votes WHERE post_id IN (SELECT id FROM forum.posts WHERE discussion_id IN (SELECT id FROM forum.discussions WHERE author_id = :u))",
    # Signalements
    "DELETE FROM forum.reports WHERE reporter_id = :u",
    "DELETE FROM forum.reports WHERE post_id IN (SELECT id FROM forum.posts WHERE author_id = :u)",
    "DELETE FROM forum.reports WHERE post_id IN (SELECT id FROM forum.posts WHERE discussion_id IN (SELECT id FROM forum.discussions WHERE author_id = :u))",
    # Réponses (siennes, puis celles d'autrui dans ses discussions)
    "DELETE FROM forum.posts WHERE author_id = :u",
    "DELETE FROM forum.posts WHERE discussion_id IN (SELECT id FROM forum.discussions WHERE author_id = :u)",
    # Modération
    "DELETE FROM forum.moderation_votes WHERE user_id = :u",
    "DELETE FROM forum.moderation_votes WHERE proposal_id IN (SELECT id FROM forum.moderation_proposals WHERE proposed_by = :u)",
    "DELETE FROM forum.moderation_proposals WHERE proposed_by = :u",
    # Abonnements (les siens + ceux sur ses discussions)
    "DELETE FROM forum.follows WHERE user_id = :u",
    "DELETE FROM forum.follows WHERE target_type = 'discussion' AND target_id IN (SELECT id FROM forum.discussions WHERE author_id = :u)",
    # Discussions
    "DELETE FROM forum.discussions WHERE author_id = :u",
    # Décrémente le compteur de membres des groupes concernés, puis adhésions + réputation
    "UPDATE forum.groups SET member_count = GREATEST(0, member_count - 1) WHERE id IN (SELECT group_id FROM forum.group_memberships WHERE user_id = :u)",
    "DELETE FROM forum.group_memberships WHERE user_id = :u",
    "DELETE FROM forum.reputation WHERE user_id = :u",
    # Notifications & push
    "DELETE FROM notification.notifications WHERE user_id = :u",
    "DELETE FROM notification.push_subscriptions WHERE user_id = :u",
    # Messagerie privée
    "DELETE FROM chat.messages WHERE sender_id = :u",
    "DELETE FROM chat.messages WHERE conversation_id IN (SELECT id FROM chat.conversations WHERE user_low = :u OR user_high = :u)",
    "DELETE FROM chat.conversations WHERE user_low = :u OR user_high = :u",
    # Compte
    "DELETE FROM auth.users WHERE id = :u",
]


async def _purge_user(session: AsyncSession, user_id: str) -> None:
    for stmt in _PURGE_SQL:
        await session.execute(text(stmt), {"u": str(user_id)})


async def _verify_turnstile(token: str, remote_ip: str | None) -> bool:
    """Vérifie un jeton Cloudflare Turnstile. True si désactivé (pas de clé secrète)."""
    if not settings.turnstile_secret_key:
        return True
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(
                "https://challenges.cloudflare.com/turnstile/v0/siteverify",
                data={"secret": settings.turnstile_secret_key, "response": token,
                      "remoteip": remote_ip or ""},
            )
            return bool(r.json().get("success"))
    except Exception:  # noqa: BLE001
        return False


async def _issue_and_send_code(email: str, username: str) -> None:
    """Génère un code à 6 chiffres, le stocke dans Redis (TTL) et déclenche l'email."""
    code = f"{secrets.randbelow(1_000_000):06d}"
    ttl = settings.verification_code_ttl_minutes * 60
    await get_redis().set(f"verify:{email}", code, ex=ttl)
    await get_event_bus().publish(
        "user.registration_code",
        {
            "email": email,
            "username": username,
            "code": code,
            "ttl_minutes": settings.verification_code_ttl_minutes,
        },
    )


@router.post("/register", response_model=UserResponse, status_code=201)
@limiter.limit("5/minute")
async def register(
    request: Request, payload: RegisterRequest, session: AsyncSession = Depends(get_session)
):
    # Honeypot : un humain ne remplit jamais ce champ caché → c'est un bot
    if payload.hp.strip():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Inscription refusée.")
    # Turnstile (si configuré)
    if not await _verify_turnstile(payload.turnstile_token, request.client.host if request.client else None):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Échec de la vérification anti-robot.")
    exists = await session.scalar(
        select(User).where((User.email == payload.email) | (User.username == payload.username))
    )
    if exists:
        raise HTTPException(status.HTTP_409_CONFLICT, "Email ou nom d'utilisateur déjà pris")

    user = User(
        email=payload.email,
        username=payload.username,
        hashed_password=hash_password(payload.password),
        preferred_language=payload.preferred_language,
        profession=payload.profession.strip()[:120],
        is_verified=False,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)

    await _issue_and_send_code(user.email, user.username)
    await get_event_bus().publish(
        "user.registered",
        {"user_id": str(user.id), "email": user.email, "username": user.username},
    )
    return user


@router.post("/verify-email", response_model=TokenResponse)
@limiter.limit("10/minute")
async def verify_email(
    request: Request, response: Response, payload: VerifyEmailRequest,
    session: AsyncSession = Depends(get_session),
):
    stored = await get_redis().get(f"verify:{payload.email}")
    if not stored or stored != payload.code:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Code invalide ou expiré")

    user = await session.scalar(select(User).where(User.email == payload.email))
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Utilisateur introuvable")

    user.is_verified = True
    await session.commit()
    await get_redis().delete(f"verify:{payload.email}")

    access = create_access_token(str(user.id), _access_claims(user))
    refresh = create_refresh_token(str(user.id))
    _set_auth_cookies(response, access, refresh)
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post("/resend-code", status_code=202)
@limiter.limit("3/minute")
async def resend_code(
    request: Request, payload: ResendCodeRequest, session: AsyncSession = Depends(get_session)
):
    user = await session.scalar(select(User).where(User.email == payload.email))
    if user and not user.is_verified:
        await _issue_and_send_code(user.email, user.username)
    # Réponse identique qu'il existe ou non (anti-énumération)
    return {"message": "Si un compte non vérifié existe, un nouveau code a été envoyé."}


@router.post("/forgot-password", status_code=202)
@limiter.limit("3/minute")
async def forgot_password(
    request: Request, payload: ForgotPasswordRequest, session: AsyncSession = Depends(get_session)
):
    user = await session.scalar(select(User).where(User.email == payload.email))
    if user:
        code = f"{secrets.randbelow(1_000_000):06d}"
        ttl = settings.verification_code_ttl_minutes * 60
        await get_redis().set(f"reset:{payload.email}", code, ex=ttl)
        await get_event_bus().publish(
            "user.password_reset_code",
            {"email": payload.email, "username": user.username, "code": code,
             "ttl_minutes": settings.verification_code_ttl_minutes},
        )
    return {"message": "Si un compte existe, un code de réinitialisation a été envoyé."}


@router.post("/reset-password")
@limiter.limit("10/minute")
async def reset_password(
    request: Request, payload: ResetPasswordRequest, session: AsyncSession = Depends(get_session)
):
    stored = await get_redis().get(f"reset:{payload.email}")
    if not stored or stored != payload.code:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Code invalide ou expiré")
    user = await session.scalar(select(User).where(User.email == payload.email))
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Utilisateur introuvable")
    user.hashed_password = hash_password(payload.new_password)
    await session.commit()
    await get_redis().delete(f"reset:{payload.email}")
    return {"message": "Mot de passe réinitialisé. Vous pouvez vous connecter."}


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
async def login(
    request: Request, response: Response, payload: LoginRequest,
    session: AsyncSession = Depends(get_session),
):
    user = await session.scalar(select(User).where(User.email == payload.email))
    if (
        not user
        or not user.hashed_password
        or not verify_password(payload.password, user.hashed_password)
    ):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Identifiants invalides")
    if not user.is_verified:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Email non vérifié. Vérifiez votre boîte mail.")
    _ensure_not_suspended(user)

    access = create_access_token(str(user.id), _access_claims(user))
    refresh = create_refresh_token(str(user.id))
    _set_auth_cookies(response, access, refresh)
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    request: Request, response: Response,
    payload: RefreshRequest | None = None,
    session: AsyncSession = Depends(get_session),
):
    token = (payload.refresh_token if payload else None) or request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Refresh token manquant")
    try:
        claims = decode_token(token)
    except ValueError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(exc)) from exc
    if claims.get("type") != "refresh":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token de refresh attendu")

    # Plafond ABSOLU : au-delà de refresh_token_expire_days depuis la connexion → reconnexion
    auth_time = claims.get("auth_time")
    if auth_time:
        age = datetime.now(UTC).timestamp() - float(auth_time)
        if age > settings.refresh_token_expire_days * 86400:
            _clear_auth_cookies(response)
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Session expirée, reconnectez-vous.")

    user = await session.get(User, claims["sub"])
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Utilisateur introuvable")
    _ensure_not_suspended(user)
    access = create_access_token(str(user.id), _access_claims(user))
    # Refresh glissant : nouvelle fenêtre d'inactivité, mais on reporte auth_time (plafond absolu)
    refresh_tok = create_refresh_token(str(user.id), auth_time=int(auth_time) if auth_time else None)
    _set_auth_cookies(response, access, refresh_tok)
    return TokenResponse(access_token=access, refresh_token=refresh_tok)


@router.post("/logout")
async def logout(response: Response):
    _clear_auth_cookies(response)
    return {"ok": True}


# --------------------------- Profil ---------------------------
@router.get("/me", response_model=UserResponse)
async def me(
    current: CurrentUser = Depends(get_current_user), session: AsyncSession = Depends(get_session)
):
    user = await session.get(User, current.id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Utilisateur introuvable")
    return user


@router.put("/me", response_model=UserResponse)
async def update_me(
    payload: ProfileUpdate,
    current: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    user = await session.get(User, current.id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Utilisateur introuvable")
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(user, field, value)
    await session.commit()
    await session.refresh(user)
    return user


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


@router.post("/change-password")
async def change_password(
    payload: ChangePasswordRequest,
    current: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    user = await session.get(User, current.id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Utilisateur introuvable")
    if not user.hashed_password or not verify_password(payload.current_password, user.hashed_password):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Mot de passe actuel incorrect.")
    if len(payload.new_password) < 8:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Le nouveau mot de passe doit faire au moins 8 caractères.")
    user.hashed_password = hash_password(payload.new_password)
    await session.commit()
    return {"message": "Mot de passe mis à jour."}


@router.delete("/me")
async def delete_my_account(
    response: Response,
    current: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Suppression de son propre compte (RGPD)."""
    user = await session.get(User, current.id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Utilisateur introuvable")
    if user.is_superadmin:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Le compte super-admin ne peut pas être supprimé depuis le profil.",
        )
    await _purge_user(session, current.id)
    await session.commit()
    _clear_auth_cookies(response)
    return {"deleted": current.id}


@router.get("/users/{ident}")
async def public_profile(ident: str, session: AsyncSession = Depends(get_session)):
    """Profil public d'un utilisateur — accessible par id (UUID) OU par pseudo (@mentions)."""
    import uuid as _uuid
    user = None
    try:
        user = await session.get(User, _uuid.UUID(ident))
    except (ValueError, AttributeError):
        user = None
    if user is None:
        user = await session.scalar(select(User).where(User.username == ident))
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Utilisateur introuvable")
    total, good = await _contribution_counts(session, user)
    return {
        "id": str(user.id),
        "username": user.username,
        "full_name": user.full_name,
        "display_name": user.display_name(),  # respecte la préférence d'affichage
        "avatar_url": user.avatar_url,
        "bio": user.bio,
        "profession": user.profession,
        "is_expert": user.is_expert,
        "expert_domain": user.expert_domain if user.is_expert else "",
        "badges": _badges_from_stats(user, total, good),
        "contribution": _contribution_from_stats(total, good),
    }


async def _contribution_counts(session: AsyncSession, user: User) -> tuple[int, int]:
    """(réponses totales, réponses jugées bonnes) — non IA, non masquées."""
    from agoraci.forum.models import Post
    base = select(func.count()).select_from(Post).where(
        Post.author_id == user.id, Post.is_ai.is_(False), Post.is_hidden.is_(False)
    )
    total = await session.scalar(base) or 0
    good = await session.scalar(base.where(Post.score > 0)) or 0
    return total, good


# Paliers de contribution (nb de réponses) — cohérents avec les badges.
_TIERS = [(0, "Nouveau membre"), (75, "Membre actif"), (100, "Contributeur"),
          (200, "Contributeur confirmé"), (500, "Référence de la communauté")]


def _badges_from_stats(user: User, total: int, good: int) -> list[dict]:
    """Badges : expert (validé admin) + palier de contribution (quantité ET qualité)."""
    rate = (good / total) if total else 0.0
    badges: list[dict] = []
    if user.is_expert:
        label = f"Expert vérifié — {user.expert_domain}" if user.expert_domain else "Expert vérifié"
        badges.append({"type": "expert", "label": label})
    if total >= 500 and rate > 0.90:
        badges.append({"type": "tier", "label": "Référence de la communauté"})
    elif total >= 200 and rate >= 0.70:
        badges.append({"type": "tier", "label": "Contributeur confirmé"})
    elif total >= 100:
        badges.append({"type": "tier", "label": "Contributeur"})
    elif total >= 75:
        badges.append({"type": "tier", "label": "Membre actif"})
    return badges


def _contribution_from_stats(total: int, good: int) -> dict:
    """Palier courant + palier suivant + progression (pour la carte « Votre niveau »)."""
    idx = 0
    for i, (thr, _) in enumerate(_TIERS):
        if total >= thr:
            idx = i
    cur_at, cur_label = _TIERS[idx]
    nxt = _TIERS[idx + 1] if idx + 1 < len(_TIERS) else None
    progress = 100
    remaining = 0
    if nxt:
        span = nxt[0] - cur_at
        progress = int(round(100 * (total - cur_at) / span)) if span else 100
        remaining = max(0, nxt[0] - total)
    return {
        "answers": total, "good": good,
        "rate": round((good / total) if total else 0.0, 2),
        "tier": cur_label,
        "next_tier": nxt[1] if nxt else None,
        "remaining": remaining,
        "progress": max(0, min(100, progress)),
    }


# --------------------------- Candidature / validation d'expert ---------------------------
@router.post("/expert/apply", status_code=202)
async def expert_apply(
    payload: ExpertApplyRequest,
    current: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Un utilisateur postule pour devenir expert vérifié dans un domaine.
    L'admin valide ensuite (justificatif facultatif au début pour ne pas décourager)."""
    user = await session.get(User, uuid.UUID(current.id))
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Utilisateur introuvable")
    if user.expert_status == "approved":
        raise HTTPException(status.HTTP_409_CONFLICT, "Vous êtes déjà expert vérifié.")
    user.expert_domain = payload.domain.strip()[:120]
    user.expert_evidence = payload.evidence.strip()[:2000]
    user.expert_status = "pending"
    user.expert_applied_at = datetime.now(UTC)
    await session.commit()
    return {"status": "pending", "message": "Candidature envoyée. Un administrateur va l'examiner."}


@router.get("/admin/expert-applications", response_model=list[ExpertApplicationOut])
async def list_expert_applications(
    _: CurrentUser = Depends(require_superadmin), session: AsyncSession = Depends(get_session)
):
    """Liste des candidatures d'experts en attente (pour l'admin)."""
    users = await session.scalars(
        select(User).where(User.expert_status == "pending").order_by(User.expert_applied_at)
    )
    return [
        ExpertApplicationOut(
            user_id=str(u.id), username=u.username, email=u.email, profession=u.profession,
            domain=u.expert_domain, evidence=u.expert_evidence, status=u.expert_status,
            applied_at=u.expert_applied_at,
        )
        for u in users
    ]


@router.post("/admin/experts/{user_id}/review")
async def review_expert(
    user_id: str, payload: ExpertReviewRequest,
    _: CurrentUser = Depends(require_superadmin), session: AsyncSession = Depends(get_session),
):
    """L'admin approuve ou rejette une candidature d'expert."""
    user = await session.get(User, uuid.UUID(user_id))
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Utilisateur introuvable")
    user.expert_status = "approved" if payload.approve else "rejected"
    await session.commit()
    return {"user_id": str(user.id), "expert_status": user.expert_status}


# --------------------------- Utilisateurs (admin) ---------------------------
@router.get("/admin/users")
async def admin_list_users(
    _: CurrentUser = Depends(require_superadmin), session: AsyncSession = Depends(get_session)
):
    users = await session.scalars(select(User).order_by(User.created_at.desc()).limit(200))
    return [
        {"id": str(u.id), "username": u.username, "email": u.email, "full_name": u.full_name,
         "is_verified": u.is_verified, "is_moderator": u.is_moderator, "is_superadmin": u.is_superadmin,
         "suspended_until": u.suspended_until.isoformat() if u.suspended_until else None,
         "suspended_reason": u.suspended_reason}
        for u in users
    ]


class RoleFlags(BaseModel):
    is_moderator: bool | None = None
    # is_superadmin retiré volontairement : le super-admin est UNIQUE (défini dans .env),
    # personne ne peut être promu super-admin depuis l'interface.


class SuspendRequest(BaseModel):
    days: int = 7
    reason: str | None = None


@router.post("/admin/users/{user_id}/suspend")
async def admin_suspend_user(
    user_id: str, payload: SuspendRequest,
    current: CurrentUser = Depends(require_superadmin),
    session: AsyncSession = Depends(get_session),
):
    """Suspend temporairement un compte (avertissement). Pouvoir réservé au super-admin."""
    if str(user_id) == current.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Vous ne pouvez pas vous suspendre vous-même.")
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Utilisateur introuvable")
    if user.is_superadmin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Impossible de suspendre un super-admin.")
    days = max(1, min(payload.days, 3650))
    user.suspended_until = datetime.now(UTC) + timedelta(days=days)
    user.suspended_reason = (payload.reason or "").strip()[:255] or None
    await session.commit()
    # Notifie l'utilisateur suspendu
    await get_event_bus().publish("user.suspended", {
        "user_id": str(user.id), "until": user.suspended_until.isoformat(),
        "reason": user.suspended_reason,
    })
    return {"id": str(user.id), "suspended_until": user.suspended_until.isoformat(),
            "suspended_reason": user.suspended_reason}


@router.post("/admin/users/{user_id}/unsuspend")
async def admin_unsuspend_user(
    user_id: str, _: CurrentUser = Depends(require_superadmin),
    session: AsyncSession = Depends(get_session),
):
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Utilisateur introuvable")
    user.suspended_until = None
    user.suspended_reason = None
    await session.commit()
    return {"id": str(user.id), "suspended_until": None}


@router.delete("/admin/users/{user_id}")
async def admin_delete_user(
    user_id: str, current: CurrentUser = Depends(require_superadmin),
    session: AsyncSession = Depends(get_session),
):
    """Supprime définitivement un compte et tout son contenu. Pouvoir absolu du super-admin."""
    if str(user_id) == current.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Vous ne pouvez pas supprimer votre propre compte.")
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Utilisateur introuvable")
    if user.is_superadmin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Impossible de supprimer un autre super-admin.")
    await _purge_user(session, user_id)
    await session.commit()
    return {"deleted": str(user_id)}


@router.post("/admin/users/{user_id}/role")
async def admin_set_user_role(
    user_id: str, payload: RoleFlags,
    current: CurrentUser = Depends(require_superadmin),
    session: AsyncSession = Depends(get_session),
):
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Utilisateur introuvable")
    if payload.is_moderator is not None:
        user.is_moderator = payload.is_moderator
    await session.commit()
    return {"id": str(user.id), "is_superadmin": user.is_superadmin, "is_moderator": user.is_moderator}


# --------------------------- OAuth Google ---------------------------
@router.get("/google/login")
async def google_login(request: Request):
    if not settings.google_client_id or not settings.google_client_secret:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "Connexion Google non configurée (GOOGLE_CLIENT_ID/SECRET manquants).",
        )
    return await oauth.google.authorize_redirect(request, settings.google_redirect_uri)


@router.get("/google/callback")
async def google_callback(request: Request, session: AsyncSession = Depends(get_session)):
    token = await oauth.google.authorize_access_token(request)
    info = token.get("userinfo") or await oauth.google.userinfo(token=token)
    email = info["email"]

    user = await session.scalar(select(User).where(User.email == email))
    if not user:
        base = email.split("@")[0]
        user = User(
            email=email,
            username=f"{base}-{secrets.token_hex(2)}",
            preferred_language="fr",
            oauth_provider="google",
            full_name=info.get("name"),
            avatar_url=info.get("picture"),
            is_verified=True,  # email validé par Google
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        await get_event_bus().publish(
            "user.registered",
            {"user_id": str(user.id), "email": user.email, "username": user.username},
        )

    access = create_access_token(str(user.id), _access_claims(user))
    refresh_tok = create_refresh_token(str(user.id))
    # Cookies httpOnly posés sur la redirection (plus de token dans l'URL)
    redirect = RedirectResponse(f"{settings.frontend_url}/auth/callback")
    _set_auth_cookies(redirect, access, refresh_tok)
    return redirect
