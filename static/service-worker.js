const CACHE_NAME = 'vbmed-cache-v1';
const urlsToCache = [
  '/',
  '/static/css/styles.css',
  '/static/images/logo-192.png',
  '/static/images/logo-512.png',
];

// Instalando o service worker
self.addEventListener('install', function (event) {
  event.waitUntil(
    caches.open(CACHE_NAME).then(function (cache) {
      return cache.addAll(urlsToCache);
    })
  );
});

// Ativando e limpando caches antigos
self.addEventListener('activate', function (event) {
  event.waitUntil(
    caches.keys().then(function (cacheNames) {
      return Promise.all(
        cacheNames.map(function (cacheName) {
          if (cacheName !== CACHE_NAME) {
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});

// Buscando recursos no cache primeiro
self.addEventListener('fetch', function (event) {
  event.respondWith(
    caches.match(event.request).then(function (response) {
      return response || fetch(event.request);
    })
  );
});
