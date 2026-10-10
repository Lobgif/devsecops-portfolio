// Suivi d'erreurs front (Sentry) — actif uniquement si NUXT_PUBLIC_SENTRY_DSN est défini.
// Capture les erreurs JS + Vue avec la page concernée. Client uniquement, inerte sinon.
import * as Sentry from '@sentry/browser'

export default defineNuxtPlugin((nuxtApp) => {
  const { public: pub } = useRuntimeConfig()
  const dsn = (pub.sentryDsn as string) || ''
  if (!dsn) return

  Sentry.init({
    dsn,
    environment: (pub.siteUrl as string)?.includes('localhost') ? 'development' : 'production',
    tracesSampleRate: 0,      // pas de tracing perf par défaut (coût/quota)
    sendDefaultPii: false,    // pas de données personnelles
  })

  // Remonte les erreurs Vue non gérées à Sentry
  nuxtApp.hook('vue:error', (err) => Sentry.captureException(err))
  nuxtApp.hook('app:error', (err) => Sentry.captureException(err))
})
