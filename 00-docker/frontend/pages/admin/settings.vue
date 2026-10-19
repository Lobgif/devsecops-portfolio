<script setup lang="ts">
definePageMeta({ layout: 'admin' })
useSeoMeta({ title: 'Admin — Paramètres', robots: 'noindex' })
const api = useApi()

const settings = ref<Record<string, string>>({})
const saved = ref(false)
const FIELDS = [
  { key: 'site_name', label: 'Nom du site' },
  { key: 'contact_email', label: 'Email de contact' },
  { key: 'contact_phone', label: 'Téléphone (Contact / pied de page)' },
  { key: 'contact_location', label: 'Localisation' },
  { key: 'about_show_team', label: '« Notre équipe » sur À propos (1 = visible, 0 = masqué)' },
  { key: 'nanan_daily_limit', label: 'Nanan : questions / utilisateur / jour (0 = illimité)' },
  { key: 'footer_tagline', label: 'Slogan (pied de page)' },
  { key: 'footer_made_with', label: 'Mention pied de page' },
  { key: 'social_facebook', label: 'Facebook (URL)' },
  { key: 'social_x', label: 'X / Twitter (URL)' },
  { key: 'social_instagram', label: 'Instagram (URL)' },
  { key: 'social_linkedin', label: 'LinkedIn (URL)' },
]
const LEGAL = [
  { key: 'legal_cgu', label: "Conditions générales d'utilisation" },
  { key: 'legal_privacy', label: 'Politique de confidentialité' },
  { key: 'legal_mentions', label: 'Mentions légales' },
]
const BADGES = [
  { key: 'badge_window_days', label: "Fenêtre d'activité (jours)" },
  { key: 'badge_alaune_ratio', label: '« À la une » : ratio du score max (0–1)' },
  { key: 'badge_populaire_ratio', label: '« Populaire » : ratio du score max (0–1)' },
  { key: 'badge_vedette_members', label: '« Vedette » : nb de membres min.' },
  { key: 'badge_reactif_posts', label: '« Réactif » : réponses récentes min.' },
  { key: 'badge_actif_days', label: '« Actif » : dernière activité ≤ (jours)' },
  { key: 'badge_nouveau_days', label: '« Nouveau » : créé il y a ≤ (jours)' },
]
onMounted(async () => {
  // /settings n'inclut plus les textes légaux (allègement) → on récupère aussi /settings/legal pour les éditer
  const [base, legal] = await Promise.all([
    api('/settings').catch(() => ({})),
    api('/settings/legal').catch(() => ({})),
  ])
  settings.value = { ...base, ...legal }
})

async function save() {
  settings.value = await api('/admin/settings', { method: 'PUT', body: settings.value })
  saved.value = true; setTimeout(() => (saved.value = false), 2500)
}
</script>

<template>
  <div>
    <h1 class="font-display text-2xl font-bold">Paramètres du site</h1>
    <p class="mt-1 text-slate-500">Enregistré en base — remplace dynamiquement le site (sans toucher au code).</p>
    <div class="card mt-6 grid gap-4 sm:grid-cols-2">
      <label v-for="f in FIELDS" :key="f.key" class="block text-sm">
        <span class="mb-1 block font-medium text-slate-600">{{ f.label }}</span>
        <input v-model="settings[f.key]" :placeholder="f.label" />
      </label>
    </div>

    <h2 class="mt-8 font-display text-lg font-bold">Textes légaux (Markdown)</h2>
    <p class="mt-1 text-sm text-slate-500">Affichés sur les pages /cgu, /confidentialite et /mentions-legales.</p>
    <div class="card mt-4 grid gap-4">
      <label v-for="f in LEGAL" :key="f.key" class="block text-sm">
        <span class="mb-1 block font-medium text-slate-600">{{ f.label }}</span>
        <textarea v-model="settings[f.key]" rows="6" class="w-full font-mono text-xs" :placeholder="f.label" />
      </label>
    </div>

    <h2 class="mt-8 font-display text-lg font-bold">Badges des groupes (automatiques)</h2>
    <p class="mt-1 text-sm text-slate-500">Seuils du calcul automatique des badges. Plusieurs groupes peuvent partager un badge.</p>
    <div class="card mt-4 grid gap-4 sm:grid-cols-2">
      <label v-for="f in BADGES" :key="f.key" class="block text-sm">
        <span class="mb-1 block font-medium text-slate-600">{{ f.label }}</span>
        <input v-model="settings[f.key]" type="number" step="0.05" :placeholder="f.label" />
      </label>
    </div>

    <div class="mt-6 flex items-center gap-3">
      <button class="btn-primary" @click="save">Enregistrer</button>
      <span v-if="saved" class="text-sm text-agora-green"><i class="pi pi-check-circle" /> Enregistré</span>
    </div>
  </div>
</template>
