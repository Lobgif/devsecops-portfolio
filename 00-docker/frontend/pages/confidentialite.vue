<script setup lang="ts">
const { public: pub } = useRuntimeConfig()
const api = useApi()
useSeoMeta({ title: 'Politique de confidentialité', ogUrl: `${pub.siteUrl}/confidentialite` })
const { data: s } = await useAsyncData('legal-privacy', () => api('/settings/legal').catch(() => ({})))
</script>

<template>
  <section class="mx-auto max-w-3xl px-4 py-10">
    <BackButton />
    <div class="card mt-2 space-y-2 leading-relaxed text-slate-700" v-html="renderMarkdown(s?.legal_privacy || 'Politique à venir.')" />
  </section>
</template>
