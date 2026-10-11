# syntax=docker/dockerfile:1

FROM cgr.dev/chainguard/python@sha256:f07413fa2abb281095b499d58ba7bf6e87d45411dda711e59f2c755efff1d91e AS builder

COPY --from=ghcr.io/astral-sh/uv@sha256:2381d6aa60c326b71fd40023f921a0a3b8f91b14d5db6b90402e65a635053709 /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_NO_DEV=1 \
    UV_TOOL_BIN_DIR=/usr/local/bin

USER root
RUN apk add --no-cache build-base libffi-dev libxml2-dev libxslt-dev

WORKDIR /app

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=backend/uv.lock,target=uv.lock \
    --mount=type=bind,source=backend/pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project


FROM cgr.dev/chainguard/python@sha256:197cf542e9f4dc373864faecd4fd1a4f642622e654e9196881ca852e8fdf26bd

LABEL org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.authors="Ibrahima FOFANA" \
      org.opencontainers.image.description="Backend API de la plateforme d'échange en Côte d'Ivoire" \
      org.opencontainers.image.source="https://gitlab.com/personnel4344847/agoraci"

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

COPY --from=builder --chown=65532:65532 /app/.venv /app/.venv

COPY --chown=65532:65532 backend/ .

ENTRYPOINT ["uvicorn", "agoraci.main:app", "--host", "0.0.0.0", "--port", "8000"]

EXPOSE 8000
