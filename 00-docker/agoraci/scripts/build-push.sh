#!/usr/bin/env bash
# Construit et pousse les 2 images applicatives (backend + frontend) vers le registre.
# Usage : REGISTRY=registry.exemple.ci/agoraci TAG=1.0.0 ./scripts/build-push.sh
set -euo pipefail

REGISTRY="${REGISTRY:?Définir REGISTRY}"
TAG="${TAG:-latest}"

echo ">> Build backend"
docker build -f backend/Dockerfile -t "${REGISTRY}/backend:${TAG}" backend
docker push "${REGISTRY}/backend:${TAG}"

echo ">> Build frontend"
docker build -f frontend/Dockerfile -t "${REGISTRY}/frontend:${TAG}" frontend
docker push "${REGISTRY}/frontend:${TAG}"

echo "OK — images backend & frontend poussées avec le tag ${TAG}"
