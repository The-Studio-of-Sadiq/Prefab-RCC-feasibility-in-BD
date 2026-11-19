"""BNBC 2020 checks on exported ETABS tables. usage: bnbc_checks.py tables_dir [label]"""
import csv, sys, os, json
d = sys.argv[1]; label = sys.argv[2] if len(sys.argv) > 2 else os.path.basename(d)
def T(n): return list(csv.DictReader(open(os.path.join(d, n + '.csv'), encoding='utf-8')))
Z, I, R, Cd, S, TC = 0.20, 1.0, 6.0, 5.0, 1.35, 0.80
Ta = 0.0488 * 30 ** 0.75; hs = 3.0
out = {'label': label}
mod = T('Modal Participating Mass Ratios')
out['modes'] = [(int(r['Mode']), float(r['Period']), float(r['UX']), float(r['UY']), float(r['RZ'])) for r in mod[:6]]
out['sum_mass_last'] = (float(mod[-1]['SumUX']), float(mod[-1]['SumUY']))
# fundamental translational periods = mode with max UX / UY
Tx = max(mod, key=lambda r: float(r['UX'])); Ty = max(mod, key=lambda r: float(r['UY']))
out['Tx'], out['Ty'] = float(Tx['Period']), float(Ty['Period'])
out['Ta'], out['1.4Ta'] = Ta, 1.4 * Ta
br = T('Base Reactions')
def vb(case, comp):
    v = [abs(float(r[comp])) for r in br if r['OutputCase'] == case]
    return max(v) if v else None
out['V_ELF'] = (vb('EQx', 'FX'), vb('EQy', 'FY'))
out['V_RS'] = (vb('RSx', 'FX'), vb('RSy', 'FY'))
out['RS_scale_forces'] = tuple(max(1.0, 0.85 * e / r) if (e and r) else None for e, r in zip(out['V_ELF'], out['V_RS']))
mass = T('Mass Summary by Story'); W = sum(float(r['UX']) for r in mass if r['Story'] != 'Base') * 9.80665
out['W_kN'] = W
# torsion
md = T('Story Max Over Avg Displacements')
for case, dr in (('EQx', 'X'), ('EQy', 'Y')):
    v = [float(r['Ratio']) for r in md if r['OutputCase'] == case and r['Direction'] == dr and r['Ratio']]
    rmax = max(v); out[f'torsion_{case}'] = rmax
    out[f'Ax_{case}'] = min(3.0, max(1.0, (rmax / 1.2) ** 2))
# drifts (design drift = Cd*elastic/I) from ELF and RS
dr = T('Story Drifts')
for case, dd in (('EQx', 'X'), ('EQy', 'Y'), ('RSx', 'X'), ('RSy', 'Y')):
    v = [float(r['Drift']) for r in dr if r['OutputCase'] == case and r['Direction'] == dd]
    if v: out[f'drift_{case}'] = max(v) * Cd / I
out['drift_limit'] = 0.020
json.dump(out, open(os.path.join(d, '_bnbc_checks.json'), 'w'), indent=1)
for k, v in out.items(): print(f'{k}: {v}')
