<script setup lang="ts">
useSeoMeta({ title: 'Mon profil', robots: 'noindex' })
const api = useApi()
const auth = useAuthStore()

const me = ref<any>(null)
const expertForm = reactive({ domain: '', evidence: '' })
const expertMsg = ref('')
const applying = ref(false)

async function loadMe() {
  if (auth.user?.username) me.value = await api(`/auth/users/${auth.user.username}`).catch(() => null)
}

async function applyExpert() {
  expertMsg.value = ''
  if (expertForm.domain.trim().length < 2) { expertMsg.value = 'Indiquez votre domaine d\'expertise.'; return }
  applying.value = true
  try {
    await api('/auth/expert/apply', { method: 'POST', body: { domain: expertForm.domain.trim(), evidence: expertForm.evidence.trim() } })
    expertMsg.value = 'Candidature envoyée ✅ Un administrateur va l\'examiner.'
  } catch (e: any) { expertMsg.value = e?.data?.detail || 'Erreur.' }
  finally { applying.value = false }
}

onMounted(async () => {
  auth.load()
  if (!auth.isAuthenticated) return navigateTo('/login')
  await auth.fetchMe(api)
  if (auth.user) Object.assign(form, {
    full_name: auth.user.full_name || '',
    bio: auth.user.bio || '',
    avatar_url: auth.user.avatar_url || '',
    display_pref: auth.user.display_pref || 'username',
  })
  await loadMe()
})

const form = reactive({ full_name: '', bio: '', avatar_url: '', display_pref: 'username' })
const saved = ref(false)
const uploadingAvatar = ref(false)

async function save() {
  await api('/auth/me', { method: 'PUT', body: form })
  await auth.fetchMe(api)
  saved.value = true
}

async function onAvatar(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return
  uploadingAvatar.value = true
  try {
    const fd = new FormData()
    fd.append('file', file)
    fd.append('prefix', 'avatars')
    const r = await api('/uploads', { method: 'POST', body: fd })
    form.avatar_url = r.url
    await api('/auth/me', { method: 'PUT', body: form })
    await auth.fetchMe(api)
  } catch (e: any) { alert(e?.data?.detail || 'Échec de l\'upload.') }
  finally { uploadingAvatar.value = false }
}

// Changement de mot de passe
const pw = reactive({ current_password: '', new_password: '', confirm: '' })
const pwMsg = ref(''); const pwErr = ref('')
async function changePassword() {
  pwMsg.value = ''; pwErr.value = ''
  if (pw.new_password.length < 8) { pwErr.value = '8 caractères minimum.'; return }
  if (pw.new_password !== pw.confirm) { pwErr.value = 'Les mots de passe ne correspondent pas.'; return }
  try {
    await api('/auth/change-password', { method: 'POST', body: { current_password: pw.current_password, new_password: pw.new_password } })
    pwMsg.value = 'Mot de passe mis à jour.'
    pw.current_password = pw.new_password = pw.confirm = ''
  } catch (e: any) { pwErr.value = e?.data?.detail || 'Erreur.' }
}

// Suppression de compte
async function deleteAccount() {
  if (!confirm('Supprimer définitivement votre compte et toutes vos données ? Cette action est irréversible.')) return
  try {
    await api('/auth/me', { method: 'DELETE' })
    auth.user = null
    navigateTo('/')
  } catch (e: any) { alert(e?.data?.detail || 'Erreur.') }
}
</script>

<template>
  <AppShell>
    <div class="mx-auto max-w-2xl">
    <h1 class="mb-4 font-display text-2xl font-extrabold">Paramètres</h1>
    <div class="card">
      <h2 class="font-display text-lg font-bold">Mon profil</h2>
      <p v-if="auth.user" class="mt-1 text-sm text-slate-500">
        @{{ auth.user.username }} · {{ auth.user.email }}
        <span v-if="auth.user.is_superadmin" class="ml-2 rounded bg-agora-orange/10 px-2 py-0.5 text-xs text-agora-orange">super-admin</span>
      </p>
      <div class="mt-6 space-y-4">
        <div class="flex items-center gap-4">
          <img v-if="form.avatar_url" :src="form.avatar_url" class="h-16 w-16 rounded-full object-cover" />
          <span v-else class="grid h-16 w-16 place-items-center rounded-full bg-agora-green text-2xl font-bold text-white">
            {{ (auth.user?.username || '?').charAt(0).toUpperCase() }}
          </span>
          <label class="btn-ghost cursor-pointer border text-sm">
            <i :class="['pi', uploadingAvatar ? 'pi-spin pi-spinner' : 'pi-camera']" /> {{ uploadingAvatar ? 'Envoi…' : 'Changer la photo' }}
            <input type="file" accept="image/*" class="hidden" @change="onAvatar" />
          </label>
        </div>
        <input v-model="form.full_name" placeholder="Nom complet" class="w-full rounded-xl border px-3 py-2" />
        <textarea v-model="form.bio" placeholder="Bio" rows="3" class="w-full rounded-xl border px-3 py-2" />
        <label class="block text-sm">
          <span class="mb-1 block font-medium text-slate-600">Afficher mon nom comme</span>
          <select v-model="form.display_pref" class="w-full rounded-xl border px-3 py-2">
            <option value="username">Pseudo (@{{ auth.user?.username }}) — par défaut</option>
            <option value="fullname">Nom complet</option>
            <option value="firstname">Prénom seulement</option>
          </select>
        </label>
        <button class="btn-primary" @click="save">Enregistrer</button>
        <p v-if="saved" class="text-sm text-agora-green">Profil mis à jour.</p>
      </div>
    </div>

    <!-- Badges + Expertise -->
    <div class="card mt-6">
      <h2 class="font-display text-lg font-bold">Badges & expertise</h2>
      <div v-if="me?.badges?.length" class="mt-3 flex flex-wrap gap-2">
        <span v-for="b in me.badges" :key="b.label"
              class="chip" :class="b.type === 'expert' ? 'bg-agora-green/10 text-agora-green' : 'bg-agora-orange/10 text-agora-orange'">
          <i :class="['pi', b.type === 'expert' ? 'pi-verified' : 'pi-star']" /> {{ b.label }}
        </span>
      </div>
      <p v-else class="mt-2 text-sm text-slate-500">Pas encore de badge. Répondez et aidez la communauté pour en gagner !</p>

      <div class="mt-5 border-t pt-4">
        <template v-if="me?.is_expert">
          <p class="text-sm text-agora-green"><i class="pi pi-verified" /> Vous êtes <strong>expert vérifié</strong><span v-if="me.expert_domain"> en {{ me.expert_domain }}</span>.</p>
        </template>
        <template v-else>
          <h3 class="font-semibold">Devenir expert vérifié</h3>
          <p class="mt-1 text-sm text-slate-500">
            Faites vérifier votre expertise (avocat, médecin, agent, comptable…). Vos réponses pèseront plus
            et porteront un badge de confiance. Un administrateur validera votre candidature.
          </p>
          <div class="mt-3 space-y-3">
            <input v-model="expertForm.domain" placeholder="Votre domaine (ex. Droit du travail, Santé, Fiscalité…)" class="w-full rounded-xl border px-3 py-2" maxlength="120" />
            <textarea v-model="expertForm.evidence" rows="3" placeholder="Justifiez brièvement (diplôme, profession, lien professionnel…). Un document pourra être demandé ensuite." class="w-full rounded-xl border px-3 py-2" maxlength="2000" />
            <p v-if="expertMsg" class="text-sm" :class="expertMsg.includes('✅') ? 'text-agora-green' : 'text-red-600'">{{ expertMsg }}</p>
            <button class="btn-primary" :disabled="applying" @click="applyExpert">
              <i :class="['pi', applying ? 'pi-spin pi-spinner' : 'pi-verified']" /> Envoyer ma candidature
            </button>
          </div>
        </template>
      </div>
    </div>

    <!-- Sécurité : mot de passe -->
    <div class="card mt-6">
      <h2 class="font-display text-lg font-bold">Mot de passe</h2>
      <div class="mt-4 space-y-3">
        <input v-model="pw.current_password" type="password" placeholder="Mot de passe actuel" class="w-full rounded-xl border px-3 py-2" />
        <input v-model="pw.new_password" type="password" placeholder="Nouveau mot de passe (8 car. min.)" class="w-full rounded-xl border px-3 py-2" />
        <input v-model="pw.confirm" type="password" placeholder="Confirmer le nouveau mot de passe" class="w-full rounded-xl border px-3 py-2" />
        <p v-if="pwErr" class="text-sm text-red-600">{{ pwErr }}</p>
        <p v-if="pwMsg" class="text-sm text-agora-green">{{ pwMsg }}</p>
        <button class="btn-ghost border" @click="changePassword">Changer le mot de passe</button>
      </div>
    </div>

    <!-- Zone de danger : suppression du compte -->
    <div v-if="!auth.user?.is_superadmin" class="card mt-6 border-red-200">
      <h2 class="font-display text-lg font-bold text-red-600">Supprimer mon compte</h2>
      <p class="mt-1 text-sm text-slate-500">Cette action supprime définitivement votre compte et tout votre contenu. Irréversible.</p>
      <button class="btn-ghost mt-3 border border-red-300 text-red-600 hover:bg-red-50" @click="deleteAccount">
        <i class="pi pi-trash" /> Supprimer définitivement mon compte
      </button>
    </div>
    </div>
  </AppShell>
</template>
