# Prefab-RCC-feasibility-in-BD

Supplementary and supporting materials for research on precast (prefabricated) RCC construction in Bangladesh. The work began as one paper, *Techno-Economic Feasibility of Modular Precast Concrete Systems in Bangladesh: A Case Study Based on BNBC 2020* (SSRN 7490639), and is now split into two manuscripts (see [`docs/SPLIT_PLAN.md`](docs/SPLIT_PLAN.md)):

| | Paper 1: pre-feasibility | Paper 2: structural and seismic performance |
|---|---|---|
| Question | Under what regulatory, economic, logistical and institutional conditions is precast RCC feasible in Bangladesh? | How does a precast RC frame–wall system perform under BNBC 2020 compared with an equivalent cast-in-situ system? |
| Folder | [`Paper1_PreFeasibility/`](Paper1_PreFeasibility) | [`Paper2_Structural/`](Paper2_Structural) |
| Status | Full draft (`Paper1_draft.md` / `.docx`) | Analysis complete; outline (`Paper2_outline.md`), results (`analysis/results_summary.md`) |

## Repository layout
```
BOQ/                    Material payment register (anonymised) of a 10-storey cast-in-situ building, Dhaka
ETABS/                  Original ETABS model (4.EDB) and exported results of the first submission
GIS/                    OSM road network of Dhaka (roads >= 16 ft) and map
Soil Test and foundation/  Sub-soil investigation report (5 boreholes, Bashundhara R/A)
References/             Literature PDFs
docs/SPLIT_PLAN.md      How the original paper was split into Papers 1 and 2
Paper1_PreFeasibility/
  Paper1_draft.md/.docx Manuscript draft
  analysis/             gis_analysis.py, cost_model.py, gfa_model.py (+ results .md/.json, figures), boq_notes.md
  research/             Fact-check and BNBC 2020 clause verification notes
Paper2_Structural/
  Paper2_outline.md     Manuscript outline
  models/               ETABS 22 models: cis_baseline (M0) and precast variants M1–M4, B7, W45, *_fix600
  scripts/              ETABS API (comtypes) scripts: build baseline, precast variants, run, export, design, checks
  analysis/             baseline_review.md, soil_data.md, results_summary.md, figures/, exported tables per variant
  research/             Literature-based precast connection stiffness parameters
BIM/                    Revit 2027 model (.rvt), IFC export, 3D view and the add-in that generates them (see BIM/README.md)
```

## Reproducing the analyses
- **Paper 1** (Python 3 + matplotlib/numpy), run from the repository root:
  `python Paper1_PreFeasibility/analysis/gis_analysis.py`, `python Paper1_PreFeasibility/analysis/cost_model.py`, `python Paper1_PreFeasibility/analysis/gfa_model.py`.
  All cost figures are **projections** based on stated assumptions.
- **Paper 2** needs ETABS 22 (licensed) and `comtypes`. Typical sequence:
  1. `scripts/bnbc_baseline.py ETABS/4.EDB models/cis_baseline.EDB perim4 WALL_200 1.04` builds the BNBC 2020 baseline: four symmetric perimeter walls, site class SD ELF and response spectrum, partitions included in the seismic mass.
  2. `scripts/make_precast_variant.py <baseline> <out> <Rk|rigid> <wall_modifier>` creates a precast variant.
  3. `scripts/etabs_tables.py <model> <outdir>` runs the model and exports tables; `scripts/bnbc_checks.py <outdir>` applies the BNBC checks.
  4. `scripts/member_design.py` + `scripts/design_summary.py` run member checks; `scripts/compare_variants.py` and `scripts/figures.py` produce comparisons and figures.

## Key caveats
- The original `ETABS/4.EDB` used a user seismic coefficient of 0.056, an off-centre open U-core (extreme torsional irregularity) and a seismic mass without partitions. `Paper2_Structural/analysis/baseline_review.md` documents this, and the corrected baseline is `Paper2_Structural/models/cis_baseline.EDB`.
- Site class is SD (N̄30 ≈ 4); S1/S2 cannot be excluded (no plasticity-index tests; loose saturated fill).
- The BOQ register is partial and materials-only; Paper 1 uses it for cost structure only.
