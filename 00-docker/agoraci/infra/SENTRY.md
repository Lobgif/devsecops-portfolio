# Sentry — Suivi d'erreurs (front + back)

Capture les **erreurs JS (front)** et les **exceptions FastAPI (back)** avec la page/route
concernée et la trace. **Gratuit** (offre Developer). **Inerte** tant que la clé DSN est vide.

---

## 1. Créer le compte (action manuelle, une fois)
- Va sur **https://sentry.io** → crée un compte gratuit.
- Crée **2 projets** :
  - un projet **JavaScript / Vue** (ou "Browser") → donne un **DSN front**
  - un projet **Python / FastAPI** → donne un **DSN back**
- Un DSN ressemble à : `https://abc123@o456.ingest.sentry.io/789`.

> Tu peux aussi n'utiliser qu'**un seul** projet et le même DSN des deux côtés si tu préfères
> commencer simple.

## 2. Ajouter les clés dans le `.env` de la VM (`~/agoraci/.env`)
```dotenv
# Backend (Python)
SENTRY_DSN=https://...ingest.sentry.io/...
# Frontend (navigateur)
NUXT_PUBLIC_SENTRY_DSN=https://...ingest.sentry.io/...
```
(Optionnel) `SENTRY_TRACES_SAMPLE_RATE=0` (laisser à 0 pour ne suivre que les erreurs, pas la
performance → économise le quota gratuit.)

## 3. Redéployer
Un simple `git push` (CI) suffit, **ou** sur la VM :
```bash
cd ~/agoraci
docker compose --project-directory . -f infra/docker-compose.prod.yml up -d --build backend frontend
```

## Vérifier
- Front : ouvre la console du navigateur → aucune erreur d'init.
- Provoque une erreur test (ou attends une vraie) → elle apparaît dans Sentry avec la **page** et la **trace**.
- Back : Sentry instrumente FastAPI automatiquement ; toute exception 500 remonte avec la **route**.

## Confidentialité
`send_default_pii=False` des deux côtés → Sentry ne reçoit **pas** de données personnelles,
seulement les erreurs techniques.
