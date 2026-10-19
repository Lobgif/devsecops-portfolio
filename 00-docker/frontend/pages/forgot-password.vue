<script setup lang="ts">
useSeoMeta({ title: 'Mot de passe oublié', robots: 'noindex' })
const api = useApi()
const router = useRouter()
const email = ref('')
const sent = ref(false)
const loading = ref(false)

async function submit() {
  loading.value = true
  try {
    await api('/auth/forgot-password', { method: 'POST', body: { email: email.value } })
    sent.value = true
  } finally { loading.value = false }
}
</script>

<template>
  <section class="mx-auto max-w-md px-4 py-12">
    <div class="card">
      <h1 class="font-display text-2xl font-bold">Mot de passe oublié</h1>
      <template v-if="!sent">
        <p class="mt-1 text-sm text-slate-500">Entrez votre email : un code de réinitialisation vous sera envoyé.</p>
        <div class="mt-6 space-y-4">
          <input v-model="email" type="email" placeholder="Email" />
          <button class="btn-primary w-full" :disabled="loading || !email" @click="submit">Envoyer le code</button>
        </div>
      </template>
      <template v-else>
        <p class="mt-3 text-sm text-agora-green">Si un compte existe, un code a été envoyé par email.</p>
        <button class="btn-primary mt-4 w-full" @click="router.push({ path: '/reset-password', query: { email } })">
          J'ai reçu mon code
        </button>
      </template>
      <p class="mt-4 text-center text-sm"><NuxtLink to="/login" class="text-agora-green">Retour à la connexion</NuxtLink></p>
    </div>
  </section>
</template>
