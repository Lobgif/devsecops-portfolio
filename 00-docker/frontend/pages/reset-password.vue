<script setup lang="ts">
useSeoMeta({ title: 'Réinitialiser le mot de passe', robots: 'noindex' })
const api = useApi()
const route = useRoute()
const router = useRouter()

const form = reactive({
  email: (route.query.email as string) || '',
  code: '',
  new_password: '',
})
const error = ref('')
const loading = ref(false)

async function submit() {
  loading.value = true
  error.value = ''
  try {
    await api('/auth/reset-password', { method: 'POST', body: form })
    router.push('/login')
  } catch (e: any) {
    error.value = e?.data?.detail || 'Code invalide ou expiré'
  } finally { loading.value = false }
}
</script>

<template>
  <section class="mx-auto max-w-md px-4 py-12">
    <div class="card">
      <h1 class="font-display text-2xl font-bold">Nouveau mot de passe</h1>
      <p class="mt-1 text-sm text-slate-500">Saisissez le code reçu par email et votre nouveau mot de passe.</p>
      <div class="mt-6 space-y-4">
        <input v-model="form.email" type="email" placeholder="Email" />
        <input v-model="form.code" inputmode="numeric" maxlength="6" placeholder="Code (6 chiffres)"
               class="text-center text-2xl tracking-[0.4em]" />
        <input v-model="form.new_password" type="password" placeholder="Nouveau mot de passe (8+ caractères)" />
        <p v-if="error" class="text-sm text-red-600">{{ error }}</p>
        <button class="btn-primary w-full" :disabled="loading" @click="submit">Réinitialiser</button>
      </div>
      <p class="mt-4 text-center text-sm"><NuxtLink to="/login" class="text-agora-green">Retour à la connexion</NuxtLink></p>
    </div>
  </section>
</template>
