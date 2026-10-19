// Transforme @pseudo en lien vers le profil, en échappant le HTML (sûr) et en
// préservant les retours à la ligne. Pour le contenu utilisateur (posts).
export function linkifyMentions(text: string): string {
  if (!text) return ''
  const esc = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
  return esc
    // Images : syntaxe markdown ![alt](url) (url interne /media ou http)
    .replace(/!\[[^\]]*\]\((\/media\/[^\s)]+|https?:\/\/[^\s)]+)\)/g,
      '<img src="$1" alt="" class="my-2 max-h-80 rounded-lg border border-slate-200" />')
    .replace(/@([A-Za-z0-9_]{3,})/g,
      '<a href="/u/$1" class="font-medium text-agora-green hover:underline">@$1</a>')
    .replace(/\n/g, '<br>')
}
