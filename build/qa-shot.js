// usage: node shot.js <outdir> <code> <w>x<h> route1 route2 ...   (fixture mode; nothing touches production)
const {chromium}=require('playwright'); const http=require('http'); const fs=require('fs'); const path=require('path');
const ROOT='/home/claude/ravine-creator-games';
const [,, out, code, size, ...routes]=process.argv; const [W,H]=size.split('x').map(Number);
const mime={'.html':'text/html','.js':'text/javascript','.json':'application/json','.png':'image/png','.jpg':'image/jpeg','.woff2':'font/woff2','.mp4':'video/mp4','.webmanifest':'application/json'};
const srv=http.createServer((q,s)=>{ let p=decodeURIComponent(q.url.split('?')[0]); if(p.endsWith('/')) p+='index.html'; const f=path.join(ROOT,p);
  fs.readFile(f,(e,b)=>{ if(e){ s.writeHead(404); return s.end(); } if(p.endsWith('index.html')) b=Buffer.from(b.toString().replace('window.APP_MODE="live"','window.APP_MODE="fixture";window.NO_SW=1').replace('<script>/* Ravine Creator Games · October build · core','<script src="./build/fixtures.js"></script><script>/* Ravine Creator Games · October build · core')); s.writeHead(200,{'content-type':mime[path.extname(f)]||'application/octet-stream'}); s.end(b); }); });
srv.listen(0,async()=>{ const port=srv.address().port; const b=await chromium.launch(); const ctx=await b.newContext({viewport:{width:W,height:H},deviceScaleFactor:1,reducedMotion:'reduce'});
  await ctx.route(u=>!u.href.startsWith('http://127.0.0.1'),r=>r.abort());
  const pg=await ctx.newPage(); const errs=[]; pg.on('pageerror',e=>errs.push('PAGEERR '+e.message+' '+(e.stack||'').split('\n').slice(1,3).join(' '))); pg.on('console',m=>{ if(m.type()==='error'&&!/ERR_FAILED|net::/.test(m.text())) errs.push('CONSOLE '+m.text().slice(0,200)); });
  await pg.goto(`http://127.0.0.1:${port}/`); await pg.fill('#code',code); await pg.evaluate(()=>doLogin()); await pg.waitForTimeout(600);
  fs.mkdirSync(out,{recursive:true});
  for(const r of routes){ const [route,act]=r.split('@'); await pg.evaluate(h=>{ location.hash='#/'+h; },route); await pg.waitForTimeout(900);
    if(act){ try{ await pg.evaluate(act); await pg.waitForTimeout(500);}catch(e){ errs.push('ACT '+route+' '+e.message.slice(0,150)); } }
    const name=route.replace(/[^a-z0-9_]+/gi,'-')+(act?'-act':'')+`-${W}`; const full=process.env.FULL!=='0';
    await pg.screenshot({path:path.join(out,name+'.png'),fullPage:full}); 
    const ov=await pg.evaluate(()=>({sw:document.documentElement.scrollWidth,cw:document.documentElement.clientWidth,title:document.title,h1:(document.querySelector('#main h1')||{}).textContent||''}));
    console.log(route, JSON.stringify(ov), ov.sw>ov.cw?'HSCROLL!':''); }
  if(errs.length) console.log(errs.join('\n')); await b.close(); srv.close(); });
