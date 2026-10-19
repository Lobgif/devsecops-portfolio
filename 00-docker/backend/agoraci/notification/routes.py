"""Routes du centre de notifications (utilisateur connecté)."""
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from agoraci.auth.models import User
from agoraci.common import get_session
from agoraci.common.auth_deps import CurrentUser, get_current_user

from .models import Notification, PushSubscription
from .push import VAPID_PUBLIC_KEY

router = APIRouter(prefix="/api/notifications", tags=["notifications"])

# Préférences (opt-out) : clé absente = activé
PREF_KEYS = ["replies", "mentions", "follows", "messages"]


@router.get("/preferences")
async def get_preferences(
    current: CurrentUser = Depends(get_current_user), session: AsyncSession = Depends(get_session)
):
    user = await session.get(User, current.id)
    prefs = (user.notif_prefs or {}) if user else {}
    return {k: bool(prefs.get(k, True)) for k in PREF_KEYS}


@router.put("/preferences")
async def set_preferences(
    payload: dict, current: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    user = await session.get(User, current.id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Utilisateur introuvable")
    prefs = dict(user.notif_prefs or {})
    for k in PREF_KEYS:
        if k in payload:
            prefs[k] = bool(payload[k])
    user.notif_prefs = prefs
    await session.commit()
    return {k: bool(prefs.get(k, True)) for k in PREF_KEYS}


class PushKeys(BaseModel):
    p256dh: str
    auth: str


class PushSub(BaseModel):
    endpoint: str
    keys: PushKeys


@router.get("/push/public-key")
async def push_public_key():
    return {"key": VAPID_PUBLIC_KEY, "enabled": bool(VAPID_PUBLIC_KEY)}


@router.post("/push/subscribe", status_code=201)
async def push_subscribe(
    payload: PushSub,
    current: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    existing = await session.scalar(
        select(PushSubscription).where(PushSubscription.endpoint == payload.endpoint)
    )
    if existing:
        existing.user_id = uuid.UUID(current.id)
        existing.p256dh = payload.keys.p256dh
        existing.auth = payload.keys.auth
    else:
        session.add(PushSubscription(
            user_id=uuid.UUID(current.id), endpoint=payload.endpoint,
            p256dh=payload.keys.p256dh, auth=payload.keys.auth,
        ))
    await session.commit()
    return {"ok": True}


@router.get("")
async def list_notifications(
    limit: int = 20, offset: int = 0,
    current: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    uid = uuid.UUID(current.id)
    limit = max(1, min(limit, 50))
    rows = await session.scalars(
        select(Notification)
        .where(Notification.user_id == uid)
        .order_by(Notification.created_at.desc())
        .limit(limit).offset(offset)
    )
    items = [
        {
            "id": str(n.id), "type": n.type, "title": n.title, "message": n.message,
            "link": n.link, "is_read": n.is_read, "created_at": n.created_at.isoformat(),
        }
        for n in rows
    ]
    unread = await session.scalar(
        select(func.count()).select_from(Notification).where(
            Notification.user_id == uid, Notification.is_read.is_(False)
        )
    )
    return {"items": items, "unread": unread or 0}


@router.get("/unread-count")
async def unread_count(
    current: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    n = await session.scalar(
        select(func.count()).select_from(Notification).where(
            Notification.user_id == uuid.UUID(current.id), Notification.is_read.is_(False)
        )
    )
    return {"unread": n or 0}


@router.post("/{notif_id}/read")
async def mark_read(
    notif_id: uuid.UUID,
    current: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    notif = await session.get(Notification, notif_id)
    if not notif or notif.user_id != uuid.UUID(current.id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Notification introuvable")
    notif.is_read = True
    await session.commit()
    return {"ok": True}


@router.post("/read-all")
async def mark_all_read(
    current: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    await session.execute(
        update(Notification)
        .where(Notification.user_id == uuid.UUID(current.id), Notification.is_read.is_(False))
        .values(is_read=True)
    )
    await session.commit()
    return {"ok": True}
