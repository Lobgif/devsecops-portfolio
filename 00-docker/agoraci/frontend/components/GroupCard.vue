<script setup lang="ts">
interface Member { username: string; avatar_url?: string | null }
interface Group {
  id: string; name: string; description: string; category: string
  member_count: number; discussion_count: number
  is_private?: boolean; badges?: string[]
  last_activity_at?: string | null; preview_members?: Member[]
}
const props = defineProps<{ group: Group }>()
const st = computed(() => categoryStyle(props.group.category))

// Couleurs d'avatars (déterministes par position) pour les membres sans photo.
const AV = ['bg-agora-orange', 'bg-indigo-500', 'bg-rose-500', 'bg-agora-green', 'bg-amber-500', 'bg-teal-500']
const previews = computed(() => (props.group.preview_members || []).slice(0, 3))
const overflow = computed(() => Math.max(0, (props.group.member_count || 0) - previews.value.length))
</script>

<template>
  <NuxtLink :to="`/groups/${group.id}`"
            class="group block overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm transition hover:-translate-y-1 hover:shadow-lg">
    <!-- Bandeau dégradé par catégorie -->
    <div class="relative flex h-24 flex-col justify-between bg-gradient-to-br px-4 py-3" :class="st.grad">
      <span class="self-start rounded-full bg-white/90 px-2.5 py-0.5 text-[11px] font-bold text-agora-ink">{{ group.category }}</span>
      <h3 class="pr-6 text-[17px] font-extrabold leading-tight text-white [text-shadow:0_1px_6px_rgba(0,0,0,.18)]">{{ group.name }}</h3>
      <i v-if="group.is_private" class="pi pi-lock absolute right-3 top-3 text-white/90" title="Groupe privé" />
      <span v-for="b in (group.badges || []).slice(0, 1)" :key="b"
            class="absolute right-3 bottom-3 rounded-full bg-white/90 px-2 py-0.5 text-[10px] font-bold text-agora-ink">{{ b }}</span>
    </div>

    <div class="px-4 pb-4 pt-3">
      <p class="line-clamp-2 min-h-[40px] text-sm text-slate-600">{{ group.description || '—' }}</p>

      <div class="mt-3 flex items-center gap-2">
        <div class="flex">
          <span v-for="(m, i) in previews" :key="m.username"
                class="-ml-2 grid h-6 w-6 place-items-center rounded-full border-2 border-white text-[10px] font-bold text-white first:ml-0"
                :class="AV[i % AV.length]" :title="m.username">
            <img v-if="m.avatar_url" :src="m.avatar_url" class="h-full w-full rounded-full object-cover" :alt="m.username" />
            <template v-else>{{ initials(m.username) }}</template>
          </span>
          <span v-if="overflow" class="-ml-2 grid h-6 w-6 place-items-center rounded-full border-2 border-white bg-slate-400 text-[10px] font-bold text-white">+{{ overflow }}</span>
        </div>
        <span class="text-xs font-semibold text-slate-500">{{ group.member_count }} membres</span>
        <span class="ml-auto rounded-full px-2 py-0.5 text-[11px] font-bold"
              :class="group.is_private ? 'bg-slate-100 text-slate-500' : 'bg-agora-green/10 text-agora-green-dark'">
          {{ group.is_private ? 'Privé' : 'Public' }}
        </span>
      </div>

      <div class="mt-3 flex items-center justify-between border-t border-slate-100 pt-3">
        <span class="text-sm font-bold text-agora-orange transition group-hover:gap-2">Voir le groupe →</span>
        <span class="text-xs text-slate-400">
          {{ group.discussion_count }} discussions<template v-if="group.last_activity_at"> · {{ timeAgo(group.last_activity_at) }}</template>
        </span>
      </div>
    </div>
  </NuxtLink>
</template>
