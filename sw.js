// Service Worker for 上下五千年 PWA
// Cache strategy: Cache First for static assets, Network First for HTML pages

const CACHE_NAME = 'history-stories-v1';
const STATIC_ASSETS = [
  '/history-stories/',
  '/history-stories/index.html',
  '/history-stories/dynasties.html',
  '/history-stories/manifest.json',
];

// Install: pre-cache core static assets
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(STATIC_ASSETS);
    })
  );
  self.skipWaiting();
});

// Activate: clean old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k))
      );
    })
  );
  self.clients.claim();
});

// Fetch: cache-first for static assets, network-first for HTML
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // Only handle same-origin requests
  if (url.origin !== self.location.origin) return;

  // Skip chrome-extension requests
  if (url.protocol === 'chrome-extension:') return;

  // For HTML pages: Network first, fallback to cache
  if (event.request.destination === 'document' || url.pathname.endsWith('.html')) {
    event.respondWith(
      fetch(event.request)
        .then((response) => {
          const cloned = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(event.request, cloned));
          return response;
        })
        .catch(() => {
          return caches.match(event.request).then((cached) => {
            return cached || caches.match('/history-stories/index.html');
          });
        })
    );
    return;
  }

  // For static assets (CSS, JS, images, fonts): Cache first
  event.respondWith(
    caches.match(event.request).then((cached) => {
      const fetched = fetch(event.request).then((response) => {
        const cloned = response.clone();
        caches.open(CACHE_NAME).then((cache) => cache.put(event.request, cloned));
        return response;
      });
      return cached || fetched;
    })
  );
});
