"""
RAVINE-QUESTS-V2 — the twelve real quests, live for every creator.

Applies exact, counted replacements to index.html. Every replacement must match
exactly once or the script refuses to write, so a drifted template can never be
half-patched. Run after refresh.py:

  python3 build/patch_quests.py            # patches ./index.html in place
  python3 build/patch_quests.py --check    # just verify every anchor is present

What changes
  * QUESTS = the 12 quests from the progression spec (ids 101-112). Progress is
    per creator and per window (month, or Central day for the comment quest),
    computed from their own approved submissions — nothing is self-logged.
  * XP = the sum of approved submissions (comment quest capped at 30 XP/month).
    Points land only when Austin approves. The old award()/logQ self-award path
    is gone.
  * Quests and My submissions are visible to creators again (the Q4 placeholder
    is removed from the sidebar, phone nav, home and the two views).
  * Evidence: each quest asks for the links it needs (evn) plus an optional note;
    the video upload is required for single-video quests and optional otherwise.
    Austin-marked quests (call, streak, leaderboard) have no creator form; Austin
    marks them from the quest page and the record goes through the same
    approve path as everything else.
  * Creators pull only their own rows from the queue; Austin pulls everything
    and gets a notification when something new is waiting.
"""
import re, sys, os, json

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
IDX = os.path.join(ROOT, 'index.html')
html = open(IDX, encoding='utf-8').read()
CHECK = '--check' in sys.argv
if 'RAVINE-QUESTS-V2' in html:
    print('already patched'); sys.exit(0)

REPL = []
def rep(old, new, what):
    REPL.append((old, new, what))

# ---------------------------------------------------------------- 1. the quests
QUESTS = [
 dict(id=101,k='post3',t='Post three videos for review in Skool',tag='Community',sc='home',x=15,lim=1,win='month',video='none',
      brief='Put three finished videos into the Skool review channel so other creators and Austin can react before you scale the idea.',
      steps=['Post video one','Post video two','Post video three'],link=['Open Skool','skool'],ev='Link to each Skool post',evn=3),
 dict(id=102,k='recreate',t="Recreate another brand's ad format",tag='Create',sc='range',x=15,lim=1,win='month',video='req',
      brief='Take a structure that works for another brand and rebuild it for Ravine with your own footage and your own words. Structure only, never a copy.',
      steps=['Pick a format from the library','Film your own version','Submit it on Trybe'],link=['Open the ad library','watch'],ev='Trybe submission link',evn=1),
 dict(id=103,k='unaware',t='Create an unaware market video',tag='Create',sc='woods',x=15,lim=1,win='month',video='req',
      brief='Make a video for someone who has never thought about the problem yet. No product talk in the first few seconds.',
      steps=['Write the opening','Film it','Submit it on Trybe'],link=['Open Trybe','trybe'],ev='Trybe submission link',evn=1),
 dict(id=104,k='openings3',t='Film three openings for one concept',tag='Create',sc='dawn',x=10,lim=1,win='month',video='opt',
      brief='One concept, three different first three seconds. The opening is the part that decides everything.',
      steps=['Opening one','Opening two','Opening three'],link=None,ev='Link to the three cuts',evn=1),
 dict(id=105,k='feedback',t='Apply feedback and submit an improved version',tag='Create',sc='site',x=15,lim=2,win='month',video='opt',
      brief='Take a note you were given, act on it, and submit the better version.',
      steps=['Read the feedback','Recut','Submit the revision'],link=['Open Trybe','trybe'],ev='Original link, then the revision link',evn=2),
 dict(id=106,k='call',t='Attend the weekly call',tag='Coach',sc='home',x=5,lim=4,win='month',video='none',admin=1,
      brief='The weekly group call — day and time are posted in Skool. Austin marks attendance from the call record, nothing to send.',
      steps=['Join the call'],link=['Book or join','call'],ev='Marked by Austin',evn=0),
 dict(id=107,k='oneonone',t='Attend a 1:1 with Austin',tag='Coach',sc='home',x=10,lim=1,win='month',video='none',
      brief='Book it, turn up, and leave with one action. Booking on its own does not count.',
      steps=['Book the slot','Attend','Write down your action'],link=['Book a 1:1','call'],ev='The action you committed to, in your words',evn=1,free=1),
 dict(id=108,k='objection',t='Turn a real customer objection into a video',tag='Create',sc='porch',x=10,lim=1,win='month',video='req',
      brief='Find something a real buyer actually said they were unsure about, and answer it on camera.',
      steps=['Find the objection','Film the answer','Submit it'],link=['Open Trybe','trybe'],ev='Trybe submission link, then where the objection came from',evn=2),
 dict(id=109,k='launch5',t='Launch five distinct TOF or MOF concepts',tag='Create',sc='ridge',x=25,lim=1,win='month',video='opt',
      brief='Five genuinely different concepts, not five cuts of one idea. Reviewed together as a set.',
      steps=['Concept one','Concept two','Concept three','Concept four','Concept five'],link=['Open Trybe','trybe'],ev='Five submission links',evn=5),
 dict(id=110,k='comment',t="Leave useful feedback on another creator's video",tag='Community',sc='home',x=1,lim=3,win='day',video='none',cap=30,
      brief='A specific, useful note on someone else\u2019s work. Not an emoji, not \u201cnice one\u201d, not your own post. Up to 3 a day and 30 XP a month.',
      steps=['Leave the comment'],link=['Open Skool','skool'],ev='Link to your comment',evn=1),
 dict(id=111,k='streak',t='Contribute on seven days in a row',tag='Habit',sc='ridge',x=5,lim=4,win='month',video='none',admin=1,
      brief='Seven days running with something posted, submitted or reviewed. Austin confirms it against the daily record.',
      steps=['Show up seven days straight'],link=None,ev='Confirmed by Austin',evn=0),
 dict(id=112,k='leader',t='Finish first on the Skool seven day leaderboard',tag='Habit',sc='marsh',x=10,lim=4,win='month',video='none',admin=1,
      brief='Top of the Skool seven day board at the weekly cutoff. Austin verifies it from a dated snapshot.',
      steps=['Be #1 at the cutoff'],link=['Open the leaderboard','skool'],ev='Verified by Austin',evn=0),
]
for q in QUESTS:
    q['need'] = q['lim']; q['got'] = 0; q['pend'] = 0
qjs = json.dumps(QUESTS, separators=(',', ':'), ensure_ascii=False)

i = html.index('let QUESTS=[')
j = html.index('];', i) + 2
old_quests = html[i:j]
rep(old_quests, 'let QUESTS=' + qjs + ';\n/* RAVINE-QUESTS-V2 */', 'QUESTS array')

# ---------------------------------------------------------------- 2. progress + XP engine (inserted after the claim helpers)
ENGINE = r"""
/* ===================== RAVINE-QUESTS-V2 · progress and XP =====================
   Nothing here is self-reported. A quest moves only when a submission for it is
   approved, and the approval is a server call Austin makes with his admin key. */
const QLINKS={skool:'https://www.skool.com/ravine-trybe-6834',trybe:'https://www.jointrybe.com'};
function ctParts(ts){const d=new Date(ts||Date.now());
 const p=new Intl.DateTimeFormat('en-US',{timeZone:'America/Chicago',year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(d);
 const g=k=>p.find(x=>x.type===k).value; return {ym:g('year')+'-'+g('month'),ymd:g('year')+'-'+g('month')+'-'+g('day')};}
const qWin=(q,ts)=>q.win==='day'?ctParts(ts).ymd:ctParts(ts).ym;
const qHref=q=>!q.link?'':q.link[1]==='watch'?"javascript:go('feed')":q.link[1]==='call'?(window.BOOK_URL||'https://www.skool.com/ravine-trybe-6834/calendar'):(QLINKS[q.link[1]]||'#');
function xpOf(cid){
 // approved rows only. Each quest pays at most `need` times per window (so a
 // fifth call in a month is worth nothing), and the comment quest is also
 // capped at 30 XP a month. Older entries win when there are too many.
 let xp=0; const cm={}, seen={};
 SUBS.filter(s=>s.cid===cid&&s.status==='approved').slice().sort((a,b)=>a.ts-b.ts).forEach(s=>{
  const q=QUESTS.find(x=>x.id===s.qid); const g=Number(s.xp)||0;
  if(!q){xp+=g;return}                                   // legacy entries from the first board
  const wk=s.qid+':'+qWin(q,s.ts); seen[wk]=(seen[wk]||0)+1; if(seen[wk]>q.need)return;
  if(q.cap){const k=qWin({win:'month'},s.ts); cm[k]=(cm[k]||0); const room=Math.max(0,q.cap-cm[k]); const add=Math.min(room,g); cm[k]+=add; xp+=add;}
  else xp+=g;});
 return xp;
}
function syncQuestProgress(){
 const now=Date.now();
 QUESTS.forEach(q=>{const w=qWin(q,now);
  const mine=SUBS.filter(s=>s.cid===ME&&s.qid===q.id&&qWin(q,s.ts)===w);
  q.got=Math.min(q.need,mine.filter(s=>s.status==='approved').length);
  q.pend=mine.filter(s=>s.status==='pending').length;});
 CR.forEach(c=>{c.xp=xpOf(c.id)});
}
const qOpen=q=>q.got<q.need;
/* Austin marks attendance / streaks / leaderboard wins. The record is written
   as a normal pending submission and then approved through decide(), so it is
   gated by the same admin key as every other point on the board. */
window.markQ=async(qid)=>{
 if(!me().admin)return;
 const q=QUESTS.find(x=>x.id===qid);if(!q)return;
 const sel=$('#qMarkWho');const cid=sel?parseInt(sel.value,10):NaN;const c=CR.find(x=>x.id===cid);
 if(!c){toast('Pick a creator first');return}
 const w=qWin(q,Date.now()), had=SUBS.filter(s=>s.cid===c.id&&s.qid===q.id&&s.status!=='denied'&&qWin(q,s.ts)===w).length;
 if(had>=q.need){toast(c.n.split(' ')[0]+' is already at '+q.need+' for this '+(q.win==='day'?'day':'month'));return}
 const id='s'+Date.now().toString(36)+Math.random().toString(36).slice(2,7);
 const sub={id,cid:c.id,cname:c.n,qid,qtitle:q.t,qtag:q.tag,xp:q.x,link:'',note:'Marked by Austin',file:'',size:0,dur:0,poster:null,ts:Date.now(),status:'pending',reason:'',video_url:null};
 if(LIVE()){
  let r=null; try{r=await REMOTE.push(sub,null)}catch(e){r={ok:false,error:e.message}}
  if(!r||r.ok===false){toast('Could not record it — '+((r&&r.error)||'no connection'));return}
 }
 SUBS.unshift(sub);saveSubs();
 await decideQ(id,'approved');
};
"""
anchor = "const pendingAll=()=>SUBS.filter(s=>s.status==='pending');\n"
rep(anchor, anchor + ENGINE, 'engine insert')

# ---------------------------------------------------------------- 3. render(): refresh progress first
rep("function render(){\n const c=me();\n", "function render(){\n try{syncQuestProgress()}catch(e){}\n const c=me();\n", 'render hook')

# ---------------------------------------------------------------- 4. kill the self-award path
i = html.index('window.logQ=id=>')
j = html.index('window.mkQuest=id=>', i)
rep(html[i:j], "window.logQ=id=>{openQ(id)};   /* RAVINE-QUESTS-V2: nothing is self-logged */\n", 'logQ')

# ---------------------------------------------------------------- 5. decideQ: XP comes from the approved rows
old = """ if(status==='approved'){
  const q=QUESTS.find(x=>x.id===s.qid);
  if(q){q.got=Math.min(q.need,q.got+1);q.subs=(q.subs||0)+1;
   if(q.got>=q.need)award(s.cid,q.x,'completed '+q.t);
   else {const c=CR.find(z=>z.id===s.cid);if(c)c.xp+=Math.round(q.x*M()/Math.max(1,q.need));}}
  pushCreator(s.cname.split(' ')[0]+', your '+s.qtitle+' video is approved','+'+(s.xp*M())+' XP just landed. Keep the run going.');"""
new = """ if(status==='approved'){
  /* RAVINE-QUESTS-V2: the approved row IS the award — XP and progress are
     recomputed from SUBS on the next render, on every device that syncs. */
  try{syncQuestProgress()}catch(e){}
  pushCreator(s.cname.split(' ')[0]+', your '+s.qtitle+' entry is approved','+'+(s.xp*M())+' XP just landed. Keep the run going.');"""
rep(old, new, 'decideQ')

# ---------------------------------------------------------------- 6. sendQ: evidence links, optional video
old_send = html[html.index('window.sendQ=async qid=>{'):html.index('/* ---------- admin decides ---------- */')]
new_send = r"""window.sendQ=async qid=>{
 const q=QUESTS.find(x=>x.id===qid);if(!q)return;
 if(q.admin){toast('Austin marks this one');return}
 if(q.video==='req'&&!PENDFILE){toast('Attach your video first');return}
 const links=[];for(let n=0;n<(q.evn||0);n++){const e=$('#qUpLink'+n);const v=e?e.value.trim():'';
  if(!v){toast(q.free?'Write it in the box first':'Paste link '+(n+1)+' first');return}
  if(!q.free&&!/^https?:\/\/\S+$/i.test(v)){toast('Link '+(n+1)+' needs to be a full https:// link');return}
  links.push(v);}
 if(!qOpen(q)){toast('You have already completed this one for the '+(q.win==='day'?'day':'month'));return}
 if(q.pend>=q.need){toast('That one is already with Austin');return}
 const link=links.join('\n');
 const note=($('#qUpNote')&&$('#qUpNote').value.trim())||'';
 const c=me();
 const id='s'+Date.now().toString(36)+Math.random().toString(36).slice(2,7);
 const file=PENDFILE;
 const sub={id,cid:c.id,cname:c.n,qid,qtitle:q.t,qtag:q.tag,xp:q.x,
   link,note,file:file?file.name:'',size:file?file.size:0,dur:file?(file.__dur||0):0,
   poster:file?(file.__poster||null):null,ts:Date.now(),status:'pending',reason:'',video_url:null};
 const btn=$('#qSendBtn');if(btn){btn.disabled=true;btn.textContent='Sending…'}
 PENDFILE=null;                       // taken; a double tap cannot send it twice
 if(file)blobPut(id,file).catch(()=>{});   // local copy is best-effort, never blocks the send
 let sent=false, err='';
 try{
  const r=await REMOTE.push(sub,file);
  if(r&&r.video_url)sub.video_url=r.video_url;
  sent=!!(r&&r.ok!==false);
  if(!sent)err=(r&&r.error)||'server refused it';
 }catch(e){err=e.name==='AbortError'?'timed out':e.message}
 if(LIVE()&&!sent){
  sub.queued=true; PENDFILE=file;
  if(btn){btn.disabled=false;btn.textContent='Send for approval'}
  toast('Could not send it — '+err+'. Nothing was lost, try again.');
  return;
 }
 SUBS.unshift(sub);saveSubs();
 notifyAdmin(sub);
 render();
 toast(LIVE()?'Sent to Austin for approval':'Submitted — waiting on approval');
};

"""
rep(old_send, new_send, 'sendQ')

# ---------------------------------------------------------------- 7. the form inside a quest
old_up = html[html.index('function questUpload(q){'):html.index('/* ===================== VIEWS ===================== */')]
new_up = r"""function questUpload(q){
 const cl=claimed(q.id);
 const mine=subsFor(ME,q.id);
 const pend=mine.filter(s=>s.status==='pending');
 const done=!qOpen(q);
 const hist=mine.length?`<div class="sec" style="margin-top:20px"><h2 style="font-size:14px">Your entries for this quest</h2>
    <span class="mini">${pend.length} waiting</span></div>
   <div style="display:grid;gap:11px">${mine.slice(0,12).map(s=>subCard(s,false)).join('')}</div>`:'';
 if(q.admin){
  const adminBox=me().admin?`<div class="form" style="margin-top:14px">
    <div class="field"><label>Mark it for</label><select id="qMarkWho">${CR.filter(x=>!x.admin).sort((a,b)=>a.n.localeCompare(b.n)).map(x=>`<option value="${x.id}">${esc(x.n)}</option>`).join('')}</select></div>
    <button class="btn" onclick="markQ(${q.id})">Mark done · +${q.x*M()} XP</button>
    <div class="mini" style="margin-top:6px">Goes through the same approval record as everything else.</div></div>`:'';
  return `<div class="g p" style="margin-top:14px" id="qUpWrap"><h3>Austin marks this one</h3>
   <div class="sub">${esc(q.ev)}. Nothing to send — just do it, and the ${q.x*M()} XP lands when he confirms it.</div>
   ${q.link?`<a class="btn gh" style="margin-top:14px" href="${qHref(q)}" ${q.link[1]==='watch'?'':'target="_blank" rel="noopener"'}>${esc(q.link[0])}</a>`:''}
   ${adminBox}${hist}</div>`;
 }
 if(done&&!pend.length)return `<div class="g p" style="margin-top:14px" id="qUpWrap"><h3>Done for ${q.win==='day'?'today':'this month'}</h3>
   <div class="sub">${q.got}/${q.need} approved. ${q.win==='day'?'Back tomorrow.':'It opens again on the 1st.'}</div>${hist}</div>`;
 if(pend.length>=q.need-q.got)return `<div class="g p" style="margin-top:14px" id="qUpWrap"><div style="display:flex;align-items:center;justify-content:space-between;gap:10px;flex-wrap:wrap"><h3 style="margin:0">With Austin</h3><span class="pill warn">● ${pend.length} waiting</span></div>
   <div class="sub" style="margin-top:6px">He reviews it and the ${q.x*M()} XP lands the moment he approves. ${q.win==='day'?'':'Nothing else to send for this one right now.'}</div>${hist}</div>`;
 if(!cl)return `<div class="g p" style="margin-top:14px" id="qUpWrap"><h3>Take this quest</h3>
  <div class="sub">Claim it, do the work, send the proof here. Austin reviews it and approves — that is when the ${q.x*M()} XP lands.</div>
  <button class="btn" style="margin-top:14px" onclick="claimQ(${q.id})">${ico('target',16)} I'm working on this quest</button>${hist}</div>`;
 const linkInputs=[];for(let n=0;n<(q.evn||0);n++){
  const lbl=q.free?esc(q.ev):(q.evn===1?esc(q.ev):esc(q.ev)+' · '+(n+1)+' of '+q.evn);
  linkInputs.push(`<div class="field"><label>${lbl}</label><input id="qUpLink${n}" placeholder="${q.free?'One sentence, your words':'https://…'}"></div>`);}
 return `<div class="g p" style="margin-top:14px" id="qUpWrap">
  <div style="display:flex;align-items:center;justify-content:space-between;gap:10px;flex-wrap:wrap">
   <h3 style="margin:0">Send your proof</h3><span class="pill live">● Claimed</span></div>
  <div class="sub" style="margin-top:6px">${q.video==='req'?'Attach the cut and the link. ':''}Austin reviews it — the ${q.x*M()} XP lands the moment he approves.</div>
  <div class="form" style="margin-top:14px">
   ${q.video!=='none'?`<label class="qdrop" for="qUpInput">
    <input type="file" id="qUpInput" accept="video/*" hidden onchange="pickQFile(this,${q.id})">
    <div class="qdi">${ico('play',22)}</div>
    <div><b>${q.video==='req'?'Choose your video':'Attach a video'} ${q.video==='opt'?'<span class="mini">(optional)</span>':''}</b><div class="mini">MP4 or MOV, up to 500MB</div></div>
   </label><div id="qUpState"></div>`:''}
   ${linkInputs.join('')}
   <div class="field"><label>Anything Austin should know <span class="mini">(optional)</span></label>
    <input id="qUpNote" placeholder="Shot at the range at golden hour, hook lands at 1s"></div>
   <div style="display:flex;gap:9px;flex-wrap:wrap">
    <button class="btn" id="qSendBtn" onclick="sendQ(${q.id})">Send for approval</button>
    <button class="btn gh" onclick="unclaimQ(${q.id})">Drop this quest</button></div>
  </div>${hist}</div>`;
}

"""
rep(old_up, new_up, 'questUpload')

# ---------------------------------------------------------------- 8. subCard: links list, no fake file line
old = """   <div class="mini" style="margin-top:3px">${adminView?esc(s.cname)+' · ':''}${esc(s.file)} · ${(s.size/1048576).toFixed(1)} MB · worth +${s.xp*M()} XP</div>"""
new = """   <div class="mini" style="margin-top:3px">${adminView?esc(s.cname)+' · ':''}${s.file?esc(s.file)+' · '+(s.size/1048576).toFixed(1)+' MB · ':''}worth +${s.xp*M()} XP</div>
   ${(s.link||'').split('\\n').filter(Boolean).map((l,n)=>/^https?:/i.test(l)?`<div class="mini" style="margin-top:4px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap"><a href="${esc(l)}" target="_blank" rel="noopener" style="color:var(--o2)">${ico('ext',12)} ${esc(l.replace(/^https?:\\/\\/(www\\.)?/,'').slice(0,70))}</a></div>`:`<div class="mini" style="margin-top:4px;color:var(--tx2)">“${esc(l)}”</div>`).join('')}"""
rep(old, new, 'subCard links')
old = """    <button class="btn sm gh" onclick="playSub('${s.id}')">${ico('play',14)} Watch</button>
    ${adminView&&st==='pending'?"""
new = """    ${s.file||s.video_url?`<button class="btn sm gh" onclick="playSub('${s.id}')">${ico('play',14)} Watch</button>`:''}
    ${adminView&&st==='pending'?"""
rep(old, new, 'subCard watch')
old = """    ${s.link?`<a class="btn sm gh" href="${esc(s.link)}" target="_blank" rel="noopener">${ico('ext',14)} Their post</a>`:''}
   </div></div></div>`;"""
new = """   </div></div></div>`;"""
rep(old, new, 'subCard post link')
old = """  <div class="apt" onclick="playSub('${s.id}')">
   ${s.poster?`<img src="${s.poster}" alt="">`:'<div class="ph"></div>'}
   <div class="vp"><div>▶</div></div>"""
new = """  <div class="apt" onclick="${s.file||s.video_url?`playSub('${s.id}')`:''}">
   ${s.poster?`<img src="${s.poster}" alt="">`:'<div class="ph"></div>'}
   ${s.file||s.video_url?'<div class="vp"><div>▶</div></div>':''}"""
rep(old, new, 'subCard poster')

# ---------------------------------------------------------------- 9. views: unhide, real copy
rep("quests(){\n /* RAVINE-QUESTSOON-V1 */ if(!me().admin)return QSOON_VIEW();\n", "quests(){\n", 'quests gate')
rep("function approvalsView(){\n /* RAVINE-QUESTSOON-V1 */ if(!me().admin)return QSOON_VIEW();\n", "function approvalsView(){\n", 'approvals gate')
old = """     <ol style="margin:12px 0 0 17px;color:var(--tx2);font-size:13px;line-height:1.85">
      <li>Watch three references in this angle before you touch a camera.</li>
      <li>Write down what happens at 0-3s in each one. Look for the shape they share.</li>
      <li>Shoot your version in your own setting, with your own words.</li>
      <li>Upload it right here and send it to Austin. Points land when he approves.</li></ol>
     <div class="note" style="margin-top:14px">${q.subs} creators have submitted to this quest · $${q.paid} paid out on it so far.</div></div>"""
new = """     <ol style="margin:12px 0 0 17px;color:var(--tx2);font-size:13px;line-height:1.85">
      ${q.steps.map(s=>`<li>${esc(s)}</li>`).join('')}
      <li>${q.admin?'Austin marks it — points land when he confirms.':'Send the proof here. Points land when Austin approves.'}</li></ol>
     <div class="note" style="margin-top:14px">+${q.x*M()} XP each · up to ${q.need} ${q.win==='day'?'a day':'a month'}${q.cap?` · ${q.cap} XP a month max`:''} · proof: ${esc(q.ev)}.${q.link?` <a href="${qHref(q)}" ${q.link[1]==='watch'?'':'target="_blank" rel="noopener"'} style="color:var(--o2)">${esc(q.link[0])} →</a>`:''}</div></div>"""
rep(old, new, 'quest how-to')
rep("""  <div class="player anim">
   <div><div class="stage">${th?`<img src="${th}">`:art(q.tag,q.id*11)}""",
    """  <div class="player anim">
   <div>${q.tag==='Create'?`<div class="stage">${th?`<img src="${th}">`:art(q.tag,q.id*11)}""", 'quest stage open')
rep("""     <a class="btn" href="${linkOf(r)}" target="_blank" rel="noopener">▶  Watch the reference</a></div></div>
    <div class="stats" style="margin-top:13px">""",
    """     <a class="btn" href="${linkOf(r)}" target="_blank" rel="noopener">▶  Watch the reference</a></div></div>`:`<div class="stage">${art(q.tag,q.id*11)}<div class="stagegrad"><div class="lbl" style="color:var(--o2)">${esc(q.tag).toUpperCase()} QUEST</div><div style="font-size:16px;font-weight:750;letter-spacing:-.3px;margin:6px 0 4px">${esc(q.t)}</div></div></div>`}
    <div class="stats" style="margin-top:13px">""", 'quest stage close')
rep("""     <div class="st"><div class="v mono">${q.got}/${q.need}</div><div class="k">Your progress</div></div>
    </div></div>""",
    """     <div class="st"><div class="v mono">${q.got}/${q.need}</div><div class="k">Approved ${q.win==='day'?'today':'this month'}</div></div>
     ${q.pend?`<div class="st"><div class="v mono" style="color:var(--warn)">${q.pend}</div><div class="k">With Austin</div></div>`:''}
    </div></div>""", 'quest stats')
rep("""    <div class="g p"><div class="lbl">WHO YOU ARE TALKING TO</div>""", """    <div class="g p"><div class="lbl">${q.tag==='Create'?'WHO YOU ARE TALKING TO':'THE QUEST'}</div>""", 'quest brief label')
rep("""     <div style="display:flex;gap:9px;flex-wrap:wrap;margin-top:16px">
      <button class="btn gh" onclick="openSwipe(LIBIDX(${r.id}))">Swipe this angle</button></div>""",
    """     ${q.tag==='Create'?`<div style="display:flex;gap:9px;flex-wrap:wrap;margin-top:16px">
      <button class="btn gh" onclick="openSwipe(LIBIDX(${r.id}))">Swipe this angle</button></div>`:''}""", 'quest swipe')
rep("""    ${refs.length?`<div class="sec"><h2>More in this angle</h2>""", """    ${refs.length&&q.tag==='Create'?`<div class="sec"><h2>More in this angle</h2>""", 'quest refs')
rep(""" const open=QUESTS.filter(q=>q.got<q.need).length;
 return `${bar('Quests',`Weekly briefs worth bonus XP. ${open} still open.`)}""",
    """ const open=QUESTS.filter(qOpen).length;
 return `${bar('Quests',`Twelve ways to earn XP this month. ${open} still open · you have ${me().xp} XP.`)}""", 'quests header')
rep("""     <span class="mini">${f.subs} submissions · $${f.paid} paid out</span></div>""",
    """     <span class="mini">${f.got}/${f.need} this month${f.pend?` · ${f.pend} with Austin`:''}</span></div>""", 'featured copy')
rep(""" const f=QUESTS[0],fr=questRef(f),fth=thumbOf(fr);""", """ const f=QUESTS.filter(qOpen).sort((a,b)=>b.x-a.x)[0]||QUESTS[0],fr=questRef(f),fth=thumbOf(fr);""", 'featured pick')
# qrow: progress + no self-log button
old = """ <button class="btn sm ${d?'gh':''}" ${d?'disabled':''} onclick="event.stopPropagation();logQ(${q.id})">${d?'Done':'Log +1'}</button></div>`}"""
new = """ <button class="btn sm ${d?'gh':''}" onclick="event.stopPropagation();openQ(${q.id})">${d?'Done':q.pend?'With Austin':'Open'}</button></div>`}"""
rep(old, new, 'qrow button')
rep("""function qrow(q){const d=q.got>=q.need,p=Math.min(100,q.got/q.need*100),r=questRef(q),th=thumbOf(r);""",
    """function qrow(q){const d=!qOpen(q),p=Math.min(100,q.got/q.need*100),r=questRef(q),th=q.tag==='Create'?thumbOf(r):null;""", 'qrow head')
rep("""<div class="qpr"><div class="qbar"><div class="qbf" style="width:${p}%"></div></div><div class="mini mono">${q.got}/${q.need}</div></div></div>""",
    """<div class="qpr"><div class="qbar"><div class="qbf" style="width:${p}%"></div></div><div class="mini mono">${q.got}/${q.need}${q.win==='day'?' today':''}</div></div></div>""", 'qrow progress')

# ---------------------------------------------------------------- 10. nav + home + mobile
rep("""    if(n[0]==='quests'&&!c.admin)return QSOON_NAV;
    if(n[0]==='approvals'&&!c.admin)return '';
    const o=n[0]==='quests'?QUESTS.filter(q=>q.got<q.need).length""",
    """    if(n[0]==='approvals'&&!c.admin)n=['approvals','My submissions','check'];
    const o=n[0]==='quests'?QUESTS.filter(qOpen).length""", 'sidebar nav')
rep("""   const here=g.items.some(n=>navKey(n)&&!(n[0]==='quests'&&!c.admin));""", """   const here=g.items.some(n=>navKey(n));""", 'sidebar here')
REPL_ALL = [("""  const o=n[0]==='quests'?QUESTS.filter(q=>q.got<q.need).length:(n[0]==='approvals'""", """  const o=n[0]==='quests'?QUESTS.filter(qOpen).length:(n[0]==='approvals'""")]  # dead if(0) branch + legacy, replace all
rep(""" $('#mobnav').innerHTML=MOB.filter(m0=>c.admin||(m0[0]!=='quests'&&m0[0]!=='approvals')).map(m0=>{const m=(m0[0]==='approvals'&&!c.admin)?['approvals','Mine','check']:m0;const o=m[0]==='quests'?QUESTS.filter(q=>q.got<q.need).length""",
    """ $('#mobnav').innerHTML=MOB.map(m0=>{const m=(m0[0]==='approvals'&&!c.admin)?['approvals','Mine','check']:m0;const o=m[0]==='quests'?QUESTS.filter(qOpen).length""", 'mobile nav')
rep(""" const nq=QUESTS.filter(q=>q.got<q.need).sort((a,b)=>b.x-a.x)[0];""", """ const nq=QUESTS.filter(q=>qOpen(q)&&!q.pend&&!q.admin).sort((a,b)=>b.x-a.x)[0];""", 'home nq')
old = html[html.index("""   ${/* QUESTSOON-HOME"""):html.index("""   <div class="g p" style="display:flex;gap:15px;align-items:center">${beat?av(beat,54,18):''}""")]
new = """   <div class="g p" style="display:flex;gap:15px;align-items:center;cursor:pointer" onclick="${nq?`openQ(${nq.id})`:`go('quests')`}">${dial(nq?nq.got/nq.need*100:0,64,7,nq?nq.got:'—','')}
    <div style="min-width:0"><div class="lbl">BEST QUEST FOR YOU</div>
    <div style="font-size:14px;font-weight:700;margin-top:6px;letter-spacing:-.2px">${nq?esc(nq.t):'All clear'}</div>
    <div class="mini" style="margin-top:4px">${nq?`+${nq.x*M()} XP · ${nq.got}/${nq.need} this month`:'Everything is done or with Austin'}</div></div></div>
"""
rep(old, new, 'home slot')
rep("""  <div class="split"><div style="display:grid;gap:9px">${QUESTS.slice(0,4).map(qrow).join('')}</div>${activity()}</div>""",
    """  <div class="split"><div style="display:grid;gap:9px">${QUESTS.filter(qOpen).slice(0,4).map(qrow).join('')}</div>${activity()}</div>""", 'home quest rows')

# ---------------------------------------------------------------- 11. pull: creators get their own rows; Austin gets pinged
old = """   const r=await fetch(`${BACKEND.url}/rest/v1/submissions?select=*&order=ts.desc`,"""
new = """   let who=''; try{ if(AUTH!=null&&!me().admin)who='&cid=eq.'+encodeURIComponent(ME) }catch(e){}
   const r=await fetch(`${BACKEND.url}/rest/v1/submissions?select=*&order=ts.desc`+who,"""
rep(old, new, 'pull filter')
old = """  const byId={};SUBS.forEach(s=>byId[s.id]=s);
  rows.forEach(row=>{const ex=byId[row.id];
   if(!ex)SUBS.push(row);
   else if(row.status&&row.status!==ex.status){ex.status=row.status;ex.reason=row.reason||'';ex.decided=row.decided||Date.now()}});
  SUBS.sort((a,b)=>b.ts-a.ts);saveSubs();render();"""
new = """  const byId={};SUBS.forEach(s=>byId[s.id]=s);
  let fresh=0, admin=false; try{admin=!!me().admin}catch(e){}
  rows.forEach(row=>{const ex=byId[row.id];
   if(!ex){SUBS.push(row); if(row.status==='pending'&&admin&&!SEEN['sub:'+row.id])fresh++;}
   else if(row.status&&row.status!==ex.status){ex.status=row.status;ex.reason=row.reason||'';ex.decided=row.decided||Date.now();
    if(!admin&&ex.cid===ME)fire(row.status==='approved'?'Your '+ex.qtitle+' entry is approved':'Changes needed on your '+ex.qtitle+' entry',row.status==='approved'?'+'+(ex.xp*M())+' XP just landed.':(row.reason||''),'decision');}});
  if(admin&&fresh){fire('Approval request',fresh===1?'1 quest entry is waiting on you':fresh+' quest entries are waiting on you','approval');
   rows.forEach(r=>{if(r.status==='pending')SEEN['sub:'+r.id]=1}); lsSet(NKEY,SEEN);}
  SUBS.sort((a,b)=>b.ts-a.ts);saveSubs();render();"""
rep(old, new, 'sync notify')

# ---------------------------------------------------------------- 12. approvals copy
rep("""   admin?'Every quest video waiting on you. Points only move when you approve — nothing is automatic.'""",
    """   admin?'Every quest entry waiting on you. Points only move when you approve — nothing is automatic.'""", 'approvals copy')
rep("""   `<div class="note">${admin?(APF==='pending'?'Nothing waiting. You are clear.':'Nothing here yet.'):'You have not entered a quest in the app yet. Your Trybe submissions are counted above.'}</div>`}</div>""",
    """   `<div class="note">${admin?(APF==='pending'?'Nothing waiting. You are clear.':'Nothing here yet.'):'You have not entered a quest yet. <a href="javascript:go(\\'quests\\')" style="color:var(--o2)">Open the quests →</a>'}</div>`}</div>""", 'approvals empty')


# ---------------------------------------------------------------- 13. ad-hoc quest makers and the swipe self-award
i = html.index('window.mkQuest=id=>'); j = html.index('window.setThumb=', i)
rep(html[i:j], """window.mkQuest=id=>{LSEL=null;claimQ(102);openQ(102);toast('Recreate it for the format quest — +15 XP when Austin approves')};
window.adQuest=i=>{ASEL=null;claimQ(102);openQ(102);toast('Recreate it for the format quest — +15 XP when Austin approves')};
""", 'mkQuest/adQuest')
rep(""" if(fresh)award(ME,5,'broke down a swipe video');else render();
 toast(fresh?`Breakdown saved · +${5*M()} XP`:'Breakdown updated')};""",
    """ render();
 toast(fresh?'Breakdown saved':'Breakdown updated')};""", 'saveNote award')

rep(""" render();toast('Claimed — upload your video when it’s cut');""", """ render();toast('Claimed — send the proof here when it’s done');""", 'claim toast')
# ---------------------------------------------------------------- apply
ok = True
for old, new, what in REPL:
    n = html.count(old)
    if n != 1:
        print('ANCHOR %-18s matches %d times' % (what, n)); ok = False
if not ok: sys.exit('refusing to patch')
if CHECK: print('all %d anchors present' % len(REPL)); sys.exit(0)
for old, new, what in REPL: html = html.replace(old, new, 1)
for old, new in REPL_ALL: html = html.replace(old, new)
open(IDX, 'w', encoding='utf-8').write(html)
print('patched %d regions' % len(REPL))
