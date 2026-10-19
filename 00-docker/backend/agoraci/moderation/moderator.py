"""Modération de contenu multilingue (français, nouchi, langues locales).

Stratégie :
  1. Classification par LLM (provider-agnostic) avec un prompt qui prend en compte
     le contexte ivoirien (français, nouchi, argot local) — meilleur recours pour le
     nouchi, non couvert par les modèles toxiques classiques.
  2. Repli sur un lexique léger si aucun LLM n'est configuré ou en cas d'erreur.

Tout est piloté par variables d'environnement (mêmes que le rag-service) :
  LLM_PROVIDER, LLM_API_KEY, LLM_MODEL, OLLAMA_BASE_URL, ANTHROPIC_VERSION.
"""
import json
import logging
import os
import re

import httpx

logger = logging.getLogger("moderation")

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "").lower()
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "claude-sonnet-4-5")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
ANTHROPIC_VERSION = os.getenv("ANTHROPIC_VERSION", "2023-06-01")

# Fournisseurs « compatibles OpenAI » (mêmes appels, base URL différente) — dont gemini
_OPENAI_COMPAT_BASES = {
    "openai": "https://api.openai.com/v1",
    "mistral": "https://api.mistral.ai/v1",
    "gemini": "https://generativelanguage.googleapis.com/v1beta/openai",
    "groq": "https://api.groq.com/openai/v1",
}
LLM_BASE_URL = os.getenv("LLM_BASE_URL") or _OPENAI_COMPAT_BASES.get(LLM_PROVIDER, "")

# Seuil au-delà duquel le contenu est signalé
THRESHOLD = float(os.getenv("MODERATION_THRESHOLD", "0.6"))

# Lexique de repli (à enrichir) — fr + nouchi
LEXICON = {w.strip().lower() for w in os.getenv("MODERATION_LEXICON", "").split(",") if w.strip()}

PROMPT = (
    "Tu es un modérateur de contenu pour une plateforme citoyenne ivoirienne. "
    "Le texte peut être en français, en nouchi (argot ivoirien) ou en langue locale. "
    "Évalue s'il contient des propos haineux, injurieux, harcelants, ou incitant à la "
    "violence. Réponds STRICTEMENT en JSON : "
    '{"toxic": true|false, "score": 0.0-1.0, "categories": ["..."]}.'
)


def _lexicon_check(content: str) -> dict:
    lowered = content.lower()
    hits = [w for w in LEXICON if w in lowered]
    score = min(1.0, len(hits) * 0.5)
    return {"flagged": score >= THRESHOLD, "score": score, "reasons": hits, "engine": "lexicon"}


async def _llm_classify(content: str) -> dict:
    user = f"Texte à évaluer :\n\"\"\"\n{content}\n\"\"\""
    if LLM_PROVIDER == "anthropic":
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.post(
                "https://api.anthropic.com/v1/messages",
                headers={"x-api-key": LLM_API_KEY, "anthropic-version": ANTHROPIC_VERSION},
                json={
                    "model": LLM_MODEL,
                    "max_tokens": 200,
                    "system": PROMPT,
                    "messages": [{"role": "user", "content": user}],
                },
            )
            r.raise_for_status()
            raw = r.json()["content"][0]["text"]
    elif LLM_PROVIDER in _OPENAI_COMPAT_BASES and LLM_BASE_URL:
        # openai, mistral, gemini, groq — API compatible OpenAI
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.post(
                f"{LLM_BASE_URL}/chat/completions",
                headers={"Authorization": f"Bearer {LLM_API_KEY}"},
                json={
                    "model": LLM_MODEL,
                    "messages": [
                        {"role": "system", "content": PROMPT},
                        {"role": "user", "content": user},
                    ],
                },
            )
            r.raise_for_status()
            raw = r.json()["choices"][0]["message"]["content"]
    elif LLM_PROVIDER == "ollama":
        async with httpx.AsyncClient(timeout=60) as c:
            r = await c.post(
                f"{OLLAMA_BASE_URL}/api/chat",
                json={
                    "model": LLM_MODEL,
                    "stream": False,
                    "format": "json",
                    "messages": [
                        {"role": "system", "content": PROMPT},
                        {"role": "user", "content": user},
                    ],
                },
            )
            r.raise_for_status()
            raw = r.json()["message"]["content"]
    else:
        raise RuntimeError("Aucun LLM configuré")

    # Parsing tolérant : certains modèles entourent le JSON de texte/```json
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if not m:
            raise
        data = json.loads(m.group(0))
    score = float(data.get("score", 0))
    return {
        "flagged": bool(data.get("toxic")) or score >= THRESHOLD,
        "score": score,
        "reasons": data.get("categories", []),
        "engine": f"llm:{LLM_PROVIDER}",
    }


async def analyze(content: str) -> dict:
    """Analyse un contenu et retourne un verdict de modération."""
    if not content.strip():
        return {"flagged": False, "score": 0.0, "reasons": [], "engine": "empty"}
    if LLM_PROVIDER and (LLM_API_KEY or LLM_PROVIDER == "ollama"):
        try:
            return await _llm_classify(content)
        except Exception as exc:  # noqa: BLE001
            logger.error("Classification LLM échouée: %s — repli lexique", exc)
    return _lexicon_check(content)
