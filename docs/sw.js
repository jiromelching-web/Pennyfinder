// PennyFinder service worker: app shell cache-first, deals.json network-first (offline fallback).
const SHELL = 'pf-shell-v1';
const ASSETS = ['./', './index.html', './manifest.webmanifest', './icons/icon-180.png', './icons/icon-192.png', './icons/icon-512.png'];
self.addEventListener('install', e => { e.waitUntil(caches.open(SHELL).then(c => c.addAll(ASSETS))); self.skipWaiting(); });
self.addEventListener('activate', e => { e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== SHELL && k !== 'pf-data').map(k => caches.delete(k))))); self.clients.claim(); });
self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);
  if (e.request.method !== 'GET' || url.origin !== location.origin) return;
  if (url.pathname.endsWith('/data/deals.json')) {
    e.respondWith(fetch(e.request).then(r => { const cp = r.clone(); caches.open('pf-data').then(c => c.put('data/deals.json', cp)); return r; })
      .catch(() => caches.open('pf-data').then(c => c.match('data/deals.json'))));
    return;
  }
  e.respondWith(caches.match(e.request).then(r => r || fetch(e.request)));
});
