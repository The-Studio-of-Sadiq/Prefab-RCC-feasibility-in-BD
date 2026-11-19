"""Open a copy of the ETABS model through the API and print its basic contents."""
import sys, comtypes.client
path = sys.argv[1]
helper = comtypes.client.CreateObject('ETABSv1.Helper')
import comtypes.gen.ETABSv1 as E
helper = helper.QueryInterface(E.cHelper)
etabs = helper.CreateObjectProgID("CSI.ETABS.API.ETABSObject")
etabs.ApplicationStart()
m = etabs.SapModel
print('open', m.File.OpenFile(path))
m.SetPresentUnits(6)  # kN_m_C
print('version', etabs.SapModel.GetVersion())
print('stories', m.Story.GetStories_2()[:4])
print('frames', m.FrameObj.Count(), 'areas', m.AreaObj.Count(), 'points', m.PointObj.Count(), 'links', m.LinkObj.Count())
print('materials', m.PropMaterial.GetNameList())
print('frame props', m.PropFrame.GetNameList())
print('area props', m.PropArea.GetNameList())
print('load patterns', m.LoadPatterns.GetNameList())
print('load cases', m.LoadCases.GetNameList())
print('combos', m.RespCombo.GetNameList())
print('link props', m.PropLink.GetNameList())
print('mass source', m.SourceMass.GetMassSource('MsSrc1') if hasattr(m,'SourceMass') else '')
etabs.ApplicationExit(False)
