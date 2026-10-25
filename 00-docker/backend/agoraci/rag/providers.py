"""Fournisseurs IA (embeddings + génération), pilotés par variables d'env.

Aucune clé en dur. Fournisseurs supportés :

  LLM_PROVIDER       = anthropic | openai | mistral | gemini | groq | ollama
  EMBEDDING_PROVIDER = openai | mistral | gemini | cohere | ollama

mistral/gemini/groq utilisent l'API « compatible OpenAI » (mêmes appels, base URL
différente). cohere et ollama ont leur propre API. Variables :

  LLM_API_KEY, LLM_MODEL, LLM_BASE_URL (override optionnel)
  EMBEDDING_API_KEY, EMBEDDING_MODEL, EMBEDDING_DIM, EMBEDDING_BASE_URL (override)
  OLLAMA_BASE_URL, ANTHROPIC_VERSION
"""
import hashlib
import logging
import os

import httpx

logger = logging.getLogger("rag.providers")

EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "").lower()
EMBEDDING_API_KEY = os.getenv("EMBEDDING_API_KEY", "")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "1536"))

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "").lower()
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "claude-sonnet-4-5")

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
ANTHROPIC_VERSION = os.getenv("ANTHROPIC_VERSION", "2023-06-01")

# Bases « compatibles OpenAI » par fournisseur
_OPENAI_COMPAT_BASES = {
    "openai": "https://api.openai.com/v1",
    "mistral": "https://api.mistral.ai/v1",
    "gemini": "https://generativelanguage.googleapis.com/v1beta/openai",
    "groq": "https://api.groq.com/openai/v1",
}
LLM_BASE_URL = os.getenv("LLM_BASE_URL") or _OPENAI_COMPAT_BASES.get(LLM_PROVIDER, "")
EMBEDDING_BASE_URL = os.getenv("EMBEDDING_BASE_URL") or _OPENAI_COMPAT_BASES.get(EMBEDDING_PROVIDER, "")

_OPENAI_COMPAT_LLM = {"openai", "mistral", "gemini", "groq"}
_OPENAI_COMPAT_EMBED = {"openai", "mistral", "gemini"}

# Vrais embeddings disponibles ? (sinon : recherche par mots-clés uniquement)
EMBEDDINGS_ENABLED = (
    EMBEDDING_PROVIDER == "ollama"
    or (EMBEDDING_PROVIDER in _OPENAI_COMPAT_EMBED and bool(EMBEDDING_API_KEY))
    or (EMBEDDING_PROVIDER == "cohere" and bool(EMBEDDING_API_KEY))
)

DISCLAIMER = (
    "\n\n---\nℹ️ *Information à titre indicatif. Pour une situation personnelle, "
    "rapprochez-vous d'un professionnel qualifié.*"
)

# Mode JURIDIQUE (page « IA Juridique ») — strictement droit ivoirien
SYSTEM_PROMPT_LEGAL = (
    "Tu es l'assistant juridique de Jamakan, spécialisé dans le DROIT IVOIRIEN (tous domaines : "
    "famille, travail, pénal, foncier, commercial/OHADA, fiscal, administratif…). "
    "Réponds en français clair et accessible. Appuie-toi STRICTEMENT sur les extraits de loi "
    "fournis et CITE les articles utilisés (numéro + code). N'invente JAMAIS un article. "
    "Si les extraits ne suffisent pas, dis-le honnêtement et invite à consulter un professionnel."
)

# Mode GÉNÉRAL (groupes) — élargi à tous les sujets de société
SYSTEM_PROMPT_GENERAL = (
    "Tu es Nanan, l'assistant IA de Jamakan, la plateforme citoyenne ivoirienne. Tu aides sur TOUS "
    "les sujets du quotidien en Côte d'Ivoire : démarches administratives, santé, éducation, emploi, "
    "business, finance, technologie, vie pratique, droit, famille, politique, culture… "
    "Réponds en français, de façon claire, utile, nuancée et respectueuse — sans jamais te limiter au droit.\n"
    "RÈGLES :\n"
    "- Questions PRATIQUES du quotidien (adresses, bons plans, cuisine, démarches, conseils…) : réponds "
    "UTILEMENT avec tes connaissances générales et le bon sens, même sans extrait fourni. Ne refuse pas "
    "en disant que ce n'est pas juridique. Précise que c'est une information générale et, si utile, où vérifier.\n"
    "- Sujets JURIDIQUES : appuie-toi STRICTEMENT sur les extraits de loi et cite les articles ; n'invente JAMAIS un article.\n"
    "- Sujets à débat (politique, religion, société) : présente plusieurs points de vue reconnus, avec neutralité et respect.\n"
    "- Les extraits « Communauté » sont des retours d'expérience de membres : distingue-les du savoir établi.\n"
    "Cite tes sources quand tu en as, et reste honnête sur tes limites."
)


# --------------------------- Embeddings ---------------------------
async def _embed_openai_compat(text: str) -> list[float]:
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.post(
            f"{EMBEDDING_BASE_URL}/embeddings",
            headers={"Authorization": f"Bearer {EMBEDDING_API_KEY}"},
            json={"model": EMBEDDING_MODEL, "input": text},
        )
        r.raise_for_status()
        return r.json()["data"][0]["embedding"]


async def _embed_cohere(text: str, input_type: str) -> list[float]:
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.post(
            "https://api.cohere.com/v2/embed",
            headers={"Authorization": f"Bearer {EMBEDDING_API_KEY}"},
            json={
                "model": EMBEDDING_MODEL,           # ex: embed-multilingual-v3.0
                "texts": [text],
                "input_type": input_type,           # search_document | search_query
                "embedding_types": ["float"],
            },
        )
        r.raise_for_status()
        return r.json()["embeddings"]["float"][0]


async def _embed_ollama(text: str) -> list[float]:
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(
            f"{OLLAMA_BASE_URL}/api/embeddings",
            json={"model": EMBEDDING_MODEL, "prompt": text},
        )
        r.raise_for_status()
        return r.json()["embedding"]


def _embed_fallback(text: str) -> list[float]:
    h = hashlib.sha256(text.encode()).digest()
    return [((h[i % len(h)] / 255.0) * 2 - 1) for i in range(EMBEDDING_DIM)]


async def embed(text: str, input_type: str = "search_query") -> list[float]:
    """input_type est utilisé par Cohere (search_document à l'ingestion, search_query aux requêtes)."""
    try:
        if EMBEDDING_PROVIDER in _OPENAI_COMPAT_EMBED and EMBEDDING_API_KEY:
            return await _embed_openai_compat(text)
        if EMBEDDING_PROVIDER == "cohere" and EMBEDDING_API_KEY:
            return await _embed_cohere(text, input_type)
        if EMBEDDING_PROVIDER == "ollama":
            return await _embed_ollama(text)
    except Exception as exc:  # noqa: BLE001
        logger.error("Embedding (%s) a échoué: %s — fallback", EMBEDDING_PROVIDER, exc)
    return _embed_fallback(text)


async def _embed_batch_cohere(texts: list[str], input_type: str) -> list[list[float]]:
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(
            "https://api.cohere.com/v2/embed",
            headers={"Authorization": f"Bearer {EMBEDDING_API_KEY}"},
            json={"model": EMBEDDING_MODEL, "texts": texts,
                  "input_type": input_type, "embedding_types": ["float"]},
        )
        r.raise_for_status()
        return r.json()["embeddings"]["float"]


async def _embed_batch_openai(texts: list[str]) -> list[list[float]]:
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(
            f"{EMBEDDING_BASE_URL}/embeddings",
            headers={"Authorization": f"Bearer {EMBEDDING_API_KEY}"},
            json={"model": EMBEDDING_MODEL, "input": texts},
        )
        r.raise_for_status()
        return [d["embedding"] for d in r.json()["data"]]


async def embed_batch(texts: list[str], input_type: str = "search_document") -> list[list[float]]:
    """Vectorise une liste de textes en un minimum d'appels (lots) — clé pour les gros documents."""
    if not texts:
        return []
    CHUNK = 64
    out: list[list[float]] = []
    for i in range(0, len(texts), CHUNK):
        batch = texts[i:i + CHUNK]
        try:
            if EMBEDDING_PROVIDER == "cohere" and EMBEDDING_API_KEY:
                out.extend(await _embed_batch_cohere(batch, input_type))
                continue
            if EMBEDDING_PROVIDER in _OPENAI_COMPAT_EMBED and EMBEDDING_API_KEY:
                out.extend(await _embed_batch_openai(batch))
                continue
        except Exception as exc:  # noqa: BLE001
            logger.error("Embedding batch (%s) échoué: %s — repli unitaire", EMBEDDING_PROVIDER, exc)
        # Repli : un par un (ollama ou erreur)
        for t in batch:
            out.append(await embed(t, input_type))
    return out


# --------------------------- Génération ---------------------------
def _build_user_prompt(question: str, passages: list[dict]) -> str:
    extraits = "\n\n".join(
        f"[{p.get('code_source', 'Source')} — art. {p.get('numero_article', '?')}]\n"
        f"{p.get('content', '')}"
        for p in passages
    ) or "(aucun extrait pertinent trouvé)"
    return f"Extraits de loi :\n{extraits}\n\nQuestion du citoyen : {question}"


def _clean_history(history: list[dict] | None) -> list[dict]:
    """Garde les derniers échanges valides (role user/assistant + content)."""
    out = []
    for m in (history or [])[-6:]:
        role, content = m.get("role"), m.get("content")
        if role in ("user", "assistant") and content:
            out.append({"role": role, "content": str(content)[:4000]})
    return out


async def _gen_anthropic(question: str, passages: list[dict], system: str, history: list[dict]) -> str:
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": LLM_API_KEY,
                "anthropic-version": ANTHROPIC_VERSION,
                "content-type": "application/json",
            },
            json={
                "model": LLM_MODEL,
                "max_tokens": 1024,
                "system": system,
                "messages": [*history, {"role": "user", "content": _build_user_prompt(question, passages)}],
            },
        )
        r.raise_for_status()
        return r.json()["content"][0]["text"]


_RETRY_STATUS = {429, 500, 502, 503, 504}


async def _post_json_retry(url: str, *, headers: dict, json: dict, timeout: int = 60, attempts: int = 3) -> httpx.Response:
    """POST avec réessais sur erreurs transitoires (surcharge/temporaire des fournisseurs IA)."""
    import asyncio
    last: Exception | None = None
    async with httpx.AsyncClient(timeout=timeout) as client:
        for i in range(attempts):
            try:
                r = await client.post(url, headers=headers, json=json)
                if r.status_code in _RETRY_STATUS:
                    last = httpx.HTTPStatusError(f"{r.status_code}", request=r.request, response=r)
                    await asyncio.sleep(1.5 * (i + 1))
                    continue
                r.raise_for_status()
                return r
            except (httpx.TransportError, httpx.TimeoutException) as exc:
                last = exc
                await asyncio.sleep(1.5 * (i + 1))
    raise last or RuntimeError("Échec de l'appel LLM")


async def _gen_openai_compat(question: str, passages: list[dict], system: str, history: list[dict]) -> str:
    r = await _post_json_retry(
        f"{LLM_BASE_URL}/chat/completions",
        headers={"Authorization": f"Bearer {LLM_API_KEY}"},
        json={
            "model": LLM_MODEL,
            "messages": [
                {"role": "system", "content": system},
                *history,
                {"role": "user", "content": _build_user_prompt(question, passages)},
            ],
        },
    )
    return r.json()["choices"][0]["message"]["content"]


async def _gen_ollama(question: str, passages: list[dict], system: str, history: list[dict]) -> str:
    async with httpx.AsyncClient(timeout=120) as client:
        r = await client.post(
            f"{OLLAMA_BASE_URL}/api/chat",
            json={
                "model": LLM_MODEL,
                "stream": False,
                "messages": [
                    {"role": "system", "content": system},
                    *history,
                    {"role": "user", "content": _build_user_prompt(question, passages)},
                ],
            },
        )
        r.raise_for_status()
        return r.json()["message"]["content"]


def _gen_fallback(question: str, passages: list[dict]) -> str:
    citations = "\n".join(
        f"- {p.get('code_source', 'Source')} — art. {p.get('numero_article', '?')}"
        for p in passages
    ) or "- (aucune source trouvée)"
    return (
        f"[Mode dégradé — aucun LLM configuré]\nQuestion : {question}\n\nSources pertinentes :\n{citations}"
    )


class LLMUnavailable(Exception):
    """Le LLM est configuré mais l'appel a échoué (surcharge/temporaire). Le caller décide quoi faire."""


def _llm_configured() -> bool:
    return (
        (LLM_PROVIDER == "anthropic" and bool(LLM_API_KEY))
        or (LLM_PROVIDER in _OPENAI_COMPAT_LLM and bool(LLM_API_KEY) and bool(LLM_BASE_URL))
        or (LLM_PROVIDER == "ollama")
    )


async def generate_answer(
    question: str, passages: list[dict], mode: str = "legal", history: list[dict] | None = None
) -> str:
    system = SYSTEM_PROMPT_LEGAL if mode == "legal" else SYSTEM_PROMPT_GENERAL
    hist = _clean_history(history)
    # Aucun LLM configuré (dev) → message dégradé informatif (sources). Pas une erreur.
    if not _llm_configured():
        return _gen_fallback(question, passages) + DISCLAIMER
    try:
        if LLM_PROVIDER == "anthropic":
            answer = await _gen_anthropic(question, passages, system, hist)
        elif LLM_PROVIDER == "ollama":
            answer = await _gen_ollama(question, passages, system, hist)
        else:
            answer = await _gen_openai_compat(question, passages, system, hist)
    except Exception as exc:  # noqa: BLE001
        # LLM configuré mais en échec (ex. 503) → on LÈVE : pas de faux contenu, pas de sources inutiles
        logger.error("Génération (%s) a échoué: %s", LLM_PROVIDER, exc)
        raise LLMUnavailable(str(exc)) from exc
    return answer + DISCLAIMER
