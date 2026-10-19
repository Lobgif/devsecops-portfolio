<script setup lang="ts">
useSeoMeta({ title: 'Connexion', robots: 'noindex' })
const { public: pub } = useRuntimeConfig()
const api = useApi()
const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const form = reactive({ email: '', password: '' })
const error = ref('')
const showPw = ref(false)
const redirect = computed(() => (route.query.redirect as string) || '/')

async function submit() {
  error.value = ''
  try {
    await api('/auth/login', { method: 'POST', body: form })  // cookies httpOnly posés
    await auth.fetchMe(api)
    router.push(redirect.value)
  } catch (e: any) {
    error.value = e?.data?.detail || 'Identifiants invalides'
  }
}
</script>

<template>
  <AuthShell active="login">
    <div class="space-y-4">
      <label class="block">
        <span class="mb-1 block text-sm font-semibold text-slate-600">Email</span>
        <input v-model="form.email" type="email" placeholder="votre@email.com" />
      </label>
      <label class="block">
        <div class="mb-1 flex items-center justify-between">
          <span class="text-sm font-semibold text-slate-600">Mot de passe</span>
          <NuxtLink to="/forgot-password" class="text-sm text-agora-orange hover:underline">Mot de passe oublié ?</NuxtLink>
        </div>
        <div class="relative">
          <input v-model="form.password" :type="showPw ? 'text' : 'password'" placeholder="••••••••" class="pr-10" @keyup.enter="submit" />
          <button type="button" class="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600" :title="showPw ? 'Masquer' : 'Afficher'" @click="showPw = !showPw">
            <i :class="['pi', showPw ? 'pi-eye-slash' : 'pi-eye']" />
          </button>
        </div>
      </label>
      <p v-if="error" class="text-sm text-red-600">{{ error }}</p>
      <button class="btn-primary w-full py-3" @click="submit">Se connecter</button>
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
