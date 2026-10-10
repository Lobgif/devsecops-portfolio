// Générateurs côté client : mot de passe fort, passphrase mémorisable, pseudo.
const UPPER = 'ABCDEFGHJKLMNPQRSTUVWXYZ'
const LOWER = 'abcdefghijkmnpqrstuvwxyz'
const DIGITS = '23456789'
const SYMBOLS = '!@#$%&*?-_'

const WORDS = [
  'tigre', 'soleil', 'orage', 'fleur', 'monde', 'rivage', 'savane', 'bambou',
  'comete', 'pixel', 'nuage', 'forge', 'atlas', 'echo', 'lotus', 'ivoire',
  'baobab', 'delta', 'cobra', 'magma', 'zephyr', 'quartz', 'horizon', 'phenix',
  'nebula', 'saphir', 'onyx', 'vortex', 'galaxie', 'menhir', 'akwaba', 'lagune',
]

function rnd(n: number): number {
  return Math.floor((crypto.getRandomValues(new Uint32Array(1))[0] / 2 ** 32) * n)
}
function pick<T>(arr: T[] | string): any {
  return arr[rnd(arr.length)]
}
function shuffle(str: string): string {
  const a = str.split('')
  for (let i = a.length - 1; i > 0; i--) {
    const j = rnd(i + 1)
    ;[a[i], a[j]] = [a[j], a[i]]
  }
  return a.join('')
}

export function generateStandard(length = 16): string {
  const all = UPPER + LOWER + DIGITS + SYMBOLS
  let out = `${pick(UPPER)}${pick(LOWER)}${pick(DIGITS)}${pick(SYMBOLS)}`
  for (let i = out.length; i < length; i++) out += pick(all)
  return shuffle(out)
}

export function generatePassphrase(words = 4): string {
  const chosen = Array.from({ length: words }, () => {
    const w = pick(WORDS) as string
    return w.charAt(0).toUpperCase() + w.slice(1)
  })
  return `${chosen.join('-')}-${pick(DIGITS)}${pick(DIGITS)}${pick(SYMBOLS)}`
}

export type PasswordMode = 'standard' | 'passphrase'
export function generatePassword(mode: PasswordMode): string {
  return mode === 'passphrase' ? generatePassphrase() : generateStandard()
}

// Pseudo unique-ish (le serveur garantit l'unicité ; ceci propose une base)
export function generateUsername(): string {
  return `${pick(WORDS)}${pick(WORDS)}${pick(DIGITS)}${pick(DIGITS)}`
}
