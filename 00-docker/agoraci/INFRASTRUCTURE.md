# Infrastructure & Déploiement — Jamakan

Ce document décrit **comment Jamakan est déployé en production** et **pourquoi** chaque
choix a été fait. Il sert de référence et de runbook reproductible.

> ⚠️ Toutes les valeurs sensibles (IP, domaine, secrets, chemin d'admin) sont remplacées
> par des **placeholders génériques** (`<...>`). Les vrais secrets ne vivent que dans le
> `.env` du serveur (jamais versionné) et dans les variables CI/CD (jamais dans ce dépôt).

---

## 1. Vue d'ensemble

| Composant | Techno | Rôle |
|---|---|---|
| Frontend | Nuxt 3 (SSR, Node/Nitro) | Site public + interface admin |
| Backend | FastAPI (Python, monolithe modulaire) | API, RAG « Nanan », auth, forum, modération |
| Base de données | PostgreSQL + pgvector | Données + recherche vectorielle (RAG) |
| Cache / temps réel | Redis | Sessions, codes, cache |
| File de messages | RabbitMQ | Événements + ingestion en arrière-plan |
| Stockage objet | MinIO (S3-compatible) | Images / avatars / fichiers |
| Reverse-proxy / TLS | Traefik v3 | Routage + HTTPS automatique (Let's Encrypt) |

**Principe directeur :** 1 image backend + 1 image frontend, tout le reste en images publiques.
Aucun secret en dur : tout passe par variables d'environnement (`.env` serveur) ou variables CI/CD.

---

## 2. Choix d'hébergement — Oracle Cloud « Always Free »

**Décision :** VM ARM (Ampere A1.Flex, jusqu'à 4 OCPU / 24 Go) du palier *Always Free* d'Oracle.

**Justification :**
- **Gratuit à vie** et suffisamment puissant (24 Go RAM) pour faire tourner **toute** la stack
  (Postgres, Redis, RabbitMQ, MinIO, backend, frontend, Traefik) sur une seule machine.
- Les offres « web services » gratuites concurrentes **mettent les apps en veille** et n'offrent
  ni RabbitMQ ni stockage objet — inadaptées à cette stack.
- Alternative payante simple (si besoin de scaler plus tard) : un VPS ~4–6 €/mois.

### Création de la VM (console OCI)
- **Image :** Ubuntu LTS **aarch64** (ARM) — l'architecture doit correspondre au shape ARM.
- **Shape :** `VM.Standard.A1.Flex`, réglé sur **4 OCPU / 24 Go** (maximum du Always Free).
- **Capacity type :** *On-demand* (jamais *Preemptible*, qui peut être repris à tout moment).
- **Boot volume :** ~50–100 Go (quota gratuit 200 Go).
- **Réseau :** VCN + sous-réseau **public** + **IP publique réservée** (stable, survit aux recréations).
- **Clé SSH :** paire dédiée téléchargée à la création (la clé privée ne s'affiche qu'une fois).

---

## 3. Réseau & pare-feux — la règle des DEUX couches

Sur une VM Oracle, **deux pare-feux** filtrent le trafic et **les deux** doivent autoriser les ports :

1. **Security List / NSG (niveau réseau Oracle)** — géré dans la console web. On y ouvre en
   *Ingress* : `0.0.0.0/0` TCP **22, 80, 443**.
2. **iptables (dans la VM)** — les images Ubuntu d'Oracle bloquent tout sauf le 22 par défaut.
   On insère les règles pour **80** et **443** **avant** la règle `REJECT`, puis on les rend
   persistantes :
   ```bash
   sudo iptables -I INPUT <pos> -p tcp -m state --state NEW -m tcp --dport 80  -j ACCEPT
   sudo iptables -I INPUT <pos> -p tcp -m state --state NEW -m tcp --dport 443 -j ACCEPT
   sudo netfilter-persistent save
   ```

**Justification :** oublier la couche iptables est l'erreur n°1 (le site reste injoignable alors que
le NSG est ouvert). Ouvrir uniquement 22/80/443 respecte le principe de moindre exposition ; Postgres,
Redis et RabbitMQ **ne sont jamais exposés** (réseau Docker interne uniquement).

---

## 4. DNS

**Décision :** un **sous-domaine** `<VOTRE_DOMAINE>` (ex. `app.exemple.com`) via un enregistrement
**A** pointant vers `<IP_DU_VPS>`.

**Justification :**
- Un sous-domaine est **indépendant** du domaine racine (qui peut servir un autre site) — aucun risque
  pour l'existant.
- Chez Cloudflare, l'enregistrement est mis en **DNS only (gris)** au premier déploiement pour que
  Let's Encrypt valide directement le serveur (le proxy orange pourra être activé ensuite).

---

## 5. Préparation du serveur

```bash
curl -fsSL https://get.docker.com | sudo sh        # Docker + Compose v2
sudo usermod -aG docker $USER && newgrp docker
```

**Justification :** Docker + Compose suffisent à tout orchestrer ; pas besoin d'installer Python,
Node, Postgres… sur l'hôte (tout est conteneurisé, donc reproductible et isolé).

---

## 6. Configuration — `.env` de production

Le `.env` **vit sur le serveur** (créé à la main, `chmod 600`), **jamais committé**. Seul
`.env.example` (placeholders) est versionné.

**Bonnes pratiques appliquées :**
- **Mots de passe forts générés sur le serveur** (`openssl rand`) pour Postgres / RabbitMQ / MinIO /
  `JWT_SECRET` / `SESSION_SECRET` — jamais tapés ni affichés.
- Clés d'API (LLM, embeddings, e-mail) conservées hors du dépôt.
- `ENV=production` (cookies `Secure`), URLs en `https://<VOTRE_DOMAINE>`.
- **Chemin d'admin secret** via `NUXT_PUBLIC_ADMIN_PATH=<CHEMIN_ADMIN_SECRET>` (voir §9).

**Justification :** poser le `.env` sur une VM mono-utilisateur est acceptable **s'il est durci**
(`chmod 600`). Pour aller plus loin : OCI Vault ou Docker secrets.

---

## 7. Déploiement — Docker Compose + HTTPS automatique

Fichier `infra/docker-compose.prod.yml` :
```bash
docker compose --project-directory . -f infra/docker-compose.prod.yml up -d --build
```

- **Traefik** obtient et renouvelle le **certificat TLS Let's Encrypt** automatiquement
  (redirection HTTP→HTTPS, e-mail ACME tiré du `.env`).
- Le backend applique les **migrations** (`alembic upgrade head`) et crée le **super-admin** au démarrage.
- Services internes non exposés ; seuls 80/443 (et 22 pour l'admin) sont publics.

**Justification :** un seul fichier décrit toute la prod ; le TLS auto évite la gestion manuelle des
certificats ; les healthchecks garantissent un ordre de démarrage correct.

---

## 8. CI/CD — GitLab

Pipeline (`.gitlab-ci.yml`), étapes : **test → build → scan → deploy → release**.

| Étape | Contenu | Justification |
|---|---|---|
| **test** | Lint (Ruff) + SAST + détection de secrets | Qualité & sécurité, non bloquants |
| **build** | `buildx` (amd64) + **cache registre `mode=max`** + push | Cache complet des couches (apt/uv/npm) → builds rapides |
| **scan** | Trivy (HIGH/CRITICAL) | Vulnérabilités des images |
| **deploy** | SSH → VPS : `git archive` + `docker compose up -d --build` | Voir décision ci-dessous |
| **release** | semantic-release (voir §10) | Versioning automatique |

### Décision : build ARM **sur la VM**, pas dans le CI
- La VM est **ARM** ; les runners GitLab gratuits sont **amd64**.
- Construire de l'ARM dans le CI via **QEMU** a été testé : **trop lent (>20 min)**.
- Un rebuild **sur la VM** avec cache Docker local est **quasi instantané (~2 s)** quand rien ne
  change, et natif-rapide sinon. → On build donc sur la VM au déploiement.

### Sécurité du déploiement
- **Aucun secret dans le `.gitlab-ci.yml`** : tout vient de variables CI/CD **Protected** :
  `SSH_PRIVATE_KEY` (clé de déploiement **dédiée**, encodée en **base64** pour éviter la corruption de
  format), `SSH_KNOWN_HOSTS`, `DEPLOY_HOST`, `DEPLOY_USER`.
- La clé de déploiement est **distincte** de la clé personnelle : en cas de fuite, on la révoque sans
  perdre l'accès admin.
- Déploiement uniquement sur la branche par défaut (protégée).

---

## 9. Sécurité — récapitulatif

- **Chemin d'admin imprévisible** : `NUXT_PUBLIC_ADMIN_PATH`. Le renommage de la route se fait **au
  build** (hook Nuxt `pages:extend`) → la variable est passée en **build arg** (sinon l'admin resterait
  sur `/admin`). `/admin` devient alors **404** ; seul le chemin secret mène au super-admin.
- HTTPS partout (HSTS via Traefik), cookies `Secure` en production.
- Secrets hors dépôt ; mots de passe forts ; clé de déploiement dédiée.
- Surface réseau minimale (22/80/443) ; bases de données non exposées.

---

## 10. Releases automatiques — semantic-release

Config `.releaserc.json` + job `release`. À partir des **commits conventionnels** :

| Préfixe | Effet |
|---|---|
| `feat:` | version **mineure** |
| `fix:` | **patch** |
| `feat!:` / `BREAKING CHANGE` | version **majeure** |
| `chore:` `docs:` `ci:` `refactor:` | pas de release |

Génère automatiquement : **version**, **`CHANGELOG.md`**, **tag Git**, **Release GitLab**.

**Prérequis :** une variable CI/CD `GITLAB_TOKEN` (scopes `api` + `write_repository`). Le job est
inactif tant qu'elle n'existe pas (aucun impact sur le reste du pipeline).

---

## 11. Exploitation courante

```bash
# État des services
docker compose --project-directory . -f infra/docker-compose.prod.yml ps
# Logs
docker compose --project-directory . -f infra/docker-compose.prod.yml logs -f backend
# Mise à jour : un simple push sur la branche par défaut redéploie automatiquement.
```

**Charger le corpus juridique** (indispensable pour que « Nanan » réponde avec de vraies sources) :
interface admin → **Base juridique** → import en masse (URL, PDF, ou crawl).
