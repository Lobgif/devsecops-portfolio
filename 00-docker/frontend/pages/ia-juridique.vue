<script setup lang="ts">
definePageMeta({ middleware: 'auth' })
const { public: pub } = useRuntimeConfig()
const api = useApi()
useSeoMeta({ title: 'Nanan — votre assistant IA', description: "Nanan, l'assistant IA qui répond à vos questions sur tous les sujets du quotidien ivoirien (à titre informatif).", ogUrl: `${pub.siteUrl}/ia-juridique` })

const topics = ['Famille & Mariage', 'Droit du travail', 'Héritage', 'Droit pénal', 'Entreprise', 'Propriété']
const faqs: Record<string, string[]> = {
  'Famille & Mariage': ["Quels sont mes droits en cas de divorce en Côte d'Ivoire ?", 'Comment obtenir la garde de mes enfants ?', 'Que dit la loi sur les violences conjugales ?'],
  'Droit du travail': ['Un licenciement sans préavis est-il légal ?', 'Combien de jours de congés payés ai-je droit ?', 'Comment contester un licenciement ?'],
  'Héritage': ["Comment se fait le partage d'un héritage ?", 'Peut-on déshériter un enfant ?', 'Comment contester un testament ?'],
  'Droit pénal': ['Quels sont mes droits en garde à vue ?', 'Comment porter plainte ?', 'Que risque-t-on pour diffamation ?'],
  'Entreprise': ['Comment créer une SARL ?', 'Quelles obligations fiscales pour une entreprise ?', "Qu'est-ce que le statut d'entreprenant ?"],
  'Propriété': ['Comment obtenir un titre foncier ?', 'Que faire en cas de litige foncier ?', "Comment sécuriser l'achat d'un terrain ?"],
}
const topic = ref(topics[0])

const STORE = 'ia-juridique-history'
const messages = ref<any[]>([])   // {role:'user'|'assistant', content, sources?}
const question = ref('')
const loading = ref(false)

onMounted(() => {
  try { messages.value = JSON.parse(localStorage.getItem(STORE) || '[]') } catch {}
})
function persist() { if (import.meta.client) localStorage.setItem(STORE, JSON.stringify(messages.value.slice(-30))) }

async function ask(q?: string) {
  const text = (q ?? question.value).trim()
  if (!text || loading.value) return
  messages.value.push({ role: 'user', content: text })
  question.value = ''
  loading.value = true
  const history = messages.value.slice(0, -1).map((m) => ({ role: m.role, content: m.content }))
  try {
    const r = await api('/rag/ask', { method: 'POST', body: { question: text, mode: 'general', history } })
    messages.value.push({ role: 'assistant', content: r.answer, sources: r.sources })
  } catch {
    messages.value.push({ role: 'assistant', content: 'Service IA momentanément indisponible.', sources: [] })
  } finally {
    loading.value = false
    persist()
    nextTick(() => { const el = document.getElementById('chat'); if (el) el.scrollTop = el.scrollHeight })
  }
}
function reset() { messages.value = []; persist() }
async function copy(t: string) { try { await navigator.clipboard.writeText(t) } catch {} }

// Référence légale dépliable : clé "messageIndex-sourceIndex"
const openSrc = ref<string | null>(null)
function toggleSrc(key: string) { openSrc.value = openSrc.value === key ? null : key }
</script>

<template>
  <section class="mx-auto max-w-3xl px-4 py-10">
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-3">
        <span class="grid h-14 w-14 place-items-center rounded-2xl bg-gradient-to-br from-agora-green to-agora-green-dark text-2xl text-white"><i class="pi pi-book" /></span>
        <div><h1 class="font-display text-3xl font-bold">Nanan</h1><p class="text-sm text-slate-500">Votre assistant IA · Tous les sujets du quotidien ivoirien</p></div>
      </div>
      <button v-if="messages.length" class="btn-ghost text-sm" @click="reset"><i class="pi pi-refresh" /> Nouvelle conversation</button>
    </div>

    <!-- Conversation -->
    <div v-if="messages.length" id="chat" class="mt-6 max-h-[55vh] space-y-4 overflow-y-auto">
      <div v-for="(m, i) in messages" :key="i" class="flex" :class="m.role === 'user' ? 'justify-end' : 'justify-start'">
        <div class="max-w-[85%]">
          <div class="rounded-2xl px-4 py-3 text-sm"
               :class="m.role === 'user' ? 'bg-agora-orange text-white' : 'border border-slate-200 bg-white text-slate-700'">
            <p v-if="m.role === 'user'" class="whitespace-pre-line">{{ m.content }}</p>
            <div v-else class="space-y-2 leading-relaxed" v-html="renderMarkdown(m.content)" />
            <div v-if="m.sources?.length" class="mt-2">
              <p class="mb-1 text-xs font-medium text-slate-400">Références légales (cliquez pour lire l'article)</p>
              <div class="flex flex-wrap gap-1">
                <button v-for="(s, j) in m.sources" :key="j" type="button"
                        class="chip bg-agora-green/10 text-agora-green transition hover:bg-agora-green/20"
                        :class="openSrc === `${i}-${j}` ? 'ring-1 ring-agora-green' : ''"
                        @click="toggleSrc(`${i}-${j}`)">
                  <i class="pi pi-book text-xs" /> {{ s.code_source }}<template v-if="s.numero_article"> · art. {{ s.numero_article }}</template>
                </button>
              </div>
              <div v-for="(s, j) in m.sources" :key="`p-${j}`" v-show="openSrc === `${i}-${j}`"
                   class="mt-2 rounded-xl border border-agora-green/30 bg-agora-green/5 p-3 text-left">
                <p class="text-xs font-semibold text-agora-green">
                  {{ s.code_source }}<template v-if="s.numero_article"> — Article {{ s.numero_article }}</template>
                </p>
                <p v-if="s.titre_hierarchie" class="text-xs text-slate-400">{{ s.titre_hierarchie }}</p>
                <p class="mt-1 whitespace-pre-line text-sm text-slate-700">{{ s.content }}</p>
              </div>
            </div>
          </div>
          <button v-if="m.role === 'assistant'" class="mt-1 text-xs text-slate-400 hover:text-agora-green" @click="copy(m.content)">
            <i class="pi pi-copy" /> Copier
          </button>
        </div>
      </div>
      <p v-if="loading" class="text-sm text-slate-400"><i class="pi pi-spin pi-spinner" /> L'IA réfléchit…</p>
    </div>

    <!-- Saisie -->
    <div class="card mt-4">
      <textarea v-model="question" rows="2" placeholder="Posez votre question… (Ctrl+Entrée)" @keydown.ctrl.enter="ask()" />
      <div class="mt-2 flex items-center justify-between">
        <span class="text-xs text-slate-400"><i class="pi pi-exclamation-triangle" /> À titre informatif — pas un conseil officiel</span>
        <button class="btn-primary" :disabled="loading || !question" @click="ask()"><i class="pi pi-send" /> Envoyer</button>
      </div>
    </div>

    <!-- Suggestions (si pas encore de conversation) -->
    <template v-if="!messages.length">
      <div class="mt-6 flex items-start gap-3 rounded-2xl border border-agora-green/30 bg-agora-green/5 p-4">
        <span class="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-agora-green text-white"><i class="pi pi-sparkles" /></span>
        <p class="text-sm leading-relaxed text-slate-700">
          <strong>Akwaba 👋 Je suis Nanan</strong>, votre assistant IA sur les sujets du quotidien ivoirien.
          Posez-moi votre question (démarches, santé, emploi, business, droit, famille…) et je vous réponds
          avec des sources que vous pouvez consulter. <span class="text-slate-400">À titre informatif — je ne remplace pas un professionnel.</span>
        </p>
      </div>
      <div class="mt-6 flex flex-wrap gap-2">
        <button v-for="t in topics" :key="t" class="chip border"
                :class="topic === t ? 'border-agora-orange text-agora-orange' : 'border-slate-200 text-slate-500'" @click="topic = t">{{ t }}</button>
      </div>
      <h2 class="mt-6 text-sm font-semibold text-slate-600">Questions fréquentes — {{ topic }}</h2>
      <div class="mt-3 grid gap-3 sm:grid-cols-3">
        <button v-for="q in faqs[topic]" :key="q" class="card text-left text-sm hover:shadow-md" @click="ask(q)">
          <i class="pi pi-sparkles text-agora-orange" /> {{ q }}
        </button>
      </div>
    </template>
  </section>
</template>
