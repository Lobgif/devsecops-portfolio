// Rendu Markdown minimal et sûr (échappe le HTML avant tout formatage).
// Gère : gras **/__, italique */_, code `…`, liens, titres #, listes - et 1.
export function renderMarkdown(src: string): string {
  if (!src) return ''

  const esc = (t: string) =>
    t.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')

  const inline = (t: string) =>
    esc(t)
      .replace(/`([^`]+)`/g, '<code class="rounded bg-slate-100 px-1 text-[0.85em]">$1</code>')
      .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
      .replace(/__([^_]+)__/g, '<strong>$1</strong>')
      .replace(/(^|[^*])\*([^*\n]+)\*(?!\*)/g, '$1<em>$2</em>')
      .replace(/\[([^\]]+)\]\((https?:[^)]+)\)/g,
        '<a href="$2" target="_blank" rel="noopener" class="text-agora-green underline">$1</a>')

  const lines = src.replace(/\r\n/g, '\n').split('\n')
  const out: string[] = []
  let list: 'ul' | 'ol' | null = null
  const closeList = () => { if (list) { out.push(`</${list}>`); list = null } }

  for (const raw of lines) {
    const line = raw.trimEnd()
    if (!line.trim()) { closeList(); continue }

    let m: RegExpMatchArray | null
    if (/^([-*_])\1{2,}$/.test(line.trim())) {
      closeList()
      out.push('<hr class="my-3 border-slate-200" />')
    } else if ((m = line.match(/^(#{1,6})\s+(.*)$/))) {
      closeList()
      const cls = m[1].length <= 2 ? 'mt-3 text-base font-bold' : 'mt-2 font-semibold'
      out.push(`<p class="${cls}">${inline(m[2])}</p>`)
    } else if ((m = line.match(/^\s*[-*•]\s+(.*)$/))) {
      if (list !== 'ul') { closeList(); out.push('<ul class="ml-1 list-disc space-y-1 pl-4">'); list = 'ul' }
      out.push(`<li>${inline(m[1])}</li>`)
    } else if ((m = line.match(/^\s*\d+[.)]\s+(.*)$/))) {
      if (list !== 'ol') { closeList(); out.push('<ol class="ml-1 list-decimal space-y-1 pl-4">'); list = 'ol' }
      out.push(`<li>${inline(m[1])}</li>`)
    } else {
      closeList()
      out.push(`<p>${inline(line)}</p>`)
    }
  }
  closeList()
  return out.join('\n')
}
