"""Exécuteur des décisions de modération.

Applique concrètement une action (`hide`, `delete`) sur un contenu, qu'elle vienne :
  - d'un vote communautaire (événement `moderation.decision`)
  - d'une résolution manuelle par un admin (appel direct depuis les routes)
"""
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from agoraci.common.db import get_engine
from agoraci.common.messaging import get_event_bus

from .models import ROLE_ADMIN, ROLE_CREATOR, ROLE_MEMBER, Group, GroupMembership, Post

logger = logging.getLogger("forum.executor")


async def apply_decision(session: AsyncSession, target_type: str, target_id, action: str,
                         group_id=None) -> bool:
    """Applique une décision de modération/gouvernance. Retourne True si appliquée."""
    if target_type == "post":
        post = await session.get(Post, target_id)
        if not post:
            return False
        if action == "delete":
            await session.delete(post)
        elif action == "hide":
            post.is_hidden = True
        else:
            return False
        return True
    # Décisions de gouvernance sur un membre (vote du groupe)
    if target_type == "user" and group_id:
        m = await session.scalar(select(GroupMembership).where(
            GroupMembership.group_id == group_id, GroupMembership.user_id == target_id
        ))
        # Retrait démocratique d'un membre (le fondateur est protégé)
        if action in ("remove_member", "ban"):
            if not m or m.role == ROLE_CREATOR:
                return False
            await session.delete(m)
            g = await session.get(Group, group_id)
            if g and (g.member_count or 0) > 0:
                g.member_count -= 1
            return True
        # Admission (groupe privé) : ajoute le membre si le vote l'approuve
        if action == "admit":
            if m:
                return True  # déjà membre
            session.add(GroupMembership(group_id=group_id, user_id=target_id, role=ROLE_MEMBER))
            g = await session.get(Group, group_id)
            if g:
                g.member_count = (g.member_count or 0) + 1
            return True
        # Élection : promeut un membre en modérateur (rôle admin de groupe)
        if action == "promote_mod":
            if m and m.role == ROLE_MEMBER:
                m.role = ROLE_ADMIN
                return True
            return False
    return False


async def _handle_decision(routing_key: str, payload: dict) -> None:
    maker = async_sessionmaker(get_engine(), expire_on_commit=False, class_=AsyncSession)
    async with maker() as session:
        ok = await apply_decision(
            session, payload.get("target_type"), payload.get("target_id"),
            payload.get("action"), payload.get("group_id"),
        )
        if ok:
            await session.commit()
            logger.info("Décision appliquée: %s sur %s %s",
                        payload.get("action"), payload.get("target_type"), payload.get("target_id"))


async def start_decision_consumer() -> None:
    await get_event_bus().subscribe(
        queue_name="forum.moderation.decision",
        routing_keys=["moderation.decision"],
        handler=_handle_decision,
    )


async def _sweep_scheduled_deletions() -> None:
    """Supprime les groupes dont le préavis de suppression est échu."""
    from datetime import UTC, datetime

    from .routes import purge_group  # import tardif (évite le cycle)
    maker = async_sessionmaker(get_engine(), expire_on_commit=False, class_=AsyncSession)
    async with maker() as session:
        due = list(await session.scalars(
            select(Group.id).where(Group.deletion_at.isnot(None), Group.deletion_at <= datetime.now(UTC))
        ))
        for gid in due:
            await purge_group(session, gid)
        if due:
            await session.commit()
            logger.info("Balayage : %d groupe(s) supprimé(s) après préavis.", len(due))


async def start_deletion_sweeper() -> None:
    """Tâche de fond : vérifie chaque heure les suppressions programmées échues."""
    import asyncio

    async def _loop():
        while True:
            try:
                await _sweep_scheduled_deletions()
            except Exception as exc:  # noqa: BLE001
                logger.error("Balayage suppression échoué: %s", exc)
            await asyncio.sleep(3600)  # toutes les heures

    asyncio.create_task(_loop())
