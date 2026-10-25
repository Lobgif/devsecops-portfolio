import { defineStore } from 'pinia'

interface UserProfile {
  id: string
  email: string
  username: string
  full_name?: string | null
  bio?: string | null
  avatar_url?: string | null
  display_pref?: string
  is_verified: boolean
  is_moderator: boolean
  is_superadmin: boolean
}

type Fetcher = (url: string, opts?: any) => Promise<any>

// Auth par cookies httpOnly : le store ne stocke plus aucun token,
// uniquement le profil utilisateur (récupéré via /auth/me, cookie envoyé automatiquement).
export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null as UserProfile | null,
  }),
  getters: {
    isAuthenticated: (s) => !!s.user,
    isSuperadmin: (s) => !!s.user?.is_superadmin,
  },
  actions: {
    // Conservé pour compatibilité (auth par cookie : rien à charger côté client)
    load() {},
    async fetchMe(fetcher: Fetcher) {
      try {
        this.user = await fetcher('/auth/me')
      } catch {
        this.user = null
      }
    },
    async logout(fetcher: Fetcher) {
      try {
        await fetcher('/auth/logout', { method: 'POST' })
      } catch {}
      this.user = null
    },
  },
})
