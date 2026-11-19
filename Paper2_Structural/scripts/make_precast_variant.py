"""Derive a precast variant from the cast-in-situ baseline.
usage: make_precast_variant.py baseline.EDB out.EDB Rk wall_membrane_mod
  Rk  : beam-end rotational spring (kN-m/rad) applied to M3 at both ends of all BEAM_300x500 frames; 'rigid' = no release
  wall_membrane_mod : in-plane (f11,f22,f12) stiffness modifier for all wall shells (bending kept at 0.70)"""
import sys, json, comtypes.client
src, dst, rk, wm = sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4])
helper = comtypes.client.CreateObject('ETABSv1.Helper')
import comtypes.gen.ETABSv1 as E
helper = helper.QueryInterface(E.cHelper)
etabs = helper.CreateObjectProgID("CSI.ETABS.API.ETABSObject")
etabs.ApplicationStart()
log = {}
try:
    m = etabs.SapModel
    m.File.OpenFile(src); m.SetPresentUnits(6); m.SetModelIsLocked(False)
    nb = 0
    if rk != 'rigid':
        k = float(rk)
        for n in m.FrameObj.GetNameList()[1]:
            if m.FrameObj.GetSection(n)[0] == 'BEAM_300x500':
                ii = [False] * 5 + [True]; jj = [False] * 5 + [True]
                sv = [0.0] * 5 + [k]; ev = [0.0] * 5 + [k]
                r = m.FrameObj.SetReleases(n, ii, jj, sv, ev)
                nb += 1
    log['beams_released'] = nb
    nw = 0
    for n in m.AreaObj.GetNameList()[1]:
        if m.AreaObj.GetProperty(n)[0].startswith('WALL'):
            m.AreaObj.SetModifiers(n, [wm, wm, wm, 0.7, 0.7, 0.7, 1.0, 1.0, 1.0, 1.0]); nw += 1
    log['walls_modified'] = nw
    log['save'] = m.File.Save(dst)
finally:
    etabs.ApplicationExit(False)
print(json.dumps(log))
