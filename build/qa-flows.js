// Isolated workflow checks. Fixture mode only: no network leaves 127.0.0.1, nothing touches production.
// usage: node build/qa-flows.js
const {chromium}=require('playwright'); const http=require('http'); const fs=require('fs'); const path=require('path'); const assert=require('assert');
const ROOT=path.join(__dirname,'..');
const mime={'.html':'text/html','.js':'text/javascript','.json':'application/json','.png':'image/png','.jpg':'image/jpeg','.woff2':'font/woff2','.svg':'image/svg+xml','.mp4':'video/mp4','.webmanifest':'application/json'};
const srv=http.createServer((q,s)=>{ let p=decodeURIComponent(q.url.split('?')[0]); if(p.endsWith('/')) p+='index.html'; const f=path.join(ROOT,p);
  fs.readFile(f,(e,b)=>{ if(e){ s.writeHead(404); return s.end(); } if(p.endsWith('index.html')) b=Buffer.from(b.toString().replace('window.APP_MODE="live"','window.APP_MODE="fixture";window.NO_SW=1').replace('<script>/* Ravine Creator Games · October build · core','<script src="./build/fixtures.js"></script><script>/* Ravine Creator Games · October build · core')); s.writeHead(200,{'content-type':mime[path.extname(f)]||'application/octet-stream'}); s.end(b); }); });
const results=[]; const ok=(n)=>{ results.push('PASS '+n); }; 
async function session(b,port,code,vp,opts={}){ const ctx=await b.newContext({viewport:vp,deviceScaleFactor:opts.dsf||1,reducedMotion:'reduce'}); const ext=[]; await ctx.route(u=>!u.href.startsWith('http://127.0.0.1'),r=>{ ext.push(r.request().url()); r.abort(); });
  if(!opts.showPop) await ctx.addInitScript(()=>{ window.__NO_RPOP=1; });
  const pg=await ctx.newPage(); const errs=[]; pg.on('pageerror',e=>errs.push(e.message)); await pg.goto(`http://127.0.0.1:${port}/`); await pg.fill('#code',code); await pg.evaluate(()=>doLogin()); await pg.waitForTimeout(500);
  await pg.evaluate(()=>{ window.__calls=[]; const o=FX.rpc; FX.rpc=function(n,a){ window.__calls.push(n); return o.call(FX,n,a); }; });
  const go=async h=>{ await pg.evaluate(x=>{ location.hash='#/'+x; },h); await pg.waitForTimeout(700); }; return {ctx,pg,errs,ext,go}; }
srv.listen(0,async()=>{ const port=srv.address().port; const b=await chromium.launch(); let fail=null;
 try{
  // ---- 0. Nov 16 rules pop-up: shows once, Got it closes it, it stays closed after a reload, admin never sees it
  { const {ctx,pg,errs}=await session(b,port,'RVFIXPOPUL',{width:390,height:844},{showPop:true});
    assert.ok(await pg.evaluate(()=>!!document.querySelector('#rpop')),'pop-up shows on first visit'); ok('rules pop-up shows on the first visit');
    assert.ok(await pg.evaluate(()=>document.activeElement&&document.activeElement.id==='rpop-ok'),'focus starts on Got it'); ok('pop-up focus starts on Got it');
    await pg.click('#rpop-ok'); await pg.waitForTimeout(300); assert.ok(!(await pg.evaluate(()=>!!document.querySelector('#rpop'))),'Got it closes it'); ok('Got it closes the pop-up');
    await pg.reload(); await pg.waitForTimeout(1200); assert.ok(!(await pg.evaluate(()=>!!document.querySelector('#rpop'))),'stays closed'); ok('pop-up does not come back after a reload');
    assert.deepEqual(errs,[]); await ctx.close(); }
  { const {ctx,pg}=await session(b,port,'RVFIXADMIN',{width:1440,height:900},{showPop:true});
    assert.ok(!(await pg.evaluate(()=>!!document.querySelector('#rpop'))),'admin does not see it'); ok('admin does not get the creator pop-up'); await ctx.close(); }
  // ---- 1. quest draft -> save -> validation -> submit -> idempotent
  { const {ctx,pg,errs,go}=await session(b,port,'RVFIXPOPUL',{width:1440,height:900}); await go('quests');
    const calls=()=>pg.evaluate(()=>window.__calls.slice());
    await pg.evaluate(()=>pickQuest('nov_aff_first')); await pg.waitForTimeout(200);
    assert.ok(!(await calls()).includes('start_quest'),'selecting a quest in the brief pane must not start it'); ok('brief pane selection creates no entry');
    await pg.evaluate(()=>openQuest('nov_aff_first')); await pg.waitForTimeout(300);
    assert.ok(!(await calls()).includes('start_quest'),'opening the brief must not start it'); ok('opening the full brief creates no entry');
    await pg.click('#startbtn'); await pg.waitForTimeout(600); assert.equal((await calls()).filter(x=>x==='start_quest').length,1); ok('Start quest creates exactly one entry');
    await pg.fill('#f_link','not a link'); await pg.evaluate(()=>document.querySelector('#subbtn').click()); await pg.waitForTimeout(700);
    assert.ok(!(await calls()).includes('submit_quest')||(await pg.evaluate(()=>FX.me().quests.instances.find(i=>i.quest_key==='nov_aff_first').state))==='in_progress','bad link must not submit'); ok('invalid link is rejected and the entry stays a draft');
    assert.equal(await pg.inputValue('#f_link'),'not a link'); ok('draft text kept after the failed submit');
    await pg.evaluate(()=>{ window.__FX_FAIL_SAVE=true; }); await pg.fill('#f_link','https://example.com/fixture-proof'); await pg.waitForTimeout(1800);
    const st1=await pg.evaluate(()=>(document.querySelector('#savestate')||{}).textContent||''); assert.ok(/save|Retry/i.test(st1),'failed save must be shown: '+st1); assert.equal(await pg.inputValue('#f_link'),'https://example.com/fixture-proof'); ok('failed autosave is shown and the text is kept ('+st1.trim().slice(0,40)+')');
    await pg.evaluate(()=>{ window.__FX_FAIL_SAVE=false; }); await pg.fill('#f_link','https://example.com/fixture-proof-2'); await pg.waitForTimeout(1900);
    assert.equal(await pg.evaluate(()=>FX.me().quests.instances.find(i=>i.quest_key==='nov_aff_first').draft.link),'https://example.com/fixture-proof-2'); ok('autosave stores the latest draft after about one second');
    await pg.evaluate(()=>closeDrawer(true)); await pg.evaluate(()=>openQuest('nov_aff_first')); await pg.waitForTimeout(400); assert.equal(await pg.inputValue('#f_link'),'https://example.com/fixture-proof-2'); ok('draft is still there after closing and reopening');
    await pg.evaluate(()=>{ const b=document.querySelector('#subbtn'); b.click(); b.click(); }); await pg.waitForTimeout(900);
    const inst=await pg.evaluate(()=>FX.me().quests.instances.filter(i=>i.quest_key==='nov_aff_first').map(i=>({s:i.state,n:i.evidence.length})));
    assert.equal(inst.length,1); assert.equal(inst[0].s,'submitted'); assert.equal(inst[0].n,1); ok('double-clicking Submit sends once; entry is In review');
    assert.equal(await pg.evaluate(()=>FX.me().quests.xp_earned),60); ok('pending XP is not added to approved XP');
    assert.deepEqual(errs,[]); await ctx.close(); }
  // ---- 2. armory: inspect never equips; equip is explicit; locked cannot equip; cosmetics
  { const {ctx,pg,errs,go}=await session(b,port,'RVFIXPOPUL',{width:1440,height:900}); await go('armory'); const calls=()=>pg.evaluate(()=>window.__calls.slice());
    assert.equal(await pg.locator('.arm-grid .camo-tile').count()>=9,true); const keys=await pg.evaluate(()=>CAMO_KEYS.slice()); assert.equal(keys.length,9); ok('all nine camo IDs render');
    await pg.evaluate(()=>openCamo('gold')); await pg.waitForTimeout(300); assert.ok(!(await calls()).includes('set_camo')); assert.equal(await pg.locator('#drawer #eqbtn').count(),0); ok('inspecting a locked camo does not equip and offers no Equip button');
    await pg.evaluate(()=>closeDrawer(true)); await pg.evaluate(()=>openCamo('desert')); await pg.waitForTimeout(300); assert.ok(!(await calls()).includes('set_camo')); ok('inspecting an owned camo does not equip');
    await pg.click('#drawer #eqbtn'); await pg.waitForTimeout(700); assert.equal((await calls()).filter(x=>x==='set_camo').length,1); assert.equal(await pg.evaluate(()=>FX.camo),'desert'); ok('Equip button equips once');
    await pg.evaluate(()=>equipCosmetic('frame','frame_night_ops')); await pg.waitForTimeout(400); assert.equal(await pg.evaluate(async()=>(await myIdentity()).loadout.frame),'frame_ravine_edge'); ok('locked frame cannot be equipped');
    await pg.evaluate(()=>equipCosmetic('title','title_feedback_pro')); await pg.waitForTimeout(500); assert.equal(await pg.evaluate(async()=>(await myIdentity()).loadout.title),'title_feedback_pro'); ok('owned title equips');
    await pg.evaluate(()=>{ window.__FX_ID=false; API.bust(); }); await go('home'); await go('armory'); assert.equal(await pg.locator('#cosmetics').count(),0); assert.equal(await pg.locator('.arm-grid .camo-tile').count(),9); ok('without the new backend the Armory shows only the nine camos');
    assert.deepEqual(errs,[]); await ctx.close(); }
  // ---- 3. roles and admin
  { const {ctx,pg,errs,go}=await session(b,port,'RVFIXPOPUL',{width:1440,height:900}); const nav=await pg.evaluate(()=>[...document.querySelectorAll('#nav .nitm span:first-of-type')].map(e=>e.textContent)); assert.equal(nav.length,14); ok('creator sees 14 destinations, no admin group');
    await go('admin_rewards'); assert.equal(await pg.evaluate(()=>S.view),'home'); assert.ok(!(await pg.evaluate(()=>window.__calls)).some(x=>/^admin|sync_payouts/.test(x))); ok('creator opening an admin link lands on Home and calls no admin data');
    await ctx.close(); }
  { const {ctx,pg,errs,go}=await session(b,port,'RVFIXADMIN',{width:1440,height:900}); const nav=await pg.evaluate(()=>[...document.querySelectorAll('#nav .nitm')].length); assert.equal(nav,18); ok('admin sees all 18 destinations');
    await go('admin'); const calls=()=>pg.evaluate(()=>window.__calls.filter(x=>/approve_quest|return_quest|reject_quest/.test(x)));
    assert.ok(await pg.locator('#main').innerText().then(t=>/Answer a real objection/.test(t))); ok('review queue lists the submitted entry');
    await pg.keyboard.press('j'); await pg.keyboard.press('k'); assert.deepEqual(await calls(),[]); ok('J and K move focus without deciding anything');
    await pg.keyboard.press('c'); await pg.waitForTimeout(300); const ta=pg.locator('#drawer textarea').first(); assert.ok(await ta.count()); await ta.focus(); await pg.keyboard.type('a quick check'); assert.deepEqual(await calls(),[]); ok('typing the letter a inside a note does not approve');
    await pg.keyboard.press('Escape'); await pg.waitForTimeout(300); assert.ok(await pg.evaluate(()=>!document.querySelector('#drawer').classList.contains('open')&&!!document.activeElement.closest('#aq_list .aq')),'focus should return to the queue entry'); assert.deepEqual(await calls(),[]); ok('Escape closes the note without deciding, and focus returns to the same queue entry');
    await pg.keyboard.press('Control+a'); assert.deepEqual(await calls(),[]); ok('Ctrl+A is ignored by the approve shortcut');
    await pg.keyboard.press('a'); await pg.waitForTimeout(600); assert.deepEqual(await calls(),['approve_quest']); ok('A approves the focused entry exactly once (test data)');
    for(const r of ['admin_pace','admin_contest','admin_rewards']){ await go(r); const t=await pg.locator('#main').innerText(); assert.ok(t.length>200&&!/could not load/i.test(t),r+' did not render'); }
    assert.ok(/#19|19/.test(await (await go('admin_pace'),pg.locator('#main').innerText()))); ok('Elite cut line, Contest & imports and Rewards & payouts render for admin');
    assert.deepEqual(errs,[]); await ctx.close(); }
  // ---- 4. keyboard
  { const {ctx,pg,errs,go}=await session(b,port,'RVFIXPOPUL',{width:1440,height:900}); await go('quests');
    const seen=new Set(); let bad=0, unnamed=0; const badList=[]; for(let i=0;i<70;i++){ await pg.keyboard.press('Tab'); const f=await pg.evaluate(()=>{ const e=document.activeElement; if(!e||e===document.body) return null; if(!e.dataset.qaTab) e.dataset.qaTab=String((window.__qaTab=(window.__qaTab||0)+1)); const r=e.getBoundingClientRect(); const cs=getComputedStyle(e); const name=(e.getAttribute('aria-label')||e.textContent||e.getAttribute('placeholder')||e.value||'').trim(); return {tag:e.dataset.qaTab,cls:'',vis:r.width>0&&r.height>0,outline:cs.outlineStyle!=='none'&&parseFloat(cs.outlineWidth)>0,name:name.slice(0,30)}; }); if(!f) continue; seen.add(f.tag+'.'+f.cls); if(!f.vis||!f.outline){ bad++; badList.push(f.name||'(no name)'); } if(!f.name){ unnamed++; } }
    assert.ok(seen.size>25,'tab order too short: '+seen.size); assert.equal(bad,0,'focused element without a visible focus ring: '+badList.slice(0,5).join(' | ')); assert.equal(unnamed,0,'focused control without a name'); ok('70 Tab presses on Quests: every stop is visible, named and shows a focus ring ('+seen.size+' distinct controls)');
    await pg.evaluate(()=>document.querySelector('#qlist .qcard').focus()); await pg.keyboard.press('Enter'); await pg.waitForTimeout(300); assert.ok(await pg.evaluate(()=>!!document.querySelector('#qlist .qcard.sel'))); ok('Enter on a quest card selects it');
    await pg.evaluate(()=>document.querySelector('#qbrief .qb-go').focus()); await pg.keyboard.press('Enter'); await pg.waitForTimeout(400); assert.ok(await pg.evaluate(()=>document.querySelector('#drawer').classList.contains('open'))); await pg.keyboard.press('Escape'); await pg.waitForTimeout(400); assert.ok(await pg.evaluate(()=>!document.querySelector('#drawer').classList.contains('open')&&document.activeElement.classList.contains('qb-go'))); ok('Enter opens the brief, Escape closes it and focus returns to the button that opened it');
    await go('armory'); await pg.evaluate(()=>document.querySelector('.arm-grid .camo-tile.lk').focus()); await pg.keyboard.press('Enter'); await pg.waitForTimeout(300); assert.ok(!(await pg.evaluate(()=>window.__calls)).includes('set_camo')); ok('Enter on a locked camo inspects only');
    assert.deepEqual(errs,[]); await ctx.close(); }
  // ---- 5. 200% zoom (1440x900 window at 200% = 720x450 CSS px) and a short desktop window
  { for(const [code,routes] of [['RVFIXPOPUL',['home','library','spy','broll','quests','rewards','rewards?v=trophies','armory','submissions','analytics','links','leaderboard','compete','pace','profile']],['RVFIXADMIN',['admin','admin_pace','admin_contest','admin_rewards']]]){
      const {ctx,pg,errs,go}=await session(b,port,code,{width:720,height:450},{dsf:2}); for(const r of routes){ await go(r); const o=await pg.evaluate(()=>({sw:document.documentElement.scrollWidth,cw:document.documentElement.clientWidth,h1:!!document.querySelector('#main h1, #main h2')})); assert.ok(o.sw<=o.cw+1,`${r} scrolls sideways at 200% (${o.sw}>${o.cw})`); assert.ok(o.h1,r+' has no heading'); } assert.deepEqual(errs,[]); await ctx.close(); }
    ok('200% zoom: all 18 destinations plus Trophy Room fit with no sideways scroll');
    const {ctx,pg,go}=await session(b,port,'RVFIXADMIN',{width:1280,height:520}); const sc=await pg.evaluate(()=>{ const n=document.querySelector('.side #nav'); n.scrollTop=n.scrollHeight; const last=[...n.querySelectorAll('.nitm')].pop().getBoundingClientRect(); const who=document.querySelector('#who').getBoundingClientRect(); return {scrolls:n.scrollHeight>n.clientHeight,lastVisible:last.bottom<=who.top+1,who:who.bottom<=521}; }); assert.ok(sc.scrolls&&sc.lastVisible&&sc.who); ok('short desktop window: menu scrolls on its own, last admin item reachable, account block stays visible'); await ctx.close(); }
  // ---- 6. privacy + no outside requests
  { const {ctx,pg,ext,go}=await session(b,port,'RVFIXPOPUL',{width:1440,height:900}); await go('leaderboard?all=1'); const t=await pg.locator('#main').innerText(); const money=(t.match(/\$[\d,]+(\.\d\d)?/g)||[]); const others=[9120,7450,6020,4880,3910,3300,2710,2150,1780,1210,980,640,410,220].map(v=>'$'+v.toLocaleString('en-US'));
    assert.ok(!money.some(m=>others.includes(m)),'another creator sales figure is on the page'); ok('leaderboard shows no other creator sales figure (own GMV and own gaps only)');
    await go('home'); await go('rewards'); assert.ok(!/ready to claim|submit claim/i.test(await pg.locator('#main').innerText())); ok('Rewards shows no claim action for November');
    const logo=await pg.evaluate(()=>{ const i=document.querySelector('.side-brand img.wm'); return {ok:i.complete&&i.naturalWidth===238&&i.naturalHeight===110,src:i.getAttribute('src')}; }); assert.ok(logo.ok&&logo.src==='./official-ravine-logo.png'); ok('official wordmark loads from the local file at 238x110');
    assert.equal(ext.filter(u=>!/^data:|^blob:/.test(u)&&!/fixture\.invalid|calendly|frame\.io|cdn\.jointrybe/.test(u)).length,0,'unexpected outside request: '+ext.slice(0,3).join(' ')); ok('no request left the test machine except blocked media links'); await ctx.close(); }
 }catch(e){ fail=e; }
 console.log(results.join('\n')); if(fail){ console.log('FAIL '+(fail.message||fail).toString().slice(0,400)); process.exitCode=1; } else console.log(`ALL ${results.length} FLOW CHECKS PASSED`);
 await b.close(); srv.close(); });
