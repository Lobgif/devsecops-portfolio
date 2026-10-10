// Configuration Nuxt 3 — SSR activé pour le SEO.
// Toutes les valeurs sensibles/variables viennent de l'environnement
// (NUXT_PUBLIC_* sont injectables sur Render, Docker, etc. sans toucher au code).

export default defineNuxtConfig({
  compatibilityDate: '2025-01-01',
  ssr: true,
  devtools: { enabled: true },

  modules: [
    '@nuxtjs/tailwindcss',
    '@primevue/nuxt-module',
    '@pinia/nuxt',
    '@nuxtjs/i18n',
    '@nuxtjs/sitemap',
    '@nuxtjs/robots',
    'nuxt-security',
  ],

  css: ['~/assets/css/main.css', 'primeicons/primeicons.css'],

  // Variables d'environnement
  runtimeConfig: {
    // Privé (serveur uniquement) : URL interne de l'API pour le rendu SSR
    apiInternal: process.env.NUXT_API_INTERNAL || 'http://gateway',
    public: {
      // Public (client) : appels API depuis le navigateur (via Traefik en local)
      apiBase: process.env.NUXT_PUBLIC_API_BASE || '/api',
      siteUrl: process.env.NUXT_PUBLIC_SITE_URL || 'http://localhost:3000',
      siteName: process.env.NUXT_PUBLIC_SITE_NAME || 'Jamakan',
      // Affiche le bouton « Continuer avec Google » seulement si configuré
      googleEnabled: process.env.NUXT_PUBLIC_GOOGLE_ENABLED === 'true',
      // Chemin (secret) de l'interface super-admin — modifiable via .env sans toucher au code
      adminPath: process.env.NUXT_PUBLIC_ADMIN_PATH || 'admin',
      // Cloudflare Turnstile (anti-robot) — vide = désactivé (honeypot seul)
      turnstileSiteKey: process.env.NUXT_PUBLIC_TURNSTILE_SITE_KEY || '',
      // Umami (analytics respectueux de la vie privée) — surchargeable via .env
      umamiSrc: process.env.NUXT_PUBLIC_UMAMI_SRC || 'https://analytics.agoraci.ibrahimafofana.com/script.js',
      umamiId: process.env.NUXT_PUBLIC_UMAMI_ID || '9c9d344c-6f8c-4a6c-aaa0-84f68831b694',
      // Sentry (suivi d'erreurs front) — DSN par défaut (projet agoraci-frontend, public par nature),
      // surchargeable par NUXT_PUBLIC_SENTRY_DSN.
      sentryDsn: process.env.NUXT_PUBLIC_SENTRY_DSN || 'https://9745e8f50dcda8b68662e829a5e00091@o4512086570893312.ingest.de.sentry.io/4512086580199504',
    },
  },

  // Renomme les routes /admin/* vers le chemin secret défini dans .env (NUXT_PUBLIC_ADMIN_PATH).
  // /admin n'existe alors plus (404) : seul le chemin imprévisible mène au super-admin.
  hooks: {
    'pages:extend'(pages) {
      const secret = process.env.NUXT_PUBLIC_ADMIN_PATH || 'admin'
      if (secret === 'admin') return
      const repath = (list: any[]) => {
        for (const p of list) {
          if (p.path === '/admin') p.path = `/${secret}`
          else if (p.path.startsWith('/admin/')) p.path = `/${secret}/${p.path.slice('/admin/'.length)}`
          if (p.children?.length) repath(p.children)
        }
      }
      repath(pages)
    },
  },

  // Sécurité (nuxt-security) : CSP avec NONCE (vraie protection XSS, sans 'unsafe-inline' pour les scripts).
  security: {
    nonce: true,
    // Désactive les middlewares qui pourraient gêner (on a notre propre rate-limit côté backend)
    rateLimiter: false,
    requestSizeLimiter: false,
    xssValidator: false,
    corsHandler: false,
    headers: {
      crossOriginEmbedderPolicy: false,   // évite de casser images/polices cross-origin
      xFrameOptions: 'SAMEORIGIN',
      referrerPolicy: 'strict-origin-when-cross-origin',
      strictTransportSecurity: { maxAge: 31536000, includeSubdomains: true },
      permissionsPolicy: { camera: [], microphone: [], geolocation: [] },
      contentSecurityPolicy: {
        'base-uri': ["'self'"],
        'default-src': ["'self'"],
        'connect-src': ["'self'", 'https://challenges.cloudflare.com', 'https://analytics.agoraci.ibrahimafofana.com'],
        'font-src': ["'self'", 'data:', 'https://fonts.gstatic.com'],
        'form-action': ["'self'"],
        'frame-ancestors': ["'self'"],
        'frame-src': ["'self'", 'https://challenges.cloudflare.com'],
        'img-src': ["'self'", 'data:', 'https:'],
        'media-src': ["'self'"],
        'object-src': ["'none'"],
        // nonce + strict-dynamic : les scripts inline de Nuxt reçoivent un nonce → plus de 'unsafe-inline'
        'script-src': ["'self'", "'nonce-{{nonce}}'", "'strict-dynamic'"],
        'style-src': ["'self'", "'unsafe-inline'", 'https://fonts.googleapis.com'],
        'upgrade-insecure-requests': true,
      },
    },
  },

  // SEO global (sitemap + robots lisent cette config)
  site: {
    url: process.env.NUXT_PUBLIC_SITE_URL || 'http://localhost:3000',
    name: process.env.NUXT_PUBLIC_SITE_NAME || 'Jamakan',
  },

  primevue: {
    options: { theme: { preset: 'Aura' } },
  },

  i18n: {
    defaultLocale: 'fr',
    strategy: 'prefix_except_default',
    vueI18n: './i18n.config.ts',
    locales: [
      { code: 'fr', language: 'fr-CI', name: 'Français' },
      { code: 'en', language: 'en-US', name: 'English' },
    ],
  },

  app: {
    pageTransition: { name: 'page', mode: 'out-in' },
    head: {
      htmlAttrs: { lang: 'fr' },
      titleTemplate: '%s · Jamakan',
      meta: [
        { charset: 'utf-8' },
        { name: 'viewport', content: 'width=device-width, initial-scale=1' },
        { name: 'theme-color', content: '#009E60' },
        // PWA / installation sur écran d'accueil
        { name: 'mobile-web-app-capable', content: 'yes' },
        { name: 'apple-mobile-web-app-capable', content: 'yes' },
        { name: 'apple-mobile-web-app-status-bar-style', content: 'default' },
        { name: 'apple-mobile-web-app-title', content: 'Jamakan' },
      ],
      link: [
        { rel: 'icon', type: 'image/svg+xml', href: '/favicon.svg' },
        { rel: 'manifest', href: '/manifest.webmanifest' },
        { rel: 'apple-touch-icon', href: '/icon.svg' },
      ],
    },
  },
})
