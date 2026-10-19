<script setup lang="ts">
useSeoMeta({ title: 'Notifications', robots: 'noindex' })
const api = useApi()
const auth = useAuthStore()
const items = ref<any[]>([])

onMounted(async () => {
  auth.load()
  if (!auth.isAuthenticated) return navigateTo('/login')
  await load()
  await loadPrefs()
})

// Préférences de notification
const showPrefs = ref(false)
const prefs = ref<Record<string, boolean>>({ replies: true, mentions: true, follows: true, messages: true })
const PREF_LABELS: Record<string, string> = {
  replies: 'Réponses à mes questions',
  mentions: 'Mentions (@moi)',
  follows: 'Groupes/discussions que je suis',
  messages: 'Messages privés',
}
async function loadPrefs() { prefs.value = await api('/notifications/preferences').catch(() => prefs.value) }
async function savePrefs() { prefs.value = await api('/notifications/preferences', { method: 'PUT', body: prefs.value }).catch(() => prefs.value) }

const PAGE = 20
const noMore = ref(false)
async function load() {
  noMore.value = false
  const r = await api(`/notifications?limit=${PAGE}&offset=0`).catch(() => ({ items: [] }))
  items.value = r.items
  if (r.items.length < PAGE) noMore.value = true
}
async function loadMore() {
  const r = await api(`/notifications?limit=${PAGE}&offset=${items.value.length}`).catch(() => ({ items: [] }))
  items.value.push(...r.items)
  if (r.items.length < PAGE) noMore.value = true
}
async function open(n: any) {
  if (!n.is_read) await api(`/notifications/${n.id}/read`, { method: 'POST' }).catch(() => {})
  if (n.link) navigateTo(n.link)
  else await load()
}
async function markAll() {
  await api('/notifications/read-all', { method: 'POST' }).catch(() => {})
  await load()
}

const icon = (t: string) =>
  ({ reply: 'pi-comment', flagged: 'pi-flag', moderation: 'pi-shield', welcome: 'pi-sparkles' }[t] || 'pi-bell')
</script>

<template>
  <section class="mx-auto max-w-2xl px-4 py-10">
    <BackButton />
    <div class="flex flex-wrap items-center justify-between gap-2">
      <h1 class="font-display text-2xl font-bold">Notifications</h1>
      <div class="flex items-center gap-2">
        <ClientOnly><PushToggle /></ClientOnly>
        <button class="btn-ghost" @click="showPrefs = !showPrefs"><i class="pi pi-sliders-h" /> Préférences</button>
        <button class="btn-ghost" @click="markAll">Tout marquer lu</button>
      </div>
    </div>

    <!-- Préférences de notification -->
    <div v-if="showPrefs" class="card mt-4">
      <h2 class="font-semibold">Préférences</h2>
      <p class="mt-1 text-sm text-slate-500">Choisis les notifications que tu souhaites recevoir.</p>
      <div class="mt-3 space-y-2">
        <label v-for="(label, key) in PREF_LABELS" :key="key" class="flex items-center gap-3 text-sm">
          <input type="checkbox" v-model="prefs[key]" @change="savePrefs" />
          {{ label }}
        </label>
      </div>
    </div>

    <div v-if="items.length" class="mt-6 space-y-2">
      <button
        v-for="n in items" :key="n.id"
        class="flex w-full items-start gap-3 rounded-2xl border p-4 text-left transition hover:shadow-sm"
        :class="n.is_read ? 'border-slate-200 bg-white' : 'border-agora-green/30 bg-agora-green/5'"
        @click="open(n)"
      >
        <span class="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-slate-100 text-slate-500">
          <i :class="['pi', icon(n.type)]" />
        </span>
        <span class="min-w-0">
          <span class="block font-medium" :class="n.is_read ? 'text-slate-600' : 'text-agora-ink'">{{ n.title }}</span>
          <span class="block text-sm text-slate-500">{{ n.message }}</span>
        </span>
        <span v-if="!n.is_read" class="ml-auto mt-1 h-2 w-2 shrink-0 rounded-full bg-agora-green" />
      </button>
      <div v-if="!noMore" class="text-center">
        <button class="btn-outline" @click="loadMore"><i class="pi pi-chevron-down" /> Voir plus</button>
      </div>
    </div>
    <p v-else class="mt-10 text-center text-slate-400">Aucune notification pour le moment.</p>
  </section>
</template>
