# syntax=docker/dockerfile:1

ARG PYTHON_VERSION=3.12-slim
ARG PYTHON_SHA=sha256:a6e34c598f2467ed0e9a8d349809fcd8b5c603269512df273a0bb1784edc11b1

FROM python:${PYTHON_VERSION}@${PYTHON_SHA} AS builder

COPY --from=ghcr.io/astral-sh/uv@sha256:2381d6aa60c326b71fd40023f921a0a3b8f91b14d5db6b90402e65a635053709 /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_NO_DEV=1 \
    UV_TOOL_BIN_DIR=/usr/local/bin


WORKDIR /app

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=backend/uv.lock,target=uv.lock \
    --mount=type=bind,source=backend/pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project


FROM python:${PYTHON_VERSION}@${PYTHON_SHA}

LABEL org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.authors="Ibrahima FOFANA" \
      org.opencontainers.image.description="Backend API de la plateforme d'échange en Côte d'Ivoire" \
      org.opencontainers.image.source="https://gitlab.com/personnel4344847/agoraci"

ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*
RUN groupadd --system --gid 999 nonroot \
  && useradd --system --gid 999 --uid 999 --create-home nonroot

COPY --from=builder --chown=nonroot:nonroot /app/.venv /app/.venv

COPY --chown=nonroot:nonroot backend/ .

ENV PATH="/app/.venv/bin:$PATH"

ENTRYPOINT []

USER nonroot

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -fsS http://localhost:8000/health || exit 1

CMD ["sh", "-c", "uvicorn agoraci.main:app --host 0.0.0.0 --port 8000"]
