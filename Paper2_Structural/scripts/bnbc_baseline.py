"""Create the BNBC 2020 cast-in-situ baseline from a copy of the original model.
- replaces the off-centre U-core with walls given in a layout spec
- sets ELF user coefficient (BNBC SD, R=6) with +/-5% eccentricity
- adds a BNBC 2020 site-class-SD design response spectrum and RSx/RSy cases
usage: bnbc_baseline.py src.EDB dst.EDB layout_name"""
import sys, json, comtypes.client
src, dst, layout = sys.argv[1], sys.argv[2], sys.argv[3]
H = [3.0 * i for i in range(11)]
LAYOUTS = {
    # each wall: (x1,y1,x2,y2, label) ; point-symmetric about (10, 7.5)
    'perim4': [(0, 5, 0, 10, 'WY1'), (20, 5, 20, 10, 'WY2'), (5, 0, 10, 0, 'WX1'), (10, 15, 15, 15, 'WX2')],
    'perim6': [(0, 5, 0, 10, 'WY1'), (20, 5, 20, 10, 'WY2'), (5, 0, 10, 0, 'WX1'), (10, 15, 15, 15, 'WX2'),
               (10, 0, 15, 0, 'WX3'), (5, 15, 10, 15, 'WX4')],
}
WALL_PROP = sys.argv[4] if len(sys.argv) > 4 else 'WALL_200'
# BNBC 2020 parameters
Z, I, R, S, TB, TC, TD, eta = 0.20, 1.0, 6.0, 1.35, 0.20, 0.80, 2.0, 1.0
def Cs(T):
    if T <= TB: return S * (1 + T / TB * (2.5 * eta - 1))
    if T <= TC: return 2.5 * S * eta
    if T <= TD: return 2.5 * S * eta * TC / T
    return 2.5 * S * eta * TC * TD / T ** 2
def Sa(T): return max(2 / 3 * Z * I / R * Cs(T), 0.67 * 0.11 * Z * I)
Ta = 0.0488 * 30 ** 0.75
# Design period: analysed T (passed as argv[5]) capped at 1.4*Ta (BNBC 2.5.7.2a); default Ta
T_an = float(sys.argv[5]) if len(sys.argv) > 5 else Ta
T_use = min(T_an, 1.4 * Ta)
C_elf = Sa(T_use)
k_elf = 1.0 if T_use <= 0.5 else (2.0 if T_use >= 2.5 else 1 + (T_use - 0.5) / 2.0)
helper = comtypes.client.CreateObject('ETABSv1.Helper')
import comtypes.gen.ETABSv1 as E
helper = helper.QueryInterface(E.cHelper)
etabs = helper.CreateObjectProgID("CSI.ETABS.API.ETABSObject")
etabs.ApplicationStart()
log = {}
try:
    m = etabs.SapModel
    m.File.OpenFile(src); m.SetPresentUnits(6); m.SetModelIsLocked(False)
    # 1. delete existing walls
    names = m.AreaObj.GetNameList()[1]
    deleted = [n for n in names if m.AreaObj.GetProperty(n)[0].startswith(('WALL', 'CORE'))]
    for n in deleted: m.AreaObj.Delete(n)
    log['deleted_walls'] = len(deleted)
    # 2. add new walls storey by storey
    added = []
    for (x1, y1, x2, y2, lab) in LAYOUTS[layout]:
        m.PierLabel.SetPier(lab)
        for s in range(10):
            z0, z1 = H[s], H[s + 1]
            r = m.AreaObj.AddByCoord(4, [x1, x2, x2, x1], [y1, y2, y2, y1], [z0, z0, z1, z1], '', WALL_PROP)
            nm = r[3]
            m.AreaObj.SetPier(nm, lab)
            added.append(nm)
    log['added_walls'] = len(added)
    # 3. ELF user coefficient via editable table
    db = m.DatabaseTables
    t = 'Load Pattern Definitions - Auto Seismic - User Coefficient'
    r = db.GetTableForEditingArray(t, '')
    ver, fields, nrec, data = r[0], list(r[1]), r[2], list(r[3]); nf = len(fields)
    rows = [data[i * nf:(i + 1) * nf] for i in range(nrec)]
    fi = {f: i for i, f in enumerate(fields)}
    for row in rows:
        if row[fi['Name']] in ('EQx', 'EQy'):
            xdir = row[fi['Name']] == 'EQx'
            for f in ('XDir', 'YDir'): row[fi[f]] = 'No'
            for f in ('XDirPlusE', 'XDirMinusE'): row[fi[f]] = 'Yes' if xdir else 'No'
            for f in ('YDirPlusE', 'YDirMinusE'): row[fi[f]] = 'No' if xdir else 'Yes'
            row[fi['C']] = f'{C_elf:.5f}'; row[fi['K']] = f'{k_elf:.4f}'
    flat = [v for row in rows for v in row]
    log['set_table'] = str(db.SetTableForEditingArray(t, ver, fields, nrec, flat))
    ap = db.ApplyEditedTables(True)
    log['apply'] = [str(x) for x in ap]
    # 3b. mass source: add partition-wall pattern (BNBC 2.5.7.3 includes partitions in W)
    t3 = 'Mass Source Definition'
    r3 = db.GetTableForEditingArray(t3, '')
    ver3, f3 = r3[0], list(r3[1]); nf3 = len(f3); d3 = list(r3[3])
    rows3 = [d3[i * nf3:(i + 1) * nf3] for i in range(r3[2])]
    if not any(r[f3.index('LoadPattern')] == 'WALL' for r in rows3):
        row = [''] * nf3; row[f3.index('Name')] = 'MsSrc1'; row[f3.index('LoadPattern')] = 'WALL'; row[f3.index('Multiplier')] = '1'
        rows3.append(row)
    log['mass_table'] = str(db.SetTableForEditingArray(t3, ver3, f3, len(rows3), [v for r in rows3 for v in r])[-1])
    log['mass_apply'] = str(db.ApplyEditedTables(True)[:4])
    # 4. response spectrum function and cases
    Ts = [round(0.02 * i, 3) for i in range(0, 201)]
    vals = [Sa(T) for T in Ts]
    t2 = 'Functions - Response Spectrum - User Defined'
    r2 = db.GetTableForEditingArray(t2, '')
    ver2, f2 = r2[0], list(r2[1]); nf2 = len(f2); old = list(r2[3])
    rows2 = [old[i * nf2:(i + 1) * nf2] for i in range(r2[2])]
    for j, (T, v) in enumerate(zip(Ts, vals)):
        row = [''] * nf2
        row[f2.index('Name')] = 'BNBC20_SD'; row[f2.index('Period')] = f'{T:.3f}'; row[f2.index('Value')] = f'{v:.6f}'
        if j == 0 and 'DampRatio' in f2: row[f2.index('DampRatio')] = '0.05'
        rows2.append(row)
    flat2 = [v for row in rows2 for v in row]
    log['rs_table'] = str(db.SetTableForEditingArray(t2, ver2, f2, len(rows2), flat2))
    log['rs_apply'] = [str(x) for x in db.ApplyEditedTables(True)]
    log['funcs'] = str(m.Func.GetNameList())
    m.LoadCases.ModalEigen.SetNumberModes('Modal', 30, 1)
    for case, d in (('RSx', 'U1'), ('RSy', 'U2')):
        m.LoadCases.ResponseSpectrum.SetCase(case)
        m.LoadCases.ResponseSpectrum.SetLoads(case, 1, [d], ['BNBC20_SD'], [9.80665], ['Global'], [0.0])
        m.LoadCases.ResponseSpectrum.SetModalCase(case, 'Modal')
        m.LoadCases.ResponseSpectrum.SetEccentricity(case, 0.05)
    log['C_elf'] = C_elf; log['k'] = k_elf; log['Ta'] = Ta; log['T_use'] = T_use
    log['save'] = m.File.Save(dst)
finally:
    etabs.ApplicationExit(False)
print(json.dumps(log, default=str))
