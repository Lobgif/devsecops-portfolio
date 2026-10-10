#!/usr/bin/env bash
# Crée les secrets Docker Swarm nécessaires au stack de production.
# À exécuter UNE FOIS sur un nœud manager.
set -euo pipefail

gen() { openssl rand -base64 32 | tr -d '\n'; }

printf '%s' "${POSTGRES_PASSWORD:-$(gen)}" | docker secret create postgres_password - 2>/dev/null || \
  echo "secret postgres_password déjà présent"

printf '%s' "${JWT_SECRET:-$(gen)}" | docker secret create jwt_secret - 2>/dev/null || \
  echo "secret jwt_secret déjà présent"

printf '%s' "${RABBITMQ_PASSWORD:-$(gen)}" | docker secret create rabbitmq_password - 2>/dev/null || \
  echo "secret rabbitmq_password déjà présent"

echo "OK — secrets créés. Vérifier : docker secret ls"
