"""Fabrique d'application FastAPI commune à tous les services.

Fournit : endpoint /health, logging, rate limiting (slowapi), middleware de
session optionnel (OAuth), et hooks de cycle de vie pour le bus d'événements.
"""
import logging
from collections.abc import Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.middleware.sessions import SessionMiddleware

from .config import get_settings
from .messaging import get_event_bus
from .ratelimit import limiter


def create_app(
    title: str,
    *,
    on_startup: Callable | None = None,
    use_event_bus: bool = True,
    enable_sessions: bool = False,
) -> FastAPI:
    settings = get_settings()
    logging.basicConfig(level=settings.log_level)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if use_event_bus:
            await get_event_bus().connect()
        if on_startup:
            await on_startup()
        yield
        if use_event_bus:
            await get_event_bus().close()

    app = FastAPI(title=title, lifespan=lifespan)

    # Rate limiting (slowapi) — limites par défaut + décorateurs par endpoint
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

    # CORS (activé seulement si CORS_ORIGINS est défini) — avec cookies (credentials)
    cors_origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
    if cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=cors_origins,
            allow_credentials=True,        # nécessaire pour les cookies httpOnly
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # Sessions (requis par Authlib pour l'état OAuth)
    if enable_sessions:
        app.add_middleware(SessionMiddleware, secret_key=settings.session_secret)

    @app.get("/health", tags=["infra"])
    async def health() -> dict:
        return {"status": "ok", "service": title, "env": settings.env}

    return app
