<script setup lang="ts">
const { public: pub } = useRuntimeConfig()
useSeoMeta({
  title: 'Contact',
  description: 'Contactez l’équipe Jamakan pour toute question, suggestion ou partenariat.',
  ogUrl: `${pub.siteUrl}/contact`,
})
const api = useApi()
const { data: settings } = await useAsyncData('contact-settings', () => api('/settings').catch(() => ({})))
const set = (k: string, fb = '') => (settings.value?.[k] ?? fb)

const form = reactive({ name: '', email: '', subject: '', message: '' })
const sending = ref(false)
const sent = ref(false)
const error = ref('')

async function submit() {
  error.value = ''
  if (!form.email.trim() || form.message.trim().length < 5) {
    error.value = 'Renseignez votre email et un message (5 caractères minimum).'
    return
  }
  sending.value = true
  try {
    await api('/contact', { method: 'POST', body: { ...form } })
    sent.value = true
  } catch (e: any) {
    error.value = e?.data?.detail || 'Envoi impossible. Réessayez plus tard.'
  } finally { sending.value = false }
}

const hasPhone = computed(() => !!set('contact_phone'))
const socials = computed(() => [
  { url: set('social_facebook'), icon: 'pi-facebook' },
  { url: set('social_x'), icon: 'pi-twitter' },
  { url: set('social_instagram'), icon: 'pi-instagram' },
  { url: set('social_linkedin'), icon: 'pi-linkedin' },
].filter(s => s.url))
</script>

<template>
  <div>
    <!-- Hero -->
    <section class="bg-gradient-to-b from-agora-orange/5 to-transparent py-16 text-center">
      <h1 class="font-display text-3xl font-extrabold md:text-4xl">Contactez <span class="text-agora-orange">Jamakan</span></h1>
      <p class="mx-auto mt-3 max-w-2xl px-4 text-slate-600">Nous sommes à votre écoute. N’hésitez pas à nous contacter pour toute question, suggestion ou partenariat.</p>
    </section>

    <div class="mx-auto -mt-6 max-w-2xl px-4 pb-16">
      <!-- Cartes infos -->
      <div class="grid gap-4" :class="hasPhone ? 'sm:grid-cols-3' : 'sm:grid-cols-2'">
        <div class="card text-center">
          <span class="mx-auto grid h-12 w-12 place-items-center rounded-full bg-agora-orange text-white"><i class="pi pi-envelope" /></span>
          <h3 class="mt-3 font-bold">Email</h3>
          <p class="mt-1 text-sm text-slate-500">Pour toute question ou demande d’information</p>
          <a :href="`mailto:${set('contact_email', 'contact@ibrahimafofana.com')}`" class="mt-1 block font-semibold text-agora-orange">{{ set('contact_email', 'contact@ibrahimafofana.com') }}</a>
        </div>
        <div v-if="set('contact_phone')" class="card text-center">
          <span class="mx-auto grid h-12 w-12 place-items-center rounded-full bg-agora-orange text-white"><i class="pi pi-phone" /></span>
          <h3 class="mt-3 font-bold">Téléphone</h3>
          <p class="mt-1 text-sm text-slate-500">Du lundi au vendredi, de 8h à 18h</p>
          <a :href="`tel:${set('contact_phone')}`" class="mt-1 block font-semibold text-agora-orange">{{ set('contact_phone') }}</a>
        </div>
        <div class="card text-center">
          <span class="mx-auto grid h-12 w-12 place-items-center rounded-full bg-agora-orange text-white"><i class="pi pi-comments" /></span>
          <h3 class="mt-3 font-bold">Réseaux sociaux</h3>
          <p class="mt-1 text-sm text-slate-500">Suivez-nous et interagissez avec nous</p>
          <div v-if="socials.length" class="mt-2 flex justify-center gap-3">
            <a v-for="s in socials" :key="s.icon" :href="s.url" target="_blank" rel="noopener" class="text-slate-400 hover:text-agora-orange"><i :class="['pi', s.icon, 'text-lg']" /></a>
          </div>
          <p v-else class="mt-1 text-sm text-slate-400">{{ set('contact_location', "Abidjan, Côte d'Ivoire") }}</p>
        </div>
      </div>

      <!-- Formulaire -->
      <div class="card mt-6">
        <h2 class="font-display text-xl font-bold">Envoyez-nous un message</h2>
        <template v-if="!sent">
          <div class="mt-4 space-y-4">
            <div class="grid gap-4 sm:grid-cols-2">
              <label class="block"><span class="mb-1 block text-sm font-semibold text-slate-600">Nom</span>
                <input v-model="form.name" placeholder="Votre nom" maxlength="120" /></label>
              <label class="block"><span class="mb-1 block text-sm font-semibold text-slate-600">Email <span class="text-red-500">*</span></span>
                <input v-model="form.email" type="email" placeholder="votre@email.com" /></label>
            </div>
            <label class="block"><span class="mb-1 block text-sm font-semibold text-slate-600">Sujet</span>
              <input v-model="form.subject" placeholder="Objet de votre message" maxlength="200" /></label>
            <label class="block"><span class="mb-1 block text-sm font-semibold text-slate-600">Message <span class="text-red-500">*</span></span>
              <textarea v-model="form.message" rows="5" placeholder="Votre message…" /></label>
            <p v-if="error" class="text-sm text-red-600">{{ error }}</p>
            <button class="btn-primary w-full py-3" :disabled="sending" @click="submit">
              <i :class="['pi', sending ? 'pi-spin pi-spinner' : 'pi-send']" /> Envoyer le message
            </button>
          </div>
        </template>
        <div v-else class="mt-4 rounded-2xl bg-agora-green/5 p-6 text-center">
          <i class="pi pi-check-circle text-3xl text-agora-green" />
          <p class="mt-2 font-bold">Message envoyé !</p>
          <p class="mt-1 text-sm text-slate-500">Merci, nous vous répondrons dès que possible.</p>
        </div>
      </div>
    </div>
  </div>
</template>
