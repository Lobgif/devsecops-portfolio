# Tests de charge (k6)

Mesure la **capacité en lecture** de la plateforme : combien d'utilisateurs
simultanés la VM Oracle (4 cœurs ARM / 24 Go) encaisse en navigation.

## Lancer

Sans rien installer (Docker) :

```bash
docker run --rm -i -e BASE_URL=https://jamakan.kaedys.com grafana/k6 run - < tests/load/read-capacity.js
```

Avec k6 installé :

```bash
BASE_URL=https://jamakan.kaedys.com k6 run tests/load/read-capacity.js
```

Réglages (variables d'env) :
- `BASE_URL` — cible (défaut : la prod).
- `MAX_VUS` — pic d'utilisateurs simultanés (défaut : `200`). Ex. `-e MAX_VUS=500`.

## Règles de sécurité

- ✅ **Lecture seule** : le script ne tape que des pages SSR publiques
  (`/`, `/forums`, `/about`, `/classement`).
- ⛔ **Jamais l'IA (Nanan)** : chaque appel coûte de l'argent (Gemini).
- ⚠️ Le **rate-limiter** backend peut renvoyer des `429` sous forte charge —
  c'est la protection qui fonctionne, pas une panne.
- 🕒 Lancer **quand il n'y a pas d'utilisateurs réels** (nuit, ou avant lancement).

## Lire les résultats

- `http_req_duration p(95)` : 95 % des requêtes sont servies sous cette durée.
  On vise **< 1,5 s**.
- `erreurs` (rate) : proportion de requêtes non-200. On vise **< 5 %**.
- Le **point de rupture** = le palier de VUs où la latence explose ou les
  erreurs grimpent → c'est ta capacité pratique en simultané.

> ⚠️ Lancé depuis une machine à faible bande passante, c'est **le réseau** qui
> limite, pas le serveur. Pour un chiffre fiable, lance depuis une machine bien
> connectée (ou un petit VPS proche géographiquement).
