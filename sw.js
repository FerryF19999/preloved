'use strict';

// Increment VERSION whenever the offline shell or caching rules change.
const VERSION = 'v1';
const PREFIX = 'nemu-preloved-';
const SHELL = `${PREFIX}shell-${VERSION}`;
const RUNTIME = `${PREFIX}runtime-${VERSION}`;
const ROOT = '/preloved/';
const OFFLINE = `${ROOT}offline.html`;
const MAX_ENTRIES = 48;
const MAX_BYTES = 2 * 1024 * 1024;
const PRECACHE = [OFFLINE, `${ROOT}manifest.webmanifest`, `${ROOT}pwa.js`,
  `${ROOT}icons/icon-192.png`, `${ROOT}icons/icon-512.png`,
  `${ROOT}icons/maskable-192.png`, `${ROOT}icons/maskable-512.png`];

self.addEventListener('install', event => {
  event.waitUntil(caches.open(SHELL).then(cache => cache.addAll(PRECACHE)));
  // Do not force a new worker onto an already-open page mid-session.
});
self.addEventListener('activate', event => {
  event.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(keys.filter(key => key.startsWith(PREFIX) &&
      key !== SHELL && key !== RUNTIME).map(key => caches.delete(key)));
    await self.clients.claim();
  })());
});

// Serialize writes so concurrent requests cannot exceed the entry limit.
let writes = Promise.resolve();
function remember(request, response) {
  if (new URL(request.url).search || !response.ok || response.status === 206 || response.type !== 'basic' ||
      response.redirected || /no-store|private/i.test(response.headers.get('cache-control') || '') ||
      response.headers.get('vary') === '*' ||
      Number(response.headers.get('content-length')) > MAX_BYTES) return Promise.resolve();
  const copy = response.clone();
  writes = writes.catch(() => {}).then(async () => {
    // Bound entries without trusting Content-Length (often absent on Pages).
    const blob = await copy.blob();
    if (blob.size > MAX_BYTES) return;
    const cache = await caches.open(RUNTIME);
    await cache.delete(request);
    await cache.put(request, new Response(blob, {
      status: copy.status, statusText: copy.statusText, headers: copy.headers
    }));
    const keys = await cache.keys();
    await Promise.all(keys.slice(0, Math.max(0, keys.length - MAX_ENTRIES))
      .map(key => cache.delete(key)));
  }).catch(() => {}); // Quota/private-mode failures must not break navigation.
  return writes;
}

async function networkFirst(request, event) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 6000);
  try {
    const response = await fetch(request, { signal: controller.signal });
    if (response.status >= 500) throw new Error('Server unavailable');
    event.waitUntil(remember(request, response));
    return response; // Preserve real 4xx errors; never disguise missing products.
  } catch (_) {
    const saved = await caches.match(request);
    if (saved) return saved;
    if (request.mode === 'navigate') {
      return (await caches.match(OFFLINE)) || new Response('Offline. Reconnect and try again.', {
        status: 503, headers: { 'Content-Type': 'text/plain; charset=utf-8' }
      });
    }
    return new Response('Network unavailable', { status: 503 });
  } finally {
    clearTimeout(timer);
  }
}

self.addEventListener('fetch', event => {
  const request = event.request;
  const url = new URL(request.url);
  if (request.method !== 'GET' || url.origin !== self.location.origin ||
      !url.pathname.startsWith(ROOT) || request.headers.has('range') ||
      request.headers.has('authorization') || (url.search && request.mode !== 'navigate')) return;
  const fresh = request.mode === 'navigate' || /\.(?:html|json)$/i.test(url.pathname);
  // Deliberately exclude catalog thumbnails, videos, API calls, and external assets.
  const asset = /\.(?:css|js|woff2?|webmanifest)$/i.test(url.pathname) ||
    url.pathname.startsWith(`${ROOT}icons/`);
  if (!fresh && !asset) return;
  event.respondWith((async () => {
    if (fresh) return networkFirst(request, event);
    // Stale-while-revalidate static assets; catalogs and documents are network-first.
    const cached = await caches.match(request);
    const update = fetch(request).then(response => {
      event.waitUntil(remember(request, response));
      return response;
    });
    if (cached) {
      event.waitUntil(update.catch(() => {}));
      return cached;
    }
    try { return await update; } catch (_) {
      return new Response('Network unavailable', { status: 503 });
    }
  })());
});
