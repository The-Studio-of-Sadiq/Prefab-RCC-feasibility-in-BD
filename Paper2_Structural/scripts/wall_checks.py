"""Hand checks of special RC walls (5.0 m x 0.20 m) from exported pier forces under BNBC combos.
Shear: Vn = Acv(0.17*sqrt(fc) + rho_t*fy) <= 0.83*sqrt(fc)*Acv, phi = 0.60 (ACI 318 21.2.4.1)
Boundary elements (stress method, ACI 318 18.10.6.3): sigma = Pu/Ag + Mu/S > 0.2 fc -> special BE required
Flexure-axial: Cardenas & Magura approximation for uniformly distributed vertical steel, phi = 0.65-0.90 per strain;
reports minimum rho_l (>= 0.0025) giving phi*Mn >= Mu.
usage: wall_checks.py 'Pier Forces.csv' [label]"""
import csv, sys, math, json
fn = sys.argv[1]; lab = sys.argv[2] if len(sys.argv) > 2 else ''
fc, fy, lw, tw = 28.0, 420.0, 5.0, 0.20
Ag = lw * tw; S = tw * lw ** 2 / 6; Acv = Ag
b1 = 0.85
rows = list(csv.DictReader(open(fn, encoding='utf-8')))
def Mn_cm(rho, Nu):  # kN, kN-m ; Nu compression positive (kN)
    As = rho * Ag * 1e6  # mm2
    w = rho * fy / fc; a = Nu * 1e3 / (lw * 1e3 * tw * 1e3 * fc)
    c_l = (w + a) / (2 * w + 0.85 * b1)
    Mn = 0.5 * As * fy * lw * 1e3 * (1 + Nu * 1e3 / (As * fy)) * (1 - c_l)  # N-mm
    # strain-based phi: eps_t = 0.003*(d - c)/c with d ~ 0.8 lw
    c = c_l * lw; et = 0.003 * (0.8 * lw - c) / c if c > 0 else 1
    phi = 0.65 if et <= 0.002 else (0.90 if et >= 0.005 else 0.65 + 0.25 * (et - 0.002) / 0.003)
    return Mn / 1e6, phi
res = {}
for r in rows:
    if r['Story'] != 'Story1' and r['Story'] != 'Story2': pass
    if r['Location'] != 'Bottom': continue
    key = (r['Pier'], r['Story'])
    P = -float(r['P']); V = abs(float(r['V2'])); M = abs(float(r['M3']))
    sig = P / Ag / 1e3 + M / S / 1e3  # MPa
    cur = res.setdefault(key, dict(Vu=0, Mu=0, Pu_max=-1e9, Pu_min=1e9, sig=0, rho_req=0.0025))
    cur['Vu'] = max(cur['Vu'], V); cur['Mu'] = max(cur['Mu'], M); cur['sig'] = max(cur['sig'], sig)
    cur['Pu_max'] = max(cur['Pu_max'], P); cur['Pu_min'] = min(cur['Pu_min'], P)
    rho = 0.0025
    while rho < 0.06:
        Mn, phi = Mn_cm(rho, max(P, 0.0))
        if phi * Mn >= M: break
        rho += 0.0005
    cur['rho_req'] = max(cur['rho_req'], rho)
out = []
for (pier, st), c in sorted(res.items(), key=lambda kv: (kv[0][0], int(kv[0][1][5:]))):
    Vmax = 0.6 * 0.83 * math.sqrt(fc) * Acv * 1e3
    rho_t = max(0.0025, (c['Vu'] / 0.6 / (Acv * 1e3) - 0.17 * math.sqrt(fc)) / fy)
    out.append(dict(pier=pier, story=st, Vu=round(c['Vu']), phiVn_max=round(Vmax), shear_DC=round(c['Vu'] / Vmax, 3),
                    rho_t_req=round(rho_t, 4), Mu=round(c['Mu']), Pu_max=round(c['Pu_max']), Pu_min=round(c['Pu_min']),
                    sigma_MPa=round(c['sig'], 2), BE_required=c['sig'] > 0.2 * fc, rho_l_req=round(c['rho_req'], 4)))
for o in out:
    if o['story'] in ('Story1', 'Story2', 'Story5', 'Story10'): print(o)
json.dump(out, open(fn.replace('.csv', f'_wallcheck{lab}.json'), 'w'), indent=1)
