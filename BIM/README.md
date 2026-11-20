# BIM model: 10-storey precast RC reference building (Revit 2027)

![3D view](Prefab_RCC_10storey_3D.png)

A simple structural BIM model of the Paper 2 reference building in its recommended precast scheme: **M2 with 600x600 boundary columns in storeys 1–3** (see `../Paper2_Structural/analysis/results_summary.md`). The model was generated automatically through the Revit API, so it can be regenerated identically.

| File | Content |
|---|---|
| `Prefab_RCC_10storey.rvt` | Revit 2027 project |
| `Prefab_RCC_10storey.ifc` | IFC4 Reference View export (open BIM, readable without Revit) |
| `Prefab_RCC_10storey_3D.png` | Isometric 3D view |
| `Prefab_RCC_10storey_foundations_3D.png` | 3D view including the pile foundation |
| `Prefab_RCC_10storey_MEP.rvt` | MEP model (Revit 2027, Systems template), linking the structural model |
| `Prefab_RCC_10storey_MEP.ifc` | IFC4 export of the MEP elements |
| `Prefab_RCC_10storey_MEP_3D.png` | 3D view of the MEP model with the linked structure |
| `build_log.txt`, `build_log_mep.txt`, `build_log_sub.txt` | Logs of the last automated builds |
| `addin/` | C# source of the Revit add-in that builds the model (`App.cs`, `PrefabBIM.csproj`, `PrefabBIM.addin`) |
| `task.txt` | Original note on a future SAPFire → Revit pile-foundation model (not yet done) |

## What is modelled
| Element | Revit family / type | Count | Mark pattern |
|---|---|---|---|
| Levels | Base (0.000) + Level 1–10 at 3.0 m spacing | 11 | — |
| Grids | A–E (x = 0…20 m at 5 m), 1–4 (y = 0…15 m at 5 m) | 9 | — |
| Columns | M_Concrete-Rectangular-Column: **C 500x500**; **C 600x600** at the 8 wall-end positions, storeys 1–3 | 200 | `PC-C-<grid>-S<n>` |
| Beams | M_Concrete-Rectangular Beam: **B 300x500**, on every grid line at every level | 310 | `PC-B-L<n>-<k>` |
| Walls | **PC Wall 200** (single 200 mm concrete layer), one precast panel per storey: WY1 (x=0, y 5–10), WY2 (x=20, y 5–10), WX1 (y=0, x 5–10), WX2 (y=15, x 10–15) | 40 | `PC-W-<wall>-S<n>` |
| Floors | **PC Slab 150** (single 150 mm concrete layer), 20 m x 15 m | 10 | `PC-S-L<n>` |
| Material | Concrete C28 (precast) | — | — |

Every element carries the Comment "Precast element; Paper 2 scheme M2 + 600x600 boundary columns S1-S3". The IFC contains the same counts (200 IfcColumn, 310 IfcBeam, 40 IfcWall, 10 IfcSlab, 11 storeys).

## Substructure (pile foundation)
Added to the structural model by `PREFAB_BIM_JOB=sub`. Sizes come from `../Paper2_Structural/analysis/substructure_summary.md` (scheme M2 + 600x600 boundary columns, Qa = 1,307 kN).
- **20 pile caps** (family M_Footing-Rectangular, types `PC-CAP …`; top of cap at ±0.000):
  - 2.7 x 1.2 x 1.0 m (2 piles, corner/edge);
  - 2.7 x 2.46 x 1.0 m (3 piles, interior);
  - 2.7 x 2.7 x 1.2 m (5 piles, the 8 wall-end columns).
- **70 bored piles,** 600 mm x 24 m, modelled as DirectShape solids.
- **31 grade (tie) beams,** 300x600, on every grid line (BNBC seismic interconnection of pile caps).
- Marks: `SUB-CAP-<grid>`, `SUB-PILE-<grid>-<k>`, `SUB-GB-<k>`.
- **IFC note:** Revit's default IFC category mapping exports the caps and piles as IfcSlab. They remain identifiable by Name, Mark and family. Remap them in the IFC export settings if IfcFooting/IfcPile classes are required.

## MEP model (simple coordination model)
`Prefab_RCC_10storey_MEP.rvt` links the structural model origin-to-origin and contains 65 elements (33 pipes, 11 ducts, 21 cable trays). There are no fittings or sizing calculations.
- **Service shaft:** x 11.0–13.0 m, y 6.0–7.5 m, in the central bay. It is cut through all 10 precast slabs in the structural model, carrying the comment *"MEP service shaft; must be formed (cast-in) in precast slabs before casting"*.
- **Risers in the shaft, full height:**
  - DN50 domestic cold water;
  - DN100 sanitary stack;
  - DN100 rainwater/vent stack;
  - 400x250 exhaust-air duct;
  - 300x100 cable tray.
- **Per floor,** in the ceiling void 0.65 m below each slab:
  - two DN25 cold-water branches;
  - one DN100 sanitary branch;
  - one 200x150 exhaust branch;
  - two 200x50 cable-tray runs.
- Purpose: to show where services cross the precast structure (one shaft, with horizontal runs under the beams). Openings and sleeves in precast elements must be fixed at design freeze, before casting.

**Not modelled (structure):** stairs and lift, partitions and finishes, reinforcement, and connection hardware.

## Regenerating
Requires Revit 2027 and the .NET 8 SDK.
```
cd BIM/addin
dotnet build -c Release
copy PrefabBIM.addin "%APPDATA%\Autodesk\Revit\Addins\2027\"
set PREFAB_BIM_JOB=1      (structural model)  or  set PREFAB_BIM_JOB=mep  (shaft opening + MEP model)  or  set PREFAB_BIM_JOB=sub  (pile foundation)
"C:\Program Files\Autodesk\Revit 2027\Revit.exe" /language ENU
```
The add-in does nothing unless `PREFAB_BIM_JOB=1` is set. With it set, the add-in builds the model from the *Structural Analysis-DefaultMetric* template, saves the RVT, exports the IFC and PNG, and closes Revit. Adjust the absolute paths in `App.cs` and `PrefabBIM.addin` to your checkout, and remove the manifest from the Addins folder afterwards.
