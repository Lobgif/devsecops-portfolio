# Fournisseurs IA — où créer les comptes & clés (offres gratuites)

Jamakan lit tout depuis `.env`. Choisis **1 fournisseur LLM** + **1 fournisseur d'embeddings**,
crée les clés ci-dessous, colle-les dans `.env`, puis **réinitialise** (la dimension des
embeddings est gravée dans la base — voir tout en bas).

## ✅ Combo recommandé « zéro euro » (FR / multilingue)

| Rôle | Fournisseur | Modèle | Dim |
|---|---|---|---|
| **LLM** | Google Gemini | `gemini-2.0-flash` | — |
| **Embeddings** | Cohere | `embed-multilingual-v3.0` | 1024 |

```env
LLM_PROVIDER=gemini
LLM_API_KEY=<clé Google AI Studio>
LLM_MODEL=gemini-2.0-flash

EMBEDDING_PROVIDER=cohere
EMBEDDING_API_KEY=<clé d'essai Cohere>
EMBEDDING_MODEL=embed-multilingual-v3.0
EMBEDDING_DIM=1024
```

---

## Où créer chaque clé

### Google Gemini (LLM) — gratuit, généreux
1. Va sur **https://aistudio.google.com/** → connecte-toi avec un compte Google.
2. **« Get API key »** → *Create API key* → copie la clé.
3. `.env` : `LLM_PROVIDER=gemini`, `LLM_API_KEY=...`, `LLM_MODEL=gemini-2.0-flash`.
   Limites free : ~15 req/min, ~1500 req/jour. (Données possiblement utilisées pour l'entraînement en gratuit.)

### Cohere (Embeddings) — clé d'essai gratuite, excellent multilingue
1. Va sur **https://dashboard.cohere.com/** → crée un compte.
2. **API Keys** → copie la **Trial key** (gratuite, ~40 req/min, usage non commercial).
3. `.env` : `EMBEDDING_PROVIDER=cohere`, `EMBEDDING_API_KEY=...`,
   `EMBEDDING_MODEL=embed-multilingual-v3.0`, `EMBEDDING_DIM=1024`.

### Mistral AI (LLM et/ou Embeddings) — « La Plateforme », free tier
1. **https://console.mistral.ai/** → compte → **API Keys** → créer une clé.
2. LLM : `LLM_PROVIDER=mistral`, `LLM_MODEL=mistral-small-latest`.
   Embeddings : `EMBEDDING_PROVIDER=mistral`, `EMBEDDING_MODEL=mistral-embed`, `EMBEDDING_DIM=1024`.

### OpenAI (LLM + Embeddings) — payant mais quasi gratuit à l'usage
1. **https://platform.openai.com/api-keys** → *Create new secret key*.
2. LLM : `LLM_PROVIDER=openai`, `LLM_MODEL=gpt-4o-mini`.
   Embeddings : `EMBEDDING_PROVIDER=openai`, `EMBEDDING_MODEL=text-embedding-3-small`, `EMBEDDING_DIM=1536`.

### Anthropic (LLM Claude) — ~5 $ de crédit au départ
1. **https://console.anthropic.com/** → *API Keys*.
2. `LLM_PROVIDER=anthropic`, `LLM_MODEL=claude-3-5-haiku-latest`, `LLM_API_KEY=...`.

### Groq (LLM ultra-rapide, free tier)
1. **https://console.groq.com/keys** → créer une clé.
2. `LLM_PROVIDER=groq`, `LLM_MODEL=llama-3.3-70b-versatile`.

### Ollama (100 % local, gratuit, privé — aucune clé)
1. Installe **https://ollama.com/** sur ta machine.
2. `ollama pull llama3` et `ollama pull nomic-embed-text`.
3. `.env` : `LLM_PROVIDER=ollama`, `LLM_MODEL=llama3`,
   `EMBEDDING_PROVIDER=ollama`, `EMBEDDING_MODEL=nomic-embed-text`, `EMBEDDING_DIM=768`,
   `OLLAMA_BASE_URL=http://host.docker.internal:11434` (depuis les conteneurs).

---

## ⚠️ Important : changer d'embeddings = réinitialiser

La **dimension** du vecteur (`EMBEDDING_DIM`) est gravée dans la colonne pgvector lors de
la migration. Pour appliquer un nouveau modèle d'embeddings :

```bash
# 1) Mets à jour .env (EMBEDDING_PROVIDER, EMBEDDING_MODEL, EMBEDDING_DIM, clés)
# 2) Réinitialise la base (perd les données de démo) + relance
docker compose --project-directory . -f infra/docker-compose.yml down -v
./dev.sh up
# 3) Re-seed + ré-ingestion du corpus
./dev.sh seed
./dev.sh seed-corpus
```

> Le **LLM** (génération) peut être changé à tout moment sans réinitialiser (seuls les
> embeddings touchent le schéma). Tant qu'aucune clé n'est configurée, l'app tourne en
> **mode dégradé** (recherche par mots-clés + réponse générique).
