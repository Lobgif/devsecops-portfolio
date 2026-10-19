"""Consumer de notifications : emails (Brevo) + notifications in-app."""
import logging
import os
import re
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from agoraci.auth.models import User
from agoraci.common.db import get_engine
from agoraci.common.messaging import get_event_bus
from agoraci.forum.models import Follow

from .brevo import send_email
from .models import Notification, PushSubscription
from .push import send_web_push

logger = logging.getLogger("notification")

TPL_WELCOME = os.getenv("BREVO_TEMPLATE_WELCOME")
TPL_VERIFY = os.getenv("BREVO_TEMPLATE_VERIFY")
MODERATOR_EMAIL = os.getenv("MODERATOR_ALERT_EMAIL", "")

_maker = None


def _sessionmaker():
    global _maker
    if _maker is None:
        _maker = async_sessionmaker(get_engine(), expire_on_commit=False, class_=AsyncSession)
    return _maker


# --------------------------- Emails (Brevo) ---------------------------
async def _send_emails(routing_key: str, payload: dict) -> None:
    if routing_key == "user.registration_code":
        await send_email(
            to_email=payload.get("email", ""), to_name=payload.get("username"),
            subject="Votre code de vérification Jamakan",
            html_content=(
                "<h1 style='margin:0 0 14px;font-size:20px;color:#0f172a;'>Vérifiez votre compte</h1>"
                f"<p style='margin:0 0 16px;line-height:1.6;'>Bonjour {payload.get('username','')}, et bienvenue sur Jamakan — la plateforme d'échange citoyenne pour les Ivoiriens. Pour activer votre compte, saisissez le code de vérification ci-dessous dans l'application.</p>"
                "<div style='margin:24px 0;text-align:center;'>"
                f"<span style='display:inline-block;background:#f8fafc;border:1px solid #e2e8f0;border-radius:12px;padding:16px 26px;font-size:30px;font-weight:800;letter-spacing:8px;color:#F77F00;'>{payload.get('code','')}</span>"
                "</div>"
                f"<p style='margin:0;line-height:1.6;color:#64748b;font-size:14px;'>Ce code est valable {payload.get('ttl_minutes',15)} minutes. Si vous n'êtes pas à l'origine de cette demande, vous pouvez ignorer cet e-mail en toute sécurité — aucun compte ne sera activé sans ce code.</p>"
            ),
            template_id=int(TPL_VERIFY) if TPL_VERIFY else None,
            params={"username": payload.get("username"), "code": payload.get("code")},
        )
    elif routing_key == "user.registered":
        await send_email(
            to_email=payload.get("email", ""), to_name=payload.get("username"),
            subject="Bienvenue sur Jamakan",
            html_content=(
                f"<h1 style='margin:0 0 14px;font-size:20px;color:#0f172a;'>Bienvenue, {payload.get('username','')} 👋</h1>"
                "<p style='margin:0 0 16px;line-height:1.6;'>Votre compte Jamakan est activé. Vous pouvez dès maintenant poser vos questions, rejoindre des groupes et échanger avec la communauté sur tous les sujets du quotidien ivoirien.</p>"
                "<div style='margin:24px 0;text-align:center;'>"
                "<a href='https://jamakan.kaedys.com/forums' style='display:inline-block;background:#F77F00;color:#ffffff;text-decoration:none;font-weight:700;padding:12px 26px;border-radius:10px;'>Explorer les forums</a>"
                "</div>"
                "<p style='margin:0;line-height:1.6;color:#64748b;font-size:14px;'>Besoin d'aide ? Nanan, notre assistant IA, répond à vos questions ancrées dans le contexte ivoirien.</p>"
            ),
            template_id=int(TPL_WELCOME) if TPL_WELCOME else None,
            params={"username": payload.get("username")},
        )
    elif routing_key == "user.password_reset_code":
        await send_email(
            to_email=payload.get("email", ""), to_name=payload.get("username"),
            subject="Réinitialisation de votre mot de passe Jamakan",
            html_content=(
                "<h1 style='margin:0 0 14px;font-size:20px;color:#0f172a;'>Réinitialisation du mot de passe</h1>"
                f"<p style='margin:0 0 16px;line-height:1.6;'>Bonjour {payload.get('username','')}, vous avez demandé à réinitialiser votre mot de passe Jamakan. Saisissez le code ci-dessous dans l'application pour choisir un nouveau mot de passe.</p>"
                "<div style='margin:24px 0;text-align:center;'>"
                f"<span style='display:inline-block;background:#f8fafc;border:1px solid #e2e8f0;border-radius:12px;padding:16px 26px;font-size:30px;font-weight:800;letter-spacing:8px;color:#F77F00;'>{payload.get('code','')}</span>"
                "</div>"
                f"<p style='margin:0;line-height:1.6;color:#64748b;font-size:14px;'>Ce code est valable {payload.get('ttl_minutes',15)} minutes. Si vous n'êtes pas à l'origine de cette demande, ignorez cet e-mail — votre mot de passe restera inchangé.</p>"
            ),
        )

    elif routing_key == "content.flagged" and MODERATOR_EMAIL:
        await send_email(
            to_email=MODERATOR_EMAIL, subject="[Modération] Contenu signalé",
            html_content=f"<p>Un contenu a été signalé :</p><pre>{payload}</pre>",
        )


# --------------------------- Notifications in-app + push ---------------------------
async def _targets(session, routing_key: str, payload: dict) -> list[dict]:
    """Construit la liste des notifications à créer : {user_id, type, title, message, link}."""
    t: list[dict] = []
    if routing_key == "user.registered" and payload.get("user_id"):
        t.append({"user_id": uuid.UUID(payload["user_id"]), "type": "welcome",
                  "title": "Bienvenue sur Jamakan 👋",
                  "message": "Votre compte est créé. Posez votre première question !", "link": "/"})
    elif routing_key == "post.created":
        author, poster, did = payload.get("discussion_author_id"), payload.get("author_id"), payload.get("discussion_id")
        body = payload.get("body") or ""
        notified = {poster}
        if author and author != poster:
            t.append({"user_id": uuid.UUID(author), "type": "reply",
                      "title": "Nouvelle réponse à votre question",
                      "message": body[:160], "link": f"/discussion/{did}" if did else None})
            notified.add(author)
        # Abonnés à la discussion
        if did:
            followers = await session.scalars(select(Follow.user_id).where(
                Follow.target_type == "discussion", Follow.target_id == uuid.UUID(did)))
            for fid in followers:
                if str(fid) not in notified:
                    t.append({"user_id": fid, "type": "follow",
                              "title": "Nouvelle réponse (discussion suivie)",
                              "message": body[:160], "link": f"/discussion/{did}"})
                    notified.add(str(fid))
        # Mentions @utilisateur
        for username in set(re.findall(r"@([A-Za-z0-9_]{3,})", body)):
            u = await session.scalar(select(User).where(User.username == username))
            if u and str(u.id) not in notified:
                t.append({"user_id": u.id, "type": "mention",
                          "title": "Vous avez été mentionné·e",
                          "message": body[:160], "link": f"/discussion/{did}" if did else None})
                notified.add(str(u.id))

    elif routing_key == "discussion.created":
        gid, author, did = payload.get("group_id"), payload.get("author_id"), payload.get("discussion_id")
        if gid:
            followers = await session.scalars(select(Follow.user_id).where(
                Follow.target_type == "group", Follow.target_id == uuid.UUID(gid)))
            for fid in followers:
                if str(fid) != author:
                    t.append({"user_id": fid, "type": "follow",
                              "title": "Nouvelle discussion (groupe suivi)",
                              "message": payload.get("title", ""), "link": f"/discussion/{did}" if did else None})
    elif routing_key == "user.suspended" and payload.get("user_id"):
        reason = payload.get("reason")
        msg = "Votre compte a été temporairement suspendu par l'administration."
        if reason:
            msg += f" Motif : {reason}"
        t.append({"user_id": uuid.UUID(payload["user_id"]), "type": "warning",
                  "title": "Compte suspendu", "message": msg, "link": "/"})
    elif routing_key == "content.flagged":
        admins = await session.scalars(select(User.id).where(User.is_superadmin.is_(True)))
        for admin_id in admins:
            t.append({"user_id": admin_id, "type": "flagged", "title": "Contenu signalé",
                      "message": "Un contenu nécessite une revue de modération.", "link": "/"})
    elif routing_key == "message.created" and payload.get("recipient_id"):
        t.append({"user_id": uuid.UUID(payload["recipient_id"]), "type": "message",
                  "title": "Nouveau message privé", "message": payload.get("preview", ""),
                  "link": f"/messages/{payload.get('conversation_id')}"})
    return t


# Type de notif → clé de préférence (opt-out). Les autres types sont toujours envoyés.
_TYPE_PREF = {"reply": "replies", "mention": "mentions", "follow": "follows", "message": "messages"}


async def _filter_by_prefs(session, targets: list[dict]) -> list[dict]:
    """Retire les notifications désactivées par le destinataire dans ses préférences."""
    kept = []
    cache: dict = {}
    for tg in targets:
        pref_key = _TYPE_PREF.get(tg["type"])
        if not pref_key:
            kept.append(tg)
            continue
        uid = tg["user_id"]
        if uid not in cache:
            u = await session.get(User, uid)
            cache[uid] = (u.notif_prefs or {}) if u else {}
        if cache[uid].get(pref_key, True):
            kept.append(tg)
    return kept


async def _create_notifications(routing_key: str, payload: dict) -> None:
    async with _sessionmaker()() as session:
        targets = await _targets(session, routing_key, payload)
        targets = await _filter_by_prefs(session, targets)
        for tg in targets:
            session.add(Notification(**tg))
        await session.commit()

        # Web push vers chaque destinataire abonné
        for tg in targets:
            subs = await session.scalars(
                select(PushSubscription).where(PushSubscription.user_id == tg["user_id"])
            )
            for s in subs:
                alive = send_web_push(
                    {"endpoint": s.endpoint, "keys": {"p256dh": s.p256dh, "auth": s.auth}},
                    {"title": tg["title"], "message": tg["message"], "link": tg["link"]},
                )
                if not alive:
                    await session.delete(s)
        await session.commit()


async def _handle_event(routing_key: str, payload: dict) -> None:
    logger.info("Événement reçu [%s]", routing_key)
    try:
        await _send_emails(routing_key, payload)
    except Exception as exc:  # noqa: BLE001
        logger.error("Email (%s) échoué: %s", routing_key, exc)
    try:
        await _create_notifications(routing_key, payload)
    except Exception as exc:  # noqa: BLE001
        logger.error("Notif in-app (%s) échouée: %s", routing_key, exc)


async def start_notification_consumer() -> None:
    await get_event_bus().subscribe(
        queue_name="notifications.all",
        routing_keys=[
            "user.registration_code",
            "user.password_reset_code",
            "user.registered",
            "user.suspended",
            "discussion.created",
            "post.created",
            "content.flagged",
            "message.created",
        ],
        handler=_handle_event,
    )
