"""Routes transverses : paramètres du site, glossaire, classement, statistiques."""
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from agoraci.auth.models import User
from agoraci.common import get_session
from agoraci.common.auth_deps import CurrentUser, require_superadmin
from agoraci.forum.models import Discussion, Group, Post, Reputation
from agoraci.rag.providers import generate_answer
from agoraci.rag.quota import nanan_usage_today

from .models import Article, ContactMessage, GlossaryTerm, SiteSetting

router = APIRouter(prefix="/api", tags=["core"])


# --------------------------- Paramètres du site (dynamiques) ---------------------------
# Réglages « lourds » (markdown légal) exclus de /settings : ce dernier est chargé sur
# CHAQUE page (footer), or ces textes ne servent que sur les 3 pages légales. On les
# sert séparément via /settings/legal → payload SSR bien plus léger partout.
_LEGAL_SETTINGS = {"legal_cgu", "legal_privacy", "legal_mentions"}


@router.get("/settings")
async def get_settings_public(session: AsyncSession = Depends(get_session)):
    rows = await session.scalars(select(SiteSetting))
    return {s.key: s.value for s in rows if s.key not in _LEGAL_SETTINGS}


@router.get("/settings/legal")
async def get_legal_settings(session: AsyncSession = Depends(get_session)):
    """Textes légaux (CGU / confidentialité / mentions) — chargés uniquement par les pages dédiées."""
    rows = await session.scalars(select(SiteSetting))
    return {s.key: s.value for s in rows if s.key in _LEGAL_SETTINGS}


# --------------------------- Contact (formulaire public + admin) ---------------------------
class ContactIn(BaseModel):
    name: str = Field(default="", max_length=120)
    email: str = Field(min_length=3, max_length=255)
    subject: str = Field(default="", max_length=200)
    message: str = Field(min_length=5, max_length=5000)


@router.post("/contact", status_code=201)
async def send_contact(payload: ContactIn, session: AsyncSession = Depends(get_session)):
    """Enregistre un message du formulaire de contact public (consultable en admin)."""
    msg = ContactMessage(
        name=payload.name.strip(), email=payload.email.strip(),
        subject=payload.subject.strip(), message=payload.message.strip(),
    )
    session.add(msg)
    await session.commit()
    return {"ok": True}


@router.get("/admin/contact-messages")
async def list_contact_messages(
    _: CurrentUser = Depends(require_superadmin),
    session: AsyncSession = Depends(get_session),
):
    rows = await session.scalars(select(ContactMessage).order_by(ContactMessage.created_at.desc()))
    return [
        {"id": str(m.id), "name": m.name, "email": m.email, "subject": m.subject,
         "message": m.message, "status": m.status, "created_at": m.created_at}
        for m in rows
    ]


class ContactStatusIn(BaseModel):
    status: str = Field(pattern="^(new|read|archived)$")


@router.patch("/admin/contact-messages/{msg_id}")
async def update_contact_status(
    msg_id: uuid.UUID, payload: ContactStatusIn,
    _: CurrentUser = Depends(require_superadmin),
    session: AsyncSession = Depends(get_session),
):
    m = await session.get(ContactMessage, msg_id)
    if not m:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Message introuvable")
    m.status = payload.status
    await session.commit()
    return {"id": str(m.id), "status": m.status}


@router.delete("/admin/contact-messages/{msg_id}", status_code=204)
async def delete_contact_message(
    msg_id: uuid.UUID,
    _: CurrentUser = Depends(require_superadmin),
    session: AsyncSession = Depends(get_session),
):
    m = await session.get(ContactMessage, msg_id)
    if m:
        await session.delete(m)
        await session.commit()


@router.get("/admin/nanan-usage")
async def admin_nanan_usage(
    _: CurrentUser = Depends(require_superadmin),
    session: AsyncSession = Depends(get_session),
):
    """Consommation Nanan du jour (questions + utilisateurs) + limite configurée."""
    usage = await nanan_usage_today()
    row = await session.get(SiteSetting, "nanan_daily_limit")
    try:
        limit = int(row.value) if row and row.value else 15
    except (TypeError, ValueError):
        limit = 15
    return {**usage, "daily_limit": limit}


@router.put("/admin/settings")
async def update_settings(
    payload: dict,
    _: CurrentUser = Depends(require_superadmin),
    session: AsyncSession = Depends(get_session),
):
    """Met à jour les paramètres (upsert). Réservé au super-admin."""
    for key, value in payload.items():
        setting = await session.get(SiteSetting, key)
        if setting:
            setting.value = str(value)
        else:
            session.add(SiteSetting(key=key, value=str(value)))
    await session.commit()
    rows = await session.scalars(select(SiteSetting))
    return {s.key: s.value for s in rows}


# --------------------------- Glossaire ---------------------------
@router.get("/glossary")
async def list_glossary(category: str | None = None, session: AsyncSession = Depends(get_session)):
    q = select(GlossaryTerm).order_by(GlossaryTerm.term)
    if category and category != "Tous":
        q = q.where(GlossaryTerm.category == category)
    terms = await session.scalars(q)
    items = [{"id": str(t.id), "term": t.term, "category": t.category, "definition": t.definition} for t in terms]
    cats = sorted({i["category"] for i in items}) if not category else None
    return {"items": items, "categories": cats}


class GlossaryIn(BaseModel):
    term: str = Field(min_length=2, max_length=120)
    category: str = "Général"
    definition: str = Field(min_length=2)


@router.post("/admin/glossary", status_code=201)
async def create_term(payload: GlossaryIn, _: CurrentUser = Depends(require_superadmin),
                      session: AsyncSession = Depends(get_session)):
    term = GlossaryTerm(**payload.model_dump())
    session.add(term)
    await session.commit()
    await session.refresh(term)
    return {"id": str(term.id)}


@router.put("/admin/glossary/{term_id}")
async def update_term(term_id: uuid.UUID, payload: GlossaryIn,
                      _: CurrentUser = Depends(require_superadmin),
                      session: AsyncSession = Depends(get_session)):
    t = await session.get(GlossaryTerm, term_id)
    if not t:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Terme introuvable")
    t.term, t.category, t.definition = payload.term, payload.category, payload.definition
    await session.commit()
    return {"ok": True}


@router.delete("/admin/glossary/{term_id}", status_code=204)
async def delete_term(term_id: uuid.UUID, _: CurrentUser = Depends(require_superadmin),
                      session: AsyncSession = Depends(get_session)):
    t = await session.get(GlossaryTerm, term_id)
    if t:
        await session.delete(t)
        await session.commit()


# --------------------------- Actualités civiques ---------------------------
def _article_brief(a: Article) -> dict:
    return {"id": str(a.id), "title": a.title, "summary": a.summary, "category": a.category,
            "source": a.source, "published_at": a.published_at.isoformat() if a.published_at else None}


@router.get("/actualites")
async def list_articles(category: str | None = None, q: str | None = None,
                        session: AsyncSession = Depends(get_session)):
    query = select(Article).order_by(Article.published_at.desc().nullslast(), Article.created_at.desc())
    if category and category not in ("Tout", "Tous"):
        query = query.where(Article.category == category)
    if q and len(q) >= 2:
        like = func.unaccent(f"%{q}%")
        query = query.where(func.unaccent(Article.title).ilike(like) | func.unaccent(Article.summary).ilike(like))
    rows = await session.scalars(query)
    items = [_article_brief(a) for a in rows]
    cats = sorted(set(await session.scalars(select(Article.category))))
    return {"items": items, "categories": cats}


@router.get("/actualites/{article_id}")
async def get_article(article_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    a = await session.get(Article, article_id)
    if not a:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Article introuvable")
    return {**_article_brief(a), "content": a.content}


@router.post("/actualites/{article_id}/analyze")
async def analyze_article(article_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    """Analyse IA à la demande d'une actualité (impact pour le citoyen)."""
    a = await session.get(Article, article_id)
    if not a:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Article introuvable")
    question = (
        f"Analyse cette actualité juridique ivoirienne pour un citoyen : ce qui change concrètement, "
        f"qui est concerné, et les points de vigilance.\nTitre : {a.title}\n{a.summary}\n{a.content}"
    )
    from agoraci.rag.providers import LLMUnavailable
    try:
        answer = await generate_answer(question, [], mode="legal")
    except LLMUnavailable:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE,
                            "Analyse IA momentanément indisponible. Réessayez dans un instant.") from None
    return {"analysis": answer}


class ArticleIn(BaseModel):
    title: str = Field(min_length=3, max_length=255)
    summary: str = ""
    content: str = ""
    category: str = "Nouvelles lois"
    source: str = ""
    published_at: str | None = None


@router.post("/admin/actualites", status_code=201)
async def create_article(payload: ArticleIn, _: CurrentUser = Depends(require_superadmin),
                         session: AsyncSession = Depends(get_session)):
    from datetime import date as _date
    data = payload.model_dump()
    data["published_at"] = _date.fromisoformat(data["published_at"]) if data.get("published_at") else None
    a = Article(**data)
    session.add(a)
    await session.commit()
    await session.refresh(a)
    return {"id": str(a.id)}


@router.put("/admin/actualites/{article_id}")
async def update_article(article_id: uuid.UUID, payload: ArticleIn,
                         _: CurrentUser = Depends(require_superadmin),
                         session: AsyncSession = Depends(get_session)):
    from datetime import date as _date
    a = await session.get(Article, article_id)
    if not a:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Article introuvable")
    a.title, a.summary, a.content = payload.title, payload.summary, payload.content
    a.category, a.source = payload.category, payload.source
    a.published_at = _date.fromisoformat(payload.published_at) if payload.published_at else None
    await session.commit()
    return {"ok": True}


@router.delete("/admin/actualites/{article_id}", status_code=204)
async def delete_article(article_id: uuid.UUID, _: CurrentUser = Depends(require_superadmin),
                         session: AsyncSession = Depends(get_session)):
    a = await session.get(Article, article_id)
    if a:
        await session.delete(a)
        await session.commit()


# --------------------------- Classement (leaderboard) ---------------------------
@router.get("/community/leaderboard")
async def leaderboard(session: AsyncSession = Depends(get_session)):
    rows = await session.execute(
        select(Reputation.points, User.id, User.username, User.full_name, User.avatar_url)
        .join(User, User.id == Reputation.user_id)
        .where(Reputation.points > 0)
        .order_by(Reputation.points.desc())
        .limit(20)
    )
    return [
        {"rank": i + 1, "user_id": str(uid), "username": uname, "full_name": fn,
         "avatar_url": av, "points": pts}
        for i, (pts, uid, uname, fn, av) in enumerate(rows)
    ]


# --------------------------- Statistiques ---------------------------
async def _count(session, model) -> int:
    return await session.scalar(select(func.count()).select_from(model)) or 0


@router.get("/community/stats")
async def stats(session: AsyncSession = Depends(get_session)):
    by_cat = await session.execute(
        select(Group.category, func.count()).select_from(Group).group_by(Group.category)
    )
    ai_posts = await session.scalar(
        select(func.count()).select_from(Post).where(Post.is_ai.is_(True))
    ) or 0
    return {
        "users": await _count(session, User),
        "groups": await _count(session, Group),
        "discussions": await _count(session, Discussion),
        "posts": await _count(session, Post),
        "ai_answers": ai_posts,
        "by_category": [{"category": c, "count": n} for c, n in by_cat],
    }


@router.get("/admin/metrics")
async def admin_metrics(
    _: CurrentUser = Depends(require_superadmin), session: AsyncSession = Depends(get_session)
):
    """Tableau de bord AARRR — métriques ACTIONNABLES (Lean Startup), pas illusoires.
    Acquisition · Activation · Rétention · Engagement · Qualité · IA.
    """
    now = datetime.now(UTC)
    d7, d14, d30 = now - timedelta(days=7), now - timedelta(days=14), now - timedelta(days=30)

    async def n(stmt) -> int:
        return await session.scalar(stmt) or 0

    def active_union(since):
        # Utilisateurs distincts ayant créé une discussion OU une réponse humaine depuis `since`
        da = select(Discussion.author_id).where(Discussion.author_id.isnot(None), Discussion.created_at >= since)
        pa = select(Post.author_id).where(Post.author_id.isnot(None), Post.is_ai.is_(False), Post.created_at >= since)
        return select(func.count()).select_from(da.union(pa).subquery())

    total_users = await n(select(func.count()).select_from(User))
    # Activation : ont contribué au moins une fois (jamais borné dans le temps)
    da_all = select(Discussion.author_id).where(Discussion.author_id.isnot(None))
    pa_all = select(Post.author_id).where(Post.author_id.isnot(None), Post.is_ai.is_(False))
    activated = await n(select(func.count()).select_from(da_all.union(pa_all).subquery()))
    total_disc = await n(select(func.count()).select_from(Discussion))
    total_answers = await n(select(func.count()).select_from(Post).where(Post.is_ai.is_(False)))
    good_disc = await n(select(func.count(func.distinct(Post.discussion_id)))
                        .where(Post.is_ai.is_(False), Post.score > 0))
    ai_total = await n(select(func.count()).select_from(Post).where(Post.is_ai.is_(True)))
    ai_disc = await n(select(func.count(func.distinct(Post.discussion_id))).where(Post.is_ai.is_(True)))

    def pct(a, b):
        return round(100 * a / b, 1) if b else 0.0

    return {
        "acquisition": {
            "total_users": total_users,
            "new_7d": await n(select(func.count()).select_from(User).where(User.created_at >= d7)),
            "new_prev_7d": await n(select(func.count()).select_from(User).where(User.created_at >= d14, User.created_at < d7)),
        },
        "activation": {
            "activated_users": activated,
            "activation_rate_pct": pct(activated, total_users),
        },
        "retention": {
            "active_7d": await n(active_union(d7)),
            "active_30d": await n(active_union(d30)),
        },
        "engagement": {
            "questions": total_disc,
            "answers": total_answers,
            "questions_7d": await n(select(func.count()).select_from(Discussion).where(Discussion.created_at >= d7)),
            "answers_7d": await n(select(func.count()).select_from(Post).where(Post.is_ai.is_(False), Post.created_at >= d7)),
        },
        "quality": {
            "answered_rate_pct": pct(good_disc, total_disc),  # % de questions avec une réponse jugée bonne
            "questions_with_good_answer": good_disc,
        },
        "ai": {
            "nanan_answers": ai_total,
            "coverage_pct": pct(ai_disc, total_disc),  # % de questions où Nanan a été sollicité
        },
    }
