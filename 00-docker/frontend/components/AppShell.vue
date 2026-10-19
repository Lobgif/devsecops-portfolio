<script setup lang="ts">
// Coquille d'application : sidebar gauche (si connecté) + contenu + rail droit optionnel.
const auth = useAuthStore()
const slots = useSlots()
onMounted(() => auth.load())
</script>

<template>
  <div class="mx-auto flex w-full max-w-[1200px] gap-7 px-4 py-7">
    <ClientOnly>
      <UserSidebar v-if="auth.isAuthenticated" />
    </ClientOnly>

    <main class="min-w-0 flex-1">
      <slot />
    </main>

    <aside v-if="slots.right" class="hidden w-[300px] shrink-0 xl:block">
      <div class="sticky top-[88px] flex flex-col gap-4">
        <slot name="right" />
      </div>
    </aside>
  </div>
</template>
