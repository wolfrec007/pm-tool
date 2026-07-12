const CACHE_NAME = 'splanly-v1';
const STATIC_ASSETS = [
    '/',
    '/static/manifest.json',
    '/static/custom-theme.css',
    'https://rsms.me/inter/inter.css',
    'https://cdn.jsdelivr.net/npm/franken-ui@2.1.2/dist/css/core.min.css',
    'https://cdn.jsdelivr.net/npm/franken-ui@2.1.2/dist/css/utilities.min.css',
    'https://cdn.jsdelivr.net/npm/franken-ui@2.1.2/dist/js/core.iife.js',
];

self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => cache.addAll(STATIC_ASSETS))
    );
    self.skipWaiting();
});

self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((keys) =>
            Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
        )
    );
    self.clients.claim();
});

self.addEventListener('fetch', (event) => {
    const url = new URL(event.request.url);

    // Skip non-GET, API calls, auth pages
    if (event.request.method !== 'GET') return;
    if (url.pathname.startsWith('/api/')) return;
    if (url.pathname.startsWith('/auth/')) return;

    // Network-first for HTML pages, cache-first for static assets
    if (event.request.headers.get('accept')?.includes('text/html')) {
        event.respondWith(
            fetch(event.request)
                .then((response) => {
                    const clone = response.clone();
                    caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
                    return response;
                })
                .catch(() => caches.match(event.request))
        );
    } else {
        event.respondWith(
            caches.match(event.request).then((cached) => {
                if (cached) return cached;
                return fetch(event.request).then((response) => {
                    const clone = response.clone();
                    caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
                    return response;
                });
            })
        );
    }
});
