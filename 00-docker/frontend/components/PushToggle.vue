<script setup lang="ts">
const api = useApi()
const state = ref<'idle' | 'on' | 'unsupported' | 'denied' | 'loading'>('idle')

function urlB64ToUint8(base64: string) {
  const pad = '='.repeat((4 - (base64.length % 4)) % 4)
  const b64 = (base64 + pad).replace(/-/g, '+').replace(/_/g, '/')
  const raw = atob(b64)
  return Uint8Array.from([...raw].map((c) => c.charCodeAt(0)))
}

onMounted(async () => {
  if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
    state.value = 'unsupported'
    return
  }
  const reg = await navigator.serviceWorker.getRegistration()
  const sub = reg && (await reg.pushManager.getSubscription())
  state.value = sub ? 'on' : 'idle'
})

async function enable() {
  state.value = 'loading'
  try {
    const perm = await Notification.requestPermission()
    if (perm !== 'granted') { state.value = 'denied'; return }
    const reg = await navigator.serviceWorker.register('/sw.js')
    await navigator.serviceWorker.ready
    const { key, enabled } = await api('/notifications/push/public-key')
    if (!enabled || !key) { state.value = 'unsupported'; return }
    const sub = await reg.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: urlB64ToUint8(key),
    })
    await api('/notifications/push/subscribe', { method: 'POST', body: sub.toJSON() })
    state.value = 'on'
  } catch (e) {
    state.value = 'idle'
  }
}
</script>

<template>
  <button
    v-if="state !== 'on' && state !== 'unsupported'"
    class="btn-ghost border" :disabled="state === 'loading'" @click="enable"
  >
    <i class="pi pi-bell" />
    {{ state === 'denied' ? 'Notifications bloquées (navigateur)' : 'Activer les notifications push' }}
  </button>
  <span v-else-if="state === 'on'" class="text-sm text-agora-green"><i class="pi pi-check-circle" /> Push activé</span>
</template>
