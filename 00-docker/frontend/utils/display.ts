// Nom d'affichage d'un utilisateur selon sa préférence (défaut : pseudo).
export function displayName(
  u?: { username?: string; full_name?: string | null; display_pref?: string } | null,
): string {
  if (!u) return ''
  if (u.display_pref === 'fullname' && u.full_name) return u.full_name
  if (u.display_pref === 'firstname' && u.full_name) return u.full_name.split(' ')[0]
  return u.username || ''
}
