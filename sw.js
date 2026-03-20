const CACHE_NAME = 'acadefit-v1';
const arquivosCache = [
  '/',
  '/index.html',
  // Adicione aqui outros arquivos estáticos se separar CSS/JS/imagens
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(arquivosCache))
  );
});

self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(resposta => resposta || fetch(event.request))
  );
});
