<script setup lang="ts">
const route = useRoute()
const router = useRouter()
const api = useApi()

const q = ref((route.query.q as string) || '')
useSeoMeta({ title: () => (q.value ? `Recherche : ${q.value}` : 'Recherche'), robots: 'noindex' })

const { data: results, refresh, pending } = await useAsyncData(
  'search',
  () => (q.value.trim().length >= 2 ? api('/forum/search', { params: { q: q.value } }) : { groups: [], discussions: [], posts: [] }),
  { watch: [] },
)

function submit() {
  router.replace({ path: '/search', query: { q: q.value } })
  refresh()
}
const total = computed(() =>
  (results.value?.groups?.length || 0) + (results.value?.discussions?.length || 0) + (results.value?.posts?.length || 0),
)
</script>

<template>
  <section class="mx-auto max-w-3xl px-4 py-10">
    <BackButton />
    <h1 class="font-display text-2xl font-bold">Recherche</h1>
    <div class="mt-4 flex gap-2">
      <input v-model="q" placeholder="Rechercher une question, un groupe…" class="flex-1 rounded-xl border px-4 py-2" @keyup.enter="submit" />
      <button class="btn-primary" @click="submit"><i class="pi pi-search" /> Rechercher</button>
    </div>

    <p v-if="!pending && q.length >= 2" class="mt-4 text-sm text-slate-500">{{ total }} résultat(s) pour « {{ q }} »</p>

    <!-- Groupes -->
    <div v-if="results?.groups?.length" class="mt-6">
      <h2 class="mb-2 font-semibold text-slate-700">Groupes</h2>
      <div class="space-y-2">
        <NuxtLink v-for="g in results.groups" :key="g.id" :to="`/groups/${g.id}`" class="card block hover:shadow-sm">
          <span class="text-xs uppercase text-agora-orange">{{ g.category }}</span>
          <p class="font-semibold">{{ g.name }}</p>
        </NuxtLink>
      </div>
    </div>

    <!-- Discussions -->
    <div v-if="results?.discussions?.length" class="mt-6">
      <h2 class="mb-2 font-semibold text-slate-700">Discussions</h2>
      <div class="space-y-2">
        <NuxtLink v-for="d in results.discussions" :key="d.id" :to="`/discussion/${d.id}`" class="card block hover:shadow-sm">
          <p class="font-semibold">{{ d.title }}</p>
          <p class="line-clamp-1 text-sm text-slate-500">{{ d.excerpt }}</p>
        </NuxtLink>
      </div>
    </div>

    <!-- Réponses -->
    <div v-if="results?.posts?.length" class="mt-6">
      <h2 class="mb-2 font-semibold text-slate-700">Réponses</h2>
      <div class="space-y-2">
        <NuxtLink v-for="p in results.posts" :key="p.id" :to="`/discussion/${p.discussion_id}`" class="card block hover:shadow-sm">
          <span v-if="p.is_ai" class="text-xs font-semibold text-agora-green">IA</span>
          <p class="line-clamp-2 text-sm text-slate-600">{{ p.excerpt }}</p>
        </NuxtLink>
      </div>
    </div>

    <p v-if="!pending && q.length >= 2 && total === 0" class="mt-10 text-center text-slate-400">
      Aucun résultat. Essayez d'autres mots-clés.
    </p>
  </section>
</template>
