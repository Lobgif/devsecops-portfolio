<script setup lang="ts">
const { public: pub } = useRuntimeConfig()
const api = useApi()
useSeoMeta({ title: "Conditions générales d'utilisation", ogUrl: `${pub.siteUrl}/cgu` })
const { data: s } = await useAsyncData('legal-cgu', () => api('/settings/legal').catch(() => ({})))
</script>

<template>
  <section class="mx-auto max-w-3xl px-4 py-10">
    <BackButton />
    <div class="card mt-2 space-y-2 leading-relaxed text-slate-700" v-html="renderMarkdown(s?.legal_cgu || 'Conditions à venir.')" />
  </section>
</template>
