const CACHE = 'bishwa-v1';
const PRECACHE = [
  '/static/style.css',
  '/static/icons/icon-192.png',
  '/static/icons/icon-512.png',
  '/offline',
];

// Install: pre-cache static shell
self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(PRECACHE)));
  self.skipWaiting();
});

// Activate: purge old caches
self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', e => {
  const { request: req } = e;
  const url = new URL(req.url);

  // Only handle same-origin GET
  if (req.method !== 'GET' || url.origin !== location.origin) return;

  // Static assets → cache-first, update in background
  if (url.pathname.startsWith('/static/')) {
    e.respondWith(
      caches.open(CACHE).then(async cache => {
        const cached = await cache.match(req);
        const networkFetch = fetch(req).then(r => {
          cache.put(req, r.clone());
          return r;
        }).catch(() => null);
        return cached || networkFetch;
      })
    );
    return;
  }

  // Navigation → network-first, fall back to offline page
  if (req.mode === 'navigate') {
    e.respondWith(
      fetch(req).catch(() => caches.match('/offline'))
    );
    return;
  }

  // API and other GETs → network only (data must be fresh)
  // Let the browser handle these normally
});
