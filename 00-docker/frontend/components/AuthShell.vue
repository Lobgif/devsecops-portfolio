<script setup lang="ts">
// Panneau d'authentification en 2 colonnes (bandeau orange + formulaire à onglets).
defineProps<{ active: 'login' | 'register' }>()
const bullets = [
  'Posez vos questions sur les sujets qui vous concernent',
  'Obtenez des réponses fiables, ancrées dans le contexte ivoirien',
  'Rejoignez une communauté citoyenne d’entraide',
]

// Réseaux sociaux : cliquables uniquement si l'URL est renseignée en admin (sinon masqués).
const api = useApi()
const { data: settings } = await useAsyncData('auth-settings', () => api('/settings').catch(() => ({})))
const socials = computed(() => [
  { url: settings.value?.social_facebook, icon: 'pi-facebook' },
  { url: settings.value?.social_x, icon: 'pi-twitter' },
  { url: settings.value?.social_instagram, icon: 'pi-instagram' },
  { url: settings.value?.social_linkedin, icon: 'pi-linkedin' },
].filter(s => s.url))
</script>

<template>
  <section class="mx-auto max-w-4xl px-4 py-10">
    <div class="grid overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm md:grid-cols-2">
      <!-- Bandeau gauche -->
      <div class="relative hidden flex-col justify-between bg-gradient-to-br from-agora-orange to-[#e0522a] p-8 text-white md:flex">
        <div>
          <h2 class="font-display text-2xl font-extrabold">Bienvenue sur Jamakan</h2>
          <p class="mt-3 text-sm text-white/90">La plateforme d’échange citoyenne pour les Ivoiriens, par les Ivoiriens.</p>
          <ul class="mt-6 space-y-3">
            <li v-for="b in bullets" :key="b" class="flex items-start gap-2.5 text-sm">
              <i class="pi pi-check-circle mt-0.5 text-white/90" /> <span>{{ b }}</span>
            </li>
          </ul>
        </div>
        <div v-if="socials.length" class="flex gap-4 text-white/80">
          <a v-for="s in socials" :key="s.icon" :href="s.url" target="_blank" rel="noopener"
             class="transition hover:text-white"><i :class="['pi', s.icon, 'text-lg']" /></a>
        </div>
      </div>

      <!-- Formulaire -->
      <div class="p-7 sm:p-8">
        <div class="mb-6 flex gap-6 border-b border-slate-200">
          <NuxtLink to="/login" class="-mb-px border-b-2 pb-2 text-base font-bold transition"
                    :class="active === 'login' ? 'border-agora-orange text-agora-orange' : 'border-transparent text-slate-400 hover:text-slate-600'">Connexion</NuxtLink>
          <NuxtLink to="/register" class="-mb-px border-b-2 pb-2 text-base font-bold transition"
                    :class="active === 'register' ? 'border-agora-orange text-agora-orange' : 'border-transparent text-slate-400 hover:text-slate-600'">Inscription</NuxtLink>
        </div>
        <slot />
      </div>
    </div>
  </section>
</template>
