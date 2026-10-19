<script setup lang="ts">
useSeoMeta({ title: 'Messages', robots: 'noindex' })
const api = useApi()
const auth = useAuthStore()
const convs = ref<any[]>([])

onMounted(async () => {
  auth.load()
  if (!auth.isAuthenticated) return navigateTo('/login')
  await auth.fetchMe(api)
  const list = await api('/messages/conversations').catch(() => [])
  // Récupère le nom de chaque interlocuteur
  convs.value = await Promise.all(list.map(async (c: any) => {
    const peer = await api(`/auth/users/${c.peer_id}`).catch(() => ({ username: 'Utilisateur' }))
    return { ...c, peer }
  }))
})
</script>

<template>
  <section class="mx-auto max-w-2xl px-4 py-10">
    <BackButton />
    <h1 class="font-display text-2xl font-bold">Messages</h1>

    <div v-if="convs.length" class="mt-6 divide-y divide-slate-100 overflow-hidden rounded-2xl border border-slate-200 bg-white">
      <NuxtLink v-for="c in convs" :key="c.id" :to="`/messages/${c.id}`" class="flex items-center gap-3 px-4 py-3 hover:bg-slate-50">
        <span class="grid h-10 w-10 place-items-center rounded-full bg-agora-green font-semibold text-white">
          {{ (c.peer.username || '?').charAt(0).toUpperCase() }}
        </span>
        <span class="min-w-0 flex-1">
          <span class="block truncate font-medium">{{ c.peer.full_name || c.peer.username }}</span>
          <span class="block truncate text-sm text-slate-500">{{ c.last_message || 'Démarrez la conversation' }}</span>
        </span>
        <span v-if="c.unread" class="grid h-5 min-w-5 place-items-center rounded-full bg-red-500 px-1 text-[10px] font-bold text-white">
          {{ c.unread }}
        </span>
      </NuxtLink>
    </div>
    <p v-else class="mt-10 text-center text-slate-400">Aucune conversation. Écrivez à un membre depuis son profil.</p>
  </section>
</template>
