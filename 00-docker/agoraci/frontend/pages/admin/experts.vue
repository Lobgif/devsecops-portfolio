<script setup lang="ts">
definePageMeta({ layout: 'admin' })
useSeoMeta({ title: 'Admin — Experts', robots: 'noindex' })
const api = useApi()
const apps = ref<any[]>([])
const msg = ref('')

async function load() { apps.value = await api('/auth/admin/expert-applications').catch(() => []) }
onMounted(load)

async function review(userId: string, approve: boolean) {
  const who = apps.value.find((a) => a.user_id === userId)
  if (!confirm(`${approve ? 'Approuver' : 'Rejeter'} la candidature de « ${who?.username} » (${who?.domain}) ?`)) return
  await api(`/auth/admin/experts/${userId}/review`, { method: 'POST', body: { approve } }).catch(() => {})
  msg.value = approve ? 'Expert validé ✅' : 'Candidature rejetée.'
  await load()
}
</script>

<template>
  <div>
    <h1 class="font-display text-2xl font-bold">
      Candidatures d'experts
      <span v-if="apps.length" class="ml-2 rounded-full bg-agora-orange px-2 py-0.5 text-sm text-white">{{ apps.length }}</span>
    </h1>
    <p class="mt-1 text-sm text-slate-500">
      Valide les personnes qui se déclarent expertes dans un domaine. Une réponse d'expert vérifié
      pèse plus dans l'apprentissage de Nanan.
    </p>
    <p v-if="msg" class="mt-3 text-sm text-agora-green">{{ msg }}</p>

    <div v-if="apps.length" class="mt-6 space-y-3">
      <div v-for="a in apps" :key="a.user_id" class="card">
        <div class="flex flex-wrap items-center gap-2">
          <span class="font-semibold">{{ a.username }}</span>
          <span class="chip bg-slate-100 text-slate-600">{{ a.email }}</span>
          <span v-if="a.profession" class="chip bg-sky-50 text-sky-700">{{ a.profession }}</span>
        </div>
        <p class="mt-2 text-sm">
          <span class="font-medium text-agora-orange">Domaine :</span> {{ a.domain }}
        </p>
        <p v-if="a.evidence" class="mt-1 whitespace-pre-wrap text-sm text-slate-700">
          <span class="font-medium">Justificatif :</span> {{ a.evidence }}
        </p>
        <div class="mt-3 flex gap-2">
          <button class="btn-primary" @click="review(a.user_id, true)"><i class="pi pi-check" /> Approuver</button>
          <button class="btn-outline text-red-600" @click="review(a.user_id, false)"><i class="pi pi-times" /> Rejeter</button>
        </div>
      </div>
    </div>
    <p v-else class="mt-6 text-slate-500">Aucune candidature d'expert en attente. 🎉</p>
  </div>
</template>
