"""
Turns the two Trybe CSV exports into CR_FULL.json + an.json.

Written to be run unattended twice a day, so it validates rather than assumes:
if a column moves, a section disappears, or the numbers collapse, it raises
instead of quietly publishing something wrong to 47 creators.
"""
import csv, json, sys, io, re

def section(path, marker, header_startswith):
    """Pull one '## Section' block out of a Trybe export as list-of-dicts."""
    rows = list(csv.reader(open(path, encoding='utf-8-sig')))
    start = None
    for i, r in enumerate(rows):
        if r and r[0].strip().startswith(marker):
            start = i; break
    if start is None:
        raise SystemExit('FATAL: section %r not found in %s' % (marker, path))
    hdr = None
    for i in range(start, min(start + 5, len(rows))):
        if rows[i] and rows[i][0].strip() == header_startswith:
            hdr = i; break
    if hdr is None:
        raise SystemExit('FATAL: header %r not found under %r in %s' % (header_startswith, marker, path))
    cols = [c.strip() for c in rows[hdr]]
    out = []
    for r in rows[hdr + 1:]:
        if not r or not r[0].strip():          # blank line ends the block
            break
        if r[0].strip().startswith('##'):
            break
        out.append(dict(zip(cols, r)))
    return cols, out

num = lambda v: float(str(v).replace(',', '').replace('$', '').strip() or 0)
int_ = lambda v: int(round(num(v)))

# ---------------------------------------------------------------- roster
CRE_CSV, AN_CSV = sys.argv[1], sys.argv[2]
cols, roster = section(CRE_CSV, '## Roster', 'Creator')
need = ['Creator','Join Date','Submissions','Approved','Sales (USD)','Earnings (USD)','Orders','Program','Sponsor','Instagram']
missing = [c for c in need if c not in cols]
if missing:
    raise SystemExit('FATAL: creators export is missing columns: %s' % missing)

# This export is already scoped to the Ravine brand by the ?b= id in the URL, so
# every row belongs here. Do NOT filter on Program — that column names the agency
# a creator came in through (Whitelist Wealth, Pured Media), not the brand, and
# filtering on it drops real Ravine creators like Thomas Montelli and Hustyn
# Wheeler who between them carry ~$29k of the sales.
rav = roster
if not rav:
    raise SystemExit('FATAL: no rows in the creators export')

# Match people by normalised name. Trybe's casing drifts between exports
# ("Alli Gamble" -> "Alli gamble"); matching on the raw string would mint a new
# id, orphan their pinned login code, and hand them a blank account.
key = lambda s: re.sub(r'[^a-z]', '', s.lower())
prev_list = json.load(open('CR_FULL.json'))
prev = {c['n']: c for c in prev_list}
prevk = {key(c['n']): c for c in prev_list}
CR, nid = [], max(c['id'] for c in prev.values())
seen = set()
for r in sorted(rav, key=lambda x: -num(x['Sales (USD)'])):
    name = r['Creator'].strip()
    k = key(name)
    if k in seen:
        continue
    seen.add(k)
    old = prevk.get(k)
    if old:
        cid = old['id']
        name = old['n']          # keep the name they were introduced to everyone as
    else:
        nid += 1; cid = nid
    CR.append({
        'id': cid, 'n': name,
        'h': '@' + (r.get('Instagram','').strip() or re.sub(r'[^a-z]','',name.lower())),
        'xp': old['xp'] if old else 0,
        'v': int_(r['Approved']), 'sub': int_(r['Submissions']),
        'sales': int_(r['Sales (USD)']), '$': int_(r['Earnings (USD)']),
        'orders': int_(r['Orders']),
        'join': (r.get('Join Date','') or (old['join'] if old else ''))[:10],
        'prog': r.get('Program','').strip() or (old['prog'] if old else ''),
        'admin': bool(old and old['admin']),
    })
if not any(c['admin'] for c in CR):
    raise SystemExit('FATAL: the brand admin row vanished from the roster')

# ------------------------------------------------------------- analytics
CANON = {re.sub(r'[^a-z]','',c['n'].lower()): c['n'] for c in CR}
acols, vids = section(AN_CSV, '## Creative Performance — by Creative', 'Creator')
vneed = ['Creator','Submission','Active Ads','CPA (USD)','Meta Purchase Value (USD)','ROAS','Sales (USD)','Spend (USD)','Thumbstop (%)']
vmissing = [c for c in vneed if c not in acols]
if vmissing:
    raise SystemExit('FATAL: analytics export is missing columns: %s' % vmissing)

THUMBS = set()
import os
if os.path.isdir('ship/v'):
    THUMBS = {f[:-4] for f in os.listdir('ship/v') if f.endswith('.jpg')}

V = []
for r in vids:
    sid = r['Submission'].strip()
    who = r['Creator'].strip()
    who = CANON.get(re.sub(r'[^a-z]','',who.lower()), who)   # same canonical name as the roster
    V.append({'who': who, 'id': sid,
              'ads': int_(r['Active Ads']), 'cpa': round(num(r['CPA (USD)']), 2),
              'pv': round(num(r['Meta Purchase Value (USD)']), 2),
              'roas': round(num(r['ROAS']), 2), 'sales': round(num(r['Sales (USD)']), 2),
              'spend': round(num(r['Spend (USD)']), 2), 'ts': round(num(r['Thumbstop (%)']), 2),
              't': 1 if sid in THUMBS else 0,
              'p': r.get('Product(s)','').strip()})

AGG = {}
for v in V:
    a = AGG.setdefault(v['who'], {'vids':0,'ads':0,'pv':0.0,'sales':0.0,'spend':0.0,'_tsw':0.0})
    a['vids'] += 1; a['ads'] += v['ads']; a['pv'] += v['pv']
    a['sales'] += v['sales']; a['spend'] += v['spend']; a['_tsw'] += v['ts'] * v['spend']
for k, a in AGG.items():
    sp = a.pop('_tsw')
    a['cpa']  = round(a['spend'] / max(1, sum(1 for v in V if v['who']==k and v['sales']>0)), 2)
    a['roas'] = round(a['pv'] / a['spend'], 2) if a['spend'] else 0
    a['ts']   = round(sp / a['spend'], 2) if a['spend'] else 0
    for f in ('pv','sales','spend'): a[f] = round(a[f], 2)

# date range straight from the file, so the app never lies about freshness
hdr = open(AN_CSV, encoding='utf-8-sig').read(400)
m = re.search(r'Date range,(\d{4}-\d{2}-\d{2}) to (\d{4}-\d{2}-\d{2})', hdr)
FROM, TO = (m.group(1), m.group(2)) if m else ('', '')

# ------------------------------------------------------------ sanity gate
tot_sales = sum(c['sales'] for c in CR)
old_sales = sum(c['sales'] for c in prev.values())
spend = round(sum(v['spend'] for v in V), 2)
if tot_sales < old_sales * 0.5:
    raise SystemExit('FATAL: sales collapsed %s -> %s. Refusing to publish.' % (old_sales, tot_sales))
if len(CR) < len(prev) * 0.8:
    raise SystemExit('FATAL: roster shrank %d -> %d. Refusing to publish.' % (len(prev), len(CR)))
if not V:
    raise SystemExit('FATAL: zero videos in the analytics export')

json.dump(CR, open('CR_FULL.json','w'), indent=1)
json.dump({'v': V, 'a': AGG}, open('an.json','w'))
json.dump({'from': FROM, 'to': TO}, open('anrange.json','w'))
print('roster      %d creators (was %d)' % (len(CR), len(prev)))
print('sales       $%s (was $%s)' % (f'{tot_sales:,}', f'{old_sales:,}'))
print('earnings    $%s' % f"{sum(c['$'] for c in CR):,}")
print('approved    %d   submissions %d' % (sum(c['v'] for c in CR), sum(c['sub'] for c in CR)))
print('videos      %d   spend $%s   range %s..%s' % (len(V), f'{spend:,.2f}', FROM, TO))
print('thumbs      %d/%d matched' % (sum(v['t'] for v in V), len(V)))
