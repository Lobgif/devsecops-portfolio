"""Pipeline d'ingestion de textes juridiques pour le RAG.

Découpe un document en **articles**, génère les embeddings et stocke chaque
fragment dans `rag.chunks` (vecteur + index plein-texte `tsv`).

Usage CLI (corpus de démonstration) :
    python -m agoraci.rag.ingest
"""
import asyncio
import logging
import re

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from agoraci.common.db import get_engine

from .models import Chunk, LegalDocument
from .providers import embed, embed_batch
from .sample_corpus import SAMPLE_DOCUMENTS

logger = logging.getLogger("rag.ingest")

# Détecte « Article 12 », « Art. 5 bis », etc. en début de ligne
ARTICLE_RE = re.compile(r"(?im)^\s*(?:article|art\.?)\s+(\d+(?:\s*(?:bis|ter|quater))?)\s*[:.\-]?\s*")


def split_into_articles(content: str) -> list[dict]:
    """Découpe un texte en articles. Si aucun marqueur, renvoie un seul chunk."""
    matches = list(ARTICLE_RE.finditer(content))
    if not matches:
        return [{"numero_article": None, "content": content.strip()}]
    chunks: list[dict] = []
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        header = content[m.start():m.end()].strip()
        body = content[m.end():end].strip()
        chunks.append({
            "numero_article": m.group(1).strip(),
            "content": f"{header} {body}".strip(),
        })
    return chunks


async def ingest_document(
    session: AsyncSession,
    *,
    title: str,
    content: str,
    source_type: str = "loi",
    code_source: str | None = None,
    source_url: str | None = None,
) -> dict:
    """Ingestion d'un document complet (idempotent par titre)."""
    existing = await session.scalar(select(LegalDocument).where(LegalDocument.title == title))
    if existing:
        return {"document_id": str(existing.id), "chunks": 0, "skipped": True}

    doc = LegalDocument(title=title, source_type=source_type, source_url=source_url, extra={})
    session.add(doc)
    await session.flush()

    articles = split_into_articles(content)
    vectors = await embed_batch([a["content"] for a in articles], "search_document")
    for pos, (art, vector) in enumerate(zip(articles, vectors, strict=True)):
        session.add(Chunk(
            document_id=doc.id,
            content=art["content"],
            embedding=vector,
            code_source=code_source or title,
            numero_article=art["numero_article"],
            position=pos,
        ))
    await session.flush()
    # Index plein-texte (recherche hybride)
    await session.execute(
        text("UPDATE rag.chunks SET tsv = to_tsvector('french', unaccent(content)) WHERE document_id = :d"),
        {"d": doc.id},
    )
    await session.commit()
    return {"document_id": str(doc.id), "chunks": len(articles), "skipped": False}


async def ingest_community_post(session: AsyncSession, *, post_id, title: str, body: str) -> bool:
    """Indexe une réponse validée de la communauté dans le RAG (idempotent par post_id)."""
    existing = await session.scalar(select(Chunk).where(Chunk.document_id == post_id))
    if existing:
        return False
    content = f"{title}\n{body}".strip()
    vector = await embed(content, "search_document")
    session.add(Chunk(
        document_id=post_id, content=content, embedding=vector,
        code_source="Communauté", numero_article=None, titre_hierarchie=title[:200],
    ))
    await session.flush()
    await session.execute(
        text("UPDATE rag.chunks SET tsv = to_tsvector('french', unaccent(content)) WHERE document_id = :d"),
        {"d": post_id},
    )
    return True


async def backfill_community(session: AsyncSession, min_likes: int = 2) -> int:
    """Indexe toutes les réponses humaines existantes ayant assez de j'aime."""
    from agoraci.forum.models import Discussion, Post  # import local (évite les cycles)

    posts = await session.scalars(
        select(Post).where(Post.is_ai.is_(False), Post.likes >= min_likes, Post.is_hidden.is_(False))
    )
    count = 0
    for p in posts:
        disc = await session.get(Discussion, p.discussion_id)
        title = disc.title if disc else "Réponse communautaire"
        if await ingest_community_post(session, post_id=p.id, title=title, body=p.body):
            count += 1
    await session.commit()
    return count


async def seed_sample_corpus() -> None:
    """Ingestion du corpus de démonstration (idempotent)."""
    maker = async_sessionmaker(get_engine(), expire_on_commit=False, class_=AsyncSession)
    async with maker() as session:
        total = 0
        for d in SAMPLE_DOCUMENTS:
            res = await ingest_document(session, **d)
            total += res["chunks"]
            logger.info("  %s -> %d articles%s", d["title"], res["chunks"],
                        " (déjà présent)" if res["skipped"] else "")
        logger.info("✅ Corpus de démonstration ingéré (%d articles).", total)


if __name__ == "__main__":
    logging.basicConfig(level="INFO")
    asyncio.run(seed_sample_corpus())
