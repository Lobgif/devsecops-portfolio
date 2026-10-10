<script setup lang="ts">
definePageMeta({ layout: 'admin' })
useSeoMeta({ title: 'Admin — Métriques', robots: 'noindex' })
const api = useApi()
const { data: m, refresh, pending } = await useAsyncData('admin-metrics', () => api('/admin/metrics').catch(() => null))

const trend = computed(() => {
  if (!m.value) return null
  const a = m.value.acquisition.new_7d, b = m.value.acquisition.new_prev_7d
  if (!b) return a > 0 ? '↗︎ nouveau' : '—'
  const d = Math.round((100 * (a - b)) / b)
  return `${d >= 0 ? '↗︎ +' : '↘︎ '}${d}% vs 7j préc.`
})

// Définitions + calcul de chaque métrique (affichées en info-bulle)
const D = {
  acquisition: "ACQUISITION : est-ce que des gens arrivent ?\n• Total inscrits = COUNT(comptes).\n• Nouveaux 7j = COUNT(comptes créés ces 7 derniers jours).\n• Tendance = (nouveaux 7j − 7j précédents) / 7j précédents.",
  activation: "ACTIVATION : est-ce qu'ils passent à l'acte (pas juste s'inscrire) ?\n• Membres actifs = nb de personnes DISTINCTES ayant créé ≥1 question OU ≥1 réponse (hors IA).\n• Taux = membres actifs ÷ total inscrits × 100.",
  retention: "RÉTENTION : est-ce qu'ils REVIENNENT ?\n• Actifs 7j / 30j = nb de contributeurs DISTINCTS ayant posté (question ou réponse) sur les 7 / 30 derniers jours.",
  engagement: "ENGAGEMENT : combien d'activité réelle ?\n• Questions = COUNT(discussions).\n• Réponses = COUNT(réponses humaines, hors IA).\n• (7j) = créées sur les 7 derniers jours.",
  quality: "QUALITÉ : la plateforme répond-elle vraiment ?\n• Taux = questions ayant ≥1 réponse jugée BONNE (score net > 0, càd plus de 👍 que de 👎) ÷ total questions × 100.",
  ai: "NANAN (IA) :\n• Réponses générées = COUNT(réponses is_ai).\n• Couverture = questions où Nanan a été sollicité ÷ total questions × 100.",
}
</script>

<template>
  <div>
    <div class="flex items-center justify-between">
      <h1 class="font-display text-2xl font-bold">Métriques (AARRR)</h1>
      <button class="btn-ghost border text-sm" :disabled="pending" @click="refresh()">
        <i :class="['pi', pending ? 'pi-spin pi-spinner' : 'pi-refresh']" /> Rafraîchir
      </button>
    </div>
    <p class="mt-1 text-sm text-slate-500">
      Les métriques qui comptent vraiment (Lean Startup) — pas les chiffres illusoires.
      <span class="text-slate-400">Survolez l'icône <i class="pi pi-info-circle" /> pour la définition et le calcul.</span>
    </p>

    <div v-if="m" class="mt-6 space-y-6">
      <!-- Acquisition -->
      <section class="card">
        <h2 class="font-display text-lg font-bold text-agora-orange">
          <i class="pi pi-user-plus" /> Acquisition
          <i class="pi pi-info-circle ml-1 cursor-help text-sm text-slate-400" :title="D.acquisition" />
        </h2>
        <div class="mt-3 grid gap-4 sm:grid-cols-3">
          <div><p class="text-2xl font-bold">{{ m.acquisition.total_users }}</p><p class="text-xs text-slate-500">inscrits (total)</p></div>
          <div><p class="text-2xl font-bold">{{ m.acquisition.new_7d }}</p><p class="text-xs text-slate-500">nouveaux (7 jours)</p></div>
          <div><p class="text-sm font-semibold" :class="String(trend).includes('↘') ? 'text-red-500' : 'text-agora-green'">{{ trend }}</p><p class="text-xs text-slate-500">tendance</p></div>
        </div>
      </section>

      <!-- Activation -->
      <section class="card">
        <h2 class="font-display text-lg font-bold text-agora-orange">
          <i class="pi pi-bolt" /> Activation
          <i class="pi pi-info-circle ml-1 cursor-help text-sm text-slate-400" :title="D.activation" />
        </h2>
        <div class="mt-3 grid gap-4 sm:grid-cols-2">
          <div><p class="text-2xl font-bold">{{ m.activation.activation_rate_pct }}%</p><p class="text-xs text-slate-500">taux d'activation</p></div>
          <div><p class="text-2xl font-bold">{{ m.activation.activated_users }}</p><p class="text-xs text-slate-500">membres actifs (ont contribué)</p></div>
        </div>
      </section>

      <!-- Rétention -->
      <section class="card">
        <h2 class="font-display text-lg font-bold text-agora-orange">
          <i class="pi pi-history" /> Rétention
          <i class="pi pi-info-circle ml-1 cursor-help text-sm text-slate-400" :title="D.retention" />
        </h2>
        <div class="mt-3 grid gap-4 sm:grid-cols-2">
          <div><p class="text-2xl font-bold">{{ m.retention.active_7d }}</p><p class="text-xs text-slate-500">actifs (7 jours)</p></div>
          <div><p class="text-2xl font-bold">{{ m.retention.active_30d }}</p><p class="text-xs text-slate-500">actifs (30 jours)</p></div>
        </div>
      </section>

      <!-- Engagement -->
      <section class="card">
        <h2 class="font-display text-lg font-bold text-agora-orange">
          <i class="pi pi-comments" /> Engagement
          <i class="pi pi-info-circle ml-1 cursor-help text-sm text-slate-400" :title="D.engagement" />
        </h2>
        <div class="mt-3 grid gap-4 sm:grid-cols-4">
          <div><p class="text-2xl font-bold">{{ m.engagement.questions }}</p><p class="text-xs text-slate-500">questions</p></div>
          <div><p class="text-2xl font-bold">{{ m.engagement.answers }}</p><p class="text-xs text-slate-500">réponses</p></div>
          <div><p class="text-2xl font-bold">{{ m.engagement.questions_7d }}</p><p class="text-xs text-slate-500">questions (7j)</p></div>
          <div><p class="text-2xl font-bold">{{ m.engagement.answers_7d }}</p><p class="text-xs text-slate-500">réponses (7j)</p></div>
        </div>
      </section>

      <!-- Qualité + IA -->
      <div class="grid gap-6 sm:grid-cols-2">
        <section class="card">
          <h2 class="font-display text-lg font-bold text-agora-green">
            <i class="pi pi-check-circle" /> Qualité
            <i class="pi pi-info-circle ml-1 cursor-help text-sm text-slate-400" :title="D.quality" />
          </h2>
          <p class="mt-3 text-3xl font-bold">{{ m.quality.answered_rate_pct }}%</p>
          <p class="text-xs text-slate-500">{{ m.quality.questions_with_good_answer }} questions bien répondues</p>
        </section>
        <section class="card">
          <h2 class="font-display text-lg font-bold text-agora-green">
            <i class="pi pi-sparkles" /> Nanan (IA)
            <i class="pi pi-info-circle ml-1 cursor-help text-sm text-slate-400" :title="D.ai" />
          </h2>
          <div class="mt-3 grid grid-cols-2 gap-4">
            <div><p class="text-2xl font-bold">{{ m.ai.nanan_answers }}</p><p class="text-xs text-slate-500">réponses générées</p></div>
            <div><p class="text-2xl font-bold">{{ m.ai.coverage_pct }}%</p><p class="text-xs text-slate-500">questions où Nanan a aidé</p></div>
          </div>
        </section>
      </div>
    </div>
    <p v-else class="mt-6 text-slate-500">Métriques indisponibles.</p>
  </div>
</template>
