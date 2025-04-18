self.addEventListener('install', event => {
    event.waitUntil(
        caches.open('hcmut-study-cache').then(cache => {
            return cache.addAll([
                '/',
                '/dashboard',
                '/static/bootstrap.min.css'
            ]);
        })
    );
});

self.addEventListener('fetch', event => {
    event.respondWith(
        caches.match(event.request).then(response => {
            return response || fetch(event.request).catch(() => {
                return new Response('Bạn đang ngoại tuyến. Vui lòng kiểm tra kết nối.');
            });
        })
    );
});