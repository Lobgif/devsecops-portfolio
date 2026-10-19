<script setup lang="ts">
useSeoMeta({ title: 'Propositions de groupes', description: 'Soutenez les groupes proposés par la communauté — ils sont créés quand ils réunissent assez de soutiens.' })
const api = useApi()
const auth = useAuthStore()
const data = ref<any>({ threshold: 30, proposals: [] })
const busy = ref('')

async function load() { data.value = await api('/forum/group-proposals').catch(() => ({ threshold: 30, proposals: [] })) }
onMounted(() => { auth.load(); load() })

async function support(p: any) {
  if (!auth.isAuthenticated) return navigateTo('/login')
  busy.value = p.id
  try {
    const r = await api(`/forum/group-proposals/${p.id}/support`, { method: 'POST' })
    if (r?.created_group_id) {
      await navigateTo(`/groups/${r.created_group_id}`)
      return
    }
    await load()
  } catch (e: any) { alert(e?.data?.detail || 'Erreur') }
  finally { busy.value = '' }
}
</script>

<template>
  <section class="mx-auto max-w-3xl px-4 py-12">
    <div class="flex items-center justify-between">
      <h1 class="font-display text-2xl font-bold">Propositions de groupes</h1>
      <NuxtLink to="/groups/new" class="btn-primary text-sm"><i class="pi pi-plus" /> Proposer</NuxtLink>
    </div>
    <p class="mt-1 text-sm text-slate-500">
      Un groupe est créé automatiquement dès qu'il réunit <strong>{{ data.threshold }} soutiens</strong>.
      Soutenez ceux qui vous intéressent — vous en deviendrez membre fondateur.
    </p>

    <div v-if="data.proposals.length" class="mt-6 space-y-3">
      <div v-for="p in data.proposals" :key="p.id" class="card">
        <div class="flex flex-wrap items-center gap-2">
          <span class="font-semibold">{{ p.name }}</span>
          <span class="chip bg-agora-orange/10 text-agora-orange">{{ p.category }}</span>
        </div>
        <p v-if="p.description" class="mt-1 text-sm text-slate-700">{{ p.description }}</p>
        <p v-if="p.motivation" class="mt-1 text-xs text-slate-500"><i class="pi pi-info-circle" /> {{ p.motivation }}</p>

        <div class="mt-3">
          <div class="h-2 w-full overflow-hidden rounded-full bg-slate-100">
            <div class="h-full rounded-full bg-agora-green transition-all"
                 :style="{ width: Math.min(100, Math.round(100 * p.support_count / data.threshold)) + '%' }" />
          </div>
          <p class="mt-1 text-xs text-slate-500">{{ p.support_count }} / {{ data.threshold }} soutiens</p>
        </div>

        <button class="btn-primary mt-3" :disabled="busy === p.id || p.supported" @click="support(p)">
          <i :class="['pi', p.supported ? 'pi-check' : 'pi-thumbs-up']" />
          {{ p.supported ? 'Déjà soutenu' : (busy === p.id ? '...' : 'Je soutiens') }}
        </button>
      </div>
    </div>
    <div v-else class="mt-6 card text-center text-slate-500">
      Aucune proposition en cours.
      <NuxtLink to="/groups/new" class="text-agora-green hover:underline">Proposez le premier groupe →</NuxtLink>
    </div>
  </section>
</template>
