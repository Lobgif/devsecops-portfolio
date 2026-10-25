"""Rate limiting partagé basé sur slowapi (stockage Redis, clé = IP client).

Usage dans un service :

    from agoraci.common.ratelimit import limiter

    @router.post("/login")
    @limiter.limit("5/minute")
    async def login(request: Request, ...):
        ...

Le `request: Request` est requis par slowapi pour identifier le client.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

from .config import get_settings

_settings = get_settings()

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=_settings.redis_url,
    default_limits=[_settings.rate_limit_default],
)
