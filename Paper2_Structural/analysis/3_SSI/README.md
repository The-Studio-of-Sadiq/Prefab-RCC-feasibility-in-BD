# ETABS analysis 3: soil–structure interaction (pile-spring sensitivity)

The fixed supports are replaced by linear pile-group springs at the 20 column bases (`scripts/add_pile_springs.py`), and 300x600 grade beams are added on every grid line at the base.
- **Pile layout:** from `substructure_summary.md` (600 mm x 24 m bored piles; 70 piles).
- **Vertical spring per pile:** Qa / s, with Qa = 1,307 kN and s = 5 / 10 / 20 mm for the stiff / central / soft cases. For scale, the elastic shortening of a 24 m pile, EA/L, gives about 353,000 kN/m, which corresponds to s ≈ 3.7 mm.
- **Lateral spring per pile:** 10,000 / 5,000 / 2,500 kN/m.
- **Cap rocking stiffness:** Σ kv·d² over the piles of each cap.
- **Loads:** the same BNBC ELF loads as the fixed-base models (T capped at 1.4Ta, so V is unchanged).
- **Drift metric:** BNBC Sec 2.5.7.7, the design storey drift Cd·δ/I at the centre of mass (rigid diaphragm average of the extreme points), excluding the rigid translation of the base.

| Model | Ty (s) | BNBC drift X / Y (%) at centre of mass | Max-point drift Y (%) | Base translation Cd·δ (mm) | Walls' share of V (Y) | Torsion ratio (Y) | Check (≤ 2.0%) |
|---|---|---|---|---|---|---|---|
| M0 cast-in-situ, fixed base | 1.27 | 1.18 / 1.20 | 1.31 | 0 | 91% | 1.10 | OK |
| M0, pile springs (stiff) | 1.66 | 1.60 / 1.64 | 1.79 | 22.3 | 70% | 1.18 | OK |
| M0, pile springs (central) | 1.92 | 1.92 / 1.97 | 2.16 | 43.9 | 57% | 1.18 | OK |
| M0, pile springs (soft) | 2.28 | 2.37 / 2.48 | 2.72 | 87.3 | 42% | 1.18 | **exceeds** |
| M2 + 600x600 precast, fixed base | 1.26 | 1.15 / 1.17 | 1.28 | 0 | 83% | 1.10 | OK |
| M2 + 600x600 precast, pile springs (central) | 1.89 | 1.85 / 1.91 | 2.09 | 44.0 | 48% | 1.18 | OK |

**Findings**
1. **Foundation flexibility is first-order on this site.** With realistic pile springs the period lengthens from 1.27 s to 1.66–2.28 s, and the BNBC drift rises from 1.20% to 1.64% (stiff), **1.97% (central, at the limit)** and **2.48% (soft, exceeds)**. That is larger than the effect of any precast connection variant (fixed base, up to 1.69%).
2. **The mechanism is rocking of the wall pile caps.** The walls' share of base shear falls from about 91% to 42–70% as the wall bases rotate on the piles and the frame picks up the load.
3. **The recommended precast scheme behaves like the cast-in-situ building on piles** (1.91% vs 1.97%, central springs). Connection type matters less than foundation stiffness once SSI is included.
4. **Design implication:** for frame–wall buildings on Dhaka soft-soil sites, the wall foundations need rotational stiffness, for example more or longer piles under wall caps, a combined cap or piled raft under each wall, or longer walls. Without it, the BNBC drift limit can be exceeded regardless of construction method.
5. **Caveats:**
   - The springs are screening values derived from the soil report capacities and assumed settlements. They are not calibrated by load tests or by a group-settlement analysis.
   - Liquefaction of the upper fill, kinematic interaction and radiation damping are not modelled.
   - The ELF period cap means the forces are not reduced to reflect the longer period. BNBC 2.5.7.7 provides no period relaxation for drift.