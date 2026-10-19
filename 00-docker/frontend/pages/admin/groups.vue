<script setup lang="ts">
definePageMeta({ layout: 'admin' })
useSeoMeta({ title: 'Admin — Groupes', robots: 'noindex' })
const api = useApi()
const groups = ref<any[]>([])
async function load() { groups.value = await api('/forum/admin/groups').catch(() => []) }
onMounted(load)
async function toggle(g: any) {
  await api(`/forum/admin/groups/${g.id}/feature?featured=${!g.is_featured}`, { method: 'POST' }).catch(() => {})
  await load()
}
async function scheduleDeletion(g: any) {
  const reason = prompt(`Programmer la suppression de « ${g.name} » (préavis, les membres seront prévenus).\nMotif :`, '')
  if (reason === null) return
  await api(`/forum/admin/groups/${g.id}`, { method: 'DELETE', body: { reason, immediate: false } }).catch((e) => alert(e?.data?.detail || 'Erreur'))
  await load()
}
async function cancelDeletion(g: any) {
  await api(`/forum/admin/groups/${g.id}/cancel-deletion`, { method: 'POST' }).catch(() => {})
  await load()
}
async function deleteNow(g: any) {
  if (!confirm(`⚠️ Supprimer IMMÉDIATEMENT « ${g.name} » (cas grave, sans préavis) ? Irréversible.`)) return
  await api(`/forum/admin/groups/${g.id}`, { method: 'DELETE', body: { immediate: true } }).catch((e) => alert(e?.data?.detail || 'Erreur'))
  await load()
}
</script>

<template>
  <div>
    <h1 class="font-display text-2xl font-bold">Groupes</h1>
    <table class="mt-6 w-full overflow-hidden rounded-2xl border border-slate-200 bg-white text-left text-sm">
      <thead class="bg-slate-50 text-slate-600">
        <tr><th class="p-3">Groupe</th><th class="p-3">Catégorie</th><th class="p-3">Membres</th><th class="p-3">Badges</th><th class="p-3"></th></tr>
      </thead>
      <tbody>
        <tr v-for="g in groups" :key="g.id" class="border-t border-slate-100">
          <td class="p-3 font-semibold">
            <NuxtLink :to="`/groups/${g.id}`" class="text-agora-green hover:underline">
              <i v-if="g.is_private" class="pi pi-lock text-xs text-slate-400" /> {{ g.name }}
            </NuxtLink>
          </td>
          <td class="p-3">{{ g.category }}</td>
          <td class="p-3">{{ g.member_count }}</td>
          <td class="p-3"><span v-for="b in g.badges" :key="b" class="chip mr-1 bg-agora-green/10 text-agora-green">{{ b }}</span></td>
          <td class="p-3 text-right">
            <button class="btn-ghost text-xs" @click="toggle(g)">{{ g.is_featured ? 'Retirer vedette' : 'Mettre en vedette' }}</button>
            <template v-if="g.deletion_at">
              <span class="chip bg-red-50 text-xs text-red-600" :title="new Date(g.deletion_at).toLocaleString('fr-FR')">Suppression programmée</span>
              <button class="btn-ghost text-xs text-agora-green" @click="cancelDeletion(g)">Annuler</button>
              <button class="btn-ghost text-xs text-red-600" @click="deleteNow(g)">Supprimer maintenant</button>
            </template>
            <button v-else class="btn-ghost text-xs text-red-600" @click="scheduleDeletion(g)"><i class="pi pi-trash" /> Programmer la suppression</button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
