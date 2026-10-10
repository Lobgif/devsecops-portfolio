// Temps relatif court en français : « il y a 2 h », « il y a 3 j »…
export function timeAgo(date?: string | Date | null): string {
  if (!date) return ''
  const d = typeof date === 'string' ? new Date(date) : date
  const s = Math.floor((Date.now() - d.getTime()) / 1000)
  if (Number.isNaN(s)) return ''
  if (s < 60) return "à l'instant"
  const m = Math.floor(s / 60)
  if (m < 60) return `il y a ${m} min`
  const h = Math.floor(m / 60)
  if (h < 24) return `il y a ${h} h`
  const j = Math.floor(h / 24)
  if (j < 7) return `il y a ${j} j`
  const sem = Math.floor(j / 7)
  if (sem < 5) return `il y a ${sem} sem`
  const mois = Math.floor(j / 30)
  if (mois < 12) return `il y a ${mois} mois`
  return `il y a ${Math.floor(j / 365)} an${j >= 730 ? 's' : ''}`
}

// Initiale(s) d'un nom pour les avatars textuels.
export function initials(name?: string | null): string {
  if (!name) return '?'
  const parts = name.trim().split(/\s+/)
  if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase()
  return name.slice(0, 2).toUpperCase()
}
