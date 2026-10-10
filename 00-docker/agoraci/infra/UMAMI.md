# Umami — Analytics respectueux de la vie privée (auto-hébergé, gratuit)

Umami tourne sur la VM, à côté de l'app, **derrière le profil Docker Compose `analytics`**
(il ne démarre donc pas avec le déploiement normal — zéro risque pour l'app).

Sans cookies, sans bandeau de consentement, données 100 % chez toi.

---

## 1. DNS (à faire une fois, côté fournisseur de domaine)
Ajoute un enregistrement **A** :

```
analytics.agoraci.ibrahimafofana.com   A   89.168.34.136
```
(ou `analytics.agoraci.ci` quand tu auras le domaine.)

## 2. Variables à ajouter dans le `.env` de la VM (`~/agoraci/.env`)
```dotenv
ANALYTICS_DOMAIN=analytics.agoraci.ibrahimafofana.com
UMAMI_DB_PASSWORD=<mot de passe long aléatoire>
UMAMI_APP_SECRET=<chaîne aléatoire longue>
```
> Générer un secret : `openssl rand -hex 32`

## 3. Démarrer Umami (une seule fois)
```bash
cd ~/agoraci
docker compose --project-directory . -f infra/docker-compose.prod.yml --profile analytics up -d
```
Traefik obtient automatiquement le certificat HTTPS pour `analytics.…`.

## 4. Première connexion Umami
- Ouvre `https://analytics.agoraci.ibrahimafofana.com`
- Identifiants par défaut : **admin / umami** → **change le mot de passe immédiatement** (Settings → Profile).
- **Settings → Websites → Add website** : Name = Jamakan, Domain = `agoraci.ibrahimafofana.com`.
- Copie le **Website ID** (et l'URL du script `https://analytics.…/script.js`).

## 5. Activer le tracking dans l'app
Dans le `.env` de la VM, ajoute :
```dotenv
NUXT_PUBLIC_UMAMI_SRC=https://analytics.agoraci.ibrahimafofana.com/script.js
NUXT_PUBLIC_UMAMI_ID=<Website ID copié à l'étape 4>
```
Puis redéploie le frontend (un simple push déclenche la CI, **ou** sur la VM) :
```bash
docker compose --project-directory . -f infra/docker-compose.prod.yml up -d --build frontend
```

## Vérifier
- Ouvre le site, navigue 2-3 pages.
- Dans Umami → Dashboard, les vues apparaissent en quasi temps réel.
- « Pages » te montre les pages les plus/moins visitées (= tes pages faibles).

## Arrêter / mettre en pause
```bash
docker compose --project-directory . -f infra/docker-compose.prod.yml --profile analytics down
```
