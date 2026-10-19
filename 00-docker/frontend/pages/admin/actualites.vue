<script setup lang="ts">
definePageMeta({ layout: 'admin' })
useSeoMeta({ title: 'Admin — Actualités', robots: 'noindex' })
const api = useApi()

const items = ref<any[]>([])
const cats = ['Nouvelles lois', 'Droits citoyens', 'Justice', 'Élections', 'Social']
const form = reactive({ id: '', title: '', summary: '', content: '', category: cats[0], source: '', published_at: '' })
const editing = computed(() => !!form.id)

async function load() { items.value = (await api('/actualites').catch(() => ({ items: [] }))).items }
onMounted(load)
function reset() { Object.assign(form, { id: '', title: '', summary: '', content: '', category: cats[0], source: '', published_at: '' }) }
async function edit(a: any) { Object.assign(form, await api(`/actualites/${a.id}`)) }

async function save() {
  if (!form.title) return
  const body = { title: form.title, summary: form.summary, content: form.content, category: form.category, source: form.source, published_at: form.published_at || null }
  if (form.id) await api(`/admin/actualites/${form.id}`, { method: 'PUT', body }).catch(() => {})
  else await api('/admin/actualites', { method: 'POST', body }).catch(() => {})
  reset(); await load()
}
async function remove(id: string) {
  if (!confirm('Supprimer cette actualité ?')) return
  await api(`/admin/actualites/${id}`, { method: 'DELETE' }).catch(() => {})
  await load()
}
</script>

<template>
  <div>
    <h1 class="font-display text-2xl font-bold">Actualités ({{ items.length }})</h1>

    <div class="card mt-4">
      <h2 class="font-semibold">{{ editing ? "Modifier l'actualité" : 'Ajouter une actualité' }}</h2>
      <div class="mt-3 grid gap-3 sm:grid-cols-2">
        <input v-model="form.title" placeholder="Titre" class="sm:col-span-2" />
        <select v-model="form.category"><option v-for="c in cats" :key="c">{{ c }}</option></select>
        <input v-model="form.source" placeholder="Source (ex. Journal Officiel CI)" />
        <input v-model="form.published_at" type="date" />
        <textarea v-model="form.summary" rows="2" placeholder="Résumé" class="sm:col-span-2" />
        <textarea v-model="form.content" rows="4" placeholder="Contenu" class="sm:col-span-2" />
      </div>
      <div class="mt-3 flex gap-2">
        <button class="btn-primary" @click="save">{{ editing ? 'Mettre à jour' : 'Publier' }}</button>
        <button v-if="editing" class="btn-ghost" @click="reset">Annuler</button>
      </div>
    </div>

    <div class="mt-4 space-y-2">
      <div v-for="a in items" :key="a.id" class="card flex items-start justify-between gap-3 py-3">
        <div class="min-w-0">
          <p class="font-semibold">{{ a.title }} <span class="chip ml-1 bg-slate-100 text-slate-500">{{ a.category }}</span></p>
          <p class="text-sm text-slate-500">{{ a.summary }}</p>
        </div>
        <div class="flex shrink-0 gap-1">
          <button class="btn-ghost text-xs" @click="edit(a)"><i class="pi pi-pencil" /></button>
          <button class="btn-ghost text-xs text-red-600" @click="remove(a.id)"><i class="pi pi-trash" /></button>
        </div>
      </div>
    </div>
  </div>
</template>
