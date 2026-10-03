/* Ravine Creator Games service worker · October build.
   Shell: network-first. Public media (images, b-roll stills, fonts, video): cache-first, versioned.
   Private responses (Supabase REST/auth, anything with ?k=) are NEVER cached.
   On activate, every older cache (including the Sept 'rcg-*' shell caches that held u/*.json) is deleted. */
const VERSION='oct-20261003-051326';
const SHELL='rcg-oct-shell-'+VERSION, MEDIA='rcg-oct-media-'+VERSION;
const PRIVATE=/supabase\.co|\/rest\/v1\/|\/auth\/v1\/|\/u\/[A-Z0-9]+\.json|[?&]k=/i;
self.addEventListener('install',e=>{ self.skipWaiting(); });
self.addEventListener('activate',e=>{ e.waitUntil((async()=>{ const keys=await caches.keys(); await Promise.all(keys.filter(k=>k!==SHELL&&k!==MEDIA).map(k=>caches.delete(k))); await self.clients.claim(); })()); });
self.addEventListener('fetch',e=>{
  const req=e.request; if(req.method!=='GET') return;
  const url=new URL(req.url);
  if(PRIVATE.test(req.url)) return;                               // straight to network, never stored
  if(url.origin!==location.origin) return;
  const isMedia=/\.(jpg|jpeg|png|webp|mp4|woff2|webmanifest)$/i.test(url.pathname)||/\/data\/(inspiration|library)\.json$/.test(url.pathname);
  if(isMedia){ e.respondWith((async()=>{ const c=await caches.open(MEDIA); const hit=await c.match(req); if(hit) return hit; const r=await fetch(req); if(r.ok) c.put(req,r.clone()); return r; })()); return; }
  if(url.pathname.endsWith('/')||url.pathname.endsWith('index.html')||url.pathname.endsWith('sw.js')){
    e.respondWith((async()=>{ try{ const r=await fetch(req); if(r.ok){ const c=await caches.open(SHELL); c.put(req,r.clone()); } return r; }catch(err){ const c=await caches.open(SHELL); return (await c.match(req))||Response.error(); } })());
  }
});
