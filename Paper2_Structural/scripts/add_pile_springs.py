"""Replace fixed supports by linear pile-group springs (soil-structure interaction sensitivity).
usage: add_pile_springs.py src.EDB dst.EDB pile_design.json case
  case 'central': vertical k = Qa / 10 mm per pile, lateral 5,000 kN/m per pile
  case 'soft'   : vertical k = Qa / 20 mm per pile, lateral 2,500 kN/m per pile
  case 'stiff'  : vertical k = Qa / 5 mm per pile,  lateral 10,000 kN/m per pile
Rotational stiffness of each cap = sum(kv * d^2) over its piles (rigid cap). Torsional rotation left free-ish (small spring).
All values are screening-level, derived from the soil report capacities; documented as assumptions."""
import sys, json, math, comtypes.client
src, dst, pj, case = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
P = json.load(open(pj))
QA = P['Qa']
S = 1.8
LAY = {2: [(-S / 2, 0), (S / 2, 0)], 3: [(-S / 2, -S / (2 * math.sqrt(3))), (S / 2, -S / (2 * math.sqrt(3))), (0, S / math.sqrt(3))],
       4: [(-S / 2, -S / 2), (S / 2, -S / 2), (-S / 2, S / 2), (S / 2, S / 2)],
       5: [(-S / 2, -S / 2), (S / 2, -S / 2), (-S / 2, S / 2), (S / 2, S / 2), (0, 0)],
       6: [(-S, -S / 2), (0, -S / 2), (S, -S / 2), (-S, S / 2), (0, S / 2), (S, S / 2)]}
SETTLE = {'stiff': 0.005, 'central': 0.010, 'soft': 0.020}
KH = {'stiff': 10000.0, 'central': 5000.0, 'soft': 2500.0}
kv1 = QA / SETTLE[case]
kh1 = KH[case]
helper = comtypes.client.CreateObject('ETABSv1.Helper')
import comtypes.gen.ETABSv1 as E
helper = helper.QueryInterface(E.cHelper)
etabs = helper.CreateObjectProgID("CSI.ETABS.API.ETABSObject")
etabs.ApplicationStart()
log = {'case': case, 'kv_per_pile': kv1, 'kh_per_pile': kh1, 'joints': {}}
try:
    m = etabs.SapModel
    m.File.OpenFile(src); m.SetPresentUnits(6); m.SetModelIsLocked(False)
    for c in P['caps']:
        j, n = c['joint'], c['n']
        pts = LAY[n]
        kv = n * kv1; kh = n * kh1
        krx = sum(kv1 * y * y for x, y in pts); kry = sum(kv1 * x * x for x, y in pts)
        k = [kh, kh, kv, krx, kry, 1e3]
        m.PointObj.SetRestraint(j, [False] * 6)
        r = m.PointObj.SetSpring(j, k, 0, False, True)
        log['joints'][j] = dict(n=n, k=[round(v) for v in k], ret=str(r))
    # Grade (tie) beams 300x600 between adjacent pile caps on every grid line at base level (BNBC seismic interconnection)
    if len(sys.argv) <= 5 or sys.argv[5] != 'nogb':
        m.PropFrame.SetRectangle('GB_300x600', 'C28_Precast', 0.6, 0.3)
        m.PropFrame.SetModifiers('GB_300x600', [1, 1, 1, 1, 0.35, 0.35, 1, 1])
        xy = {}
        for c in P['caps']:
            xy[(round(c['xy'][0]), round(c['xy'][1]))] = c['joint']
        ngb = 0
        for (x, y), j in xy.items():
            for nb in ((x + 5, y), (x, y + 5)):
                if nb in xy:
                    r = m.FrameObj.AddByPoint(j, xy[nb], '', 'GB_300x600')
                    ngb += 1
        log['grade_beams'] = ngb
    log['save'] = m.File.Save(dst)
finally:
    etabs.ApplicationExit(False)
print(json.dumps({k: v for k, v in log.items() if k != 'joints'}), len(log['joints']), 'joints')
