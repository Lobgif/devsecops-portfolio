# Jamakan

---

# Plateforme Citoyenne Collaborative - Côte d'Ivoire

## Description

Cette plateforme web vise à offrir un espace communautaire d'entraide et d'information pour les citoyens ivoiriens.  
Elle permet aux utilisateurs de poser des questions, partager leurs expériences et accéder à des réponses juridiques, sociales, éducatives et politiques, en particulier sur des sujets sensibles comme le mariage, le divorce, l'héritage, la violence, la corruption, etc.

La plateforme intègre :  
- Un système de forums thématiques (mariage, droits, éducation, politique...)  
- Un chat en temps réel (WebSocket) pour échanges instantanés  
- Une intelligence artificielle qui propose des réponses basées sur la loi ivoirienne et des cas précédents validés  
- Un système de vote pour évaluer la qualité des réponses (humaines ou IA)  
- Un moteur de modération automatique pour éviter les propos haineux ou injurieux  
- La possibilité de créer et rejoindre des groupes thématiques, sans censure par les propriétaires  
- Un support multilingue incluant les langues locales  
- Un espace d’échanges pour étudiants et passionnés (matières scolaires, sports, loisirs...)

---

## Fonctionnalités principales

| Fonctionnalité                            | Description                                                                                     |
|-----------------------------------------|-------------------------------------------------------------------------------------------------|
| **Forums thématiques**                   | Sujets organisés par catégories (mariage, héritage, politique...) avec discussions modérées    |
| **Chat en temps réel**                   | Conversations instantanées dans chaque groupe/forum via WebSocket                               |
| **IA juridique intégrée**                | Réponses automatiques validées, avec références légales et exemples ivoiriens                   |
| **Système de vote**                      | Chaque réponse (IA ou utilisateur) peut être votée pour garantir la fiabilité et la pertinence |
| **Modération automatique**               | Analyse sémantique pour filtrer les propos haineux, injurieux ou incitant à la violence        |
| **Groupes sans contrôle total**         | Création de groupes ouverts où aucun modérateur ne peut censurer les opinions à sa guise       |
| **Multi-langues, incluant langues locales** | Interface et échanges disponibles en français, anglais, et langues ivoiriennes                  |
| **Espaces d’échange pour étudiants**    | Groupes dédiés aux matières scolaires, sports, culture, jeux, etc.                             |

---

## Technologies utilisées

### Backend

- **FastAPI** : Framework Python asynchrone pour construire des APIs performantes
- **Starlette** : Framework ASGI utilisé pour la gestion des WebSocket et middleware
- **Pydantic** : Validation des données, modèles métier clairs et typés
- **SQLAlchemy + Alembic** : ORM et migrations de schéma versionnées
- **PostgreSQL** : Base de données relationnelle robuste et open-source (données métier)
- **pgvector** (extension PostgreSQL) : stockage et recherche vectorielle pour le RAG juridique
- **`tsvector`** (PostgreSQL natif) : recherche plein-texte / mots-clés (recherche hybride avec pgvector)
- **Redis** : Cache, sessions, pub/sub WebSocket et back-end de file d’attente
- **Celery ou ARQ** : files de tâches asynchrones (appels IA, modération, emails, notifications)
- **slowapi** : rate limiting / anti-abus au niveau de l’API

### Authentification & sécurité

- **JWT (access + refresh tokens)** : authentification stateless
- **OAuth2** : connexion via Google (et autres fournisseurs à terme)
- **Hachage des mots de passe** : `argon2` / `bcrypt`

### Intelligence Artificielle (RAG)

- **Approche RAG** (Retrieval-Augmented Generation) : pas d’entraînement/fine-tuning du modèle ;
  le système **récupère** les textes de loi pertinents puis génère une réponse **avec citations vérifiables**
- **Base vectorielle** : PostgreSQL + pgvector (Qdrant en option d’évolution si fort volume)
- **Modèle d’embeddings multilingue** : ex. `multilingual-e5` ou équivalent (français + langues locales)
- **LLM de génération** : API (Claude / GPT) pour démarrer, ou modèle open-source auto-hébergé
  (Mistral / Llama via Ollama ou vLLM) pour la souveraineté des données
- **Recherche hybride** : combinaison dense (vecteurs) + sparse (mots-clés) pour la précision juridique

### Frontend

- **Nuxt 3** (Vue 3 + SSR/SSG) : rendu serveur pour le **SEO** et la performance
- **Pinia** (`@pinia/nuxt`) : gestion d’état
- **Tailwind CSS** : design system sur-mesure (palette ivoirienne)
- **PrimeVue** (`@primevue/nuxt-module`) : composants riches, thème Aura
- **SEO** : `@nuxtjs/sitemap` (sitemap.xml), `@nuxtjs/robots` (robots.txt),
  route serveur **`/feed.xml`** (RSS), `useSeoMeta`/`useHead` (OpenGraph, Twitter Cards, JSON-LD)
- **i18n** (`@nuxtjs/i18n`) : multilingue fr/en + `hreflang`, extensible aux langues locales

### Notifications

- **Brevo** (ex-Sendinblue) en **mode API HTTP v3** (clé API, header `api-key`) :
  emails transactionnels, templates, statistiques — entièrement piloté par variables d’env
- **Web push** (VAPID) : canal complémentaire optionnel

### Infrastructure & DevOps

- **Docker / Docker Compose** : développement local reproductible
- **Docker Swarm** : orchestration de production (réplication, rolling updates, secrets)
- **Traefik** : reverse proxy, routage dynamique et HTTPS automatique (Let’s Encrypt)
- **GitLab CI/CD** : SAST, détection de secrets, scan de dépendances et **Trivy** (images)
- **MinIO / S3** : stockage objet pour les documents sources (textes de loi, pièces jointes)
- **Sentry** + **Prometheus / Grafana** (ou Uptime Kuma) : observabilité

### Choix d’API (verrouillé)

**REST/HTTP** pour la communication client↔backend, complété par l’**événementiel RabbitMQ**
(asynchrone, interne). C’est le meilleur compromis long terme : cacheable, SEO-friendly,
simple à maintenir. Le backend est un **monolithe modulaire** (une image), mais le code est
découpé par domaine pour pouvoir extraire un module en service séparé plus tard si nécessaire.

### Configuration par variables d’environnement

Aucune valeur sensible ou spécifique à un environnement n’est codée en dur. Tout passe par des
variables d’environnement (`.env` en local, variables de la plateforme en prod — ex. **Render**) :
secrets DB/JWT/RabbitMQ (via secrets Docker en Swarm), clés Brevo, fournisseurs IA, et variables
publiques du frontend (`NUXT_PUBLIC_*`). Voir [`.env.example`](.env.example).

### Déploiement

Guide complet (VPS Docker+Traefik **ou** Render avec services managés, variables par service,
images à publier, R2/CloudAMQP, checklist) : **[`DEPLOYMENT.md`](DEPLOYMENT.md)**.

---

## Architecture du projet

Jamakan est un **monolithe modulaire** : **une seule image backend** (toutes les API dans
une app FastAPI, code organisé par domaine) + **une image frontend** Nuxt. Les seules autres
images sont des briques d'infrastructure standard (PostgreSQL, Redis, RabbitMQ, MinIO, Traefik).
Cela garde le code propre et découplé **sans** la lourdeur opérationnelle des microservices.

```
agoraci/
├── Makefile                    # Raccourcis (up, deploy, secrets, migrate...)
├── .env.example                # Toutes les variables d'environnement
├── scripts/                    # build-push.sh, create-secrets.sh
│
├── backend/                    # ───────── Une seule app FastAPI ─────────
│   ├── Dockerfile              # Image backend (multi-stage, uv)
│   ├── pyproject.toml  uv.lock  # Dépendances figées (uv)
│   ├── alembic.ini  migrations/    # Migrations (tous les schémas)
│   └── agoraci/                # Package applicatif
│       ├── main.py             # App unique : monte tous les routers + consumers
│       ├── common/             # config, db, messaging, sécurité, auth_deps, ratelimit
│       ├── auth/               # Inscription + vérif. email, OAuth Google, profil — `auth`
│       ├── forum/              # Groupes/rôles, badges, votes+points, modération vote — `forum`
│       ├── rag/                # IA juridique (LLM + embeddings réels, hybride) — `rag`
│       ├── moderation/         # Modération NLP multilingue (fr/nouchi) — `moderation`
│       ├── notification/       # Emails via Brevo (consumer d'événements)
│       └── chat/               # WebSocket temps réel (Redis pub/sub) — `chat`
│
├── frontend/                   # ───────── Nuxt 3 (SSR + SEO) ─────────
│   ├── nuxt.config.ts          # SSR, modules SEO/i18n, runtimeConfig (env)
│   ├── pages/  layouts/  composables/  stores/
│   ├── server/routes/feed.xml.ts   # Flux RSS
│   └── assets/css/  i18n.config.ts
│
└── infra/                      # ───────── Infrastructure ─────────
    ├── docker-compose.yml      # Orchestration LOCALE (dev)
    ├── docker-stack.yml        # Orchestration PRODUCTION (Docker Swarm)
    ├── DEPLOYMENT.md           # Guide de déploiement (local, Swarm, Render)
    ├── postgres/init.sql       # Schémas + extensions (pgvector, pg_trgm)
    └── traefik/                # Config reverse proxy (local & prod)
```

> Les fichiers d'orchestration sont dans `infra/` ; les `Dockerfile` restent près du code
> (`backend/`, `frontend/`). Les commandes `make` s'exécutent depuis la racine.

### Communication interne

| Type | Techno | Exemple |
|---|---|---|
| HTTP (client → backend) | REST via Traefik | le frontend appelle `/api/rag/ask` |
| Asynchrone | RabbitMQ (exchange topic `agoraci.events`) | `discussion.created` → modération |
| Temps réel | WebSocket + Redis pub/sub | chat multi-instances |

> Le code reste **modulaire par domaine** : si un module (ex. `rag`) doit un jour scaler
> séparément, il peut être extrait en service indépendant sans réécriture.

### Routage Traefik (préfixes)

`/api/*` et `/ws` → **backend** · `/` → **frontend**
(les préfixes `/api/auth`, `/api/forum`, `/api/rag`, `/api/moderation` sont des routers
internes de l'app backend unique.)

---

## Architecture IA / RAG (réponses juridiques)

L’IA juridique ne « connaît » pas la loi par cœur : elle **recherche** les textes pertinents
à chaque question, puis génère une réponse **sourcée et vérifiable**. Cette approche (RAG)
évite l’entraînement coûteux, se met à jour en ajoutant un document, et limite les hallucinations.

### Pipeline d’ingestion (hors-ligne)

1. **Source brute** : textes officiels (Code civil, Code de la famille, lois, décrets,
   jurisprudence…) conservés tels quels dans un stockage objet (MinIO/S3) pour la traçabilité.
2. **Structuration** : parsing en hiérarchie (Code > Livre > Titre > Chapitre > Article),
   stockée en PostgreSQL (`JSONB` pour les métadonnées).
3. **Découpage** : chunking **par article** (le droit se découpe naturellement par article,
   pas par nombre de tokens fixe).
4. **Vectorisation** : génération des embeddings (modèle multilingue) → stockés en `pgvector`.

### Pipeline de réponse (temps réel)

1. La question est vectorisée puis comparée au corpus (**recherche hybride** :
   `pgvector` pour le sens + `tsvector` pour les termes/numéros exacts).
2. Les passages les plus pertinents sont récupérés (avec leurs métadonnées).
3. Le LLM génère une réponse **en citant les articles** (n° d’article, code source, lien).
4. La réponse est accompagnée d’un **disclaimer juridique** systématique.

### Stockage : format et base de données

| Niveau | Contenu | Stockage / format |
|---|---|---|
| **Source brute** | PDF / texte original | Stockage objet (MinIO/S3) |
| **Document structuré** | Texte parsé + hiérarchie | PostgreSQL + colonne `JSONB` |
| **Chunks** | Découpage par article + vecteur + index plein-texte | Table `chunks` (`vector` + `tsvector`) |

Métadonnées clés par chunk : `code_source`, `numero_article`, `titre_hierarchie`,
`date_vigueur`, `est_abroge`, `url_source`. Elles rendent les **citations vérifiables**.

> **Choix de base de données** : PostgreSQL + pgvector est adapté à l’échelle d’un corpus
> juridique national (dizaines de milliers à quelques millions de chunks) et permet une
> recherche **hybride** dans une seule base. Une base vectorielle dédiée (**Qdrant**)
> ne devient pertinente qu’en cas de très fort volume ou de QPS élevé.

---

## Sécurité, modération et conformité

- **Authentification** : JWT (access + refresh), OAuth2 Google, mots de passe hachés (argon2/bcrypt).
- **Rate limiting / anti-spam / anti-bot** : protection des endpoints sensibles (slowapi + Redis).
- **Modération en deux niveaux** :
  1. **Automatique** (NLP) : filtrage des propos haineux, injurieux ou incitant à la violence.
  2. **Humaine** : workflow de signalement → revue par des modérateurs (indispensable car la
     modération auto échoue souvent sur le **nouchi** et les langues locales).
- **Disclaimer juridique** : mention systématique « Ceci n’est pas un conseil juridique officiel »
  sur toute réponse IA — protège les utilisateurs et la plateforme.
- **Protection des données (RGPD / données sensibles)** : sujets sensibles (divorce, violence…) →
  chiffrement, minimisation des données, anonymisation possible, droit à l’effacement.
- **Observabilité** : logs structurés, suivi des erreurs (Sentry), métriques (Prometheus/Grafana).

---

## Fonctionnalités complémentaires (intégrées au périmètre)

| Fonctionnalité | Pourquoi c'est important |
|---|---|
| **Auth robuste** (JWT + refresh, OAuth Google) | Indispensable et sécurisée par défaut. |
| **Rate limiting / anti-spam / anti-bot** | Une plateforme ouverte est une cible de spam et de flood. |
| **Recherche plein-texte** | Couvre la « recherche globale » via `tsvector` natif PostgreSQL. |
| **File d'attente asynchrone** (Celery/ARQ + Redis) | Décharge l'API des tâches lourdes : IA, modération, emails, notifications. |
| **Disclaimer juridique** | Protège juridiquement les utilisateurs et la plateforme. |
| **Modération humaine en complément** | La modération auto seule échoue sur le nouchi/langues locales. |
| **Notifications temps réel + email + web push** | Réactivité des interactions (réponses, votes, messages). |
| **RGPD / protection des données** | Données sensibles : chiffrement et anonymisation. |
| **Observabilité** (logs structurés, Sentry, traces) | Débogage et fiabilité en production. |
| **Tests + CI** | Tests unitaires/intégration (pytest, Vitest) en plus du SAST/Secret Detection. |

---

## Communauté & gouvernance

| Fonctionnalité | Détail |
|---|---|
| **Vérification d'email par code** | À l'inscription, un code à 6 chiffres (Redis, TTL configurable) est envoyé par Brevo. Connexion bloquée tant que l'email n'est pas vérifié. Renvoi de code possible. |
| **Profils utilisateurs** | Nom, bio, avatar, langue — éditables via `/api/auth/me`. |
| **Rôles de groupe** | `creator` → `admin` → `member`. Le créateur (ou un admin) peut **promouvoir des admins** (`/api/forum/groups/{id}/admins`). |
| **Super-admin plateforme** | Rôle `is_superadmin` (claim JWT). Interface `/admin` : lister les groupes, **mettre en vedette**. Endpoints `/api/forum/admin/*`. |
| **Badges de groupe** | `vedette` (super-admin), `nouveau` (< 7 j), `réactif` (activité < 2 j), `populaire` (≥ 100 membres) — calculés dynamiquement. |
| **Modération par vote** | Chaque membre propose une décision (`delete/hide/pin/ban`) soumise au **vote communautaire** ; au seuil atteint → événement `moderation.decision`. |
| **Points / réputation** | Chaque réponse gagne des points selon les **j'aime** reçus ; réputation par utilisateur (`/api/forum/reputation/{user_id}`). |
| **OAuth Google** | `/api/auth/google/login` → callback → redirection frontend avec tokens (utilisateur auto-vérifié). |
| **Rate limiting** | `slowapi` (stockage Redis) : limites par défaut + spécifiques (login, register, ask, modération). |

### Événements RabbitMQ (exchange `agoraci.events`)

`user.registration_code` · `user.registered` · `discussion.created` · `post.created`
· `content.flagged` · `moderation.decision`

### Migrations (production)

Les tables sont auto-créées **en dev uniquement**. En production, utiliser Alembic
(scaffolding fourni dans `auth/forum/rag`) :

```bash
# générer une migration après modif des modèles (service en cours d'exécution)
make up
docker compose --project-directory . -f infra/docker-compose.yml exec auth-service \
  alembic revision --autogenerate -m "init"
# appliquer
make migrate
```

---

## Installation & démarrage

### Prérequis

* Docker & Docker Compose v2
* (Optionnel pour dev hors conteneur) Python 3.12+ et Node.js 20+

### Développement local (Docker Compose)

```bash
git clone <url-du-depot> agoraci
cd agoraci
cp .env.example .env          # adapter les secrets
make up                       # ou : docker compose --project-directory . -f infra/docker-compose.yml up --build -d
```

Accès :

| Service | URL |
|---|---|
| Application (frontend) | http://localhost |
| Dashboard Traefik | http://localhost:8080 |
| API (via Traefik) | http://localhost/api/auth, `/api/forum`, `/api/rag`, ... |
| RabbitMQ (console) | http://localhost:15672 |
| MinIO (console) | http://localhost:9001 |

> Swagger de chaque service : exposé à `/docs` **dans le conteneur** (healthchecks internes).
> Pour l'exposer derrière Traefik, configurer `root_path` du service (FastAPI) selon son préfixe.

Logs : `make logs` · Arrêt : `make down`

### Production (Docker Swarm)

```bash
make swarm-init                                   # initialise Swarm (1ère fois)
make secrets                                      # crée les secrets Docker
export REGISTRY=registry.exemple.ci/agoraci TAG=1.0.0
make push                                         # build + push des images
DOMAIN=agoraci.ci ACME_EMAIL=contact@agoraci.ci make deploy
```

Swarm gère la **réplication**, le **rolling update** (`start-first`) et le **redémarrage auto**
des services ; Traefik fournit le **HTTPS automatique** (Let's Encrypt).
État : `docker stack services agoraci`

> En production, exécuter les **migrations Alembic** de chaque service plutôt que la
> création automatique des tables (active en dev uniquement).

---

## Contribution

Les contributions sont les bienvenues !

* Merci de créer une issue avant de proposer une pull request
* Respecter la charte de modération et d’inclusion
* Ajouter des tests unitaires pour toute nouvelle fonctionnalité

---

## Équipe

* Fofana Ibrahima - Ingénieur Géomaticien & Devops
* \[Autres contributeurs...]

---

## Licence

Ce projet est sous licence MIT.

---

## Contact

Pour toute question, propose d'amélioration ou collaboration :
Email : [lahigic@gmail.com](mailto:lahigic@gmail.com)
GitHub : [https://github.com/mon-compte](https://github.com/ensg_fofana)

---

## Architecture du site et navigation

### 1. Page d’accueil  
- Présentation claire de la mission et des objectifs de la plateforme.  
- Accès rapide aux forums thématiques populaires (mariage, héritage, santé, politique, etc.).  
- Boutons visibles « Connexion » et « Inscription ».  
- Moteur de recherche rapide pour chercher une question ou un sujet spécifique.

### 2. Page Connexion / Inscription  
- Formulaire de connexion sécurisé (email + mot de passe).  
- Formulaire d’inscription simple avec choix de la langue préférée.  
- Fonction de récupération ou réinitialisation du mot de passe.

### 3. Tableau de bord (après connexion)  
- Fil d’actualité affichant les discussions récentes ou tendances.  
- Accès rapide aux groupes/forums dont l’utilisateur est membre.  
- Notifications en temps réel pour réponses, votes ou messages privés.  
- Bouton « Poser une question » facilement accessible.

### 4. Page Forums / Groupes thématiques  
- Liste complète et classée des forums/groupes par thématiques (juridique, social, politique, culture, etc.).  
- Option pour rejoindre un groupe existant ou en créer un nouveau, avec règles claires sur la modération et la liberté d’expression.  
- Statistiques visibles : nombre de discussions, membres, activité récente.

### 5. Page Discussion (question + réponses)  
- Affichage clair de la question posée, avec métadonnées (auteur, date).  
- Liste des réponses classées par popularité ou chronologie, avec distinction entre réponses apportées par l’IA et par les membres.  
- Boutons pour voter positivement ou négativement chaque réponse.  
- Fonction de signalement des contenus inappropriés.  
- Zone de saisie pour écrire une nouvelle réponse.  
- Alerte/modération automatique en cas d’usage de langage inapproprié, incitant à reformuler.

### 6. Page Création / Gestion de groupes  
- Formulaire simple pour créer un groupe (nom, description, catégorie).  
- Liste des groupes créés ou suivis par l’utilisateur.  
- Fonction pour quitter un groupe.  
- Rappel que le créateur n’a pas de contrôle exclusif sur le contenu, garantissant une modération communautaire.

### 7. Page Profil / Paramètres utilisateur  
- Informations personnelles et possibilité de mise à jour (nom, email, langue).  
- Gestion des notifications (email, push).  
- Paramètres personnalisés de modération (filtrage de contenu, blocage d’utilisateurs).  
- Historique des questions posées et réponses fournies.

---

## Fonctionnalités clés transversales  
- **Interface multilingue** : français et langues locales ivoiriennes avec possibilité de changement rapide.  
- **Intelligence artificielle intégrée** : réponse automatique aux questions avec exemples concrets, références légales ivoiriennes et contextualisation.  
- **Système de vote communautaire** : valorisation des meilleures réponses par la communauté.  
- **Modération automatique** : détection des propos haineux, grossièretés, ou discours incitant à la haine, avec avertissements.  
- **Liberté d’expression garantie** : possibilité de créer des groupes sans contrôle exclusif, pour éviter la censure.  
- **Notifications en temps réel** pour interactions (réponses, votes, messages).  
- **Recherche globale** sur toutes les questions, réponses et groupes.

---

## Bonus / évolutions futures possibles  
- Messagerie privée entre membres.  
- Page FAQ / documentation juridique simplifiée.  
- Ressources éducatives intégrées (guides, articles).  
- Interface mobile optimisée.

---

## Conclusion  
Cette architecture garantit une plateforme riche, sécurisée et facile à utiliser, capable d’apporter un impact social fort en Côte d’Ivoire. Elle repose sur une navigation fluide entre les pages essentielles, avec une séparation claire des fonctions pour une meilleure expérience utilisateur.

---

*Ce README servira de base pour le développement frontend et backend, ainsi que pour la conception UI/UX.*
