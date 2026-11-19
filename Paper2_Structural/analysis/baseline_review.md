# Paper 2: review of the existing ETABS model against BNBC 2020

Model: `repo/ETABS/4.EDB` (ETABS 22.5). A copy was opened and run through the ETABS API on 2026-11-19. Scripts are in `paper2/scripts/`, exported tables in `paper2/analysis/tables_base/`. The run **reproduces the repository workbooks** (T1 = 1.878 s; V = 1,624.6 kN).

## What the model is
- 10 storeys at 3 m (h = 30 m), plan 20 m x 15 m.
- 20 columns of 500x500 per storey; beams 300x500; 150 mm slabs; three 200 mm walls (W1–W3) grouped as pier P_CORE. Material C28 (f'c 28 MPa).
- Cracked-section modifiers: 0.70 for columns and walls, 0.35 for beams, 0.25 for slab bending.
- Fixed base (20 supports) and one rigid diaphragm per floor.
- **No link elements and no frame end releases: every joint is monolithic.** In effect this is a **cast-in-situ** model with a "precast" material name. Precast connections are **not modelled**.
- Seismic load is a **user coefficient C = 0.056** with k = 1 and 5% eccentricity, applied to W = 29,010 kN, giving V = 1,624.6 kN. There is no BNBC auto-seismic definition and the response spectrum function is a placeholder ("UnifRS" = 1.0). The mass source is self-weight + FF + PW + 0.25 Live (consistent with BNBC 2.5.7.3).
- The "DConS*/DWalS*" combinations are ETABS's auto-generated concrete-frame and shear-wall **design** combinations, not construction stages. The seismic combinations are ASCE-style (1.2D+1.0L+1.0E, 0.9D+1.0E).
- The wall design in the workbooks used **ACI 318-19**, not BNBC 2020.

## BNBC 2020 parameters for this site (verified against the gazette text)
| Item | Value | Source |
|---|---|---|
| Zone, Z | 2, 0.20 (Dhaka) | Tables 6.2.14 and 6.2.15 |
| Site class | **SD** (N̄30 = 3.5–4.7 over 5 boreholes); S1/S2 not excluded (no PI tests; ~6.7 m saturated loose fill, GWL 0 m) | Table 6.2.13; `soil_data.md` |
| Spectrum, SD | S = 1.35, TB = 0.20 s, TC = 0.80 s, TD = 2.0 s | Table 6.2.16 |
| Occupancy / I | II (residential) / 1.0 | Table 6.2.17 |
| SDC | **D** (SD, Zone 2, Occupancy II) | Table 6.2.18 |
| System | Building frame with **special** RC shear walls: R = 6, Ω = 2.5, Cd = 5, height limit 50 m in SDC D (ordinary RC walls: **not permitted** in SDC D) | Table 6.2.19 |
| Ta | 0.0488 · 30^0.75 = **0.626 s** ("all other systems") | Table 6.2.20 |
| Cs at Ta | 2.5 · S = 3.375 (plateau) | Sec 2.5.4.3 |
| Sa = (2/3)(ZI/R)Cs | **0.075** (R = 6), so V ≈ 0.075 x 29,010 ≈ **2,176 kN** | |
| Drift limit | 0.020 h (Occupancy II, "all other structures") | Table 6.2.21 |

## Findings
1. **Base shear is about 25% below BNBC.** The model uses C = 0.056; BNBC SD with R = 6 gives about 0.075. C = 0.056 would correspond to R ≈ 8 or a stiffer site class.
2. **Extreme torsional irregularity.** δmax/δavg = 1.67–1.86 under EQx and 1.75–2.47 under EQy, against BNBC's thresholds of 1.2 (irregular) and 1.4 (extreme). Mode 1 (T = 1.878 s) is predominantly torsional (RZ = 0.49; UX = 0.18, UY = 0.06). The three walls are clustered off-centre, so the stiffness centre is far from the centre of mass (≈ 10.1, 7.5 m). Consequences under BNBC: Ax = (δmax/1.2δavg)² up to the 3.0 cap on the 5% accidental eccentricity, and dynamic (response-spectrum) analysis should govern.
3. **The period is long relative to Ta.** T1 = 1.88 s is 3 x Ta, which shows the lateral system is very flexible. Equivalent static analysis remains permitted by the period rule (T < 4TC = 3.2 s and < 2 s, just), but not when the torsion is this severe.
4. **Drift appears acceptable even so.** The maximum elastic drift is 0.0027 (EQx, Story 5). Scaled to the BNBC base shear and multiplied by Cd = 5, it is about 0.018 against the 0.020 limit, with a small margin before torsional amplification. To be rechecked with a response-spectrum analysis.
5. **Connections are not modelled**, so the model cannot yet support any statement about precast behaviour.

## Consequence for Paper 2
A precast vs cast-in-situ comparison built on this layout would compare two systems that **both fail** BNBC's regularity and base-shear requirements. Reviewers would reject that. The baseline needs to be made code-consistent first.

---
## Redesigned cast-in-situ baseline (`paper2/model/cis_baseline.EDB`), 2026-11-19
Built from a copy of the original model by `scripts/bnbc_baseline.py` (layout `perim4`, WALL_200, analysed T = 1.04 s). Columns, beams, slabs, loads, mass source and cracked-section modifiers are unchanged.
- **Wall layout:** the off-centre open U-core (W1–W3, 15 m of wall) is replaced by four 5 m, 200 mm walls on the perimeter, point-symmetric about the plan centre (10, 7.5):
  - WY1 at x = 0, y = 5–10; WY2 at x = 20, y = 5–10;
  - WX1 at y = 0, x = 5–10; WX2 at y = 15, x = 10–15.
  - Total wall length 20 m.
- **ELF:** C = Sa(T_use) = 0.0685, with T_use = min(T, 1.4·Ta) = 0.876 s; k = 1.19; ±5% eccentricity, giving V = 2,034 kN (W ≈ 29,680 kN).
- **RSA:** BNBC 2020 site-class SD design spectrum (R = 6, I = 1) entered as the user function `BNBC20_SD`; cases RSx/RSy with CQC, SRSS and 5% eccentricity, 30 modes.

| Check | Result | Limit | Status |
|---|---|---|---|
| Fundamental periods | Ty = 1.04 s (mode 1), Tx = 1.03 s (mode 2), torsion 0.71 s (mode 3) | translational modes first | ✔ |
| Mass participation (30 modes) | 99.8% X / 99.6% Y | ≥ 90% | ✔ |
| Torsion δmax/δavg | 1.04 (EQx), 1.08 (EQy) | < 1.2 | ✔ regular, Ax = 1.0 |
| V_RS / V_ELF | 1,251 / 2,034 kN (X); 1,243 / 2,034 kN (Y) | ≥ 0.85 | scale RS **forces** ×1.38 / ×1.39 |
| Design drift Cd·δ/I (ELF) | 0.0083 (X), 0.0087 (Y) | 0.020 h | ✔ |
| Design drift (RSA) | 0.0051 (X), 0.0053 (Y) | 0.020 h | ✔ |

**Still to check before the baseline is final:** P-delta stability coefficient θ; wall and column demand/capacity under BNBC 2020 Part 6 Ch 6 (special-wall boundary elements); vertical irregularity (soft storey / mass) checks; gravity column deformation compatibility.
