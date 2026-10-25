<script setup lang="ts">
useSeoMeta({ title: 'Inscription', robots: 'noindex' })
const { public: pub } = useRuntimeConfig()
const api = useApi()
const router = useRouter()

const form = reactive({ username: '', email: '', password: '', profession: '', preferred_language: 'fr', hp: '', turnstile_token: '' })
const error = ref('')
const loading = ref(false)
const showPw = ref(false)
const pwMode = ref<'standard' | 'passphrase'>('standard')

function genUsername() { form.username = generateUsername() }
function genPassword() { form.password = generatePassword(pwMode.value); showPw.value = true }

// Cloudflare Turnstile (chargé uniquement si une clé publique est configurée)
const turnstileKey = pub.turnstileSiteKey
if (turnstileKey) {
  useHead({ script: [{ src: 'https://challenges.cloudflare.com/turnstile/v0/api.js', async: true, defer: true }] })
}

async function submit() {
  error.value = ''
  if (form.username.trim().length < 3) { error.value = "Le pseudo est obligatoire (3 caractères minimum)."; return }
  if (form.password.length < 8) { error.value = 'Mot de passe : 8 caractères minimum.'; return }
  // Récupère le jeton Turnstile depuis le champ injecté par le widget
  const tsToken = turnstileKey
    ? (document.querySelector('[name="cf-turnstile-response"]') as HTMLInputElement | null)?.value || ''
    : ''
  if (turnstileKey && !tsToken) { error.value = 'Merci de valider le test anti-robot.'; return }
  form.turnstile_token = tsToken
  loading.value = true
  try {
    await api('/auth/register', { method: 'POST', body: { ...form, username: form.username.trim() } })
    router.push({ path: '/verify-email', query: { email: form.email } })
  } catch (e: any) {
    error.value = e?.data?.detail || "Échec de l'inscription"
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <AuthShell active="register">
    <p class="-mt-2 mb-4 text-sm text-slate-500">Un code de vérification vous sera envoyé par email.</p>
    <div class="space-y-4">
      <!-- Honeypot anti-spam : caché aux humains, rempli par les bots -->
      <input v-model="form.hp" type="text" name="website" tabindex="-1" autocomplete="off"
             aria-hidden="true" class="absolute left-[-9999px] h-0 w-0 opacity-0" />
      <!-- Pseudo (obligatoire, unique) -->
      <div>
        <label class="mb-1 block text-sm font-semibold text-slate-600">Pseudo <span class="text-red-500">*</span></label>
        <div class="flex gap-2">
          <input v-model="form.username" placeholder="ex. ivoirebaobab12" />
          <button type="button" class="btn-outline shrink-0" title="Générer un pseudo" @click="genUsername"><i class="pi pi-refresh" /></button>
        </div>
        <p class="mt-1 text-xs text-slate-400">Visible publiquement, unique. C'est ce qui s'affichera par défaut.</p>
      </div>

      <label class="block">
        <span class="mb-1 block text-sm font-semibold text-slate-600">Email</span>
        <input v-model="form.email" type="email" placeholder="votre@email.com" />
      </label>

      <!-- Profession (demandée à tous — sert au profil et aux futures candidatures d'expert) -->
      <div>
        <label class="mb-1 block text-sm font-semibold text-slate-600">Profession / activité</label>
        <input v-model="form.profession" placeholder="ex. Étudiant, Avocat, Commerçant, Développeur…" maxlength="120" />
        <p class="mt-1 text-xs text-slate-400">Facultatif, mais utile pour la communauté. Les experts pourront ensuite se faire vérifier.</p>
      </div>

      <!-- Mot de passe : standard / passphrase, afficher/masquer, générer -->
      <div>
        <div class="mb-1 flex items-center justify-between">
          <label class="text-sm font-semibold text-slate-600">Mot de passe</label>
          <div class="flex rounded-lg border border-slate-200 text-xs">
            <button type="button" class="px-2 py-0.5" :class="pwMode==='standard' ? 'bg-agora-orange/10 text-agora-orange' : 'text-slate-500'" @click="pwMode='standard'">Mot de passe</button>
            <button type="button" class="px-2 py-0.5" :class="pwMode==='passphrase' ? 'bg-agora-orange/10 text-agora-orange' : 'text-slate-500'" @click="pwMode='passphrase'">Passphrase</button>
          </div>
        </div>
        <div class="relative">
          <input v-model="form.password" :type="showPw ? 'text' : 'password'" placeholder="8 caractères minimum" class="pr-10" />
          <button type="button" class="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600" :title="showPw ? 'Masquer' : 'Afficher'" @click="showPw = !showPw">
            <i :class="['pi', showPw ? 'pi-eye-slash' : 'pi-eye']" />
          </button>
        </div>
        <button type="button" class="mt-1 text-xs text-agora-green hover:underline" @click="genPassword">
          <i class="pi pi-sparkles" /> Générer {{ pwMode === 'passphrase' ? 'une passphrase' : 'un mot de passe' }}
        </button>
      </div>

      <!-- Test anti-robot Cloudflare Turnstile (affiché seulement si configuré) -->
      <div v-if="turnstileKey" class="cf-turnstile" :data-sitekey="turnstileKey" />

      <p v-if="error" class="text-sm text-red-600">{{ error }}</p>
      <button class="btn-primary w-full py-3" :disabled="loading" @click="submit">S'inscrire</button>
    </div>

    <template v-if="pub.googleEnabled">
      <div class="my-5 flex items-center gap-3 text-sm text-slate-400">
        <span class="h-px flex-1 bg-slate-200" /> ou continuer avec <span class="h-px flex-1 bg-slate-200" />
      </div>
      <a :href="`${pub.apiBase}/auth/google/login`" class="btn-outline w-full justify-center py-2.5">
        <i class="pi pi-google text-agora-orange" /> Google
      </a>
    </template>
  </AuthShell>
</template>
