<script setup lang="ts">
const { public: pub } = useRuntimeConfig()
const auth = useAuthStore()
const router = useRouter()
const route = useRoute()
const api = useApi()

const links = [
  { to: '/', label: 'Accueil', icon: 'pi-home' },
  { to: '/forums', label: 'Forums', icon: 'pi-comments' },
  { to: '/ia-juridique', label: 'Nanan', icon: 'pi-sparkles' },
  { to: '/about', label: 'À propos', icon: 'pi-info-circle' },
  { to: '/contact', label: 'Contact', icon: 'pi-envelope' },
]
const isActive = (to: string) => (to === '/' ? route.path === '/' : route.path.startsWith(to))

// Paramètres du site (dynamiques, éditables en admin) — sans await pour ne pas casser les hooks
const { data: settings } = useAsyncData('layout-settings', () => api('/settings').catch(() => ({})))
const set = (k: string, fallback = '') => (settings.value?.[k] ?? fallback)

const open = ref(false)
const mobileOpen = ref(false)
const menuRef = ref<HTMLElement | null>(null)

const initial = computed(() => (auth.user?.username || '?').charAt(0).toUpperCase())

function onDocClick(e: MouseEvent) {
  if (menuRef.value && !menuRef.value.contains(e.target as Node)) open.value = false
}
onMounted(() => document.addEventListener('click', onDocClick))
onBeforeUnmount(() => document.removeEventListener('click', onDocClick))
watch(() => route.fullPath, () => { open.value = false; mobileOpen.value = false })

async function logout() {
  await auth.logout(api)
  open.value = false
  router.push('/')
}

const searchQ = ref('')
function goSearch() {
  if (searchQ.value.trim().length >= 2) router.push({ path: '/search', query: { q: searchQ.value } })
}
</script>

<template>
  <div class="flex min-h-screen flex-col">
    <header class="sticky top-0 z-50 border-b border-slate-200 bg-white/80 backdrop-blur">
      <div class="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
        <NuxtLink to="/" title="Jamakan — Accueil" aria-label="Jamakan — Accueil" class="group flex items-center font-display text-xl font-extrabold">
          <span class="grid h-9 w-9 place-items-center rounded-lg bg-gradient-to-br from-agora-orange to-agora-green text-base font-bold text-white shadow-sm transition group-hover:scale-105">J</span>
        </NuxtLink>

        <nav class="hidden gap-1 md:flex">
          <NuxtLink
            v-for="l in links" :key="l.to" :to="l.to"
            class="flex items-center gap-1.5 rounded-full px-3 py-1.5 text-sm font-medium transition"
            :class="isActive(l.to) ? 'bg-agora-orange/10 text-agora-orange' : 'text-slate-600 hover:bg-slate-100'"
          >
            <i :class="['pi', l.icon, 'text-xs']" /> {{ l.label }}
          </NuxtLink>
        </nav>

        <div class="relative hidden flex-1 max-w-xs lg:block">
          <i class="pi pi-search absolute left-3 top-1/2 -translate-y-1/2 text-sm text-slate-400" />
          <input
            v-model="searchQ"
            placeholder="Rechercher…"
            class="w-full rounded-full border border-slate-200 bg-slate-50 py-1.5 !pl-9 pr-3 text-sm focus:bg-white focus:outline-none"
            @keyup.enter="goSearch"
          />
        </div>

        <div class="hidden items-center md:flex">
        <ClientOnly>
          <!-- Connecté : cloche + bouton profil + menu déroulant -->
          <div v-if="auth.isAuthenticated" class="flex items-center gap-1">
            <NotificationBell />
            <div ref="menuRef" class="relative">
            <button
              class="flex items-center gap-2 rounded-full border border-slate-200 py-1 pl-1 pr-3 transition hover:bg-slate-50"
              @click="open = !open"
            >
              <img v-if="auth.user?.avatar_url" :src="auth.user.avatar_url" class="h-8 w-8 rounded-full object-cover" />
              <span v-else class="grid h-8 w-8 place-items-center rounded-full bg-agora-green font-semibold text-white">
                {{ initial }}
              </span>
              <span class="hidden max-w-[120px] truncate text-sm font-medium sm:inline">{{ auth.user?.username }}</span>
              <i class="pi pi-angle-down text-xs text-slate-400" />
            </button>

            <!-- Menu -->
            <div
              v-show="open"
              class="absolute right-0 mt-2 w-56 overflow-hidden rounded-2xl border border-slate-200 bg-white py-1 shadow-lg"
            >
              <div class="border-b border-slate-100 px-4 py-3">
                <p class="truncate font-semibold">{{ displayName(auth.user) }}</p>
                <p class="truncate text-xs text-slate-500">{{ auth.user?.email }}</p>
                <span v-if="auth.user?.is_superadmin" class="mt-1 inline-block rounded bg-agora-orange/10 px-2 py-0.5 text-xs text-agora-orange">
                  super-admin
                </span>
              </div>
              <NuxtLink to="/profile" class="flex items-center gap-2 px-4 py-2 text-sm hover:bg-slate-50">
                <i class="pi pi-user text-slate-400" /> Mon profil
              </NuxtLink>
              <NuxtLink to="/messages" class="flex items-center gap-2 px-4 py-2 text-sm hover:bg-slate-50">
                <i class="pi pi-envelope text-slate-400" /> Messages
              </NuxtLink>
              <NuxtLink to="/forums" class="flex items-center gap-2 px-4 py-2 text-sm hover:bg-slate-50">
                <i class="pi pi-comments text-slate-400" /> Forums
              </NuxtLink>
              <NuxtLink
                v-if="auth.isSuperadmin"
                :to="`/${pub.adminPath}`"
                class="flex items-center gap-2 px-4 py-2 text-sm hover:bg-slate-50"
              >
                <i class="pi pi-shield text-slate-400" /> Administration
              </NuxtLink>
              <button
                class="flex w-full items-center gap-2 border-t border-slate-100 px-4 py-2 text-left text-sm text-red-600 hover:bg-red-50"
                @click="logout"
              >
                <i class="pi pi-sign-out" /> Déconnexion
              </button>
            </div>
            </div>
          </div>

          <!-- Déconnecté -->
          <div v-else class="flex items-center gap-2">
            <NuxtLink to="/login" class="btn-ghost">Connexion</NuxtLink>
            <NuxtLink to="/register" class="btn-primary">Inscription</NuxtLink>
          </div>

          <template #fallback>
            <div class="flex items-center gap-2">
              <NuxtLink to="/login" class="btn-ghost">Connexion</NuxtLink>
              <NuxtLink to="/register" class="btn-primary">Inscription</NuxtLink>
            </div>
          </template>
        </ClientOnly>
        </div>

        <!-- Bouton menu (mobile) -->
        <button class="grid h-10 w-10 place-items-center rounded-lg text-slate-600 hover:bg-slate-100 md:hidden"
                aria-label="Menu" @click="mobileOpen = !mobileOpen">
          <i :class="['pi', mobileOpen ? 'pi-times' : 'pi-bars', 'text-lg']" />
        </button>
      </div>

      <!-- Panneau de navigation mobile -->
      <div v-show="mobileOpen" class="border-t border-slate-200 bg-white px-4 py-3 md:hidden">
        <div class="relative mb-3">
          <i class="pi pi-search absolute left-3 top-1/2 -translate-y-1/2 text-sm text-slate-400" />
          <input v-model="searchQ" placeholder="Rechercher…"
                 class="w-full rounded-full border border-slate-200 bg-slate-50 py-2 !pl-9 pr-3 text-sm focus:bg-white focus:outline-none"
                 @keyup.enter="goSearch(); mobileOpen = false" />
        </div>
        <nav class="grid gap-1">
          <NuxtLink v-for="l in links" :key="l.to" :to="l.to"
                    class="flex items-center gap-2 rounded-xl px-3 py-2 text-sm font-medium transition"
                    :class="isActive(l.to) ? 'bg-agora-orange/10 text-agora-orange' : 'text-slate-700 hover:bg-slate-100'">
            <i :class="['pi', l.icon]" /> {{ l.label }}
          </NuxtLink>
        </nav>
        <ClientOnly>
          <div v-if="auth.isAuthenticated" class="mt-3 grid gap-1 border-t border-slate-100 pt-3">
            <NuxtLink to="/profile" class="flex items-center gap-2 rounded-xl px-3 py-2 text-sm hover:bg-slate-100"><i class="pi pi-user text-slate-400" /> Mon profil</NuxtLink>
            <NuxtLink to="/messages" class="flex items-center gap-2 rounded-xl px-3 py-2 text-sm hover:bg-slate-100"><i class="pi pi-envelope text-slate-400" /> Messages</NuxtLink>
            <NuxtLink to="/notifications" class="flex items-center gap-2 rounded-xl px-3 py-2 text-sm hover:bg-slate-100"><i class="pi pi-bell text-slate-400" /> Notifications</NuxtLink>
            <NuxtLink v-if="auth.isSuperadmin" :to="`/${pub.adminPath}`" class="flex items-center gap-2 rounded-xl px-3 py-2 text-sm hover:bg-slate-100"><i class="pi pi-shield text-slate-400" /> Administration</NuxtLink>
            <button class="flex items-center gap-2 rounded-xl px-3 py-2 text-left text-sm text-red-600 hover:bg-red-50" @click="logout"><i class="pi pi-sign-out" /> Déconnexion</button>
          </div>
          <div v-else class="mt-3 grid grid-cols-2 gap-2 border-t border-slate-100 pt-3">
            <NuxtLink to="/login" class="btn-ghost justify-center border">Connexion</NuxtLink>
            <NuxtLink to="/register" class="btn-primary justify-center">Inscription</NuxtLink>
          </div>
        </ClientOnly>
      </div>
    </header>

    <main class="flex-1">
      <slot />
    </main>

    <footer class="mt-12 bg-agora-ink text-slate-300">
      <div class="mx-auto grid max-w-6xl gap-8 px-4 py-12 sm:grid-cols-2 lg:grid-cols-4">
        <!-- Marque + réseaux -->
        <div>
          <div class="flex items-center gap-2 font-display text-lg font-extrabold text-white">
            <span class="grid h-8 w-8 place-items-center rounded-lg bg-gradient-to-br from-agora-orange to-agora-green text-sm text-white">J</span>
            <span>Jama<span class="text-agora-orange">kan</span></span>
          </div>
          <p class="mt-3 text-sm text-slate-400">
            {{ set('footer_tagline', "Plateforme citoyenne collaborative pour la Côte d'Ivoire.") }}
          </p>
          <div class="mt-4 flex gap-3 text-slate-400">
            <a v-if="set('social_facebook')" :href="set('social_facebook')" target="_blank" rel="noopener" class="hover:text-white"><i class="pi pi-facebook text-lg" /></a>
            <a v-if="set('social_x')" :href="set('social_x')" target="_blank" rel="noopener" class="hover:text-white"><i class="pi pi-twitter text-lg" /></a>
            <a v-if="set('social_instagram')" :href="set('social_instagram')" target="_blank" rel="noopener" class="hover:text-white"><i class="pi pi-instagram text-lg" /></a>
            <a v-if="set('social_linkedin')" :href="set('social_linkedin')" target="_blank" rel="noopener" class="hover:text-white"><i class="pi pi-linkedin text-lg" /></a>
          </div>
        </div>

        <!-- Liens rapides -->
        <div>
          <p class="mb-3 text-sm font-semibold text-white">Liens rapides</p>
          <ul class="space-y-2 text-sm text-slate-400">
            <li><NuxtLink to="/" class="hover:text-agora-orange">Accueil</NuxtLink></li>
            <li><NuxtLink to="/forums" class="hover:text-agora-orange">Forums</NuxtLink></li>
            <li><NuxtLink to="/ia-juridique" class="hover:text-agora-orange">Nanan (assistant IA)</NuxtLink></li>
            <li><NuxtLink to="/comparateur" class="hover:text-agora-orange">Comparateur</NuxtLink></li>
            <li><NuxtLink to="/classement" class="hover:text-agora-orange">Classement</NuxtLink></li>
            <li><NuxtLink to="/faq" class="hover:text-agora-orange">Questions fréquentes</NuxtLink></li>
          </ul>
        </div>

        <!-- Légal -->
        <div>
          <p class="mb-3 text-sm font-semibold text-white">Légal</p>
          <ul class="space-y-2 text-sm text-slate-400">
            <li><NuxtLink to="/cgu" class="hover:text-agora-orange">Conditions d’utilisation</NuxtLink></li>
            <li><NuxtLink to="/confidentialite" class="hover:text-agora-orange">Politique de confidentialité</NuxtLink></li>
            <li><NuxtLink to="/mentions-legales" class="hover:text-agora-orange">Mentions légales</NuxtLink></li>
            <li><NuxtLink to="/about" class="hover:text-agora-orange">À propos</NuxtLink></li>
          </ul>
        </div>

        <!-- Nous contacter -->
        <div>
          <p class="mb-3 text-sm font-semibold text-white">Nous contacter</p>
          <ul class="space-y-2 text-sm text-slate-400">
            <li><a :href="`mailto:${set('contact_email', 'contact@ibrahimafofana.com')}`" class="flex items-center gap-2 hover:text-agora-orange"><i class="pi pi-envelope text-agora-orange" /> {{ set('contact_email', 'contact@ibrahimafofana.com') }}</a></li>
            <li v-if="set('contact_phone')"><a :href="`tel:${set('contact_phone')}`" class="flex items-center gap-2 hover:text-agora-orange"><i class="pi pi-phone text-agora-orange" /> {{ set('contact_phone') }}</a></li>
            <li class="flex items-center gap-2"><i class="pi pi-map-marker text-agora-orange" /> {{ set('contact_location', "Abidjan, Côte d'Ivoire") }}</li>
          </ul>
          <p class="mb-2 mt-4 text-sm font-semibold text-white">Langues</p>
          <div class="flex flex-wrap gap-2">
            <span class="rounded-md bg-white/10 px-2.5 py-1 text-xs font-semibold text-white">FR</span>
            <span class="rounded-md bg-white/5 px-2.5 py-1 text-xs text-slate-400" title="Bientôt">EN</span>
            <span class="rounded-md bg-white/5 px-2.5 py-1 text-xs text-slate-400" title="Bientôt">Baoulé</span>
            <span class="rounded-md bg-white/5 px-2.5 py-1 text-xs text-slate-400" title="Bientôt">Dioula</span>
          </div>
        </div>
      </div>
      <div class="border-t border-white/10 py-5 text-center text-xs text-slate-500">
        © {{ new Date().getFullYear() }} {{ set('site_name', pub.siteName) }}. Tous droits réservés.
        <span v-if="set('footer_made_with')"> · {{ set('footer_made_with') }}</span>
      </div>
    </footer>
  </div>
</template>
