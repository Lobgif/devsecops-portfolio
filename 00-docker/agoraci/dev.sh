#!/usr/bin/env bash
# Wrapper pratique (équivalent du Makefile) pour ceux qui n'ont pas `make`.
# Usage : ./dev.sh up | down | logs | ps | rebuild | migrate | migration "msg"
set -euo pipefail
cd "$(dirname "$0")"

COMPOSE=(docker compose --project-directory . -f infra/docker-compose.yml)

cmd="${1:-help}"
case "$cmd" in
  up)        "${COMPOSE[@]}" up --build -d ;;
  down)      "${COMPOSE[@]}" down ;;
  logs)      "${COMPOSE[@]}" logs -f ;;
  ps)        "${COMPOSE[@]}" ps ;;
  rebuild)   "${COMPOSE[@]}" build --no-cache ;;
  restart)   "${COMPOSE[@]}" restart "${2:-}" ;;
  seed)        "${COMPOSE[@]}" exec backend python -m agoraci.seed ;;
  seed-corpus) "${COMPOSE[@]}" exec backend python -m agoraci.rag.ingest ;;
  index-community) "${COMPOSE[@]}" exec backend python -m agoraci.rag.community "${2:-2}" ;;
  migrate)   "${COMPOSE[@]}" exec backend alembic upgrade head ;;
  migration) "${COMPOSE[@]}" exec backend alembic revision --autogenerate -m "${2:?message requis}" ;;
  *) echo "Usage: ./dev.sh {up|down|logs|ps|rebuild|restart|migrate|migration \"msg\"}" ;;
esac
