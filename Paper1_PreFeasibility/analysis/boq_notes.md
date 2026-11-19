# BOQ audit: repo `BOQ/AppendixA_BOQ_precast_RCC (2).docx`

Source: an anonymised building owner's handwritten material payment register for a 10-storey cast-in-situ residential building in Dhaka (Dec 2024 – May 2026), shared by personal communication. Checked by Claude on 2026-11-19.

## What it is
- **Materials only.** It contains no labour, equipment hire, transport, overhead or profit.
- **Partial.** Rebar entries run from the basement to the 5th-floor slab, and ready-mix concrete (RMC) entries from the ground-floor slab to the 4th-floor slab. Several items are "~" running totals because pages were missing.
- No gross floor area is stated. The ETABS model in the repo is 20 m x 15 m on plan, with 10 storeys at 3 m (about 300 m² per floor, about 3,000 m² GFA). It is **not confirmed** that the BOQ building is the same building, since the BOQ building has a basement and a retaining wall.

## Recomputed totals (BDT)
| Section | Items as listed | Sum of items | Subtotal stated in the doc |
|---|---|---|---|
| A. Structural core and shell | cement 5,40,000; rebar 41,65,950; stone chips 3,00,000; Sylhet sand 3,88,450; local sand 1,34,000; bricks 10,00,000; RMC 80,00,000 | **1,45,28,400** (14.53 M) | "~1,00,00,000+" (10 M) |
| B. Formwork, scaffolding, shuttering | steel shuttering 1,25,00,000; mango wood 1,30,100 | **1,26,30,100** (12.63 M) | 1,26,30,100 ✔ |
| C. Finishing and MEP (excluded) | 2,26,408 + 27,850 + 1,34,000 + 76,640 + 3,27,140 | **7,92,038** | 6,66,038 |
| Stated grand total | | A(10 M) + B + C(0.67 M) ≈ 2.33 crore | "2,33,00,000+" |

## Inconsistencies to fix or disclose
1. Subtotal A (10 M) is lower than its own items (14.53 M), and the grand total uses the lower figure.
2. Subtotal C does not match its items (a 1,26,000 gap). Local sand (1,34,000) is listed in both A5 and C12, so it is double-counted.
3. In the RMC note, "1,500 cft @ ৳350 = ৳18,12,500" is wrong: 1,500 x 350 = 5,25,000. The bank payment probably covered more than one pour.
4. Steel shuttering (12.5 M) is a **reusable capital purchase**. It is not a consumable cost per m² of this building, so the share attributable to one project depends on how many reuses are assumed.

## What Paper 1 can legitimately say
- It can use the register as **cost-structure evidence for a real Dhaka project**:
  - formwork and shuttering ≈ **46%** of recorded structural material spend (12.63 / (14.53 + 12.63));
  - RMC ≈ 55% of section A, and rebar ≈ 29%.
  - These are partial-register shares, not a full-cost breakdown.
- Formwork is clearly a major cost centre. This supports, qualitatively, the precast argument that formwork is eliminated. The size of the saving depends on how many times shuttering is reused, so it should be tested in the sensitivity analysis.
- It **cannot** give a defensible BDT/m² baseline until the GFA and the floors covered are confirmed. The 18,000 BDT/m² "core and shell" baseline in the SSRN version is an **assumption**, and the draft must label it as one.
