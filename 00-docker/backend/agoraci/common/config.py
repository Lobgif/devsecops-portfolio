"""Configuration partagée, lue depuis l'environnement et les secrets Docker.

En production (Swarm), les valeurs sensibles sont montées dans /run/secrets
(ex: postgres_password, jwt_secret, rabbitmq_password) et lues automatiquement
grâce à `secrets_dir`. En local, elles viennent du fichier .env.
"""
import os
from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Secrets Docker (Swarm) : utilisé seulement si le dossier existe (évite un warning en local)
_SECRETS_DIR = "/run/secrets" if os.path.isdir("/run/secrets") else None


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        secrets_dir=_SECRETS_DIR,
        extra="ignore",
    )

    # Général
    env: str = "local"
    log_level: str = "INFO"
    service_name: str = "agoraci-service"

    # PostgreSQL (base unique, un schéma par service)
    postgres_user: str = "agoraci"
    postgres_password: str = "agoraci"
    postgres_host: str = "postgres"
    postgres_port: int = 5432
    postgres_db: str = "agoraci"

    # Redis
    redis_url: str = "redis://redis:6379/0"

    # CORS : vide = désactivé (même origine via Traefik). Sinon liste d'origines séparées
    # par des virgules (utile si frontend et backend sont sur des domaines différents, ex. Render).
    cors_origins: str = ""

    # Cloudflare Turnstile (anti-robot à l'inscription) — vide = désactivé
    turnstile_secret_key: str = ""

    # MinIO / stockage objet (avatars, images)
    minio_endpoint: str = "minio:9000"
    minio_root_user: str = "agoraci"
    minio_root_password: str = ""
    minio_public_bucket: str = "media"   # bucket public (lecture anonyme), servi via /media
    minio_secure: bool = False           # True si MinIO en HTTPS
    media_base_url: str = "/media"       # préfixe public des URLs (servi par Traefik)

    # RabbitMQ (URL construite à partir des composants si non fournie)
    rabbitmq_user: str = "agoraci"
    rabbitmq_password: str = "agoraci"
    rabbitmq_host: str = "rabbitmq"
    rabbitmq_port: int = 5672
    rabbitmq_vhost: str = "/"
    rabbitmq_url: str = ""
    rabbitmq_exchange: str = "agoraci.events"

    # JWT
    jwt_secret: str = "change_me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    # Timeout d'INACTIVITÉ : le refresh token glissant expire après N min sans activité (OWASP)
    refresh_idle_minutes: int = 30
    # Plafond ABSOLU : durée de vie max d'une session depuis la connexion, quoi qu'il arrive
    refresh_token_expire_days: int = 30

    # OAuth Google
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost/api/auth/google/callback"

    # Sessions (Authlib a besoin d'un middleware de session pour l'état OAuth)
    session_secret: str = "change_me_session"

    # Frontend (redirections post-OAuth / liens de vérification)
    frontend_url: str = "http://localhost"

    # Super-administrateur (créé/promu automatiquement au démarrage si défini)
    superadmin_email: str = ""
    superadmin_password: str = ""
    superadmin_username: str = "superadmin"

    # Vérification d'email
    verification_code_ttl_minutes: int = 15

    # Rate limiting (slowapi)
    rate_limit_default: str = "100/minute"

    @model_validator(mode="after")
    def _build_rabbitmq_url(self) -> "Settings":
        if not self.rabbitmq_url:
            vhost = self.rabbitmq_vhost.lstrip("/")
            self.rabbitmq_url = (
                f"amqp://{self.rabbitmq_user}:{self.rabbitmq_password}"
                f"@{self.rabbitmq_host}:{self.rabbitmq_port}/{vhost}"
            )
        return self

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
