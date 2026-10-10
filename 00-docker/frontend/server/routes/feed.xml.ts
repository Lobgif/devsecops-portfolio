// Flux RSS (feed.xml) généré côté serveur pour le SEO et les agrégateurs.
// Les forums récents sont récupérés depuis forum-service (URL interne).
export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig()
  const siteUrl = config.public.siteUrl
  const siteName = config.public.siteName

  let items: any[] = []
  try {
    items = await $fetch(`${config.apiInternal}${config.public.apiBase}/forum/groups`)
  } catch {
    items = []
  }

  const esc = (s: string) =>
    String(s ?? '').replace(/[<>&'"]/g, (c) =>
      ({ '<': '&lt;', '>': '&gt;', '&': '&amp;', "'": '&apos;', '"': '&quot;' }[c]!),
    )

  const entries = items
    .map(
      (g) => `
    <item>
      <title>${esc(g.name)}</title>
      <link>${siteUrl}/forums</link>
      <guid isPermaLink="false">${esc(g.id)}</guid>
      <description>${esc(g.description)}</description>
    </item>`,
    )
    .join('')

  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>${esc(siteName)} — Forums</title>
    <link>${siteUrl}</link>
    <description>Dernières discussions et forums de la plateforme citoyenne ${esc(siteName)}.</description>
    <language>fr-ci</language>${entries}
  </channel>
</rss>`

  setHeader(event, 'content-type', 'application/rss+xml; charset=utf-8')
  return xml
})
