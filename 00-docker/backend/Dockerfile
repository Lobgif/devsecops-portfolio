ARG PYTHON_VERSION=3.12-slim
ARG PYTHON_SHA=sha256:a6e34c598f2467ed0e9a8d349809fcd8b5c603269512df273a0bb1784edc11b1

FROM python:${PYTHON_VERSION}@${PYTHON_SHA}

COPY --from=ghcr.io/astral-sh/uv@sha256:2381d6aa60c326b71fd40023f921a0a3b8f91b14d5db6b90402e65a635053709 /uv /uvx /bin/

LABEL version=1.0.0
LABEL author="Ibrahima FOFANA"
LABEL description="Backend API de la plateforme d'échange en Côte d'Ivoire"

# Setup a non-root user
RUN groupadd --system --gid 999 nonroot \
  && useradd --system --gid 999 --uid 1000 --create-home nonroot

WORKDIR /app

ENV PYTHONUNBUFFERED=1

ENV UV_COMPILE_BYTECODE=1

ENV UV_LINK_MODE=copy

ENV UV_NO_DEV=1

ENV UV_TOOL_BIN_DIR=/usr/local/bin

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=backend/uv.lock,target=uv.lock \
    --mount=type=bind,source=backend/pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project

COPY backend/ .

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked

ENV PATH="/app/backend/.venv/bin:$PATH"

ENTRYPOINT []

USER nonroot

EXPOSE 8080

CMD ["/app/backend/.venv/bin/fastapi", "run", "/app/backend/main.py", "--port", "8080", "--host", "0.0.0.0"]
