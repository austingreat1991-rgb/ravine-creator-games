// Isolated speed measurements (fixture mode, nothing leaves 127.0.0.1).
// usage: node build/qa-perf.js [repoRoot]   -> prints JSON. Run it on a checkout of main and on this branch to compare.
const {chromium}=require('playwright'); const http=require('http'); const fs=require('fs'); const path=require('path'); const zlib=require('zlib');
const ROOT=path.resolve(process.argv[2]||path.join(__dirname,'..')); const FIX=path.join(__dirname,'fixtures.js');
const mime={'.html':'text/html','.js':'text/javascript','.json':'application/json','.png':'image/png','.jpg':'image/jpeg','.woff2':'font/woff2','.svg':'image/svg+xml','.mp4':'video/mp4','.webmanifest':'application/json'};
let log=[];
const srv=http.createServer((q,s)=>{ let p=decodeURIComponent(q.url.split('?')[0]); if(p.endsWith('/')) p+='index.html'; const f=p==='/build/fixtures.js'?FIX:path.join(ROOT,p);
  fs.readFile(f,(e,b)=>{ if(e){ s.writeHead(404); return s.end(); } if(p.endsWith('index.html')) b=Buffer.from(b.toString().replace('window.APP_MODE="live"','window.APP_MODE="fixture";window.NO_SW=1').replace('<script>/* Ravine Creator Games · October build · core','<script src="./build/fixtures.js"></script><script>/* Ravine Creator Games · October build · core'));
    const ext=path.extname(f); const text=['.html','.js','.json','.svg'].includes(ext); if(p!=='/build/fixtures.js') log.push({p,raw:b.length,wire:text?zlib.gzipSync(b).length:b.length});   // GitHub Pages gzips text
    s.writeHead(200,{'content-type':mime[ext]||'application/octet-stream'}); s.end(b); }); });
const ROUTES=['home','quests','leaderboard','armory','rewards','rewards?v=trophies','library','submissions'];
async function run(b,port,vp,throttle){ const ctx=await b.newContext({viewport:vp,deviceScaleFactor:1}); await ctx.route(u=>!u.href.startsWith('http://127.0.0.1'),r=>r.abort());
  const pg=await ctx.newPage(); const cdp=await ctx.newCDPSession(pg); await cdp.send('Performance.enable'); if(throttle>1) await cdp.send('Emulation.setCPUThrottlingRate',{rate:throttle});
  const M=async()=>Object.fromEntries((await cdp.send('Performance.getMetrics')).metrics.map(m=>[m.name,m.value]));
  log=[]; const t0=Date.now(); await pg.goto(`http://127.0.0.1:${port}/`); await pg.fill('#code','RVFIXPOPUL'); await pg.evaluate(()=>doLogin()); await pg.waitForSelector('#main .anim'); await pg.waitForLoadState('networkidle');
  const first={ms:Date.now()-t0,requests:log.length,rawKB:Math.round(log.reduce((n,x)=>n+x.raw,0)/1024),wireKB:Math.round(log.reduce((n,x)=>n+x.wire,0)/1024),htmlWireKB:Math.round((log.find(x=>x.p.endsWith('index.html'))||{wire:0}).wire/1024),biggest:[...log].sort((a,b)=>b.wire-a.wire).slice(0,4).map(x=>x.p.replace(/^\//,'')+' '+Math.round(x.wire/1024)+'KB')};
  await pg.evaluate(()=>{ window.__calls=[]; const o=FX.rpc; FX.rpc=function(n,a){ window.__calls.push(n); return o.call(FX,n,a); }; window.__cls=0; try{ new PerformanceObserver(l=>{ for(const e of l.getEntries()) if(!e.hadRecentInput) window.__cls+=e.value; }).observe({type:'layout-shift',buffered:false}); }catch(e){} });
  const out={};
  for(const r of ROUTES){ const runs=[]; for(let k=0;k<3;k++){ log=[]; const a=await M();
      const ms=await pg.evaluate(async h=>{ S.cache={}; S.cacheAt={}; window.__calls=[]; window.__cls=0; const [v,qs]=h.split('?'); const t=performance.now(); S.view=v; S.params=Object.fromEntries(new URLSearchParams(qs||'')); try{ history.replaceState(null,'','#/'+h); }catch(e){} await render(); await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))); return performance.now()-t; },r);
      await pg.waitForLoadState('networkidle'); await pg.waitForTimeout(250); const z=await M(); const x=await pg.evaluate(()=>({calls:[...new Set(window.__calls)].length,cls:+window.__cls.toFixed(3),nodes:document.querySelectorAll('#main *').length}));
      runs.push({ms:+ms.toFixed(0),script:+((z.ScriptDuration-a.ScriptDuration)*1000).toFixed(0),layout:+(((z.LayoutDuration-a.LayoutDuration)+(z.RecalcStyleDuration-a.RecalcStyleDuration))*1000).toFixed(0),...x,imgReq:log.length,imgKB:Math.round(log.reduce((n,y)=>n+y.wire,0)/1024)}); }
    runs.sort((p,q)=>p.ms-q.ms); out[r]={...runs[1],firstVisitImgKB:Math.max(...runs.map(x=>x.imgKB))}; }
  await ctx.close(); return {first,routes:out}; }
srv.listen(0,async()=>{ const port=srv.address().port; const b=await chromium.launch(); const res={root:ROOT,desktop:await run(b,port,{width:1440,height:900},1),phone4xCPU:await run(b,port,{width:390,height:844},4)}; console.log(JSON.stringify(res)); await b.close(); srv.close(); });
