# Déploiement d'Jamakan

Ce guide couvre **deux options** : un **VPS** (le plus simple, tout en Docker Compose + Traefik) et **Render** (services managés). Toutes les valeurs sensibles passent par variables d'environnement — voir `.env.example`.

---

## 1. Architecture & images

| Composant | Image | Construit ? | Rôle |
|---|---|---|---|
| **backend** | `backend/Dockerfile` (multi-stage, uv) | ✅ à construire | API FastAPI (auth, forum, RAG « Nanan », modération, notifs, uploads, jobs) |
| **frontend** | `frontend/Dockerfile` (multi-stage, Nuxt SSR) | ✅ à construire | Site Nuxt 3 (SSR/SEO) |
| postgres | `pgvector/pgvector:pg16` (ou `postgres` + extension) | image publique | Base + recherche vectorielle |
| redis | `redis` | image publique | Cache, codes, temps réel |
| rabbitmq | `rabbitmq:3-management` | image publique | File des jobs/événements |
| minio | `minio/minio` | image publique | Stockage fichiers (local ; **R2/S3 en prod**) |
| traefik | `traefik:v3` | image publique | Reverse-proxy + TLS (**VPS uniquement**) |

👉 **Tu ne publies que 2 images** (backend, frontend). Le reste = images publiques / services managés.

---

## 2. Option A — VPS (Docker Compose + Traefik) ✅ recommandé pour démarrer

C'est exactement la stack locale, mais avec **HTTPS automatique** (Let's Encrypt) via le fichier
dédié **`infra/docker-compose.prod.yml`**. Une seule machine, pas de CORS, pas de R2 (MinIO suffit).

### Étape 0 — DNS (à faire en premier)
Chez ton registrar / Cloudflare, crée un enregistrement **A** :
`agoraci.ci → <IP_DU_VPS>` (et idéalement `www` aussi). Si Cloudflare : mets le nuage en **DNS only (gris)**
le temps d'émettre le certificat Let's Encrypt, tu pourras réactiver le proxy (orange) ensuite.

### Étape 1 — Préparer le serveur
```bash
# Sur le VPS (Ubuntu/Debian)
curl -fsSL https://get.docker.com | sh          # Docker + Compose v2
git clone <url-du-repo> agoraci && cd agoraci
```

### Étape 2 — Créer le `.env` directement sur le serveur (jamais committé)
```bash
cp .env.example .env
nano .env
```
Remplis **au minimum** :
- `ENV=production` (active les cookies `Secure`)
- `DOMAIN=agoraci.ci` · `ACME_EMAIL=toi@exemple.com` (pour Let's Encrypt)
- `NUXT_PUBLIC_SITE_URL=https://agoraci.ci` · `FRONTEND_URL=https://agoraci.ci`
- `GOOGLE_REDIRECT_URI=https://agoraci.ci/api/auth/google/callback` (si Google OAuth)
- `NUXT_PUBLIC_ADMIN_PATH=<valeur imprévisible>` (route admin cachée)
- **mots de passe forts** : `POSTGRES_PASSWORD`, `RABBITMQ_PASSWORD`, `MINIO_ROOT_PASSWORD`, `JWT_SECRET`, `SESSION_SECRET`
- IA : `LLM_*` (Gemini) + `EMBEDDING_*` (Cohere), `BREVO_*` (e-mails)

### Étape 3 — Lancer
```bash
docker compose --project-directory . -f infra/docker-compose.prod.yml up -d --build
```
- Traefik obtient le **certificat TLS automatiquement** (port 80/443 doivent être ouverts dans le pare-feu).
- Les **migrations s'appliquent au démarrage** du backend (`alembic upgrade head`).
- Le **super-admin** est créé automatiquement (`SUPERADMIN_*`).

### Étape 4 — Vérifier
```bash
docker compose --project-directory . -f infra/docker-compose.prod.yml ps        # tous "healthy"
docker compose --project-directory . -f infra/docker-compose.prod.yml logs -f backend
```
Puis ouvre **https://agoraci.ci** (le `http://` redirige vers `https://`).

> Sécurité : dans ce compose prod, les services internes (postgres/redis/rabbitmq + consoles
> MinIO/RabbitMQ) **ne sont pas exposés** sur Internet. Pour y accéder en admin, passe par un
> **tunnel SSH** (`ssh -L 15672:localhost:15672 user@vps`).

### Mises à jour ultérieures
```bash
git pull
docker compose --project-directory . -f infra/docker-compose.prod.yml up -d --build
```
(ou, si tu utilises les images du registre GitLab — voir §5 bis — remplace `build:` par `image:`
et fais `... pull && ... up -d`).

### Données
- (Option) Démo : `... -f infra/docker-compose.prod.yml exec backend python -m agoraci.seed`
- **Vrai corpus juridique** : Admin → Base juridique → Import en masse.

---

## 2 bis. Oracle Cloud Always Free — VPS gratuit à vie

Oracle offre une VM **ARM Ampere gratuite à vie** (jusqu'à 4 OCPU / 24 Go RAM) : assez pour
faire tourner **toute** la stack via `infra/docker-compose.prod.yml`, sans mise en veille.

### Créer la VM (console OCI)
- **Compute → Instances → Create instance**
- **Image** : Canonical **Ubuntu 22.04** (le guide ci-dessous suppose Ubuntu)
- **Shape** : *Change shape* → **Ampere (ARM)** → `VM.Standard.A1.Flex` → **4 OCPU / 24 Go RAM**
  (⚠️ ne PAS prendre `VM.Standard.E2.1.Micro` : 1 Go de RAM = trop peu, OOM garanti)
- **Capacity type** : **On-demand** (jamais *Preemptible* → reprise possible à tout moment)
- **Networking** : VCN par défaut, **Assign a public IPv4 address** ✅
- **Storage / Boot volume** : **~100 Go** (quota gratuit de 200 Go)
- **SSH keys** : générer/coller ta clé → note l'**IP publique**

> « Out of capacity » sur l'ARM ? Réessaie plus tard ou change d'Availability Domain.

### Ouvrir les ports 80/443 — LES DEUX pare-feux (piège classique)
1. **Security List (réseau)** : Networking → VCN → Security Lists → *Default* → **Add Ingress Rules** :
   `0.0.0.0/0` TCP **80**, puis `0.0.0.0/0` TCP **443**.
2. **iptables de la VM** (Ubuntu Oracle bloque tout sauf 22), en SSH :
   ```bash
   sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
   sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT
   sudo netfilter-persistent save
   ```

### Déployer
```bash
ssh -i /chemin/cle-privee ubuntu@IP_PUBLIQUE
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker ubuntu && newgrp docker

# Repo privé → Deploy Token GitLab (Settings → Repository → Deploy tokens, scope read_repository)
git clone https://<deploy_user>:<deploy_token>@gitlab.com/personnel4344847/agoraci.git
cd agoraci

cp .env.example .env
nano .env            # ENV=production, DOMAIN, ACME_EMAIL, mots de passe forts, LLM_*, EMBEDDING_*, BREVO_*
chmod 600 .env       # ⚠️ durcissement : secrets lisibles par le seul propriétaire

docker compose --project-directory . -f infra/docker-compose.prod.yml up -d --build
```
> Sur ARM, `build:` produit des images **natives ARM** — on ne pull donc PAS les images
> du registre GitLab (elles sont en amd64). DNS : un enregistrement **A** `domaine → IP` (voir §2).

### Sécurité du `.env` sur la VM
Poser le `.env` sur la machine est **acceptable en mono-VM** (il n'est jamais commité) **si** on le
durcit : `chmod 600 .env` + propriétaire = ton user. À savoir : les variables restent visibles via
`docker inspect` pour qui a accès au démon Docker. Pour aller plus loin : **OCI Vault** (secrets hors
machine) ou **Docker secrets** (Swarm, montés dans `/run/secrets`).

---

## 3. Option B — Render (services managés)

Render n'a pas de RabbitMQ ni de stockage objet persistant pratique → on complète avec **CloudAMQP** (RabbitMQ) et **Cloudflare R2** (fichiers).

### Services à créer
| Service Render | Type | Source |
|---|---|---|
| `agoraci-backend` | **Web Service** (Docker) | `backend/Dockerfile` |
| `agoraci-frontend` | **Web Service** (Docker) | `frontend/Dockerfile` |
| `agoraci-postgres` | **PostgreSQL** managé | activer l'extension `vector` (pgvector) |
| `agoraci-redis` | **Key Value** (Redis) managé | — |
| RabbitMQ | **CloudAMQP** (externe, offre gratuite « Little Lemur ») | — |
| Fichiers | **Cloudflare R2** (externe, S3-compatible) | bucket public `media` |

> Render construit les images **depuis le repo Git** (Dockerfile). Tu n'as donc rien à publier manuellement. (Alternative registry : voir §5.)

### Réseau / routage
Sur Render, chaque service a sa propre URL HTTPS (pas de Traefik). Deux schémas :
- **Sous-domaines séparés** : `https://agoraci.ci` (front) + `https://api.agoraci.ci` (back) → il **faut activer CORS** (`CORS_ORIGINS`) et mettre `NUXT_PUBLIC_API_BASE=https://api.agoraci.ci/api`.
- **Plus simple** : garder le front qui proxifie `/api` vers le back (si tu mets un proxy), mais sur Render le plus direct = sous-domaines + CORS.

### Variables — backend (`agoraci-backend`)
```
ENV=production
POSTGRES_HOST / POSTGRES_PORT / POSTGRES_USER / POSTGRES_PASSWORD / POSTGRES_DB   (depuis la BDD Render)
REDIS_URL=<url Redis Render>
RABBITMQ_URL=<url amqps:// de CloudAMQP>
JWT_SECRET / SESSION_SECRET            (longues chaînes aléatoires)
ACCESS_TOKEN_EXPIRE_MINUTES=15 / REFRESH_TOKEN_EXPIRE_DAYS=30
FRONTEND_URL=https://agoraci.ci
GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET / GOOGLE_REDIRECT_URI=https://api.agoraci.ci/api/auth/google/callback
SUPERADMIN_EMAIL / SUPERADMIN_PASSWORD / SUPERADMIN_USERNAME
LLM_PROVIDER=gemini / LLM_API_KEY=... / LLM_MODEL=gemini-2.5-flash
EMBEDDING_PROVIDER=cohere / EMBEDDING_API_KEY=... / EMBEDDING_MODEL=embed-multilingual-v3.0 / EMBEDDING_DIM=1024
BREVO_API_KEY / BREVO_SENDER_NAME / BREVO_SENDER_EMAIL   (expéditeur vérifié)
VAPID_PUBLIC_KEY / VAPID_PRIVATE_KEY / VAPID_SUBJECT
CORS_ORIGINS=https://agoraci.ci,https://www.agoraci.ci
TURNSTILE_SECRET_KEY=...                (si Turnstile activé)
# Stockage R2 (S3-compatible)
MINIO_ENDPOINT=<accountid>.r2.cloudflarestorage.com
MINIO_ROOT_USER=<R2 Access Key ID>
MINIO_ROOT_PASSWORD=<R2 Secret Access Key>
MINIO_PUBLIC_BUCKET=media
MINIO_SECURE=true
MEDIA_BASE_URL=https://pub-xxxxxxxx.r2.dev    (URL publique du bucket R2)
```

### Variables — frontend (`agoraci-frontend`)
```
NUXT_PUBLIC_SITE_URL=https://agoraci.ci
NUXT_PUBLIC_SITE_NAME=Jamakan
NUXT_PUBLIC_API_BASE=https://api.agoraci.ci/api   (ou /api si même origine)
NUXT_API_INTERNAL=https://api.agoraci.ci          (URL interne du backend)
NUXT_PUBLIC_GOOGLE_ENABLED=true
NUXT_PUBLIC_ADMIN_PATH=<valeur imprévisible>
NUXT_PUBLIC_TURNSTILE_SITE_KEY=...                (si Turnstile activé)
```

### Points spécifiques Render
- **pgvector** : dans la console SQL de la BDD Render → `CREATE EXTENSION IF NOT EXISTS vector;` (les migrations le tentent aussi).
- **Migrations** : le backend les applique au boot (`alembic upgrade head`). Rien à faire.
- **R2 public** : crée un bucket `media`, rends-le public (ou domaine R2 `r2.dev`), mets l'URL dans `MEDIA_BASE_URL`. Les avatars/images y seront servis (plus besoin de la route `/media` Traefik).
- **Worker** : le backend héberge déjà les consumers (jobs, modération, notifs) dans le même process — pas besoin d'un service worker séparé.

---

## 3 bis. Gestion des secrets (⚠️ ne JAMAIS committer de secret)

`.env` est dans `.gitignore` et **n'est jamais poussé**. Seul `.env.example` (placeholders) est versionné. Les vrais secrets se saisissent **directement sur la plateforme** :

| Cible | Où mettre les secrets |
|---|---|
| **Local** | `.env` sur ta machine (gitignored) |
| **VPS** | créer le `.env` **directement sur le serveur** (scp/édition), ou **Docker secrets** (Swarm `/run/secrets`, déjà supporté par la config) |
| **Render** | onglet **Environment** du service (chiffré) ou **Environment Group** / **Secret Files** — jamais dans le repo |
| **render.yaml** (blueprint) | marquer chaque secret `sync: false` → Render demande la valeur dans le dashboard, elle n'est **pas** stockée dans le YAML |

Bonnes pratiques : secrets **longs et aléatoires** (`JWT_SECRET`, `SESSION_SECRET`), **rotation** possible, et **ne jamais** logger une clé.

---

## 4. Variables par service (résumé)

- **Toutes** : voir `.env.example` (commenté).
- **Backend** lit la majorité (BDD, Redis, RabbitMQ, JWT, IA, Brevo, MinIO/R2, CORS, Turnstile…).
- **Frontend** ne lit que les `NUXT_PUBLIC_*` + `NUXT_API_INTERNAL`.
- La **clé secrète** Turnstile va au **backend** (`TURNSTILE_SECRET_KEY`), la **clé publique** au **frontend** (`NUXT_PUBLIC_TURNSTILE_SITE_KEY`).

---

## 5. Publier les images sur un registre (optionnel)

Si tu préfères pré-construire (GHCR / Docker Hub) au lieu de laisser Render builder :

```bash
# Backend
docker build -t ghcr.io/<user>/agoraci-backend:1.0 ./backend
docker push ghcr.io/<user>/agoraci-backend:1.0
# Frontend (prod)
docker build -t ghcr.io/<user>/agoraci-frontend:1.0 ./frontend
docker push ghcr.io/<user>/agoraci-frontend:1.0
```
Puis sur Render : « Deploy an existing image » et renseigner ces tags. (Sur un VPS, tu peux aussi pointer le compose vers ces images au lieu de `build:`.)

---

## 5 bis. CI/CD GitLab — construction automatique des images

Le fichier **`.gitlab-ci.yml`** construit et publie automatiquement les **deux** images
(`backend` + `frontend`) dans le **GitLab Container Registry** du projet, à chaque push.

**Aucune configuration de secret n'est requise** : le pipeline n'utilise que les variables
prédéfinies GitLab (`$CI_REGISTRY`, `$CI_REGISTRY_USER`, `$CI_REGISTRY_PASSWORD = $CI_JOB_TOKEN`).
Il suffit que le **Container Registry** soit activé : *Settings → General → Visibility → Container Registry*.

**Étapes du pipeline :**
| Stage | Job | Rôle |
|-------|-----|------|
| `test` | `lint:backend`, SAST, Secret-Detection | Lint Ruff + scans de sécurité (non bloquants) |
| `build` | `build:backend`, `build:frontend` | Build BuildKit (cache de couches) + push registry |
| `scan` | `scan:backend`, `scan:frontend` | Scan Trivy HIGH/CRITICAL (non bloquant) |

**Tags produits** automatiquement :
- `…/backend:<short-sha>` et `…/frontend:<short-sha>` → à chaque pipeline (traçabilité)
- `…:latest` → sur la branche par défaut (`main`)
- `…:<tag-git>` + `…:latest` → quand tu pousses un tag Git (release) : `git tag v1.0.0 && git push --tags`

**Images publiées** (remplace `<NAMESPACE>` par ton chemin projet, ex. `registry.gitlab.com/personnel4344847/agoraci`) :
```
<NAMESPACE>/backend:latest
<NAMESPACE>/frontend:latest
```

**Récupérer / déployer ces images :**
```bash
# Connexion (token de déploiement ou personnel avec scope read_registry)
docker login registry.gitlab.com
docker pull registry.gitlab.com/<NAMESPACE>/backend:latest
docker pull registry.gitlab.com/<NAMESPACE>/frontend:latest
```
Sur **Render** : « Deploy an existing image » + ces tags ; sur un **VPS**, pointe le `image:` du
compose vers ces tags (au lieu de `build:`) puis `docker compose pull && up -d`.

> Pour un déploiement automatique (CD complet), ajoute un job `deploy` (stage supplémentaire)
> qui appelle un **Deploy Hook** Render ou un `ssh … docker compose pull && up -d` sur le VPS,
> en stockant l'URL/clé du hook dans une variable CI **masquée** (jamais en dur dans le fichier).

---

## 6. Checklist post-déploiement
- [ ] `ENV=production` (cookies `Secure`)
- [ ] Domaines/URLs cohérents (`SITE_URL`, `FRONTEND_URL`, `GOOGLE_REDIRECT_URI`)
- [ ] `NUXT_PUBLIC_ADMIN_PATH` = valeur secrète
- [ ] Secrets forts (JWT, SESSION, BDD, RabbitMQ, MinIO/R2)
- [ ] Brevo : expéditeur vérifié → les codes de vérification partent
- [ ] pgvector activé ; migrations passées (logs backend : `alembic upgrade head`)
- [ ] R2 : bucket `media` public + `MEDIA_BASE_URL` correct (test : upload d'avatar)
- [ ] (option) CORS + Turnstile renseignés
- [ ] Sauvegardes : dump Postgres planifié + versioning R2
- [ ] Charger le **vrai corpus juridique** (Admin → Base juridique → import en masse)
