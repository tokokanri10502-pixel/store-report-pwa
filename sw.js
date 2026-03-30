const CACHE_NAME = 'store-report-v3';
const ASSETS = [
  './index.html',
  './manifest.json',
  './images/page_1.jpg',
  './images/page_2.jpg',
  './images/page_3.jpg',
  './images/page_4.jpg'
];

// ネットワーク優先で取得するファイル（常に最新を取得）
const NETWORK_FIRST = ['reports_data.js', 'reports.json'];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(ASSETS))
  );
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', event => {
  const url = event.request.url;

  // reports_data.js と reports.json はネットワーク優先
  if (NETWORK_FIRST.some(f => url.includes(f))) {
    event.respondWith(
      fetch(event.request)
        .then(response => {
          const clone = response.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
          return response;
        })
        .catch(() => caches.match(event.request))
    );
    return;
  }

  // それ以外はキャッシュ優先
  event.respondWith(
    caches.match(event.request).then(cached => cached || fetch(event.request))
  );
});
