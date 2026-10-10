// Endpoint de santé léger pour le healthcheck Docker du frontend.
export default defineEventHandler(() => ({ status: 'ok' }))
