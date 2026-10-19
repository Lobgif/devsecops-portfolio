"""Traitement des jobs d'ingestion en arrière-plan (consommés depuis RabbitMQ).

L'admin lance un job → un événement part dans RabbitMQ → ce consumer traite
indépendamment du navigateur. L'utilisateur peut fermer la page : le serveur continue.
La progression est écrite en base (table rag.ingest_jobs) et lue par l'admin.
"""
import asyncio
import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from agoraci.common.db import get_engine
from agoraci.common.messaging import get_event_bus
from agoraci.common.storage import get_object

from .extract import crawl_collect, extract_from_url, extract_text
from .ingest import ingest_document
from .models import IngestJob

logger = logging.getLogger("rag.jobs")
_maker = None


def _sessionmaker():
    global _maker
    if _maker is None:
        _maker = async_sessionmaker(get_engine(), expire_on_commit=False, class_=AsyncSession)
    return _maker


async def _is_cancelled(session: AsyncSession, job_id) -> bool:
    return (await session.scalar(select(IngestJob.status).where(IngestJob.id == job_id))) == "cancelled"


async def _process(job_id: str) -> None:
    async with _sessionmaker()() as session:
        job = await session.get(IngestJob, uuid.UUID(job_id))
        if not job or job.status in ("cancelled", "done"):
            return
        job.status = "running"
        await session.commit()
        try:
            if job.kind == "crawl":
                links = await asyncio.to_thread(crawl_collect, job.source, job.crawl_filter, 1, 60)
                job.total = len(links)
                await session.commit()
                for i, link in enumerate(links):
                    if await _is_cancelled(session, job.id):
                        break
                    try:
                        text = await asyncio.to_thread(extract_from_url, link)
                        if text.strip():
                            r = await ingest_document(
                                session, title=link[:200], content=text,
                                source_type=job.source_type, code_source=link[:120],
                                source_url=link,
                            )
                            job.chunks += r["chunks"]
                    except Exception as exc:  # noqa: BLE001
                        logger.warning("crawl %s: %s", link, exc)
                    job.done = i + 1
                    await session.commit()
                    await asyncio.sleep(1.0)  # politesse : évite le throttling (503) du site cible
                job.status = "cancelled" if await _is_cancelled(session, job.id) else "done"
            else:  # url | text | file
                job.total = 1
                if job.kind == "text":
                    text = job.source
                elif job.kind == "file":
                    data = await asyncio.to_thread(get_object, job.source)  # source = clé MinIO
                    text = await asyncio.to_thread(extract_text, job.title or "fichier", data, True)
                else:  # url (page web ou PDF en ligne)
                    text = await asyncio.to_thread(extract_from_url, job.source)
                if not text.strip():
                    raise ValueError("Aucun texte extrait de cette source.")
                title = job.title or (job.source[:200] if job.kind != "text" else "Document")
                r = await ingest_document(
                    session, title=title, content=text,
                    source_type=job.source_type, code_source=title[:120],
                    source_url=job.source if job.kind == "url" else None,
                )
                job.chunks = r["chunks"]
                job.done = 1
                job.status = "done"
            await session.commit()
            logger.info("Job %s terminé (%s) : %d articles", job_id, job.status, job.chunks)
        except Exception as exc:  # noqa: BLE001
            job.status = "error"
            job.message = str(exc)[:500]
            await session.commit()
            logger.error("Job %s en erreur: %s", job_id, exc)


async def _handler(routing_key: str, payload: dict) -> None:
    job_id = payload.get("job_id")
    if job_id:
        await _process(job_id)


async def _resume_pending() -> None:
    """Au démarrage : relance les jobs interrompus (pending/running) → résilience aux redémarrages."""
    async with _sessionmaker()() as session:
        interrupted = list(await session.scalars(
            select(IngestJob).where(IngestJob.status.in_(["pending", "running"]))
        ))
        for j in interrupted:
            j.status = "pending"  # un job « running » coupé par un redémarrage repart de zéro
        await session.commit()
        bus = get_event_bus()
        for j in interrupted:
            await bus.publish("ingest.requested", {"job_id": str(j.id)})
        if interrupted:
            logger.info("Reprise de %d job(s) d'ingestion après redémarrage", len(interrupted))


async def start_ingest_consumer() -> None:
    await get_event_bus().subscribe(
        queue_name="rag.ingest", routing_keys=["ingest.requested"], handler=_handler
    )
    await _resume_pending()
