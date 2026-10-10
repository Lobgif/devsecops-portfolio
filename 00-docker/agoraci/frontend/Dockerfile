# syntax=docker/dockerfile:1
# Production Nuxt 3 (SSR) : build multi-stage puis exécution du serveur Node léger.
# (Le local utilise Dockerfile.dev avec hot-reload ; celui-ci sert au déploiement.)
# Build sur Debian slim (glibc) + npm@12 : évite le bug npm "edgesOut" (npm 10.x)
# et récupère les binaires natifs ARM (oxc-parser) que le package-lock.json généré
# sous Windows ne contient pas. npm install (et non ci) re-résout pour la plateforme.
FROM node:22-slim AS build
WORKDIR /app
COPY package.json ./
RUN npm install -g npm@12 && npm install --no-audit --no-fund --loglevel=error
COPY . .
# Le chemin admin secret est appliqué au BUILD (hook pages:extend de Nuxt) :
# il doit donc être présent comme variable AU MOMENT du build, pas seulement au runtime.
ARG NUXT_PUBLIC_ADMIN_PATH=admin
ENV NUXT_PUBLIC_ADMIN_PATH=$NUXT_PUBLIC_ADMIN_PATH
RUN npm run build

FROM node:22-alpine AS runtime
WORKDIR /app
ENV NODE_ENV=production \
    NITRO_PORT=3000 \
    NITRO_HOST=0.0.0.0
COPY --from=build /app/.output ./.output
# Execution en non-root : l'utilisateur 'node' (uid 1000) existe dans l'image officielle.
# Le serveur Nitro lit .output (lecture seule) et n'ecrit rien localement.
USER node
EXPOSE 3000
HEALTHCHECK --interval=15s --timeout=5s --start-period=20s --retries=5 \
    CMD wget -qO- http://127.0.0.1:3000/healthz || exit 1
CMD ["node", ".output/server/index.mjs"]
