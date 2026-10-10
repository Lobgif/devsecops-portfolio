<script setup lang="ts">
const { public: pub } = useRuntimeConfig()
const api = useApi()
useSeoMeta({ title: 'FAQ — questions fréquentes', description: 'Les questions les plus posées par la communauté, par thème.', ogUrl: `${pub.siteUrl}/faq` })

const { data: groups } = await useAsyncData('faq', () => api('/forum/faq').catch(() => []))
</script>

<template>
  <section class="mx-auto max-w-3xl px-4 py-10">
    <BackButton />
    <h1 class="font-display text-3xl font-bold">❓ Questions fréquentes</h1>
    <p class="mt-1 text-slate-500">Les sujets les plus actifs de la communauté, par thème.</p>

    <div v-if="groups?.length" class="mt-6 space-y-6">
      <div v-for="g in groups" :key="g.category">
        <h2 class="mb-2 text-sm font-semibold uppercase tracking-wide text-agora-orange">{{ g.category }}</h2>
        <div class="overflow-hidden rounded-2xl border border-slate-200 bg-white">
          <NuxtLink v-for="q in g.questions" :key="q.id" :to="`/discussion/${q.id}`"
                    class="flex items-center justify-between gap-3 border-b border-slate-50 px-4 py-3 hover:bg-slate-50">
            <span class="text-sm">{{ q.title }}</span>
            <span class="shrink-0 text-xs text-slate-400"><i class="pi pi-comments" /> {{ q.answers }}</span>
          </NuxtLink>
        </div>
      </div>
    </div>
    <p v-else class="mt-10 text-center text-slate-400">Pas encore de questions — lancez la discussion !</p>
  </section>
</template>
