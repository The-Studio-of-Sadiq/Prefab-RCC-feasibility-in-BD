"""Summarise ETABS ACI 318-19 frame design + wall hand checks for a design_* folder."""
import csv, sys, os, json, subprocess, collections
d = sys.argv[1]; lab = sys.argv[2] if len(sys.argv) > 2 else os.path.basename(d)
def T(n): return list(csv.DictReader(open(os.path.join(d, n + '.csv'), encoding='utf-8')))
col = T('Concrete Column Design Summary - ACI 318-19'); bm = T('Concrete Beam Design Summary - ACI 318-19'); jt = T('Concrete Joint Design Summary - ACI 318-19')
Ag_c, bd = 0.25, 0.3 * 0.44
S = {'label': lab}
fails = lambda rows: [r for r in rows if (r.get('ErrMsg', 'No Message') not in ('No Message', '')) or ('O/S' in r.get('Status', '') or 'Fail' in r.get('Status', ''))]
def ag(sec):
    b = int(sec.split('_')[1].split('x')[0]) / 1000
    return b * b
rc = [float(r['As']) / ag(r['DesignSect']) for r in col if r['As']]
S['col_rho_max'] = max(rc); S['col_rho_gt_4pct'] = sum(x > 0.04 for x in rc)
S['col_fail'] = len(fails(col)); S['col_msgs'] = collections.Counter(r['ErrMsg'] for r in col).most_common(3)
rb = [max(float(r['AsTop'] or 0), float(r['AsBot'] or 0)) / bd for r in bm]
S['beam_rho_max'] = max(rb); S['beam_rho_gt_2.5pct'] = sum(x > 0.025 for x in rb)
S['beam_fail'] = len(fails(bm)); S['beam_msgs'] = collections.Counter(r['ErrMsg'] for r in bm).most_common(3)
js = [max(float(r['JSMajRatio'] or 0), float(r['JSMinRatio'] or 0)) for r in jt]
bc = [max(float(r['BCMajRatio'] or 0), float(r['BCMinRatio'] or 0)) for r in jt]
S['joint_shear_max'] = max(js); S['joint_shear_gt1'] = sum(x > 1 for x in js)
S['bc_ratio_max'] = max(bc); S['bc_gt_1'] = sum(x > 1 for x in bc)   # ETABS reports beam/column capacity ratio; <=1/1.2 required for SMF
# walls
r = subprocess.run([sys.executable, os.path.join(os.path.dirname(__file__), 'wall_checks.py'), os.path.join(d, 'Pier Forces.csv'), lab], capture_output=True, text=True)
w = json.load(open(os.path.join(d, f'Pier Forces_wallcheck{lab}.json')))
S['wall_shear_DC_max'] = max(x['shear_DC'] for x in w); S['wall_rho_t_req_max'] = max(x['rho_t_req'] for x in w)
S['wall_rho_l_req_max'] = max(x['rho_l_req'] for x in w); S['wall_BE_storeys'] = sorted({x['story'] for x in w if x['BE_required']})
S['wall_sigma_max'] = max(x['sigma_MPa'] for x in w); S['wall_Pu_min'] = min(x['Pu_min'] for x in w)
# Peak elastic edge tension at wall ends (0.9D+E): sigma = Pu/Ag - Mu/S (MPa, negative = tension).
# BNBC 6.10.5.2.5 minimum vertical ties (44 kN per m) are compared with the tension resultant per metre of wall
# in the tension zone, i.e. 0.5*|sigma|*t (kN per m of wall length at the extreme fibre, per unit length).
edge = []
for x in w:
    sig = x['Pu_min'] / 1.0 / 1e3 - x['Mu'] / (0.2 * 5.0 ** 2 / 6) / 1e3   # MPa
    edge.append(sig)
S['wall_edge_stress_min_MPa'] = min(edge)
S['wall_edge_tension_force_kN_per_m'] = max(0.0, -min(edge)) * 1e3 * 0.20   # kN per m length at extreme fibre
S['bnbc_min_vertical_tie_kN_per_m'] = 44.0
json.dump(S, open(os.path.join(d, '_design_summary.json'), 'w'), indent=1, default=str)
for k, v in S.items(): print(f'{k}: {v}')
