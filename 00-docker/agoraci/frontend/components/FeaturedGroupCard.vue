<script setup lang="ts">
interface Group {
  id: string; name: string; description: string; category: string
  member_count: number; discussion_count: number; is_private?: boolean; badges?: string[]
}
const props = defineProps<{ group: Group }>()
const st = computed(() => categoryStyle(props.group.category))
// Le ruban reprend le 1er badge du groupe (Populaire, À la une…), sinon « Vedette ».
const ribbon = computed(() => (props.group.badges && props.group.badges[0]) || 'Vedette')
</script>

<template>
  <NuxtLink :to="`/groups/${group.id}`"
            class="relative block overflow-hidden rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition hover:-translate-y-1 hover:shadow-lg">
    <!-- Ruban diagonal -->
    <span class="absolute -right-9 top-3.5 w-32 rotate-45 py-1 text-center text-[11px] font-extrabold tracking-wide text-white shadow"
          :class="st.solid">{{ ribbon }}</span>

    <div class="flex items-start gap-3">
      <span class="grid h-11 w-11 shrink-0 place-items-center rounded-xl text-sm font-extrabold text-white" :class="st.solid">
        {{ initials(group.name) }}
      </span>
      <div class="min-w-0">
        <h3 class="truncate pr-8 text-base font-extrabold leading-tight">{{ group.name }}</h3>
        <p class="mt-0.5 text-xs font-semibold uppercase tracking-wide" :class="st.chip.split(' ')[1]">{{ group.category }}</p>
      </div>
    </div>

    <p class="mt-3 line-clamp-2 min-h-[40px] text-sm text-slate-600">{{ group.description || '—' }}</p>

    <div class="mt-3 flex gap-4 text-[13px] text-slate-500">
      <span><b class="font-bold text-agora-ink">{{ group.member_count }}</b> membres</span>
      <span><b class="font-bold text-agora-ink">{{ group.discussion_count }}</b> discussions</span>
    </div>

    <div class="mt-3 flex items-center justify-between">
      <span class="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500">
        <span class="h-2 w-2 rounded-full bg-agora-green" /> Actif
      </span>
      <span class="rounded-lg px-4 py-1.5 text-[13px] font-bold text-white" :class="st.solid">Rejoindre</span>
    </div>
  </NuxtLink>
</template>
