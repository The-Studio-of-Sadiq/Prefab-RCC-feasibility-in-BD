"""Compare BNBC check results and wall shear share across model variants.
usage: compare_variants.py label=tables_dir ..."""
import csv, os, sys, json, subprocess
rows = []
for arg in sys.argv[1:]:
    lab, d = arg.split('=')
    subprocess.run([sys.executable, os.path.join(os.path.dirname(__file__), 'bnbc_checks.py'), d, lab], capture_output=True)
    c = json.load(open(os.path.join(d, '_bnbc_checks.json')))
    pf = list(csv.DictReader(open(os.path.join(d, 'Pier Forces.csv'), encoding='utf-8')))
    def wall_share(case, piers):
        v = {}
        for r in pf:
            if r['Story'] == 'Story1' and r['OutputCase'] == case and r['Location'] == 'Bottom' and r['Pier'] in piers:
                v[(r['Pier'], r.get('StepNumber', ''))] = abs(float(r['V2']))
        steps = {k[1] for k in v}
        return max(sum(val for (p, s), val in v.items() if s == st) for st in steps) if v else None
    sx = wall_share('EQx', ('WX1', 'WX2')); sy = wall_share('EQy', ('WY1', 'WY2'))
    rows.append(dict(variant=lab, Tx=c['Tx'], Ty=c['Ty'], V_ELF=c['V_ELF'][0], V_RSx=c['V_RS'][0], V_RSy=c['V_RS'][1],
                     drift_x=c['drift_EQx'], drift_y=c['drift_EQy'], drift_RSx=c['drift_RSx'], drift_RSy=c['drift_RSy'],
                     tors_x=c['torsion_EQx'], tors_y=c['torsion_EQy'],
                     wall_share_x=sx / c['V_ELF'][0] if sx else None, wall_share_y=sy / c['V_ELF'][1] if sy else None))
hdr = list(rows[0].keys())
print(' | '.join(hdr))
for r in rows: print(' | '.join(f'{v:.4g}' if isinstance(v, float) else str(v) for v in r.values()))
out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'analysis', 'variant_comparison.json')
json.dump(rows, open(out, 'w'), indent=1)
