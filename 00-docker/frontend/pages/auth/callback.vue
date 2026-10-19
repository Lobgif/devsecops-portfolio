<script setup lang="ts">
// OAuth Google : le backend a déjà posé les cookies httpOnly sur la redirection.
// On récupère juste le profil puis on redirige.
useSeoMeta({ title: 'Connexion…', robots: 'noindex' })
const auth = useAuthStore()
const router = useRouter()
const api = useApi()

onMounted(async () => {
  await auth.fetchMe(api)
  router.replace('/')
})
</script>

<template>
  <section class="grid min-h-[40vh] place-items-center text-slate-500">
    <p><i class="pi pi-spin pi-spinner" /> Connexion en cours…</p>
  </section>
</template>
