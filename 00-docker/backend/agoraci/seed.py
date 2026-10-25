"""Peuplement de la base avec des données de démonstration (idempotent).

Lancer :  docker compose ... exec backend python -m agoraci.seed

Crée :
  - le super-admin (s'il n'existe pas déjà via le bootstrap)
  - 10 utilisateurs aléatoires (vérifiés, mot de passe commun)
  - plusieurs groupes thématiques, avec créateurs et membres
  - le SUPER-ADMIN membre de CHAQUE groupe avec le rôle le plus élevé (creator)
  - des discussions, des réponses (dont des réponses IA) et des votes
"""
import asyncio
import logging
import random

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from agoraci.auth.models import User
from agoraci.common import get_settings
from agoraci.common.db import get_engine
from agoraci.common.security import hash_password
from agoraci.forum.models import (
    ROLE_ADMIN,
    ROLE_CREATOR,
    ROLE_MEMBER,
    Discussion,
    Group,
    GroupMembership,
    Post,
    Reputation,
    Vote,
)

logging.basicConfig(level="INFO")
logger = logging.getLogger("seed")

DEMO_PASSWORD = "Password123!"

PRENOMS = ["Awa", "Koffi", "Aya", "Yao", "Adjoua", "Kouamé", "Fatou", "Ibrahim",
           "Mariam", "Seydou", "Aminata", "Bakary", "Rokia", "Drissa", "Nadège"]
NOMS = ["Koné", "Traoré", "Konan", "Diabaté", "Ouattara", "Kouassi", "Bamba",
        "Yao", "Cissé", "Touré", "Gbagbo", "N'Guessan"]

GROUPES = [
    ("Mariage & Famille", "Mariage & Famille", "Questions sur le mariage, le divorce, la dot et la vie de famille."),
    ("Héritage & Succession", "Héritage", "Partage des biens, testament, droits des héritiers."),
    ("Droit du travail", "Droits & Justice", "Contrats, licenciement, congés, droits des salariés."),
    ("Éducation & Bourses", "Éducation", "Scolarité, bourses, orientation, vie étudiante."),
    ("Vie citoyenne", "Société", "Papiers, démarches administratives, droits du citoyen."),
    ("Débat politique", "Politique", "Échanges respectueux sur la vie politique ivoirienne."),
]

DISCUSSIONS = [
    ("Quels sont mes droits en cas de divorce ?",
     "Mon conjoint demande le divorce. Comment se passe le partage des biens et la garde des enfants ?"),
    ("Comment contester un héritage ?",
     "Un membre de la famille a été écarté du partage. Quels recours sont possibles ?"),
    ("Licenciement sans préavis, est-ce légal ?",
     "Mon employeur m'a renvoyé du jour au lendemain. Ai-je droit à une indemnité ?"),
    ("Comment obtenir une bourse d'études ?",
     "Quelles sont les conditions et les démarches pour une bourse en Côte d'Ivoire ?"),
    ("Refaire une CNI perdue : la procédure",
     "J'ai perdu ma carte nationale d'identité, quelles sont les étapes pour la refaire ?"),
]

REPONSES = [
    "D'après mon expérience, il faut d'abord saisir le tribunal compétent.",
    "Pense à rassembler tous les documents justificatifs avant toute démarche.",
    "Un avocat pourra t'accompagner, mais beaucoup de démarches sont gratuites.",
    "J'ai vécu une situation similaire, la médiation a beaucoup aidé.",
]


async def _get_or_create_user(session: AsyncSession, email: str, **kwargs) -> User:
    user = await session.scalar(select(User).where(User.email == email))
    if user:
        return user
    user = User(email=email, **kwargs)
    session.add(user)
    await session.flush()
    return user


async def _ensure_membership(session: AsyncSession, group_id, user_id, role: str) -> None:
    existing = await session.scalar(
        select(GroupMembership).where(
            GroupMembership.group_id == group_id, GroupMembership.user_id == user_id
        )
    )
    if existing:
        # Promeut si le nouveau rôle est plus élevé
        order = {ROLE_MEMBER: 0, ROLE_ADMIN: 1, ROLE_CREATOR: 2}
        if order[role] > order.get(existing.role, 0):
            existing.role = role
        return
    session.add(GroupMembership(group_id=group_id, user_id=user_id, role=role))


async def seed() -> None:
    settings = get_settings()
    maker = async_sessionmaker(get_engine(), expire_on_commit=False, class_=AsyncSession)
    random.seed(42)

    async with maker() as session:
        # --- Super-admin (réutilise celui du bootstrap quel que soit son email) ---
        admin_email = settings.superadmin_email or "admin@agoraci.ci"
        admin = await session.scalar(select(User).where(User.email == admin_email))
        if admin is None:
            admin = await session.scalar(
                select(User).where(User.is_superadmin.is_(True)).limit(1)
            )
        if admin is None:
            admin = User(
                email=admin_email,
                username=settings.superadmin_username or "superadmin",
                hashed_password=hash_password(settings.superadmin_password or DEMO_PASSWORD),
                full_name="Super Administrateur",
                is_verified=True, is_superadmin=True, is_moderator=True,
            )
            session.add(admin)
            await session.flush()
        else:
            admin.is_superadmin = True
            admin.is_verified = True

        # --- 10 utilisateurs aléatoires (emails stables => idempotent) ---
        users: list[User] = []
        for i in range(1, 11):
            prenom = random.choice(PRENOMS)
            nom = random.choice(NOMS)
            user = await _get_or_create_user(
                session, f"user{i:02d}@agoraci.ci",
                username=f"{prenom.lower()}{i:02d}",
                hashed_password=hash_password(DEMO_PASSWORD),
                full_name=f"{prenom} {nom}",
                bio=f"Citoyen·ne engagé·e — {nom}.",
                preferred_language="fr",
                is_verified=True,
            )
            users.append(user)
        await session.commit()

        # --- Groupes + discussions + réponses ---
        for idx, (name, category, desc) in enumerate(GROUPES):
            group = await session.scalar(select(Group).where(Group.name == name))
            if group is None:
                creator = users[idx % len(users)]
                group = Group(
                    name=name, category=category, description=desc,
                    created_by=creator.id,
                    is_featured=(idx < 2),  # 2 groupes en vedette
                )
                session.add(group)
                await session.flush()
                await _ensure_membership(session, group.id, creator.id, ROLE_CREATOR)

                # Membres aléatoires
                for member in random.sample(users, k=random.randint(3, 7)):
                    await _ensure_membership(session, group.id, member.id, ROLE_MEMBER)

                # 1 à 2 discussions par groupe
                for d_title, d_body in random.sample(DISCUSSIONS, k=random.randint(1, 2)):
                    author = random.choice(users)
                    disc = Discussion(group_id=group.id, author_id=author.id,
                                      title=d_title, body=d_body)
                    session.add(disc)
                    await session.flush()

                    # Réponses (humaines + 1 IA)
                    posts = []
                    for body in random.sample(REPONSES, k=random.randint(1, 3)):
                        p = Post(discussion_id=disc.id, author_id=random.choice(users).id, body=body)
                        session.add(p)
                        posts.append(p)
                    ai = Post(discussion_id=disc.id, is_ai=True, author_id=None,
                              body="[IA] Selon le droit ivoirien, plusieurs articles encadrent ce cas. "
                                   "Consultez un professionnel pour votre situation précise.")
                    session.add(ai)
                    posts.append(ai)
                    await session.flush()

                    # Votes -> likes/score + réputation des auteurs
                    for p in posts:
                        voters = random.sample(users, k=random.randint(0, 6))
                        for v in voters:
                            session.add(Vote(post_id=p.id, user_id=v.id, value=1))
                            p.likes += 1
                        p.score = p.likes - p.dislikes
                        if p.author_id and p.likes:
                            rep = await session.get(Reputation, p.author_id)
                            if rep:
                                rep.points += p.likes
                            else:
                                session.add(Reputation(user_id=p.author_id, points=p.likes))

            # --- SUPER-ADMIN membre de CHAQUE groupe, rôle le plus élevé ---
            await _ensure_membership(session, group.id, admin.id, ROLE_CREATOR)

            # Recalcule les compteurs
            group.member_count = await session.scalar(
                select(func.count()).select_from(GroupMembership).where(GroupMembership.group_id == group.id)
            )
            group.discussion_count = await session.scalar(
                select(func.count()).select_from(Discussion).where(Discussion.group_id == group.id)
            )

        await session.commit()

    logger.info("✅ Seed terminé : 1 super-admin + 10 utilisateurs + %d groupes.", len(GROUPES))
    logger.info("   Mot de passe des comptes de démo : %s", DEMO_PASSWORD)


if __name__ == "__main__":
    asyncio.run(seed())
