<script setup lang="ts">
const route = useRoute()
const api = useApi()
const auth = useAuthStore()
const { public: pub } = useRuntimeConfig()
const id = route.params.id as string

const { data: group, refresh: refreshGroup } = await useAsyncData(`group-${id}`, () => api(`/forum/group/${id}`).catch(() => null))

// Pagination des discussions : page 1 en SSR, « Voir plus » charge la suite et l'ajoute
const PAGE = 10
const offset = ref(0)
const extra = ref<any[]>([])
const noMore = ref(false)
const privateBlocked = ref(false)
const { data: page1, refresh } = await useAsyncData(`disc-${id}`, async () => {
  try {
    return await api(`/forum/discussions/${id}?limit=${PAGE}&offset=0`)
  } catch (e: any) {
    if ((e?.status || e?.statusCode || e?.response?.status) === 403) privateBlocked.value = true
    return []
  }
})

const joining = ref(false)
async function joinGroup() {
  if (!auth.isAuthenticated) return navigateTo('/login')
  joining.value = true
  try {
    await api(`/forum/groups/${id}/join`, { method: 'POST' })
    privateBlocked.value = false
    extra.value = []; offset.value = 0
    await Promise.all([refresh(), refreshGroup()])  // met à jour my_role → « Rejoindre » disparaît
  } catch (e: any) { alert(e?.data?.detail || 'Erreur') }
  finally { joining.value = false }
}
// Partage : Web Share API (mobile → WhatsApp, etc.) sinon copie du lien dans le presse-papiers
const shared = ref(false)
async function shareGroup() {
  const url = `${pub.siteUrl}/groups/${id}`
  try {
    if (typeof navigator !== 'undefined' && navigator.share) {
      await navigator.share({ title: group.value?.name || 'Groupe', text: group.value?.description || '', url })
    } else {
      await navigator.clipboard.writeText(url)
      shared.value = true
      setTimeout(() => (shared.value = false), 2000)
    }
  } catch { /* partage annulé par l'utilisateur — rien à faire */ }
}

const discussions = computed(() => [...(page1.value || []), ...extra.value])
watchEffect(() => { noMore.value = (page1.value || []).length < PAGE })
async function loadMore() {
  offset.value += PAGE
  const more = await api(`/forum/discussions/${id}?limit=${PAGE}&offset=${offset.value}`).catch(() => [])
  extra.value.push(...more)
  if (more.length < PAGE) noMore.value = true
}

useSeoMeta({
  title: () => group.value?.name || 'Groupe',
  description: () => group.value?.description,
  ogUrl: `${pub.siteUrl}/groups/${id}`,
})

const form = reactive({ title: '', body: '' })
const error = ref('')
const sending = ref(false)
const published = ref('')

async function createDiscussion() {
  sending.value = true
  error.value = ''; published.value = ''
  try {
    const d = await api('/forum/discussions', { method: 'POST', body: { group_id: id, ...form } })
    form.title = ''; form.body = ''
    extra.value = []; offset.value = 0
    await Promise.all([refresh(), refreshGroup()])
    published.value = 'Votre question a été publiée ✓'
    setTimeout(() => (published.value = ''), 4000)
    if (d?.id) navigateTo(`/discussion/${d.id}`)
  } catch (e: any) {
    error.value = e?.data?.detail || 'Erreur (connecté ?)'
  } finally {
    sending.value = false
  }
}

// --- Gestion des membres (admins de groupe uniquement) ---
// useAsyncData (et non onMounted) car le setup est async (await ci-dessus) :
// 401/403 → null → panneau masqué. SSR forwarde le cookie → rendu côté serveur si admin.
const { data: members, refresh: refreshMembers } = await useAsyncData(
  `members-${id}`,
  () => api(`/forum/groups/${id}/members`).catch(() => null),
)
async function setRole(userId: string, role: string) {
  await api(`/forum/groups/${id}/members/${userId}/role`, { method: 'POST', body: { role } }).catch(() => {})
  await refreshMembers()
  await loadPublicMembers()
}

// Bouton « Membres » : panneau repliable + pagination
const showMembers = ref(false)
const memberLimit = ref(10)
const publicMembers = ref<any[]>([])
const canManage = computed(() => !!members.value)  // l'appel admin a réussi → créateur/admin/super-admin
async function loadPublicMembers() { publicMembers.value = await api(`/forum/groups/${id}/members/list`).catch(() => []) }
function toggleMembers() {
  showMembers.value = !showMembers.value
  if (showMembers.value && !publicMembers.value.length) loadPublicMembers()
}
</script>

<template>
  <AppShell>
    <NuxtLink to="/forums" class="inline-flex items-center gap-1 text-sm font-medium text-agora-orange">
      <i class="pi pi-arrow-left text-xs" /> Forums
    </NuxtLink>

    <div v-if="group" class="mt-3 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
      <!-- Hero dégradé par catégorie -->
      <div class="bg-gradient-to-br px-6 py-6 text-white" :class="categoryStyle(group.category).grad">
        <span class="chip bg-white/90 text-agora-ink">{{ group.category }}</span>
        <h1 class="mt-2 font-display text-3xl font-extrabold [text-shadow:0_1px_8px_rgba(0,0,0,.15)]">
          <i v-if="group.is_private" class="pi pi-lock text-xl" title="Groupe privé" /> {{ group.name }}
        </h1>
        <p v-if="group.description" class="mt-1 max-w-2xl text-sm text-white/90">{{ group.description }}</p>
        <div class="mt-3 flex flex-wrap items-center gap-4 text-sm font-semibold">
          <span><i class="pi pi-users" /> {{ group.member_count }} membres</span>
          <span v-for="b in group.badges" :key="b" class="rounded-full bg-white/90 px-2.5 py-0.5 text-[11px] font-bold text-agora-ink">{{ b }}</span>
        </div>
      </div>
      <!-- Barre de contrôles -->
      <div class="flex flex-wrap items-center gap-2 border-t border-slate-100 p-4">
        <button class="btn-ghost border text-sm" :class="showMembers ? 'text-agora-green' : ''" @click="toggleMembers">
          <i class="pi pi-users" /> Membres ({{ group.member_count }})
        </button>
        <NuxtLink v-if="group.my_role" :to="`/groups/gouvernance?g=${group.id}`" class="btn-ghost border text-sm">
          <i class="pi pi-sitemap" /> Gouvernance
        </NuxtLink>
        <span v-if="group.my_role" class="chip border border-agora-green/40 bg-agora-green/10 text-agora-green">
          <i class="pi pi-check" /> Membre<template v-if="group.my_role !== 'member'"> · {{ group.my_role }}</template>
        </span>
        <button v-else-if="auth.isAuthenticated" class="btn-primary text-sm" :disabled="joining" @click="joinGroup">
          <i class="pi pi-user-plus" /> Rejoindre
        </button>
        <NuxtLink v-else to="/login" class="btn-primary text-sm">
          <i class="pi pi-user-plus" /> Rejoindre
        </NuxtLink>
        <div class="ml-auto flex items-center gap-2">
          <button class="btn-ghost border text-sm" :class="shared ? 'text-agora-green' : ''" @click="shareGroup">
            <i :class="shared ? 'pi pi-check' : 'pi pi-share-alt'" /> {{ shared ? 'Lien copié' : 'Partager' }}
          </button>
          <FollowButton target-type="group" :target-id="group.id" />
        </div>
      </div>
    </div>

    <div v-if="group?.deletion_at" class="mt-3 rounded-xl border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-700">
      <i class="pi pi-exclamation-triangle" /> Ce groupe est <strong>programmé pour suppression</strong>
      le {{ new Date(group.deletion_at).toLocaleString('fr-FR') }}.
      <span v-if="group.deletion_reason">Motif : {{ group.deletion_reason }}.</span>
    </div>

    <!-- Nouvelle discussion -->
    <div v-if="auth.isAuthenticated" class="card mt-8">
      <h2 class="font-semibold">Poser une question</h2>
      <div class="mt-3 space-y-3">
        <input v-model="form.title" placeholder="Titre de votre question" class="w-full rounded-xl border px-3 py-2" />
        <textarea v-model="form.body" rows="3" placeholder="Détaillez votre situation…" class="w-full rounded-xl border px-3 py-2" />
        <p v-if="error" class="text-sm text-red-600">{{ error }}</p>
        <p v-if="published" class="text-sm text-agora-green"><i class="pi pi-check-circle" /> {{ published }}</p>
        <button class="btn-primary" :disabled="sending || !form.title || !form.body" @click="createDiscussion">Publier</button>
      </div>
    </div>
    <div v-else class="card mt-8 flex flex-col items-center gap-2 text-center">
      <i class="pi pi-users text-2xl text-agora-orange" />
      <h2 class="font-semibold">Rejoignez la discussion</h2>
      <p class="max-w-md text-sm text-slate-500">Créez un compte gratuit pour poser vos questions et participer à ce groupe.</p>
      <div class="mt-1 flex flex-wrap justify-center gap-2">
        <NuxtLink to="/register" class="btn-primary"><i class="pi pi-user-plus" /> S'inscrire gratuitement</NuxtLink>
        <NuxtLink to="/login" class="btn-outline">J'ai déjà un compte</NuxtLink>
      </div>
    </div>

    <!-- Panneau membres (déclenché par le bouton « Membres ») -->
    <div v-if="showMembers" class="card mt-6">
      <div class="flex items-center justify-between">
        <h2 class="font-semibold">Membres ({{ publicMembers.length }})</h2>
        <span v-if="canManage" class="text-xs text-slate-400">Vous pouvez promouvoir/rétrograder · exclusion = vote communautaire</span>
      </div>
      <div class="mt-3 divide-y divide-slate-100">
        <div v-for="m in publicMembers.slice(0, memberLimit)" :key="m.user_id" class="flex items-center gap-3 py-2">
          <NuxtLink :to="`/u/${m.user_id}`" class="grid h-8 w-8 shrink-0 place-items-center overflow-hidden rounded-full bg-agora-green text-sm font-semibold text-white">
            <img v-if="m.avatar_url" :src="m.avatar_url" class="h-full w-full object-cover" />
            <template v-else>{{ (m.username || '?').charAt(0).toUpperCase() }}</template>
          </NuxtLink>
          <NuxtLink :to="`/u/${m.user_id}`" class="min-w-0 flex-1 truncate text-sm hover:underline">@{{ m.username }}</NuxtLink>
          <span class="chip" :class="m.role === 'creator' ? 'bg-agora-orange/10 text-agora-orange' : 'bg-slate-100 text-slate-500'">{{ m.role }}</span>
          <template v-if="canManage && m.role !== 'creator'">
            <button v-if="m.role === 'member'" class="btn-ghost text-xs" @click="setRole(m.user_id, 'admin')">Promouvoir</button>
            <button v-else class="btn-ghost text-xs" @click="setRole(m.user_id, 'member')">Rétrograder</button>
          </template>
        </div>
      </div>
      <div v-if="publicMembers.length > memberLimit" class="mt-3 text-center">
        <button class="btn-outline text-sm" @click="memberLimit += 10"><i class="pi pi-chevron-down" /> Voir plus</button>
      </div>
    </div>

    <!-- Chat temps réel -->
    <div class="mt-8">
      <ClientOnly>
        <GroupChat :group-id="id" />
      </ClientOnly>
    </div>

    <!-- Liste des discussions -->
    <h2 class="mt-10 font-display text-xl font-bold">Discussions</h2>
    <div v-if="privateBlocked" class="card mt-4 text-center">
      <i class="pi pi-lock text-2xl text-slate-300" />
      <p class="mt-2 text-slate-600">Ce groupe est privé. Rejoignez-le pour voir les discussions.</p>
      <button class="btn-primary mt-3" :disabled="joining" @click="joinGroup"><i class="pi pi-user-plus" /> Rejoindre le groupe</button>
    </div>
    <div v-else-if="discussions?.length" class="mt-4 space-y-3">
      <NuxtLink
        v-for="d in discussions" :key="d.id" :to="`/discussion/${d.id}`"
        class="card block transition hover:-translate-y-0.5 hover:shadow-md"
      >
        <h3 class="font-semibold text-agora-ink">{{ d.title }}</h3>
        <p class="mt-1 line-clamp-2 text-sm text-slate-600">{{ d.body }}</p>
      </NuxtLink>
      <div v-if="!noMore" class="text-center">
        <button class="btn-outline" @click="loadMore"><i class="pi pi-chevron-down" /> Voir plus</button>
      </div>
    </div>
    <p v-else class="mt-4 text-slate-500">Aucune discussion pour le moment.</p>
  </AppShell>
</template>
