"""Enlarge wall-end (boundary) columns in the lower storeys of a model copy.
usage: fix_boundary_columns.py src.EDB dst.EDB size_mm n_storeys"""
import sys, json, comtypes.client
src, dst, size, nst = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
ENDS = {(0, 5), (0, 10), (20, 5), (20, 10), (5, 0), (10, 0), (10, 15), (15, 15)}   # ends of WY1, WY2, WX1, WX2
helper = comtypes.client.CreateObject('ETABSv1.Helper')
import comtypes.gen.ETABSv1 as E
helper = helper.QueryInterface(E.cHelper)
etabs = helper.CreateObjectProgID("CSI.ETABS.API.ETABSObject")
etabs.ApplicationStart()
log = {}
try:
    m = etabs.SapModel
    m.File.OpenFile(src); m.SetPresentUnits(6); m.SetModelIsLocked(False)
    sec = f'COL_{size}x{size}'
    m.PropFrame.SetRectangle(sec, 'C28_Precast', size / 1000, size / 1000)
    m.PropFrame.SetModifiers(sec, [1, 1, 1, 1, 0.7, 0.7, 1, 1])
    rb = m.PropFrame.GetRebarColumn('COL_500x500')
    log['rebar_src'] = [str(x) for x in rb]
    try:
        m.PropFrame.SetRebarColumn(sec, *rb[:-1])
    except Exception as ex:
        log['rebar_err'] = str(ex)[:120]
    fr = m.FrameObj.GetAllFrames()
    changed = []
    for i, n in enumerate(fr[1]):
        if fr[2][i] != 'COL_500x500': continue
        xy = (round(fr[6][i]), round(fr[7][i]))
        zmax = max(fr[8][i], fr[11][i])
        if xy in ENDS and zmax <= 3.0 * nst + 0.01:
            m.FrameObj.SetSection(n, sec); changed.append(n)
    log['columns_changed'] = len(changed)
    log['save'] = m.File.Save(dst)
finally:
    etabs.ApplicationExit(False)
print(json.dumps(log))
