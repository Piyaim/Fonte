// Fonte : coquille de l'appli en cache, données toujours prises sur le serveur en priorité.
const V = 'fonte-v1';
const SHELL = ['/', '/manifest.webmanifest', '/static/icons/icon-192.png', '/static/icons/icon-512.png'];
self.addEventListener('install', e => { e.waitUntil(caches.open(V).then(c => c.addAll(SHELL)).then(() => self.skipWaiting())); });
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== V).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener('fetch', e => {
  const u = new URL(e.request.url);
  if (e.request.method !== 'GET' || u.origin !== location.origin) return;
  // jamais en cache : photos, santé du service, et toute l'API sauf l'état (dernier état connu pour ouvrir l'appli hors connexion)
  if (u.pathname.startsWith('/photos/') || u.pathname === '/healthz' || (u.pathname.startsWith('/api/') && u.pathname !== '/api/state')) return;
  e.respondWith(fetch(e.request).then(r => {
    if (r.ok) { const cp = r.clone(); caches.open(V).then(c => c.put(e.request, cp)); }
    return r;
  }).catch(() => caches.match(e.request).then(r => r || caches.match('/'))));
});
