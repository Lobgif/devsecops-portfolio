"""Initialise les paramètres du site et le glossaire (idempotent, au démarrage)."""
import logging
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from agoraci.common.db import get_engine

from .defaults import ARTICLES, DEFAULT_SETTINGS, GLOSSARY_TERMS
from .models import Article, GlossaryTerm, SiteSetting

logger = logging.getLogger("core.bootstrap")

# Groupes de démarrage : un par grande catégorie, pour que la plateforme soit
# vivante et couvre TOUS les sujets citoyens dès le lancement (pas seulement le droit).
STARTER_GROUPS = [
    ("Démarches administratives", "Entraide sur les papiers, mairies, préfectures et documents officiels."),
    ("Droit & Justice", "Vos droits, la loi ivoirienne, litiges et conseils juridiques."),
    ("Santé & Bien-être", "Questions santé, prévention, où se soigner, bien-être."),
    ("Éducation & Formation", "École, université, bourses, examens et formations."),
    ("Emploi & Carrière", "Recherche d'emploi, CV, entretiens et droits du travailleur."),
    ("Business & Entrepreneuriat", "Créer et gérer son entreprise, OHADA, financements."),
    ("Finance & Argent", "Banque, Mobile Money, épargne, impôts — et éviter les arnaques."),
    ("Technologie & Numérique", "Internet, smartphones, sécurité et services en ligne."),
    ("Immobilier & Logement", "Location, achat, terrain et litiges de bail."),
    ("Politique & Société", "Débats citoyens et vie de la cité, dans le respect."),
    ("Mariage & Famille", "Mariage, filiation, héritage et vie de famille."),
    ("Vie pratique", "Astuces du quotidien : transport, consommation, bons plans."),
]


async def ensure_starter_groups(session: AsyncSession) -> None:
    """Crée un groupe par catégorie si AUCUN groupe n'existe encore (idempotent)."""
    from agoraci.auth.models import User
    from agoraci.forum.models import ROLE_CREATOR, Group, GroupMembership

    if (await session.scalar(select(func.count()).select_from(Group)) or 0) > 0:
        return
    admin = await session.scalar(select(User).where(User.is_superadmin.is_(True)).limit(1))
    if not admin:
        return
    for name, desc in STARTER_GROUPS:
        g = Group(name=name, category=name, description=desc, created_by=admin.id, member_count=1)
        session.add(g)
        await session.flush()
        session.add(GroupMembership(group_id=g.id, user_id=admin.id, role=ROLE_CREATOR))
    logger.info("Groupes de démarrage créés (%d catégories).", len(STARTER_GROUPS))


async def ensure_defaults() -> None:
    maker = async_sessionmaker(get_engine(), expire_on_commit=False, class_=AsyncSession)
    async with maker() as session:
        # Paramètres : ne crée que les clés manquantes (ne pas écraser les valeurs éditées)
        existing = set(await session.scalars(select(SiteSetting.key)))
        for k, v in DEFAULT_SETTINGS.items():
            if k not in existing:
                session.add(SiteSetting(key=k, value=v))

        # Glossaire : ajoute les termes manquants
        known = set(await session.scalars(select(GlossaryTerm.term)))
        for term, category, definition in GLOSSARY_TERMS:
            if term not in known:
                session.add(GlossaryTerm(term=term, category=category, definition=definition))

        # Actualités : seed une seule fois (si la table est vide)
        count = await session.scalar(select(func.count()).select_from(Article)) or 0
        if count == 0:
            for title, summary, content, category, source, d in ARTICLES:
                session.add(Article(
                    title=title, summary=summary, content=content, category=category,
                    source=source, published_at=date.fromisoformat(d),
                ))

        await ensure_starter_groups(session)
        await session.commit()
    logger.info("Paramètres du site & glossaire initialisés.")
