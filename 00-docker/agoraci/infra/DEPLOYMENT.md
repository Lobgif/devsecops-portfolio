# Guide de déploiement — Jamakan

Jamakan = **2 images applicatives** seulement :

| Image | Rôle | Construite depuis |
|---|---|---|
| `backend` | Toutes les API (auth, forum, rag, modération, notifications) + WebSocket | `backend/Dockerfile` |
| `frontend` | SPA/SSR Nuxt 3 | `frontend/Dockerfile` |

…plus des **services d'infrastructure** en images officielles (pas de build) :
PostgreSQL (pgvector), Redis, RabbitMQ, MinIO, Traefik.

> ⚠️ **Aucune valeur n'est codée en dur.** Toute la configuration passe par des
> variables d'environnement. Copier `.env.example` → `.env` et tout renseigner.

---

## 1. Variables d'environnement (obligatoire)

Copier le modèle puis éditer :

```bash
cp .env.example .env
```

Variables **critiques** à définir absolument :

| Variable | Description |
|---|---|
| `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` | Base de données |
| `RABBITMQ_USER` / `RABBITMQ_PASSWORD` | File de messages |
| `MINIO_ROOT_USER` / `MINIO_ROOT_PASSWORD` | Stockage objet |
| `JWT_SECRET` | Signature des tokens (chaîne aléatoire longue) |
| `SESSION_SECRET` | État OAuth (chaîne aléatoire) |
| `SUPERADMIN_EMAIL` / `SUPERADMIN_PASSWORD` | Compte super-admin créé au 1er démarrage |
| `BREVO_API_KEY` / `BREVO_SENDER_EMAIL` | Emails (vérification, notifications) |
| `LLM_PROVIDER` + `LLM_API_KEY` / `EMBEDDING_PROVIDER` + `EMBEDDING_API_KEY` | IA juridique (RAG) |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | Connexion Google (optionnel) |
| `NUXT_PUBLIC_SITE_URL` | URL publique du site (SEO, liens, OAuth) |

Sans clés IA/Brevo, l'app démarre quand même (mode dégradé : pas d'email réel, réponses IA factices).

---

## 2. Développement local (Docker Compose)

Toujours **depuis la racine du dépôt** (pas depuis `infra/`) :

```bash
make up        # build + démarre tout
make logs      # suivre les logs
make ps        # état des conteneurs
make down      # arrêter
```

Équivalent sans `make` :
```bash
docker compose --project-directory . -f infra/docker-compose.yml up --build -d
```

Accès : http://localhost (site) · http://localhost:8080 (Traefik) ·
http://localhost:15672 (RabbitMQ) · http://localhost:9001 (MinIO).

### Migrations de base de données
En local les tables sont créées automatiquement. Pour générer/appliquer des
migrations Alembic (recommandé avant la prod) :
```bash
make migration m="init"   # génère la migration depuis les modèles
make migrate              # applique
```

---

## 3. Production — Option A : Docker Swarm

```bash
# Sur le nœud manager
make swarm-init                     # une seule fois
make secrets                        # crée les secrets Docker (mdp DB/JWT/RabbitMQ)

# Build + push des 2 images vers ton registre
export REGISTRY=registry.exemple.ci/agoraci TAG=1.0.0
make push

# Déploiement (renseigner le domaine + l'email Let's Encrypt)
export DOMAIN=agoraci.ci ACME_EMAIL=contact@agoraci.ci
# + exporter les variables applicatives (BREVO_API_KEY, LLM_API_KEY, SUPERADMIN_*, ...)
make deploy

docker stack services agoraci       # état
```

Swarm gère la réplication, le rolling update et le redémarrage. Traefik fournit
le HTTPS automatique (Let's Encrypt). Les mots de passe sensibles sont des
**secrets Docker** (montés dans `/run/secrets`), le reste vient des variables d'env.

**Pré-requis nœuds** : étiqueter le nœud qui héberge les données :
```bash
docker node update --label-add db=true <NODE_ID>
```

---

## 4. Production — Option B : Render (ou PaaS équivalent)

Pas de Swarm. On déploie **2 services** + des add-ons managés :

| Sur Render | Quoi |
|---|---|
| **Web Service** `backend` | Repo, root `backend/`, Dockerfile. Port 8000. |
| **Web Service** `frontend` | Repo, root `frontend/`, Dockerfile. Port 3000. |
| **PostgreSQL** (add-on managé) | Activer l'extension `vector` (pgvector) |
| **Redis** (add-on managé / Upstash) | — |
| **RabbitMQ** | Externe : **CloudAMQP** (Render n'en fournit pas) |
| **Stockage objet** | **S3 / Backblaze B2** (au lieu de MinIO) |

Étapes :
1. Créer les add-ons (Postgres, Redis), noter leurs URLs.
2. Créer un compte CloudAMQP → récupérer `RABBITMQ_URL`.
3. Dans chaque service Render, renseigner les **variables d'environnement**
   (les mêmes que `.env`) — *via le dashboard Render, jamais dans le code*.
   - backend : `POSTGRES_*` (ou `DATABASE_URL` décomposée), `REDIS_URL`,
     `RABBITMQ_URL`, `JWT_SECRET`, `SESSION_SECRET`, `BREVO_API_KEY`,
     `LLM_*`, `EMBEDDING_*`, `GOOGLE_*`, `SUPERADMIN_*`, `FRONTEND_URL`,
     `GOOGLE_REDIRECT_URI`.
   - frontend : `NUXT_PUBLIC_API_BASE` (URL publique du backend, ex.
     `https://api.agoraci.ci/api`), `NUXT_API_INTERNAL` (idem),
     `NUXT_PUBLIC_SITE_URL`, `NUXT_PUBLIC_SITE_NAME`.
4. Lancer les migrations une fois : `alembic upgrade head` (via un Job Render
   ou un shell sur le service backend).

> Sur Render, le backend doit écouter le port fourni par `$PORT` ; adapte la
> commande de démarrage si besoin : `uvicorn agoraci.main:app --host 0.0.0.0 --port $PORT`.

---

## 4 bis. Activer la connexion Google (optionnel)

Par défaut le bouton « Continuer avec Google » est **masqué** et l'endpoint renvoie 503,
car aucune clé n'est configurée. Pour l'activer :

1. Google Cloud Console → *APIs & Services* → *Credentials* → **Create OAuth client ID**
   (type *Web application*).
2. **Authorized redirect URI** :
   - local : `http://localhost/api/auth/google/callback`
   - prod  : `https://<DOMAIN>/api/auth/google/callback`
3. Renseigner dans `.env` (ou variables Render) :
   ```
   GOOGLE_CLIENT_ID=...
   GOOGLE_CLIENT_SECRET=...
   GOOGLE_REDIRECT_URI=http://localhost/api/auth/google/callback   # adapter en prod
   NUXT_PUBLIC_GOOGLE_ENABLED=true                                  # affiche le bouton
   ```
4. Redémarrer : `make up` (ou recréer les services backend + frontend).

---

## 4 ter. Corpus juridique (RAG)

L'IA juridique répond à partir des textes **ingérés** dans la base (table `rag.chunks`).

- **Corpus de démonstration** (illustratif, non officiel) :
  `./dev.sh seed-corpus`  (ou `make seed-corpus`)
- **Ingérer un vrai texte** (super-admin) — découpage automatique par article :
  ```bash
  curl -X POST http://localhost/api/rag/ingest-document \
    -H "Authorization: Bearer <TOKEN_SUPERADMIN>" -H "Content-Type: application/json" \
    -d '{"title":"Code de la famille 2019","content":"Article 1 : ...","code_source":"Code de la famille"}'
  ```
- **Qualité** : sans `EMBEDDING_PROVIDER`/`LLM_PROVIDER` configurés, le système tourne en
  **mode dégradé** (embeddings factices + réponse générique). Renseigner les clés IA
  (section variables) améliore drastiquement la pertinence et active les vraies réponses.

---

## 4 quater. Web Push (VAPID) — notifications navigateur

Les clés VAPID ne s'obtiennent sur **aucune plateforme** : on les **génère localement**
(une paire de clés, aucun compte). Méthodes :

```bash
# Option 1 (Node) :
npx web-push generate-vapid-keys

# Option 2 (depuis le conteneur backend, déjà équipé) :
docker compose --project-directory . -f infra/docker-compose.yml exec backend python - <<'PY'
import base64
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
k = ec.generate_private_key(ec.SECP256R1())
priv = k.private_numbers().private_value.to_bytes(32, "big")
pub = k.public_key().public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)
b = lambda x: base64.urlsafe_b64encode(x).rstrip(b"=").decode()
print("VAPID_PUBLIC_KEY=" + b(pub)); print("VAPID_PRIVATE_KEY=" + b(priv))
PY
```

Coller le résultat dans `.env` (`VAPID_PUBLIC_KEY`, `VAPID_PRIVATE_KEY`). La clé **publique**
sera exposée au navigateur, la **privée** reste secrète côté serveur.

> Le code d'envoi web push n'est pas encore branché — ces clés sont prêtes pour quand
> on activera la fonctionnalité. Les **notifications in-app** (cloche) fonctionnent déjà.

---

## 4 quinquies. Sécurité — auth & tokens

- **Cookies httpOnly** : les JWT (`access_token`, `refresh_token`) sont posés en cookies
  `HttpOnly` + `SameSite=Lax` + `Secure` (en production). Ils sont **inaccessibles au JavaScript**
  → immunisés contre le vol par XSS. Aucun token n'est stocké dans `localStorage`.
- **OAuth Google** : les cookies sont posés directement sur la redirection (aucun token dans l'URL).
- **CSRF** : `SameSite=Lax` empêche l'envoi des cookies sur les requêtes cross-site → protège les
  endpoints d'état. (Pour un durcissement maximal, ajouter un jeton CSRF double-submit.)
- **Repli `Authorization: Bearer`** accepté (scripts, tests, intégrations serveur).
- En prod : servir en **HTTPS** (Traefik le fait) pour que `Secure` s'applique ; envisager une **CSP** stricte côté frontend.
- Secrets : `JWT_SECRET`, `SESSION_SECRET`, mots de passe DB = valeurs aléatoires fortes ;
  en Swarm via secrets Docker, sur Render via variables d'environnement. Ne jamais committer `.env`.

---

## 4 sexies. Couverture juridique du RAG

L'IA répond **uniquement à partir des textes ingérés** dans `rag.chunks` — elle n'est pas
limitée à des sujets prédéfinis. Pour couvrir l'ensemble du droit ivoirien, **ingérer les
textes officiels** par domaine (famille, successions, travail, **commerce/OHADA, impôts,
foncier**, pénal, etc.) via `POST /api/rag/ingest-document` (super-admin) ou le pipeline.
Le découpage par article est automatique. Plus le corpus est complet, plus les réponses
couvrent de sujets.

---

## 5. Checklist de mise en production

- [ ] `.env` / variables Render renseignés (aucun secret par défaut conservé)
- [ ] `JWT_SECRET`, `SESSION_SECRET`, mots de passe = valeurs aléatoires fortes
- [ ] pgvector activé sur la base
- [ ] Migrations Alembic appliquées (`alembic upgrade head`)
- [ ] Expéditeur Brevo vérifié + clé API valide
- [ ] `GOOGLE_REDIRECT_URI` enregistré dans la console Google Cloud
- [ ] `NUXT_PUBLIC_SITE_URL` = URL publique réelle (SEO, sitemap, OAuth)
- [ ] Super-admin : se connecter puis changer le mot de passe
