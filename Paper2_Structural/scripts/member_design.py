"""Member checks on a model copy.
1. Adds BNBC 2020 Sec 2.7.3 strength combinations (D = Dead+FF+PW+WALL; E = ELF EQx/EQy, both signs)
2. Runs ETABS concrete frame design (ACI 318-19 as the BNBC Part 6 Ch 6 proxy) -> column PMM / beam rebar summary
3. Exports pier forces for the BNBC combos for hand wall checks (wall_checks.py)
usage: member_design.py model.EDB outdir"""
import sys, os, csv, json, comtypes.client
src, outdir = sys.argv[1], sys.argv[2]; os.makedirs(outdir, exist_ok=True)
helper = comtypes.client.CreateObject('ETABSv1.Helper')
import comtypes.gen.ETABSv1 as E
helper = helper.QueryInterface(E.cHelper)
etabs = helper.CreateObjectProgID("CSI.ETABS.API.ETABSObject")
etabs.ApplicationStart()
log = {}
try:
    m = etabs.SapModel
    m.File.OpenFile(src); m.SetPresentUnits(6); m.SetModelIsLocked(False)
    D = ['Dead', 'FF', 'PW', 'WALL']
    combos = {'B1_1.4D': [(p, 1.4) for p in D], 'B2_1.2D+1.6L': [(p, 1.2) for p in D] + [('Live', 1.6)]}
    for eq in ('EQx', 'EQy'):
        for sg, s in (('+', 1.0), ('-', -1.0)):
            combos[f'B5_1.2D+L{sg}{eq}'] = [(p, 1.2) for p in D] + [('Live', 1.0), (eq, s)]
            combos[f'B7_0.9D{sg}{eq}'] = [(p, 0.9) for p in D] + [(eq, s)]
    for c, items in combos.items():
        m.RespCombo.Add(c, 0)
        for p, f in items: m.RespCombo.SetCaseList(c, 0, p, f)
    m.DesignConcrete.SetCode('ACI 318-19')
    # use only BNBC combos for strength design
    for c in m.RespCombo.GetNameList()[1]:
        m.DesignConcrete.SetComboStrength(c, c in combos)
    log['run'] = m.Analyze.RunAnalysis()
    log['design'] = m.DesignConcrete.StartDesign()
    cols = m.DesignConcrete.GetSummaryResultsColumn('ALL', 2) if False else None
    # summary via database tables (more robust than per-object calls)
    db = m.DatabaseTables
    names = list(db.GetAvailableTables()[1])
    for want in ('Concrete Column Design Summary', 'Concrete Beam Design Summary', 'Concrete Joint Design Summary', 'Pier Forces'):
        hits = [n for n in names if n.startswith(want)]
        for name in hits[:2]:
            if name == 'Pier Forces':
                m.Results.Setup.DeselectAllCasesAndCombosForOutput()
                for c in combos: m.Results.Setup.SetComboSelectedForOutput(c)
            r = db.GetTableForDisplayArray(name, [], '')
            f, n, d = list(r[2]), r[3], list(r[4]); nf = len(f)
            with open(os.path.join(outdir, name + '.csv'), 'w', newline='', encoding='utf-8') as fh:
                w = csv.writer(fh); w.writerow(f)
                for i in range(n): w.writerow(d[i * nf:(i + 1) * nf])
            log[name] = n
    log['design_tables_available'] = [n for n in names if 'Concrete' in n and 'Summary' in n]
finally:
    etabs.ApplicationExit(False)
print(json.dumps(log, default=str))
