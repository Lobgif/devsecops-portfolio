<script setup lang="ts">
definePageMeta({ layout: 'admin' })
useSeoMeta({ title: 'Admin — Statistiques', robots: 'noindex' })
const api = useApi()

const { data: s } = await useAsyncData('admin-statistiques', () => api('/community/stats').catch(() => null))

const metrics = computed(() => s.value ? [
  { label: 'Membres', value: s.value.users, icon: 'pi-users', cls: 'text-agora-orange bg-agora-orange/10' },
  { label: 'Groupes', value: s.value.groups, icon: 'pi-comments', cls: 'text-agora-green bg-agora-green/10' },
  { label: 'Discussions', value: s.value.discussions, icon: 'pi-question-circle', cls: 'text-sky-600 bg-sky-100' },
  { label: 'Réponses', value: s.value.posts, icon: 'pi-reply', cls: 'text-violet-600 bg-violet-100' },
  { label: 'Réponses IA', value: s.value.ai_answers, icon: 'pi-sparkles', cls: 'text-amber-600 bg-amber-100' },
] : [])

const maxCat = computed(() => Math.max(1, ...((s.value?.by_category || []).map((c: any) => c.count))))
const palette = ['#F77F00', '#009E60', '#2563eb', '#7c3aed', '#dc2626', '#0891b2', '#ca8a04']
</script>

<template>
  <div>
    <h1 class="font-display text-2xl font-bold">📊 Statistiques</h1>
    <p class="mt-1 text-slate-500">Activité de la plateforme en temps réel.</p>

    <div class="mt-6 grid grid-cols-2 gap-4 sm:grid-cols-5">
      <div v-for="m in metrics" :key="m.label" class="card text-center">
        <span class="mx-auto grid h-10 w-10 place-items-center rounded-xl" :class="m.cls"><i :class="['pi', m.icon]" /></span>
        <p class="mt-2 text-2xl font-bold">{{ m.value }}</p>
        <p class="text-xs text-slate-500">{{ m.label }}</p>
      </div>
    </div>

    <div class="card mt-6">
      <h2 class="font-semibold">Groupes par catégorie</h2>
      <div class="mt-4 space-y-3">
        <div v-for="(c, i) in s?.by_category || []" :key="c.category" class="flex items-center gap-3">
          <span class="w-40 truncate text-sm text-slate-600">{{ c.category }}</span>
          <div class="h-3 flex-1 overflow-hidden rounded-full bg-slate-100">
            <div class="h-full rounded-full" :style="{ width: (c.count / maxCat * 100) + '%', background: palette[i % palette.length] }" />
          </div>
          <span class="w-6 text-right text-sm font-semibold">{{ c.count }}</span>
        </div>
      </div>
    </div>
  </div>
</template>
