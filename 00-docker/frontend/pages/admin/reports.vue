<script setup lang="ts">
definePageMeta({ layout: 'admin' })
useSeoMeta({ title: 'Admin — Signalements', robots: 'noindex' })
const api = useApi()
const reports = ref<any[]>([])
async function load() { reports.value = await api('/forum/admin/reports').catch(() => []) }
onMounted(load)
async function resolve(id: string, action: string) {
  await api(`/forum/admin/reports/${id}/resolve`, { method: 'POST', body: { action } }).catch(() => {})
  await load()
}
</script>

<template>
  <div>
    <h1 class="font-display text-2xl font-bold">
      Contenus signalés
      <span v-if="reports.length" class="ml-2 rounded-full bg-red-500 px-2 py-0.5 text-sm text-white">{{ reports.length }}</span>
    </h1>
    <div v-if="reports.length" class="mt-6 space-y-3">
      <div v-for="r in reports" :key="r.id" class="card">
        <p class="text-sm text-slate-700">{{ r.post_excerpt }}</p>
        <div class="mt-3 flex gap-2">
          <button class="btn-outline" @click="resolve(r.id, 'hide')"><i class="pi pi-eye-slash" /> Masquer</button>
          <button class="btn-outline text-red-600" @click="resolve(r.id, 'delete')"><i class="pi pi-trash" /> Supprimer</button>
          <button class="btn-ghost" @click="resolve(r.id, 'dismiss')">Ignorer</button>
        </div>
      </div>
    </div>
    <p v-else class="mt-6 text-slate-500">Aucun contenu signalé. 🎉</p>
  </div>
</template>
