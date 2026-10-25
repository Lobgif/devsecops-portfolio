"""Badges AUTOMATIQUES et DYNAMIQUES des groupes.

Le classement est **relatif** et basé sur l'**activité récente (30 jours)** : un groupe
chaud aujourd'hui peut être dépassé demain. Aucun réglage manuel — tout est recalculé
à partir des discussions, réponses, réactions, de l'ancienneté et de la fraîcheur.
"""
from datetime import UTC, datetime

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Group

_DEFAULTS = {
    "badge_alaune_posts_week": 1000.0,     # « à la une » : très gros volume hebdo (top popularité)
    "badge_populaire_posts_week": 375.0,   # « populaire » : > 375 messages / semaine
    "badge_vedette_members": 100.0,        # « vedette » : > 100 membres
    "badge_reactif_posts_day": 50.0,       # « réactif » : > 50 réponses / jour
    "badge_actif_days": 7.0,               # « actif » : dernière activité <= N jours
    "badge_nouveau_days": 7.0,             # « nouveau » : créé il y a <= N jours
    "badge_max_per_group": 1.0,            # nb de badges affichés par groupe (1 par défaut)
}


async def _thresholds(session: AsyncSession) -> dict:
    """Lit les seuils des badges depuis site_settings (avec repli sur les défauts)."""
    out = dict(_DEFAULTS)
    try:
        rows = await session.execute(text(
            "SELECT key, value FROM public.site_settings WHERE key LIKE 'badge_%'"
        ))
        for k, v in rows.all():
            try:
                out[k] = float(v)
            except (TypeError, ValueError):
                pass
    except Exception:  # noqa: BLE001
        pass
    return out


async def compute_badges_map(session: AsyncSession) -> dict:
    """Badges de TOUS les groupes, sur des SEUILS ABSOLUS (configurables en admin).

    Un groupe peut cocher plusieurs critères, mais on n'affiche que les `badge_max_per_group`
    plus prestigieux (1 par défaut). Attribution 100% automatique selon l'activité.
    """
    groups = list(await session.scalars(select(Group)))
    if not groups:
        return {}
    cfg = await _thresholds(session)

    # Réponses par groupe sur 7 jours (semaine) et sur 1 jour (réactivité)
    rows_week = await session.execute(text(
        "SELECT d.group_id, count(p.id) FROM forum.posts p "
        "JOIN forum.discussions d ON p.discussion_id = d.id "
        "WHERE p.created_at > now() - interval '7 days' GROUP BY d.group_id"
    ))
    posts_week = {gid: n for gid, n in rows_week.all()}
    rows_day = await session.execute(text(
        "SELECT d.group_id, count(p.id) FROM forum.posts p "
        "JOIN forum.discussions d ON p.discussion_id = d.id "
        "WHERE p.created_at > now() - interval '1 day' GROUP BY d.group_id"
    ))
    posts_day = {gid: n for gid, n in rows_day.all()}

    now = datetime.now(UTC)

    def _age(g: Group) -> int:
        c = g.created_at
        if not c:
            return 9999
        if c.tzinfo is None:
            c = c.replace(tzinfo=UTC)
        return (now - c).days

    def _idle(g: Group) -> int:
        la = g.last_activity_at
        if not la:
            return 9999
        if la.tzinfo is None:
            la = la.replace(tzinfo=UTC)
        return (now - la).days

    max_badges = max(1, int(cfg.get("badge_max_per_group", 1)))
    out: dict = {}
    for g in groups:
        pw = posts_week.get(g.id, 0)
        pd = posts_day.get(g.id, 0)
        # Ordre de PRIORITÉ (le plus prestigieux d'abord) → on garde les N premiers
        ordered: list[str] = []
        if pw >= cfg["badge_alaune_posts_week"]:
            ordered.append("à la une")
        if (g.member_count or 0) >= cfg["badge_vedette_members"]:
            ordered.append("vedette")
        if pw >= cfg["badge_populaire_posts_week"]:
            ordered.append("populaire")
        if pd >= cfg["badge_reactif_posts_day"]:
            ordered.append("réactif")
        if _idle(g) <= cfg["badge_actif_days"] and pw > 0:
            ordered.append("actif")
        if _age(g) <= cfg["badge_nouveau_days"]:
            ordered.append("nouveau")
        out[g.id] = ordered[:max_badges]
    return out


# Compat : badges d'un seul groupe sans contexte (fallback léger, non relatif)
def compute_badges(group: Group) -> list[str]:
    now = datetime.now(UTC)
    created = group.created_at
    if created and created.tzinfo is None:
        created = created.replace(tzinfo=UTC)
    age_days = (now - created).days if created else 9999
    badges: list[str] = []
    if group.discussion_count >= 20:
        badges.append("réactif")
    if age_days <= 7:
        badges.append("nouveau")
    return badges[:2]
