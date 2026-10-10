<script setup lang="ts">
// Tableau de bord (utilisateur connecté) : fil « Pour vous / Tendances / Récents » + rail droit.
const api = useApi()

const TABS = [
  { key: 'foryou', label: 'Pour vous' },
  { key: 'trending', label: 'Tendances' },
  { key: 'recent', label: 'Récents' },
]
const tab = ref('foryou')
const feed = ref<any[]>([])
const loading = ref(true)

async function loadFeed() {
  loading.value = true
  feed.value = await api(`/forum/feed?sort=${tab.value}&limit=20`).catch(() => [])
  loading.value = false
}
watch(tab, loadFeed)
onMounted(loadFeed)

// Groupes (pour le rail droit) : mes groupes + forums populaires.
const { data: groups } = useAsyncData('dash-groups', () => api('/forum/groups').catch(() => []), { default: () => [] })
const myGroups = computed(() => (groups.value as any[]).filter(g => g.my_role).slice(0, 4))
const popular = computed(() =>
  [...(groups.value as any[])].sort((a, b) => b.member_count - a.member_count).slice(0, 4))
</script>

<template>
  <AppShell>
    <!-- Onglets du fil -->
    <div class="flex items-center gap-1 rounded-2xl border border-slate-200 bg-white p-1.5 shadow-sm">
      <button v-for="t in TABS" :key="t.key"
              class="flex-1 rounded-xl py-2.5 text-sm font-bold transition"
              :class="tab === t.key ? 'bg-[#fff4e8] text-agora-orange shadow-[inset_0_0_0_1px_#ffe0c0]' : 'text-slate-500 hover:text-agora-ink'"
              @click="tab = t.key">{{ t.label }}</button>
    </div>

    <!-- Fil -->
    <div v-if="loading" class="mt-4 space-y-4">
      <div v-for="i in 3" :key="i" class="h-40 animate-pulse rounded-2xl border border-slate-200 bg-white" />
    </div>
    <div v-else-if="feed.length" class="mt-4 space-y-4">
      <QuestionCard v-for="q in feed" :key="q.id" :item="q" />
    </div>
    <div v-else class="mt-4 rounded-2xl border border-slate-200 bg-white p-10 text-center text-slate-500">
      <i class="pi pi-inbox text-2xl text-slate-300" />
      <p class="mt-2 font-medium">{{ tab === 'foryou' ? 'Rejoignez des groupes pour voir des questions ici.' : 'Aucune discussion pour le moment.' }}</p>
      <NuxtLink to="/forums" class="mt-3 inline-block"><span class="btn-primary"><i class="pi pi-compass" /> Explorer les forums</span></NuxtLink>
    </div>

    <!-- Rail droit -->
    <template #right>
      <NuxtLink to="/forums" class="btn-primary w-full justify-center py-3 text-base shadow-sm">
        <i class="pi pi-question-circle" /> Poser une question
      </NuxtLink>

      <div v-if="myGroups.length" class="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
        <div class="mb-2 flex items-center justify-between">
          <p class="font-bold">Mes groupes</p>
          <NuxtLink to="/forums" class="text-xs font-semibold text-agora-orange">Voir tout</NuxtLink>
        </div>
        <ul class="space-y-1">
          <li v-for="g in myGroups" :key="g.id">
            <NuxtLink :to="`/groups/${g.id}`" class="flex items-center gap-2.5 rounded-xl px-1.5 py-1.5 hover:bg-slate-50">
              <span class="grid h-8 w-8 shrink-0 place-items-center rounded-lg text-[11px] font-bold text-white" :class="categoryStyle(g.category).solid">{{ initials(g.name) }}</span>
              <span class="min-w-0">
                <span class="block truncate text-sm font-semibold">{{ g.name }}</span>
                <span class="block text-xs text-slate-400">{{ g.member_count }} membres · {{ g.discussion_count }} disc.</span>
              </span>
            </NuxtLink>
          </li>
        </ul>
      </div>

      <div v-if="popular.length" class="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
        <p class="mb-2 font-bold">Forums populaires</p>
        <ul class="space-y-2">
          <li v-for="g in popular" :key="g.id" class="flex items-center gap-2.5">
            <span class="grid h-8 w-8 shrink-0 place-items-center rounded-lg text-[11px] font-bold text-white" :class="categoryStyle(g.category).solid">{{ initials(g.name) }}</span>
            <span class="min-w-0 flex-1">
              <NuxtLink :to="`/groups/${g.id}`" class="block truncate text-sm font-semibold hover:text-agora-orange">{{ g.name }}</NuxtLink>
              <span class="block text-xs text-slate-400">{{ g.member_count }} membres</span>
            </span>
            <NuxtLink v-if="!g.my_role" :to="`/groups/${g.id}`" class="shrink-0 text-xs font-bold text-agora-orange">Rejoindre</NuxtLink>
          </li>
        </ul>
      </div>
    </template>
  </AppShell>
</template>
