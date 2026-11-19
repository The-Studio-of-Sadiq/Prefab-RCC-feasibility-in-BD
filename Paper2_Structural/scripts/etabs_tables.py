"""Open an ETABS model copy, (optionally) run it, and dump database tables to CSV.
usage: etabs_tables.py model.EDB outdir [run=1] [table-name-filter ...]"""
import sys, os, csv, comtypes.client
path, outdir = sys.argv[1], sys.argv[2]
run = sys.argv[3] if len(sys.argv) > 3 else '1'
wanted = sys.argv[4:] or [
    'Modal Participating Mass Ratios', 'Modal Periods And Frequencies', 'Base Reactions', 'Story Drifts',
    'Story Forces', 'Mass Summary by Story', 'Centers Of Mass And Rigidity', 'Pier Forces',
    'Story Max Over Avg Displacements', 'Joint Displacements', 'Load Pattern Definitions',
    'Load Case Definitions - Summary', 'Mass Source Definition', 'Material Properties - Concrete Data',
    'Frame Assignments - Releases and Partial Fixity', 'Area Assignments - Pier Labels',
    'Story Definitions', 'Diaphragm Definitions', 'Joint Assignments - Restraints']
os.makedirs(outdir, exist_ok=True)
helper = comtypes.client.CreateObject('ETABSv1.Helper')
import comtypes.gen.ETABSv1 as E
helper = helper.QueryInterface(E.cHelper)
etabs = helper.CreateObjectProgID("CSI.ETABS.API.ETABSObject")
etabs.ApplicationStart()
try:
    m = etabs.SapModel
    m.File.OpenFile(path); m.SetPresentUnits(6)
    if run == '1':
        print('run', m.Analyze.RunAnalysis(), flush=True)
        m.Results.Setup.DeselectAllCasesAndCombosForOutput()
    db = m.DatabaseTables
    allt = db.GetAvailableTables()
    names = list(allt[1])
    open(os.path.join(outdir, '_available_tables.txt'), 'w').write('\n'.join(names))
    # include all load-pattern/auto-seismic tables
    extra = [n for n in names if 'Auto Seismic' in n or 'Response Spectrum' in n]
    for t in wanted + extra:
        hits = [n for n in names if n.lower() == t.lower()] or [n for n in names if n.lower().startswith(t.lower())]
        for name in hits[:4]:
            r = db.GetTableForDisplayArray(name, [], '')
            fields, nrec, data = list(r[2]), r[3], list(r[4])
            nf = len(fields)
            fn = os.path.join(outdir, name.replace('/', '_').replace(':', '') + '.csv')
            with open(fn, 'w', newline='', encoding='utf-8') as fh:
                w = csv.writer(fh); w.writerow(fields)
                for i in range(nrec): w.writerow(data[i * nf:(i + 1) * nf])
            print(f'{name}: {nrec} rows', flush=True)
finally:
    etabs.ApplicationExit(False)
