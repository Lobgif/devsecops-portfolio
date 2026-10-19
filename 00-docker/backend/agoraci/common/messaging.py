"""Bus d'événements inter-services via RabbitMQ (aio-pika).

Modèle : exchange `topic` partagé. Chaque service publie des événements
(`user.registered`, `post.created`, `content.flagged`, ...) et s'abonne
aux routing keys qui l'intéressent.
"""
import asyncio
import json
import logging
from collections.abc import Awaitable, Callable

import aio_pika
from aio_pika.abc import AbstractIncomingMessage

from .config import get_settings

logger = logging.getLogger(__name__)

Handler = Callable[[str, dict], Awaitable[None]]


class EventBus:
    def __init__(self) -> None:
        self._settings = get_settings()
        self._connection: aio_pika.RobustConnection | None = None
        self._channel: aio_pika.abc.AbstractChannel | None = None
        self._exchange: aio_pika.abc.AbstractExchange | None = None

    async def connect(self, *, retries: int = 30, delay: float = 2.0) -> None:
        """Connexion résiliente : réessaie tant que RabbitMQ n'accepte pas (démarrage)."""
        last_exc: Exception | None = None
        for attempt in range(1, retries + 1):
            try:
                self._connection = await aio_pika.connect_robust(self._settings.rabbitmq_url)
                self._channel = await self._connection.channel()
                self._exchange = await self._channel.declare_exchange(
                    self._settings.rabbitmq_exchange,
                    aio_pika.ExchangeType.TOPIC,
                    durable=True,
                )
                logger.info("EventBus connecté à RabbitMQ (%s)", self._settings.rabbitmq_exchange)
                return
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                logger.warning("RabbitMQ indisponible (essai %d/%d): %s", attempt, retries, exc)
                await asyncio.sleep(delay)
        raise RuntimeError("Impossible de se connecter à RabbitMQ") from last_exc

    async def close(self) -> None:
        if self._connection:
            await self._connection.close()

    async def publish(self, routing_key: str, payload: dict) -> None:
        assert self._exchange, "EventBus non connecté"
        message = aio_pika.Message(
            body=json.dumps(payload).encode(),
            content_type="application/json",
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        )
        await self._exchange.publish(message, routing_key=routing_key)
        logger.debug("Événement publié: %s", routing_key)

    async def subscribe(
        self, queue_name: str, routing_keys: list[str], handler: Handler
    ) -> None:
        assert self._channel and self._exchange, "EventBus non connecté"
        queue = await self._channel.declare_queue(queue_name, durable=True)
        for key in routing_keys:
            await queue.bind(self._exchange, routing_key=key)

        async def _on_message(message: AbstractIncomingMessage) -> None:
            async with message.process():
                payload = json.loads(message.body.decode())
                await handler(message.routing_key or "", payload)

        await queue.consume(_on_message)
        logger.info("Abonné à %s sur la file %s", routing_keys, queue_name)


_bus: EventBus | None = None


def get_event_bus() -> EventBus:
    global _bus
    if _bus is None:
        _bus = EventBus()
    return _bus
