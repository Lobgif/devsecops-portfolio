"""Accès base de données async (SQLAlchemy 2.0 + asyncpg).

Base PostgreSQL unique partagée : chaque service déclare ses tables dans
son propre schéma via `__table_args__ = {"schema": "<service>"}`.
"""
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from .config import get_settings

_engine: AsyncEngine | None = None
_sessionmaker: async_sessionmaker[AsyncSession] | None = None


class Base(DeclarativeBase):
    """Classe de base déclarative partagée."""


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_async_engine(
            settings.database_url,
            echo=False,
            pool_pre_ping=True,
        )
    return _engine


def _get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    global _sessionmaker
    if _sessionmaker is None:
        _sessionmaker = async_sessionmaker(
            get_engine(), expire_on_commit=False, class_=AsyncSession
        )
    return _sessionmaker


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Dépendance FastAPI : `session: AsyncSession = Depends(get_session)`."""
    async with _get_sessionmaker()() as session:
        yield session


async def init_models() -> None:
    """Crée les tables du service (dev only ; en prod utiliser Alembic)."""
    async with get_engine().begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def maybe_init_models() -> None:
    """Crée les tables automatiquement SAUF en production (où Alembic gère le schéma)."""
    from .config import get_settings

    if get_settings().env != "production":
        await init_models()
