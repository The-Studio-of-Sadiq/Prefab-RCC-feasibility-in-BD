# Substructure: preliminary bored-pile foundation (recommended precast scheme M2 + 600x600 boundary columns)

Script: `scripts/pile_design.py` (reactions exported from ETABS: `reactions_M2_fix600/Joint Reactions.csv`). This is a preliminary, allowable-stress sizing for coordination and for the soil–structure interaction (SSI) study, **not a construction design**.

## Basis
- **Piles:** bored cast-in-situ, **600 mm diameter, 24 m long**, founded in dense fine sand (N 38–145 below about 20 m).
  - Soil report Sec 3.7 gives skin friction of 1,307–1,548 kN (BH-1…5) for this size. The lowest value is taken as the allowable compression **Qa = 1,307 kN**.
  - The report does not state whether the table is ultimate or allowable, and it requires pile load tests. The alternative reading (ultimate, FS = 2.5, Qa = 523 kN) is reported below.
- **Other capacities:** allowable uplift 0.5Qa = 654 kN; allowable lateral load 50 kN per pile (soft clay, screening value).
- **Layout:** pile spacing 1.8 m (3D); cap overhang 0.45 m; caps 1.0–1.2 m deep.
- **Combinations (ASD):** D + L; D + 0.75L ± 0.525E; 0.6D ± 0.7E, with E taken from the ELF cases including ±5% eccentricity. D = dead + finishes + partitions.
- **Lateral load:** base shear is shared by all piles through the ground-floor slab and tie (grade) beams.

## Results (Qa = 1307 kN)
- **Total piles: 70.** Service base shear 0.7V = 2219 kN gives 31.7 kN per pile, within the 50 kN allowed (45 piles would be needed for lateral load alone).
- **Tie beams** between all caps on the grid lines (BNBC seismic interconnection of pile caps): axial force of at least 358 kN (10% of the largest column load). Suggested section 300 x 600 mm.

| Grid | Column D+L (kN) | Piles | Cap L x B x D (m) | Max pile load (kN) | Min pile load (kN) | Governing (min) |
|---|---|---|---|---|---|---|
| A1 | 1474 | 2 | 2.7 x 1.2 x 1.0 | 831 | 336 | S3 0.6D+0.7EQx#1 |
| A2 | 2726 | 5 | 2.7 x 2.7 x 1.2 | 1169 | -476 | S3 0.6D+0.7EQy#2 |
| A3 | 2816 | 5 | 2.7 x 2.7 x 1.2 | 1184 | -473 | S3 0.6D-0.7EQy#2 |
| A4 | 1586 | 2 | 2.7 x 1.2 x 1.0 | 863 | 352 | S3 0.6D-0.7EQy#2 |
| B1 | 2761 | 5 | 2.7 x 2.7 x 1.2 | 1169 | -463 | S3 0.6D+0.7EQx#2 |
| B2 | 2637 | 3 | 2.7 x 2.46 x 1.0 | 936 | 439 | S3 0.6D+0.7EQx#1 |
| B3 | 2574 | 3 | 2.7 x 2.46 x 1.0 | 917 | 405 | S3 0.6D-0.7EQy#2 |
| B4 | 2350 | 2 | 2.7 x 1.2 x 1.0 | 1215 | 567 | S3 0.6D-0.7EQy#2 |
| C1 | 2876 | 5 | 2.7 x 2.7 x 1.2 | 1194 | -447 | S3 0.6D-0.7EQx#2 |
| C2 | 2915 | 3 | 2.7 x 2.46 x 1.0 | 1028 | 492 | S3 0.6D-0.7EQx#2 |
| C3 | 2646 | 3 | 2.7 x 2.46 x 1.0 | 940 | 442 | S3 0.6D+0.7EQx#1 |
| C4 | 2768 | 5 | 2.7 x 2.7 x 1.2 | 1171 | -460 | S3 0.6D+0.7EQx#1 |
| D1 | 2419 | 2 | 2.7 x 1.2 x 1.0 | 1250 | 610 | S3 0.6D+0.7EQy#1 |
| D2 | 3549 | 3 | 2.7 x 2.46 x 1.0 | 1237 | 599 | S3 0.6D+0.7EQy#1 |
| D3 | 3584 | 3 | 2.7 x 2.46 x 1.0 | 1248 | 599 | S3 0.6D-0.7EQy#1 |
| D4 | 2928 | 5 | 2.7 x 2.7 x 1.2 | 1203 | -442 | S3 0.6D-0.7EQx#1 |
| E1 | 1614 | 2 | 2.7 x 1.2 x 1.0 | 888 | 383 | S3 0.6D+0.7EQy#1 |
| E2 | 2907 | 5 | 2.7 x 2.7 x 1.2 | 1237 | -495 | S3 0.6D+0.7EQy#1 |
| E3 | 2935 | 5 | 2.7 x 2.7 x 1.2 | 1243 | -492 | S3 0.6D-0.7EQy#1 |
| E4 | 1827 | 2 | 2.7 x 1.2 x 1.0 | 1007 | 441 | S3 0.6D-0.7EQx#2 |

**Findings**
1. **Wall-end caps.** The 8 caps under the wall-end (boundary) columns (A2, A3, B1, C1, C4, D4, E2, E3) need **5 piles**. Under 0.6D ± 0.7E their piles go into **tension of about 440–500 kN**.
   - These are the same members whose demand rose with precast joint flexibility (Paper 2, Sec 5.5).
   - The precast column-to-cap connection must therefore transfer uplift: a grouted-sleeve or pocket connection with tension ties, consistent with BNBC 6.10.5.1.3(a) (column tie strength ≥ 1.4Ag).
   - The piles need full-length tension reinforcement.
2. **Other columns:** 2 piles (corner and edge) or 3 piles (interior); all in compression.
3. **Cast-in-situ vs precast:** foundation demands are practically the same (cast-in-situ: 70 piles, max D+L 3590 kN). The foundation does not distinguish the two systems; the precast-specific item is the column-to-cap connection.
4. **If the tabulated capacity is ultimate** (Qa = 523 kN), the wall-end caps would need more than 9 piles each. A piled raft or longer and larger piles would then be the realistic option, so **pile load tests are essential**, as the soil report itself requires.
5. **Not covered:** liquefaction of the upper ~6.7 m of fill (it would cause loss of lateral support and downdrag), negative skin friction, settlement analysis of the pile groups, and structural design of caps and piles.