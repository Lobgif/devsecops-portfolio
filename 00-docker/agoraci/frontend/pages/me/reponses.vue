<script setup lang="ts">
useSeoMeta({ title: 'Mes réponses', robots: 'noindex' })
const api = useApi()
const auth = useAuthStore()

const items = ref<any[]>([])
const loaded = ref(false)
onMounted(async () => {
  auth.load()
  if (!auth.isAuthenticated) return navigateTo('/login')
  items.value = await api('/forum/me/posts').catch(() => [])
  loaded.value = true
})
</script>

<template>
  <AppShell>
    <h1 class="font-display text-2xl font-extrabold">Mes réponses</h1>
    <p class="mt-1 text-sm text-slate-500">Les réponses que vous avez apportées à la communauté.</p>

    <div v-if="items.length" class="mt-6 space-y-3">
      <NuxtLink v-for="p in items" :key="p.id" :to="`/discussion/${p.discussion_id}`"
                class="block rounded-2xl border border-slate-200 bg-white p-4 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md">
        <div class="flex items-center justify-between gap-2 text-xs text-slate-400">
          <span class="truncate">Réponse à <b class="font-semibold text-slate-600">{{ p.discussion_title }}</b></span>
          <span class="shrink-0">{{ timeAgo(p.created_at) }}</span>
        </div>
        <p class="mt-1.5 line-clamp-3 text-sm text-slate-700">{{ p.excerpt }}</p>
        <div class="mt-2 flex items-center gap-3 text-xs">
          <span class="inline-flex items-center gap-1 font-semibold"
                :class="p.score > 0 ? 'text-agora-green' : p.score < 0 ? 'text-red-500' : 'text-slate-400'">
            <i class="pi pi-arrow-up" /> {{ p.score }}
          </span>
          <span v-if="p.is_hidden" class="rounded bg-red-50 px-2 py-0.5 text-red-500">Masquée</span>
          <span class="text-agora-orange">Voir la discussion →</span>
        </div>
      </NuxtLink>
    </div>

    <div v-else-if="loaded" class="mt-6 rounded-2xl border border-slate-200 bg-white p-10 text-center text-slate-500">
      Vous n'avez pas encore répondu à une discussion.
      <NuxtLink to="/forums" class="mt-3 inline-block"><span class="btn-primary"><i class="pi pi-comments" /> Aider la communauté</span></NuxtLink>
    </div>
  </AppShell>
</template>
