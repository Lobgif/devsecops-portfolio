<script setup lang="ts">
const { public: pub } = useRuntimeConfig()

useSeoMeta({
  title: 'L’entraide citoyenne en Côte d’Ivoire',
  description:
    "Jamakan : posez vos questions sur tous les sujets du quotidien ivoirien (démarches, droit, santé, éducation, emploi, vie pratique…) et obtenez des réponses fiables, validées par la communauté et éclairées par l’IA.",
  ogTitle: 'Jamakan — Plateforme citoyenne collaborative',
  ogDescription: 'Des réponses fiables sur tous les sujets du quotidien ivoirien, par la communauté et l’IA.',
  ogType: 'website',
  ogUrl: pub.siteUrl,
})
useHead({
  script: [{
    type: 'application/ld+json',
    innerHTML: JSON.stringify({
      '@context': 'https://schema.org', '@type': 'WebSite',
      name: pub.siteName, url: pub.siteUrl, inLanguage: 'fr-CI',
    }),
  }],
})

const features = [
  { icon: 'pi-users', color: 'text-agora-orange bg-agora-orange/10', title: 'Communauté active', text: 'Citoyens engagés qui s’entraident au quotidien.' },
  { icon: 'pi-sparkles', color: 'text-agora-green bg-agora-green/10', title: 'Nanan, le conseiller IA', text: 'Des réponses sourcées, ancrées dans le contexte ivoirien.' },
  { icon: 'pi-shield', color: 'text-sky-600 bg-sky-100', title: 'Espace sécurisé', text: 'Modération communautaire et respect.' },
]

// Connecté → tableau de bord ; déconnecté → page d'accueil marketing (rendue en SSR pour le SEO).
const auth = useAuthStore()
const showHero = computed(() => !auth.isAuthenticated)

// Données réelles pour les sections de la page d'accueil (SSR → bon pour le SEO).
const api = useApi()
const { data: homeGroups } = useAsyncData('home-groups', () => api('/forum/groups').catch(() => []), { default: () => [] })
const popularGroups = computed(() => [...(homeGroups.value as any[])].sort((a, b) => b.member_count - a.member_count).slice(0, 6))
const { data: recentQuestions } = useAsyncData('home-recent', () => api('/forum/feed?sort=recent&limit=4').catch(() => []), { default: () => [] })

const mission = [
  { icon: 'pi-comments', color: 'text-agora-orange bg-agora-orange/10', title: 'Échangez librement', text: 'Posez vos questions et partagez vos expériences sur les sujets qui vous concernent.' },
  { icon: 'pi-sparkles', color: 'text-agora-green bg-agora-green/10', title: 'Assistance IA', text: 'Nanan vous éclaire avec des réponses ancrées dans le contexte ivoirien.' },
  { icon: 'pi-users', color: 'text-violet-600 bg-violet-100', title: 'Créez des groupes', text: 'Formez des communautés autour de vos centres d’intérêt et invitez d’autres membres.' },
]
</script>

<template>
  <div>
  <!-- Tableau de bord (utilisateur connecté) -->
  <ClientOnly>
    <DashboardHome v-if="auth.isAuthenticated" />
  </ClientOnly>

  <div v-if="showHero">
  <!-- Hero -->
  <section class="relative overflow-hidden">
    <div class="absolute inset-0 -z-10 bg-gradient-to-b from-agora-orange/5 via-white to-white" />
    <div class="mx-auto max-w-4xl px-4 py-20 text-center">
      <span class="chip bg-agora-orange/10 text-agora-orange">
        <i class="pi pi-sparkles" /> Plateforme citoyenne collaborative
      </span>
      <h1 class="mt-5 font-display text-4xl font-extrabold leading-tight md:text-5xl">
        L'entraide citoyenne <span class="text-agora-orange">au cœur</span> de la Côte d'Ivoire
      </h1>
      <p class="mx-auto mt-4 max-w-2xl text-lg text-slate-600">
        Posez vos questions sur tous les sujets du quotidien, partagez vos expériences et accédez à des
        réponses fiables grâce à notre communauté et à Nanan, notre assistant IA ancré dans le contexte ivoirien.
      </p>
      <div class="mt-8 flex flex-wrap justify-center gap-3">
        <NuxtLink to="/forums" class="btn-primary px-6 py-3"><i class="pi pi-comments" /> Explorer les forums</NuxtLink>
        <NuxtLink to="/ia-juridique" class="btn-outline px-6 py-3"><i class="pi pi-sparkles" /> Demander à Nanan</NuxtLink>
      </div>

      <div class="mt-12 grid gap-4 sm:grid-cols-3">
        <div v-for="f in features" :key="f.title" class="card text-left">
          <span class="grid h-11 w-11 place-items-center rounded-xl" :class="f.color"><i :class="['pi', f.icon]" /></span>
          <h3 class="mt-3 font-semibold">{{ f.title }}</h3>
          <p class="mt-1 text-sm text-slate-500">{{ f.text }}</p>
        </div>
      </div>
    </div>
  </section>

  <!-- Notre Mission -->
  <section class="mx-auto max-w-6xl px-4 py-16 text-center">
    <h2 class="font-display text-2xl font-bold md:text-3xl">Notre Mission</h2>
    <p class="mx-auto mt-2 max-w-2xl text-slate-500">Jamakan facilite l’échange d’informations et de conseils sur les sujets essentiels pour les Ivoiriens.</p>
    <div class="mt-8 grid gap-4 md:grid-cols-3">
      <div v-for="m in mission" :key="m.title" class="card text-left">
        <span class="grid h-12 w-12 place-items-center rounded-xl text-lg" :class="m.color"><i :class="['pi', m.icon]" /></span>
        <h3 class="mt-3 font-bold">{{ m.title }}</h3>
        <p class="mt-1 text-sm text-slate-500">{{ m.text }}</p>
      </div>
    </div>
    <div class="mt-6 rounded-2xl border-l-4 border-agora-orange bg-agora-orange/5 p-5 text-left">
      <h3 class="font-bold">Notre engagement</h3>
      <p class="mt-1 text-sm text-slate-600">Nous croyons en la liberté d’expression et au partage des connaissances. La plateforme est conçue pour être inclusive, respectueuse et accessible à tous les Ivoiriens, où qu’ils soient.</p>
    </div>
  </section>

  <!-- Forums populaires -->
  <section v-if="popularGroups.length" class="mx-auto max-w-6xl px-4 pb-4 text-center">
    <h2 class="font-display text-2xl font-bold md:text-3xl">Forums populaires</h2>
    <p class="mt-2 text-slate-500">Rejoignez les discussions sur les sujets qui vous intéressent.</p>
    <div class="mt-8 grid gap-4 text-left sm:grid-cols-2 lg:grid-cols-3">
      <NuxtLink v-for="g in popularGroups" :key="g.id" :to="`/groups/${g.id}`" class="card transition hover:-translate-y-1 hover:shadow-md">
        <div class="flex items-center gap-3">
          <span class="grid h-10 w-10 shrink-0 place-items-center rounded-xl text-xs font-extrabold text-white" :class="categoryStyle(g.category).solid">{{ initials(g.name) }}</span>
          <div class="min-w-0">
            <h3 class="truncate font-bold">{{ g.name }}</h3>
            <p class="text-xs text-slate-400">{{ g.member_count }} membres · {{ g.discussion_count }} discussions</p>
          </div>
        </div>
        <p class="mt-3 line-clamp-2 text-sm text-slate-600">{{ g.description || '—' }}</p>
        <span class="mt-3 block rounded-xl bg-agora-orange/10 py-2 text-center text-sm font-bold text-agora-orange">Rejoindre la discussion</span>
      </NuxtLink>
    </div>
    <NuxtLink to="/forums" class="btn-primary mt-8 px-6 py-3"><i class="pi pi-compass" /> Voir tous les forums</NuxtLink>
  </section>

  <!-- Questions récentes -->
  <section v-if="recentQuestions.length" class="mx-auto max-w-4xl px-4 py-16 text-center">
    <h2 class="font-display text-2xl font-bold md:text-3xl">Questions récentes</h2>
    <div class="mt-8 divide-y divide-slate-100 overflow-hidden rounded-2xl border border-slate-200 bg-white text-left shadow-sm">
      <NuxtLink v-for="q in recentQuestions" :key="q.id" :to="`/discussion/${q.id}`" class="flex items-start gap-4 p-4 transition hover:bg-slate-50">
        <div class="flex shrink-0 flex-col items-center text-slate-400">
          <i class="pi pi-chevron-up text-xs" />
          <span class="font-display text-sm font-extrabold" :class="q.answer_count ? 'text-agora-green' : 'text-slate-500'">{{ q.answer_count }}</span>
          <i class="pi pi-chevron-down text-xs" />
        </div>
        <div class="min-w-0">
          <h3 class="font-bold leading-snug">{{ q.title }}</h3>
          <p class="mt-0.5 text-xs text-slate-400">
            Posté par {{ q.author?.display_name || q.author?.username }} · {{ timeAgo(q.created_at) }} · {{ q.answer_count }} réponses ·
            <span class="text-agora-orange">{{ q.group_name }}</span>
          </p>
        </div>
      </NuxtLink>
    </div>
    <NuxtLink to="/forums" class="btn-outline mt-8 px-6 py-3">Voir plus de questions</NuxtLink>
  </section>
  </div>
  </div>
</template>
