<script setup lang="ts">
definePageMeta({ layout: 'admin' })
useSeoMeta({ title: 'Admin — Messages', robots: 'noindex' })
const api = useApi()

const items = ref<any[]>([])
const loading = ref(true)
async function load() {
  loading.value = true
  items.value = await api('/admin/contact-messages').catch(() => [])
  loading.value = false
}
onMounted(load)

async function setStatus(m: any, status: string) {
  await api(`/admin/contact-messages/${m.id}`, { method: 'PATCH', body: { status } }).catch(() => {})
  m.status = status
}
async function remove(m: any) {
  if (!confirm('Supprimer ce message ?')) return
  await api(`/admin/contact-messages/${m.id}`, { method: 'DELETE' }).catch(() => {})
  items.value = items.value.filter(x => x.id !== m.id)
}

const STATUS: Record<string, string> = { new: 'bg-agora-orange/10 text-agora-orange', read: 'bg-slate-100 text-slate-500', archived: 'bg-slate-100 text-slate-400' }
const newCount = computed(() => items.value.filter(m => m.status === 'new').length)
</script>

<template>
  <div>
    <h1 class="font-display text-2xl font-bold">Messages de contact</h1>
    <p class="mt-1 text-slate-500">{{ items.length }} message(s) · <span class="font-semibold text-agora-orange">{{ newCount }} nouveau(x)</span></p>

    <div v-if="loading" class="mt-6 text-slate-400">Chargement…</div>
    <div v-else-if="items.length" class="mt-6 space-y-3">
      <div v-for="m in items" :key="m.id" class="card">
        <div class="flex flex-wrap items-start justify-between gap-2">
          <div>
            <p class="font-bold">{{ m.subject || '(sans sujet)' }}</p>
            <p class="text-sm text-slate-500">
              {{ m.name || 'Anonyme' }} · <a :href="`mailto:${m.email}`" class="text-agora-orange hover:underline">{{ m.email }}</a>
              · {{ timeAgo(m.created_at) }}
            </p>
          </div>
          <span class="chip" :class="STATUS[m.status]">{{ m.status }}</span>
        </div>
        <p class="mt-3 whitespace-pre-line text-slate-700">{{ m.message }}</p>
        <div class="mt-3 flex flex-wrap gap-2 text-sm">
          <a :href="`mailto:${m.email}?subject=Re: ${encodeURIComponent(m.subject || '')}`" class="btn-ghost border"><i class="pi pi-reply" /> Répondre</a>
          <button v-if="m.status !== 'read'" class="btn-ghost border" @click="setStatus(m, 'read')"><i class="pi pi-check" /> Marquer lu</button>
          <button v-if="m.status !== 'archived'" class="btn-ghost border" @click="setStatus(m, 'archived')"><i class="pi pi-inbox" /> Archiver</button>
          <button class="btn-ghost border text-red-600" @click="remove(m)"><i class="pi pi-trash" /> Supprimer</button>
        </div>
      </div>
    </div>
    <div v-else class="mt-6 rounded-2xl border border-slate-200 bg-white p-10 text-center text-slate-500">Aucun message pour le moment.</div>
  </div>
</template>
