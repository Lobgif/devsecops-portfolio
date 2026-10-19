<script setup lang="ts">
// Rail de navigation gauche (utilisateur connecté) — fidèle à la maquette.
const { public: pub } = useRuntimeConfig()
const auth = useAuthStore()
const api = useApi()
const route = useRoute()

const links = computed(() => [
  { to: '/', label: 'Tableau de bord', icon: 'pi-home' },
  { to: '/me/discussions', label: 'Mes discussions', icon: 'pi-comments' },
  { to: '/me/reponses', label: 'Mes réponses', icon: 'pi-pencil' },
  { to: '/me/favoris', label: 'Favoris', icon: 'pi-bookmark' },
  { to: '/forums', label: 'Mes groupes', icon: 'pi-users' },
  { to: '/messages', label: 'Messages', icon: 'pi-envelope' },
  { to: '/notifications', label: 'Notifications', icon: 'pi-bell' },
  ...(auth.isSuperadmin ? [{ to: `/${pub.adminPath}`, label: 'Administration', icon: 'pi-shield' }] : []),
  { to: '/profile', label: 'Paramètres', icon: 'pi-cog' },
])
// Exact pour « / » et les préfixes /me/* (sinon /me/discussions activerait aussi /me/reponses via startsWith).
const isActive = (to: string) => (to === '/' ? route.path === '/' : route.path === to || route.path.startsWith(to + '/'))
const initial = computed(() => (auth.user?.username || '?').charAt(0).toUpperCase())

// Mes groupes (filtre my_role) + mes stats de contribution — vraies données.
const { data: myGroups } = useAsyncData('sidebar-my-groups', async () => {
  const all = await api('/forum/groups').catch(() => [])
  return (all as any[]).filter(g => g.my_role)
}, { default: () => [] })

const { data: me } = useAsyncData('sidebar-me', () =>
  auth.user?.username ? api(`/auth/users/${auth.user.username}`).catch(() => null) : Promise.resolve(null))
</script>

<template>
  <aside class="hidden w-60 shrink-0 flex-col gap-4 lg:flex">
    <div class="sticky top-[88px] flex flex-col gap-4">
      <!-- Carte profil + nav -->
      <div class="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
        <NuxtLink to="/profile" class="flex items-center gap-3 border-b border-slate-100 p-4 transition hover:bg-slate-50">
          <img v-if="auth.user?.avatar_url" :src="auth.user.avatar_url" class="h-11 w-11 rounded-full object-cover" />
          <span v-else class="grid h-11 w-11 place-items-center rounded-full bg-agora-green font-bold text-white">{{ initial }}</span>
          <div class="min-w-0">
            <p class="truncate font-bold">{{ displayName(auth.user) || auth.user?.username }}</p>
            <p class="truncate text-xs text-slate-500">{{ me?.contribution?.tier || 'Nouveau membre' }}</p>
          </div>
        </NuxtLink>
        <nav class="p-2">
          <NuxtLink v-for="l in links" :key="l.to" :to="l.to"
                    class="flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition"
                    :class="isActive(l.to)
                      ? 'bg-[#fff4e8] font-semibold text-agora-orange shadow-[inset_0_0_0_1px_#ffe0c0]'
                      : 'text-slate-600 hover:bg-slate-100'">
            <i :class="['pi', l.icon, 'w-4 text-center', isActive(l.to) ? 'text-agora-orange' : 'text-slate-400']" />
            {{ l.label }}
          </NuxtLink>
        </nav>
      </div>

      <!-- Vos groupes -->
      <div v-if="myGroups?.length" class="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
        <p class="mb-2.5 text-[11px] font-bold uppercase tracking-wide text-slate-400">Vos groupes</p>
        <ul class="space-y-0.5">
          <li v-for="g in myGroups.slice(0, 5)" :key="g.id">
            <NuxtLink :to="`/groups/${g.id}`" class="flex items-center gap-2.5 rounded-lg px-1 py-1.5 text-sm font-medium text-slate-600 hover:text-agora-ink">
              <span class="h-1.5 w-1.5 shrink-0 rounded-full" :class="categoryStyle(g.category).dot" />
              <span class="truncate">{{ g.name }}</span>
            </NuxtLink>
          </li>
        </ul>
        <NuxtLink to="/forums" class="mt-2 flex items-center gap-1.5 text-[13px] font-semibold text-agora-orange">
          <i class="pi pi-plus text-xs" /> Voir tous mes groupes
        </NuxtLink>
      </div>

      <!-- Votre niveau -->
      <LevelCard :contribution="me?.contribution" />
    </div>
  </aside>
</template>
