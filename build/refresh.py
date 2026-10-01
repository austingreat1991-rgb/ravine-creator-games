"""
One-shot numbers refresh for Ravine Creator Games.

  python3 build/refresh.py <creators-export.csv> <analytics-export.csv> --month 2026-09

Run from the repo root. It rewrites index.html (CR / TOTALS / SYNC / POOL),
every u/<CODE>.json, and bumps sw.js. Nothing here pushes; commit + push is a
separate, deliberate step.

Where the numbers come from
  * all-time figures ............ the creators export (All time, Trybe-attributed)
  * this-month figures .......... all-time minus the frozen 1st-of-month baseline
                                  (base is carried inside each existing u/ file;
                                  --snapshot-baseline freezes a new one for next month)
  * ad metrics .................. the analytics export (Last 30 days, by creative)
  * login codes ................. pinned by creator id from the published u/ files.
                                  A code never changes once issued. New creators get
                                  a fresh code; creators gone from the roster get
                                  their file revoked.
  * prize pool .................. proportional 60/40 (sales / approved videos),
                                  this month only, VIDEO accounts only. Static-image
                                  accounts (program "Ravine Static Image Ads", or the
                                  smaller duplicate of a name) never enter the pool.
"""
import csv, json, os, re, sys, glob, argparse, datetime, secrets

ap = argparse.ArgumentParser()
ap.add_argument('creators'); ap.add_argument('analytics')
ap.add_argument('--month', required=True, help='YYYY-MM the app is scoring')
ap.add_argument('--root', default='.', help='repo root (has index.html, u/, sw.js)')
ap.add_argument('--pool', type=int, default=None, help='pool amount override')
ap.add_argument('--baseline', default=None,
                help='JSON of {id:{sales,v,sub}} to use as this month\'s base instead of the u/ files')
ap.add_argument('--snapshot-baseline', default=None,
                help='write the all-time figures of THIS export here, to serve as next month\'s base')
ap.add_argument('--allow-shrink', action='store_true', help='accept a roster that shrank by more than 20%%')
ap.add_argument('--dry', action='store_true')
a = ap.parse_args()
ROOT = os.path.abspath(a.root)
IDX = os.path.join(ROOT, 'index.html'); UDIR = os.path.join(ROOT, 'u'); SW = os.path.join(ROOT, 'sw.js')

num = lambda v: float(str(v).replace(',', '').replace('$', '').strip() or 0)
int_ = lambda v: int(round(num(v)))
key = lambda s: re.sub(r'[^a-z]', '', str(s).lower())
ALPH = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
def mint(taken):
    while True:
        c = 'RV' + ''.join(secrets.choice(ALPH) for _ in range(8))
        if c not in taken: return c

MONTHS = ['January','February','March','April','May','June','July','August','September','October','November','December']
Y, M = int(a.month[:4]), int(a.month[5:7])
MNAME = MONTHS[M-1]
import calendar
LAST = calendar.monthrange(Y, M)[1]
POOLS = {'2026-09': 5000, '2026-10': 25000}
POOL_AMT = a.pool or POOLS.get(a.month, 5000)

# ------------------------------------------------------------------ section reader
def section(path, marker, header_first):
    rows = list(csv.reader(open(path, encoding='utf-8-sig')))
    start = next((i for i, r in enumerate(rows) if r and r[0].strip().startswith(marker)), None)
    if start is None: raise SystemExit('FATAL: section %r not found in %s' % (marker, path))
    hdr = next((i for i in range(start, min(start+5, len(rows))) if rows[i] and rows[i][0].strip() == header_first), None)
    if hdr is None: raise SystemExit('FATAL: header under %r not found' % marker)
    cols = [c.strip() for c in rows[hdr]]
    out = []
    for r in rows[hdr+1:]:
        if not r or not r[0].strip() or r[0].strip().startswith('##'): break
        out.append(dict(zip(cols, r)))
    return cols, out

# ------------------------------------------------------------------ what is live now
html = open(IDX, encoding='utf-8').read()
i = html.index('let CR='); j = html.index('\n', i)
LIVE_CR = json.loads(html[i+7:j].rstrip(';'))
LIVE = {}      # id -> (code, u-file dict)
CODES = set()
for f in glob.glob(os.path.join(UDIR, '*.json')):
    code = os.path.basename(f)[:-5]; CODES.add(code)
    try: d = json.load(open(f))
    except Exception: continue
    if d.get('revoked') or d.get('id') is None: continue
    LIVE[d['id']] = (code, d)
byname = {}
for c in LIVE_CR: byname[key(c['n'])] = c
for cid, (code, d) in LIVE.items():
    byname.setdefault(key(d['n']), {'id': cid, 'n': d['n'], 'h': '', 'xp': d.get('xp', 0), 'join': '', 'prog': '', 'admin': False})
BASE_OVERRIDE = json.load(open(a.baseline)) if a.baseline else None

# ------------------------------------------------------------------ roster
cols, roster = section(a.creators, '## Roster', 'Creator')
need = ['Creator','Join Date','Submissions','Approved','Sales (USD)','Earnings (USD)','Orders','Program','Instagram']
miss = [c for c in need if c not in cols]
if miss: raise SystemExit('FATAL: creators export missing %s' % miss)
hdr = open(a.creators, encoding='utf-8-sig').read(600)
if 'Brand,Ravine' not in hdr: raise SystemExit('FATAL: this is not a Ravine export (wrong brand picked)')
if 'Date range,All time' not in hdr: raise SystemExit('FATAL: creators export must be All time')

# group duplicates (video account + static account under one name)
groups = {}
for r in roster: groups.setdefault(key(r['Creator']), []).append(r)
STATIC_DROPPED = []
picked = []
for k, rs in groups.items():
    vid = [r for r in rs if 'static' not in r.get('Program', '').lower()]
    pool = vid or rs
    # the video account is the one that actually submits videos
    pool.sort(key=lambda r: (-int_(r['Submissions']), -num(r['Sales (USD)'])))
    picked.append(pool[0])
    for r in rs:
        if r is not pool[0]: STATIC_DROPPED.append((r['Creator'], r.get('Program',''), num(r['Sales (USD)'])))

CR = []
nid = max([c['id'] for c in LIVE_CR] + list(LIVE.keys()) + [0])
for r in sorted(picked, key=lambda x: -num(x['Sales (USD)'])):
    name = re.sub(r'\s+', ' ', r['Creator']).strip(); k = key(name)
    old = byname.get(k)
    if old: cid = old['id']; name = old['n'] or name
    else: nid += 1; cid = nid
    CR.append({'id': cid, 'n': name,
               'h': '@' + (r.get('Instagram','').strip() or k),
               'xp': (old or {}).get('xp', 0),
               'v': int_(r['Approved']), 'sub': int_(r['Submissions']),
               'sales': int_(r['Sales (USD)']), 'salesx': round(num(r['Sales (USD)']), 2),
               '$': int_(r['Earnings (USD)']), 'orders': int_(r['Orders']),
               # Trybe restamps Join Date when a creator is moved between programs;
               # the earliest date we have ever seen for them is the real one
               'join': min([d for d in [(r.get('Join Date','') or '')[:10], ((old or {}).get('join') or '')[:10]] if d] or ['']),
               'prog': r.get('Program','').strip() or (old or {}).get('prog',''),
               'admin': bool(old and old.get('admin'))})
if not any(c['admin'] for c in CR):
    adm = next((c for c in LIVE_CR if c['admin']), None)
    if not adm: raise SystemExit('FATAL: no brand admin row anywhere')
    # the brand account is not a Trybe creator; carry it over unchanged
    CR.append({'id': adm['id'], 'n': adm['n'], 'h': adm.get('h',''), 'xp': adm.get('xp',0), 'v': 0, 'sub': 0,
               'sales': 0, 'salesx': 0.0, '$': 0, 'orders': 0, 'join': adm.get('join',''), 'prog': adm.get('prog',''), 'admin': True})
ADMIN = next(c for c in CR if c['admin'])

if len([c for c in CR if not c['admin']]) < 0.8 * len([c for c in LIVE_CR if not c['admin']]) and not a.allow_shrink:
    raise SystemExit('FATAL: roster shrank %d -> %d. Re-run with --allow-shrink if Austin really removed them.'
                     % (len(LIVE_CR), len(CR)))

# ------------------------------------------------------------------ this-month figures
def base_for(c):
    if BASE_OVERRIDE is not None:
        b = BASE_OVERRIDE.get(str(c['id']))
        return {'sales': int(b['sales']), 'v': int(b['v']), 'sub': int(b['sub'])} if b else {'sales': 0, 'v': 0, 'sub': 0}
    d = LIVE.get(c['id'], (None, {}))[1]
    b = d.get('base') or {'sales': 0, 'v': 0, 'sub': 0}
    return {'sales': int(b.get('sales', 0)), 'v': int(b.get('v', 0)), 'sub': int(b.get('sub', 0))}
for c in CR:
    b = base_for(c)
    if b['sales'] > c['sales'] or b['v'] > c['v']:
        # a re-joined account starts over on Trybe; the old base no longer applies
        b = {'sales': 0, 'v': 0, 'sub': 0}
    c['base'] = b
    c['sep'] = {'sales': max(0, c['sales'] - b['sales']), 'v': max(0, c['v'] - b['v']), 'sub': max(0, c['sub'] - b['sub'])}

# ------------------------------------------------------------------ analytics
acols, vids = section(a.analytics, '## Creative Performance — by Creative', 'Creator')
vneed = ['Creator','Submission','Active Ads','CPA (USD)','Meta Purchase Value (USD)','ROAS','Sales (USD)','Spend (USD)','Thumbstop (%)']
vmiss = [c for c in vneed if c not in acols]
if vmiss: raise SystemExit('FATAL: analytics export missing %s' % vmiss)
ahdr = open(a.analytics, encoding='utf-8-sig').read(600)
if 'Brand,Ravine' not in ahdr: raise SystemExit('FATAL: analytics export is not for Ravine')
CANON = {key(c['n']): c['n'] for c in CR}
THUMBS = {f[:-4] for f in os.listdir(os.path.join(ROOT, 'v'))} if os.path.isdir(os.path.join(ROOT, 'v')) else set()
V = []
for r in vids:
    sid = r['Submission'].strip(); who = CANON.get(key(r['Creator']), r['Creator'].strip())
    prod = r.get('Product(s)', '').strip()
    V.append({'who': who, 'id': sid, 'ads': int_(r['Active Ads']), 'cpa': round(num(r['CPA (USD)']), 2),
              'pv': round(num(r['Meta Purchase Value (USD)']), 2), 'roas': round(num(r['ROAS']), 2),
              'sales': round(num(r['Sales (USD)']), 2), 'spend': round(num(r['Spend (USD)']), 2),
              'ts': round(num(r['Thumbstop (%)']), 2), 't': 1 if sid in THUMBS else 0, 'p': prod,
              'static': 1 if prod in ('—', '-', '') else 0})
AGG = {}
for v in V:
    g = AGG.setdefault(v['who'], {'vids': 0, 'ads': 0, 'pv': 0.0, 'sales': 0.0, 'spend': 0.0, '_w': 0.0})
    g['vids'] += 1; g['ads'] += v['ads']; g['pv'] += v['pv']; g['sales'] += v['sales']; g['spend'] += v['spend']; g['_w'] += v['ts'] * v['spend']
for k, g in AGG.items():
    w = g.pop('_w')
    g['cpa'] = round(g['spend'] / max(1, sum(1 for v in V if v['who'] == k and v['sales'] > 0)), 2)
    g['roas'] = round(g['pv'] / g['spend'], 2) if g['spend'] else 0
    g['ts'] = round(w / g['spend'], 2) if g['spend'] else 0
    for f in ('pv', 'sales', 'spend'): g[f] = round(g[f], 2)
m = re.search(r'Date range,(\d{4}-\d{2}-\d{2}) to (\d{4}-\d{2}-\d{2})', ahdr)
FROM, TO = (m.group(1), m.group(2)) if m else ('', '')
ANTOT = {'spend': round(sum(v['spend'] for v in V), 2), 'pv': round(sum(v['pv'] for v in V), 2), 'vids': len(V),
         'ts': round(sum(v['ts']*v['spend'] for v in V) / max(1, sum(v['spend'] for v in V)), 2)}
BYNAME = {}
for v in V: BYNAME.setdefault(v['who'], []).append(v)
for l in BYNAME.values(): l.sort(key=lambda x: -x['spend'])

# ------------------------------------------------------------------ pool (this month, video accounts)
roster = [c for c in CR if not c['admin'] and (c['sep']['v'] > 0 or c['sep']['sales'] > 0)]
tg = sum(c['sep']['sales'] for c in roster) or 1
tv = sum(c['sep']['v'] for c in roster) or 1
def split(total, parts):
    # largest-remainder rounding: cents add up to `total` exactly
    raw = {k: total * v for k, v in parts.items()}
    flo = {k: int(v * 100) for k, v in raw.items()}
    left = int(round(total * 100)) - sum(flo.values())
    for k in sorted(raw, key=lambda k: -(raw[k] * 100 - flo[k]))[:max(0, left)]: flo[k] += 1
    return {k: v / 100 for k, v in flo.items()}
GS = split(POOL_AMT * 0.6, {c['id']: c['sep']['sales'] / tg for c in roster})
VS = split(POOL_AMT * 0.4, {c['id']: c['sep']['v'] / tv for c in roster})
share = {c['id']: {'pct': round((GS[c['id']] + VS[c['id']]) / POOL_AMT * 100, 4),
                   'amt': round(GS[c['id']] + VS[c['id']], 2),
                   'g': GS[c['id']], 's': VS[c['id']]} for c in roster}
order = sorted(roster, key=lambda c: (-c['sep']['sales'], -c['sep']['v'], c['n']))
rank = {c['id']: n + 1 for n, c in enumerate(order)}

# ------------------------------------------------------------------ history
from zoneinfo import ZoneInfo
TODAY = datetime.datetime.now(ZoneInfo('America/Chicago')).date()   # Trybe exports are Central-time days
STAMP = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
DKEY = TODAY.strftime('%m-%d')

# ------------------------------------------------------------------ write
NEW_CODES = {}
ids_now = {c['id'] for c in CR}
out_u = {}
for c in CR:
    code, old = LIVE.get(c['id'], (None, {}))
    if not code:
        code = mint(CODES); CODES.add(code); NEW_CODES[c['n']] = code
    hist = dict(old.get('hist') or {'d': [], 's': [], 'sub': [], 'v': []})
    hist = {k: list(v) for k, v in hist.items()}
    if hist['d'] and hist['d'][-1] == DKEY:
        for k in ('d', 's', 'sub', 'v'): hist[k].pop()
    hist['d'].append(DKEY); hist['s'].append(c['sales']); hist['sub'].append(c['sub']); hist['v'].append(c['v'])
    mine = {'id': c['id'], 'n': c['n'], 'sales': c['sep']['sales'], 'allSales': c['sales'], '$': c['$'],
            'v': c['v'], 'sub': c['sub'], 'xp': c['xp'], 'rank': rank.get(c['id'], 0),
            'pool': share.get(c['id'], {'pct': 0, 'amt': 0}),
            'sep': c['sep'], 'base': c['base']}
    if old.get('up'): mine['up'] = old['up']
    mine['hist'] = hist
    mine['an'] = {'rows': BYNAME.get(c['n'], []), 'agg': AGG.get(c['n'])}
    if c['admin']:
        mine['antot'] = ANTOT
        mine['all'] = [{'id': x['id'], 'n': x['n'], 'sales': x['sep']['sales'], 'allSales': x['sales'], '$': x['$'],
                        'v': x['v'], 'sub': x['sub'], 'rank': rank.get(x['id'], 0),
                        'pool': share.get(x['id'], {'pct': 0, 'amt': 0})} for x in CR]
    out_u[code] = mine
REVOKE = [code for cid, (code, d) in LIVE.items() if cid not in ids_now]

pub = [{'id': c['id'], 'n': c['n'], 'h': c['h'], 'xp': c['xp'], 'v': c['v'], 'sepV': c['sep']['v'], 'sub': c['sub'],
        'sales': 0, '$': 0, 'rank': rank.get(c['id'], 0), 'join': c['join'], 'prog': c['prog'], 'admin': c['admin']} for c in CR]
TOTALS = {'sales': sum(c['sales'] for c in CR), 'sepSales': sum(c['sep']['sales'] for c in CR),
          'sepV': sum(c['sep']['v'] for c in CR), 'paid': sum(c['$'] for c in CR),
          'subs': sum(c['sub'] for c in CR), 'v': sum(c['v'] for c in CR),
          'active': len([c for c in CR if not c['admin'] and (c['v'] > 0 or c['sales'] > 0)]), 'poolN': len(roster),
          'spend': ANTOT['spend'], 'anVids': ANTOT['vids'], 'ts': ANTOT['ts'], 'anFrom': FROM, 'anTo': TO,
          'refreshed': STAMP}
POOL = {'month': MNAME, 'amount': POOL_AMT, 'wGmv': 60, 'wSub': 40,
        'open': '%s 1' % MNAME[:3], 'close': '%s %d' % (MNAME[:3], LAST)}

def sub1(pat, rep, s, what):
    s2, n = re.subn(pat, rep, s, count=1, flags=re.S)
    if n != 1: raise SystemExit('FATAL: could not splice %s' % what)
    return s2
js = lambda o: json.dumps(o, separators=(',', ':'), ensure_ascii=False)
html = sub1(r'let CR=\[.*?\];\n', lambda m: 'let CR=' + js(pub) + ';\n', html, 'CR')
html = sub1(r'const TOTALS=\{.*?\};', lambda m: 'const TOTALS=' + js(TOTALS) + ';', html, 'TOTALS')
html = sub1(r"const SYNC=\{.*?\};", lambda m: "const SYNC={\n source:'Trybe',\n at:'%s',\n live:false,\n trybeSales:%d,\n metaSales:0\n};" % (STAMP, TOTALS['sales']), html, 'SYNC')
html = sub1(r"let POOL=\{[^\n]*\};", lambda m: 'let POOL=' + js(POOL) + ';', html, 'POOL')
html = sub1(r"const POOL_END=new Date\('[^']*'\);", lambda m: "const POOL_END=new Date('%04d-%02d-%02dT23:59:59-05:00');" % (Y, M, LAST), html, 'POOL_END')
leaked = [c for c in set(re.findall(r'\bRV[A-Z0-9]{8}\b', html)) if c != 'RVAB12CD34' and set(c[2:]) <= set(ALPH)]
if leaked: raise SystemExit('FATAL: a login code leaked into index.html')

print('roster       %d creators (live had %d)  new: %d  revoked: %d  static rows dropped: %d'
      % (len(CR), len(LIVE_CR), len(NEW_CODES), len(REVOKE), len(STATIC_DROPPED)))
for n, p, s in STATIC_DROPPED: print('   dropped    %-28s %-28s $%.2f' % (n, p, s))
for n in NEW_CODES: print('   new code   %s' % n)
print('all-time     $%s sales   %d approved   %d submissions   $%s earned'
      % (f"{TOTALS['sales']:,}", TOTALS['v'], TOTALS['subs'], f"{TOTALS['paid']:,}"))
print('%-12s $%s sales   %d approved   pool $%s over %d creators'
      % (MNAME, f"{TOTALS['sepSales']:,}", TOTALS['sepV'], f"{POOL_AMT:,}", len(roster)))
print('analytics    %d creatives (%d static)  spend $%s  %s..%s'
      % (len(V), sum(v['static'] for v in V), f"{ANTOT['spend']:,.2f}", FROM, TO))
print('pool check   $%.2f' % sum(s['amt'] for s in share.values()))
for c in order[:5]: print('   #%d %-22s $%s this month  %d approved  pool $%.2f' % (rank[c['id']], c['n'], f"{c['sep']['sales']:,}", c['sep']['v'], share[c['id']]['amt']))

if a.snapshot_baseline:
    snap = {str(c['id']): {'n': c['n'], 'sales': c['sales'], 'v': c['v'], 'sub': c['sub'], 'orders': c['orders']} for c in CR}
    json.dump({'as_of': TODAY.isoformat(), 'for_month': '%04d-%02d' % ((Y + (M // 12)), (M % 12) + 1), 'creators': snap},
              open(a.snapshot_baseline, 'w'), indent=1)
    print('baseline     snapshot written to %s' % a.snapshot_baseline)
if a.dry:
    print('DRY RUN - nothing written'); sys.exit(0)

for code, mine in out_u.items():
    json.dump(mine, open(os.path.join(UDIR, code + '.json'), 'w'), separators=(',', ':'))
for code in REVOKE:
    json.dump({'id': -1, 'revoked': True}, open(os.path.join(UDIR, code + '.json'), 'w'))
open(IDX, 'w', encoding='utf-8').write(html)
sw = open(SW, encoding='utf-8').read()
stamp = datetime.datetime.now(ZoneInfo('America/Chicago')).strftime('%Y%m%d-%H%M%S')
sw2, n = re.subn(r"(VERSION\s*=\s*')[^']*(')", lambda m: m.group(1) + 'rcg-' + stamp + m.group(2), sw, count=1)
if n != 1: raise SystemExit('FATAL: sw.js has no VERSION line')
open(SW, 'w', encoding='utf-8').write(sw2)
# private: the new codes, never into the repo
priv = os.path.join(os.path.dirname(ROOT), 'pipeline', 'NEW_CODES-%s.json' % stamp)
if NEW_CODES:
    json.dump(NEW_CODES, open(priv, 'w'), indent=1); print('new codes    -> %s (private)' % priv)
print('wrote index.html, %d u/ files, sw.js %s' % (len(out_u) + len(REVOKE), 'rcg-' + stamp))
