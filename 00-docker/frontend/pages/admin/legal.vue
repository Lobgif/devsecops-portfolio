<script setup lang="ts">
definePageMeta({ layout: 'admin' })
useSeoMeta({ title: 'Admin — Base juridique', robots: 'noindex' })
const api = useApi()

const docs = ref<any[]>([])
const docLimit = ref(5)   // pagination « voir plus » des documents
const jobLimit = ref(5)   // pagination « voir plus » des imports (jobs)

// Recherche + filtre
const q = ref('')
const jobStatusFilter = ref('all')
const filteredDocs = computed(() => {
  const s = q.value.trim().toLowerCase()
  if (!s) return docs.value
  return docs.value.filter((d) =>
    (d.title || '').toLowerCase().includes(s) || (d.source_type || '').toLowerCase().includes(s))
})
const filteredJobs = computed(() => {
  const s = q.value.trim().toLowerCase()
  return jobs.value.filter((j) =>
    (jobStatusFilter.value === 'all' || j.status === jobStatusFilter.value)
    && (!s || (j.source || '').toLowerCase().includes(s)))
})
watch([q, jobStatusFilter], () => { docLimit.value = 5; jobLimit.value = 5 })
async function load() { docs.value = await api('/rag/admin/documents').catch(() => []) }

// --- Import en masse en arrière-plan (jobs RabbitMQ) ---
const batch = reactive({ urls: '', kind: 'url', source_type: 'loi', crawl_filter: '' })
const jobs = ref<any[]>([])
const batchMsg = ref('')
async function loadJobs() { jobs.value = await api('/rag/admin/jobs').catch(() => []) }
async function submitBatch() {
  const urls = batch.urls.split('\n').map((u) => u.trim()).filter(Boolean)
  if (!urls.length) return
  const r = await api('/rag/admin/ingest-jobs', { method: 'POST', body: {
    urls, kind: batch.kind, source_type: batch.source_type,
    crawl_filter: batch.crawl_filter || null,
  } }).catch((e) => { alert(e?.data?.detail || 'Erreur'); return null })
  if (r) { batchMsg.value = `${r.jobs.length} job(s) lancé(s) en arrière-plan.`; batch.urls = ''; await loadJobs() }
}
async function cancelJob(j: any) {
  await api(`/rag/admin/jobs/${j.id}/cancel`, { method: 'POST' }).catch(() => {})
  await loadJobs()
}
const failedCount = computed(() => jobs.value.filter((j) => j.status === 'error').length)
async function retryFailed() {
  const r = await api('/rag/admin/jobs/retry-failed', { method: 'POST' }).catch(() => null)
  if (r) { batchMsg.value = `${r.retried} job(s) relancé(s).`; await loadJobs() }
}

// --- Crawl : aperçu (pagination + profondeur) puis import de la sélection ---
const depth = ref(1)
const previewBusy = ref(false)
const previewMsg = ref('')
const previewUrls = ref<{ url: string; sel: boolean }[]>([])
async function previewCrawl() {
  const url = batch.urls.split('\n').map((u) => u.trim()).filter(Boolean)[0]
  if (!url) { alert('Collez l\'URL de la page index à crawler.'); return }
  previewBusy.value = true; previewUrls.value = []; previewMsg.value = ''
  try {
    const r = await api('/rag/admin/crawl-preview', { method: 'POST', body: {
      url, crawl_filter: batch.crawl_filter || null, depth: depth.value,
    } })
    previewUrls.value = (r.urls || []).map((u: string) => ({ url: u, sel: true }))
    previewMsg.value = `${r.count} URL(s) trouvée(s) — décochez celles à exclure, puis importez.`
  } catch (e: any) { alert(e?.data?.detail || 'Échec du crawl.') }
  finally { previewBusy.value = false }
}
async function importSelection() {
  const urls = previewUrls.value.filter((u) => u.sel).map((u) => u.url)
  if (!urls.length) return
  const r = await api('/rag/admin/ingest-jobs', { method: 'POST', body: {
    urls, kind: 'url', source_type: batch.source_type,
  } }).catch(() => null)
  if (r) { batchMsg.value = `${r.jobs.length} job(s) lancé(s) en arrière-plan.`; previewUrls.value = []; previewMsg.value = ''; await loadJobs() }
}
const jobBadge = (s: string) => ({
  pending: 'bg-slate-100 text-slate-600', running: 'bg-sky-100 text-sky-700',
  done: 'bg-emerald-100 text-emerald-700', error: 'bg-red-100 text-red-700',
  cancelled: 'bg-amber-100 text-amber-700',
}[s] || 'bg-slate-100 text-slate-600')

let timer: any = null
onMounted(() => {
  load(); loadJobs()
  // Rafraîchit la progression toutes les 3 s tant qu'on est sur la page
  timer = setInterval(() => { loadJobs(); load() }, 3000)
})
onBeforeUnmount(() => { if (timer) clearInterval(timer) })

const form = reactive({ title: '', source_type: 'loi', code_source: '', source_url: '', content: '' })
const busy = ref(false)
const msg = ref(''); const err = ref('')

async function submit() {
  err.value = ''; msg.value = ''
  if (!form.title.trim() || !form.content.trim()) { err.value = 'Titre et contenu obligatoires.'; return }
  busy.value = true
  try {
    await api('/rag/admin/ingest-text', { method: 'POST', body: {
      title: form.title, content: form.content, source_type: form.source_type,
    } })
    msg.value = 'Texte envoyé en arrière-plan — voir la file plus haut.'
    Object.assign(form, { title: '', code_source: '', source_url: '', content: '' })
    await loadJobs()
  } catch (e: any) { err.value = e?.data?.detail || 'Erreur lors de l\'ingestion.' }
  finally { busy.value = false }
}

async function remove(d: any) {
  if (!confirm(`Supprimer « ${d.title} » et ses ${d.chunks} article(s) indexé(s) ?`)) return
  await api(`/rag/admin/documents/${d.id}`, { method: 'DELETE' }).catch((e) => alert(e?.data?.detail || 'Erreur'))
  await load()
}
async function reingest(d: any) {
  if (!confirm(`Relancer « ${d.title} » depuis sa source (le contenu sera rafraîchi) ?`)) return
  const r = await api(`/rag/admin/documents/${d.id}/reingest`, { method: 'POST' }).catch((e) => { alert(e?.data?.detail || 'Erreur'); return null })
  if (r) { batchMsg.value = 'Ré-ingestion lancée en arrière-plan.'; await Promise.all([load(), loadJobs()]) }
}

async function removeDemo() {
  if (!confirm('Supprimer TOUS les documents de démonstration ?')) return
  const r = await api('/rag/admin/documents/demo/all', { method: 'DELETE' }).catch(() => null)
  if (r) alert(`${r.deleted_documents} document(s) de démo supprimé(s).`)
  await load()
}

// --- Upload de fichiers (.pdf/.docx/.txt) ---
const selected = ref<File[]>([])
const uploadType = ref('loi')
const ocr = ref(true)
const uploading = ref(false)
const uploadResults = ref<any[]>([])
function onFiles(e: Event) { selected.value = Array.from((e.target as HTMLInputElement).files || []) }
async function uploadFiles() {
  if (!selected.value.length) return
  uploading.value = true; uploadResults.value = []
  const fd = new FormData()
  for (const f of selected.value) fd.append('files', f)
  fd.append('source_type', uploadType.value)
  try {
    const r = await api('/rag/admin/import-files', { method: 'POST', body: fd })
    batchMsg.value = `${r.jobs.length} fichier(s) envoyé(s) en arrière-plan — voir la file.`
    selected.value = []
    await loadJobs()
  } catch (e: any) { alert(e?.data?.detail || 'Échec de l\'import.') }
  finally { uploading.value = false }
}

// --- Import par URL ---
const url = reactive({ url: '', title: '', source_type: 'loi' })
const urlBusy = ref(false); const urlMsg = ref(''); const urlErr = ref('')
async function importUrl() {
  urlMsg.value = ''; urlErr.value = ''
  if (!url.url.trim()) return
  urlBusy.value = true
  try {
    await api('/rag/admin/import-url', { method: 'POST', body: { ...url } })
    urlMsg.value = 'URL envoyée en arrière-plan — voir la file.'
    url.url = ''; url.title = ''
    await loadJobs()
  } catch (e: any) { urlErr.value = e?.data?.detail || 'Erreur.' }
  finally { urlBusy.value = false }
}

const fmt = (d: string) => d ? new Date(d).toLocaleDateString('fr-FR') : ''
</script>

<template>
  <div>
    <h1 class="font-display text-2xl font-bold">Base juridique (Nanan)</h1>
    <p class="mt-1 text-slate-500">
      Ajoutez les vrais textes de loi ivoiriens. Le texte est découpé automatiquement par
      « Article N », vectorisé et indexé pour les réponses de Nanan.
    </p>

    <!-- Import en masse en arrière-plan -->
    <div class="card mt-6 border-agora-orange/30">
      <h2 class="font-semibold"><i class="pi pi-bolt text-agora-orange" /> Import en masse (arrière-plan)</h2>
      <p class="mt-1 text-sm text-slate-500">
        Collez plusieurs liens (un par ligne) : pages de loi ou PDF en ligne. Les jobs tournent côté
        serveur — vous pouvez <strong>quitter la page</strong>, ils continuent. « Crawler » suit les liens
        d'une page index (ex. un site qui liste plusieurs codes).
      </p>
      <textarea v-model="batch.urls" rows="4" class="mt-3 w-full rounded-xl border px-3 py-2 font-mono text-xs"
                placeholder="https://exemple.ci/code-du-travail.pdf&#10;https://exemple.ci/code-de-la-famille" />
      <div class="mt-2 flex flex-wrap items-end gap-3">
        <label class="text-sm"><span class="mb-1 block text-slate-600">Mode</span>
          <select v-model="batch.kind" class="rounded-xl border px-3 py-2">
            <option value="url">Chaque ligne = un document</option>
            <option value="crawl">Chaque ligne = page index à crawler</option>
          </select>
        </label>
        <label class="text-sm"><span class="mb-1 block text-slate-600">Type</span>
          <select v-model="batch.source_type" class="rounded-xl border px-3 py-2">
            <option value="code">Code</option><option value="loi">Loi</option>
            <option value="decret">Décret</option><option value="jurisprudence">Jurisprudence</option>
          </select>
        </label>
        <label v-if="batch.kind === 'crawl'" class="text-sm"><span class="mb-1 block text-slate-600">Filtre de liens (facultatif)</span>
          <input v-model="batch.crawl_filter" placeholder="ex. /codes/" class="rounded-xl border px-3 py-2" />
        </label>
        <label v-if="batch.kind === 'crawl'" class="text-sm"><span class="mb-1 block text-slate-600">Profondeur</span>
          <select v-model.number="depth" class="rounded-xl border px-3 py-2">
            <option :value="1">1 (page index)</option>
            <option :value="2">2 (sous-index)</option>
            <option :value="3">3</option>
          </select>
        </label>
        <button v-if="batch.kind === 'url'" class="btn-primary" @click="submitBatch"><i class="pi pi-play" /> Lancer en arrière-plan</button>
        <button v-else class="btn-primary" :disabled="previewBusy" @click="previewCrawl">
          <i :class="['pi', previewBusy ? 'pi-spin pi-spinner' : 'pi-search']" /> Aperçu du crawl
        </button>
      </div>
      <p v-if="batchMsg" class="mt-2 text-sm text-agora-green">{{ batchMsg }}</p>
      <p v-if="previewMsg" class="mt-2 text-sm text-slate-600">{{ previewMsg }}</p>

      <!-- Aperçu des URLs trouvées (avant ingestion) -->
      <div v-if="previewUrls.length" class="mt-3 rounded-xl border border-slate-200 p-3">
        <div class="mb-2 flex items-center justify-between">
          <span class="text-sm font-medium">{{ previewUrls.filter(u => u.sel).length }}/{{ previewUrls.length }} sélectionnée(s)</span>
          <button class="btn-primary text-sm" @click="importSelection"><i class="pi pi-download" /> Importer la sélection</button>
        </div>
        <div class="max-h-60 space-y-1 overflow-y-auto">
          <label v-for="u in previewUrls" :key="u.url" class="flex items-center gap-2 text-xs">
            <input v-model="u.sel" type="checkbox" />
            <span class="truncate" :title="u.url">{{ u.url }}</span>
          </label>
        </div>
      </div>

      <p v-if="jobs.some(j => j.status==='pending' || j.status==='running')" class="mt-3 text-sm text-sky-700">
        <i class="pi pi-spin pi-spinner" /> Imports en cours… (voir le suivi dans « Documents & sources » plus bas)
      </p>
    </div>

    <!-- Import de fichiers -->
    <div class="card mt-6">
      <h2 class="font-semibold"><i class="pi pi-upload text-agora-orange" /> Importer des fichiers (.pdf, .docx, .txt)</h2>
      <p class="mt-1 text-sm text-slate-500">Sélectionne plusieurs fichiers — le texte est extrait, découpé et indexé automatiquement (OCR de secours pour les PDF scannés).</p>
      <div class="mt-3 flex flex-wrap items-end gap-3">
        <input type="file" multiple accept=".pdf,.docx,.txt,.md" class="text-sm" @change="onFiles" />
        <label class="text-sm"><span class="mb-1 block text-slate-600">Type</span>
          <select v-model="uploadType" class="rounded-xl border px-3 py-2">
            <option value="code">Code</option><option value="loi">Loi</option>
            <option value="decret">Décret</option><option value="jurisprudence">Jurisprudence</option>
          </select>
        </label>
        <label class="flex items-center gap-2 text-sm text-slate-600"><input v-model="ocr" type="checkbox" /> OCR si scanné</label>
        <button class="btn-primary" :disabled="uploading || !selected.length" @click="uploadFiles">
          <i :class="['pi', uploading ? 'pi-spin pi-spinner' : 'pi-upload']" /> {{ uploading ? 'Import…' : `Importer (${selected.length})` }}
        </button>
      </div>
      <ul v-if="uploadResults.length" class="mt-3 space-y-1 text-sm">
        <li v-for="(r, i) in uploadResults" :key="i" :class="r.ok ? 'text-agora-green' : 'text-red-600'">
          <i :class="['pi', r.ok ? 'pi-check' : 'pi-times']" /> {{ r.file }} —
          <template v-if="r.ok">{{ r.chunks }} article(s){{ r.skipped ? ' (déjà présent)' : '' }}</template>
          <template v-else>{{ r.error }}</template>
        </li>
      </ul>
    </div>

    <!-- Import par URL -->
    <div class="card mt-4">
      <h2 class="font-semibold"><i class="pi pi-link text-agora-orange" /> Importer depuis une URL</h2>
      <div class="mt-3 flex flex-wrap items-end gap-3">
        <input v-model="url.url" placeholder="https://… (page de loi ou PDF en ligne)" class="min-w-[260px] flex-1 rounded-xl border px-3 py-2 text-sm" />
        <input v-model="url.title" placeholder="Titre (facultatif)" class="rounded-xl border px-3 py-2 text-sm" />
        <button class="btn-primary" :disabled="urlBusy || !url.url" @click="importUrl">
          <i :class="['pi', urlBusy ? 'pi-spin pi-spinner' : 'pi-download']" /> Importer
        </button>
      </div>
      <p v-if="urlMsg" class="mt-2 text-sm text-agora-green">{{ urlMsg }}</p>
      <p v-if="urlErr" class="mt-2 text-sm text-red-600">{{ urlErr }}</p>
    </div>

    <!-- Formulaire d'ajout (copier-coller) -->
    <h2 class="mt-6 font-display text-lg font-bold">Ou coller le texte manuellement</h2>
    <div class="card mt-3 grid gap-4">
      <div class="grid gap-4 sm:grid-cols-2">
        <label class="block text-sm">
          <span class="mb-1 block font-medium text-slate-600">Titre du document</span>
          <input v-model="form.title" placeholder="Ex. Code de la famille" class="w-full rounded-xl border px-3 py-2" />
        </label>
        <label class="block text-sm">
          <span class="mb-1 block font-medium text-slate-600">Type</span>
          <select v-model="form.source_type" class="w-full rounded-xl border px-3 py-2">
            <option value="code">Code</option>
            <option value="loi">Loi</option>
            <option value="decret">Décret</option>
            <option value="jurisprudence">Jurisprudence</option>
          </select>
        </label>
        <label class="block text-sm">
          <span class="mb-1 block font-medium text-slate-600">Source citée (facultatif)</span>
          <input v-model="form.code_source" placeholder="Ex. Code de la famille (2019)" class="w-full rounded-xl border px-3 py-2" />
        </label>
        <label class="block text-sm">
          <span class="mb-1 block font-medium text-slate-600">URL source (facultatif)</span>
          <input v-model="form.source_url" placeholder="https://…" class="w-full rounded-xl border px-3 py-2" />
        </label>
      </div>
      <label class="block text-sm">
        <span class="mb-1 block font-medium text-slate-600">Contenu (texte brut, articles préfixés par « Article N »)</span>
        <textarea v-model="form.content" rows="10" class="w-full rounded-xl border px-3 py-2 font-mono text-xs"
                  placeholder="Article 1 : ...&#10;Article 2 : ..." />
      </label>
      <div class="flex items-center gap-3">
        <button class="btn-primary" :disabled="busy" @click="submit">
          <i :class="['pi', busy ? 'pi-spin pi-spinner' : 'pi-plus']" /> {{ busy ? 'Indexation…' : 'Ajouter à la base' }}
        </button>
        <span v-if="msg" class="text-sm text-agora-green">{{ msg }}</span>
        <span v-if="err" class="text-sm text-red-600">{{ err }}</span>
      </div>
    </div>

    <!-- ===== Documents & sources (regroupé) ===== -->
    <h2 class="mt-8 font-display text-lg font-bold">Documents &amp; sources</h2>

    <!-- Recherche + filtre statut -->
    <div class="mt-3 flex flex-wrap items-center gap-3">
      <div class="relative min-w-[240px] flex-1">
        <i class="pi pi-search absolute left-3 top-1/2 -translate-y-1/2 text-sm text-slate-400" />
        <input v-model="q" placeholder="Rechercher (titre, URL, type)…" class="w-full rounded-xl border py-2 pl-9 pr-3 text-sm" />
      </div>
      <label class="text-sm text-slate-600">Statut
        <select v-model="jobStatusFilter" class="ml-1 rounded-xl border px-2 py-2">
          <option value="all">Tous</option>
          <option value="pending">En attente</option>
          <option value="running">En cours</option>
          <option value="done">Terminé</option>
          <option value="error">Erreur</option>
          <option value="cancelled">Annulé</option>
        </select>
      </label>
      <button v-if="q || jobStatusFilter !== 'all'" class="btn-ghost text-xs" @click="q = ''; jobStatusFilter = 'all'">
        <i class="pi pi-times" /> Réinitialiser
      </button>
    </div>

    <!-- Suivi des imports (jobs) — paginé -->
    <div v-if="jobs.length" class="mt-3">
      <div class="mb-2 flex items-center justify-between">
        <span class="text-sm font-medium text-slate-600">Imports ({{ filteredJobs.length }})</span>
        <button v-if="failedCount" class="btn-ghost text-xs text-amber-700" @click="retryFailed">
          <i class="pi pi-refresh" /> Relancer les échecs ({{ failedCount }})
        </button>
      </div>
      <div class="overflow-x-auto">
        <table class="w-full text-left text-sm">
          <thead class="text-slate-500"><tr><th class="py-1">Source</th><th>Statut</th><th>Progression</th><th>Articles</th><th></th></tr></thead>
          <tbody>
            <tr v-for="j in filteredJobs.slice(0, jobLimit)" :key="j.id" class="border-t border-slate-100">
              <td class="max-w-[260px] truncate py-2" :title="j.source">{{ j.source }}</td>
              <td><span class="chip" :class="jobBadge(j.status)">{{ j.status }}</span><span v-if="j.message" class="ml-1 text-xs text-red-500" :title="j.message">⚠</span></td>
              <td>{{ j.done }}<span v-if="j.total">/{{ j.total }}</span></td>
              <td>{{ j.chunks }}</td>
              <td class="text-right"><button v-if="j.status==='pending'||j.status==='running'" class="btn-ghost text-xs text-amber-600" @click="cancelJob(j)">Annuler</button></td>
            </tr>
          </tbody>
        </table>
      </div>
      <div v-if="filteredJobs.length > jobLimit" class="mt-2 text-center">
        <button class="btn-outline text-sm" @click="jobLimit += 5"><i class="pi pi-chevron-down" /> Voir plus ({{ filteredJobs.length - jobLimit }})</button>
      </div>
      <div v-if="jobLimit > 5" class="mt-1 text-center"><button class="text-xs text-slate-400 hover:text-agora-green" @click="jobLimit = 5">Réduire</button></div>
    </div>

    <!-- Documents indexés — paginé, avec Relancer / Supprimer -->
    <div class="mt-5 flex items-center justify-between">
      <span class="text-sm font-medium text-slate-600">Documents indexés ({{ filteredDocs.length }})</span>
      <button class="btn-ghost text-xs text-red-600" @click="removeDemo"><i class="pi pi-trash" /> Supprimer les documents de démo</button>
    </div>
    <div class="mt-3 overflow-x-auto">
      <table class="w-full overflow-hidden rounded-2xl border border-slate-200 bg-white text-left text-sm">
        <thead class="bg-slate-50 text-slate-600">
          <tr><th class="p-3">Titre</th><th class="p-3">Type</th><th class="p-3">Articles</th><th class="p-3">Ajouté</th><th class="p-3 text-right">Actions</th></tr>
        </thead>
        <tbody>
          <tr v-for="d in filteredDocs.slice(0, docLimit)" :key="d.id" class="border-t border-slate-100">
            <td class="p-3 font-medium"><span class="block max-w-[320px] truncate" :title="d.title">{{ d.title }}</span></td>
            <td class="p-3 text-slate-500">{{ d.source_type }}</td>
            <td class="p-3">{{ d.chunks }}</td>
            <td class="p-3 text-slate-400">{{ fmt(d.created_at) }}</td>
            <td class="p-3">
              <div class="flex justify-end gap-1">
                <button v-if="d.source_url || (d.title && d.title.startsWith('http'))" class="btn-ghost text-xs text-sky-700" title="Relancer (rafraîchir depuis la source)" @click="reingest(d)"><i class="pi pi-refresh" /> Relancer</button>
                <button class="btn-ghost text-xs text-red-600" @click="remove(d)"><i class="pi pi-trash" /> Supprimer</button>
              </div>
            </td>
          </tr>
          <tr v-if="!filteredDocs.length"><td colspan="5" class="p-6 text-center text-slate-400">{{ q ? 'Aucun résultat pour cette recherche.' : 'Aucun document — ajoutez le premier texte de loi.' }}</td></tr>
        </tbody>
      </table>
      <div v-if="filteredDocs.length > docLimit" class="mt-3 text-center">
        <button class="btn-outline text-sm" @click="docLimit += 5"><i class="pi pi-chevron-down" /> Voir plus ({{ filteredDocs.length - docLimit }})</button>
      </div>
      <div v-if="docLimit > 5 && docs.length > 5" class="mt-1 text-center"><button class="text-xs text-slate-400 hover:text-agora-green" @click="docLimit = 5">Réduire</button></div>
    </div>
  </div>
</template>
