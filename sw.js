/* Ravine Creator Games — service worker
   Strategy: network-first for the app shell so a push goes live on next open,
   cache fallback so the app still works with no signal. */
const VERSION = 'rcg-v2.0.0';
const SHELL = ['./', './index.html', './manifest.webmanifest',
  './icon-192.png', './icon-512.png', './apple-touch-icon.png'];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(VERSION).then(c => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys => Promise.all(keys.filter(k => k !== VERSION).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.origin !== location.origin) return;           // let YouTube/TikTok/Meta through untouched
  // Video: never intercept. These are large, range-requested files and the
  // browser's own HTTP cache handles them correctly. A SW in the middle breaks seeking.
  if (/\.(mp4|webm|m4v)$/i.test(url.pathname)) return;
  // Small immutable images: cache-first.
  if (/\.(jpg|jpeg|png|svg)$/i.test(url.pathname)) {
    e.respondWith(caches.match(req).then(hit => hit || fetch(req).then(res => {
      const copy = res.clone();
      caches.open(VERSION).then(c => c.put(req, copy)).catch(()=>{});
      return res;
    })));
    return;
  }
  e.respondWith(
    fetch(req).then(res => {
      const copy = res.clone();
      caches.open(VERSION).then(c => c.put(req, copy));
      return res;
    }).catch(() => caches.match(req).then(r => r || caches.match('./index.html')))
  );
});

self.addEventListener('message', e => { if (e.data === 'SKIP_WAITING') self.skipWaiting(); });
