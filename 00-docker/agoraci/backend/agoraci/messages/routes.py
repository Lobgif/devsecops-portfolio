"""Routes de la messagerie privée 1-à-1."""
import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from agoraci.common import get_redis, get_session
from agoraci.common.auth_deps import CurrentUser, get_current_user
from agoraci.common.messaging import get_event_bus

from .models import Conversation, Message

router = APIRouter(prefix="/api/messages", tags=["messages"])


class StartRequest(BaseModel):
    peer_id: uuid.UUID


class SendRequest(BaseModel):
    body: str = Field(min_length=1, max_length=4000)


def _pair(a: uuid.UUID, b: uuid.UUID) -> tuple[uuid.UUID, uuid.UUID]:
    return (a, b) if str(a) < str(b) else (b, a)


async def _get_conv_or_404(session: AsyncSession, conv_id: uuid.UUID, me: uuid.UUID) -> Conversation:
    conv = await session.get(Conversation, conv_id)
    if not conv or me not in (conv.user_low, conv.user_high):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Conversation introuvable")
    return conv


@router.post("/start")
async def start_conversation(
    payload: StartRequest,
    current: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    me = uuid.UUID(current.id)
    if payload.peer_id == me:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Impossible de se message soi-même")
    low, high = _pair(me, payload.peer_id)
    conv = await session.scalar(
        select(Conversation).where(Conversation.user_low == low, Conversation.user_high == high)
    )
    if not conv:
        conv = Conversation(user_low=low, user_high=high)
        session.add(conv)
        await session.commit()
        await session.refresh(conv)
    return {"conversation_id": str(conv.id)}


@router.get("/conversations")
async def list_conversations(
    current: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    me = uuid.UUID(current.id)
    convs = await session.scalars(
        select(Conversation)
        .where(or_(Conversation.user_low == me, Conversation.user_high == me))
        .order_by(Conversation.last_message_at.desc())
    )
    out = []
    for c in convs:
        peer = c.user_high if c.user_low == me else c.user_low
        last = await session.scalar(
            select(Message).where(Message.conversation_id == c.id).order_by(Message.created_at.desc()).limit(1)
        )
        unread = await session.scalar(
            select(func.count()).select_from(Message).where(
                Message.conversation_id == c.id, Message.sender_id != me, Message.is_read.is_(False)
            )
        )
        out.append({
            "id": str(c.id), "peer_id": str(peer),
            "last_message": (last.body[:80] if last else ""),
            "last_message_at": c.last_message_at.isoformat(),
            "unread": unread or 0,
        })
    return out


@router.get("/{conversation_id}")
async def get_thread(
    conversation_id: uuid.UUID,
    current: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    me = uuid.UUID(current.id)
    conv = await _get_conv_or_404(session, conversation_id, me)
    msgs = await session.scalars(
        select(Message).where(Message.conversation_id == conv.id).order_by(Message.created_at)
    )
    items = [
        {"id": str(m.id), "sender_id": str(m.sender_id), "body": m.body,
         "created_at": m.created_at.isoformat()} for m in msgs
    ]
    # Marque comme lus les messages reçus
    await session.execute(
        update(Message)
        .where(Message.conversation_id == conv.id, Message.sender_id != me, Message.is_read.is_(False))
        .values(is_read=True)
    )
    await session.commit()
    peer = conv.user_high if conv.user_low == me else conv.user_low
    return {"id": str(conv.id), "peer_id": str(peer), "messages": items}


@router.post("/{conversation_id}", status_code=201)
async def send_message(
    conversation_id: uuid.UUID,
    payload: SendRequest,
    current: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    me = uuid.UUID(current.id)
    conv = await _get_conv_or_404(session, conversation_id, me)
    msg = Message(conversation_id=conv.id, sender_id=me, body=payload.body)
    session.add(msg)
    conv.last_message_at = func.now()
    await session.commit()
    await session.refresh(msg)

    data = {"id": str(msg.id), "sender_id": str(me), "body": msg.body,
            "created_at": msg.created_at.isoformat()}
    # Temps réel : diffuse aux clients WebSocket de la room dm-<conv>
    try:
        await get_redis().publish(f"chat:dm-{conv.id}", json.dumps(data))
    except Exception:  # noqa: BLE001
        pass
    # Notification au destinataire
    peer = conv.user_high if conv.user_low == me else conv.user_low
    await get_event_bus().publish(
        "message.created",
        {"conversation_id": str(conv.id), "recipient_id": str(peer),
         "sender_id": str(me), "preview": msg.body[:80]},
    )
    return data
