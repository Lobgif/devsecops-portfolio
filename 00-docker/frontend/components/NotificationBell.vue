<script setup lang="ts">
const api = useApi()
const auth = useAuthStore()

const open = ref(false)
const unread = ref(0)
const items = ref<any[]>([])
const wrap = ref<HTMLElement | null>(null)
let timer: any = null

async function refreshCount() {
  if (!auth.isAuthenticated) return
  try { unread.value = (await api('/notifications/unread-count')).unread } catch {}
}
async function loadList() {
  try { const d = await api('/notifications'); items.value = d.items; unread.value = d.unread } catch {}
}
async function toggle() {
  open.value = !open.value
  if (open.value) await loadList()
}
async function openItem(n: any) {
  if (!n.is_read) await api(`/notifications/${n.id}/read`, { method: 'POST' }).catch(() => {})
  open.value = false
  await refreshCount()
  if (n.link) navigateTo(n.link)
}
async function markAll() {
  await api('/notifications/read-all', { method: 'POST' }).catch(() => {})
  await loadList()
}
function onDoc(e: MouseEvent) {
  if (wrap.value && !wrap.value.contains(e.target as Node)) open.value = false
}
onMounted(() => {
  refreshCount()
  timer = setInterval(refreshCount, 30000)
  document.addEventListener('click', onDoc)
})
onBeforeUnmount(() => {
  if (timer) clearInterval(timer)
  document.removeEventListener('click', onDoc)
})
</script>

<template>
  <div ref="wrap" class="relative">
    <button class="relative grid h-9 w-9 place-items-center rounded-full hover:bg-slate-100" @click="toggle">
      <i class="pi pi-bell text-lg text-slate-600" />
      <span v-if="unread > 0"
            class="absolute -right-0.5 -top-0.5 grid h-5 min-w-5 place-items-center rounded-full bg-red-500 px-1 text-[10px] font-bold text-white">
        {{ unread > 9 ? '9+' : unread }}
      </span>
    </button>

    <div v-show="open" class="absolute right-0 mt-2 w-80 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-lg">
      <div class="flex items-center justify-between border-b border-slate-100 px-4 py-2">
        <span class="font-semibold">Notifications</span>
        <button class="text-xs text-agora-green hover:underline" @click="markAll">Tout marquer lu</button>
      </div>
      <div class="max-h-80 overflow-y-auto">
        <p v-if="!items.length" class="px-4 py-6 text-center text-sm text-slate-400">Aucune notification.</p>
        <button
          v-for="n in items" :key="n.id"
          class="block w-full border-b border-slate-50 px-4 py-3 text-left hover:bg-slate-50"
          :class="!n.is_read ? 'bg-agora-green/5' : ''"
          @click="openItem(n)"
        >
          <p class="text-sm font-medium" :class="!n.is_read ? 'text-agora-ink' : 'text-slate-500'">{{ n.title }}</p>
          <p class="line-clamp-2 text-xs text-slate-500">{{ n.message }}</p>
        </button>
      </div>
      <NuxtLink to="/notifications" class="block border-t border-slate-100 px-4 py-2 text-center text-sm text-agora-green hover:bg-slate-50" @click="open = false">
        Voir tout
      </NuxtLink>
    </div>
  </div>
</template>
