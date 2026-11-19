# Splitting SSRN 7490639 into two papers

Source: `ssrn-7490639.pdf`, "Techno-Economic Feasibility of Modular Precast Concrete Systems in Bangladesh: A Case Study Based on BNBC 2020" (Sifat, Prince, Islam).
Supporting data: `repo/` (GitHub: The-Studio-of-Sadiq/Prefab-RCC-feasibility-in-BD).

## 1. What the manuscript actually contains

| Claim in the abstract | What the body has |
|---|---|
| "Finite element dynamic structural analysis of a 10-storey building ... resolves the seismic connection performance gap" | **None.** No ETABS model, figure, table or result. Methodology (3.1) says the study is "qualitative desk-based"; 4.8 and 5.9 list seismic connection data as *missing* and needing lab tests. |
| "Cost-benefit analysis grounded in a locally sourced contractor BOQ" | **Not used.** Table 7 starts from a rounded 18,000 BDT/m² baseline and applies literature percentages (-60% labour, -80% formwork). The real BOQ (repo `BOQ/AppendixA...docx`) is never referenced in the text. |
| "GIS-based road network analysis of Dhaka" | **None.** Table 5 is qualitative; 4.8 item 3 lists geospatial mapping as *future* research. The repo has a 3,441-segment OSM layer of Dhaka roads at least 16 ft wide that the text never uses. |
| Benchmarked against India and Malaysia | Present (Sec. 4.5), qualitative. Vietnam is admitted to be undocumented. |

Other problems a reviewer will catch:
- Results 4.0 still says "Grey italic fields indicate data to be completed by the authors."
- Lit-review table rows are mostly off-topic (glass walls, Albanian masonry, Australian shopping centres, facade KBE).
- Literature figures are left without citations (e.g. "26.3% to 72.1% more", "USD 986 billion", "54.7% CO2").
- The market-size figure is wrong: the global precast market is roughly USD 100-150 billion, not "986 billion by 2024".
- Placeholder citations remain in the text: "[previous responses, 6]", "[model history]".
- Limitations section refers to an LCCA / NPV / 50-year schedule and a stakeholder sample that the paper never presents.
- Table 1's "Up to 36 storeys" and Section 4.1's "6.07 kN/m² factored" capacity have no traceable source.
- Compliance matrix rates "Seismic Zone Design Requirements" as **Compliant** with no analysis, then the discussion says connection performance is unvalidated. These contradict each other.
- The paper discusses Dhaka as "Zone 2", which is correct under BNBC 2020 (Z = 0.20).

## 2. Paper 1: Pre-feasibility (regulatory, economic, logistic, institutional)

**RQ:** Under what regulatory, economic, logistical and institutional conditions is precast RCC construction feasible in Bangladesh?
**Target journals:** construction management and economics (e.g. *Engineering, Construction and Architectural Management*; *Construction Management and Economics*; *International Journal of Construction Management*; *Buildings*).

| New section | Comes from | Change |
|---|---|---|
| Introduction, RQ | Intro, RQs 1-9 | Merge 9 RQs into 1 main RQ + 4 sub-RQs (regulatory, material/supply chain, cost/scale, logistics, institutional). Drop RQ3 (storey capacity limits) and its structural framing. |
| Literature review | 2.1, 2.2 BNBC, 2.3 RAJUK, review table | Cut the BNBC and RAJUK summaries by about 70%, keeping only the precast-relevant clauses. Replace the review table with precast-adoption and precast-cost studies. Cite every number. |
| BNBC regulatory analysis | "Comparative analysis" section + 4.1 | **Keep and strengthen.** Ties (Sec. 6.10, 22/44 kN/m), the gravity/friction connection ban (6.10.5.1.4), inspection/test-at-site (3.8.5, 3.8.8), minor-alterations paradox, setbacks/plot geometry. Seismic row becomes "Conditional: requires certified ductile connections", **not** "Compliant". Remove the 36-storey claim and the height-capacity framing. |
| Material compatibility and supply chain | 4.2 | Keep. |
| Workforce, equipment, process | 4.3 | Keep. |
| Cost model | 4.6 | **Rebuild on the real BOQ.** Derive the conventional core-and-shell BDT/m² from repo Appendix A (sections A+B over the building's floor area), then apply clearly labelled literature-derived adjustment factors. Add a sensitivity/tornado analysis on labour, transport and plant cost. Label it a *projection*. |
| Economies of scale | 4.6.3 | Keep. Show the fixed-cost and capacity assumptions explicitly, give the breakeven as a range, and run a sensitivity check. |
| GIS logistics | 4.4 + repo GIS | **Add the real analysis.** Network length by road class and width, corridors at least 16 ft wide, and candidate factory-to-site distances (e.g. Savar/Gazipur to central Dhaka). Rural assessment remains literature-based and labelled as such. |
| Regional comparison | 4.5 | Keep India and Malaysia; drop Vietnam or mark it as insufficient evidence. |
| Feasibility matrix, roadmap, policy | 4.7, 5.x, Table 11 | Keep. |
| Limitations | 4.8, 5.9 | Rewrite to match what is actually in the paper. Remove references to the LCCA/NPV and the stakeholder sample unless they are added. State that structural/seismic validation is the subject of Paper 2. |

**Moves out to Paper 2:** RQ3, the abstract's FEA and seismic claims, Table 1 (structural capacity parameters), and any statement that a specific building satisfies seismic requirements.

## 3. Paper 2: Structural and seismic performance

**RQ:** How does a precast RCC structural system perform under BNBC 2020 design requirements compared with an equivalent conventional cast-in-situ RCC system?
**Target journals:** structural and building engineering (e.g. *Journal of Building Engineering*; *Structures*; *Engineering Structures*; *Buildings*).

There is **no text** in the SSRN paper to carry over. Paper 2 is written from the repo's ETABS data.

| Section | Data available in repo | Status |
|---|---|---|
| Building geometry and system | `ETABS/4.EDB`, `Floorplan/Drawing6.dws`; 10 storeys, P_CORE core + walls W1-W3 | Have the model; geometry needs extracting |
| BNBC seismic and wind parameters | none written | Need: zone, site class (from `Soil Test.../Astha Orchid soil report`), R, I, Cd, Ta, and wind speed |
| Materials and sections | in EDB | Extract |
| Load cases and combinations | EQx, EQy, 1.2D+1.0L+1.0EQ, 0.9D+1.0EQ; construction-stage cases DConS1-26 / DWalS1-18 | Have it. Construction-stage cases are a possible novelty. |
| Modal analysis | Book1: T1 = 1.878 s, UX 18% / UY 6% in mode 1, mode 2 UY 53% | **Red flag:** mode 1 is torsion-dominated. Needs explaining or redesigning. |
| Base shear and period | Bengali-named workbook 2 + Book5 | Have it. Check the Ta cap and scale response-spectrum base shear to the equivalent static value (ELF). |
| Storey drift | workbook 1 + Book4 (e.g. 1/551 at roof under EQx) | Have it. Check against the BNBC limit (0.02 h_sx for this risk category, after Cd amplification). |
| Member forces and D/C | Book3 pier forces, Book6 ACI 318-19 pier design | Have it, **but designed to ACI 318-19, not BNBC 2020.** Justify equivalence or re-check. |
| Connection modelling | workbook 3 "vertical tie force" = wall reactions W1-W3 | Joints appear **monolithic**. Either model them (link/hinge/reduced-stiffness joints) or state this clearly as a limitation. |
| Conventional cast-in-situ comparison | **none** | **Must be built and run.** |
| Sensitivity (joint stiffness, cracked-section factors, soil class) | none | Must be run. |

## 4. Decisions needed from the authors
1. Paper 2's cast-in-situ comparison model must be built and run in ETABS. This needs the authors' licence; no AI can run ETABS.
2. Paper 1: confirm the floor area of the BOQ building so cost per m² can be derived.
3. Whether to withdraw or revise the SSRN version once Paper 1 replaces it, since its abstract claims analyses it does not contain.
