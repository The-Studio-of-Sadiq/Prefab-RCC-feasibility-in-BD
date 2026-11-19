"""Preliminary bored-pile foundation design from ETABS joint reactions (service / allowable-stress level).

Pile: bored cast-in-situ, 600 mm diameter, 24 m long, founded in the dense fine sand
(soil report Sec 3.7: skin friction 1,307-1,548 kN across BH-1..5 for 600 mm x 24 m).
Capacity basis (stated assumption): the tabulated value is taken as the ALLOWABLE compression capacity,
Qa = 1,307 kN (lowest borehole). Sensitivity: if the table is ultimate, Qa = 1,307/2.5 = 523 kN.
Uplift (allowable) taken as 0.5*Qa (skin friction only, reduced). Lateral capacity per pile 50 kN (soft clay, free head, screening).

Load combinations at foundation level (allowable-stress style, BNBC 2.7.2-type):
  S1 = D + L
  S2 = D + 0.75L + 0.75(0.7E)      E = EQx, EQy with +/- accidental eccentricity steps, both signs
  S3 = 0.6D + 0.7E                  (uplift check)
D = Dead + FF + PW + WALL. Base moments from the fixed-base model are distributed to piles.
usage: pile_design.py "Joint Reactions.csv" out.json [Qa_kN]
"""
import csv, sys, json, math, collections

fn, out = sys.argv[1], sys.argv[2]
QA = float(sys.argv[3]) if len(sys.argv) > 3 else 1307.0
QT = 0.5 * QA
HLAT = 50.0
S = 1.8   # pile spacing 3D
# pile layouts (x, y) relative to cap centre, cap plan size (Lx, Ly), cap depth
LAYOUTS = {
    2: ([(-S / 2, 0), (S / 2, 0)], (S + 0.9, 0.9 + 0.3), 1.0),
    3: ([(-S / 2, -S / (2 * math.sqrt(3))), (S / 2, -S / (2 * math.sqrt(3))), (0, S / math.sqrt(3))], (S + 0.9, S * 0.866 + 0.9), 1.0),
    4: ([(-S / 2, -S / 2), (S / 2, -S / 2), (-S / 2, S / 2), (S / 2, S / 2)], (S + 0.9, S + 0.9), 1.1),
    5: ([(-S / 2, -S / 2), (S / 2, -S / 2), (-S / 2, S / 2), (S / 2, S / 2), (0, 0)], (S + 0.9, S + 0.9), 1.2),
    6: ([(-S, -S / 2), (0, -S / 2), (S, -S / 2), (-S, S / 2), (0, S / 2), (S, S / 2)], (2 * S + 0.9, S + 0.9), 1.2),
    8: ([(x, y) for x in (-1.5 * S, -0.5 * S, 0.5 * S, 1.5 * S) for y in (-S / 2, S / 2)], (3 * S + 0.9, S + 0.9), 1.4),
    9: ([(x, y) for x in (-S, 0, S) for y in (-S, 0, S)], (2 * S + 0.9, 2 * S + 0.9), 1.5),
}
rows = list(csv.DictReader(open(fn, encoding='utf-8')))
R = collections.defaultdict(lambda: collections.defaultdict(list))
for r in rows:
    v = [float(r[k]) for k in ('FX', 'FY', 'FZ', 'MX', 'MY')]
    R[r['UniqueName']][r['OutputCase']].append(v)
def one(j, c):
    return R[j][c][0] if R[j][c] else [0.0] * 5
import os
MD = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'analysis', 'model_definition.json')))
XY = {k: [round(v['xyz'][0], 2), round(v['xyz'][1], 2)] for k, v in MD['supports'].items()}
res = []
for j in sorted(R, key=lambda x: int(x)):
    D = [sum(one(j, c)[i] for c in ('Dead', 'FF', 'PW', 'WALL')) for i in range(5)]
    L = one(j, 'Live')
    combos = {'S1 D+L': [D[i] + L[i] for i in range(5)]}
    for eq in ('EQx', 'EQy'):
        for k, e in enumerate(R[j][eq]):
            for sg in (1, -1):
                combos[f'S2 D+0.75L{"+" if sg > 0 else "-"}0.525{eq}#{k+1}'] = [D[i] + 0.75 * L[i] + sg * 0.525 * e[i] for i in range(5)]
                combos[f'S3 0.6D{"+" if sg > 0 else "-"}0.7{eq}#{k+1}'] = [0.6 * D[i] + sg * 0.7 * e[i] for i in range(5)]
    chosen = None
    for n in sorted(LAYOUTS):
        pts, cap, t = LAYOUTS[n]
        capw = cap[0] * cap[1] * t * 24.0          # cap self-weight kN
        Ix = sum(y * y for x, y in pts); Iy = sum(x * x for x, y in pts)
        pmax, pmin, hmax, govmax, govmin = -1e9, 1e9, 0, '', ''
        for c, (fx, fy, fz, mx, my) in combos.items():
            P = fz + (capw if c.startswith(('S1', 'S2')) else 0.6 * capw)
            for (x, y) in pts:
                p = P / n + (mx * y / Ix if Ix else 0) - (my * x / Iy if Iy else 0)
                if p > pmax: pmax, govmax = p, c
                if p < pmin: pmin, govmin = p, c
            hmax = max(hmax, math.hypot(fx, fy) / n)
        if pmax <= QA and pmin >= -QT:   # lateral checked globally below (ground slab + tie beams share base shear)
            chosen = dict(n=n, cap_LxLyT=[round(cap[0], 2), round(cap[1], 2), t], pile_max=round(pmax), gov_max=govmax,
                          pile_min=round(pmin), gov_min=govmin, H_per_pile=round(hmax, 1))
            break
    if chosen is None:
        chosen = dict(n='>9', pile_max=round(pmax), pile_min=round(pmin), H_per_pile=round(hmax, 1))
    chosen.update(joint=j, xy=XY.get(j), DL=round(combos['S1 D+L'][2]))
    res.append(chosen)
tot = sum(c['n'] for c in res if isinstance(c['n'], int))
# global lateral check: service-level base shear 0.7*V shared by all piles through ground slab / tie-beam diaphragm
Vserv = 0.7 * max(sum(math.hypot(*R[j][eq][k][:2]) for j in R) for eq in ('EQx', 'EQy') for k in range(len(next(iter(R.values()))[eq])))
H_glob = Vserv / tot if tot else None
n_lat = math.ceil(Vserv / HLAT)
Pmax = max(c['DL'] for c in res)
summary = dict(Qa=QA, Qt=QT, H_allow=HLAT, total_piles=tot, V_service_kN=round(Vserv), H_per_pile_global=round(H_glob, 1), piles_needed_for_lateral=n_lat, caps=res,
               tie_beam_force_kN=round(0.10 * Pmax), note='Tie (grade) beams between caps designed for 10% of the larger column load (seismic interconnection)')
json.dump(summary, open(out, 'w'), indent=1)
print(f'Qa={QA:.0f} kN  total piles={tot}  max D+L={Pmax:.0f} kN  tie force={0.1*Pmax:.0f} kN  V_serv={Vserv:.0f} kN  H/pile={H_glob:.1f} kN (allow {HLAT})  piles for lateral={n_lat}')
for c in res: print(c['joint'], c['xy'], c['DL'], c['n'], c.get('cap_LxLyT'), c['pile_max'], c['pile_min'], c['H_per_pile'], c.get('gov_min', ''))
