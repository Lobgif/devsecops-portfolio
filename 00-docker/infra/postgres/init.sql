-- ============================================================
-- Jamakan - Initialisation PostgreSQL
-- Base unique partagée : un schéma isolé par microservice.
-- Exécuté automatiquement au premier démarrage du conteneur.
-- ============================================================

-- Extensions
CREATE EXTENSION IF NOT EXISTS vector;        -- pgvector (RAG)
CREATE EXTENSION IF NOT EXISTS pg_trgm;       -- recherche fuzzy / trigram
CREATE EXTENSION IF NOT EXISTS unaccent;      -- recherche insensible aux accents
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";   -- UUID

-- Un schéma par service (isolation logique des tables)
CREATE SCHEMA IF NOT EXISTS auth;
CREATE SCHEMA IF NOT EXISTS forum;
CREATE SCHEMA IF NOT EXISTS chat;
CREATE SCHEMA IF NOT EXISTS rag;
CREATE SCHEMA IF NOT EXISTS moderation;
CREATE SCHEMA IF NOT EXISTS notification;

-- Note : les tables sont créées par les migrations Alembic de chaque service.
-- pgvector étant à l'échelle de la base, l'extension est disponible pour le schéma `rag`.
