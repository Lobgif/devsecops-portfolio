// Protège l'interface super-admin (chemin configurable via NUXT_PUBLIC_ADMIN_PATH).
// Global + exécuté avant le rendu (SSR & client) → pas d'effet « flash puis disparaît ».
export default defineNuxtRouteMiddleware((to) => {
  const base = `/${useRuntimeConfig().public.adminPath}`
  const isAdminRoute = to.path === base || to.path.startsWith(`${base}/`)
  if (!isAdminRoute) return

  const auth = useAuthStore()
  if (auth.isSuperadmin) return
  // Non connecté → login ; connecté mais pas super-admin → accueil
  return navigateTo(
    auth.isAuthenticated ? '/' : `/login?redirect=${encodeURIComponent(to.fullPath)}`,
  )
})
