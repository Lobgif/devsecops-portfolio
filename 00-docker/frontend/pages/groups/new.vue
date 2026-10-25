<script setup lang="ts">
useSeoMeta({ title: 'Proposer un groupe', robots: 'noindex' })
const api = useApi()
const auth = useAuthStore()
const router = useRouter()

onMounted(() => {
  auth.load()
  if (!auth.isAuthenticated) navigateTo('/login')
})

const categories = [
  'Démarches administratives', 'Droit & Justice', 'Santé & Bien-être',
  'Éducation & Formation', 'Emploi & Carrière', 'Business & Entrepreneuriat',
  'Finance & Argent', 'Technologie & Numérique', 'Immobilier & Logement',
  'Politique & Société', 'Mariage & Famille', 'Vie pratique',
]
const form = reactive({ name: '', description: '', motivation: '', category: categories[0], is_private: false })
const error = ref('')
const loading = ref(false)

async function propose() {
  loading.value = true; error.value = ''
  try {
    await api('/forum/group-proposals', { method: 'POST', body: {
      name: form.name.trim(), category: form.category, description: form.description, motivation: form.motivation,
    } })
    router.push('/groups/propositions')
  } catch (e: any) {
    error.value = e?.data?.detail || 'Échec de la proposition'
  } finally { loading.value = false }
}

// Création directe : réservée (super-admin / expert / haute réputation) — l'API contrôle l'accès.
async function createDirect() {
  loading.value = true; error.value = ''
  try {
    await api('/forum/groups', { method: 'POST', body: form })
    router.push('/forums')
  } catch (e: any) {
    error.value = e?.data?.detail || 'Création directe refusée'
  } finally { loading.value = false }
}
</script>

<template>
  <AppShell>
    <!-- Fil d'ariane -->
    <nav class="flex flex-wrap items-center gap-1.5 text-sm text-slate-400">
      <NuxtLink to="/" class="hover:text-agora-orange">Accueil</NuxtLink><i class="pi pi-angle-right text-xs" />
      <NuxtLink to="/forums" class="hover:text-agora-orange">Forums</NuxtLink><i class="pi pi-angle-right text-xs" />
      <span class="font-semibold text-agora-orange">Créer un groupe</span>
    </nav>

    <h1 class="mt-3 font-display text-2xl font-extrabold">Créer un nouveau groupe</h1>
    <p class="mt-1 max-w-xl text-slate-500">Créez un espace de discussion pour connecter des personnes partageant les mêmes intérêts.</p>

    <!-- Note gouvernance -->
    <div class="mt-4 rounded-xl border border-agora-green/30 bg-agora-green/5 px-4 py-3 text-sm text-slate-600">
      <i class="pi pi-info-circle text-agora-green" /> Un groupe est <strong>créé automatiquement</strong> quand votre proposition
      réunit assez de <strong>soutiens</strong> de la communauté. Vous en devenez le fondateur.
    </div>

    <!-- Carte formulaire -->
    <div class="mt-5 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <h2 class="font-display text-lg font-bold">Informations de base</h2>

      <div class="mt-5 space-y-5">
        <!-- Nom -->
        <div>
          <label class="mb-1 block text-sm font-semibold text-slate-600">Nom du groupe <span class="text-red-500">*</span></label>
          <input v-model="form.name" placeholder="Ex : Entrepreneurs Abidjan" maxlength="120" />
          <div class="mt-1 flex justify-between text-xs text-slate-400">
            <span>Choisissez un nom clair et descriptif</span><span>{{ form.name.length }}/120</span>
          </div>
        </div>

        <!-- Catégorie -->
        <div>
          <label class="mb-1 block text-sm font-semibold text-slate-600">Catégorie <span class="text-red-500">*</span></label>
          <select v-model="form.category">
            <option v-for="c in categories" :key="c" :value="c">{{ c }}</option>
          </select>
          <p class="mt-1 text-xs text-slate-400">La thématique qui décrit le mieux votre groupe.</p>
        </div>

        <!-- Description -->
        <div>
          <label class="mb-1 block text-sm font-semibold text-slate-600">Description <span class="text-red-500">*</span></label>
          <textarea v-model="form.description" rows="3" placeholder="Décrivez l'objectif de votre groupe en quelques phrases…" maxlength="2000" />
          <div class="mt-1 flex justify-between text-xs text-slate-400">
            <span>Présentez le but et le fonctionnement du groupe</span><span>{{ form.description.length }}/2000</span>
          </div>
        </div>

        <!-- Motivation -->
        <div>
          <label class="mb-1 block text-sm font-semibold text-slate-600">Motivation</label>
          <textarea v-model="form.motivation" rows="2" placeholder="Pourquoi ce groupe est-il utile pour la communauté ?" maxlength="2000" />
          <p class="mt-1 text-xs text-slate-400">Aide les autres à décider de soutenir votre proposition.</p>
        </div>

        <p v-if="error" class="text-sm text-red-600">{{ error }}</p>
        <div class="flex flex-wrap gap-3">
          <button class="btn-primary" :disabled="loading || form.name.trim().length < 3" @click="propose">
            <i class="pi pi-megaphone" /> {{ loading ? '...' : 'Proposer ce groupe' }}
          </button>
          <NuxtLink to="/groups/propositions" class="btn-outline">Voir les propositions en cours →</NuxtLink>
        </div>
      </div>

      <!-- Création directe : réservée (l'API refuse si non autorisé) -->
      <details v-if="auth.user?.is_superadmin" class="mt-6 border-t pt-4">
        <summary class="cursor-pointer text-sm font-medium text-slate-600">Création directe (réservée)</summary>
        <label class="mt-3 flex items-start gap-3 rounded-xl border border-slate-200 p-3 text-sm">
          <input v-model="form.is_private" type="checkbox" class="mt-0.5 !w-auto" />
          <span><span class="font-medium text-slate-700"><i class="pi pi-lock" /> Groupe privé</span>
            <span class="block text-xs text-slate-500">Masqué de la liste publique, contenu réservé aux membres.</span></span>
        </label>
        <button class="btn-ghost mt-3 w-full border" :disabled="loading" @click="createDirect">Créer directement</button>
      </details>
    </div>
  </AppShell>
</template>
