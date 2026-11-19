# ETABS analysis 1: cast-in-situ RC building (reference)

**Model:** `../../models/1_CastInSitu/cis_baseline.EDB` (ETABS 22)
- Monolithic RC frame with special RC shear walls.
- Four 5 m x 200 mm perimeter walls, point-symmetric about the plan centre; 500x500 columns; 300x500 beams; 150 mm slabs; C28.
- 10 storeys at 3 m; plan 20 m x 15 m.

**Loads (BNBC 2020):**
- Site Zone 2 (Z = 0.20), site class SD, SDC D; R = 6, Cd = 5, I = 1.
- ELF: C = 0.0685 at T = 1.4Ta = 0.876 s; k = 1.19; ±5% eccentricity. Seismic weight 44,431 kN (partitions included), so V = 3,044 kN.
- RSA uses the BNBC SD design spectrum (CQC/SRSS, 5% eccentricity). Its forces are scaled to 85% of V_ELF.
- Strength combinations from BNBC 2.7.3.

| Result | Value | Limit / note |
|---|---|---|
| Periods | Ty 1.27 s (mode 1), Tx 1.27 s (mode 2), torsion 0.90 s (mode 3) | translational modes first |
| Mass participation (30 modes) | > 99% | ≥ 90% |
| Torsion ratio δmax/δavg | 1.04 (X), 1.10 (Y) | < 1.2: regular |
| Max design drift Cd·δ/I | 1.23% (X), 1.31% (Y) | 2.0% |
| P-Δ stability θ | ≤ 0.03 | ≤ 0.10 |
| V_RS / V_ELF | 0.52 | scale RS forces ×1.63 |
| Walls' share of base shear | 91% | building frame system |
| Columns | max ρ 3.6%, none overstressed | ACI 318-19 frame design (BNBC Part 6 proxy) |
| Beams / joints | ρ ≤ 0.53%; joint shear D/C ≤ 0.52 | |
| Walls | shear D/C 0.58; ρl ≈ 1.4%; special boundary elements storeys 1–6 | hand checks |

`tables_original_4EDB/` contains results of the **original** submission model (`ETABS/4.EDB`): C = 0.056, off-centre U-core, partitions excluded from the mass. It is kept for comparison; see `../baseline_review.md`.
