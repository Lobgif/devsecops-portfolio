<script setup lang="ts">
const { public: pub } = useRuntimeConfig()
useSeoMeta({
  title: 'À propos',
  description: "Jamakan : la plateforme citoyenne collaborative qui rend l'information et l'entraide accessibles à tous, sur tous les sujets du quotidien ivoirien.",
  ogUrl: `${pub.siteUrl}/about`,
})
const api = useApi()
const { data: settings } = await useAsyncData('about-settings', () => api('/settings').catch(() => ({})))
const showTeam = computed(() => String(settings.value?.about_show_team ?? '1') === '1')

const values = [
  { icon: 'pi-globe', title: 'Accessibilité', text: 'Une information claire, sans jargon, accessible à tous les Ivoiriens.' },
  { icon: 'pi-verified', title: 'Fiabilité', text: 'Des réponses sourcées, validées par la communauté et les experts.' },
  { icon: 'pi-users', title: 'Communauté', text: 'L’entraide et le partage de connaissances au cœur du projet.' },
  { icon: 'pi-shield', title: 'Respect', text: 'Une modération communautaire transparente, sans censure arbitraire.' },
]
const team = [
  { role: 'Fondateur', name: 'Équipe fondatrice' },
  { role: 'Équipe technique', name: 'Développement & IA' },
  { role: 'Modération', name: 'Communauté' },
]
</script>

<template>
  <div>
    <!-- Hero -->
    <section class="bg-gradient-to-b from-agora-orange/5 to-transparent py-16 text-center">
      <h1 class="font-display text-3xl font-extrabold md:text-4xl">À propos de <span class="text-agora-orange">Jamakan</span></h1>
      <p class="mx-auto mt-3 max-w-2xl px-4 text-slate-600">Découvrez notre mission, notre vision et notre engagement à créer un espace d’échange et de partage pour tous les Ivoiriens.</p>
    </section>

    <!-- Notre mission -->
    <section class="mx-auto max-w-4xl px-4 py-12">
      <h2 class="font-display text-2xl font-bold">Notre mission</h2>
      <div class="mt-4 space-y-4 text-slate-700">
        <p>
          <strong>Jamakan</strong> est née d’une vision simple mais puissante : créer un espace numérique où chaque Ivoirien
          peut accéder à l’information, partager ses connaissances et contribuer au développement collectif de notre société.
        </p>
        <p>
          Dans un monde où l’information est abondante mais souvent dispersée ou inaccessible, nous avons conçu une plateforme
          qui rassemble l’intelligence collective de notre communauté pour répondre aux questions du quotidien —
          démarches administratives, santé, éducation, emploi, business, droit, famille…
        </p>
        <p class="rounded-xl bg-agora-orange/10 p-4 text-sm text-agora-orange">
          ℹ️ Les informations fournies sont à but informatif et ne remplacent pas l’avis d’un professionnel qualifié.
        </p>
      </div>
    </section>

    <!-- Nos valeurs -->
    <section class="bg-slate-100/60 py-12">
      <div class="mx-auto max-w-5xl px-4 text-center">
        <h2 class="font-display text-2xl font-bold">Nos valeurs</h2>
        <div class="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div v-for="v in values" :key="v.title" class="card text-left">
            <span class="grid h-11 w-11 place-items-center rounded-xl bg-agora-green/10 text-agora-green"><i :class="['pi', v.icon]" /></span>
            <h3 class="mt-3 font-bold">{{ v.title }}</h3>
            <p class="mt-1 text-sm text-slate-500">{{ v.text }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- Notre équipe (masquable en admin via about_show_team) -->
    <section v-if="showTeam" class="mx-auto max-w-5xl px-4 py-12 text-center">
      <h2 class="font-display text-2xl font-bold">Notre équipe</h2>
      <p class="mt-2 text-slate-500">Une équipe engagée au service de la communauté ivoirienne.</p>
      <div class="mt-8 grid gap-4 sm:grid-cols-3">
        <div v-for="t in team" :key="t.role" class="card text-center">
          <span class="mx-auto grid h-16 w-16 place-items-center rounded-full bg-gradient-to-br from-agora-orange to-agora-green text-xl font-bold text-white"><i class="pi pi-user" /></span>
          <h3 class="mt-3 font-bold">{{ t.name }}</h3>
          <p class="text-sm text-agora-orange">{{ t.role }}</p>
        </div>
      </div>
    </section>

    <!-- CTA -->
    <section class="mx-auto max-w-4xl px-4 pb-16">
      <div class="rounded-2xl bg-gradient-to-r from-agora-orange to-agora-green p-8 text-center text-white">
        <h2 class="font-display text-2xl font-bold">Rejoignez la communauté</h2>
        <p class="mx-auto mt-2 max-w-xl text-white/90">Posez vos questions, partagez votre expérience et aidez d’autres Ivoiriens au quotidien.</p>
        <div class="mt-5 flex flex-wrap justify-center gap-3">
          <NuxtLink to="/register" class="rounded-xl bg-white px-6 py-3 font-semibold text-agora-orange">S’inscrire</NuxtLink>
          <NuxtLink to="/forums" class="rounded-xl border border-white/70 px-6 py-3 font-semibold text-white">Explorer les forums</NuxtLink>
        </div>
      </div>
    </section>
  </div>
</template>
