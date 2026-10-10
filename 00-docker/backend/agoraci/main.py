"""Point d'entrée unique du backend Jamakan (monolithe modulaire).

Une seule application FastAPI = une seule image Docker, mais le code reste
organisé par domaine (auth, forum, rag, moderation, notification, chat).
Les échanges asynchrones passent toujours par RabbitMQ (consumers internes).
"""
import logging
import os

# Import des modèles pour que Base.metadata soit complet (création/migrations)
from agoraci.auth import models as _auth_models  # noqa: F401
from agoraci.auth.bootstrap import ensure_superadmin
from agoraci.auth.routes import router as auth_router
from agoraci.chat.ws import router as chat_router
from agoraci.chat.ws import start_chat_listener
from agoraci.common import create_app, get_settings
from agoraci.common.storage import ensure_public_bucket
from agoraci.core import models as _core_models  # noqa: F401
from agoraci.core.bootstrap import ensure_defaults
from agoraci.core.routes import router as core_router
from agoraci.forum import models as _forum_models  # noqa: F401
from agoraci.forum.executor import start_decision_consumer, start_deletion_sweeper
from agoraci.forum.routes import router as forum_router
from agoraci.messages import models as _msg_models  # noqa: F401
from agoraci.messages.routes import router as messages_router
from agoraci.moderation.consumer import start_moderation_consumer
from agoraci.moderation.routes import router as moderation_router
from agoraci.notification import models as _notif_models  # noqa: F401
from agoraci.notification.consumer import start_notification_consumer
from agoraci.notification.routes import router as notification_router
from agoraci.rag import models as _rag_models  # noqa: F401
from agoraci.rag.jobs import start_ingest_consumer
from agoraci.rag.routes import router as rag_router
from agoraci.uploads.routes import router as uploads_router

logger = logging.getLogger("agoraci")
settings = get_settings()

# Suivi d'erreurs (Sentry) — instrumente automatiquement FastAPI/Starlette.
# DSN par défaut (projet agoraci-backend), surchargeable par la variable SENTRY_DSN.
# Un DSN n'est pas un secret d'accès (clé d'ingestion en écriture seule).
# Init DÉFENSIF : toute erreur (module absent, init KO) est ignorée → ne peut JAMAIS
# empêcher le backend de démarrer.
_sentry_dsn = os.getenv(
    "SENTRY_DSN",
    "https://66b903876273c4c3cf6c834463e495da@o4512086570893312.ingest.de.sentry.io/4512086590488656",
).strip()
if _sentry_dsn:
    try:
        import sentry_sdk

        sentry_sdk.init(
            dsn=_sentry_dsn,
            environment=os.getenv("ENV", "production"),
            traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0") or 0),
            send_default_pii=False,  # ne pas envoyer de données personnelles
        )
        logger.info("Sentry activé (suivi d'erreurs).")
    except Exception as exc:  # noqa: BLE001
        logger.warning("Sentry non initialisé (ignoré, backend démarre quand même): %s", exc)


async def _startup() -> None:
    # Le schéma est géré par Alembic (appliqué au démarrage du conteneur, avant uvicorn).
    # Super-admin défini dans l'environnement (idempotent).
    try:
        await ensure_superadmin()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Bootstrap super-admin ignoré: %s", exc)
    try:
        await ensure_defaults()  # paramètres du site + glossaire
    except Exception as exc:  # noqa: BLE001
        logger.warning("Bootstrap paramètres/glossaire ignoré: %s", exc)
    try:
        ensure_public_bucket()  # bucket MinIO public (avatars/images)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Bootstrap bucket MinIO ignoré: %s", exc)
    # Consumers d'événements internes + écoute chat (Redis pub/sub).
    await start_moderation_consumer()
    await start_notification_consumer()
    await start_decision_consumer()
    await start_deletion_sweeper()
    await start_chat_listener()
    await start_ingest_consumer()


# enable_sessions=True : requis par Authlib (OAuth Google)
app = create_app("agoraci-backend", on_startup=_startup, enable_sessions=True)

for _router in (
    auth_router, forum_router, rag_router, moderation_router,
    notification_router, messages_router, core_router, chat_router,
    uploads_router,
):
    app.include_router(_router)
