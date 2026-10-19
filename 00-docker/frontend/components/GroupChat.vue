<script setup lang="ts">
// Chat temps réel d'un groupe via WebSocket (backend /ws/{room}, relais Redis).
const props = defineProps<{ groupId: string }>()
const auth = useAuthStore()

const messages = ref<{ user: string; text: string }[]>([])
const draft = ref('')
const connected = ref(false)
let ws: WebSocket | null = null

onMounted(() => {
  const proto = location.protocol === 'https:' ? 'wss' : 'ws'
  ws = new WebSocket(`${proto}://${location.host}/ws/group-${props.groupId}`)
  ws.onopen = () => (connected.value = true)
  ws.onclose = () => (connected.value = false)
  ws.onmessage = (e) => {
    try { messages.value.push(JSON.parse(e.data)) } catch {}
  }
})
onBeforeUnmount(() => ws?.close())

function send() {
  if (!draft.value || !ws || ws.readyState !== WebSocket.OPEN) return
  ws.send(JSON.stringify({ user: auth.user?.username || 'Invité', text: draft.value }))
  draft.value = ''
}
</script>

<template>
  <div class="card">
    <div class="mb-2 flex items-center justify-between">
      <h3 class="font-semibold">Chat du groupe</h3>
      <span class="text-xs" :class="connected ? 'text-agora-green' : 'text-slate-400'">
        <i class="pi pi-circle-fill text-[8px]" /> {{ connected ? 'en ligne' : 'hors ligne' }}
      </span>
    </div>
    <div class="h-56 space-y-2 overflow-y-auto rounded-xl bg-slate-50 p-3 text-sm">
      <p v-if="!messages.length" class="text-slate-400">Aucun message. Lancez la discussion en direct !</p>
      <p v-for="(m, i) in messages" :key="i">
        <span class="font-semibold text-agora-green">{{ m.user }}</span>
        <span class="text-slate-700"> : {{ m.text }}</span>
      </p>
    </div>
    <div v-if="auth.isAuthenticated" class="mt-3 flex gap-2">
      <input v-model="draft" placeholder="Votre message…" class="flex-1 rounded-xl border px-3 py-2"
             @keyup.enter="send" />
      <button class="btn-primary" @click="send">Envoyer</button>
    </div>
    <p v-else class="mt-3 text-sm text-slate-500">
      <NuxtLink to="/login" class="text-agora-green">Connectez-vous</NuxtLink> pour discuter en direct.
    </p>
  </div>
</template>
