<script setup lang="ts">
definePageMeta({ layout: 'admin' })
useSeoMeta({ title: 'Admin — Tableau de bord', robots: 'noindex' })
const api = useApi()

const base = `/${useRuntimeConfig().public.adminPath}`
const { data: stats } = await useAsyncData('admin-stats', () => api('/community/stats').catch(() => null))
const reports = ref<any[]>([])
const nanan = ref<{ questions: number; users: number; daily_limit: number } | null>(null)
onMounted(async () => {
  reports.value = await api('/forum/admin/reports').catch(() => [])
  nanan.value = await api('/admin/nanan-usage').catch(() => null)
})

const cards = computed(() => stats.value ? [
  { label: 'Membres', value: stats.value.users, icon: 'pi-users', to: `${base}/users` },
  { label: 'Groupes', value: stats.value.groups, icon: 'pi-comments', to: `${base}/groups` },
  { label: 'Discussions', value: stats.value.discussions, icon: 'pi-question-circle', to: '/forums' },
  { label: 'Réponses', value: stats.value.posts, icon: 'pi-reply', to: '/forums' },
] : [])
</script>

<template>
  <div>
    <h1 class="font-display text-2xl font-bold">Tableau de bord</h1>
    <p class="mt-1 text-slate-500">Vue d'ensemble de la plateforme.</p>

    <div class="mt-6 grid grid-cols-2 gap-4 lg:grid-cols-4">
      <NuxtLink v-for="c in cards" :key="c.label" :to="c.to" class="card transition hover:shadow-md">
        <span class="grid h-10 w-10 place-items-center rounded-xl bg-agora-orange/10 text-agora-orange"><i :class="['pi', c.icon]" /></span>
        <p class="mt-2 text-2xl font-bold">{{ c.value }}</p>
        <p class="text-xs text-slate-500">{{ c.label }}</p>
      </NuxtLink>
    </div>

    <!-- Compteur Nanan du jour (suivi de la consommation IA) -->
    <div v-if="nanan" class="mt-6 rounded-2xl border border-agora-green/30 bg-agora-green/5 p-5">
      <div class="flex items-center gap-2 text-sm font-semibold text-agora-green">
        <i class="pi pi-sparkles" /> Nanan aujourd'hui
      </div>
      <div class="mt-2 flex flex-wrap items-end gap-x-8 gap-y-2">
        <div><span class="font-display text-3xl font-extrabold">{{ nanan.questions }}</span> <span class="text-sm text-slate-500">questions posées</span></div>
        <div><span class="font-display text-3xl font-extrabold">{{ nanan.users }}</span> <span class="text-sm text-slate-500">utilisateurs</span></div>
        <div class="text-sm text-slate-500">Limite : <b>{{ nanan.daily_limit === 0 ? 'illimitée' : nanan.daily_limit + '/jour/pers.' }}</b></div>
      </div>
      <p class="mt-2 text-xs text-slate-400">Suivi en temps réel de la consommation IA. Ajuste la limite dans Paramètres.</p>
    </div>

    <div class="mt-6 grid gap-4 sm:grid-cols-2">
      <NuxtLink :to="`${base}/reports`" class="card flex items-center justify-between transition hover:shadow-md">
        <div><p class="font-semibold">Contenus signalés</p><p class="text-sm text-slate-500">À traiter</p></div>
        <span class="grid h-9 min-w-9 place-items-center rounded-full px-2 text-sm font-bold text-white" :class="reports.length ? 'bg-red-500' : 'bg-slate-300'">{{ reports.length }}</span>
      </NuxtLink>
      <NuxtLink :to="`${base}/settings`" class="card flex items-center justify-between transition hover:shadow-md">
        <div><p class="font-semibold">Paramètres du site</p><p class="text-sm text-slate-500">Email, pied de page, réseaux…</p></div>
        <i class="pi pi-cog text-slate-400" />
      </NuxtLink>
      <NuxtLink :to="`${base}/statistiques`" class="card flex items-center justify-between transition hover:shadow-md">
        <div><p class="font-semibold">Statistiques</p><p class="text-sm text-slate-500">Activité détaillée par catégorie</p></div>
        <i class="pi pi-chart-bar text-slate-400" />
      </NuxtLink>
      <NuxtLink :to="`${base}/messages`" class="card flex items-center justify-between transition hover:shadow-md">
        <div><p class="font-semibold">Messages de contact</p><p class="text-sm text-slate-500">Reçus via le formulaire</p></div>
        <i class="pi pi-envelope text-slate-400" />
      </NuxtLink>
    </div>
  </div>
</template>
