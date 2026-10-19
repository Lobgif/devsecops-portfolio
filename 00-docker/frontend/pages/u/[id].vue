<script setup lang="ts">
const route = useRoute()
const api = useApi()
const auth = useAuthStore()
const id = route.params.id as string

const { data: profile } = await useAsyncData(`user-${id}`, () => api(`/auth/users/${id}`).catch(() => null))
useSeoMeta({ title: () => (profile.value ? `@${profile.value.username}` : 'Profil'), robots: 'noindex' })

const rep = ref(0)
onMounted(async () => {
  auth.load()
  const r = await api(`/forum/reputation/${id}`).catch(() => ({ points: 0 }))
  rep.value = r.points
})

const c = computed(() => profile.value?.contribution)
const tierBadges = computed(() => (profile.value?.badges || []).filter((b: any) => b.type === 'tier'))

async function message() {
  if (!auth.isAuthenticated) return navigateTo('/login')
  const r = await api('/messages/start', { method: 'POST', body: { peer_id: id } }).catch(() => null)
  if (r) navigateTo(`/messages/${r.conversation_id}`)
}
const isSelf = computed(() => auth.user?.id === (profile.value?.id || id))
</script>

<template>
  <AppShell>
    <template v-if="profile">
      <BackButton />
      <!-- Carte d'en-tête -->
      <div class="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
        <div class="h-24 bg-gradient-to-r from-agora-orange to-agora-green" />
        <div class="px-6 pb-6">
          <div class="-mt-10 flex flex-wrap items-end justify-between gap-4">
            <div class="flex items-end gap-4">
              <img v-if="profile.avatar_url" :src="profile.avatar_url" class="h-20 w-20 rounded-2xl border-4 border-white object-cover shadow" />
              <span v-else class="grid h-20 w-20 place-items-center rounded-2xl border-4 border-white bg-agora-green text-3xl font-bold text-white shadow">
                {{ (profile.username || '?').charAt(0).toUpperCase() }}
              </span>
              <div class="pb-1">
                <h1 class="flex items-center gap-2 font-display text-2xl font-extrabold">
                  {{ profile.display_name || profile.username }}
                  <i v-if="profile.is_expert" class="pi pi-verified text-lg text-agora-green" :title="`Expert vérifié${profile.expert_domain ? ' — ' + profile.expert_domain : ''}`" />
                </h1>
                <p class="text-sm text-slate-500">@{{ profile.username }}<span v-if="profile.profession"> · {{ profile.profession }}</span></p>
              </div>
            </div>
            <button v-if="auth.isAuthenticated && !isSelf" class="btn-primary" @click="message"><i class="pi pi-envelope" /> Message</button>
            <NuxtLink v-else-if="isSelf" to="/profile" class="btn-outline"><i class="pi pi-cog" /> Modifier</NuxtLink>
          </div>

          <!-- Badges -->
          <div v-if="profile.badges?.length" class="mt-4 flex flex-wrap gap-2">
            <span v-for="b in profile.badges" :key="b.label" class="chip"
                  :class="b.type === 'expert' ? 'bg-agora-green/10 text-agora-green' : 'bg-agora-orange/10 text-agora-orange'">
              <i :class="['pi', b.type === 'expert' ? 'pi-verified' : 'pi-star']" /> {{ b.label }}
            </span>
          </div>
        </div>
      </div>

      <!-- Statistiques -->
      <div class="mt-4 grid grid-cols-3 gap-4">
        <div class="rounded-2xl border border-slate-200 bg-white p-4 text-center shadow-sm">
          <p class="font-display text-2xl font-extrabold text-agora-orange">{{ c?.answers ?? 0 }}</p>
          <p class="text-xs font-medium text-slate-500">Réponses</p>
        </div>
        <div class="rounded-2xl border border-slate-200 bg-white p-4 text-center shadow-sm">
          <p class="font-display text-2xl font-extrabold text-agora-green">{{ rep }}</p>
          <p class="text-xs font-medium text-slate-500">Points</p>
        </div>
        <div class="rounded-2xl border border-slate-200 bg-white p-4 text-center shadow-sm">
          <p class="font-display text-2xl font-extrabold text-sky-600">{{ Math.round((c?.rate ?? 0) * 100) }}%</p>
          <p class="text-xs font-medium text-slate-500">Bonnes réponses</p>
        </div>
      </div>

      <!-- Palier + progression -->
      <div v-if="c" class="mt-4 rounded-2xl border border-[#ffe6cc] bg-gradient-to-b from-[#fff8f0] to-white p-5 shadow-sm">
        <div class="flex items-center gap-2 font-bold">
          <i class="pi pi-star-fill text-agora-orange" /> {{ c.tier }}
        </div>
        <div class="my-3 h-2 overflow-hidden rounded-full bg-slate-100">
          <span class="block h-full rounded-full bg-gradient-to-r from-agora-orange to-[#ffb15e]" :style="{ width: c.progress + '%' }" />
        </div>
        <p v-if="c.next_tier" class="text-sm text-slate-500">
          Encore <b>{{ c.remaining }}</b> réponse{{ c.remaining > 1 ? 's' : '' }} pour <b>{{ c.next_tier }}</b>.
        </p>
        <p v-else class="text-sm text-agora-green"><i class="pi pi-check-circle" /> Palier maximal atteint.</p>
      </div>

      <!-- Bio -->
      <div v-if="profile.bio" class="mt-4 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <h2 class="mb-1 font-display text-sm font-bold uppercase tracking-wide text-slate-400">À propos</h2>
        <p class="whitespace-pre-line text-slate-700">{{ profile.bio }}</p>
      </div>
    </template>

    <div v-else class="py-20 text-center text-slate-400">Profil introuvable.</div>
  </AppShell>
</template>
