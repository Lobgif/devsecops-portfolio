<script setup lang="ts">
const { public: pub } = useRuntimeConfig()

useSeoMeta({
  title: 'Forums & Groupes thématiques',
  description: 'Rejoignez les forums Jamakan : emploi, santé, éducation, droit, agriculture et plus encore.',
  ogUrl: `${pub.siteUrl}/forums`,
})

const api = useApi()
const { data: groups } = await useAsyncData('groups', () => api('/forum/groups').catch(() => []), { default: () => [] })

const featured = computed(() => (groups.value || []).filter((g: any) => g.is_featured).slice(0, 3))

const categories = computed(() => ['Tous', ...new Set((groups.value || []).map((g: any) => g.category))])
const filter = ref('Tous')

const CAT_LIMIT = 7
const showAllCats = ref(false)
const visibleCategories = computed(() =>
  showAllCats.value ? categories.value : categories.value.slice(0, CAT_LIMIT))

const q = ref('')
const filtered = computed(() => {
  let list = filter.value === 'Tous' ? (groups.value || []) : (groups.value || []).filter((g: any) => g.category === filter.value)
  const needle = q.value.trim().toLowerCase()
  if (needle) list = list.filter((g: any) => (g.name + ' ' + g.description).toLowerCase().includes(needle))
  return list
})

const PAGE = 8
const limit = ref(PAGE)
watch([filter, q], () => (limit.value = PAGE))
const shown = computed(() => filtered.value.slice(0, limit.value))
</script>

<template>
  <AppShell>
    <!-- En-tête -->
    <div class="flex flex-wrap items-start justify-between gap-3">
      <div>
        <h1 class="font-display text-3xl font-extrabold tracking-tight">Forums &amp; Groupes thématiques</h1>
        <p class="mt-1 max-w-[48ch] text-slate-500">Découvrez et rejoignez des communautés de discussion sur les sujets qui vous concernent.</p>
      </div>
      <div class="flex gap-2">
        <NuxtLink to="/groups/propositions" class="btn-ghost border"><i class="pi pi-megaphone" /> Propositions</NuxtLink>
        <NuxtLink to="/groups/new" class="btn-primary"><i class="pi pi-plus" /> Proposer un groupe</NuxtLink>
      </div>
    </div>

    <!-- Groupes en vedette -->
    <template v-if="featured.length">
      <h2 class="mt-7 font-display text-lg font-extrabold">Groupes en vedette</h2>
      <div class="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <FeaturedGroupCard v-for="g in featured" :key="g.id" :group="g" />
      </div>
    </template>

    <!-- Filtres -->
    <div class="mt-6 flex flex-wrap items-center gap-2.5">
      <button v-for="c in visibleCategories" :key="c"
              class="rounded-full border px-4 py-1.5 text-sm font-semibold transition"
              :class="filter === c ? 'border-[#ffd6ad] bg-[#fff4e8] text-agora-orange' : 'border-slate-200 bg-white text-slate-500 hover:text-agora-ink'"
              @click="filter = c">{{ c }}</button>
      <button v-if="categories.length > CAT_LIMIT"
              class="rounded-full border border-dashed border-slate-300 px-4 py-1.5 text-sm font-medium text-slate-500 hover:text-agora-orange"
              @click="showAllCats = !showAllCats">
        {{ showAllCats ? 'Voir moins' : `+${categories.length - CAT_LIMIT}` }}
      </button>
      <div class="relative ml-auto">
        <i class="pi pi-search absolute left-3 top-1/2 -translate-y-1/2 text-sm text-slate-400" />
        <input v-model="q" placeholder="Rechercher…" class="!w-52 rounded-full !py-2 !pl-9 text-sm" />
      </div>
    </div>

    <!-- Grille -->
    <div v-if="shown.length" class="mt-2 grid gap-4 sm:grid-cols-2">
      <GroupCard v-for="g in shown" :key="g.id" :group="g" />
    </div>

    <div v-if="shown.length < filtered.length" class="mt-6 text-center">
      <button class="btn-outline" @click="limit += PAGE">
        <i class="pi pi-chevron-down" /> Voir plus ({{ filtered.length - shown.length }})
      </button>
    </div>

    <div v-if="!filtered.length" class="mt-6 rounded-2xl border border-slate-200 bg-white p-10 text-center text-slate-500">
      Aucun forum dans cette catégorie pour le moment.
    </div>
  </AppShell>
</template>
