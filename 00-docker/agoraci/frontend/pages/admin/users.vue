<script setup lang="ts">
definePageMeta({ layout: 'admin' })
useSeoMeta({ title: 'Admin — Utilisateurs', robots: 'noindex' })
const api = useApi()
const auth = useAuthStore()
const users = ref<any[]>([])
const q = ref('')
async function load() { users.value = await api('/auth/admin/users').catch(() => []) }
onMounted(load)
const filtered = computed(() => users.value.filter((u) =>
  !q.value || (u.username + u.email).toLowerCase().includes(q.value.toLowerCase())))

async function setRole(u: any, flags: any) {
  await api(`/auth/admin/users/${u.id}/role`, { method: 'POST', body: flags }).catch(() => {})
  await load()
}

function isSuspended(u: any) { return u.suspended_until && new Date(u.suspended_until) > new Date() }
const fmt = (d: string) => new Date(d).toLocaleDateString('fr-FR', { day: '2-digit', month: 'short', year: 'numeric' })

async function suspend(u: any) {
  const days = parseInt(window.prompt(`Suspendre @${u.username} pour combien de jours ?`, '7') || '', 10)
  if (!days || days < 1) return
  const reason = window.prompt('Motif (facultatif, visible par l\'utilisateur) :', '') || ''
  await api(`/auth/admin/users/${u.id}/suspend`, { method: 'POST', body: { days, reason } }).catch((e) => alert(e?.data?.detail || 'Erreur'))
  await load()
}
async function unsuspend(u: any) {
  await api(`/auth/admin/users/${u.id}/unsuspend`, { method: 'POST' }).catch(() => {})
  await load()
}
async function remove(u: any) {
  if (!confirm(`Supprimer DÉFINITIVEMENT le compte @${u.username} et tout son contenu ?\nCette action est irréversible.`)) return
  await api(`/auth/admin/users/${u.id}`, { method: 'DELETE' }).catch((e) => alert(e?.data?.detail || 'Erreur'))
  await load()
}
</script>

<template>
  <div>
    <h1 class="font-display text-2xl font-bold">Utilisateurs ({{ users.length }})</h1>
    <p class="mt-1 text-sm text-slate-500">Pouvoirs super-admin : rôles, suspension temporaire, suppression définitive.</p>
    <input v-model="q" placeholder="Rechercher (nom, email)…" class="mt-4 max-w-sm" />

    <div class="mt-4 overflow-x-auto">
    <table class="w-full overflow-hidden rounded-2xl border border-slate-200 bg-white text-left text-sm">
      <thead class="bg-slate-50 text-slate-600">
        <tr><th class="p-3">Utilisateur</th><th class="p-3">Email</th><th class="p-3">Statut</th><th class="p-3 text-right">Actions</th></tr>
      </thead>
      <tbody>
        <tr v-for="u in filtered" :key="u.id" class="border-t border-slate-100" :class="isSuspended(u) ? 'bg-amber-50' : ''">
          <td class="p-3 font-medium">{{ u.full_name || u.username }} <span class="text-slate-400">@{{ u.username }}</span></td>
          <td class="p-3 text-slate-500">{{ u.email }}</td>
          <td class="p-3">
            <span v-if="u.is_superadmin" class="chip bg-agora-orange/10 text-agora-orange">super-admin</span>
            <span v-if="isSuspended(u)" class="chip bg-amber-100 text-amber-700" :title="u.suspended_reason || ''">suspendu → {{ fmt(u.suspended_until) }}</span>
            <span v-else-if="u.is_verified" class="chip bg-emerald-100 text-emerald-700">vérifié</span>
            <span v-else class="chip bg-slate-100 text-slate-500">non vérifié</span>
          </td>
          <td class="p-3">
            <div class="flex flex-wrap justify-end gap-1">
              <button class="btn-ghost text-xs" @click="setRole(u, { is_moderator: !u.is_moderator })">
                {{ u.is_moderator ? '✓ modérateur' : 'modérateur' }}
              </button>
              <template v-if="!u.is_superadmin && u.id !== auth.user?.id">
                <button v-if="isSuspended(u)" class="btn-ghost text-xs text-amber-700" @click="unsuspend(u)">
                  <i class="pi pi-unlock" /> Réactiver
                </button>
                <button v-else class="btn-ghost text-xs text-amber-700" @click="suspend(u)">
                  <i class="pi pi-ban" /> Suspendre
                </button>
                <button class="btn-ghost text-xs text-red-600" @click="remove(u)">
                  <i class="pi pi-trash" /> Supprimer
                </button>
              </template>
            </div>
          </td>
        </tr>
      </tbody>
    </table>
    </div>
  </div>
</template>
