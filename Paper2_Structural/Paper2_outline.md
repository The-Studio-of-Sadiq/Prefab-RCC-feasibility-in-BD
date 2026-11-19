# Paper 2: working outline (structural and seismic performance)

**Working title:** Seismic performance of a precast RC frame–wall residential building under BNBC 2020: influence of connection stiffness relative to an equivalent cast-in-situ system

**Research question:** How does a precast RCC structural system perform under BNBC 2020 design requirements compared with an equivalent conventional cast-in-situ RC system, and how sensitive is that performance to the stiffness of its precast connections?

**Target journals:** *Journal of Building Engineering*; *Structures*; *Buildings*; *Bulletin of Earthquake Engineering* (if nonlinear work is added later).

## 1 Introduction
- Context: precast adoption in Bangladesh; the companion pre-feasibility paper (Paper 1) found that connection certification is the critical unresolved technical gap.
- What is missing: BNBC-based quantitative evidence on how precast connection flexibility changes global response (periods, drift, force distribution, wall demands) for a typical Dhaka residential building on soft soil.
- Contributions:
  1. A BNBC 2020-consistent reference building, including a documented correction of an irregular preliminary layout.
  2. A parametric comparison of the cast-in-situ system with precast variants spanning emulative to dry connections.
  3. Implications for BNBC design practice and for the connection-testing programme (Paper 3).

## 2 Background
- BNBC 2020 seismic provisions (zone, site class, SDC, R/Cd, Ta cap, RSA scaling, torsion), and precast provisions in Sec 6.10 (integrity ties, connections "by analysis or test").
- ACI 318-19 precast seismic options (18.9 strong/ductile connections, 18.11 special precast walls, ITG-5.1/550.6).
- Connection-stiffness literature:
  - beam–column semi-rigid behaviour (Monforton & Wu 1963; Elliott et al. 2003; Ferreira et al.; Lacerda et al. 2018; Moreira et al. 2024);
  - grouted-sleeve and bed-joint walls (Soudki et al. 1995; Peng et al. 2016; Xu et al. 2017; Zhu & Guo 2018; Han et al. 2019).

## 3 Building, site and code parameters
- 10 storeys at 3 m, 20 m x 15 m plan, 5 m grid; columns 500x500; beams 300x500; 150 mm slabs; C28; Grade 60 steel.
- Loads: dead, floor finish, partitions (line loads on beams), live 2.0 kN/m².
- Site: Bashundhara R/A, Dhaka. 5 SPT boreholes to 30.5 m, GWL at 0 m, N̄30 = 3.5–4.7, giving **site class SD**. S1/S2 are not excluded: no plasticity-index tests, and about 6.7 m of loose saturated fill is a liquefaction concern.
- BNBC: Z = 0.20, I = 1.0, SDC D; building frame system with special RC walls, R = 6, Ω = 2.5, Cd = 5; Ta = 0.626 s, design T ≤ 1.4Ta = 0.876 s.

## 4 Methodology
- **4.1 Preliminary layout and its deficiencies.** The original U-core design had extreme torsional irregularity (1.67–2.47), C = 0.056 (25% below BNBC) and partitions missing from the seismic weight.
- **4.2 Reference cast-in-situ model (M0).** Four point-symmetric perimeter walls; ETABS 22, scripted through the API; cracked-section modifiers; rigid diaphragms; fixed base; partitions in the mass.
- **4.3 Precast variants (M1–M4).**
  - Beam-end rotational springs Rk from fixity factor γ = 1/(1 + 3EI/(Rk L)).
  - Wall in-plane modifiers representing grouted bed joints.
  - Same loads and R (emulative assumption), with discussion of when R must change.
- **4.4 Analyses.** Modal (30 modes); ELF; RSA (BNBC SD spectrum, CQC/SRSS, 5% eccentricity, scaled to 85% V_ELF for forces); P-Δ stability coefficient; torsion check.
- **4.5 Member checks.**
  - Frame design: ETABS ACI 318-19 as a proxy for BNBC Part 6 Ch 6.
  - Walls: hand checks for shear, special boundary elements and required vertical steel.
  - Integrity-tie demand against BNBC 6.10.5 (44 kN/m vertical, 22 kN/m floor ties, 71 kN perimeter).
- **4.6 Sensitivity.** Rk and wall modifier ranges; diaphragm flexibility (optional); site class SD vs SE/S1 bracket.

## 5 Results (to be filled from `analysis/`)
- 5.1 Baseline compliance table: original vs redesigned.
- 5.2 Periods and modal shapes (M0–M4).
- 5.3 Base shear: ELF vs RSA, and scaling.
- 5.4 Storey drift profiles against the 0.020 limit.
- 5.5 Distribution of lateral force between walls and frames.
- 5.6 Member demand/capacity: walls, columns, beams; tie forces.
- 5.7 Sensitivity / tornado on drift and wall shear.

## 6 Discussion
- When precast is "equivalent" (emulative) and when connection flexibility matters.
- Design implications: walls carry more of the load as beam connections soften; the drift margin left; consequences for the gravity frame's deformation compatibility.
- Limits of linear analysis: no cyclic degradation, pinching or joint opening. These motivate nonlinear and experimental work (Paper 3).

## 7 Limitations
- Linear elastic analysis; idealised connection springs taken from literature ranges, not tests.
- ACI 318-19 used as a proxy for BNBC concrete design.
- Fixed base on soft soil (soil–structure interaction ignored); S1/S2 site class not excluded.
- Single building archetype.

## 8 Conclusions

## Data availability
Scripts in `paper2/scripts/`; models in `paper2/model/`. Add both to the GitHub repository.
