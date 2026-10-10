<script setup lang="ts">
useSeoMeta({ title: 'Vérification email', robots: 'noindex' })
const api = useApi()
const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const email = ref((route.query.email as string) || '')
const code = ref('')
const error = ref('')
const info = ref('')

async function verify() {
  error.value = ''
  try {
    await api('/auth/verify-email', { method: 'POST', body: { email: email.value, code: code.value } })
    await auth.fetchMe(api)
    router.push('/')
  } catch (e: any) {
    error.value = e?.data?.detail || 'Code invalide'
  }
}

async function resend() {
  info.value = ''
  await api('/auth/resend-code', { method: 'POST', body: { email: email.value } }).catch(() => {})
  info.value = 'Un nouveau code a été envoyé si le compte existe.'
}
</script>

<template>
  <section class="mx-auto max-w-md px-4 py-12">
    <div class="card">
      <h1 class="font-display text-2xl font-bold">Vérifiez votre email</h1>
      <p class="mt-1 text-sm text-slate-500">Saisissez le code à 6 chiffres reçu par email.</p>
      <div class="mt-6 space-y-4">
        <input v-model="email" type="email" placeholder="Email" class="w-full rounded-xl border px-3 py-2" />
        <input v-model="code" inputmode="numeric" maxlength="6" placeholder="Code (6 chiffres)"
               class="w-full rounded-xl border px-3 py-2 text-center text-2xl tracking-[0.5em]" />
        <p v-if="error" class="text-sm text-red-600">{{ error }}</p>
        <p v-if="info" class="text-sm text-agora-green">{{ info }}</p>
        <button class="btn-primary w-full" @click="verify">Valider</button>
        <button class="btn-ghost w-full justify-center" @click="resend">Renvoyer le code</button>
      </div>
    </div>
  </section>
</template>
