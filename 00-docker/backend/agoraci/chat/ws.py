"""Chat temps réel : WebSocket + diffusion via Redis pub/sub (multi-instances)."""
import asyncio
import json
import logging

import redis.asyncio as redis
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from agoraci.common.config import get_settings

settings = get_settings()
router = APIRouter()
logger = logging.getLogger("chat.ws")


class RoomManager:
    def __init__(self) -> None:
        self.local: dict[str, set[WebSocket]] = {}
        self._redis = redis.from_url(settings.redis_url, decode_responses=True)

    async def join(self, room: str, ws: WebSocket) -> None:
        await ws.accept()
        self.local.setdefault(room, set()).add(ws)

    def leave(self, room: str, ws: WebSocket) -> None:
        self.local.get(room, set()).discard(ws)

    async def publish(self, room: str, message: dict) -> None:
        await self._redis.publish(f"chat:{room}", json.dumps(message))

    async def broadcast_local(self, room: str, message: dict) -> None:
        for ws in list(self.local.get(room, set())):
            try:
                await ws.send_json(message)
            except Exception:  # noqa: BLE001
                self.leave(room, ws)

    async def redis_listener(self) -> None:
        """Écoute Redis pub/sub en continu et diffuse aux WebSockets locaux.

        Résilient : en cas de timeout ou de déconnexion Redis, la tâche NE MEURT PAS —
        elle se reconnecte automatiquement (le chat temps réel reste opérationnel)."""
        while True:
            pubsub = self._redis.pubsub()
            try:
                await pubsub.psubscribe("chat:*")
                async for msg in pubsub.listen():
                    if msg["type"] != "pmessage":
                        continue
                    room = msg["channel"].split(":", 1)[1]
                    await self.broadcast_local(room, json.loads(msg["data"]))
            except asyncio.CancelledError:
                raise  # arrêt propre de l'application
            except Exception as exc:  # noqa: BLE001
                logger.warning("redis_listener interrompu (%s) — reconnexion dans 2 s", exc)
                await asyncio.sleep(2)
            finally:
                try:
                    await pubsub.aclose()
                except Exception:  # noqa: BLE001
                    pass


manager = RoomManager()


async def start_chat_listener() -> None:
    asyncio.create_task(manager.redis_listener())


@router.websocket("/ws/{room}")
async def chat_ws(ws: WebSocket, room: str) -> None:
    await manager.join(room, ws)
    try:
        while True:
            data = await ws.receive_json()
            await manager.publish(room, data)
    except WebSocketDisconnect:
        manager.leave(room, ws)
