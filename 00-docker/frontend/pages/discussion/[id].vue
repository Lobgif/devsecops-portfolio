<script setup lang="ts">
const route = useRoute()
const api = useApi()
const auth = useAuthStore()
const { public: pub } = useRuntimeConfig()
const id = route.params.id as string

const { data: disc, refresh } = await useAsyncData(`discussion-${id}`, () =>
  api(`/forum/discussion/${id}`).catch(() => null),
)

useSeoMeta({
  title: () => disc.value?.title || 'Discussion',
  description: () => disc.value?.body?.slice(0, 160),
  ogUrl: `${pub.siteUrl}/discussion/${id}`,
})

// Donnée structurée Q/R pour le SEO
useHead(() => ({
  script: disc.value ? [{
    type: 'application/ld+json',
    innerHTML: JSON.stringify({
      '@context': 'https://schema.org', '@type': 'QAPage',
      mainEntity: {
        '@type': 'Question', name: disc.value.title, text: disc.value.body,
        answerCount: disc.value.posts?.length || 0,
      },
    }),
  }] : [],
}))

const reply = ref('')
const aiLoading = ref(false)
const busy = ref(false)

// --- Affichage uniquement : onglets de tri + repérage de la meilleure réponse ---
const tab = ref<'best' | 'recent' | 'ai'>('best')
const sortedPosts = computed<any[]>(() => {
  const posts: any[] = disc.value?.posts || []
  if (tab.value === 'ai') return posts.filter(p => p.is_ai)
  if (tab.value === 'recent') return [...posts].sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
  return [...posts].sort((a, b) => b.score - a.score)
})
const bestId = computed<string | null>(() => {
  const scored: any[] = (disc.value?.posts || []).filter((p: any) => p.score > 0)
  return scored.length ? scored.reduce((m, p) => (p.score > m.score ? p : m)).id : null
})

async function vote(postId: string, value: number) {
  if (!auth.isAuthenticated) return navigateTo('/login')
  await api('/forum/votes', { method: 'POST', body: { post_id: postId, value } }).catch(() => {})
  await refresh()
}
async function report(postId: string) {
  if (!auth.isAuthenticated) return navigateTo('/login')
  await api(`/forum/posts/${postId}/report`, { method: 'POST' }).catch(() => {})
  alert('Merci, le contenu a été signalé.')
}
async function sendReply() {
  if (!reply.value) return
  busy.value = true
  try {
    await api('/forum/posts', { method: 'POST', body: { discussion_id: id, body: reply.value } })
    reply.value = ''
    await refresh()
  } finally { busy.value = false }
}
const imgBusy = ref(false)
async function attachImage(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return
  imgBusy.value = true
  try {
    const fd = new FormData()
    fd.append('file', file); fd.append('prefix', 'uploads')
    const r = await api('/uploads', { method: 'POST', body: fd })
    reply.value += `\n![image](${r.url})\n`
  } catch (e: any) { alert(e?.data?.detail || 'Échec de l\'upload.') }
  finally { imgBusy.value = false }
}
const aiError = ref('')
async function askAI() {
  aiLoading.value = true; aiError.value = ''
  try {
    await api(`/forum/discussions/${id}/ai-answer`, { method: 'POST' })
    await refresh()
  } catch (e: any) {
    aiError.value = e?.data?.detail || 'Nanan est momentanément indisponible. Réessayez.'
    setTimeout(() => (aiError.value = ''), 5000)
  } finally { aiLoading.value = false }
}

// Boucle brouillon : « Améliorer » un brouillon de Nanan = focus sur la zone de réponse humaine
function improveFromAi() {
  nextTick(() => {
    const el = document.getElementById('reply-box') as HTMLTextAreaElement | null
    el?.focus()
    el?.scrollIntoView({ behavior: 'smooth', block: 'center' })
  })
}

// --- Édition / suppression de la discussion (auteur) ---
const editingDisc = ref(false)
const discEdit = reactive({ title: '', body: '' })
function startEditDisc() { discEdit.title = disc.value.title; discEdit.body = disc.value.body; editingDisc.value = true }
async function saveDisc() {
  await api(`/forum/discussions/${id}`, { method: 'PUT', body: { title: discEdit.title, body: discEdit.body } }).catch((e) => alert(e?.data?.detail || 'Erreur'))
  editingDisc.value = false
  await refresh()
}
async function deleteDisc() {
  if (!confirm('Supprimer cette discussion et toutes ses réponses ?')) return
  const gid = disc.value.group_id
  await api(`/forum/discussions/${id}`, { method: 'DELETE' }).catch((e) => alert(e?.data?.detail || 'Erreur'))
  navigateTo(`/groups/${gid}`)
}

// --- Édition / suppression d'une réponse (auteur) ---
const editingPost = ref<string | null>(null)
const postBody = ref('')
function startEditPost(p: any) { editingPost.value = p.id; postBody.value = p.body }
async function savePost(p: any) {
  await api(`/forum/posts/${p.id}`, { method: 'PUT', body: { body: postBody.value } }).catch((e) => alert(e?.data?.detail || 'Erreur'))
  editingPost.value = null
  await refresh()
}
async function deletePost(p: any) {
  if (!confirm('Supprimer votre réponse ?')) return
  await api(`/forum/posts/${p.id}`, { method: 'DELETE' }).catch((e) => alert(e?.data?.detail || 'Erreur'))
  await refresh()
}
</script>

<template>
  <AppShell>
    <template v-if="disc">
      <NuxtLink :to="`/groups/${disc.group_id}`" class="inline-flex items-center gap-1 text-sm font-medium text-agora-orange">
        <i class="pi pi-arrow-left text-xs" /> Retour au groupe
      </NuxtLink>

      <!-- Question -->
      <article class="mt-3 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div class="flex items-start justify-between gap-3">
          <h1 v-if="!editingDisc" class="font-display text-2xl font-extrabold leading-tight">{{ disc.title }}</h1>
          <input v-else v-model="discEdit.title" class="flex-1 text-lg font-bold" />
          <FollowButton v-if="!editingDisc" target-type="discussion" :target-id="id" />
        </div>
        <template v-if="!editingDisc">
          <div class="mt-3 flex items-center gap-2.5">
            <img v-if="disc.author_avatar" :src="disc.author_avatar" class="h-8 w-8 rounded-full object-cover" />
            <span v-else class="grid h-8 w-8 place-items-center rounded-full bg-agora-green text-xs font-bold text-white">{{ initials(disc.author_username || 'M') }}</span>
            <div class="text-xs">
              <NuxtLink :to="`/u/${disc.author_id}`" class="font-semibold text-agora-ink hover:text-agora-orange">{{ disc.author_username || 'membre' }}</NuxtLink>
              <span class="text-slate-400"> · {{ timeAgo(disc.created_at) }}</span>
            </div>
          </div>
          <p class="mt-3 leading-relaxed text-slate-700" v-html="linkifyMentions(disc.body)" />
          <div v-if="disc.author_id === auth.user?.id" class="mt-3 flex gap-3 text-xs text-slate-400">
            <button class="hover:text-agora-green" @click="startEditDisc"><i class="pi pi-pencil" /> Modifier</button>
            <button class="hover:text-red-500" @click="deleteDisc"><i class="pi pi-trash" /> Supprimer</button>
          </div>
        </template>
        <div v-else class="mt-2">
          <textarea v-model="discEdit.body" rows="4" />
          <div class="mt-2 flex gap-2">
            <button class="btn-primary" @click="saveDisc">Enregistrer</button>
            <button class="btn-ghost border" @click="editingDisc = false">Annuler</button>
          </div>
        </div>
      </article>

      <!-- En-tête des réponses : onglets + Nanan -->
      <div class="mt-6 flex flex-wrap items-center gap-3">
        <h2 class="font-display text-lg font-extrabold">{{ disc.posts.length }} réponse{{ disc.posts.length > 1 ? 's' : '' }}</h2>
        <div class="flex items-center gap-1 rounded-full border border-slate-200 bg-white p-1 text-sm shadow-sm">
          <button v-for="t in [{ k: 'best', l: 'Populaires' }, { k: 'recent', l: 'Récentes' }, { k: 'ai', l: 'IA' }]" :key="t.k"
                  class="rounded-full px-3 py-1 font-semibold transition"
                  :class="tab === t.k ? 'bg-[#fff4e8] text-agora-orange' : 'text-slate-500 hover:text-agora-ink'"
                  @click="tab = t.k as any">{{ t.l }}</button>
        </div>
        <button class="btn-ghost ml-auto border" :disabled="aiLoading" @click="askAI">
          <i :class="['pi', aiLoading ? 'pi-spin pi-spinner' : 'pi-sparkles']" /> {{ aiLoading ? 'Nanan réfléchit…' : 'Demander à Nanan' }}
        </button>
      </div>
      <p v-if="aiError" class="mt-2 text-right text-sm text-amber-600"><i class="pi pi-exclamation-triangle" /> {{ aiError }}</p>

      <!-- Réponses -->
      <div class="mt-4 space-y-4">
        <article v-for="p in sortedPosts" :key="p.id"
                 class="flex gap-4 rounded-2xl border bg-white p-5 shadow-sm transition"
                 :class="p.id === bestId ? 'border-agora-green/50 ring-1 ring-agora-green/30' : p.is_ai ? 'border-agora-green/30 bg-agora-green/5' : 'border-slate-200'">
          <!-- Colonne de vote -->
          <div class="flex shrink-0 flex-col items-center gap-1 text-slate-400">
            <button class="grid h-8 w-8 place-items-center rounded-lg transition hover:bg-agora-green/10 hover:text-agora-green" title="Utile" @click="vote(p.id, 1)"><i class="pi pi-chevron-up" /></button>
            <span class="font-display text-lg font-extrabold" :class="p.score > 0 ? 'text-agora-green' : p.score < 0 ? 'text-red-500' : 'text-slate-500'">{{ p.score }}</span>
            <button class="grid h-8 w-8 place-items-center rounded-lg transition hover:bg-red-50 hover:text-red-500" title="Pas utile" @click="vote(p.id, -1)"><i class="pi pi-chevron-down" /></button>
          </div>

          <!-- Contenu -->
          <div class="min-w-0 flex-1">
            <div class="mb-2 flex flex-wrap items-center gap-2">
              <span v-if="p.id === bestId" class="chip bg-agora-green/10 text-agora-green"><i class="pi pi-check-circle" /> Meilleure réponse</span>
              <span v-if="p.is_ai" class="chip font-semibold text-white"
                    :class="p.score >= 2 ? 'bg-agora-green' : 'bg-slate-500'">
                <i class="pi" :class="p.score >= 2 ? 'pi-verified' : 'pi-sparkles'" />
                {{ p.score >= 2 ? 'Nanan · Validé' : 'Nanan · À valider' }}
              </span>
              <template v-else>
                <img v-if="p.author_avatar" :src="p.author_avatar" class="h-6 w-6 rounded-full object-cover" />
                <span v-else class="grid h-6 w-6 place-items-center rounded-full bg-agora-green text-[10px] font-bold text-white">{{ initials(p.author_username || 'M') }}</span>
                <NuxtLink :to="`/u/${p.author_id}`" class="text-sm font-semibold text-agora-ink hover:text-agora-orange">{{ p.author_username || 'membre' }}</NuxtLink>
                <span class="text-xs text-slate-400">· {{ timeAgo(p.created_at) }}</span>
                <NuxtLink v-if="p.author_id && p.author_id !== auth.user?.id" :to="`/u/${p.author_id}`" class="text-xs text-slate-400 hover:text-agora-green" title="Envoyer un message"><i class="pi pi-envelope" /></NuxtLink>
              </template>
            </div>

            <div v-if="p.is_ai">
              <div class="space-y-2 leading-relaxed text-slate-700" v-html="renderMarkdown(p.body)" />
              <p v-if="p.score < 2" class="mt-2 rounded-lg bg-slate-50 px-3 py-2 text-xs text-slate-500">
                🤖 Brouillon proposé par Nanan. <strong>Votez 👍 pour le valider</strong>, ou proposez une meilleure réponse ci-dessous.
              </p>
            </div>
            <template v-else>
              <div v-if="editingPost === p.id">
                <textarea v-model="postBody" rows="3" />
                <div class="mt-2 flex gap-2">
                  <button class="btn-primary" @click="savePost(p)">Enregistrer</button>
                  <button class="btn-ghost border" @click="editingPost = null">Annuler</button>
                </div>
              </div>
              <p v-else class="leading-relaxed text-slate-700" v-html="linkifyMentions(p.body)" />
            </template>

            <div class="mt-3 flex items-center gap-4 text-xs text-slate-400">
              <template v-if="!p.is_ai && p.author_id === auth.user?.id && editingPost !== p.id">
                <button class="hover:text-agora-green" @click="startEditPost(p)"><i class="pi pi-pencil" /> Modifier</button>
                <button class="hover:text-red-500" @click="deletePost(p)"><i class="pi pi-trash" /> Supprimer</button>
              </template>
              <template v-else>
                <button v-if="p.is_ai && auth.isAuthenticated" class="hover:text-agora-green" @click="improveFromAi()"><i class="pi pi-pencil" /> Améliorer</button>
                <button class="hover:text-red-500" @click="report(p.id)"><i class="pi pi-flag" /> Signaler</button>
              </template>
            </div>
          </div>
        </article>
      </div>

      <!-- Répondre -->
      <div v-if="auth.isAuthenticated" class="mt-6 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <h3 class="font-bold">Votre réponse</h3>
        <textarea id="reply-box" v-model="reply" rows="3" class="mt-2" placeholder="Partagez votre expérience… (@pseudo pour mentionner)" />
        <div class="mt-2 flex items-center gap-2">
          <button class="btn-primary" :disabled="busy || !reply" @click="sendReply">Répondre</button>
          <label class="btn-ghost cursor-pointer border text-sm">
            <i :class="['pi', imgBusy ? 'pi-spin pi-spinner' : 'pi-image']" /> Image
            <input type="file" accept="image/*" class="hidden" @change="attachImage" />
          </label>
        </div>
      </div>
      <p v-else class="mt-6 text-sm text-slate-500">
        <NuxtLink to="/login" class="text-agora-orange">Connectez-vous</NuxtLink> pour répondre ou voter.
      </p>
    </template>

    <div v-else class="py-20 text-center text-slate-500">Discussion introuvable.</div>
  </AppShell>
</template>
