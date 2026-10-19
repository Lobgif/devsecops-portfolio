// Restaure la session au chargement (SSR + client) via le cookie httpOnly.
export default defineNuxtPlugin(async () => {
  const auth = useAuthStore()
  if (!auth.user) await auth.fetchMe(useApi())
})
