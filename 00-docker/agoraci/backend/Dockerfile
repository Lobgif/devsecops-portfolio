# syntax=docker/dockerfile:1
# Image backend Jamakan — multi-stage avec uv (dépendances figées par uv.lock).

# ---- Stage 1 : builder — uv installe les dépendances dans /app/.venv ----
FROM python:3.12-slim AS builder
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0
WORKDIR /app
RUN pip install --no-cache-dir uv \
    && apt-get update && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*
# Installe EXACTEMENT les versions de uv.lock (reproductible), sans le projet lui-même
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

# ---- Stage 2 : runtime léger (OCR + poppler), venv copié depuis le builder ----
FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH"
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl tesseract-ocr tesseract-ocr-fra poppler-utils \
    && rm -rf /var/lib/apt/lists/*
# Utilisateur non-root : le conteneur n'exécute pas l'app en root (durcissement).
RUN useradd --create-home --uid 10001 appuser
COPY --from=builder /app/.venv /app/.venv

COPY agoraci ./agoraci
COPY alembic.ini ./
COPY migrations ./migrations

# L'app n'ecrit aucun fichier local (OCR temporaire va dans /tmp, world-writable).
# On donne /app a appuser et on bascule en non-root avant le CMD.
RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=25s --retries=3 \
    CMD curl -fsS http://localhost:8000/health || exit 1

CMD ["sh", "-c", "alembic upgrade head && uvicorn agoraci.main:app --host 0.0.0.0 --port 8000"]
