"""Routes du service RAG : ingestion d'un chunk + question juridique (recherche hybride)."""
import os
import re
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
from sqlalchemy import func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from agoraci.common import get_session, limiter
from agoraci.common.auth_deps import CurrentUser, get_optional_user, require_superadmin
from agoraci.common.messaging import get_event_bus

from .models import Chunk, IngestJob, LegalDocument
from .providers import EMBEDDINGS_ENABLED, embed, generate_answer
from .quota import bump_nanan_quota, check_nanan_quota

router = APIRouter(prefix="/api/rag", tags=["rag"])


class IngestChunk(BaseModel):
    document_id: uuid.UUID
    content: str
    code_source: str | None = None
    numero_article: str | None = None
    titre_hierarchie: str | None = None


class IngestDocument(BaseModel):
    title: str
    content: str
    source_type: str = "loi"
    code_source: str | None = None
    source_url: str | None = None


class AskRequest(BaseModel):
    question: str
    top_k: int = 5
    mode: str = "legal"   # legal (page IA Juridique) | general (groupes)
    history: list[dict] = []  # échanges précédents : [{role, content}] (conversation)


@router.post("/ingest", status_code=201)
async def ingest(payload: IngestChunk, session: AsyncSession = Depends(get_session)):
    vector = await embed(payload.content, "search_document")
    chunk = Chunk(
        document_id=payload.document_id,
        content=payload.content,
        embedding=vector,
        code_source=payload.code_source,
        numero_article=payload.numero_article,
        titre_hierarchie=payload.titre_hierarchie,
    )
    session.add(chunk)
    await session.flush()
    # Index plein-texte (recherche hybride)
    await session.execute(
        text("UPDATE rag.chunks SET tsv = to_tsvector('french', unaccent(content)) WHERE id = :id"),
        {"id": chunk.id},
    )
    await session.commit()
    return {"chunk_id": str(chunk.id)}


@router.post("/ingest-document", status_code=201)
async def ingest_document_endpoint(
    payload: IngestDocument,
    _: CurrentUser = Depends(require_superadmin),
    session: AsyncSession = Depends(get_session),
):
    """Ingestion d'un document juridique complet (découpage par article). Super-admin."""
    from .ingest import ingest_document

    return await ingest_document(session, **payload.model_dump())


class IngestJobsRequest(BaseModel):
    urls: list[str]
    kind: str = "url"            # url | crawl
    source_type: str = "loi"
    crawl_filter: str | None = None


@router.post("/admin/ingest-jobs", status_code=202)
async def admin_create_ingest_jobs(
    payload: IngestJobsRequest,
    _: CurrentUser = Depends(require_superadmin),
    session: AsyncSession = Depends(get_session),
):
    """Crée des jobs d'ingestion en arrière-plan (1 par URL) et les publie dans RabbitMQ."""
    kind = payload.kind if payload.kind in ("url", "crawl") else "url"
    created = []
    for raw in payload.urls:
        url = raw.strip()
        if not url:
            continue
        job = IngestJob(kind=kind, source=url, source_type=payload.source_type,
                        crawl_filter=(payload.crawl_filter or None))
        session.add(job)
        await session.flush()
        created.append(str(job.id))
    await session.commit()  # commit AVANT de publier (sinon le consumer ne voit pas encore le job)
    for jid in created:
        await get_event_bus().publish("ingest.requested", {"job_id": jid})
    return {"jobs": created}


class CrawlPreview(BaseModel):
    url: str
    crawl_filter: str | None = None
    depth: int = 1


@router.post("/admin/crawl-preview")
async def admin_crawl_preview(
    payload: CrawlPreview, _: CurrentUser = Depends(require_superadmin),
):
    """Aperçu : crawle (pagination + profondeur) et renvoie les URLs trouvées, SANS ingérer."""
    from .extract import crawl_collect
    depth = max(1, min(payload.depth, 3))
    try:
        urls = await run_in_threadpool(
            crawl_collect, payload.url.strip(), (payload.crawl_filter or None), depth, 80
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Échec du crawl : {exc}") from exc
    return {"count": len(urls), "urls": urls}


@router.get("/admin/jobs")
async def admin_list_jobs(
    _: CurrentUser = Depends(require_superadmin), session: AsyncSession = Depends(get_session)
):
    rows = await session.scalars(select(IngestJob).order_by(IngestJob.created_at.desc()).limit(40))
    return [
        {"id": str(j.id), "kind": j.kind,
         "source": j.title or (j.source[:80] if j.kind == "text" else j.source),
         "status": j.status, "total": j.total, "done": j.done, "chunks": j.chunks,
         "message": j.message, "created_at": j.created_at.isoformat() if j.created_at else None}
        for j in rows
    ]


@router.post("/admin/jobs/retry-failed")
async def admin_retry_failed(
    _: CurrentUser = Depends(require_superadmin), session: AsyncSession = Depends(get_session)
):
    """Relance tous les jobs en erreur (ex. 503 transitoires) → repassent en file."""
    rows = list(await session.scalars(select(IngestJob).where(IngestJob.status == "error")))
    for j in rows:
        j.status = "pending"
        j.message = None
        j.done = 0
        j.chunks = 0
    await session.commit()
    for j in rows:
        await get_event_bus().publish("ingest.requested", {"job_id": str(j.id)})
    return {"retried": len(rows)}


@router.post("/admin/jobs/{job_id}/cancel")
async def admin_cancel_job(
    job_id: uuid.UUID,
    _: CurrentUser = Depends(require_superadmin),
    session: AsyncSession = Depends(get_session),
):
    job = await session.get(IngestJob, job_id)
    if not job:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Job introuvable")
    if job.status in ("pending", "running"):
        job.status = "cancelled"
        await session.commit()
    return {"id": str(job_id), "status": job.status}


@router.get("/admin/documents")
async def admin_list_documents(
    _: CurrentUser = Depends(require_superadmin), session: AsyncSession = Depends(get_session)
):
    """Liste les documents juridiques de la base de connaissances (avec nb d'articles)."""
    docs = await session.scalars(select(LegalDocument).order_by(LegalDocument.created_at.desc()))
    out = []
    for d in docs:
        n = await session.scalar(
            select(func.count()).select_from(Chunk).where(Chunk.document_id == d.id)
        ) or 0
        out.append({
            "id": str(d.id), "title": d.title, "source_type": d.source_type,
            "source_url": d.source_url, "chunks": n,
            "created_at": d.created_at.isoformat() if d.created_at else None,
        })
    return out


@router.delete("/admin/documents/{document_id}")
async def admin_delete_document(
    document_id: uuid.UUID,
    _: CurrentUser = Depends(require_superadmin),
    session: AsyncSession = Depends(get_session),
):
    """Supprime un document et tous ses articles indexés. Super-admin uniquement."""
    doc = await session.get(LegalDocument, document_id)
    if not doc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document introuvable")
    await session.execute(text("DELETE FROM rag.chunks WHERE document_id = :d"), {"d": str(document_id)})
    await session.delete(doc)
    await session.commit()
    return {"deleted": str(document_id)}


@router.post("/admin/documents/{document_id}/reingest")
async def admin_reingest_document(
    document_id: uuid.UUID,
    _: CurrentUser = Depends(require_superadmin),
    session: AsyncSession = Depends(get_session),
):
    """Relance l'ingestion d'un document depuis son URL d'origine (rafraîchit le contenu)."""
    doc = await session.get(LegalDocument, document_id)
    if not doc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document introuvable")
    url = doc.source_url or (doc.title if str(doc.title).startswith("http") else None)
    if not url:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            "Pas d'URL d'origine : ce document (fichier/texte) ne peut pas être relancé.")
    # Supprime l'ancien contenu puis crée un job de ré-ingestion
    await session.execute(text("DELETE FROM rag.chunks WHERE document_id = :d"), {"d": str(document_id)})
    await session.delete(doc)
    job = IngestJob(kind="url", source=url, title=doc.title, source_type=doc.source_type)
    session.add(job)
    await session.flush()
    jid = str(job.id)
    await session.commit()
    await get_event_bus().publish("ingest.requested", {"job_id": jid})
    return {"job": jid}


@router.delete("/admin/documents/demo/all")
async def admin_delete_demo_documents(
    _: CurrentUser = Depends(require_superadmin), session: AsyncSession = Depends(get_session)
):
    """Supprime d'un coup tous les documents de démonstration (titre/source contenant « démo »)."""
    rows = await session.scalars(select(LegalDocument))
    ids = [d.id for d in rows if "démo" in (d.title or "").lower() or "demo" in (d.title or "").lower()]
    # Inclut aussi les chunks de démo par code_source
    await session.execute(
        text("DELETE FROM rag.chunks WHERE lower(coalesce(code_source,'')) LIKE '%démo%' "
             "OR lower(coalesce(code_source,'')) LIKE '%demo%' OR document_id = ANY(:ids)"),
        {"ids": ids},
    )
    for did in ids:
        d = await session.get(LegalDocument, did)
        if d:
            await session.delete(d)
    await session.commit()
    return {"deleted_documents": len(ids)}


@router.post("/admin/import-files", status_code=202)
async def admin_import_files(
    files: list[UploadFile] = File(...),
    source_type: str = Form("loi"),
    _: CurrentUser = Depends(require_superadmin),
    session: AsyncSession = Depends(get_session),
):
    """Stocke les fichiers puis crée un JOB d'arrière-plan par fichier (extraction + indexation)."""
    from agoraci.common.storage import put_import

    created = []
    for f in files:
        data = await f.read()
        ext = (f.filename or "").rsplit(".", 1)[-1].lower() if "." in (f.filename or "") else "bin"
        key = await run_in_threadpool(put_import, data, ext=ext, content_type=f.content_type or "application/octet-stream")
        job = IngestJob(kind="file", source=key, title=(f.filename or "fichier")[:255], source_type=source_type)
        session.add(job)
        await session.flush()
        created.append(str(job.id))
    await session.commit()
    for jid in created:
        await get_event_bus().publish("ingest.requested", {"job_id": jid})
    return {"jobs": created}


class ImportUrl(BaseModel):
    url: str
    title: str | None = None
    source_type: str = "loi"


@router.post("/admin/import-url", status_code=202)
async def admin_import_url(
    payload: ImportUrl,
    _: CurrentUser = Depends(require_superadmin),
    session: AsyncSession = Depends(get_session),
):
    """Crée un JOB d'arrière-plan pour ingérer une page web / PDF en ligne."""
    job = IngestJob(kind="url", source=payload.url.strip(),
                    title=(payload.title or None), source_type=payload.source_type)
    session.add(job)
    await session.flush()
    jid = str(job.id)
    await session.commit()
    await get_event_bus().publish("ingest.requested", {"job_id": jid})
    return {"jobs": [jid]}


class ImportText(BaseModel):
    title: str
    content: str
    source_type: str = "loi"


@router.post("/admin/ingest-text", status_code=202)
async def admin_ingest_text(
    payload: ImportText,
    _: CurrentUser = Depends(require_superadmin),
    session: AsyncSession = Depends(get_session),
):
    """Crée un JOB d'arrière-plan pour un texte collé manuellement."""
    if not payload.content.strip():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Contenu vide.")
    job = IngestJob(kind="text", source=payload.content,
                    title=payload.title[:255] or "Document", source_type=payload.source_type)
    session.add(job)
    await session.flush()
    jid = str(job.id)
    await session.commit()
    await get_event_bus().publish("ingest.requested", {"job_id": jid})
    return {"jobs": [jid]}


async def _sparse_ids(session: AsyncSession, question: str, limit: int) -> list:
    # Construit une requête OU par mot (chaque article étant un chunk distinct, le ET
    # de plainto_tsquery est trop strict). plainto_tsquery gère les mots vides.
    words = [w for w in re.findall(r"\w+", question, flags=re.UNICODE) if len(w) >= 3][:12]
    if not words:
        words = [question]
    or_expr = " || ".join(f"plainto_tsquery('french', unaccent(:w{i}))" for i in range(len(words)))
    params: dict = {f"w{i}": w for i, w in enumerate(words)}
    params["k"] = limit
    params["fresh_m"] = int(os.getenv("COMMUNITY_FRESHNESS_MONTHS", "24"))
    rows = await session.execute(
        text(
            f"SELECT id FROM rag.chunks "
            f"WHERE tsv @@ ({or_expr}) "
            # Fraîcheur : jamais de contenu abrogé, ni de réponse communautaire trop ancienne.
            f"AND est_abroge = false "
            f"AND (coalesce(code_source,'') <> 'Communauté' OR indexed_at >= now() - make_interval(months => :fresh_m)) "
            f"ORDER BY ts_rank(tsv, ({or_expr})) DESC LIMIT :k"
        ),
        params,
    )
    return list(rows.scalars().all())


async def _hybrid_search(session: AsyncSession, question: str, top_k: int) -> list[Chunk]:
    """Recherche hybride dense (pgvector) + sparse (tsvector) via RRF.

    Si aucun fournisseur d'embeddings réel n'est configuré, on s'appuie
    uniquement sur la recherche par mots-clés (évite le bruit des vecteurs factices).
    """
    sparse_ids = await _sparse_ids(session, question, top_k * 2)

    if not EMBEDDINGS_ENABLED:
        ids = sparse_ids[:top_k]
        by_id = {c.id: c for c in await session.scalars(select(Chunk).where(Chunk.id.in_(ids)))}
        return [by_id[i] for i in ids if i in by_id]

    q_vec = await embed(question)
    cutoff = datetime.now(UTC) - timedelta(days=30 * int(os.getenv("COMMUNITY_FRESHNESS_MONTHS", "24")))
    fresh = or_(func.coalesce(Chunk.code_source, "") != "Communauté", Chunk.indexed_at >= cutoff)
    dense_rows = list(
        await session.scalars(
            select(Chunk).where(Chunk.est_abroge.is_(False), fresh)
            .order_by(Chunk.embedding.cosine_distance(q_vec)).limit(top_k * 2)
        )
    )

    # RRF : score = somme(1 / (K + rang)) sur chaque liste
    K = 60
    scores: dict[uuid.UUID, float] = {}
    by_id: dict[uuid.UUID, Chunk] = {}
    for rank, c in enumerate(dense_rows):
        scores[c.id] = scores.get(c.id, 0) + 1 / (K + rank)
        by_id[c.id] = c
    for rank, cid in enumerate(sparse_ids):
        scores[cid] = scores.get(cid, 0) + 1 / (K + rank)

    missing = [cid for cid in scores if cid not in by_id]
    if missing:
        for c in await session.scalars(select(Chunk).where(Chunk.id.in_(missing))):
            by_id[c.id] = c

    # Léger boost selon le type de source : loi/code prioritaires sur la jurisprudence
    doc_ids = {c.document_id for c in by_id.values() if c.document_id}
    if doc_ids:
        type_rows = await session.execute(
            select(LegalDocument.id, LegalDocument.source_type).where(LegalDocument.id.in_(doc_ids))
        )
        types = {did: (st or "") for did, st in type_rows}
        BOOST = {"code": 0.020, "loi": 0.015, "decret": 0.005, "jurisprudence": -0.005}
        for cid, c in by_id.items():
            scores[cid] = scores.get(cid, 0) + BOOST.get(types.get(c.document_id, ""), 0)

    ranked = sorted(scores, key=lambda i: scores[i], reverse=True)[:top_k]
    return [by_id[i] for i in ranked if i in by_id]


@router.post("/ask")
@limiter.limit("20/minute")
async def ask(request: Request, payload: AskRequest, session: AsyncSession = Depends(get_session)):
    # Quota quotidien Nanan (par utilisateur si connecté, sinon par IP) — réglable en admin.
    user = await get_optional_user(request)
    uid = user.id if user else None
    await check_nanan_quota(request, session, uid)

    chunks = await _hybrid_search(session, payload.question, payload.top_k)
    passages = [
        {
            "content": c.content,
            "code_source": c.code_source,
            "numero_article": c.numero_article,
            "titre_hierarchie": c.titre_hierarchie,
        }
        for c in chunks
    ]
    from .providers import LLMUnavailable
    try:
        answer = await generate_answer(payload.question, passages, payload.mode, payload.history)
    except LLMUnavailable:
        # Échec IA → message simple, SANS citer de sources (inutiles dans ce cas)
        return {
            "answer": "⏳ Le service IA est momentanément indisponible. Réessayez dans un instant.",
            "sources": [], "error": True,
        }
    await bump_nanan_quota(request, session, uid)  # ne compte que les réponses réussies
    return {"answer": answer, "sources": passages}
