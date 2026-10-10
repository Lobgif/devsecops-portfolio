// Test de charge k6 — capacité en LECTURE (pages SSR publiques).
//
// Objectif : trouver combien d'utilisateurs simultanés la VM encaisse en
// navigation (accueil, forums, à propos) — SANS toucher à l'IA (coûteuse) ni
// aux écritures. Monte progressivement les VUs (utilisateurs virtuels) et
// mesure latence + taux d'erreur.
//
// Lancer (Docker, aucune install) :
//   docker run --rm -i -e BASE_URL=https://jamakan.kaedys.com grafana/k6 run - < tests/load/read-capacity.js
// Ou avec k6 installé :
//   BASE_URL=https://jamakan.kaedys.com k6 run tests/load/read-capacity.js
//
// Variables : BASE_URL (défaut prod), MAX_VUS (défaut 200), STAGE (défaut "ramp").

import http from 'k6/http'
import { check, sleep } from 'k6'
import { Rate, Trend } from 'k6/metrics'

const BASE = __ENV.BASE_URL || 'https://jamakan.kaedys.com'
const MAX = parseInt(__ENV.MAX_VUS || '200', 10)

const errors = new Rate('erreurs')
const ttfb = new Trend('ttfb_ms', true)

export const options = {
  scenarios: {
    // Montée en charge progressive jusqu'à MAX utilisateurs simultanés.
    ramp: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '30s', target: Math.round(MAX * 0.1) },
        { duration: '1m', target: Math.round(MAX * 0.25) },
        { duration: '1m', target: Math.round(MAX * 0.5) },
        { duration: '1m', target: MAX },
        { duration: '30s', target: 0 },
      ],
      gracefulRampDown: '10s',
    },
  },
  thresholds: {
    http_req_duration: ['p(95)<1500'], // 95 % des requêtes sous 1,5 s
    erreurs: ['rate<0.05'],            // moins de 5 % d'erreurs
  },
}

// Pages SSR publiques uniquement (lecture). Pas d'IA, pas d'écriture, pas de login.
const PAGES = ['/', '/forums', '/about', '/classement']

export default function () {
  const path = PAGES[Math.floor(Math.random() * PAGES.length)]
  const res = http.get(`${BASE}${path}`, { tags: { name: path } })

  ttfb.add(res.timings.waiting)
  const ok = check(res, {
    'statut 200': (r) => r.status === 200,
    'HTML reçu': (r) => (r.body || '').includes('<!DOCTYPE html>') || (r.body || '').includes('<html'),
  })
  errors.add(!ok)

  // 1 à 3 s entre deux pages : imite un vrai utilisateur qui lit.
  sleep(Math.random() * 2 + 1)
}
