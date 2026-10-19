// Service worker Jamakan — réception des notifications Web Push.
self.addEventListener('push', (event) => {
  let data = {}
  try { data = event.data ? event.data.json() : {} } catch (e) {}
  const title = data.title || 'Jamakan'
  event.waitUntil(
    self.registration.showNotification(title, {
      body: data.message || '',
      icon: '/favicon.svg',
      badge: '/favicon.svg',
      data: { url: data.link || '/' },
    }),
  )
})

self.addEventListener('notificationclick', (event) => {
  event.notification.close()
  const url = (event.notification.data && event.notification.data.url) || '/'
  event.waitUntil(clients.openWindow(url))
})
