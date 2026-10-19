<script setup lang="ts">
definePageMeta({ middleware: 'auth' })
const { public: pub } = useRuntimeConfig()
const api = useApi()
useSeoMeta({ title: 'Comparateur de lois', description: 'Comparez deux régimes juridiques ivoiriens (ex. mariage coutumier vs civil).', ogUrl: `${pub.siteUrl}/comparateur` })

const presets = [
  ['Mariage coutumier', 'Mariage civil'],
  ['Contrat à durée déterminée (CDD)', 'Contrat à durée indéterminée (CDI)'],
  ['SARL', 'Entreprise individuelle'],
  ['Succession légale', 'Succession testamentaire'],
]
const a = ref('Mariage coutumier')
const b = ref('Mariage civil')
const result = ref('')
const loading = ref(false)

async function compare() {
  if (!a.value.trim() || !b.value.trim()) return
  loading.value = true; result.value = ''
  const question = `Compare de façon structurée et claire « ${a.value} » et « ${b.value} » en droit ivoirien : `
    + `définition, formalités/conditions, droits et obligations, avantages et inconvénients. `
    + `Présente si possible sous forme de points ou de tableau.`
  try { result.value = (await api('/rag/ask', { method: 'POST', body: { question, mode: 'legal' } })).answer }
  catch { result.value = 'Service IA indisponible.' }
  finally { loading.value = false }
}
function usePreset(p: string[]) { a.value = p[0]; b.value = p[1]; compare() }
</script>

<template>
  <section class="mx-auto max-w-3xl px-4 py-10">
    <BackButton />
    <h1 class="font-display text-3xl font-bold">⚖️ Comparateur de lois</h1>
    <p class="mt-1 text-slate-500">Comparez deux régimes juridiques ivoiriens grâce à l'IA.</p>

    <div class="card mt-6 grid items-end gap-3 sm:grid-cols-[1fr_auto_1fr_auto]">
      <label class="text-sm"><span class="mb-1 block font-medium text-slate-600">Option A</span><input v-model="a" /></label>
      <span class="hidden pb-2 text-center font-bold text-slate-400 sm:block">VS</span>
      <label class="text-sm"><span class="mb-1 block font-medium text-slate-600">Option B</span><input v-model="b" /></label>
      <button class="btn-primary" :disabled="loading" @click="compare"><i class="pi pi-sync" /> Comparer</button>
    </div>

    <div class="mt-3 flex flex-wrap gap-2">
      <button v-for="p in presets" :key="p[0]" class="chip border border-slate-200 text-slate-500 hover:border-agora-orange hover:text-agora-orange" @click="usePreset(p)">
        {{ p[0] }} vs {{ p[1] }}
      </button>
    </div>

    <div v-if="loading" class="mt-6 text-slate-400"><i class="pi pi-spin pi-spinner" /> Analyse comparative…</div>
    <div v-if="result" class="card mt-6">
      <div class="space-y-2 leading-relaxed text-slate-700" v-html="renderMarkdown(result)" />
    </div>
  </section>
</template>
