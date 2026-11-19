"""Extract model definition from an ETABS model copy into JSON (kN, m)."""
import sys, json, collections, comtypes.client
path, out = sys.argv[1], sys.argv[2]
helper = comtypes.client.CreateObject('ETABSv1.Helper')
import comtypes.gen.ETABSv1 as E
helper = helper.QueryInterface(E.cHelper)
etabs = helper.CreateObjectProgID("CSI.ETABS.API.ETABSObject")
etabs.ApplicationStart()
m = etabs.SapModel
m.File.OpenFile(path)
m.SetPresentUnits(6)
D = {}
# frames
fr = m.FrameObj.GetAllFrames()
names = fr[1]
D['frames'] = []
print("frames start", len(names), flush=True)
for i, n in enumerate(names):
    prop = fr[2][i]
    D['frames'].append(dict(name=n, prop=prop, story=fr[3][i], p1=fr[4][i], p2=fr[5][i],
                            xyz1=[fr[6][i], fr[7][i], fr[8][i]], xyz2=[fr[9][i], fr[10][i], fr[11][i]],
                            design=m.FrameObj.GetDesignOrientation(n)[0],
                            release=list(m.FrameObj.GetReleases(n)[:2])))
D['frame_prop_count'] = dict(collections.Counter(f['prop'] for f in D['frames']))
# areas
print("areas start", flush=True)
ar = m.AreaObj.GetNameList()[1]
D['areas'] = []
for n in ar:
    pts = m.AreaObj.GetPoints(n)[1]
    coords = [list(m.PointObj.GetCoordCartesian(p)[:3]) for p in pts]
    D['areas'].append(dict(name=n, prop=m.AreaObj.GetProperty(n)[0], pier=m.AreaObj.GetPier(n)[0],
                           spandrel=m.AreaObj.GetSpandrel(n)[0], diaphragm=m.AreaObj.GetDiaphragm(n)[0],
                           coords=coords, modifiers=list(m.AreaObj.GetModifiers(n)[0])))
D['area_prop_count'] = dict(collections.Counter(a['prop'] for a in D['areas']))
# section definitions actually used
D['frame_sections'] = {}
for s in D['frame_prop_count']:
    r = m.PropFrame.GetRectangle(s)
    D['frame_sections'][s] = dict(rect=list(r[:4]) if r[-1] == 0 else None,
                                  modifiers=list(m.PropFrame.GetModifiers(s)[0]))
D['area_sections'] = {}
for s in D['area_prop_count']:
    try:
        w = m.PropArea.GetWall(s); D['area_sections'][s] = dict(kind='wall', raw=[str(x) for x in w])
    except Exception:
        pass
    try:
        sl = m.PropArea.GetSlab(s)
        if sl[-1] == 0: D['area_sections'][s] = dict(kind='slab', raw=[str(x) for x in sl])
    except Exception:
        pass
    D['area_sections'][s]['modifiers'] = list(m.PropArea.GetModifiers(s)[0])
print("materials", flush=True)
# materials
D['materials'] = {}
for mat in m.PropMaterial.GetNameList()[1]:
    iso = m.PropMaterial.GetMPIsotropic(mat)
    conc = m.PropMaterial.GetOConcrete_1(mat) if m.PropMaterial.GetMaterial(mat)[0] == 2 else None
    D['materials'][mat] = dict(E=iso[0], nu=iso[1], wt=m.PropMaterial.GetWeightAndMass(mat)[:2],
                               fc=conc[0] if conc else None)
print("supports", flush=True)
# supports
pts = m.PointObj.GetNameList()[1]
D['supports'] = {}
for p in pts:
    r = m.PointObj.GetRestraint(p)[0]
    if any(r):
        D['supports'][p] = dict(restraint=list(r), xyz=list(m.PointObj.GetCoordCartesian(p)[:3]))
print("patterns", flush=True)
# load patterns & seismic definitions
D['load_patterns'] = {}
for lp in m.LoadPatterns.GetNameList()[1]:
    t = m.LoadPatterns.GetLoadType(lp)[0]
    D['load_patterns'][lp] = dict(type=t, selfwt=m.LoadPatterns.GetSelfWTMultiplier(lp)[0])
    try:
        D['load_patterns'][lp]['autoseismic'] = m.LoadPatterns.AutoSeismic.GetAutoSeismicCode(lp)[0]
    except Exception:
        pass
print("seismic", flush=True)
# user seismic coefficient if any
for lp in ('EQx', 'EQy'):
    for fn in ('GetUserCoefficient', 'GetBNBC2020', 'GetBNBC2006', 'GetASCE716', 'GetIBC2006'):
        f = getattr(m.LoadPatterns.AutoSeismic, fn, None)
        if f:
            try:
                r = f(lp)
                if r[-1] == 0: D['load_patterns'][lp][fn] = [str(x) for x in r]
            except Exception:
                pass
print("loads", flush=True)
# area loads by pattern (uniform)
D['area_loads'] = collections.defaultdict(list)
for a in D['areas']:
    r = m.AreaObj.GetLoadUniform(a['name'])
    if r[0] > 0:
        for k in range(r[0]):
            D['area_loads'][r[2][k]].append([a['name'], r[4][k], r[5][k]])
D['frame_dist_loads'] = collections.defaultdict(int)
for f in D['frames']:
    r = m.FrameObj.GetLoadDistributed(f['name'])
    if r[0] > 0:
        for k in range(r[0]): D['frame_dist_loads'][r[2][k]] += 1
print("mass", flush=True)
# mass source, modal, diaphragms
try: D['mass_source'] = [str(x) for x in m.PropMaterial.__class__ and m.SourceMass.GetMassSource(m.SourceMass.GetDefault()[0])]
except Exception as ex: D['mass_source'] = str(ex)
try: D['modal'] = [str(x) for x in m.LoadCases.ModalEigen.GetNumberModes('Modal')]
except Exception as ex: D['modal'] = str(ex)
try: D['diaphragms'] = [str(x) for x in m.Diaphragm.GetNameList()]
except Exception as ex: D['diaphragms'] = str(ex)
D['combos'] = {}
for c in ['1.2D+1.0L+1.0EQx', '0.9D+1.0EQx', '0.9D+1.0EQy', 'DConS1', 'DWalS1']:
    r = m.RespCombo.GetCaseList(c)
    D['combos'][c] = list(zip(r[2], r[3]))
etabs.ApplicationExit(False)
json.dump(D, open(out, 'w'), indent=1, default=str)
print('frames', len(D['frames']), D['frame_prop_count']); print('areas', D['area_prop_count'])
print('supports', len(D['supports'])); print('patterns', D['load_patterns'])
print('area loads', {k: len(v) for k, v in D['area_loads'].items()}, 'frame loads', dict(D['frame_dist_loads']))
print('mass', D['mass_source']); print('modal', D['modal']); print('diaph', D['diaphragms']); print('combos', D['combos'])
print('materials', D['materials']); print('frame secs', D['frame_sections']); print('area secs', D['area_sections'])
