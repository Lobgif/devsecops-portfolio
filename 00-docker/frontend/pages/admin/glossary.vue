<script setup lang="ts">
definePageMeta({ layout: 'admin' })
useSeoMeta({ title: 'Admin — Glossaire', robots: 'noindex' })
const api = useApi()

const items = ref<any[]>([])
const form = reactive({ id: '', term: '', category: 'Général', definition: '' })
const editing = computed(() => !!form.id)

async function load() { items.value = (await api('/glossary').catch(() => ({ items: [] }))).items }
onMounted(load)

function reset() { form.id = ''; form.term = ''; form.category = 'Général'; form.definition = '' }
function edit(t: any) { Object.assign(form, t) }

async function save() {
  if (!form.term || !form.definition) return
  const body = { term: form.term, category: form.category, definition: form.definition }
  if (form.id) await api(`/admin/glossary/${form.id}`, { method: 'PUT', body }).catch(() => {})
  else await api('/admin/glossary', { method: 'POST', body }).catch(() => {})
  reset(); await load()
}
async function remove(id: string) {
  if (!confirm('Supprimer ce terme ?')) return
  await api(`/admin/glossary/${id}`, { method: 'DELETE' }).catch(() => {})
  await load()
}
</script>

<template>
  <div>
    <h1 class="font-display text-2xl font-bold">Glossaire ({{ items.length }})</h1>

    <div class="card mt-4">
      <h2 class="font-semibold">{{ editing ? 'Modifier le terme' : 'Ajouter un terme' }}</h2>
      <div class="mt-3 grid gap-3 sm:grid-cols-2">
        <input v-model="form.term" placeholder="Terme" />
        <input v-model="form.category" placeholder="Catégorie" />
        <textarea v-model="form.definition" rows="2" placeholder="Définition" class="sm:col-span-2" />
      </div>
      <div class="mt-3 flex gap-2">
        <button class="btn-primary" @click="save">{{ editing ? 'Mettre à jour' : 'Ajouter' }}</button>
        <button v-if="editing" class="btn-ghost" @click="reset">Annuler</button>
      </div>
    </div>

    <div class="mt-4 space-y-2">
      <div v-for="t in items" :key="t.id" class="card flex items-start justify-between gap-3 py-3">
        <div class="min-w-0">
          <p class="font-semibold">{{ t.term }} <span class="chip ml-1 bg-slate-100 text-slate-500">{{ t.category }}</span></p>
          <p class="text-sm text-slate-500">{{ t.definition }}</p>
        </div>
        <div class="flex shrink-0 gap-1">
          <button class="btn-ghost text-xs" @click="edit(t)"><i class="pi pi-pencil" /></button>
          <button class="btn-ghost text-xs text-red-600" @click="remove(t.id)"><i class="pi pi-trash" /></button>
        </div>
      </div>
    </div>
  </div>
</template>
