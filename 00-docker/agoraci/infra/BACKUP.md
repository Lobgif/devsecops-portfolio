# Sauvegardes PostgreSQL (hors VM) — runbook

Objectif : si la VM Oracle disparaît, on peut **restaurer la base**. Un `pg_dump`
quotidien est chiffré (optionnel) et envoyé vers un **stockage objet externe**
S3-compatible (Cloudflare R2 recommandé, ou Backblaze B2).

Service : `db-backup` (image `eeshugerman/postgres-backup-s3`), profil compose
`backup`. Planifié à **03h00 UTC**, rétention **14 jours** (réglables via
`BACKUP_SCHEDULE` / `BACKUP_KEEP_DAYS`).

---

## 1) Créer le bucket + les clés (Cloudflare R2)

1. Cloudflare → **R2** → **Create bucket** (ex. `jamakan-backups`).
2. R2 → **Manage R2 API Tokens** → **Create API token** :
   - Permissions : **Object Read & Write**, limité à ce bucket.
   - Note l'**Access Key ID** et la **Secret Access Key**.
3. Récupère ton **Account ID** (page R2) → l'endpoint est :
   `https://<ACCOUNT_ID>.r2.cloudflarestorage.com`

*(Backblaze B2 : même principe, l'endpoint ressemble à
`https://s3.<region>.backblazeb2.com`.)*

## 2) Renseigner les variables CI/CD (GitLab)

Projet → **Settings → CI/CD → Variables** (cocher **Protected**, et **Masked**
pour les secrets) :

| Variable | Valeur |
|---|---|
| `S3_ENDPOINT` | `https://<ACCOUNT_ID>.r2.cloudflarestorage.com` |
| `S3_BUCKET` | `jamakan-backups` |
| `S3_ACCESS_KEY_ID` | (clé R2) |
| `S3_SECRET_ACCESS_KEY` | (secret R2) — **Masked** |
| `S3_REGION` | `auto` |

## 3) Activer

Pipeline `main` → job manuel **`backup:up`** → ▶.
Il écrit les variables S3 dans le `.env` de la VM (idempotent), démarre le
service `db-backup` et **déclenche une sauvegarde de test immédiate**.

## 4) Vérifier

- Dans le bucket R2, un fichier `agoraci-db/…​.sql.gz` doit apparaître.
- Logs : `docker compose … logs db-backup` sur la VM.

---

## 5) RESTAURER (à tester au moins une fois !)

1. Télécharge le dernier dump depuis R2 (console Cloudflare, ou `rclone`/`aws s3 cp`).
2. Sur la VM :

```bash
cd ~/agoraci
# décompresse et réinjecte dans le conteneur postgres
gunzip -c chemin/vers/backup.sql.gz | \
  docker compose --project-directory . -f infra/docker-compose.prod.yml \
  exec -T postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"
```

> Si `PASSPHRASE` a été défini (dump chiffré `.gpg`), déchiffre d'abord :
> `gpg --decrypt --batch --passphrase "$BACKUP_PASSPHRASE" backup.sql.gz.gpg > backup.sql.gz`

3. Redémarre le backend pour repartir sur des connexions saines :
   `docker compose … up -d backend`

---

## Notes

- Les backups partent sur le réseau `internal` (accès sortant Internet OK).
- Le profil `backup` ne démarre **pas** avec un déploiement normal et n'est pas
  arrêté par ceux-ci (comme Umami) : une fois activé, il tourne en continu.
- **À faire aussi un jour** : sauvegarde du volume MinIO (avatars/images) — moins
  critique (ré-uploadables) mais utile. Non couvert ici pour rester simple.
