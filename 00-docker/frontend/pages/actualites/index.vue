<script setup lang="ts">
const { public: pub } = useRuntimeConfig()
const api = useApi()
useSeoMeta({ title: 'Actualités civiques', description: "Lois, droits et actualités de Côte d'Ivoire.", ogUrl: `${pub.siteUrl}/actualites` })

const { data } = await useAsyncData('articles', () => api('/actualites').catch(() => ({ items: [], categories: [] })))
const categories = computed(() => ['Tout', ...(data.value?.categories || [])])
const cat = ref('Tout')
const q = ref('')
const filtered = computed(() => (data.value?.items || []).filter((a: any) =>
  (cat.value === 'Tout' || a.category === cat.value) &&
  (!q.value || a.title.toLowerCase().includes(q.value.toLowerCase()))))

const ICON: Record<string, string> = {
  'Nouvelles lois': 'pi-book', 'Droits citoyens': 'pi-users', 'Justice': 'pi-briefcase',
  'Élections': 'pi-flag', 'Social': 'pi-heart',
}
const fmt = (d: string) => d ? new Date(d).toLocaleDateString('fr-FR', { day: '2-digit', month: 'short', year: 'numeric' }) : ''
</script>

<template>
  <section class="mx-auto max-w-3xl px-4 py-10">
    <div class="flex items-center gap-3">
      <span class="grid h-14 w-14 place-items-center rounded-2xl bg-gradient-to-br from-sky-500 to-blue-600 text-2xl text-white"><i class="pi pi-megaphone" /></span>
      <div><h1 class="font-display text-3xl font-bold">Actualités civiques</h1><p class="text-sm text-slate-500">Lois, droits et actualités de Côte d'Ivoire</p></div>
    </div>

    <input v-model="q" placeholder="Rechercher une actualité…" class="mt-6" />
    <div class="mt-3 flex flex-wrap gap-2">
      <button v-for="c in categories" :key="c" class="chip border"
              :class="cat === c ? 'border-agora-orange bg-agora-orange/10 text-agora-orange' : 'border-slate-200 text-slate-500'"
              @click="cat = c">{{ c }}</button>
    </div>

    <div class="mt-6 space-y-4">
      <NuxtLink v-for="a in filtered" :key="a.id" :to="`/actualites/${a.id}`" class="card flex gap-4 transition hover:shadow-md">
        <span class="grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-sky-100 text-sky-600"><i :class="['pi', ICON[a.category] || 'pi-file']" /></span>
        <div class="min-w-0 flex-1">
          <div class="flex items-start justify-between gap-2">
            <h2 class="font-semibold">{{ a.title }}</h2>
            <span class="chip shrink-0 border border-slate-200 text-slate-500">{{ a.category }}</span>
          </div>
          <p class="mt-1 text-sm text-slate-600">{{ a.summary }}</p>
          <div class="mt-2 flex items-center justify-between text-xs text-slate-400">
            <span><i class="pi pi-calendar" /> {{ fmt(a.published_at) }} · {{ a.source }}</span>
            <span class="font-medium text-agora-orange">Lire l'analyse IA →</span>
          </div>
        </div>
      </NuxtLink>
      <p v-if="!filtered.length" class="text-center text-slate-400">Aucune actualité.</p>
    </div>
  </section>
</template>
