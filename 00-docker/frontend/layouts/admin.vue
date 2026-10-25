<script setup lang="ts">
const auth = useAuthStore()
const route = useRoute()
const base = `/${useRuntimeConfig().public.adminPath}`
// L'accès est garanti par le middleware global `admin.global.ts` (avant rendu).

const items = [
  { to: base, label: 'Tableau de bord', icon: 'pi-th-large' },
  { to: `${base}/metrics`, label: 'Métriques (AARRR)', icon: 'pi-chart-line' },
  { to: `${base}/statistiques`, label: 'Statistiques', icon: 'pi-chart-bar' },
  { to: `${base}/settings`, label: 'Paramètres du site', icon: 'pi-cog' },
  { to: `${base}/reports`, label: 'Signalements', icon: 'pi-flag' },
  { to: `${base}/messages`, label: 'Messages', icon: 'pi-envelope' },
  { to: `${base}/experts`, label: 'Experts', icon: 'pi-verified' },
  { to: `${base}/groups`, label: 'Groupes', icon: 'pi-comments' },
  { to: `${base}/actualites`, label: 'Actualités', icon: 'pi-megaphone' },
  { to: `${base}/glossary`, label: 'Glossaire', icon: 'pi-bookmark' },
  { to: `${base}/legal`, label: 'Base juridique', icon: 'pi-book' },
  { to: `${base}/users`, label: 'Utilisateurs', icon: 'pi-users' },
]
const active = (to: string) => (to === base ? route.path === base : route.path.startsWith(to))
</script>

<template>
  <div class="min-h-screen bg-slate-50">
    <div class="mx-auto flex max-w-7xl">
      <!-- Sidebar -->
      <aside class="sticky top-0 hidden h-screen w-64 shrink-0 border-r border-slate-200 bg-white p-4 md:block">
        <NuxtLink to="/" class="mb-6 flex items-center gap-2 font-display text-lg font-extrabold">
          <span class="grid h-8 w-8 place-items-center rounded-lg bg-gradient-to-br from-agora-orange to-agora-green text-sm font-bold text-white">J</span>
          <span class="text-agora-green">Jama<span class="text-agora-orange">kan</span></span>
        </NuxtLink>
        <p class="mb-2 px-2 text-xs font-semibold uppercase tracking-wide text-slate-400">Administration</p>
        <nav class="space-y-1">
          <NuxtLink v-for="it in items" :key="it.to" :to="it.to"
                    class="flex items-center gap-2.5 rounded-xl px-3 py-2 text-sm font-medium transition"
                    :class="active(it.to) ? 'bg-agora-orange/10 text-agora-orange' : 'text-slate-600 hover:bg-slate-100'">
            <i :class="['pi', it.icon]" /> {{ it.label }}
          </NuxtLink>
        </nav>
        <NuxtLink to="/" class="mt-6 flex items-center gap-2 px-3 text-sm text-slate-500 hover:text-agora-green">
          <i class="pi pi-arrow-left" /> Retour au site
        </NuxtLink>
      </aside>

      <!-- Contenu -->
      <main class="min-w-0 flex-1 p-4 md:p-8">
        <!-- Nav mobile -->
        <div class="mb-4 flex gap-2 overflow-x-auto md:hidden">
          <NuxtLink v-for="it in items" :key="it.to" :to="it.to"
                    class="chip whitespace-nowrap border"
                    :class="active(it.to) ? 'border-agora-orange text-agora-orange' : 'border-slate-200 text-slate-500'">
            {{ it.label }}
          </NuxtLink>
        </div>
        <slot />
      </main>
    </div>
  </div>
</template>
