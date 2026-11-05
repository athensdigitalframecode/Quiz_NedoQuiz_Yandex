const V="2fab3f47a8a3",C="quiz-"+V;
/* V подменяется при сборке на хеш версии: новый сайт = новый sw.js = старый кэш удаляется */
self.addEventListener("install",e=>{self.skipWaiting()});
self.addEventListener("activate",e=>{e.waitUntil(caches.keys().then(k=>Promise.all(k.filter(x=>x!==C).map(x=>caches.delete(x)))).then(()=>self.clients.claim()))});
self.addEventListener("fetch",e=>{
  const r=e.request;if(r.method!=="GET")return;
  const u=new URL(r.url);if(u.origin!==location.origin)return;
  if(u.pathname.endsWith("/version.json")||u.pathname.endsWith("/sw.js"))return;
  if(r.mode==="navigate"){e.respondWith(fetch(r,{cache:"no-cache"}).then(x=>{const c=x.clone();caches.open(C).then(h=>h.put("./",c));return x}).catch(()=>caches.match("./")));return}
  e.respondWith(caches.match(r).then(m=>m||fetch(r).then(x=>{if(x.ok){const c=x.clone();caches.open(C).then(h=>h.put(r,c))}return x})));
});
