const CACHE_NAME = 'frontion-v27';
const BASE = '/frontion-news/';
const ASSETS = [
  BASE,
  BASE + 'index.html',
  BASE + 'manifest.json',
  BASE + 'icon-192.png',
  BASE + 'icon-512.png'
];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE_NAME).then(c => c.addAll(ASSETS)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});

self.addEventListener('fetch', e => {
  if (e.request.url.endsWith('.json')) {
    // JSON: always network first, cache fallback
    e.respondWith(fetch(e.request).then(r => {
      const clone = r.clone();
      caches.open(CACHE_NAME).then(c => c.put(e.request, clone));
      return r;
    }).catch(() => caches.match(e.request)));
  } else if (e.request.url.endsWith('index.html') || e.request.url.endsWith('/frontion-news/') || e.request.url === 'https://alprnkmbr.github.io/frontion-news') {
    // HTML pages: network first, cache fallback
    e.respondWith(fetch(e.request).then(r => {
      const clone = r.clone();
      caches.open(CACHE_NAME).then(c => c.put(e.request, clone));
      return r;
    }).catch(() => caches.match(e.request)));
  } else {
    // Static assets: cache first, network fallback
    e.respondWith(caches.match(e.request).then(r => r || fetch(e.request)));
  }
});