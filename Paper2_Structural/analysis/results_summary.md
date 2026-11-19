# Paper 2: variant results (linear, BNBC 2020 site class SD, SDC D, R = 6)

All variants use the same ELF loads (V = 3,044 kN, C = 0.0685, T capped at 1.4Ta = 0.876 s) and BNBC strength combinations.
Drift = Cd·δmax/I (ELF, including ±5% eccentricity). The limit is 2.0%.

| Variant | Beam-end spring Rk (kN·m/rad) | Wall membrane modifier | Description | Tx / Ty (s) | Drift X / Y (%) | Margin to limit (Y) | V_RS/V_ELF | Wall share of V (Y) | Torsion ratio (Y) |
|---|---|---|---|---|---|---|---|---|---|
| M0 | rigid | 0.70 | Cast-in-situ baseline | 1.27 / 1.27 | 1.23 / 1.31 | 34% | 0.52 | 91% | 1.09 |
| M1 | rigid | 0.65 | Emulative precast | 1.34 / 1.35 | 1.35 / 1.44 | 28% | 0.50 | 88% | 1.10 |
| M2 | 30,000 (γ≈0.65) | 0.56 | Semi-rigid, central | 1.35 / 1.36 | 1.34 / 1.44 | 28% | 0.50 | 87% | 1.10 |
| M3 | 16,321 (γ=0.50) | 0.45 | Semi-rigid, low | 1.45 / 1.46 | 1.55 / 1.65 | 18% | 0.47 | 85% | 1.10 |
| M4 | 7,000 (γ≈0.30) | 0.50 | Dry mechanical | 1.51 / 1.52 | 1.74 / 1.84 | 8% | 0.46 | 87% | 1.09 |
| B7 | 7,000 (γ≈0.30) | 0.70 | Beam joints only | 1.45 / 1.45 | 1.62 / 1.72 | 14% | 0.47 | 90% | 1.09 |
| W45 | rigid | 0.45 | Wall joints only | 1.40 / 1.41 | 1.44 / 1.53 | 23% | 0.49 | 85% | 1.10 |

## Member checks (ETABS ACI 318-19 frame design as a proxy for BNBC Part 6; hand checks for the walls)

| Variant | Max column ρ (stations >4%) | Column O/S | Max beam ρ | Joint shear D/C | Wall shear D/C | Wall ρl required | Special boundary elements | Peak wall edge stress (MPa) |
|---|---|---|---|---|---|---|---|---|
| M0 | 3.6% (0) | 0 | 0.53% | 0.52 | 0.58 | 1.40% | Story1–Story6 | -13.0 |
| M2 | 5.4% (24) | 0 | 0.58% | 0.55 | 0.57 | 0.95% | Story1–Story5 | -9.0 |
| M4 | 7.1% (48) | 24 | 0.54% | 0.42 | 0.59 | 1.00% | Story1–Story5 | -9.3 |
| B7 | 6.0% (30) | 0 | 0.54% | 0.42 | 0.59 | 1.25% | Story1–Story6 | -11.5 |
| W45 | 6.2% (30) | 5 | 0.54% | 0.53 | 0.56 | 0.80% | Story1–Story5 | -7.9 |

## Key findings
1. **Global response stays within BNBC limits in every variant.** Drift rises from 1.31% (M0) to 1.84% (M4, +40%); the margin to the 2.0% limit falls from 34% to 8%. Periods lengthen by 6–19%.
2. **Beam-joint flexibility matters more than wall-joint flexibility for drift.** Beam joints only (B7): 1.72%. Wall joints only (W45): 1.54%. Their effects are roughly additive (M4: 1.84%).
3. **Torsional regularity is unaffected** (ratio 1.09–1.10): the symmetric layout is robust to connection flexibility.
4. **The walls carry 85–91% of the base shear in every variant**, consistent with a building frame system.
5. **Critical precast consequence: the wall-end (boundary) columns in storeys 1–2.**
   - Required longitudinal steel rises from 3.6% (M0) to 5.4% (M2) and 7.1% (M4).
   - M4 exceeds ACI's 6% maximum, with 24 overstressed column stations (5 in W45).
   - Flexible wall bed joints shift overturning axial force into the stiffer boundary columns, and flexible beam joints reduce frame coupling.
   - Precast schemes therefore need stronger or integral boundary columns at the lower storeys.
6. **Wall demands are similar across variants** (shear D/C 0.57–0.59; special boundary elements in storeys 1–5/6).
   - Elastic edge tension of 8–13 MPa is far above BNBC's 44 kN/m minimum vertical tie (6.10.5.2.5).
   - Vertical continuity at precast horizontal joints must therefore carry the full flexural reinforcement (ACI 318-19 18.11 / Type 2 splices), not just minimum ties.
7. **The strong-column/weak-beam check fails at 8 joints in M0 and M2.** It is not mandatory here because the frame is not part of the seismic-force-resisting system (building frame system), but the gravity frame must meet the deformation-compatibility requirements (ACI 18.14) at the larger precast drifts.

Limitations: linear analysis; connection stiffness from literature ranges (central values unverified against the original test reports); fixed base on SD soil (S1/S2 not excluded); ACI 318-19 used as a proxy for BNBC concrete design.
## Remedial check: enlarged wall-end (boundary) columns
The 8 columns at the wall ends were enlarged from 500x500 to **600x600 in storeys 1–3** (24 members; same material, 0.70 cracked modifier, same rebar pattern) by `scripts/fix_boundary_columns.py`. The models were then re-run under the same BNBC loads and checked.

| Variant | Drift X / Y (%) | Margin (Y) | Max column ρ | Column O/S | Wall shear D/C | Wall ρl required | Wall share of V (Y) |
|---|---|---|---|---|---|---|---|
| M0 cast-in-situ (500x500) | 1.23 / 1.31 | 34% | 3.6% | 0 | 0.58 | 1.40% | 91% |
| M2 semi-rigid (500x500) | 1.34 / 1.44 | 28% | 5.4% | 0 | 0.57 | 0.95% | 87% |
| **M2 + 600x600 boundary columns** | **1.19 / 1.28** | **36%** | **2.8%** | **0** | 0.56 | 0.75% | 83% |
| M4 dry (500x500) | 1.74 / 1.84 | 8% | 7.1% | 24 | 0.59 | 1.00% | 87% |
| **M4 + 600x600 boundary columns** | **1.51 / 1.60** | **20%** | **3.9%** | **0** | 0.58 | 0.80% | 83% |

**Interpretation**
- A modest local change restores BNBC/ACI compliance in every precast variant: 600x600 wall-end columns over the lowest three storeys (about 7.9 m³ of extra concrete in total: 24 columns × 3 m × 0.11 m²).
  - Column steel falls back below the practical 4% limit, and no member is overstressed.
  - The 500x500 columns above the size change (storey 4) need at most 2.4% steel.
- The larger boundary columns also stiffen the system: drift falls by 11–13%. The central precast variant (M2) then performs **at least as well as the cast-in-situ baseline** (1.28% vs 1.31%), and the dry-connection case keeps a 20% drift margin.
- Design implication for precast schemes in BNBC SDC D: **size the wall boundary columns, or integral boundary elements, for the redistribution of overturning that flexible joints cause.** Do not carry over cast-in-situ column sizes.
