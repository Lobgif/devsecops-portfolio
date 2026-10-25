<script setup lang="ts">
interface Contribution {
  answers: number; tier: string; next_tier?: string | null
  remaining: number; progress: number
}
defineProps<{ contribution?: Contribution | null }>()
</script>

<template>
  <div v-if="contribution" class="rounded-2xl border border-[#ffe6cc] bg-gradient-to-b from-[#fff8f0] to-white p-4 shadow-sm">
    <p class="text-[11px] font-bold uppercase tracking-wide text-slate-400">Votre niveau</p>
    <div class="mt-1.5 flex items-center gap-2 font-bold">
      <i class="pi pi-star-fill text-sm text-agora-orange" /> {{ contribution.tier }}
      <span class="ml-auto text-xs font-semibold text-slate-500">{{ contribution.answers }} rép.</span>
    </div>
    <div class="my-3 h-[7px] overflow-hidden rounded-full bg-slate-100">
      <span class="block h-full rounded-full bg-gradient-to-r from-agora-orange to-[#ffb15e]"
            :style="{ width: contribution.progress + '%' }" />
    </div>
    <p v-if="contribution.next_tier" class="text-xs text-slate-500">
      {{ contribution.remaining }} réponse{{ contribution.remaining > 1 ? 's' : '' }} pour atteindre <b>{{ contribution.next_tier }}</b>
    </p>
    <p v-else class="text-xs text-agora-green"><i class="pi pi-check-circle" /> Palier maximal atteint 🎉</p>
  </div>
</template>
