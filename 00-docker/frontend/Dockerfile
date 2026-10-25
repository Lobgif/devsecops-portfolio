# syntax=docker/dockerfile:1

ARG NODE_VERSION=22.23.3
ARG NODE_SHA=sha256:0a7108bf6c7bf5de370ffb1a3ed6be93d405b43ff159f681a8d18c0e2bc2e402

FROM node:${NODE_VERSION}-slim AS deps
WORKDIR /app

RUN --mount=type=cache,target=/root/.npm \
    --mount=type=bind,source=frontend/package.json,target=package.json \
    npm install -g npm@12 \
 && npm install --no-audit --no-fund --ignore-scripts --no-save --loglevel=error

FROM node:${NODE_VERSION}-slim AS build
WORKDIR /app
ARG NUXT_PUBLIC_ADMIN_PATH=admin
ENV NUXT_PUBLIC_ADMIN_PATH=$NUXT_PUBLIC_ADMIN_PATH
COPY --from=deps /app/node_modules ./node_modules
COPY frontend/ ./
RUN npm run build

FROM node:${NODE_VERSION}-alpine@${NODE_SHA} AS runtime
WORKDIR /app
ENV NODE_ENV=production \
    NITRO_PORT=3000 \
    NITRO_HOST=0.0.0.0
COPY --from=build --chown=node:node /app/.output ./.output
USER node
EXPOSE 3000
HEALTHCHECK --interval=15s --timeout=5s --start-period=20s --retries=5 \
    CMD wget -qO- http://127.0.0.1:3000/healthz || exit 1
CMD ["node", ".output/server/index.mjs"]
