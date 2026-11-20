# ETABS analysis 2: precast (prefabricated) RC building

Every precast model is derived from the cast-in-situ reference (`1_CastInSitu`) by `scripts/make_precast_variant.py`, with the same geometry, loads and BNBC 2020 parameters. The precast connections are represented by:
- **beam–column joints:** a rotational spring Rk at both ends of every beam (ETABS partial fixity, M3);
- **wall horizontal (bed) joints:** reduced in-plane membrane stiffness of the wall panels (f11, f22, f12).

Stiffness values come from the literature (`../../research/connection_parameters.md`).

| Model | Beam-end Rk (kN·m/rad) | Wall membrane modifier | Represents |
|---|---|---|---|
| pc_M1 | rigid | 0.65 | emulative (wet) precast |
| pc_M2 | 30,000 (γ ≈ 0.65) | 0.56 | semi-rigid, central |
| pc_M3 | 16,321 (γ = 0.50) | 0.45 | semi-rigid, lower bound |
| pc_M4 | 7,000 (γ ≈ 0.30) | 0.50 | dry mechanical connections |
| pc_B7 | 7,000 | 0.70 | beam joints only (one-factor) |
| pc_W45 | rigid | 0.45 | wall joints only (one-factor) |
| pc_M2_fix600, pc_M4_fix600 | as M2 / M4 | as M2 / M4 | plus 600x600 wall-end columns, storeys 1–3 (recommended precast scheme) |

| Model | Ty (s) | Drift Y (%) | Max column ρ | Column O/S |
|---|---|---|---|---|
| M1 | 1.35 | 1.44 | — | — |
| M2 | 1.36 | 1.44 | 5.4% | 0 |
| M3 | 1.46 | 1.65 | — | — |
| M4 | 1.52 | 1.84 | 7.1% | 24 |
| B7 | 1.45 | 1.72 | 6.0% | 0 |
| W45 | 1.41 | 1.53 | 6.2% | 5 |
| **M2 + fix600** | 1.26 | **1.28** | **2.8%** | **0** |
| **M4 + fix600** | 1.39 | **1.60** | **3.9%** | **0** |

The cast-in-situ reference (M0) gives a drift of 1.31% with maximum column ρ of 3.6%. Full tables are in `../results_summary.md`.
