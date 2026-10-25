"""Outils de sécurité partagés : hachage de mot de passe et JWT."""
from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt
from passlib.context import CryptContext

from .config import get_settings

_pwd = CryptContext(schemes=["argon2"], deprecated="auto")


def hash_password(password: str) -> str:
    return _pwd.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd.verify(plain, hashed)


def create_token(
    subject: str,
    expires_delta: timedelta,
    token_type: str,
    extra: dict | None = None,
) -> str:
    settings = get_settings()
    now = datetime.now(UTC)
    payload = {
        "sub": subject,
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
        **(extra or {}),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_access_token(subject: str, extra: dict | None = None) -> str:
    s = get_settings()
    return create_token(
        subject, timedelta(minutes=s.access_token_expire_minutes), "access", extra
    )


def create_refresh_token(subject: str, auth_time: int | None = None) -> str:
    """Refresh token GLISSANT : expire après `refresh_idle_minutes` d'inactivité.

    `auth_time` = horodatage (epoch) de la connexion initiale, reporté à chaque
    renouvellement pour faire respecter le plafond absolu (`refresh_token_expire_days`).
    """
    s = get_settings()
    if auth_time is None:
        auth_time = int(datetime.now(UTC).timestamp())
    return create_token(
        subject, timedelta(minutes=s.refresh_idle_minutes), "refresh",
        extra={"auth_time": auth_time},
    )


def decode_token(token: str) -> dict:
    settings = get_settings()
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:  # noqa: BLE001
        raise ValueError("Token invalide ou expiré") from exc
