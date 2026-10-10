"""Runner Alembic unique pour tout le backend (tous les schémas).

`migrations/env.py` importe tous les modèles (pour peupler Base.metadata) puis
appelle `run_migrations()`. Les tables de tous les schémas (auth, forum, rag, ...)
sont gérées dans une seule lignée de migrations ; la table de version vit dans `public`.
"""
import asyncio

from alembic import context
from sqlalchemy.engine import Connection

from .config import get_settings
from .db import Base, get_engine


def _do_run(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=Base.metadata,
        include_schemas=True,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def _run_async() -> None:
    engine = get_engine()
    async with engine.connect() as connection:
        await connection.run_sync(_do_run)
    await engine.dispose()


def run_migrations() -> None:
    settings = get_settings()
    if context.is_offline_mode():
        context.configure(
            url=settings.database_url,
            target_metadata=Base.metadata,
            include_schemas=True,
            literal_binds=True,
        )
        with context.begin_transaction():
            context.run_migrations()
    else:
        asyncio.run(_run_async())
