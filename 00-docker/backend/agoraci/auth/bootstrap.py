"""Création/promotion automatique du super-administrateur depuis les variables d'env.

Idempotent : exécuté à chaque démarrage. Si SUPERADMIN_EMAIL est défini :
  - crée le compte s'il n'existe pas (vérifié, mot de passe depuis SUPERADMIN_PASSWORD)
  - sinon, promeut le compte existant en super-admin.
"""
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from agoraci.common import get_settings
from agoraci.common.db import get_engine
from agoraci.common.security import hash_password

from .models import User

logger = logging.getLogger("auth.bootstrap")


async def ensure_superadmin() -> None:
    settings = get_settings()
    if not settings.superadmin_email or not settings.superadmin_password:
        logger.info("Aucun super-admin configuré (SUPERADMIN_EMAIL/PASSWORD vides).")
        return

    maker = async_sessionmaker(get_engine(), expire_on_commit=False, class_=AsyncSession)
    async with maker() as session:
        # Cherche par email, sinon par username, sinon un super-admin existant
        user = await session.scalar(select(User).where(User.email == settings.superadmin_email))
        if user is None:
            user = await session.scalar(
                select(User).where(User.username == settings.superadmin_username)
            )
        if user is None:
            user = await session.scalar(select(User).where(User.is_superadmin.is_(True)).limit(1))

        if user:
            # Réconcilie le compte existant avec la config (.env) : email, username ET
            # mot de passe → SUPERADMIN_PASSWORD fait autorité (changer le .env + redémarrer
            # met à jour le mot de passe et invalide l'ancien).
            user.email = settings.superadmin_email
            user.username = settings.superadmin_username
            user.hashed_password = hash_password(settings.superadmin_password)
            user.is_superadmin = True
            user.is_verified = True
            await session.commit()
            logger.info("Super-admin réconcilié : %s", settings.superadmin_email)
        else:
            session.add(
                User(
                    email=settings.superadmin_email,
                    username=settings.superadmin_username,
                    hashed_password=hash_password(settings.superadmin_password),
                    full_name="Super Administrateur",
                    is_superadmin=True,
                    is_verified=True,
                )
            )
            await session.commit()
            logger.info("Super-admin créé : %s", settings.superadmin_email)
