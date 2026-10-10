<script setup lang="ts">
interface FeedItem {
  id: string; title: string; excerpt: string
  group_id: string; group_name: string; category: string
  author: { username: string; avatar_url?: string | null; display_name?: string }
  answer_count: number; created_at: string
}
const props = defineProps<{ item: FeedItem }>()

const isNew = computed(() => (Date.now() - new Date(props.item.created_at).getTime()) < 864e5) // < 24 h
const isHot = computed(() => props.item.answer_count >= 10)
const st = computed(() => categoryStyle(props.item.category))
</script>

<template>
  <NuxtLink :to="`/discussion/${item.id}`"
            class="block rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md">
    <div class="flex items-start justify-between gap-3">
      <div class="flex min-w-0 items-center gap-2.5">
        <img v-if="item.author.avatar_url" :src="item.author.avatar_url" class="h-9 w-9 rounded-full object-cover" />
        <span v-else class="grid h-9 w-9 shrink-0 place-items-center rounded-full text-xs font-bold text-white" :class="st.solid">
          {{ initials(item.author.display_name || item.author.username) }}
        </span>
        <div class="min-w-0">
          <p class="truncate text-sm font-bold leading-tight">{{ item.author.display_name || item.author.username }}</p>
          <p class="truncate text-xs text-slate-400">{{ timeAgo(item.created_at) }} · {{ item.group_name }}</p>
        </div>
      </div>
      <span v-if="isHot" class="shrink-0 rounded-full bg-agora-orange/10 px-2.5 py-0.5 text-[11px] font-bold text-agora-orange">Populaire</span>
      <span v-else-if="isNew" class="shrink-0 rounded-full bg-sky-50 px-2.5 py-0.5 text-[11px] font-bold text-sky-600">Nouveau</span>
    </div>

    <h3 class="mt-3 text-[17px] font-extrabold leading-snug">{{ item.title }}</h3>
    <p class="mt-1.5 line-clamp-3 text-sm text-slate-600">{{ item.excerpt }}</p>

    <div class="mt-3 flex items-center gap-5 text-sm text-slate-400">
      <span class="inline-flex items-center gap-1.5"><i class="pi pi-comment" /> {{ item.answer_count }}</span>
      <span class="ml-auto font-bold text-agora-orange">Répondre →</span>
    </div>
  </NuxtLink>
</template>
