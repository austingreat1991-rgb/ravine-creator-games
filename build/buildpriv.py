import json, os, secrets, string
CR=json.load(open('CR_FULL.json'))
POOL={'amount':5000,'wGmv':60,'wSub':40}

# --- pool split, computed here at build time, never shipped whole ---
roster=[c for c in CR if not c['admin'] and (c['v']>0 or c['sales']>0)]
tg=sum(c['sales'] for c in roster) or 1
tv=sum(c['v'] for c in roster) or 1
wg, wv = POOL['wGmv']/100, POOL['wSub']/100
weights={c['id']: wg*(c['sales']/tg)+wv*(c['v']/tv) for c in roster}
tw=sum(weights.values()) or 1
share={cid: {'pct':w/tw*100,'amt':POOL['amount']*w/tw} for cid,w in weights.items()}

# --- sales rank (ties broken by videos then name, deterministic) ---
order=sorted(roster, key=lambda c:(-c['sales'], -c['v'], c['n']))
rank={c['id']: n+1 for n,c in enumerate(order)}

ALPH='ABCDEFGHJKLMNPQRSTUVWXYZ23456789'   # no I/O/0/1
def code():
    r=lambda n: ''.join(secrets.choice(ALPH) for _ in range(n))
    return 'RV'+r(4)+r(4)

# Pinned codes. A creator's code must never change, or their app dies.
# CODEPIN.json is the source of truth, but it is deliberately NOT in the public
# repo (it is the full list of everyone's logins). If a fresh machine doesn't
# have it, rebuild it from the per-creator files already published in ship/u/ —
# each is named for the code and carries the creator id inside.
try:
    PIN=json.load(open('CODEPIN.json'))
except Exception:
    PIN={}
    import glob as _g
    for f in _g.glob('ship/u/*.json'):
        try:
            d=json.load(open(f))
            code=os.path.basename(f)[:-5]
            if d.get('id') is not None: PIN[str(d['id'])]=code
        except Exception: pass
    if PIN: print('CODEPIN rebuilt from ship/u/: %d codes recovered'%len(PIN))
codes={}
os.makedirs('ship/u',exist_ok=True)
for f in os.listdir('ship/u'):
    os.remove('ship/u/'+f)

AN=json.load(open('an.json'))
try: RANGE=json.load(open('anrange.json'))
except Exception: RANGE={}
import datetime, os
STAMP=os.environ.get('RCG_STAMP') or datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
BYNAME={}
for v in AN['v']: BYNAME.setdefault(v['who'],[]).append(v)
for lst in BYNAME.values(): lst.sort(key=lambda x:-x['spend'])
AGG=AN['a']
ANTOT={'spend':round(sum(v['spend'] for v in AN['v']),2),
       'pv':round(sum(v['pv'] for v in AN['v']),2),
       'vids':len(AN['v']),
       'ts':round(sum(v['ts']*v['spend'] for v in AN['v'])/max(1,sum(v['spend'] for v in AN['v'])),2)}

for c in CR:
    k=PIN.get(str(c['id'])) or code()      # a creator's code never changes once issued
    codes[c['id']]=k
    mine={'id':c['id'],'n':c['n'],'sales':c['sales'],'$':c['$'],
          'v':c['v'],'sub':c['sub'],'xp':c['xp'],
          'rank':rank.get(c['id'],0),
          'pool':{'pct':round(share.get(c['id'],{}).get('pct',0),4),
                  'amt':round(share.get(c['id'],{}).get('amt',0),2)}}
    mine['an']={'rows':BYNAME.get(c['n'],[]), 'agg':AGG.get(c['n'])}
    if c['admin']:
        # the brand dashboard legitimately needs the whole table
        mine['antot']=ANTOT
        mine['all']=[{'id':x['id'],'n':x['n'],'sales':x['sales'],'$':x['$'],'v':x['v'],'sub':x['sub'],
                      'rank':rank.get(x['id'],0),
                      'pool':{'pct':round(share.get(x['id'],{}).get('pct',0),4),
                              'amt':round(share.get(x['id'],{}).get('amt',0),2)}} for x in CR]
    json.dump(mine, open('ship/u/%s.json'%k,'w'))

# --- redacted roster for the shared bundle ---
pub=[]
for c in CR:
    pub.append({'id':c['id'],'n':c['n'],'h':c['h'],'xp':c['xp'],'v':c['v'],'sub':c['sub'],
                'sales':0,'$':0,'rank':rank.get(c['id'],0),
                'join':c['join'],'prog':c['prog'],'admin':c['admin']})

TOTALS={'sales':sum(c['sales'] for c in CR),'paid':sum(c['$'] for c in CR),
        'subs':sum(c['sub'] for c in CR),'v':sum(c['v'] for c in CR),
        'active':len(roster),
        'spend':ANTOT['spend'],'anVids':ANTOT['vids'],'ts':ANTOT['ts'],
        'anFrom':RANGE.get('from',''),'anTo':RANGE.get('to',''),
        'refreshed':STAMP}

# --- rewrite data_core.js ---
s=open('data_core.js',encoding='utf-8').read()
import re as _re
# stamp the freshness pill from this run, or it will keep claiming the age of a
# snapshot we replaced hours ago
s=_re.sub(r"const SYNC=\{[^}]*\};",
 "const SYNC={\n source:'Trybe',\n at:'%s',      // when this snapshot was pulled\n live:false,                      // flips true when a backend feed is connected\n trybeSales:%d,               // Trybe attribution at pull time\n metaSales:0\n};" % (STAMP, TOTALS['sales']),
 s, count=1)
import re as _re
s=_re.sub(r'\nconst TOTALS=\{[^\n]*\};', '', s)   # drop any TOTALS from a previous run
i=s.index('let CR='); j=s.index('\n',i)
s=s[:i]+'let CR='+json.dumps(pub,separators=(',',':'),ensure_ascii=False)+';\nconst TOTALS='+json.dumps(TOTALS,separators=(',',':'))+';'+s[j:]
open('data_core.js','w',encoding='utf-8').write(s)

with open('CREATOR-CODES.csv','w') as f:
    f.write('creator,login code\n')
    for c in CR: f.write('%s,%s\n'%(c['n'],codes[c['id']]))
print('codes written for', len(codes), 'creators')
print('TOTALS', TOTALS)
print('admin code', codes[[c['id'] for c in CR if c['admin']][0]])

json.dump({str(cid):k for cid,k in codes.items()}, open('CODEPIN.json','w'), indent=1)
print('codes pinned:', len(codes))
