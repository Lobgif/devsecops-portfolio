"""Routes du service Forum."""
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from agoraci.auth.models import User
from agoraci.common import get_session
from agoraci.common.auth_deps import (
    CurrentUser,
    get_current_user,
    get_optional_user,
    require_superadmin,
)
from agoraci.common.messaging import get_event_bus
from agoraci.rag.providers import generate_answer
from agoraci.rag.quota import bump_nanan_quota, check_nanan_quota
from agoraci.rag.routes import _hybrid_search

from .badges import compute_badges, compute_badges_map
from .executor import apply_decision
from .models import (
    ROLE_ADMIN,
    ROLE_CREATOR,
    ROLE_MEMBER,
    Discussion,
    Follow,
    Group,
    GroupMembership,
    GroupProposal,
    GroupProposalSupport,
    ModerationProposal,
    ModerationVote,
    Post,
    Report,
    Reputation,
    Vote,
)
from .schemas import (
    AddAdminRequest,
    DiscussionCreate,
    DiscussionOut,
    GroupCreate,
    GroupOut,
    PostCreate,
    PostOut,
    ProposalCreate,
    ProposalOut,
    ProposalVote,
    ReputationOut,
    VoteCreate,
)

router = APIRouter(prefix="/api/forum", tags=["forum"])


# --------------------------- Helpers ---------------------------
def _to_group_out(g: Group, badges: list[str] | None = None, my_role: str | None = None,
                  preview: list[dict] | None = None) -> GroupOut:
    b = badges if badges is not None else compute_badges(g)
    upd: dict = {"badges": b, "my_role": my_role}
    if preview is not None:
        upd["preview_members"] = preview
    return GroupOut.model_validate(g).model_copy(update=upd)


async def _preview_members_map(
    session: AsyncSession, group_ids: list[uuid.UUID], per_group: int = 3
) -> dict[uuid.UUID, list[dict]]:
    """Jusqu'à `per_group` membres par groupe (creator/admin d'abord) → avatars empilés."""
    if not group_ids:
        return {}
    rows = await session.execute(
        select(GroupMembership.group_id, User.username, User.avatar_url)
        .join(User, User.id == GroupMembership.user_id)
        .where(GroupMembership.group_id.in_(group_ids))
        .order_by(GroupMembership.role, GroupMembership.joined_at)
    )
    out: dict[uuid.UUID, list[dict]] = {}
    for gid, username, avatar_url in rows:
        bucket = out.setdefault(gid, [])
        if len(bucket) < per_group:
            bucket.append({"username": username, "avatar_url": avatar_url})
    return out


async def _role_in_group(session: AsyncSession, group_id: uuid.UUID, user_id: str) -> str | None:
    return await session.scalar(
        select(GroupMembership.role).where(
            GroupMembership.group_id == group_id, GroupMembership.user_id == user_id
        )
    )


async def _ensure_group_access(session: AsyncSession, group: Group, request: Request) -> None:
    """Pour un groupe privé : exige d'en être membre (sinon 403)."""
    if not group.is_private:
        return
    user = await get_optional_user(request)
    if not user or not await _role_in_group(session, group.id, user.id):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Groupe privé : contenu réservé aux membres.")


async def _add_points(session: AsyncSession, user_id: uuid.UUID, delta: int) -> None:
    rep = await session.get(Reputation, user_id)
    if rep is None:
        rep = Reputation(user_id=user_id, points=max(0, delta))
        session.add(rep)
    else:
        rep.points = max(0, rep.points + delta)


# --------------------------- Groupes ---------------------------
@router.get("/groups", response_model=list[GroupOut])
async def list_groups(request: Request, session: AsyncSession = Depends(get_session)):
    groups = list(await session.scalars(
        select(Group).order_by(Group.is_featured.desc(), Group.last_activity_at.desc())
    ))
    # Masque les groupes privés sauf à leurs membres
    member_ids: set = set()
    user = await get_optional_user(request)
    if user:
        member_ids = set(await session.scalars(
            select(GroupMembership.group_id).where(GroupMembership.user_id == uuid.UUID(user.id))
        ))
    visible = [g for g in groups if not g.is_private or g.id in member_ids]
    badge_map = await compute_badges_map(session)
    preview_map = await _preview_members_map(session, [g.id for g in visible])
    return [_to_group_out(g, badge_map.get(g.id, []), preview=preview_map.get(g.id, [])) for g in visible]


@router.get("/search")
async def search(q: str, session: AsyncSession = Depends(get_session)):
    """Recherche globale (groupes, discussions, réponses) — insensible aux accents."""
    q = (q or "").strip()
    if len(q) < 2:
        return {"groups": [], "discussions": [], "posts": []}
    like = func.unaccent(f"%{q}%")

    groups = await session.scalars(
        select(Group)
        .where(func.unaccent(Group.name).ilike(like) | func.unaccent(Group.description).ilike(like))
        .limit(8)
    )
    discussions = await session.scalars(
        select(Discussion)
        .where(func.unaccent(Discussion.title).ilike(like) | func.unaccent(Discussion.body).ilike(like))
        .order_by(Discussion.created_at.desc())
        .limit(12)
    )
    posts = await session.scalars(
        select(Post)
        .where(func.unaccent(Post.body).ilike(like), Post.is_hidden.is_(False))
        .order_by(Post.score.desc())
        .limit(12)
    )
    return {
        "groups": [{"id": str(g.id), "name": g.name, "category": g.category} for g in groups],
        "discussions": [
            {"id": str(d.id), "title": d.title, "group_id": str(d.group_id),
             "excerpt": d.body[:160]} for d in discussions
        ],
        "posts": [
            {"id": str(p.id), "discussion_id": str(p.discussion_id),
             "excerpt": p.body[:160], "is_ai": p.is_ai} for p in posts
        ],
    }


@router.get("/group/{group_id}", response_model=GroupOut)
async def get_group(group_id: uuid.UUID, request: Request, session: AsyncSession = Depends(get_session)):
    group = await session.get(Group, group_id)
    if not group:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Groupe introuvable")
    # Le détail (nom/description) reste visible (permet de rejoindre via lien) ;
    # seules les discussions sont protégées pour les groupes privés.
    badge_map = await compute_badges_map(session)
    user = await get_optional_user(request)
    my_role = await _role_in_group(session, group_id, user.id) if user else None
    return _to_group_out(group, badge_map.get(group.id, []), my_role)


async def _setting_float(session: AsyncSession, key: str, default: float) -> float:
    """Lit un paramètre numérique depuis site_settings (repli sur le défaut)."""
    try:
        r = await session.execute(
            text("SELECT value FROM public.site_settings WHERE key = :k"), {"k": key}
        )
        v = r.scalar_one_or_none()
        return float(v) if v is not None else default
    except Exception:  # noqa: BLE001
        return default


@router.post("/groups", response_model=GroupOut, status_code=201)
async def create_group(
    payload: GroupCreate,
    current: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    # Création DIRECTE réservée (gouvernance) : super-admin, expert vérifié, ou haute réputation.
    # Les autres doivent passer par une PROPOSITION (créée au seuil de soutiens).
    user = await session.get(User, uuid.UUID(current.id))
    allowed = bool(user and (user.is_superadmin or user.expert_status == "approved"))
    if not allowed:
        min_rep = await _setting_float(session, "group_direct_creation_min_rep", 0)
        if min_rep > 0:
            rep = await session.scalar(
                select(Reputation.points).where(Reputation.user_id == uuid.UUID(current.id))
            ) or 0
            allowed = rep >= min_rep
    if not allowed:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "La création directe est réservée. Proposez un groupe : il sera créé automatiquement "
            "quand il atteindra le seuil de soutiens.",
        )
    if await session.scalar(select(Group.id).where(Group.name == payload.name.strip())):
        raise HTTPException(status.HTTP_409_CONFLICT, "Un groupe porte déjà ce nom.")
    group = Group(**payload.model_dump(), created_by=uuid.UUID(current.id))
    session.add(group)
    await session.flush()
    session.add(GroupMembership(group_id=group.id, user_id=uuid.UUID(current.id), role=ROLE_CREATOR))
    await session.commit()
    await session.refresh(group)
    return _to_group_out(group)


# --------------------------- Propositions de groupe (gouvernance) ---------------------------
class ProposeGroup(BaseModel):
    name: str = Field(min_length=3, max_length=120)
    category: str = Field(min_length=2, max_length=60)
    description: str = Field(default="", max_length=2000)
    motivation: str = Field(default="", max_length=2000)


@router.post("/group-proposals", status_code=201)
async def propose_group(
    payload: ProposeGroup,
    current: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Propose la création d'un groupe. Créé automatiquement au seuil de soutiens."""
    user = await session.get(User, uuid.UUID(current.id))
    if not user or not user.is_verified:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Compte vérifié requis pour proposer un groupe.")
    name = payload.name.strip()
    if await session.scalar(select(Group.id).where(Group.name == name)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Un groupe porte déjà ce nom.")
    if await session.scalar(
        select(GroupProposal.id).where(GroupProposal.name == name, GroupProposal.status == "open")
    ):
        raise HTTPException(status.HTTP_409_CONFLICT, "Une proposition ouverte porte déjà ce nom — soutenez-la !")
    prop = GroupProposal(
        name=name, category=payload.category.strip(), description=payload.description.strip(),
        motivation=payload.motivation.strip(), proposed_by=user.id, support_count=1,
    )
    session.add(prop)
    await session.flush()
    session.add(GroupProposalSupport(proposal_id=prop.id, user_id=user.id))  # le proposeur soutient
    await session.commit()
    return {"id": str(prop.id), "support_count": 1}


@router.get("/group-proposals")
async def list_group_proposals(
    current: CurrentUser | None = Depends(get_optional_user),
    session: AsyncSession = Depends(get_session),
):
    threshold = int(await _setting_float(session, "group_creation_threshold", 30))
    props = list(await session.scalars(
        select(GroupProposal).where(GroupProposal.status == "open")
        .order_by(GroupProposal.support_count.desc(), GroupProposal.created_at.desc())
    ))
    supported: set = set()
    if current:
        supported = set(await session.scalars(
            select(GroupProposalSupport.proposal_id).where(GroupProposalSupport.user_id == uuid.UUID(current.id))
        ))
    return {
        "threshold": threshold,
        "proposals": [{
            "id": str(p.id), "name": p.name, "category": p.category,
            "description": p.description, "motivation": p.motivation,
            "support_count": p.support_count, "supported": p.id in supported,
        } for p in props],
    }


@router.post("/group-proposals/{proposal_id}/support")
async def support_proposal(
    proposal_id: uuid.UUID,
    current: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Soutient une proposition. Au seuil atteint → le groupe est créé automatiquement."""
    user = await session.get(User, uuid.UUID(current.id))
    if not user or not user.is_verified:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Compte vérifié requis.")
    prop = await session.get(GroupProposal, proposal_id)
    if not prop or prop.status != "open":
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Proposition introuvable ou déjà clôturée.")
    if await session.scalar(select(GroupProposalSupport.id).where(
        GroupProposalSupport.proposal_id == proposal_id, GroupProposalSupport.user_id == user.id
    )):
        return {"support_count": prop.support_count, "already": True, "created_group_id": None}

    session.add(GroupProposalSupport(proposal_id=proposal_id, user_id=user.id))
    prop.support_count += 1
    threshold = int(await _setting_float(session, "group_creation_threshold", 30))
    created_group_id = None
    if prop.support_count >= threshold:
        group = Group(
            name=prop.name, category=prop.category, description=prop.description,
            created_by=prop.proposed_by, member_count=0,
        )
        session.add(group)
        await session.flush()
        supporter_ids = set(await session.scalars(
            select(GroupProposalSupport.user_id).where(GroupProposalSupport.proposal_id == proposal_id)
        ))
        supporter_ids.add(user.id)  # le soutien courant (pas encore commité)
        for uid in supporter_ids:
            role = ROLE_CREATOR if uid == prop.proposed_by else ROLE_MEMBER
            session.add(GroupMembership(group_id=group.id, user_id=uid, role=role))
        group.member_count = len(supporter_ids)
        prop.status = "created"
        prop.created_group_id = group.id
        created_group_id = group.id
    await session.commit()
    return {
        "support_count": prop.support_count,
        "created_group_id": str(created_group_id) if created_group_id else None,
    }


@router.post("/groups/{group_id}/join", status_code=201)
async def join_group(
    group_id: uuid.UUID,
    current: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    if await _role_in_group(session, group_id, current.id):
        return {"message": "Déjà membre"}
    group = await session.get(Group, group_id)
    if not group:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Groupe introuvable")
    # Groupe PRIVÉ : l'adhésion est soumise au VOTE des membres (proposition d'admission).
    if group.is_private:
        existing = await session.scalar(select(ModerationProposal.id).where(
            ModerationProposal.group_id == group_id,
            ModerationProposal.target_id == uuid.UUID(current.id),
            ModerationProposal.action == "admit", ModerationProposal.status == "open",
        ))
        if existing:
            return {"message": "Demande déjà en attente de vote.", "pending": True}
        session.add(ModerationProposal(
            group_id=group_id, target_type="user", target_id=uuid.UUID(current.id),
            action="admit", proposed_by=uuid.UUID(current.id),
        ))
        await session.commit()
        return {"message": "Demande d'admission envoyée — soumise au vote des membres.", "pending": True}
    # Groupe public : adhésion directe.
    session.add(GroupMembership(group_id=group_id, user_id=uuid.UUID(current.id), role=ROLE_MEMBER))
    group.member_count += 1
    await session.commit()
    return {"message": "Adhésion réussie"}


@router.post("/groups/{group_id}/admins", status_code=201)
async def add_admin(
    group_id: uuid.UUID,
    payload: AddAdminRequest,
    current: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Le créateur (ou un admin) peut promouvoir un membre en administrateur."""
    role = await _role_in_group(session, group_id, current.id)
    if role not in (ROLE_CREATOR, ROLE_ADMIN):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Réservé au créateur ou aux admins du groupe")

    membership = await session.scalar(
        select(GroupMembership).where(
            GroupMembership.group_id == group_id, GroupMembership.user_id == payload.user_id
        )
    )
    if not membership:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "L'utilisateur n'est pas membre du groupe")
    membership.role = ROLE_ADMIN
    await session.commit()
    return {"message": "Administrateur ajouté", "user_id": str(payload.user_id)}


@router.get("/groups/{group_id}/members")
async def list_members(
    group_id: uuid.UUID,
    current: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Liste des membres du groupe — réservée au créateur / admins (ou super-admin)."""
    role = await _role_in_group(session, group_id, current.id)
    if role not in (ROLE_CREATOR, ROLE_ADMIN) and not current.is_superadmin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Réservé aux administrateurs du groupe")
    rows = await session.execute(
        select(GroupMembership, User)
        .join(User, User.id == GroupMembership.user_id)
        .where(GroupMembership.group_id == group_id)
        .order_by(GroupMembership.role, GroupMembership.joined_at)
    )
    return [
        {
            "user_id": str(u.id), "username": u.username, "full_name": u.full_name,
            "avatar_url": u.avatar_url, "role": m.role, "is_creator": m.role == ROLE_CREATOR,
        }
        for m, u in rows
    ]


@router.get("/groups/{group_id}/members/list")
async def list_members_public(
    group_id: uuid.UUID, request: Request, session: AsyncSession = Depends(get_session)
):
    """Liste des membres pour affichage (bouton « Membres ») — gardée aux membres si groupe privé."""
    group = await session.get(Group, group_id)
    if not group:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Groupe introuvable")
    await _ensure_group_access(session, group, request)
    rows = await session.execute(
        select(GroupMembership, User)
        .join(User, User.id == GroupMembership.user_id)
        .where(GroupMembership.group_id == group_id)
        .order_by(GroupMembership.role, GroupMembership.joined_at)
    )
    return [
        {"user_id": str(u.id), "username": u.username, "full_name": u.full_name,
         "avatar_url": u.avatar_url, "role": m.role}
        for m, u in rows
    ]


# --------------------------- Espace personnel ---------------------------
@router.get("/me/discussions")
async def my_discussions(
    current: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Discussions lancées par l'utilisateur courant (« Mes discussions »)."""
    rows = await session.execute(
        select(Discussion, Group.name)
        .join(Group, Group.id == Discussion.group_id)
        .where(Discussion.author_id == uuid.UUID(current.id))
        .order_by(Discussion.created_at.desc())
        .limit(100)
    )
    return [
        {"id": str(d.id), "title": d.title, "group_id": str(d.group_id),
         "group_name": gname, "excerpt": d.body[:180], "created_at": d.created_at}
        for d, gname in rows
    ]


@router.get("/me/posts")
async def my_posts(
    current: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Réponses écrites par l'utilisateur courant (« Mes réponses »)."""
    rows = await session.execute(
        select(Post, Discussion.title, Discussion.group_id)
        .join(Discussion, Discussion.id == Post.discussion_id)
        .where(Post.author_id == uuid.UUID(current.id), Post.is_ai.is_(False))
        .order_by(Post.created_at.desc())
        .limit(100)
    )
    return [
        {"id": str(p.id), "discussion_id": str(p.discussion_id), "discussion_title": title,
         "group_id": str(gid), "excerpt": p.body[:200], "score": p.score,
         "is_hidden": p.is_hidden, "created_at": p.created_at}
        for p, title, gid in rows
    ]


@router.get("/me/follows")
async def my_follows(
    current: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Favoris : groupes et discussions suivis par l'utilisateur courant."""
    uid = uuid.UUID(current.id)
    follows = list(await session.scalars(
        select(Follow).where(Follow.user_id == uid).order_by(Follow.created_at.desc())
    ))
    group_ids = [f.target_id for f in follows if f.target_type == "group"]
    disc_ids = [f.target_id for f in follows if f.target_type == "discussion"]
    groups = {g.id: g for g in (await session.scalars(
        select(Group).where(Group.id.in_(group_ids))) if group_ids else [])}
    discs: dict = {}
    if disc_ids:
        rows = await session.execute(
            select(Discussion, Group.name).join(Group, Group.id == Discussion.group_id)
            .where(Discussion.id.in_(disc_ids))
        )
        discs = {d.id: (d, gname) for d, gname in rows}
    out_groups, out_discs = [], []
    for f in follows:
        if f.target_type == "group" and f.target_id in groups:
            g = groups[f.target_id]
            out_groups.append({
                "id": str(g.id), "name": g.name, "category": g.category,
                "description": g.description, "member_count": g.member_count,
                "discussion_count": g.discussion_count, "is_private": g.is_private,
                "last_activity_at": g.last_activity_at, "badges": [], "preview_members": [],
            })
        elif f.target_type == "discussion" and f.target_id in discs:
            d, gname = discs[f.target_id]
            out_discs.append({"id": str(d.id), "title": d.title,
                              "group_id": str(d.group_id), "group_name": gname})
    return {"groups": out_groups, "discussions": out_discs}


@router.get("/feed")
async def feed(
    request: Request,
    sort: str = "recent",
    limit: int = 20,
    session: AsyncSession = Depends(get_session),
):
    """Fil de discussions pour le tableau de bord.
    sort = recent (défaut) | trending (plus de réponses) | foryou (mes groupes)."""
    limit = max(1, min(limit, 50))
    user = await get_optional_user(request)
    member_ids: set = set()
    if user:
        member_ids = set(await session.scalars(
            select(GroupMembership.group_id).where(GroupMembership.user_id == uuid.UUID(user.id))
        ))

    # Nombre de réponses (non masquées) par discussion.
    ans = (
        select(Post.discussion_id.label("did"), func.count().label("n"))
        .where(Post.is_hidden.is_(False))
        .group_by(Post.discussion_id)
        .subquery()
    )
    n_answers = func.coalesce(ans.c.n, 0)
    stmt = (
        select(Discussion, Group.name, Group.category, Group.is_private,
               User.username, User.avatar_url, User.full_name, User.display_pref, n_answers)
        .join(Group, Group.id == Discussion.group_id)
        .join(User, User.id == Discussion.author_id)
        .outerjoin(ans, ans.c.did == Discussion.id)
        # masque les discussions des groupes privés dont on n'est pas membre
        .where((Group.is_private.is_(False)) | (Group.id.in_(member_ids) if member_ids else Group.is_private.is_(False)))
    )
    if sort == "foryou":
        stmt = stmt.where(Group.id.in_(member_ids)) if member_ids else stmt.where(Discussion.id.is_(None))
    if sort == "trending":
        stmt = stmt.order_by(n_answers.desc(), Discussion.created_at.desc())
    else:
        stmt = stmt.order_by(Discussion.created_at.desc())
    rows = await session.execute(stmt.limit(limit))
    return [
        {
            "id": str(d.id), "title": d.title, "excerpt": d.body[:220],
            "group_id": str(d.group_id), "group_name": gname, "category": cat,
            "author": {"username": uname, "avatar_url": avatar,
                       "display_name": displayName_py(uname, fname, pref)},
            "answer_count": int(n), "created_at": d.created_at,
        }
        for d, gname, cat, _priv, uname, avatar, fname, pref, n in rows
    ]


def displayName_py(username: str, full_name: str | None, pref: str | None) -> str:
    """Nom d'affichage côté API (miroir de utils/display.ts)."""
    if pref == "fullname" and full_name:
        return full_name
    if pref == "firstname" and full_name:
        return full_name.split(" ")[0]
    return username


class SetRoleRequest(BaseModel):
    role: str = Field(pattern="^(member|admin)$")


@router.post("/groups/{group_id}/members/{user_id}/role")
async def set_member_role(
    group_id: uuid.UUID,
    user_id: uuid.UUID,
    payload: SetRoleRequest,
    current: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Promouvoir/rétrograder un membre (creator↔admin↔member). Pas de bannissement ici :
    l'exclusion passe par le vote communautaire ou le super-admin."""
    role = await _role_in_group(session, group_id, current.id)
    if role not in (ROLE_CREATOR, ROLE_ADMIN) and not current.is_superadmin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Réservé aux administrateurs du groupe")
    membership = await session.scalar(
        select(GroupMembership).where(
            GroupMembership.group_id == group_id, GroupMembership.user_id == user_id
        )
    )
    if not membership:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Membre introuvable")
    if membership.role == ROLE_CREATOR:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Le rôle du créateur ne peut pas changer")
    membership.role = payload.role
    await session.commit()
    return {"user_id": str(user_id), "role": membership.role}


# --------------------------- Discussions & posts ---------------------------
@router.post("/discussions", response_model=DiscussionOut, status_code=201)
async def create_discussion(
    payload: DiscussionCreate,
    current: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    discussion = Discussion(**payload.model_dump(), author_id=uuid.UUID(current.id))
    session.add(discussion)
    group = await session.get(Group, payload.group_id)
    if group:
        group.discussion_count += 1
        group.last_activity_at = func.now()
    await session.commit()
    await session.refresh(discussion)
    await get_event_bus().publish(
        "discussion.created",
        {"discussion_id": str(discussion.id), "group_id": str(discussion.group_id),
         "author_id": current.id, "title": discussion.title, "body": discussion.body},
    )
    return discussion


@router.get("/discussions/{group_id}", response_model=list[DiscussionOut])
async def list_discussions(
    group_id: uuid.UUID, request: Request, limit: int = 10, offset: int = 0,
    session: AsyncSession = Depends(get_session),
):
    group = await session.get(Group, group_id)
    if group:
        await _ensure_group_access(session, group, request)
    limit = max(1, min(limit, 50))
    return list(await session.scalars(
        select(Discussion).where(Discussion.group_id == group_id)
        .order_by(Discussion.created_at.desc()).limit(limit).offset(offset)
    ))


@router.post("/posts", response_model=PostOut, status_code=201)
async def create_post(
    payload: PostCreate,
    current: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    post = Post(
        discussion_id=payload.discussion_id,
        body=payload.body,
        is_ai=payload.is_ai,
        author_id=None if payload.is_ai else uuid.UUID(current.id),
    )
    session.add(post)
    # Remonte l'activité du groupe parent + récupère l'auteur de la discussion (notif)
    disc = await session.get(Discussion, payload.discussion_id)
    if disc:
        group = await session.get(Group, disc.group_id)
        if group:
            group.last_activity_at = func.now()
    await session.commit()
    await session.refresh(post)
    await get_event_bus().publish(
        "post.created",
        {
            "post_id": str(post.id),
            "discussion_id": str(payload.discussion_id),
            "discussion_author_id": str(disc.author_id) if disc else None,
            "author_id": None if post.is_ai else current.id,
            "is_ai": post.is_ai,
            "body": post.body,
        },
    )
    return post


@router.get("/discussion/{discussion_id}")
async def get_discussion(discussion_id: uuid.UUID, request: Request, session: AsyncSession = Depends(get_session)):
    """Détail d'une discussion + ses réponses (triées : meilleures d'abord)."""
    disc = await session.get(Discussion, discussion_id)
    if not disc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Discussion introuvable")
    grp = await session.get(Group, disc.group_id)
    if grp:
        await _ensure_group_access(session, grp, request)
    posts = list(await session.scalars(
        select(Post)
        .where(Post.discussion_id == discussion_id, Post.is_hidden.is_(False))
        .order_by(Post.is_ai.desc(), Post.score.desc(), Post.created_at)
    ))
    # Récupère les noms d'auteurs (discussion + réponses humaines)
    author_ids = {disc.author_id} | {p.author_id for p in posts if p.author_id}
    names: dict = {}
    if author_ids:
        rows = await session.execute(
            select(User.id, User.username, User.avatar_url).where(User.id.in_(author_ids))
        )
        names = {uid: (uname, avatar) for uid, uname, avatar in rows}

    def post_dict(p: Post) -> dict:
        d = PostOut.model_validate(p).model_dump()
        d["author_id"] = str(p.author_id) if p.author_id else None
        d["author_username"] = names.get(p.author_id, (None, None))[0] if p.author_id else None
        d["author_avatar"] = names.get(p.author_id, (None, None))[1] if p.author_id else None
        d["created_at"] = p.created_at
        return d

    return {
        "id": str(disc.id),
        "group_id": str(disc.group_id),
        "title": disc.title,
        "body": disc.body,
        "author_id": str(disc.author_id),
        "author_username": names.get(disc.author_id, (None, None))[0],
        "author_avatar": names.get(disc.author_id, (None, None))[1],
        "created_at": disc.created_at,
        "posts": [post_dict(p) for p in posts],
    }


class PostUpdate(BaseModel):
    body: str = Field(min_length=1)


class DiscussionUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1)
    body: str | None = Field(default=None, min_length=1)


@router.put("/posts/{post_id}", response_model=PostOut)
async def update_post(
    post_id: uuid.UUID, payload: PostUpdate,
    current: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    post = await session.get(Post, post_id)
    if not post:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Réponse introuvable")
    if post.is_ai or str(post.author_id) != current.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Vous ne pouvez modifier que vos propres réponses.")
    post.body = payload.body
    await session.commit()
    await session.refresh(post)
    return post


@router.delete("/posts/{post_id}")
async def delete_post(
    post_id: uuid.UUID,
    current: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    post = await session.get(Post, post_id)
    if not post:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Réponse introuvable")
    if str(post.author_id) != current.id and not current.is_superadmin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Action non autorisée.")
    await session.execute(text("DELETE FROM forum.votes WHERE post_id = :p"), {"p": str(post_id)})
    await session.execute(text("DELETE FROM forum.reports WHERE post_id = :p"), {"p": str(post_id)})
    await session.delete(post)
    await session.commit()
    return {"deleted": str(post_id)}


@router.put("/discussions/{discussion_id}", response_model=DiscussionOut)
async def update_discussion(
    discussion_id: uuid.UUID, payload: DiscussionUpdate,
    current: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    disc = await session.get(Discussion, discussion_id)
    if not disc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Discussion introuvable")
    if str(disc.author_id) != current.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Vous ne pouvez modifier que vos propres discussions.")
    if payload.title is not None:
        disc.title = payload.title
    if payload.body is not None:
        disc.body = payload.body
    await session.commit()
    await session.refresh(disc)
    return disc


@router.delete("/discussions/{discussion_id}")
async def delete_discussion(
    discussion_id: uuid.UUID,
    current: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    disc = await session.get(Discussion, discussion_id)
    if not disc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Discussion introuvable")
    if str(disc.author_id) != current.id and not current.is_superadmin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Action non autorisée.")
    d = str(discussion_id)
    for stmt in [
        "DELETE FROM forum.votes WHERE post_id IN (SELECT id FROM forum.posts WHERE discussion_id = :d)",
        "DELETE FROM forum.reports WHERE post_id IN (SELECT id FROM forum.posts WHERE discussion_id = :d)",
        "DELETE FROM forum.posts WHERE discussion_id = :d",
        "DELETE FROM forum.follows WHERE target_type = 'discussion' AND target_id = :d",
        "DELETE FROM forum.discussions WHERE id = :d",
    ]:
        await session.execute(text(stmt), {"d": d})
    grp = await session.get(Group, disc.group_id)
    if grp and grp.discussion_count > 0:
        grp.discussion_count -= 1
    await session.commit()
    return {"deleted": d}


@router.post("/posts/{post_id}/report", status_code=202)
async def report_post(
    post_id: uuid.UUID,
    current: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Signale un contenu (déclenche la chaîne de modération)."""
    post = await session.get(Post, post_id)
    if not post:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Post introuvable")
    # Persiste le signalement (file de modération humaine), en évitant les doublons ouverts
    existing = await session.scalar(
        select(Report).where(
            Report.post_id == post_id,
            Report.reporter_id == uuid.UUID(current.id),
            Report.status == "open",
        )
    )
    if not existing:
        session.add(Report(post_id=post_id, reporter_id=uuid.UUID(current.id)))
        await session.commit()
    await get_event_bus().publish(
        "content.flagged",
        {"source_event": "user.report", "post_id": str(post_id),
         "reporter": current.id, "body": post.body, "analysis": {"reported_by_user": True}},
    )
    return {"message": "Signalement enregistré, merci."}


@router.post("/discussions/{discussion_id}/ai-answer", response_model=PostOut, status_code=201)
async def ai_answer(
    discussion_id: uuid.UUID,
    request: Request,
    current: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Génère une réponse IA (RAG) à la question et l'ajoute comme réponse."""
    disc = await session.get(Discussion, discussion_id)
    if not disc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Discussion introuvable")
    await check_nanan_quota(request, session, current.id)  # quota quotidien Nanan
    question = f"{disc.title}\n{disc.body}"
    chunks = await _hybrid_search(session, question, 5)
    passages = [
        {"content": c.content, "code_source": c.code_source, "numero_article": c.numero_article}
        for c in chunks
    ]
    # Nanan adapte son mode à la CATÉGORIE du groupe : droit -> juridique, sinon général.
    group = await session.get(Group, disc.group_id)
    cat = (group.category or "").lower() if group else ""
    mode = "legal" if any(k in cat for k in ("droit", "juridiqu", "loi", "justice", "légal", "legal")) else "general"
    from agoraci.rag.providers import LLMUnavailable
    try:
        answer = await generate_answer(question, passages, mode=mode)
    except LLMUnavailable:
        # On NE crée PAS de post « indisponible » : juste une erreur transitoire
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE,
                            "Nanan est momentanément indisponible. Réessayez dans un instant.") from None
    await bump_nanan_quota(request, session, current.id)  # ne compte que les réponses réussies
    post = Post(discussion_id=disc.id, is_ai=True, author_id=None, body=answer)
    session.add(post)
    await session.commit()
    await session.refresh(post)
    return post


# --------------------------- Votes & points ---------------------------
@router.post("/votes")
async def vote(
    payload: VoteCreate,
    current: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    post = await session.get(Post, payload.post_id)
    if not post:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Post introuvable")

    existing = await session.scalar(
        select(Vote).where(Vote.post_id == payload.post_id, Vote.user_id == uuid.UUID(current.id))
    )
    old = existing.value if existing else 0
    if existing:
        existing.value = payload.value
    else:
        session.add(Vote(post_id=payload.post_id, user_id=uuid.UUID(current.id), value=payload.value))

    # Recalcule likes/dislikes/score à partir du delta
    def apply(delta_like: int, delta_dislike: int) -> None:
        post.likes += delta_like
        post.dislikes += delta_dislike

    if old == 1:
        apply(-1, 0)
    elif old == -1:
        apply(0, -1)
    if payload.value == 1:
        apply(1, 0)
    elif payload.value == -1:
        apply(0, 1)
    post.score = post.likes - post.dislikes

    # Réputation de l'auteur : +1 par like net gagné (système de points par réponse)
    if post.author_id:
        gained = (1 if payload.value == 1 else 0) - (1 if old == 1 else 0)
        await _add_points(session, post.author_id, gained)

    await session.commit()

    # Enrichissement RAG : indexe la réponse SEULEMENT si elle passe des critères de QUALITÉ
    # (pas seulement populaire) : score NET suffisant, non masquée, aucun signalement ouvert.
    import os
    threshold = int(os.getenv("COMMUNITY_INDEX_MIN_SCORE", "3"))
    # Les réponses d'un EXPERT VÉRIFIÉ pèsent plus → seuil abaissé (indexées plus vite).
    if post.author_id:
        from agoraci.auth.models import User as _User
        if await session.scalar(select(_User.expert_status).where(_User.id == post.author_id)) == "approved":
            threshold = 1
    if not post.is_ai and post.author_id and not post.is_hidden and post.score >= threshold:
        open_reports = await session.scalar(
            select(func.count()).select_from(Report)
            .where(Report.post_id == post.id, Report.status == "open")
        )
        if not open_reports:
            try:
                from agoraci.rag.ingest import ingest_community_post
                disc = await session.get(Discussion, post.discussion_id)
                if await ingest_community_post(
                    session, post_id=post.id,
                    title=disc.title if disc else "Réponse communautaire", body=post.body,
                ):
                    await session.commit()
            except Exception:  # noqa: BLE001
                pass

    return {"post_id": str(post.id), "likes": post.likes, "dislikes": post.dislikes, "score": post.score}


@router.get("/reputation/{user_id}", response_model=ReputationOut)
async def get_reputation(user_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    rep = await session.get(Reputation, user_id)
    return ReputationOut(user_id=user_id, points=rep.points if rep else 0)


# --------------------------- Système de suivi ---------------------------
class FollowRequest(BaseModel):
    target_type: str = Field(pattern="^(group|discussion)$")
    target_id: uuid.UUID


@router.get("/follow/status")
async def follow_status(target_type: str, target_id: uuid.UUID,
                        current: CurrentUser = Depends(get_current_user),
                        session: AsyncSession = Depends(get_session)):
    f = await session.scalar(select(Follow).where(
        Follow.user_id == uuid.UUID(current.id), Follow.target_type == target_type,
        Follow.target_id == target_id))
    return {"following": bool(f)}


@router.post("/follow")
async def follow(payload: FollowRequest, current: CurrentUser = Depends(get_current_user),
                 session: AsyncSession = Depends(get_session)):
    existing = await session.scalar(select(Follow).where(
        Follow.user_id == uuid.UUID(current.id), Follow.target_type == payload.target_type,
        Follow.target_id == payload.target_id))
    if not existing:
        session.add(Follow(user_id=uuid.UUID(current.id), target_type=payload.target_type,
                           target_id=payload.target_id))
        await session.commit()
    return {"following": True}


@router.delete("/follow")
async def unfollow(target_type: str, target_id: uuid.UUID,
                   current: CurrentUser = Depends(get_current_user),
                   session: AsyncSession = Depends(get_session)):
    f = await session.scalar(select(Follow).where(
        Follow.user_id == uuid.UUID(current.id), Follow.target_type == target_type,
        Follow.target_id == target_id))
    if f:
        await session.delete(f)
        await session.commit()
    return {"following": False}


# --------------------------- FAQ dynamique ---------------------------
@router.get("/faq")
async def faq(session: AsyncSession = Depends(get_session)):
    """Questions les plus actives (par nb de réponses), regroupées par catégorie."""
    rows = await session.execute(
        select(Discussion.id, Discussion.title, Discussion.group_id, Group.category,
               func.count(Post.id).label("n"))
        .join(Group, Group.id == Discussion.group_id)
        .outerjoin(Post, Post.discussion_id == Discussion.id)
        .group_by(Discussion.id, Group.category)
        .order_by(func.count(Post.id).desc())
        .limit(60)
    )
    by_cat: dict = {}
    for did, title, _gid, category, n in rows:
        by_cat.setdefault(category, [])
        if len(by_cat[category]) < 5:
            by_cat[category].append({"id": str(did), "title": title, "answers": n})
    return [{"category": c, "questions": qs} for c, qs in by_cat.items()]


# --------------------------- Modération par vote ---------------------------
@router.post("/groups/{group_id}/moderation/proposals", response_model=ProposalOut, status_code=201)
async def create_proposal(
    group_id: uuid.UUID,
    payload: ProposalCreate,
    current: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    if not await _role_in_group(session, group_id, current.id):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Réservé aux membres du groupe")
    proposal = ModerationProposal(
        group_id=group_id, proposed_by=uuid.UUID(current.id), **payload.model_dump()
    )
    session.add(proposal)
    await session.commit()
    await session.refresh(proposal)
    return proposal


@router.get("/groups/{group_id}/moderation/proposals", response_model=list[ProposalOut])
async def list_proposals(group_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    return list(
        await session.scalars(
            select(ModerationProposal).where(ModerationProposal.group_id == group_id)
        )
    )


@router.post("/moderation/proposals/{proposal_id}/vote", response_model=ProposalOut)
async def vote_proposal(
    proposal_id: uuid.UUID,
    payload: ProposalVote,
    current: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    proposal = await session.get(ModerationProposal, proposal_id)
    if not proposal:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Proposition introuvable")
    if proposal.status != "open":
        raise HTTPException(status.HTTP_409_CONFLICT, "Proposition déjà clôturée")
    if not await _role_in_group(session, proposal.group_id, current.id):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Réservé aux membres du groupe")

    existing = await session.scalar(
        select(ModerationVote).where(
            ModerationVote.proposal_id == proposal_id,
            ModerationVote.user_id == uuid.UUID(current.id),
        )
    )
    old = existing.value if existing else 0
    if existing:
        existing.value = payload.value
    else:
        session.add(
            ModerationVote(proposal_id=proposal_id, user_id=uuid.UUID(current.id), value=payload.value)
        )

    # Met à jour les compteurs (retire l'ancien vote, applique le nouveau)
    for v, sign in ((old, -1), (payload.value, 1)):
        if v == 1:
            proposal.votes_for += sign
        elif v == -1:
            proposal.votes_against += sign

    # Décision au seuil — VOTE PONDÉRÉ par la réputation (plafonné) pour équilibrer :
    # les membres sérieux pèsent un peu plus, sans écraser les autres.
    await session.flush()
    cap = await _setting_float(session, "vote_weight_cap", 2.0)
    rows = await session.execute(
        select(ModerationVote.value, func.coalesce(Reputation.points, 0))
        .outerjoin(Reputation, Reputation.user_id == ModerationVote.user_id)
        .where(ModerationVote.proposal_id == proposal_id)
    )
    wf = wa = 0.0
    for val, pts in rows.all():
        w = min(1.0 + min(pts, 400) / 400.0 * 0.8, cap)  # 1.0 → 1.8, plafonné à `cap`
        if val == 1:
            wf += w
        elif val == -1:
            wa += w
    net = wf - wa
    if net >= proposal.threshold:
        proposal.status = "approved"
        await get_event_bus().publish(
            "moderation.decision",
            {
                "proposal_id": str(proposal.id),
                "group_id": str(proposal.group_id),
                "action": proposal.action,
                "target_type": proposal.target_type,
                "target_id": str(proposal.target_id),
            },
        )
    elif -net >= proposal.threshold:
        proposal.status = "rejected"

    await session.commit()
    await session.refresh(proposal)
    return proposal


# --------------------------- Super-admin (plateforme) ---------------------------
@router.get("/admin/groups", response_model=list[GroupOut])
async def admin_list_groups(
    _: CurrentUser = Depends(require_superadmin), session: AsyncSession = Depends(get_session)
):
    groups = list(await session.scalars(select(Group).order_by(Group.created_at.desc())))
    badge_map = await compute_badges_map(session)
    return [_to_group_out(g, badge_map.get(g.id, [])) for g in groups]


@router.post("/admin/groups/{group_id}/feature", response_model=GroupOut)
async def admin_feature_group(
    group_id: uuid.UUID,
    featured: bool = True,
    _: CurrentUser = Depends(require_superadmin),
    session: AsyncSession = Depends(get_session),
):
    group = await session.get(Group, group_id)
    if not group:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Groupe introuvable")
    group.is_featured = featured  # badge « vedette »
    await session.commit()
    await session.refresh(group)
    return _to_group_out(group)


_PURGE_GROUP_SQL = [
    "DELETE FROM forum.votes WHERE post_id IN (SELECT id FROM forum.posts WHERE discussion_id IN (SELECT id FROM forum.discussions WHERE group_id = :g))",
    "DELETE FROM forum.reports WHERE post_id IN (SELECT id FROM forum.posts WHERE discussion_id IN (SELECT id FROM forum.discussions WHERE group_id = :g))",
    "DELETE FROM forum.posts WHERE discussion_id IN (SELECT id FROM forum.discussions WHERE group_id = :g)",
    "DELETE FROM forum.moderation_votes WHERE proposal_id IN (SELECT id FROM forum.moderation_proposals WHERE group_id = :g)",
    "DELETE FROM forum.moderation_proposals WHERE group_id = :g",
    "DELETE FROM forum.follows WHERE target_type = 'discussion' AND target_id IN (SELECT id FROM forum.discussions WHERE group_id = :g)",
    "DELETE FROM forum.follows WHERE target_type = 'group' AND target_id = :g",
    "DELETE FROM forum.discussions WHERE group_id = :g",
    "DELETE FROM forum.group_memberships WHERE group_id = :g",
    "DELETE FROM forum.groups WHERE id = :g",
]


async def purge_group(session: AsyncSession, group_id) -> None:
    """Supprime définitivement un groupe et TOUT son contenu."""
    for stmt in _PURGE_GROUP_SQL:
        await session.execute(text(stmt), {"g": str(group_id)})


class ScheduleDeletion(BaseModel):
    reason: str = Field(default="", max_length=255)
    immediate: bool = False  # cas grave (illégal) : suppression sans préavis


@router.delete("/admin/groups/{group_id}")
async def admin_delete_group(
    group_id: uuid.UUID,
    payload: ScheduleDeletion | None = None,
    _: CurrentUser = Depends(require_superadmin),
    session: AsyncSession = Depends(get_session),
):
    """Programme la suppression d'un groupe avec PRÉAVIS (72h par défaut, configurable),
    sauf `immediate` (cas grave). Les membres sont prévenus ; annulable avant l'échéance."""
    group = await session.get(Group, group_id)
    if not group:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Groupe introuvable")
    payload = payload or ScheduleDeletion()
    if payload.immediate:
        await purge_group(session, group_id)
        await session.commit()
        return {"deleted": str(group_id)}
    notice_h = await _setting_float(session, "superadmin_group_delete_notice_h", 72)
    group.deletion_at = datetime.now(UTC) + timedelta(hours=notice_h)
    group.deletion_reason = payload.reason.strip() or None
    await session.commit()
    # Prévient les membres (préavis)
    await get_event_bus().publish("group.deletion_scheduled", {
        "group_id": str(group_id), "deletion_at": group.deletion_at.isoformat(),
        "reason": group.deletion_reason or "",
    })
    return {"scheduled": str(group_id), "deletion_at": group.deletion_at.isoformat()}


@router.post("/admin/groups/{group_id}/cancel-deletion")
async def admin_cancel_deletion(
    group_id: uuid.UUID,
    _: CurrentUser = Depends(require_superadmin),
    session: AsyncSession = Depends(get_session),
):
    group = await session.get(Group, group_id)
    if not group:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Groupe introuvable")
    group.deletion_at = None
    group.deletion_reason = None
    await session.commit()
    return {"cancelled": str(group_id)}


@router.get("/admin/reports")
async def admin_list_reports(
    _: CurrentUser = Depends(require_superadmin), session: AsyncSession = Depends(get_session)
):
    """Liste les contenus signalés ouverts (avec un extrait du post)."""
    rows = await session.scalars(
        select(Report).where(Report.status == "open").order_by(Report.created_at.desc())
    )
    out = []
    for r in rows:
        post = await session.get(Post, r.post_id)
        out.append({
            "id": str(r.id),
            "post_id": str(r.post_id),
            "reporter_id": str(r.reporter_id),
            "status": r.status,
            "post_excerpt": (post.body[:300] if post else "(supprimé)"),
            "post_hidden": bool(post.is_hidden) if post else True,
        })
    return out


class ResolveReport(BaseModel):
    action: str = Field(pattern="^(hide|delete|dismiss)$")


@router.post("/admin/reports/{report_id}/resolve")
async def admin_resolve_report(
    report_id: uuid.UUID,
    payload: ResolveReport,
    _: CurrentUser = Depends(require_superadmin),
    session: AsyncSession = Depends(get_session),
):
    """Traite un signalement : masquer / supprimer le post, ou ignorer."""
    report = await session.get(Report, report_id)
    if not report:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Signalement introuvable")
    if payload.action in ("hide", "delete"):
        await apply_decision(session, "post", report.post_id, payload.action)
    report.status = "resolved" if payload.action != "dismiss" else "dismissed"
    await session.commit()
    return {"message": "Signalement traité", "action": payload.action}
