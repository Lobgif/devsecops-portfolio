// Palette visuelle par catégorie de groupe.
// Les classes sont écrites en toutes lettres (pas de concaténation) pour que Tailwind les conserve.
export interface CatStyle {
  grad: string   // dégradé du bandeau de carte (bg-gradient-to-br + from/to)
  solid: string  // aplat (pastille d'icône)
  chip: string   // puce colorée douce
  dot: string    // point coloré (listes)
}

const PALETTES: CatStyle[] = [
  { grad: 'from-[#F77F00] to-[#ff9d3d]', solid: 'bg-agora-orange', chip: 'bg-agora-orange/10 text-agora-orange', dot: 'bg-agora-orange' },
  { grad: 'from-[#4b3fd6] to-[#7b6bf0]', solid: 'bg-indigo-600', chip: 'bg-indigo-50 text-indigo-600', dot: 'bg-indigo-500' },
  { grad: 'from-[#009E60] to-[#2fc783]', solid: 'bg-agora-green', chip: 'bg-agora-green/10 text-agora-green', dot: 'bg-agora-green' },
  { grad: 'from-[#e11d6b] to-[#ff5d94]', solid: 'bg-rose-600', chip: 'bg-rose-50 text-rose-600', dot: 'bg-rose-500' },
  { grad: 'from-[#d97706] to-[#f5b23d]', solid: 'bg-amber-600', chip: 'bg-amber-50 text-amber-700', dot: 'bg-amber-500' },
  { grad: 'from-[#0d9488] to-[#34c8bb]', solid: 'bg-teal-600', chip: 'bg-teal-50 text-teal-600', dot: 'bg-teal-500' },
  { grad: 'from-[#0284c7] to-[#38bdf8]', solid: 'bg-sky-600', chip: 'bg-sky-50 text-sky-600', dot: 'bg-sky-500' },
  { grad: 'from-[#7c3aed] to-[#a78bfa]', solid: 'bg-violet-600', chip: 'bg-violet-50 text-violet-600', dot: 'bg-violet-500' },
]

// Catégories connues → index fixe (couleur stable dans le temps).
const FIXED: Record<string, number> = {
  Droit: 0, 'Droits & Justice': 0, Emploi: 0, 'Emploi & Carrière': 0,
  Politique: 1, Société: 1,
  Entrepreneuriat: 2, Agriculture: 2, Économie: 2,
  Famille: 3, 'Mariage & Famille': 3, Santé: 3,
  'Vie pratique': 4, Héritage: 4, Administratif: 4,
  Éducation: 6, Culture: 7,
}

export function categoryStyle(category?: string | null): CatStyle {
  const c = (category || '').trim()
  if (c in FIXED) return PALETTES[FIXED[c]]
  // Repli déterministe : hash simple du nom → index de palette.
  let h = 0
  for (let i = 0; i < c.length; i++) h = (h * 31 + c.charCodeAt(i)) >>> 0
  return PALETTES[h % PALETTES.length]
}
