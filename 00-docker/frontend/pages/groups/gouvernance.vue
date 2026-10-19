<script setup lang="ts">
useSeoMeta({ title: 'Gouvernance du groupe', robots: 'noindex' })
const api = useApi()
const auth = useAuthStore()
const route = useRoute()
const gid = computed(() => String(route.query.g || ''))

const members = ref<any[]>([])
const proposals = ref<any[]>([])
const busy = ref('')

const ACTIONS: Record<string, string> = {
  ban: 'Retrait du membre', hide: 'Masquer le contenu', delete: 'Supprimer le contenu',
  admit: "Admission d'un candidat", promote_mod: 'Élire un modérateur',
}

async function load() {
  if (!gid.value) return
  members.value = await api(`/forum/groups/${gid.value}/members/list`).catch(() => [])
  proposals.value = await api(`/forum/groups/${gid.value}/moderation/proposals`).catch(() => [])
}
onMounted(() => { auth.load(); if (!auth.isAuthenticated) return navigateTo('/login'); load() })

async function proposeAction(m: any, action: 'ban' | 'promote_mod', label: string) {
  if (!confirm(`${label} « ${m.username} » — soumettre au vote du groupe ?`)) return
  busy.value = m.user_id
  try {
    await api(`/forum/groups/${gid.value}/moderation/proposals`, { method: 'POST', body: {
      target_type: 'user', target_id: m.user_id, action,
    } })
    await load()
  } catch (e: any) { alert(e?.data?.detail || 'Erreur') }
  finally { busy.value = '' }
}

async function vote(p: any, value: number) {
  busy.value = p.id
  try {
    await api(`/forum/moderation/proposals/${p.id}/vote`, { method: 'POST', body: { value } })
    await load()
  } catch (e: any) { alert(e?.data?.detail || 'Erreur') }
  finally { busy.value = '' }
}
</script>

<template>
  <section class="mx-auto max-w-3xl px-4 py-12">
    <BackButton />
    <h1 class="font-display text-2xl font-bold">Gouvernance du groupe</h1>
    <p class="mt-1 text-sm text-slate-500">
      Les décisions (retrait d'un membre, modération) se prennent par <strong>vote des membres</strong>.
      Le vote est <strong>pondéré</strong> par la réputation (plafonné) — personne ne décide seul.
    </p>

    <!-- Propositions en cours -->
    <h2 class="mt-8 font-display text-lg font-bold">Propositions au vote</h2>
    <div v-if="proposals.filter(p => p.status === 'open').length" class="mt-3 space-y-3">
      <div v-for="p in proposals.filter(p => p.status === 'open')" :key="p.id" class="card">
        <p class="font-medium">{{ ACTIONS[p.action] || p.action }}</p>
        <p class="mt-1 text-xs text-slate-500">Pour : {{ p.votes_for }} · Contre : {{ p.votes_against }} · seuil net : {{ p.threshold }}</p>
        <div class="mt-3 flex gap-2">
          <button class="btn-primary" :disabled="busy === p.id" @click="vote(p, 1)"><i class="pi pi-thumbs-up" /> Pour</button>
          <button class="btn-ghost border text-red-600" :disabled="busy === p.id" @click="vote(p, -1)"><i class="pi pi-thumbs-down" /> Contre</button>
        </div>
      </div>
    </div>
    <p v-else class="mt-3 text-sm text-slate-500">Aucune proposition en cours.</p>

    <!-- Membres : proposer un retrait -->
    <h2 class="mt-8 font-display text-lg font-bold">Membres</h2>
    <div class="mt-3 space-y-2">
      <div v-for="m in members" :key="m.user_id" class="flex flex-wrap items-center justify-between gap-2 rounded-xl border px-3 py-2">
        <span class="text-sm"><strong>{{ m.username }}</strong> <span class="text-xs text-slate-400">· {{ m.role }}</span></span>
        <div class="flex gap-2">
          <button v-if="m.role === 'member'" class="btn-ghost border text-xs text-agora-green" :disabled="busy === m.user_id" @click="proposeAction(m, 'promote_mod', 'Élire modérateur')">
            <i class="pi pi-star" /> Élire modérateur
          </button>
          <button v-if="m.role !== 'creator'" class="btn-ghost border text-xs text-red-600" :disabled="busy === m.user_id" @click="proposeAction(m, 'ban', 'Retrait de')">
            <i class="pi pi-user-minus" /> Proposer le retrait
          </button>
        </div>
      </div>
    </div>
  </section>
</template>
