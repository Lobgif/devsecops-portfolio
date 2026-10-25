"""Dépendances FastAPI d'authentification, partagées par tous les services.

Le JWT d'accès est lu en priorité depuis le **cookie httpOnly** `access_token`
(protégé du JavaScript → anti-XSS), avec repli sur l'en-tête `Authorization: Bearer`
(pratique pour les scripts/tests). Validation locale (secret partagé), sans appel réseau.
"""
from dataclasses import dataclass

from fastapi import HTTPException, Request, status

from .security import decode_token


@dataclass
class CurrentUser:
    id: str
    is_superadmin: bool = False
    is_verified: bool = False


def _extract_token(request: Request) -> str | None:
    token = request.cookies.get("access_token")
    if token:
        return token
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth[7:]
    return None


async def get_current_user(request: Request) -> CurrentUser:
    token = _extract_token(request)
    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Authentification requise")
    try:
        claims = decode_token(token)
    except ValueError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(exc)) from exc
    if claims.get("type") != "access":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token d'accès attendu")
    return CurrentUser(
        id=claims["sub"],
        is_superadmin=bool(claims.get("is_superadmin", False)),
        is_verified=bool(claims.get("is_verified", False)),
    )


async def get_optional_user(request: Request) -> CurrentUser | None:
    """Comme get_current_user mais renvoie None au lieu de lever (routes publiques)."""
    try:
        return await get_current_user(request)
    except HTTPException:
        return None


async def require_superadmin(request: Request) -> CurrentUser:
    user = await get_current_user(request)
    if not user.is_superadmin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Accès super-administrateur requis")
    return user
