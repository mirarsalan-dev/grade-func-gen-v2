self.addEventListener('install', (e) => {
    e.waitUntil(caches.open('gradefunc-store').then((cache) => cache.addAll(['/', '/static/style.css'])));
});
self.addEventListener('fetch', (e) => {
    e.respondWith(caches.match(e.request).then((response) => response || fetch(e.request)));
});