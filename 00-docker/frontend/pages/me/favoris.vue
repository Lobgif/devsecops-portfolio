<script setup lang="ts">
useSeoMeta({ title: 'Favoris', robots: 'noindex' })
const api = useApi()
const auth = useAuthStore()

const data = ref<{ groups: any[]; discussions: any[] }>({ groups: [], discussions: [] })
const loaded = ref(false)
onMounted(async () => {
  auth.load()
  if (!auth.isAuthenticated) return navigateTo('/login')
  data.value = await api('/forum/me/follows').catch(() => ({ groups: [], discussions: [] }))
  loaded.value = true
})
const empty = computed(() => !data.value.groups.length && !data.value.discussions.length)
</script>

<template>
  <AppShell>
    <h1 class="font-display text-2xl font-extrabold">Favoris</h1>
    <p class="mt-1 text-sm text-slate-500">Les groupes et discussions que vous suivez.</p>

    <template v-if="data.groups.length">
      <h2 class="mt-6 font-display text-lg font-bold">Groupes suivis</h2>
      <div class="mt-3 grid gap-4 sm:grid-cols-2">
        <GroupCard v-for="g in data.groups" :key="g.id" :group="g" />
      </div>
    </template>

    <template v-if="data.discussions.length">
      <h2 class="mt-8 font-display text-lg font-bold">Discussions suivies</h2>
      <div class="mt-3 space-y-3">
        <NuxtLink v-for="d in data.discussions" :key="d.id" :to="`/discussion/${d.id}`"
                  class="block rounded-2xl border border-slate-200 bg-white p-4 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md">
          <div class="text-xs font-semibold text-agora-orange">{{ d.group_name }}</div>
          <h3 class="mt-0.5 font-bold leading-snug">{{ d.title }}</h3>
        </NuxtLink>
      </div>
    </template>

    <div v-if="empty && loaded" class="mt-6 rounded-2xl border border-slate-200 bg-white p-10 text-center text-slate-500">
      <i class="pi pi-bookmark text-2xl text-slate-300" />
      <p class="mt-2">Aucun favori pour le moment.</p>
      <p class="mt-1 text-sm">Suivez un groupe ou une discussion pour le retrouver ici.</p>
    </div>
  </AppShell>
</template>
