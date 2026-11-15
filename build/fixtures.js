/* Synthetic preview data for the redesign QA harness. Invented names and numbers only; never loaded by the live app.
   Use: serve the repo with window.APP_MODE="fixture" and include this file before the app script (see build/qa-shot.js). */
(function(){
const now=Date.now(), iso=ms=>new Date(now+ms).toISOString(), H=3600e3, D=864e5;
const P1={key:'2026-11-P1',label:'Nov 1–15',starts_at:'2026-11-01T05:00:00Z',ends_at:'2026-11-16T06:00:00Z'}, P2={key:'2026-11-P2',label:'Nov 16–30',starts_at:'2026-11-16T06:00:00Z',ends_at:'2026-12-01T06:00:00Z'};
const proofV={field:'videos',label:'Your videos',type:'submission_list',required:true,min:3,max:3}, proofL={field:'link',label:'Post link',type:'url',required:true}, proofT={field:'note',label:'What you changed',type:'text',required:true,min:20};
const Q=(k,cat,title,outcome,xp,o={})=>Object.assign({quest_key:k,category:cat,title,outcome,xp_value:xp,xp_base:xp,period_kind:'reward_period',per_period_limit:2,period_now:P1.key,
  proof:[proofL],criteria:['The work matches the assignment','Evidence opens and can be checked'],steps:['Plan it','Film it','Attach it'],examples:[],why:'It builds a repeatable skill.',image_key:'tile',
  done_in_period:0,xp_this_month:0,xp_this_period:0,completions_total:0,monthly_xp_cap:xp*4,max_xp:xp*4,reuse_rule:null,scarce:false,locked:false},o);
const catalog=()=>[
  Q('oct_hooks3','Film','3 openings, same video','Three different openings for one core video, with the strongest one picked.',25,{proof:[proofV,proofT],image_key:'hooks'}),
  Q('oct_objection','Film','Answer a real objection','One video that answers a real question a buyer asked.',20),
  Q('oct_recreate','Film','Recreate a winner','Study a winning video in the Angle Library and make your own version.',30),
  Q('oct_feedback','Improve','Apply review feedback','Fix one reviewer note and resubmit the same video.',15,{proof:[proofL,proofT]}),
  Q('oct_weakspot','Improve','Fix your weak spot','Find the stage where viewers drop and fix it.',20),
  Q('oct_win_post','Community','Share a win','Post a win in Ravine Elite.',10,{per_period_limit:1}),
  Q('oct_acad_win','Academy','Share a win in the Academy','Post a win in the Academy.',10,{per_period_limit:1}),
  Q('nov_aff_story3','Affiliate','Post 3 stories with your link','Three stories with your affiliate link.',10),
  Q('nov_aff_first','Affiliate','First affiliate sale','Make your first affiliate sale.',15,{per_period_limit:1}),
  Q('nov_boss_p2','Boss','Boss: 10 videos in a half','Ten approved original videos in one half.',60,{locked:true,min_prestige:2,min_prestige_name:'Prestige II',per_period_limit:1}),
];
const tiersOf=(xp,cc)=>[['t1','Builder',50,2,5000],['t2','Operator',100,4,10000],['t3','Elite',200,8,25000]].map(([id,name,x,c,cents])=>({id,name,xp_required:x,concepts_required:c,sales_required_cents:0,cash_total_cents:cents,published:true,draft:false,prestige_level:0,
  xp_met:xp>=x,concepts_met:cc>=c,status:xp>=x&&cc>=c?'approved_for_payment':'locked',claim:null}));
const levels=()=>[0,1,2,3,4].map(l=>({level:l,name:['Rookie','Prestige I','Prestige II','Prestige III','Prestige Master'][l],emblem:['🎯','🥉','🥈','🥇','👑'][l],
  tiers:[['Builder',50,2,5000],['Operator',100,4,10000],['Elite',200,8,25000]].map(([name,x,c,cents],i)=>({id:`l${l}t${i}`,name,xp_required:x+l*25,concepts_required:c+l,sales_required_cents:l>=2?(l-1)*250000:0,cash_total_cents:cents*(1+l),published:true,prestige_level:l})),boss:[]}));
const rewards=(xp,cc,lv)=>({xp,concepts:cc,sales_cents:293000,xp_pending:0,level:lv,period:{key:P1.key,label:P1.label,ends_at:P1.ends_at,starts_at:P1.starts_at},tiers:tiersOf(xp,cc),
  periods:[{...P1,current:true,xp,concepts:cc,tiers:tiersOf(xp,cc)}],history:[],ledger:{reserved_cents:0,paid_cents:0},
  prestige:{level:lv,unlocked:lv,can_change_current:false,change_until:'2026-11-04T06:00:00Z',launch_at:'2026-11-01T05:00:00Z',next:{level:lv,label:P2.label,starts_at:P2.starts_at,has_prestige:true,picked:false},levels:levels()}});
const vid=(i,st,sales,spend,o={})=>Object.assign({id:'fx'+String(i).padStart(6,'0')+'abcd',title:`Nov ${1+(i%13)}, ${1+(i%11)}:1${i%6} PM`,status:st,submitted_at:iso(-(i+1)*D*1.3),approved_at:st==='approved'?iso(-(i+1)*D*1.3+5*H):null,
  thumb_url:`./ph/${['qa-hooks','tier-builder','tier-operator','hero-board','tier-elite','hero-rewards'][i%6]}.jpg`,media_url:null,campaign_key:'2026-11',sales,oct_sales:0,all_sales:sales,spend,all_spend:spend,hook_rate:22+(i*7)%20,version:1,ads:spend>0?1:0,funnel:'TOF',contest_slot:i<20?i+1:null,parent_id:null,media_type:'VIDEO',revisions:[],timeline:[]},o);
const source={status:'ok',finished_at:iso(-2*H),reporting_through:new Date(now-D).toISOString().slice(0,10),stale:false};
function creator(name,kind){
  const pop=kind==='pop', cat=catalog(); const inst=[];
  if(pop){ const I=(k,state,o={})=>inst.push(Object.assign({id:'in-'+k+'-'+state,quest_key:k,period_key:P1.key,seq:1,state,draft:{},draft_rev:1,checklist:[true,false,false],evidence:[],review_note:null,submitted_at:null,created_at:iso(-3*D),updated_at:iso(-5*H),inspiration_ref:null,history:[{at:iso(-3*D),event:'started'}],xp:null},o));
    I('oct_feedback','needs_changes',{review_note:'The product is out of frame during the demo. Reshoot the 0:06 to 0:12 section so the case stays visible, then resubmit this same entry.',history:[{at:iso(-3*D),event:'started'},{at:iso(-2*D),event:'submitted'},{at:iso(-1*D),event:'changes_requested',detail:{note:'Reshoot'}}]});
    I('oct_hooks3','in_progress',{draft:{videos:['fx000001abcd','fx000002abcd']}});
    I('oct_objection','submitted',{submitted_at:iso(-6*H)});
    I('oct_recreate','approved',{xp:30}); I('oct_win_post','approved',{xp:10}); I('oct_weakspot','approved',{xp:20});
    cat.find(c=>c.quest_key==='oct_recreate').done_in_period=1; cat.find(c=>c.quest_key==='oct_win_post').done_in_period=1; cat.find(c=>c.quest_key==='oct_weakspot').done_in_period=1;
    cat.forEach(c=>{ c.completions_total=c.done_in_period; }); }
  const vids=pop?[vid(0,'approved',1210.5,410),vid(1,'approved',980,380),vid(2,'approved',5320.25,1900),vid(3,'changes_requested',0,0),vid(4,'pending',0,0),vid(5,'approved',310,150),vid(6,'approved',120,60),vid(7,'rejected',0,0),vid(8,'approved',44,30)]
    :kind==='pend'?[vid(0,'pending',0,0)]:[];
  const cnt=s=>vids.filter(v=>v.status===s).length; const xp=pop?60:0, cc=pop?3:0;
  return {home:{creator:{id:'fx-'+kind,display_name:name,joined_at:pop?'2026-08-12T15:00:00Z':iso(-2*D),role:'creator'},is_admin:false,
      campaign:{key:'2026-11',name:'November 2026',starts_at:'2026-11-01T05:00:00Z',ends_at:'2026-12-01T06:00:00Z',prizes:[],prize_total_cents:0},contest:{score_sales:pop?2930:0,rank:pop?5:null,ranked_creators:15,tied:false},
      submissions:{all:vids.length,pending:cnt('pending'),approved:cnt('approved'),changes:cnt('changes_requested'),rejected:cnt('rejected'),this_campaign:vids.length},
      activity:pop?[{at:iso(-5*H),kind:'quest_returned',text:'Apply review feedback was returned with notes'},{at:iso(-1*D),kind:'video_approved',text:'Video approved'}]:[],source:kind==='nosrc'?null:source},
    quests:{catalog:cat,instances:inst,periods:[P1,P2],period_now:P1.key,xp_earned:xp,xp_pending:0,max_xp_period:310,prestige_name:pop?'Prestige II':'Rookie',prestige_emblem:pop?'🥈':'🎯'},
    rewards:rewards(xp,cc,pop?2:0),contest:{campaign:{key:'2026-11'}},
    submissions:{videos:vids,source:kind==='nosrc'?null:source,counts:{}},analytics:{days:[],totals:{}},analytics_sep:{days:[],totals:{}}};
}
window.FIXTURES={codes:{RVFIXPOPUL:'populated',RVFIXEMPTY:'empty',RVFIXPENDG:'pending',RVFIXNOSRC:'nosrc',RVFIXADMIN:'admin'},
  creators:{populated:creator('Populated Creator','pop'),empty:creator('New Creator','empty'),pending:creator('Pending Creator','pend'),nosrc:creator('NoSource Creator','nosrc')},
  admin:{queue:[],recent:[],campaign:{key:'2026-11',name:'November 2026'},standings:[],snapshots:[],runs:[],pending_videos:[],claims:[],payouts:[],ledger:[],tiers:[],creators:[]}};
window.FIXTURES.creators.admin=creator('Fixture Admin','empty');
/* November preview patches on top of the October-era fixture backend */
window.addEventListener('DOMContentLoaded',()=>{ try{
  const n0=FX.numbersOf; FX.numbersOf=m=>{ const n=n0(m); if(n&&n.month_sales!=null){ n.campaign_key=window.CAMP; n.month_label='November'; } return n; };
  const t0=FX.teamGoalOf; FX.teamGoalOf=m=>Object.assign(t0(m),{month_key:window.CAMP,label:'November',goal:2000000,bonus_pool:25000,ends_at:'2026-12-01T06:00:00Z',starts_at:'2026-11-01T05:00:00Z'});
  const r0=FX.rewardsOf; FX.rewardsOf=m=>{ const r=m.rewards; r.xp_pending=FX.questsOf(m).xp_pending; let top=null; r.tiers.forEach(t=>{ if(t.xp_met&&t.concepts_met) top=t; }); r.tiers.forEach(t=>{ t.status=!(t.xp_met&&t.concepts_met)?'locked':t===top?'approved_for_payment':'included'; }); return r; };
  const p0=FX.paceOf; FX.paceOf=m=>Object.assign(p0(m),{campaign:window.CAMP,month_label:'November',ends_at:'2026-12-01T06:00:00Z'});
}catch(e){ console.error('fixture patch',e); } },{once:true,capture:true});
})();
