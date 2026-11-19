# Precast Connection Stiffness Parameters for Linear-Elastic ETABS Modeling

**Project Context & Mission.** This technical research report establishes literature-based stiffness parameters to model **precast concrete connections** in a linear-elastic ETABS model of a **10-storey reinforced concrete (RC) frame + shear-wall building**, benchmarked against an equivalent monolithic cast-in-situ (CIS) structure under the provisions of **BNBC 2020 (Part 6)** and **ACI 318-19**.

---

## 1. Mathematical Basis and Member Normalization

### 1.1 Project Structural Specifications
* **Storey Count & Height:** 10 storeys, typical storey height $h = 3.0\text{ m}$ (total height $H = 30.0\text{ m}$).
* **Concrete Compressive Strength:** $f'_c = 28\text{ MPa}$ (normal-weight concrete).
* **Modulus of Elasticity ($E_c$):**
  $$E_c = 4700\sqrt{f'_c} = 4700\sqrt{28} \approx 24{,}870.06\text{ MPa} = 2.4870 \times 10^7\text{ kN/m}^2$$
* **Columns:** $500 \times 500\text{ mm}$ ($0.5\text{ m} \times 0.5\text{ m}$):
  $$I_g = \frac{0.5 \times 0.5^3}{12} = 0.00520833\text{ m}^4$$
  $$I_{eff} = 0.70 I_g = 0.00364583\text{ m}^4$$
* **Beams:** $300 \times 500\text{ mm}$ ($b = 0.3\text{ m}$, total depth $h = 0.5\text{ m}$), clear/center span $L = 5.0\text{ m}$:
  $$I_g = \frac{0.3 \times 0.5^3}{12} = 0.003125\text{ m}^4$$
  $$I_{eff} = 0.35 I_g = 0.00109375\text{ m}^4$$
  $$E_c I_{eff} = (2.487006 \times 10^7\text{ kN/m}^2)(0.00109375\text{ m}^4) = 27{,}202.25\text{ kN}\cdot\text{m}^2$$
  $$\frac{E_c I_{eff}}{L} = \frac{27{,}202.25}{5.0} = 5{,}440.45\text{ kN}\cdot\text{m/rad}$$
  $$\frac{3E_c I_{eff}}{L} = 3 \times 5{,}440.45 = 16{,}321.35\text{ kN}\cdot\text{m/rad}$$
  $$\frac{4E_c I_{eff}}{L} = 4 \times 5{,}440.45 = 21{,}761.80\text{ kN}\cdot\text{m/rad}$$
* **Shear Walls:** Four in-plane structural walls, length $L_w = 5.0\text{ m}$, thickness $t_w = 200\text{ mm} = 0.2\text{ m}$.
  * Monolithic benchmark modifier (ACI 318-19 §6.6.3.1.1 / BNBC 2020 Part 6 §6.3.1.1): $f_{11} = f_{22} = f_{12} = 0.70$ (uncracked in flexure/shear) or $0.35$ (cracked).

---

### 1.2 Beam-Column Rotational Spring Formulation
The rotational restraint at the beam ends is characterized using the classical **Monforton & Wu (1963)** fixity factor $\gamma$ (also denoted $\alpha_R$ in **Ferreira, El Debs & Elliott 2003** and Brazilian code **ABNT NBR 9062**):

$$\gamma = \frac{1}{1 + \frac{3 E_c I_{eff}}{R_k L}} = \frac{R_k}{R_k + \frac{3 E_c I_{eff}}{L}}$$

Inverting this relationship gives the required ETABS rotational spring stiffness $R_k$ (in $\text{kN}\cdot\text{m/rad}$):

$$R_k = \frac{3 E_c I_{eff}}{L} \left(\frac{\gamma}{1 - \gamma}\right) = 16{,}321.35 \left(\frac{\gamma}{1 - \gamma}\right)$$

The normalized stiffness ratio relative to beam flexural rigidity is:

$$\frac{R_k}{E_c I_{eff} / L} = \frac{3\gamma}{1 - \gamma}$$

* When $\gamma = 1.00$: $R_k \to \infty$ (fully rigid, monolithic condition).
* When $\gamma = 0.00$: $R_k = 0$ (ideal pinned joint).
* When $0.15 < \gamma < 0.85$: connection exhibits **semi-rigid** behavior per NBR 9062 / Eurocode classification.

---

## 2. Literature-Based Connection Parameters Table

The parameters below compile experimental test data, finite element investigations, and international code classifications from **Elliott, Davies, Ferreira, Gorgun, & Mahdi (2003)**, **Ferreira, El Debs, & Elliott (2003)**, **Lacerda et al. (2018)**, **Moreira et al. (2024)**, **Xu et al. (2017)**, **Peng et al. (2016)**, **Zhu & Guo (2018)**, and **Soudki et al. (1995)**.

All derived $R_k$ values are explicitly calculated for the project beam ($300 \times 500\text{ mm}$, $L = 5.0\text{ m}$, $f'_c = 28\text{ MPa}$, $I_{eff} = 0.35 I_g$).

| Structural Connection / Component | Parameter Measure | Low | Central | High | ETABS Modeling Implementation | Key Literature Source(s) |
|---|---|---:|---:|---:|---|---|
| **A1. Emulative / Wet Cast-in-Place Joints**<br>*(Projecting rebar cast continuously in joint core)* | Fixity factor $\gamma$<br>$R_k$ ($\text{kN}\cdot\text{m/rad}$)<br>$R_k / (EI_{eff}/L)$ | **0.85**<br>92,488<br>17.00 | **0.95**<br>310,106<br>57.00 | **1.00**<br>$\infty$ (Rigid)<br>$\infty$ | **Assign > Frame > Releases & Partial Fixity**.<br>For $\gamma=1.00$, keep M3 rigid (no release). For finite emulative secant, release M3 and enter $R_k$. | ACI 318-19 §18.9.3; ABNT NBR 9062; Han et al. (2019); Ferreira et al. (2003) |
| **A2. Corbel + Dowel + Continuity Bars**<br>*(With vertical grouted interface & CIP topping)* | Fixity factor $\gamma$<br>$R_k$ ($\text{kN}\cdot\text{m/rad}$)<br>$R_k / (EI_{eff}/L)$ | **0.50**<br>16,321<br>3.00 | **0.65**<br>30,311<br>5.57 | **0.75**<br>48,964<br>9.00 | Release M3 at beam start and end; assign partial fixity spring $R_k$. Central value matches Lacerda test secant at yield ($29{,}903\text{ kN}\cdot\text{m/rad}$). | Lacerda et al. (2018); Ferreira, El Debs & Elliott (2003); fib Bulletin 43 (2008) |
| **A2b. Corbel + Continuity Bars (Ungrouted)**<br>*(Corbel bearing pad, ungrouted vertical seam)* | Fixity factor $\gamma$<br>$R_k$ ($\text{kN}\cdot\text{m/rad}$)<br>$R_k / (EI_{eff}/L)$ | **0.25**<br>5,440<br>1.00 | **0.27**<br>6,036<br>1.11 | **0.29**<br>6,667<br>1.23 | Release M3 at beam start and end; assign partial fixity spring $R_k$. Demonstrates loss of stiffness if vertical corbel gap is ungrouted. | Lacerda et al. (2018); fib Bulletin 43 (2008) |
| **A3. Bolted / Welded Dry Connections**<br>*(Steel cleats, embedded billets, welded plates)* | Fixity factor $\gamma$<br>$R_k$ ($\text{kN}\cdot\text{m/rad}$)<br>$R_k / (EI_{eff}/L)$ | **0.15**<br>2,880<br>0.53 | **0.30**<br>6,995<br>1.29 | **0.45**<br>13,354<br>2.45 | Release M3 at beam start and end; assign partial fixity spring $R_k$. Matches tested bare mechanical connectors before topping engagement. | Elliott, Davies, Ferreira, Gorgun, & Mahdi (2003); Moreira et al. (2024); Hashim & Agarwal (2018) |
| **A4. Pinned Bearings**<br>*(Elastomeric bearing pads / simple seated shelf)* | Fixity factor $\gamma$<br>$R_k$ ($\text{kN}\cdot\text{m/rad}$)<br>$R_k / (EI_{eff}/L)$ | **0.00**<br>0 (Free Pin)<br>0.00 | **0.05**<br>859<br>0.16 | **0.15**<br>2,880<br>0.53 | For ideal pin, release M3 with $R_k=0$. Upper bound ($\gamma=0.15$) represents nominal pad rotational restraint per code limits. | ABNT NBR 9062; Silva et al. (2021); fib Bulletin 43 (2008) |
| **B1. Grouted-Sleeve Precast Shear Walls**<br>*(Direct Macro-Modifier Method)* | Precast/Monolithic Initial Stiffness Ratio ($K_{PC}/K_{CIP}$)<br>**ETABS In-Plane Modifier ($f_{11}, f_{22}, f_{12}$)** | **0.65**<br><br>**0.45**<br>($0.70 \times 0.65$) | **0.80**<br><br>**0.56**<br>($0.70 \times 0.80$) | **0.93**<br><br>**0.65**<br>($0.70 \times 0.93$) | **Assign > Shell > Stiffness Modifiers**.<br>Apply modifier to membrane components $f_{11}, f_{22}, f_{12}$. Maintain out-of-plane bending modifiers $m_{11}=m_{22}=m_{12}=0.70$. | Xu et al. (2017); Peng, Qian, & Wang (2016); Zhu & Guo (2018); Soudki et al. (1995); Seifi et al. (2016) |
| **B2. Horizontal Bed Joints (Discrete Link Method)**<br>*(Horizontal shear sliding across 5 m joint)* | Total Joint Shear Stiffness $K_s$ ($\text{kN/mm}$)<br>Link Stiffness ($5$ links @ $1.0\text{ m}$) | **15,000**<br>3,000 / link | **28,750**<br>5,750 / link | **60,000**<br>12,000 / link | Model duplicated coincident seam nodes across floor levels; connect with 2-joint linear link elements in local shear direction. Keep shell modifier at $0.70$. | Pekau & Hum (1991); Seifi, Henry, & Ingham (2017) |
| **D1. Precast Floor Diaphragms**<br>*(Hollow-core / half-slab with structural topping)* | In-plane Modulus Ratio<br>$E_{eff}/E_c$ and $G_{eff}/G_c$ | **0.25** | **0.30** | **0.35** | Model floor as semi-rigid shell; apply modifier $0.30$ to in-plane membrane properties $f_{11}, f_{22}, f_{12}$. | Fleischman (2014) DSDM Report; ACI 550.5-18 |

---

## 3. Recommended ETABS Model Variants

To systematically evaluate the lateral performance of the precast building relative to the monolithic baseline, the following **six model variants** are recommended. All variants share identical geometry, gravity loading, mass, column modifiers ($0.70 I_g$), and seismic loading parameters.

```
+------------------------------------------------------------------------------------------------------------------------+
|                                              RECOMMENDED MODEL VARIANTS                                                |
+==================+===========================+=================================+========================+==============+
| Variant Label    | Beam-Column Connection    | Precast Wall In-Plane Modifier  | Floor Diaphragm        | Purpose      |
+==================+===========================+=================================+========================+==============+
| M0: CIS-Baseline | Rigid (Monolithic)        | Monolithic: f11=f22=f12 = 0.70  | Rigid                  | Reference    |
|                  | Rk = inf, gamma = 1.00    | (Cracked flexure/shear: 0.70)   | (Monolithic CIP slab)  | Benchmark    |
+------------------+---------------------------+---------------------------------+------------------------+--------------+
| M1: PC-Emulative | Fully Continuous          | Emulative Grouted Sleeves       | Rigid                  | Upper Bound  |
|     (Code SMF/SSW)| Rk = inf, gamma = 1.00   | f11=f22=f12 = 0.65              | (Continuous 150mm CIP  | Emulative    |
|                  | (Wet joint core §18.9.3)  | (Ratio K_PC/K_CIP = 0.93)       | structural topping)    | Qualification|
+------------------+---------------------------+---------------------------------+------------------------+--------------+
| M2: PC-SR-Central| Semi-Rigid Corbel         | Standard Grouted Sleeves        | Rigid                  | Recommended  |
|     (Standard PC)| Rk = 30,000 kN*m/rad      | f11=f22=f12 = 0.56              | (Topped precast floor) | Central      |
|                  | gamma = 0.647             | (Ratio K_PC/K_CIP = 0.80)       |                        | Design Model |
+------------------+---------------------------+---------------------------------+------------------------+--------------+
| M3: PC-SR-Low    | Lower Semi-Rigid Corbel   | Compliant Grouted Bed Joint     | Rigid                  | Conservative |
|     (Sensitivity)| Rk = 16,321 kN*m/rad      | f11=f22=f12 = 0.45              | (Topped precast floor) | Drift/P-Delta|
|                  | gamma = 0.500             | (Ratio K_PC/K_CIP = 0.65)       |                        | Envelope     |
+------------------+---------------------------+---------------------------------+------------------------+--------------+
| M4: PC-Dry-Mech  | Dry Bolted / Cleat        | Grouted Dowel Wall Bed Joint    | Rigid                  | Skeletal Dry |
|     (Mechanical) | Rk = 7,000 kN*m/rad       | f11=f22=f12 = 0.50              | (Topped precast floor) | Precast      |
|                  | gamma = 0.300             | (Ratio K_PC/K_CIP = 0.71)       |                        | Sensitivity  |
+------------------+---------------------------+---------------------------------+------------------------+--------------+
| M5: PC-Full-Flex | Semi-Rigid Corbel         | Standard Grouted Sleeves        | Semi-Rigid Shell       | Combined     |
|     (Diaphragm   | Rk = 30,000 kN*m/rad      | f11=f22=f12 = 0.56              | In-plane E_eff=0.30Ec, | Flexibility  |
|      Flexibility)| gamma = 0.647             | (Ratio K_PC/K_CIP = 0.80)       | G_eff=0.30Gc           | Realistic SLS|
+------------------+---------------------------+---------------------------------+------------------------+--------------+
```

### Variant Selection Logic
1. **M0 vs. M1:** Isolates the pure effect of precast wall grouted-sleeve joint compliance ($0.70 \to 0.65$) under fully emulative frame conditions.
2. **M0 vs. M2:** Demonstrates the realistic change in fundamental period, lateral drift, and frame moment redistribution when transitioning from cast-in-place to standard precast frame construction (corbels + continuous slab rebar).
3. **M2 vs. M3:** Provides the lower-bound sensitivity bracket recommended by PEER and ACI for frame stiffness uncertainty.
4. **M2 vs. M5:** Highlights whether in-plane diaphragm flexibility (PCI DSDM methodology) alters the shear wall load sharing and chord forces.

---

## 4. Code Compliance and Seismic Response Factors (Question C)

### 4.1 ACI 318-19 Seismic Provisions in SDC D
Under **ACI 318-19 Chapter 18**, structures assigned to **Seismic Design Category (SDC) D, E, or F** must use **Special Seismic Systems**:

#### 1. Special Moment Frames Constructed Using Precast Concrete (§18.9)
ACI 318-19 §18.9 permits two primary design routes:
* **Ductile Connections (§18.9.2):**
  * Inelastic yielding is designed to occur within the connection itself.
  * Must be qualified by comprehensive cyclic testing satisfying **ACI 374.1** (*Acceptance Criteria for Moment Frames Based on Structural Testing*).
  * The mechanical connectors or splices must develop high cyclic strain ductility without brittle failure.
* **Strong Connections (§18.9.3):**
  * The connection between precast elements is designed to remain essentially elastic while yielding occurs in precast beam plastic hinge zones away from the connection interface.
  * Connections must develop a design strength $\phi S_n \ge 1.4 S_e$, or develop at least $1.25 f_y$ of the longitudinal reinforcement.
  * **Emulative "wet" cast-in-place joints** (where longitudinal rebar laps within cast-in-place joint cores) qualify under this provision.

#### 2. Special Structural Walls Constructed Using Precast Concrete (§18.11)
* **General Scope (§18.11.1 & §18.11.2):** Special precast walls must satisfy all design and detailing requirements of **Section 18.10** (Cast-in-place Special Structural Walls), including boundary elements, shear reinforcement ratios, and web crushing limits.
* **Vertical Joints & Splices:**
  * Longitudinal reinforcement across horizontal panel joints must be spliced using **Type 2 mechanical splices** (§18.2.7), which are required to develop both the specified tensile strength ($f_u$) and at least $1.25 f_y$ of the bar.
  * Grouted splice sleeves meeting Type 2 requirements qualify as emulative "strong connections," enabling the precast wall to emulate cast-in-place monolithic performance.
* **Unbonded Post-Tensioned Precast Structural Walls (Jointed Rocking Walls):**
  * Governed by **ACI 318-19 §18.11.2.1**, **ACI ITG-5.1-07**, and successor standards **ACI 550.6-19** (Acceptance Criteria) and **ACI 550.7-19** (Design Requirements).
  * Walls rock on the foundation bed joint; self-centering is provided by unbonded post-tensioning tendons, while energy dissipation is provided by mild steel yielding devices or friction dampers.

---

### 4.2 Seismic Response Parameters ($R$, $\Omega_0$, $C_d$) Under ASCE 7-16/22 and BNBC 2020

```
+------------------------------------------------------------------------------------------------------------------------+
|                                SEISMIC RESPONSE FACTORS FOR SDC D STRUCTURES                                           |
+=============================================+=====+==========+=====+==================+================================+
| Structural System Classification            |  R  | Omega_0  | C_d | Height Limit (m) | Governing Code Standard        |
+=============================================+=====+==========+=====+==================+================================+
| Special RC Shear Walls (Building Frame)     | 6.0 |   2.5    | 5.0 |       50 m       | ASCE 7-16 Tab 12.2-1 / BNBC Tab 6.2.19 |
| Special Precast Shear Walls (Emulative)     | 6.0 |   2.5    | 5.0 |       50 m       | ACI 318 §18.11 / ASCE 7-16     |
| Special RC Shear Walls (Bearing Wall)       | 5.0 |   2.5    | 5.0 |       50 m       | ASCE 7-16 Tab 12.2-1 / BNBC Tab 6.2.19 |
| Special Precast Shear Walls (Bearing Wall)  | 5.0 |   2.5    | 5.0 |       50 m       | ACI 318 §18.11 / ASCE 7-16     |
| Dual System: Special Precast Walls + SMF    | 7.0 |   2.5    | 5.5 |     No Limit     | ASCE 7-16 Tab 12.2-1 / BNBC Tab 6.2.19 |
| Dual System: Special Precast Walls + IMF    | 6.5 |   2.5    | 5.0 |       50 m       | ASCE 7-16 Tab 12.2-1 / BNBC Tab 6.2.19 |
| Special Precast Moment Frames               | 8.0 |   3.0    | 5.5 |     No Limit     | ACI 318 §18.9 / ASCE 7-16      |
| Unbonded PT Rocking Walls (ACI 550.6/550.7) | 6.0 |   2.5    | 5.0 |       50 m       | ASCE 7 Alternative / NEHRP     |
+---------------------------------------------+-----+----------+-----+------------------+--------------------------------+
```

### 4.3 Do $R$ and $C_d$ Stay the Same as Cast-in-Place?
* **YES, provided the system is certified as EMULATIVE:**
  If the precast shear walls utilize grouted splice sleeves developing Type 2 mechanical splice strength ($\ge 1.25 f_y$ and $\ge f_u$) and satisfy all boundary zone detailing of ACI 318-19 §18.10 / §18.11, the precast system qualifies for the **exact same seismic response parameters** as monolithic cast-in-place walls:
  $$R = 6.0, \quad \Omega_0 = 2.5, \quad C_d = 5.0 \quad \text{(for Building Frame System)}$$
* **CRITICAL DESIGN CAVEAT for Semi-Rigid Frames:**
  If the precast frame utilizes **corbels or dry mechanical connectors** (semi-rigid with $\gamma = 0.30 - 0.65$), it does **NOT** qualify as a Special Moment Frame ($R=8$). 
  * Under BNBC 2020 §2.5.5.4, the building must be classified as a **Building Frame System with Special Precast Shear Walls** ($R=6, C_d=5$), where the precast frame is designed solely as a gravity framing system capable of supporting gravity loads through the design lateral displacement ($C_d \times \Delta_e$).
  * If the frame is intended to participate in lateral resistance as a **Dual System** ($R=7$), the frame must be verified to carry at least 25% of the total base shear and must satisfy §18.9 emulative wet connection or ACI 374.1 ductile testing requirements.

---

## 5. Step-by-Step ETABS Modeling Implementation

### 5.1 Beam End Releases & Rotational Springs
1. Select all 5 m floor beams.
2. Navigate to **Assign > Frame > Releases/Partial Fixity**.
3. Check the **Major Bending (M3)** box for both **Start** and **End**.
4. In the **Partial Fixity Springs** column, enter the chosen $R_k$ value:
   * **Central Corbel (Variant M2):** Enter `30000` $\text{kN}\cdot\text{m/rad}$.
   * **Low Corbel (Variant M3):** Enter `16321` $\text{kN}\cdot\text{m/rad}$.
   * **Dry Mechanical (Variant M4):** Enter `7000` $\text{kN}\cdot\text{m/rad}$.
5. Leave Axial, Shear, Torsion, and Minor Bending (M2) unticked (rigidly connected) unless specific details dictate otherwise.

### 5.2 Precast Shear Wall Modifiers (Direct Macro Method)
1. Select the four $5.0\text{ m} \times 0.2\text{ m}$ wall panels across all 10 storeys.
2. Navigate to **Assign > Shell > Stiffness Modifiers**.
3. In the **Membrane** fields ($f_{11}$, $f_{22}$, $f_{12}$), enter the equivalent modifier:
   * **CIS Reference (M0):** `0.70`
   * **PC-Emulative (M1):** `0.65`
   * **PC-Central (M2):** `0.56`
   * **PC-Low (M3):** `0.45`
4. In the **Bending** fields ($m_{11}$, $m_{22}$, $m_{12}$), keep `0.70` to maintain out-of-plane panel stability.

### 5.3 Diaphragm Flexibility Assignment
1. To model the precast floor diaphragm as semi-rigid (Variant M5), select floor slabs and go to **Assign > Shell > Diaphragms** -> select **Semi-Rigid**.
2. Navigate to **Assign > Shell > Stiffness Modifiers** and assign $f_{11} = f_{22} = f_{12} = 0.30$ to represent the reduced in-plane stiffness of precast hollow-core/half-slab units relative to monolithic concrete per PCI DSDM.

---

## 6. Verification Limits and Evidence Boundary

1. **Constitutive Non-Linearity vs. Elastic Secant:** Linear-elastic ETABS springs assume a constant secant stiffness $R_k$ or modifier. In reality, grouted bed joints and semi-rigid corbels experience progressive stiffness degradation, gap opening, and pinching under cyclic earthquake loading.
2. **Transferability of Test Strengths:** Cited experimental investigations utilized varying concrete strengths ($f'_c = 35\text{–}65\text{ MPa}$) and grout strengths ($60\text{–}90\text{ MPa}$). While dimensionless parameters ($\gamma$ and $K_{PC}/K_{CIP}$) normalize geometry and member size, localized bar bond-slip inside sleeves is sensitive to specific rebar diameter and sleeve geometry.
3. **Out-of-Plane Joint Action:** The wall stiffness reductions reported in literature apply strictly to **in-plane shear and flexure**. Out-of-plane wall stiffness and inter-panel vertical shear key behavior are not captured by 2D shell in-plane modifiers alone.
4. **fib Bulletin 43 Status:** fib Bulletin 43 provides the definitive qualitative framework and component force mechanisms for precast connections, but explicitly recommends project-specific testing or component calculation for absolute numerical rotational stiffness.

---

## 7. References (APA Style)

* American Concrete Institute. (2019). *Building code requirements for structural concrete (ACI 318-19) and commentary (ACI 318R-19)*. American Concrete Institute. https://doi.org/10.14359/51716937
* American Concrete Institute Innovation Task Group 5. (2008). *Acceptance criteria for special unbonded post-tensioned precast structural walls based on validation testing (ACI ITG-5.1-07)*. American Concrete Institute. https://www.concrete.org/store/productdetail.aspx?Format=DOWNLOAD&ItemID=ITG5107&Language=English&Units=Metric
* American Concrete Institute Committee 550. (2018). *Code requirements for the design of precast concrete diaphragms for earthquake motions (ACI 550.5-18) and commentary*. American Concrete Institute. https://www.concrete.org/Portals/0/Files/PDF/Previews/550.5-18_preview.pdf
* American Concrete Institute Committee 550. (2018). *Qualification of precast concrete diaphragm connections and reinforcement at joints for earthquake loading (ACI 550.4-18) and commentary*. American Concrete Institute. https://www.concrete.org/Portals/0/Files/PDF/Previews/550.4-18_preview.pdf
* American Concrete Institute Committee 550. (2019). *Acceptance criteria for special unbonded post-tensioned precast structural walls based on validation testing (ACI 550.6-19)*. American Concrete Institute. https://www.concrete.org/Portals/0/Files/PDF/Previews/550.6-19_preview.pdf
* American Concrete Institute Committee 550. (2019). *Requirements for design of a special unbonded post-tensioned precast shear wall satisfying ACI 550.6 (ACI 550.7-19)*. American Concrete Institute. https://www.concrete.org/Portals/0/Files/PDF/Previews/550.7-19_preview.pdf
* Elliott, K. S., Davies, G., Ferreira, M., Gorgun, H., & Mahdi, A. A. (2003). Can precast concrete structures be designed as semi-rigid frames? – Part 1: The experimental evidence. *The Structural Engineer*, 81(16), 14–27. https://www.istructe.org/journal/volumes/volume-81-(2003)/issue-16/can-precast-concrete-structures-be-designed-as-(1)/
* Elliott, K. S., Davies, G., Ferreira, M., Mahdi, A. A., & Gorgun, H. (2003). Can precast concrete structures be designed as semi-rigid frames? – Part 2: Analytical equations and column effective length factors. *The Structural Engineer*, 81(16), 28–37. https://www.istructe.org/journal/volumes/volume-81-(2003)/issue-16/can-precast-concrete-structures-be-designed-as-(2)/
* Ferreira, M. A., El Debs, M. K., & Elliott, K. S. (2003). Analysis of multi-storey precast frames with semi-rigid connections. In *Proceedings of the 45th Brazilian Concrete Congress (IBRACON 2003)*. IBRACON.
* Fédération internationale du béton. (2008). *Structural connections for precast concrete buildings* (fib Bulletin 43). International Federation for Structural Concrete. ISBN: 978-2-88394-083-3. https://www.fib-international.org/publications/fib-bulletins/structural-connections-for-precast-concrete-buildings-detail.html
* Fleischman, R. B. (2014). *Seismic design methodology document for precast concrete diaphragms* (DSDM Consortium Deliverable). Precast/Prestressed Concrete Institute. https://www.pci.org/PCI_Docs/Design_Resources/Research_and_Development/DSDM%20report.pdf
* Government of Bangladesh, Ministry of Housing and Public Works. (2021). *Bangladesh National Building Code (BNBC 2020)* (S.R.O. No. 55-Law/2020). Bangladesh Government Press.
* Han, W., Zhao, Z., & Qian, J. (2019). Global experimental response of a three-story, full-scale precast concrete shear wall structure with reinforcing bars spliced by grouted couplers. *PCI Journal*, 64(1), 65–80. https://doi.org/10.15554/pcij64.1-01
* Hashim, N., & Agarwal, J. (2018). Rotational stiffness of precast beam-column connection using finite element method. *IOP Conference Series: Earth and Environmental Science*, 140, Article 012128. https://doi.org/10.1088/1755-1315/140/1/012128
* Lacerda, M. M. S., da Silva, T. J., Alva, G. M. S., & de Lima, M. C. V. (2018). Influence of the vertical grouting in the interface between corbel and beam in beam-to-column connections of precast concrete structures—An experimental analysis. *Engineering Structures*, 172, 201–213. https://doi.org/10.1016/j.engstruct.2018.05.113
* Monforton, G. R., & Wu, T. S. (1963). Matrix analysis of semi-rigidly connected frames. *Journal of the Structural Division, ASCE*, 89(6), 13–42. https://doi.org/10.1061/JSDEAG.0000997
* Moreira, G., Marreiros, R., Marchão, C., & Reguengo, R. (2024). Evaluation of the rotational stiffness of precast reinforced concrete beam-column connections. *Engineering Structures*, 308, Article 117933. https://doi.org/10.1016/j.engstruct.2024.117933
* Pekau, O. A., & Hum, D. (1991). Seismic response of friction-jointed precast panel shear walls. *PCI Journal*, 36(2), 56–71. https://doi.org/10.15554/pcij.03011991.56.71
* Peng, Y.-Y., Qian, J.-R., & Wang, Y.-H. (2016). Cyclic performance of precast concrete shear walls with a mortar–sleeve connection for longitudinal steel bars. *Materials and Structures*, 49(6), 2455–2469. https://doi.org/10.1617/s11527-015-0660-0
* Seifi, P., Henry, R. S., & Ingham, J. M. (2016). Panel connection details in existing New Zealand precast concrete buildings. *Bulletin of the New Zealand Society for Earthquake Engineering*, 49(2), 190–199. https://doi.org/10.5459/bnzsee.49.2.190-199
* Seifi, P., Henry, R. S., & Ingham, J. M. (2017). In-plane testing of precast concrete wall panels with grouted sleeve. In *Proceedings of the 2017 NZSEE Conference*. New Zealand Society for Earthquake Engineering. https://db.nzsee.org.nz/2017/O2A.2_Seifi.pdf
* Silva, J. V. M. A., Vanalli, L., de Souza, L. A. F., & Rolim, C. P. M. (2021). Numerical analysis of the behavior of beam-column precast connections without continuity reinforcement. *Revista IBRACON de Estruturas e Materiais*, 14(5), Article e14505. https://doi.org/10.1590/S1983-41952021000500005
* Soudki, K. A., Rizkalla, S. H., & LeBlanc, B. (1995). Horizontal connections for precast concrete shear walls subjected to cyclic deformations — Part 1: Mild steel connections. *PCI Journal*, 40(4), 78–96. https://doi.org/10.15554/pcij.07011995.78.96
* Soudki, K. A., Rizkalla, S. H., & Daikiw, R. W. (1995). Horizontal connections for precast concrete shear walls subjected to cyclic deformations — Part 2: Prestressed connections. *PCI Journal*, 40(5), 82–96. https://doi.org/10.15554/pcij.09011995.82.96
* Xu, G., Wang, Z., Wu, B., Bursi, O. S., Tan, X., Yang, Q., & Wen, L. (2017). Seismic performance of precast shear wall with sleeves connection based on experimental and numerical studies. *Engineering Structures*, 150, 346–358. https://doi.org/10.1016/j.engstruct.2017.06.026
* Zhu, Z., & Guo, Z. (2018). In-plane quasi-static cyclic tests on emulative precast concrete walls. *KSCE Journal of Civil Engineering*, 22(8), 2890–2898. https://doi.org/10.1007/s12205-017-0695-6
