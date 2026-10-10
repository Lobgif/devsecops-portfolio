<script setup lang="ts">
useSeoMeta({ title: 'Mes discussions', robots: 'noindex' })
const api = useApi()
const auth = useAuthStore()

const items = ref<any[]>([])
const loaded = ref(false)
onMounted(async () => {
  auth.load()
  if (!auth.isAuthenticated) return navigateTo('/login')
  items.value = await api('/forum/me/discussions').catch(() => [])
  loaded.value = true
})
</script>

<template>
  <AppShell>
    <h1 class="font-display text-2xl font-extrabold">Mes discussions</h1>
    <p class="mt-1 text-sm text-slate-500">Les sujets que vous avez lancés.</p>

    <div v-if="items.length" class="mt-6 space-y-3">
      <NuxtLink v-for="d in items" :key="d.id" :to="`/discussion/${d.id}`"
                class="block rounded-2xl border border-slate-200 bg-white p-4 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md">
        <div class="flex items-center gap-2 text-xs text-slate-400">
          <NuxtLink :to="`/groups/${d.group_id}`" class="font-semibold text-agora-orange hover:underline">{{ d.group_name }}</NuxtLink>
          <span>· {{ timeAgo(d.created_at) }}</span>
        </div>
        <h3 class="mt-1 font-bold leading-snug">{{ d.title }}</h3>
        <p class="mt-1 line-clamp-2 text-sm text-slate-600">{{ d.excerpt }}</p>
      </NuxtLink>
    </div>

    <div v-else-if="loaded" class="mt-6 rounded-2xl border border-slate-200 bg-white p-10 text-center text-slate-500">
      Vous n'avez pas encore lancé de discussion.
      <NuxtLink to="/forums" class="mt-3 inline-block"><span class="btn-primary"><i class="pi pi-comments" /> Explorer les forums</span></NuxtLink>
    </div>
  </AppShell>
</template>
