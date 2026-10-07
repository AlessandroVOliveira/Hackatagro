// Guarda o app no celular para abrir sem sinal. Os registros ficam no IndexedDB (app.js).
const VERSAO = 'ronda-v1';
const CASCA = ['/', '/web/app.js', '/web/mapa.js', '/web/estilo.css', '/web/manifest.webmanifest', '/web/icone.svg'];

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(VERSAO).then((c) => c.addAll(CASCA)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((ks) => Promise.all(ks.filter((k) => k !== VERSAO).map((k) => caches.delete(k))))
      .then(() => self.clients.claim()),
  );
});

self.addEventListener('fetch', (e) => {
  const url = new URL(e.request.url);
  if (e.request.method !== 'GET' || url.pathname.startsWith('/api/')) return; // a API decide sozinha

  if (url.host.endsWith('fonts.googleapis.com') || url.host.endsWith('fonts.gstatic.com')) {
    e.respondWith(caches.open(VERSAO).then(async (c) => {
      const salvo = await c.match(e.request);
      const rede = fetch(e.request).then((r) => { const copia = r.clone(); c.put(e.request, copia); return r; }).catch(() => salvo);
      return salvo || rede;
    }));
    return;
  }

  // app: rede primeiro (pega atualização), cache se estiver sem sinal
  e.respondWith(
    fetch(e.request)
      .then((r) => {
        if (r.ok && url.origin === location.origin) {
          const copia = r.clone();
          caches.open(VERSAO).then((c) => c.put(e.request, copia));
        }
        return r;
      })
      .catch(() => caches.match(e.request).then((r) => r || caches.match('/'))),
  );
});
