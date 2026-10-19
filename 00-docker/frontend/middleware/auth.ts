// Protège les pages réservées aux membres connectés.
// L'état est déjà résolu par le plugin auth (SSR + client) avant l'exécution du middleware.
export default defineNuxtRouteMiddleware((to) => {
  const auth = useAuthStore()
  if (!auth.isAuthenticated) {
    return navigateTo(`/login?redirect=${encodeURIComponent(to.fullPath)}`)
  }
})
