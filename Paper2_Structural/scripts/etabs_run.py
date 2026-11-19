"""Run analysis on an ETABS model copy and export key results to JSON (kN, m)."""
import sys, json, comtypes.client
path, out = sys.argv[1], sys.argv[2]
helper = comtypes.client.CreateObject('ETABSv1.Helper')
import comtypes.gen.ETABSv1 as E
helper = helper.QueryInterface(E.cHelper)
etabs = helper.CreateObjectProgID("CSI.ETABS.API.ETABSObject")
etabs.ApplicationStart()
R = {}
try:
    m = etabs.SapModel
    m.File.OpenFile(path); m.SetPresentUnits(6)
    # seismic load definition
    for lp in ('EQx', 'EQy'):
        info = {}
        for attr in dir(m.LoadPatterns.AutoSeismic):
            pass
        try: info['code'] = str(m.LoadPatterns.AutoSeismic.GetAutoCode(lp))
        except Exception as ex: info['code_err'] = str(ex)[:80]
        R[lp + '_def'] = info
    R['autoseismic_methods'] = [a for a in dir(m.LoadPatterns.AutoSeismic) if a.startswith('Get')]
    print('run', m.Analyze.RunAnalysis(), flush=True)
    res = m.Results; setup = res.Setup
    def sel(cases=(), combos=()):
        setup.DeselectAllCasesAndCombosForOutput()
        for c in cases: setup.SetCaseSelectedForOutput(c)
        for c in combos: setup.SetComboSelectedForOutput(c)
    sel(['Modal'])
    mp = res.ModalParticipatingMassRatios()
    R['modal'] = [dict(mode=i + 1, T=mp[4][i], UX=mp[5][i], UY=mp[6][i], SumUX=mp[8][i], SumUY=mp[9][i], RZ=mp[13][i]) for i in range(mp[0])]
    sel(['EQx', 'EQy', 'Dead', 'Live', 'FF', 'PW', 'WALL'])
    br = res.BaseReact()
    R['base'] = [dict(case=br[1][i], FX=br[4][i], FY=br[5][i], FZ=br[6][i]) for i in range(br[0])]
    dr = res.StoryDrifts()
    R['drifts'] = [dict(story=dr[1][i], case=dr[2][i], dir=dr[5][i], drift=dr[6][i]) for i in range(dr[0])]
    sf = res.StoryForces()
    R['story_forces'] = [dict(story=sf[1][i], case=sf[2][i], loc=sf[5][i], P=sf[6][i], VX=sf[7][i], VY=sf[8][i]) for i in range(sf[0])]
    # masses
    try:
        mm = res.AssembledJointMass_1('', 2) if hasattr(res, 'AssembledJointMass_1') else res.AssembledJointMass('', 2)
        R['total_mass_x'] = sum(mm[4]) if isinstance(mm[4], tuple) else None
    except Exception as ex: R['mass_err'] = str(ex)[:100]
    # joint loads on EQ patterns (user-applied story forces?)
    jl = {}
    for p in m.PointObj.GetNameList()[1]:
        r = m.PointObj.GetLoadForce(p)
        if r[0] > 0:
            for k in range(r[0]):
                if r[2][k] in ('EQx', 'EQy'): jl.setdefault(r[2][k], []).append([p, r[4][k], r[5][k]])
    R['eq_joint_loads'] = jl
    # story drift via displacement of diaphragm centers
    sel(['EQx', 'EQy'])
    # wall pier forces
    try:
        pf = res.PierForce()
        R['pier_forces'] = [dict(story=pf[1][i], pier=pf[2][i], case=pf[3][i], loc=pf[4][i], P=pf[5][i], V2=pf[6][i], M3=pf[10][i]) for i in range(pf[0])]
    except Exception as ex: R['pier_err'] = str(ex)[:100]
finally:
    etabs.ApplicationExit(False)
json.dump(R, open(out, 'w'), indent=1, default=str)
print('modal', [(d['mode'], round(d['T'], 3), round(d['UX'], 3), round(d['UY'], 3), round(d['RZ'], 3)) for d in R.get('modal', [])][:6])
print('base', [(d['case'], round(d['FX'], 1), round(d['FY'], 1), round(d['FZ'], 1)) for d in R.get('base', [])])
print('eqdef', R.get('EQx_def'), R.get('autoseismic_methods'))
print('eq joint loads', {k: len(v) for k, v in R.get('eq_joint_loads', {}).items()}, R.get('mass_err'), R.get('total_mass_x'))
print('piers', len(R.get('pier_forces', [])), R.get('pier_err'))
