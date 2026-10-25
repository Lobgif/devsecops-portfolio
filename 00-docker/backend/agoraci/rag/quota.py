"""Quota quotidien d'usage de Nanan (protège le coût de l'IA + la capacité).

Base technique du futur « freemium » : compteur par utilisateur (ou par IP si anonyme),
remis à zéro chaque jour, avec une limite RÉGLABLE en admin (clé `nanan_daily_limit`).
0 = illimité. Si Redis est indisponible, on ne bloque jamais (dégradation douce).
"""
from datetime import UTC, datetime

from fastapi import HTTPException, Request, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from agoraci.common import get_redis

DEFAULT_DAILY_LIMIT = 15


async def _daily_limit(session: AsyncSession) -> int:
    try:
        r = await session.execute(
            text("SELECT value FROM public.site_settings WHERE key = 'nanan_daily_limit'")
        )
        v = r.scalar_one_or_none()
        return int(v) if v not in (None, "") else DEFAULT_DAILY_LIMIT
    except Exception:  # noqa: BLE001
        return DEFAULT_DAILY_LIMIT


def _identity(request: Request, user_id: str | None) -> str:
    if user_id:
        return f"u:{user_id}"
    xff = request.headers.get("x-forwarded-for", "")
    ip = xff.split(",")[0].strip() if xff else (request.client.host if request.client else "anon")
    return f"ip:{ip}"


def _key(request: Request, user_id: str | None) -> str:
    day = datetime.now(UTC).strftime("%Y%m%d")
    return f"nanan:quota:{_identity(request, user_id)}:{day}"


async def check_nanan_quota(request: Request, session: AsyncSession, user_id: str | None = None) -> None:
    """Bloque (429) si la limite quotidienne est déjà atteinte. 0 = illimité."""
    limit = await _daily_limit(session)
    if limit <= 0:
        return
    try:
        used = await get_redis().get(_key(request, user_id))
    except Exception:  # noqa: BLE001
        return  # Redis indisponible → on ne bloque pas
    if used is not None and int(used) >= limit:
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            f"Vous avez atteint votre limite de {limit} questions à Nanan pour aujourd'hui. "
            "Revenez demain — bientôt, Jamakan Pro permettra d'en poser davantage 🙂",
        )


async def bump_nanan_quota(request: Request, session: AsyncSession, user_id: str | None = None) -> None:
    """Incrémente les compteurs du jour (à appeler après une réponse réussie de Nanan) :
    - compteur par utilisateur (quota) ;
    - total global + ensemble des utilisateurs (pour le suivi admin de la consommation)."""
    limit_active = await _daily_limit(session) > 0
    try:
        redis = get_redis()
        day = datetime.now(UTC).strftime("%Y%m%d")
        ident = _identity(request, user_id)
        # Compteur de quota par utilisateur (seulement si une limite est active)
        if limit_active:
            key = f"nanan:quota:{ident}:{day}"
            if await redis.incr(key) == 1:
                await redis.expire(key, 86400)  # 24 h
        # Suivi global (toujours, pour le compteur admin) — expire au bout de 2 jours
        total_key = f"nanan:total:{day}"
        if await redis.incr(total_key) == 1:
            await redis.expire(total_key, 172800)
        users_key = f"nanan:users:{day}"
        if await redis.sadd(users_key, ident) and (await redis.ttl(users_key)) < 0:
            await redis.expire(users_key, 172800)
    except Exception:  # noqa: BLE001
        pass


async def nanan_usage_today() -> dict:
    """Consommation Nanan du jour (pour l'admin) : total de questions + utilisateurs uniques."""
    day = datetime.now(UTC).strftime("%Y%m%d")
    try:
        redis = get_redis()
        total = await redis.get(f"nanan:total:{day}")
        users = await redis.scard(f"nanan:users:{day}")
        return {"questions": int(total) if total else 0, "users": int(users or 0)}
    except Exception:  # noqa: BLE001
        return {"questions": 0, "users": 0}
