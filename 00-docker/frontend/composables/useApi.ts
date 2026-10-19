// Wrapper $fetch — authentification par cookies httpOnly.
// - Client : `credentials: 'include'` envoie les cookies (même origine via Traefik).
// - Serveur (SSR) : on transfère le cookie de la requête entrante vers l'API interne.
// - Sur 401 (token d'accès expiré) : tentative de refresh via le cookie refresh_token,
//   puis réessai unique de la requête → session fluide sans déconnexion visible.
export function useApi() {
  const config = useRuntimeConfig()
  const baseURL = import.meta.server
    ? `${config.apiInternal}${config.public.apiBase}`
    : config.public.apiBase
  const headers = import.meta.server ? useRequestHeaders(['cookie']) : undefined

  const client = $fetch.create({ baseURL, credentials: 'include', headers })

  const api = ((request: any, opts: any = {}) =>
    client(request, opts).catch(async (err: any) => {
      const status = err?.response?.status ?? err?.status
      const url = String(request)
      const isAuthFlow = url.includes('/auth/refresh') || url.includes('/auth/login')
      // Token expiré → on rafraîchit (1 seule fois) puis on rejoue la requête. Client uniquement.
      if (import.meta.client && status === 401 && !opts.__retried && !isAuthFlow) {
        try {
          await client('/auth/refresh', { method: 'POST' })
        } catch {
          throw err // refresh impossible → réellement déconnecté
        }
        return client(request, { ...opts, __retried: true })
      }
      throw err
    })) as typeof client

  return api
}
