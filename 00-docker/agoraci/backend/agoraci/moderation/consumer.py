"""Consumer de modération : analyse les contenus créés et signale les abus."""
from agoraci.common.messaging import get_event_bus

from .moderator import analyze


async def _handle_event(routing_key: str, payload: dict) -> None:
    content = payload.get("body", "") or payload.get("title", "")
    result = await analyze(content)
    if result["flagged"]:
        await get_event_bus().publish(
            "content.flagged",
            {"source_event": routing_key, "payload": payload, "analysis": result},
        )


async def start_moderation_consumer() -> None:
    await get_event_bus().subscribe(
        queue_name="moderation.content",
        routing_keys=["post.created", "discussion.created"],
        handler=_handle_event,
    )
