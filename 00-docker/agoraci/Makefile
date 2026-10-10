.PHONY: help up down logs build rebuild ps swarm-init deploy secrets push test migrate

# Les fichiers d'orchestration sont dans infra/ ; on exécute depuis la racine
# pour que les chemins relatifs (./backend, ./frontend, ./infra) restent valides.
COMPOSE = docker compose --project-directory . -f infra/docker-compose.yml
STACK_FILE = infra/docker-stack.yml

help:                ## Affiche cette aide
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

# ----- Local (docker compose) -----
up:                  ## Démarre la stack locale
	$(COMPOSE) up --build -d

down:                ## Arrête la stack locale
	$(COMPOSE) down

logs:                ## Suit les logs
	$(COMPOSE) logs -f

ps:                  ## État des conteneurs
	$(COMPOSE) ps

rebuild:             ## Reconstruit sans cache
	$(COMPOSE) build --no-cache

seed:                ## Peuple la base de données (données de démo)
	$(COMPOSE) exec backend python -m agoraci.seed

seed-corpus:         ## Ingestion du corpus juridique de démonstration (RAG)
	$(COMPOSE) exec backend python -m agoraci.rag.ingest

migrate:             ## Applique les migrations Alembic (backend)
	$(COMPOSE) exec backend alembic upgrade head

migration:           ## Génère une migration auto (usage: make migration m="message")
	$(COMPOSE) exec backend alembic revision --autogenerate -m "$(m)"

# ----- Production (Docker Swarm) -----
swarm-init:          ## Initialise le mode Swarm sur ce nœud
	docker swarm init

secrets:             ## Crée les secrets de prod
	bash scripts/create-secrets.sh

push:                ## Build + push des images (REGISTRY, TAG requis)
	bash scripts/build-push.sh

deploy:              ## Déploie le stack en production
	docker stack deploy -c $(STACK_FILE) agoraci

# ----- Qualité -----
test:                ## Lance les tests (à compléter par service)
	@echo "TODO: pytest par service + vitest frontend"
