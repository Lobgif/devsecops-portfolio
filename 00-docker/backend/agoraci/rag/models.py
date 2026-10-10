"""Modèles du service RAG (schéma `rag`).

Chunk juridique = un article de loi, avec son embedding (pgvector),
son index plein-texte (tsvector) et ses métadonnées de citation.
"""
import uuid
from datetime import date, datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import Boolean, Date, DateTime, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR, UUID
from sqlalchemy.orm import Mapped, mapped_column

from agoraci.common import Base

SCHEMA = "rag"
EMBEDDING_DIM = int(__import__("os").getenv("EMBEDDING_DIM", "1536"))


class LegalDocument(Base):
    """Document source (Code, loi, décret, jurisprudence)."""
    __tablename__ = "legal_documents"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255))
    source_type: Mapped[str] = mapped_column(String(50))   # code | loi | decret | jurisprudence
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    object_key: Mapped[str | None] = mapped_column(Text, nullable=True)  # clé MinIO/S3
    extra: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class IngestJob(Base):
    """Job d'ingestion en arrière-plan (URL, PDF en ligne, crawl de site)."""
    __tablename__ = "ingest_jobs"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    kind: Mapped[str] = mapped_column(String(20))          # url | crawl
    source: Mapped[str] = mapped_column(Text)              # URL (ou page index pour crawl)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_type: Mapped[str] = mapped_column(String(50), default="loi")
    crawl_filter: Mapped[str | None] = mapped_column(String(255), nullable=True)  # sous-chaîne des liens à suivre
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending|running|done|error|cancelled
    total: Mapped[int] = mapped_column(Integer, default=0)
    done: Mapped[int] = mapped_column(Integer, default=0)
    chunks: Mapped[int] = mapped_column(Integer, default=0)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Chunk(Base):
    """Fragment indexé (typiquement un article) prêt pour la recherche hybride."""
    __tablename__ = "chunks"
    __table_args__ = (
        Index("ix_rag_chunks_embedding", "embedding",
              postgresql_using="hnsw",
              postgresql_with={"m": 16, "ef_construction": 64},
              postgresql_ops={"embedding": "vector_cosine_ops"}),
        Index("ix_rag_chunks_tsv", "tsv", postgresql_using="gin"),
        {"schema": SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    content: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIM))
    tsv: Mapped[str | None] = mapped_column(TSVECTOR, nullable=True)

    # Métadonnées de citation
    code_source: Mapped[str | None] = mapped_column(String(120), nullable=True)
    numero_article: Mapped[str | None] = mapped_column(String(60), index=True, nullable=True)
    titre_hierarchie: Mapped[str | None] = mapped_column(Text, nullable=True)
    date_vigueur: Mapped[date | None] = mapped_column(Date, nullable=True)
    est_abroge: Mapped[bool] = mapped_column(Boolean, default=False)
    position: Mapped[int] = mapped_column(Integer, default=0)
    # Fraîcheur : date d'indexation (sert à écarter les réponses communautaires trop vieilles)
    indexed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
