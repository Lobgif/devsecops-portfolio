<script setup lang="ts">
const props = defineProps<{ to?: string; label?: string }>()
const router = useRouter()
function go() {
  if (props.to) router.push(props.to)
  else router.back()
}
</script>

<template>
  <button class="mb-4 inline-flex items-center gap-1.5 text-sm text-slate-500 transition hover:text-agora-green" @click="go">
    <i class="pi pi-arrow-left" /> {{ label || 'Retour' }}
  </button>
</template>
