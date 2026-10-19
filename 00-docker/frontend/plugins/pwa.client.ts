// Enregistre le service worker au chargement pour que l'app soit installable
// (PWA « Ajouter à l'écran d'accueil »). Le même SW gère aussi les Web Push
// (voir PushToggle.vue) — register() est idempotent, aucun conflit.
export default defineNuxtPlugin(() => {
  if (import.meta.server) return
  if (!('serviceWorker' in navigator)) return
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js').catch(() => {
      /* échec silencieux : le site reste pleinement fonctionnel sans PWA */
    })
  })
})
