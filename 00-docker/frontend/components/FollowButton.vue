<script setup lang="ts">
const props = defineProps<{ targetType: 'group' | 'discussion'; targetId: string }>()
const api = useApi()
const auth = useAuthStore()
const following = ref(false)
const busy = ref(false)

onMounted(async () => {
  if (!auth.isAuthenticated) return
  try {
    following.value = (await api('/forum/follow/status', {
      params: { target_type: props.targetType, target_id: props.targetId },
    })).following
  } catch {}
})

async function toggle() {
  if (!auth.isAuthenticated) return navigateTo('/login')
  busy.value = true
  try {
    if (following.value) {
      await api('/forum/follow', { method: 'DELETE', params: { target_type: props.targetType, target_id: props.targetId } })
      following.value = false
    } else {
      await api('/forum/follow', { method: 'POST', body: { target_type: props.targetType, target_id: props.targetId } })
      following.value = true
    }
  } catch {} finally { busy.value = false }
}
</script>

<template>
  <button class="text-sm" :class="following ? 'btn-ghost border border-agora-green text-agora-green' : 'btn-outline'"
          :disabled="busy" @click="toggle">
    <i :class="['pi', following ? 'pi-check' : 'pi-bell']" /> {{ following ? 'Suivi' : 'Suivre' }}
  </button>
</template>
