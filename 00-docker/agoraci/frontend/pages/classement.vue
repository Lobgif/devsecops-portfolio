<script setup lang="ts">
const { public: pub } = useRuntimeConfig()
const api = useApi()
useSeoMeta({ title: 'Classement des contributeurs', description: 'Les membres les plus actifs et utiles de la communauté Jamakan.', ogUrl: `${pub.siteUrl}/classement` })

const { data: list } = await useAsyncData('leaderboard', () => api('/community/leaderboard').catch(() => []))
const podium = computed(() => (list.value || []).slice(0, 3))
const rest = computed(() => (list.value || []).slice(3))
const order = [1, 0, 2] // 2e, 1er, 3e pour l'effet podium
const medal = ['🥇', '🥈', '🥉']
const initial = (u: any) => (u.username || '?').charAt(0).toUpperCase()
</script>

<template>
  <section class="mx-auto max-w-3xl px-4 py-10">
    <h1 class="text-center font-display text-3xl font-bold">🏆 Classement</h1>
    <p class="mt-1 text-center text-slate-500">Les contributeurs les plus utiles (points = j'aime reçus sur leurs réponses).</p>

    <!-- Podium -->
    <div v-if="podium.length" class="mt-10 grid grid-cols-3 items-end gap-3">
      <template v-for="i in order" :key="i">
        <div v-if="podium[i]" class="text-center">
          <div class="mx-auto grid place-items-center rounded-full bg-agora-green font-bold text-white"
               :class="i === 0 ? 'h-20 w-20 text-2xl' : 'h-14 w-14 text-lg'">
            {{ initial(podium[i]) }}
          </div>
          <p class="mt-2 truncate text-sm font-semibold">{{ podium[i].username }}</p>
          <p class="text-xs text-slate-500">{{ podium[i].points }} pts</p>
          <div class="mt-2 rounded-t-xl bg-agora-orange/10 pt-3 text-3xl"
               :class="i === 0 ? 'h-24' : i === 1 ? 'h-16' : 'h-12'">{{ medal[podium[i].rank - 1] }}</div>
        </div>
      </template>
    </div>

    <!-- Reste du classement -->
    <div v-if="rest.length" class="mt-8 overflow-hidden rounded-2xl border border-slate-200 bg-white">
      <NuxtLink v-for="u in rest" :key="u.user_id" :to="`/u/${u.user_id}`"
                class="flex items-center gap-3 border-b border-slate-50 px-4 py-3 hover:bg-slate-50">
        <span class="w-6 text-center text-sm font-semibold text-slate-400">{{ u.rank }}</span>
        <span class="grid h-8 w-8 place-items-center rounded-full bg-slate-200 text-sm font-semibold text-slate-600">{{ initial(u) }}</span>
        <span class="flex-1 truncate text-sm">{{ u.full_name || u.username }}</span>
        <span class="text-sm font-semibold text-agora-green">{{ u.points }} pts</span>
      </NuxtLink>
    </div>
    <p v-if="!list?.length" class="mt-10 text-center text-slate-400">Pas encore de classement — votez pour les meilleures réponses !</p>
  </section>
</template>
