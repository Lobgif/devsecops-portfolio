<script setup lang="ts">
const { public: pub } = useRuntimeConfig()
const api = useApi()
useSeoMeta({ title: 'Glossaire juridique', description: 'Les termes du droit ivoirien expliqués simplement.', ogUrl: `${pub.siteUrl}/glossaire` })

const { data } = await useAsyncData('glossary', () => api('/glossary').catch(() => ({ items: [], categories: [] })))
const categories = computed(() => ['Tous', ...(data.value?.categories || [])])
const cat = ref('Tous')
const q = ref('')
const expanded = ref<Record<string, string>>({})
const loading = ref<string | null>(null)

const filtered = computed(() => (data.value?.items || []).filter((t: any) =>
  (cat.value === 'Tous' || t.category === cat.value) &&
  (!q.value || t.term.toLowerCase().includes(q.value.toLowerCase())),
))

async function enrich(t: any) {
  if (expanded.value[t.id]) { delete expanded.value[t.id]; return }
  loading.value = t.id
  try {
    const r = await api('/rag/ask', { method: 'POST', body: { question: `Explique en détail le terme juridique ivoirien : ${t.term}`, mode: 'legal' } })
    expanded.value[t.id] = r.answer
  } catch { expanded.value[t.id] = "Enrichissement indisponible." }
  finally { loading.value = null }
}
</script>

<template>
  <section class="mx-auto max-w-3xl px-4 py-10">
    <h1 class="font-display text-3xl font-bold">📖 Glossaire juridique</h1>
    <p class="mt-1 text-slate-500">Les termes du droit ivoirien expliqués simplement. Cliquez « Approfondir avec l'IA ».</p>

    <input v-model="q" placeholder="Rechercher un terme…" class="mt-6" />
    <div class="mt-3 flex flex-wrap gap-2">
      <button v-for="c in categories" :key="c" class="chip border"
              :class="cat === c ? 'border-agora-orange bg-agora-orange/10 text-agora-orange' : 'border-slate-200 text-slate-500'"
              @click="cat = c">{{ c }}</button>
    </div>

    <div class="mt-6 space-y-3">
      <div v-for="t in filtered" :key="t.id" class="card">
        <div class="flex items-center justify-between gap-2">
          <h2 class="font-semibold">{{ t.term }}</h2>
          <span class="chip bg-slate-100 text-slate-500">{{ t.category }}</span>
        </div>
        <p class="mt-1 text-sm text-slate-600">{{ t.definition }}</p>
        <button class="btn-ghost mt-2 text-xs" :disabled="loading === t.id" @click="enrich(t)">
          <i class="pi pi-sparkles" /> {{ loading === t.id ? 'Analyse…' : (expanded[t.id] ? 'Masquer' : 'Approfondir avec l\'IA') }}
        </button>
        <p v-if="expanded[t.id]" class="mt-2 whitespace-pre-line border-t border-slate-100 pt-2 text-sm text-slate-700">{{ expanded[t.id] }}</p>
      </div>
      <p v-if="!filtered.length" class="text-center text-slate-400">Aucun terme trouvé.</p>
    </div>
  </section>
</template>
