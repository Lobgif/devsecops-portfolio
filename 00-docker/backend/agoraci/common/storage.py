"""Stockage objet (MinIO/S3) pour les fichiers publics : avatars, images de posts.

Le bucket public est servi en lecture anonyme via Traefik sous /{bucket}/...
(ex: /media/avatars/xxx.png). Seul le binaire va ici — jamais de données sensibles.
"""
import json
import logging
import uuid

import boto3
from botocore.client import Config

from .config import get_settings

logger = logging.getLogger("storage")
settings = get_settings()
_client = None


def get_s3():
    global _client
    if _client is None:
        scheme = "https" if settings.minio_secure else "http"
        _client = boto3.client(
            "s3",
            endpoint_url=f"{scheme}://{settings.minio_endpoint}",
            aws_access_key_id=settings.minio_root_user,
            aws_secret_access_key=settings.minio_root_password,
            config=Config(signature_version="s3v4"),
            region_name="us-east-1",
        )
    return _client


def ensure_public_bucket() -> None:
    """Crée le bucket public (idempotent) et applique une politique de lecture anonyme."""
    s3 = get_s3()
    bucket = settings.minio_public_bucket
    try:
        s3.head_bucket(Bucket=bucket)
    except Exception:  # noqa: BLE001
        try:
            s3.create_bucket(Bucket=bucket)
        except Exception as exc:  # noqa: BLE001
            logger.warning("création bucket %s: %s", bucket, exc)
    policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow", "Principal": {"AWS": ["*"]},
            "Action": ["s3:GetObject"], "Resource": [f"arn:aws:s3:::{bucket}/*"],
        }],
    }
    try:
        s3.put_bucket_policy(Bucket=bucket, Policy=json.dumps(policy))
    except Exception as exc:  # noqa: BLE001
        logger.warning("politique bucket %s: %s", bucket, exc)
    logger.info("Bucket public MinIO prêt: %s", bucket)


def upload_public(data: bytes, *, prefix: str, ext: str, content_type: str) -> str:
    """Stocke un binaire et renvoie son URL publique (relative, servie par Traefik)."""
    s3 = get_s3()
    bucket = settings.minio_public_bucket
    key = f"{prefix}/{uuid.uuid4().hex}.{ext.lstrip('.')}"
    s3.put_object(Bucket=bucket, Key=key, Body=data, ContentType=content_type)
    # MEDIA_BASE_URL absolu (ex. Cloudflare R2 public) → URL complète ; sinon chemin /media (Traefik local)
    base = (settings.media_base_url or "").rstrip("/")
    if base.startswith("http"):
        return f"{base}/{key}"
    return f"/{bucket}/{key}"


def put_import(data: bytes, *, ext: str, content_type: str) -> str:
    """Stocke un fichier à ingérer (préfixe imports/) et renvoie sa clé (pour le job d'arrière-plan)."""
    s3 = get_s3()
    key = f"imports/{uuid.uuid4().hex}.{ext.lstrip('.')}"
    s3.put_object(Bucket=settings.minio_public_bucket, Key=key, Body=data, ContentType=content_type)
    return key


def get_object(key: str) -> bytes:
    """Récupère le contenu binaire d'un objet (utilisé par le consumer d'ingestion)."""
    s3 = get_s3()
    return s3.get_object(Bucket=settings.minio_public_bucket, Key=key)["Body"].read()
