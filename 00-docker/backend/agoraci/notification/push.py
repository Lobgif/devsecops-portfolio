"""Envoi de notifications Web Push (VAPID) via pywebpush."""
import json
import logging
import os

logger = logging.getLogger("push")

VAPID_PUBLIC_KEY = os.getenv("VAPID_PUBLIC_KEY", "")
VAPID_PRIVATE_KEY = os.getenv("VAPID_PRIVATE_KEY", "")
VAPID_SUBJECT = os.getenv("VAPID_SUBJECT", "mailto:admin@agoraci.ci")

PUSH_ENABLED = bool(VAPID_PUBLIC_KEY and VAPID_PRIVATE_KEY)


def send_web_push(sub: dict, payload: dict) -> bool:
    """Envoie un push à un abonnement. Retourne False si l'abonnement est mort (410/404)."""
    if not PUSH_ENABLED:
        return True
    try:
        from pywebpush import webpush

        webpush(
            subscription_info=sub,
            data=json.dumps(payload),
            vapid_private_key=VAPID_PRIVATE_KEY,
            vapid_claims={"sub": VAPID_SUBJECT},
        )
        return True
    except Exception as exc:  # noqa: BLE001
        # 404/410 = abonnement expiré → à supprimer
        status = getattr(getattr(exc, "response", None), "status_code", None)
        if status in (404, 410):
            return False
        logger.error("Web push échoué: %s", exc)
        return True
