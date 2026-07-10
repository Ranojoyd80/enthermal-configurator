# Pre-flight gate for TEST-PLAN.md (section 2) — run BEFORE any UI interaction.
# Any FAIL aborts the suite. Expectations here are derived from App_Data JSON +
# domain rules, never from the app's own JS (independent-predicate discipline).
#
#   python "Automated Test/preflight.py"        (from repo root)
#
# Exit 0 = all gates pass. Exit 1 = abort, do not run the UI suite.
import json, os, re, sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
AD = os.path.join(ROOT, "App_Data")

# CEN rule (corrected 2026-07-09): cen == (a Saint-Gobain coating is present
# anywhere in the assembly) AND (no Vitro coating is present). The old
# "Saint-Gobain on Surface 2" rule is WRONG for current data (636 rows differ).
SG = {'SKN183', 'XTR6129', 'LUMI', 'ZEN'}
VITRO = {'SB60', 'SB70', 'SB72', 'SBR67'}
KNOWN_COATINGS = SG | VITRO | {'C180', 'C270', 'C272', 'C340', 'C366', 'Q452'}

EXPECT_ROWS = {'enthermal': 98, 'enthermal-plus-inboard': 4470, 'enthermal-plus-outboard': 1876}
EXPECT_CEN  = {'enthermal': 19, 'enthermal-plus-inboard': 752, 'enthermal-plus-outboard': 366}

fails, passes = [], 0
def gate(ok, label, detail=''):
    global passes
    if ok: passes += 1
    else: fails.append(f'{label}: {detail}')
    print(('PASS ' if ok else 'FAIL ') + label + ('' if ok else ' — ' + detail))

def load(n): return json.load(open(os.path.join(AD, n + '.json'), encoding='utf-8'))
def glasses(d): return [l for l in d['stack'] if l['type'] == 'glass']
def gas(d):
    g = [l for l in d['stack'] if l['type'] == 'gas']
    return g[0]['gasType'] if g else None
def second(d):
    g = glasses(d)
    if len(g) < 3: return None, None
    if g[1].get('coating'): return g[1]['coating'], 'S4'
    if g[2].get('coating'): return g[2]['coating'], 'S5'
    return None, None

DATA = {n: load(n) for n in EXPECT_ROWS}

# -- Gate 1: row counts ------------------------------------------------------
for n, want in EXPECT_ROWS.items():
    gate(len(DATA[n]) == want, f'rows {n}', f'{len(DATA[n])} != {want}')

# -- Gate 2: CEN counts + rule + covariance ----------------------------------
for n, want in EXPECT_CEN.items():
    got = sum(1 for d in DATA[n] if d['cen'])
    gate(got == want, f'cen count {n}', f'{got} != {want}')
for n, data in DATA.items():
    viol = cov = 0
    for d in data:
        coats = {g.get('coating') for g in glasses(d) if g.get('coating')}
        want = bool(coats & SG) and not (coats & VITRO)
        if bool(d['cen']) != want: viol += 1
        if (d.get('gFactor') is not None) != bool(d['cen']) or (d.get('uvalCEN') is not None) != bool(d['cen']): cov += 1
        if coats - KNOWN_COATINGS: viol += 1
    gate(viol == 0, f'cen rule {n}', f'{viol} rows violate SG-present-and-no-Vitro')
    gate(cov == 0, f'cen covariance {n}', f'{cov} rows with gFactor/uvalCEN presence != cen')

# -- Gate 3: UI match-key uniqueness ----------------------------------------
keys = Counter((g[0]['thickness'], g[0].get('coating'), g[0]['substrate'], g[1]['thickness'])
               for d in DATA['enthermal'] for g in [glasses(d)])
gate(max(keys.values()) == 1, 'match-key uniqueness enthermal', f'{sum(1 for v in keys.values() if v>1)} dup keys')
for n, mono_i, vig in (('enthermal-plus-inboard', 0, (1, 2)), ('enthermal-plus-outboard', 2, (0, 1))):
    keys = Counter()
    for d in DATA[n]:
        g = glasses(d); sc, ss = second(d)
        keys[(g[mono_i]['thickness'], g[0].get('coating'), g[0]['substrate'], gas(d),
              (g[vig[0]]['thickness'], g[vig[1]]['thickness']), sc, ss)] += 1
    gate(max(keys.values()) == 1, f'match-key uniqueness {n}', f'{sum(1 for v in keys.values() if v>1)} dup keys')

# -- Gate 4: cid + anchor render files ---------------------------------------
cids = {d['cid'] for data in DATA.values() for d in data}
gate(all(isinstance(c, int) and c >= 1 for c in cids) and cids == set(range(1, max(cids) + 1)),
     'cid contiguity', f'{len(cids)} cids, max {max(cids)}')
for folder in ('Overcast', 'PartlyClear'):
    have = {int(m.group(1)) for f in os.listdir(os.path.join(AD, 'Anchor_Renders', folder))
            if (m := re.match(r'anchor_(\d+)\.webp$', f))}
    gate(cids <= have, f'renders {folder}', f'missing {sorted(cids - have)[:5]}')

# -- Gate 5: full test-matrix validation (every entry -> exactly 1 row, cen as planned)
def enth(coat, sub, ot, it):
    return [d for d in DATA['enthermal'] for g in [glasses(d)]
            if g[0]['coating'] == coat and g[0]['substrate'] == sub
            and g[0]['thickness'] == ot and g[1]['thickness'] == it]
def plus_in(monoT, s2, vig, vc, srf, gt, sub='Clear'):
    return [d for d in DATA['enthermal-plus-inboard'] for g in [glasses(d)] for scss in [second(d)]
            if g[0]['thickness'] == monoT and g[0]['coating'] == s2 and g[0]['substrate'] == sub
            and (g[1]['thickness'], g[2]['thickness']) == vig and scss == (vc, srf) and gas(d) == gt]
def plus_out(vig, s2, monoT, s5, gt, sub='Clear'):
    return [d for d in DATA['enthermal-plus-outboard'] for g in [glasses(d)] for scss in [second(d)]
            if (g[0]['thickness'], g[1]['thickness']) == vig and g[0]['coating'] == s2
            and g[0]['substrate'] == sub and g[2]['thickness'] == monoT
            and scss == (s5, 'S5') and gas(d) == gt]

# (finder, args, expected cen) — mirrors TEST-PLAN.md section 4 exactly.
MATRIX = {
 'A1':  (enth, ('C366','Clear',6,6), False), 'A2':  (enth, ('C180','Clear',4,4), False),
 'A3':  (enth, ('C270','Clear',4,4), False), 'A4':  (enth, ('C272','Clear',4,4), False),
 'A5':  (enth, ('C340','Clear',4,4), False), 'A6':  (enth, ('Q452','Clear',4,4), False),
 'A7':  (enth, ('SB60','Clear',4,4), False), 'A8':  (enth, ('SB70','Clear',4,4), False),
 'A9':  (enth, ('LUMI','Clear',4,4), True),  'A10': (enth, ('ZEN','Clear',4,4), True),
 'A11': (enth, ('XTR6129','Clear',4,4), True),'A12': (enth, ('SKN183','Clear',6,4), True),
 'A13': (enth, ('SB72','Starphire',6,4), False),'A14': (enth, ('SBR67','Clear',5,4), False),
 'B1':  (enth, ('SB60','Starphire',6,4), False),'B2': (enth, ('SB60','Starphire',5,5), False),
 'B3':  (enth, ('SB60','Optiblue',6,4), False), 'B4': (enth, ('SB60','Optigray',6,5), False),
 'B5':  (enth, ('SB60','Solarblue',6,6), False),'B6': (enth, ('SB60','Solarbronze',6,4), False),
 'B7':  (enth, ('SB72','Starphire',6,6), False),
 'B8':  (enth, ('SB60','Solexia',6,4), False),  'B9': (enth, ('SB60','Solargray',6,4), False),
 'D1':  (plus_in, (4,'C366',(4,4),'C366','S4','Ar90'), False),
 'D2':  (plus_in, (4,'C366',(4,4),'C366','S5','Ar90'), False),
 'D3':  (plus_in, (4,'C366',(4,4),'C366','S4','Air'), False),
 'D4':  (plus_in, (4,'LUMI',(4,4),'C366','S4','Ar90'), True),
 'D5':  (plus_in, (4,'SB70',(4,4),'C366','S4','Ar90'), False),
 'D6':  (plus_in, (6,'C366',(6,6),'C366','S4','Ar90'), False),
 'D7':  (plus_in, (4,'ZEN',(4,4),'LUMI','S4','Ar90'), True),
 'D8':  (plus_in, (5,'C366',(5,4),'C270','S4','Ar90'), False),
 'D9':  (plus_in, (4,'XTR6129',(4,4),'C366','S5','Ar90'), True),
 'D10': (plus_in, (6,'SKN183',(6,6),'SKN183','S4','Ar90'), True),
 'D11a':(plus_in, (5,'C180',(5,4),'C180','S4','Ar90'), False),
 'D11b':(plus_in, (5,'C180',(5,4),'C180','S5','Ar90'), False),
 'E1':  (plus_out, ((5,5),'C366',4,'C366','Ar90'), False),
 'E2':  (plus_out, ((4,4),'C366',4,'C366','Ar90'), False),
 'E3':  (plus_out, ((6,6),'C366',6,'C366','Ar90'), False),
 'E4':  (plus_out, ((5,5),'C270',4,'C272','Ar90'), False),
 'E5':  (plus_out, ((5,5),'C366',4,'C366','Air'), False),
 'E6':  (plus_out, ((5,5),'SB70',5,'LUMI','Ar90'), False),
 'E7':  (plus_out, ((5,4),'C366',4,'C366','Ar90'), False),
 'E8':  (plus_out, ((6,6),'C366',6,'SKN183','Ar90'), True),
 'G7':  (plus_out, ((4,4),'LUMI',4,'LUMI','Ar90'), True),
 'G8':  (plus_out, ((5,5),'C366',4,'LUMI','Ar90'), True),
}
bad = []
for k, (fn, args, cen) in MATRIX.items():
    r = fn(*args)
    if len(r) != 1: bad.append(f'{k}: {len(r)} matches')
    elif bool(r[0]['cen']) != cen: bad.append(f'{k}: cen={r[0]["cen"]}, plan expects {cen}')
gate(not bad, f'matrix validation ({len(MATRIX)} entries)', '; '.join(bad[:6]))

# -- Gate 6: golden.json numerics match the JSON rows ------------------------
GOLD_ROW = {'A1': (enth, ('C366','Clear',6,6)), 'A9': (enth, ('LUMI','Clear',4,4)),
            'A13': (enth, ('SB72','Starphire',6,4)),
            'D1': (plus_in, (4,'C366',(4,4),'C366','S4','Ar90')),
            'E1': (plus_out, ((5,5),'C366',4,'C366','Ar90'))}
gold = json.load(open(os.path.join(HERE, 'golden.json'), encoding='utf-8'))
bad = []
for k, (fn, args) in GOLD_ROW.items():
    row = fn(*args)[0]
    for f in ('uval','uvalIP','rval','shgc','uvalCEN','gFactor','tvis','routVis','tuv','cid'):
        if f in gold[k] and gold[k][f] != row.get(f):
            bad.append(f'{k}.{f}: golden {gold[k][f]} != data {row.get(f)}')
gate(not bad, 'golden anchors vs data', '; '.join(bad[:6]))

print(f'\n== pre-flight: {passes} gates passed, {len(fails)} failed ==')
if fails:
    print('ABORT — do not run the UI suite:')
    for f in fails: print('  ' + f)
sys.exit(1 if fails else 0)
