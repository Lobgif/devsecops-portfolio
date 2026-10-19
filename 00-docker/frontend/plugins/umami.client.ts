// Injecte le script Umami (analytics respectueux de la vie privée, sans cookies)
// uniquement si les variables sont configurées. Client uniquement.
export default defineNuxtPlugin(() => {
  const { umamiSrc, umamiId } = useRuntimeConfig().public as { umamiSrc?: string; umamiId?: string }
  if (!umamiSrc || !umamiId) return
  useHead({
    script: [{ src: umamiSrc, defer: true, 'data-website-id': umamiId }],
  })
})
