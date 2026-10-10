<script setup lang="ts">
useSeoMeta({ title: 'Conversation', robots: 'noindex' })
const route = useRoute()
const api = useApi()
const auth = useAuthStore()
const id = route.params.id as string

const messages = ref<any[]>([])
const peer = ref<any>({ username: '' })
const draft = ref('')
const myId = ref('')
let ws: WebSocket | null = null

onMounted(async () => {
  auth.load()
  if (!auth.isAuthenticated) return navigateTo('/login')
  await auth.fetchMe(api)
  myId.value = auth.user?.id || ''

  const data = await api(`/messages/${id}`).catch(() => null)
  if (!data) return navigateTo('/messages')
  messages.value = data.messages
  peer.value = await api(`/auth/users/${data.peer_id}`).catch(() => ({ username: 'Utilisateur' }))

  // Temps réel
  const proto = location.protocol === 'https:' ? 'wss' : 'ws'
  ws = new WebSocket(`${proto}://${location.host}/ws/dm-${id}`)
  ws.onmessage = (e) => {
    try {
      const m = JSON.parse(e.data)
      if (m.sender_id !== myId.value) { messages.value.push(m); scrollDown() }
    } catch {}
  }
})
onBeforeUnmount(() => ws?.close())

function scrollDown() {
  nextTick(() => {
    const el = document.getElementById('thread')
    if (el) el.scrollTop = el.scrollHeight
  })
}

async function send() {
  if (!draft.value.trim()) return
  const m = await api(`/messages/${id}`, { method: 'POST', body: { body: draft.value } }).catch(() => null)
  if (m) { messages.value.push(m); draft.value = ''; scrollDown() }
}
</script>

<template>
  <section class="mx-auto flex max-w-2xl flex-col px-4 py-6" style="height: calc(100vh - 80px)">
    <NuxtLink to="/messages" class="text-sm text-agora-green">← Messages</NuxtLink>
    <div class="mt-2 flex items-center gap-2">
      <span class="grid h-9 w-9 place-items-center rounded-full bg-agora-green font-semibold text-white">
        {{ (peer.username || '?').charAt(0).toUpperCase() }}
      </span>
      <h1 class="font-display text-lg font-bold">{{ peer.full_name || peer.username }}</h1>
    </div>

    <div id="thread" class="mt-4 flex-1 space-y-2 overflow-y-auto rounded-2xl bg-slate-50 p-4">
      <p v-if="!messages.length" class="text-center text-sm text-slate-400">Aucun message.</p>
      <div v-for="m in messages" :key="m.id" class="flex" :class="m.sender_id === myId ? 'justify-end' : 'justify-start'">
        <span
          class="max-w-[75%] rounded-2xl px-3 py-2 text-sm"
          :class="m.sender_id === myId ? 'bg-agora-green text-white' : 'bg-white border border-slate-200'"
        >{{ m.body }}</span>
      </div>
    </div>

    <div class="mt-3 flex gap-2">
      <input v-model="draft" placeholder="Écrivez un message…" class="flex-1 rounded-xl border px-4 py-2" @keyup.enter="send" />
      <button class="btn-primary" @click="send"><i class="pi pi-send" /></button>
    </div>
  </section>
</template>
