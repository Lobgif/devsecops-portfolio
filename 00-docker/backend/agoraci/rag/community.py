"""Backfill : indexe dans le RAG les réponses validées de la communauté.

Usage : python -m agoraci.rag.community [min_likes]
"""
import asyncio
import logging
import sys

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from agoraci.common.db import get_engine

from .ingest import backfill_community

logging.basicConfig(level="INFO")


async def _run(min_likes: int) -> None:
    maker = async_sessionmaker(get_engine(), expire_on_commit=False, class_=AsyncSession)
    async with maker() as session:
        n = await backfill_community(session, min_likes)
    logging.getLogger("rag.community").info("✅ %d réponse(s) communautaire(s) indexée(s).", n)


if __name__ == "__main__":
    likes = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    asyncio.run(_run(likes))
