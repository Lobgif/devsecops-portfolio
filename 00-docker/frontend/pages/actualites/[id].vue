<script setup lang="ts">
const route = useRoute()
const api = useApi()
const { public: pub } = useRuntimeConfig()
const id = route.params.id as string

const { data: a } = await useAsyncData(`article-${id}`, () => api(`/actualites/${id}`).catch(() => null))
useSeoMeta({
  title: () => a.value?.title || 'Actualité',
  description: () => a.value?.summary,
  ogUrl: `${pub.siteUrl}/actualites/${id}`,
})

const analysis = ref('')
const loading = ref(false)
async function analyze() {
  loading.value = true
  try { analysis.value = (await api(`/actualites/${id}/analyze`, { method: 'POST' })).analysis }
  catch { analysis.value = 'Analyse indisponible.' }
  finally { loading.value = false }
}
const fmt = (d: string) => d ? new Date(d).toLocaleDateString('fr-FR', { day: '2-digit', month: 'long', year: 'numeric' }) : ''
</script>

<template>
  <div>
  <section v-if="a" class="mx-auto max-w-3xl px-4 py-10">
    <BackButton to="/actualites" label="Actualités" />
    <span class="chip bg-sky-100 text-sky-700">{{ a.category }}</span>
    <h1 class="mt-2 font-display text-3xl font-bold">{{ a.title }}</h1>
    <p class="mt-1 text-sm text-slate-400"><i class="pi pi-calendar" /> {{ fmt(a.published_at) }} · {{ a.source }}</p>
    <p class="mt-4 text-lg text-slate-700">{{ a.summary }}</p>
    <p class="mt-4 whitespace-pre-line text-slate-600">{{ a.content }}</p>

    <div class="mt-6">
      <button class="btn-primary" :disabled="loading" @click="analyze">
        <i class="pi pi-sparkles" /> {{ loading ? 'Analyse…' : "Analyser avec l'IA" }}
      </button>
    </div>
    <div v-if="analysis" class="card mt-4 border-agora-green/30 bg-agora-green/5">
      <p class="mb-2 font-semibold text-agora-green"><i class="pi pi-sparkles" /> Analyse IA</p>
      <div class="space-y-2 leading-relaxed text-slate-700" v-html="renderMarkdown(analysis)" />
    </div>
  </section>
  <section v-else class="mx-auto max-w-3xl px-4 py-20 text-center text-slate-400">Actualité introuvable.</section>
  </div>
</template>
