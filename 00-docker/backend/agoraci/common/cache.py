"""Accès Redis partagé (codes de vérification, cache, stockage rate-limit)."""
import redis.asyncio as redis

from .config import get_settings

_redis: redis.Redis | None = None


def get_redis() -> redis.Redis:
    global _redis
    if _redis is None:
        _redis = redis.from_url(get_settings().redis_url, decode_responses=True)
    return _redis
