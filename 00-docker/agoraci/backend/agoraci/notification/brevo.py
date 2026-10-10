"""Client Brevo (ex-Sendinblue) — API HTTP transactionnelle v3.

Mode d'authentification : **clé API** (header `api-key`).
Toutes les valeurs proviennent des variables d'environnement (aucune en dur) :

    BREVO_API_KEY        clé API transactionnelle (xkeysib-...)
    BREVO_SENDER_NAME    nom de l'expéditeur
    BREVO_SENDER_EMAIL   email expéditeur (vérifié dans Brevo)
    BREVO_API_URL        (optionnel) défaut https://api.brevo.com/v3/smtp/email

On peut envoyer soit un contenu HTML, soit un `templateId` Brevo + variables.
"""
import logging
import os
import re

import httpx

logger = logging.getLogger("brevo")

BREVO_API_URL = os.getenv("BREVO_API_URL", "https://api.brevo.com/v3/smtp/email")
BREVO_API_KEY = os.getenv("BREVO_API_KEY", "")
BREVO_SENDER_NAME = os.getenv("BREVO_SENDER_NAME", "Jamakan")
BREVO_SENDER_EMAIL = os.getenv("BREVO_SENDER_EMAIL", "noreply@kaedys.com")


def _email_layout(body_html: str) -> str:
    """Enveloppe un fragment HTML dans un e-mail Jamakan minimaliste et responsive (styles inline)."""
    return (
        "<!doctype html><html lang='fr'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'></head>"
        "<body style='margin:0;padding:0;background:#f1f5f9;"
        "font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,Helvetica,Arial,sans-serif;color:#1e293b;'>"
        "<table role='presentation' width='100%' cellpadding='0' cellspacing='0' style='background:#f1f5f9;padding:24px 12px;'>"
        "<tr><td align='center'>"
        "<table role='presentation' width='100%' cellpadding='0' cellspacing='0' "
        "style='max-width:480px;background:#ffffff;border-radius:16px;overflow:hidden;box-shadow:0 1px 3px rgba(15,23,42,.08);'>"
        "<tr><td style='background:#F77F00;background:linear-gradient(135deg,#F77F00,#009E60);padding:22px;text-align:center;'>"
        "<span style='font-size:20px;font-weight:800;color:#ffffff;letter-spacing:.3px;'>Jamakan</span></td></tr>"
        f"<tr><td style='padding:32px 28px;'>{body_html}</td></tr>"
        "<tr><td style='padding:18px 28px;border-top:1px solid #e2e8f0;text-align:center;"
        "font-size:12px;color:#94a3b8;line-height:1.5;'>"
        "Jamakan — la voix du peuple.<br>Plateforme citoyenne collaborative pour la Côte d'Ivoire.</td></tr>"
        "</table>"
        "<p style='max-width:480px;margin:14px auto 0;text-align:center;font-size:11px;color:#94a3b8;line-height:1.5;'>"
        "Vous recevez cet e-mail suite à une action effectuée avec cette adresse sur Jamakan.</p>"
        "</td></tr></table></body></html>"
    )


def _html_to_text(html: str) -> str:
    """Version texte brut d'un fragment HTML (améliore la délivrabilité : partie text/plain)."""
    text = re.sub(r"(?i)<br\s*/?>", "\n", html)
    text = re.sub(r"(?i)</(p|h1|h2|h3|div|li|a)>", "\n", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = (text.replace("&nbsp;", " ").replace("&amp;", "&")
                .replace("&lt;", "<").replace("&gt;", ">").replace("&#39;", "'"))
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


async def send_email(
    to_email: str,
    to_name: str | None = None,
    *,
    subject: str | None = None,
    html_content: str | None = None,
    text_content: str | None = None,
    template_id: int | None = None,
    params: dict | None = None,
) -> bool:
    """Envoie un email transactionnel via l'API Brevo.

    Utiliser soit (subject + html_content), soit (template_id + params).
    Retourne True si l'envoi est accepté par Brevo (HTTP 2xx).
    """
    if not BREVO_API_KEY:
        logger.warning("BREVO_API_KEY absente — email vers %s ignoré (mode dev)", to_email)
        return False

    payload: dict = {
        "sender": {"name": BREVO_SENDER_NAME, "email": BREVO_SENDER_EMAIL},
        "to": [{"email": to_email, **({"name": to_name} if to_name else {})}],
    }
    if template_id is not None:
        payload["templateId"] = template_id
        if params:
            payload["params"] = params
    else:
        body = html_content or ""
        payload["subject"] = subject or "Notification Jamakan"
        # On enveloppe le fragment dans un e-mail Jamakan complet + version texte (meilleure délivrabilité).
        payload["htmlContent"] = _email_layout(body)
        payload["textContent"] = text_content or (_html_to_text(body) + "\n\n— Jamakan, la voix du peuple.")

    headers = {
        "api-key": BREVO_API_KEY,
        "accept": "application/json",
        "content-type": "application/json",
    }

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(BREVO_API_URL, json=payload, headers=headers)
    if resp.is_success:
        logger.info("Email Brevo envoyé à %s (msgId=%s)", to_email, resp.json().get("messageId"))
        return True
    logger.error("Échec Brevo (%s): %s", resp.status_code, resp.text)
    return False
