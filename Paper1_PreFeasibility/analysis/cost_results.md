# Projected Cost Model: Precast RCC vs. Conventional Cast-in-Situ Construction
**Location:** Dhaka, Bangladesh  
**Benchmark:** 10-Storey Residential Structure (Core & Shell)  
**Date:** November 2026  
**Status:** Pre-feasibility Projections (Mathematical & Deterministic Implementation)

> [!IMPORTANT]
> **Projected Figures Notice:** No commercial primary precast manufacturing facility currently operates in Bangladesh for multi-storey residential superstructures. All precast figures presented in this report are **projections** derived from international literature adjustment factors, empirical cast-in-situ material registers in Dhaka, and engineering plant amortisation economics.

---

## 1. Corrected Table 7: Projected Cost Comparison (BDT/m² Gross Floor Area)

This table recomputes the earlier working paper's Table 7, strictly correcting variance calculation errors (specifically, Equipment/Plant Cost corrected from +140% to **+150.0%**, and QC/Testing corrected from +100% to **+150.0%**), and providing system cost shares.

| Cost Component | Conventional Baseline (BDT/m²) | Precast RCC Projected (BDT/m²) | Projected Variance (%) | Conv. Share (%) | Precast Share (%) | Status / Notes |
|:---|:---:|:---:|:---:|:---:|:---:|:---|
| **Material Cost** | 10,000 | 9,200 | -8.0% | 55.56% | 60.13% | Verified |
| **Labour Cost** | 4,000 | 1,600 | -60.0% | 22.22% | 10.46% | Verified |
| **Equipment / Plant Cost** | 500 | 1,250 | +150.0% | 2.78% | 8.17% | Corrected (+140% -> +150%) |
| **Transportation Cost** | 500 | 1,650 | +230.0% | 2.78% | 10.78% | Verified |
| **Formwork Cost** | 2,000 | 400 | -80.0% | 11.11% | 2.61% | Verified |
| **Quality Control / Testing** | 200 | 500 | +150.0% | 1.11% | 3.27% | Corrected (+100% -> +150%) |
| **Overhead & Preliminaries** | 800 | 700 | -12.5% | 4.44% | 4.58% | Verified |
| **Total Construction Cost** | **18,000** | **15,300** | **-15.0%** | **100.00%** | **100.00%** | **15.0% Net Saving at Design Scale** |

---

## 2. Plant Economics & Calibration

The earlier working paper suffered from an internal inconsistency in Table 8, where multiplying fixed cost per panel by volume yielded total fixed costs scaling from 70M to 380M BDT/year. In a single dedicated manufacturing facility, total annual fixed overhead and capitalised depreciation are mathematically constant.

### Calibration Parameters:
- **Standard Panel Dimensions:** $4.3\text{ m} \times 3.0\text{ m} = 12.9\text{ m}^2$ ($A = 12.9\text{ m}^2$).
- **Floor-Area Conversion Factor ($k$):** Assume $1\text{ m}^2\text{ panel} \approx 1\text{ m}^2\text{ floor area equivalent}$ ($k = 1.0$, tested $0.8 - 1.2$).
- **Design Benchmark Production Scale ($N_0$):** $5,000\text{ panels/year}$ ($64,500\text{ m}^2\text{ floor area/year}$).
- **Financial Baseline:** Discount rate $i = 10.0\%$, plant economic life $n = 15\text{ years}$.
  $$\text{CRF} = \frac{i(1+i)^n}{(1+i)^n - 1} = \frac{0.10(1.10)^{15}}{(1.10)^{15} - 1} \approx 0.131474$$
- **Fixed Cost Calibration from Table 7:**
  - Annualised Equipment / Plant Capex: $1,250\text{ BDT/m}^2 \times 64,500\text{ m}^2 = 80,625,000\text{ BDT/year}$
  - Fixed Annual Overhead ($F_o$): $700\text{ BDT/m}^2 \times 64,500\text{ m}^2 = 45,150,000\text{ BDT/year}$
  - **Total Annual Fixed Cost ($F$):** $125,775,000\text{ BDT/year}$ (strictly constant)
- **Implied Initial Plant Capex ($C_0$):**
  $$C_0 = \frac{\text{Annualised Capex}}{\text{CRF}} = \frac{80,625,000}{0.131474} = 613,240,160\text{ BDT} \quad (\approx \$5,026,558.69\text{ USD at 122 BDT/USD})$$
  *(This $5.03M USD initial capex aligns with international turn-key carousel plant installations of 60,000–80,000 m²/year capacity).*
- **Variable Operating Cost ($v$):**
  - Manufacturing Variable: $\text{Material (9,200)} + \text{Labour (1,600)} + \text{Formwork (400)} + \text{QC (500)} = 11,700\text{ BDT/m}^2$
  - Transportation & Erection: $1,650\text{ BDT/m}^2$
  - **Total Variable Cost ($v_{total}$):** $13,350\text{ BDT/m}^2$ ($172,215\text{ BDT/panel}$)

### Closed-Form Parity Breakeven Volume ($N^*$):
$$\text{Unit Margin } m = c_{conv} - v_{total} = 18,000 - 13,350 = 4,650\text{ BDT/m}^2$$
$$N^* = \frac{F}{m \cdot A \cdot k} = \frac{125,775,000}{4,650 \times 12.9 \times 1.0} = \mathbf{2,096.77\text{ panels/year}} \quad (\approx 27,048\text{ m}^2/\text{year})$$
*This analytically verifies the earlier paper's headline parity threshold of ~2,000–3,000 panels/year.*

---

## 3. Corrected Table 8: Economies of Scale Projection

All fixed costs scale strictly inversely with annual output volume ($F / N$), while direct variable unit costs remain constant.

| Annual Volume (panels/yr) | Fixed Cost / Panel (BDT) | Variable Cost / Panel (BDT) | Total Cost / Panel (BDT) | Projected Cost per m² (BDT) | Fixed Share per m² (BDT) | Var. Share per m² (BDT) | vs. Conventional (18,000 BDT/m²) | Economic Assessment |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---|
| **500** | 251,550 | 172,215 | 423,765 | **32,850** | 19,500 | 13,350 | **+82.50%** | Severe Low-Scale Penalty |
| **1,000** | 125,775 | 172,215 | 297,990 | **23,100** | 9,750 | 13,350 | **+28.33%** | Severe Low-Scale Penalty |
| **2,000** | 62,888 | 172,215 | 235,102 | **18,225** | 4,875 | 13,350 | **+1.25%** | Near Cost Parity (+1.3%) |
| **3,000** | 41,925 | 172,215 | 214,140 | **16,600** | 3,250 | 13,350 | **-7.78%** | Economic Viability Reached (-7.8%) |
| **5,000** | 25,155 | 172,215 | 197,370 | **15,300** | 1,950 | 13,350 | **-15.00%** | Design Scale Parity (-15.0%) |
| **10,000** | 12,578 | 172,215 | 184,792 | **14,325** | 975 | 13,350 | **-20.42%** | High-Scale Industrialised (-20.4%) |

---

## 4. Sensitivity Analysis (One-at-a-Time)

Tornado sensitivity testing ranks each parameter's influence on the parity threshold $N^*$ (panels/year) and the projected cost differential at 5,000 panels/year.

| Rank | Parameter | Base Value | Low Value | High Value | Low Impact: $N^*$ (panels/yr) | High Impact: $N^*$ (panels/yr) | $N^*$ Spread (panels/yr) | Cost at 5k: Low vs High (% vs Conv) |
|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 1 | **Conventional Baseline (BDT/m²)** | 18,000.00 | 14,000.00 | 22,000.00 | 15,000.0 | 1,127.2 | **13,872.8** | +9.3% to -30.5% |
| 2 | **Floor Area Served per Panel Area (k)** | 1.00 | 0.80 | 1.20 | 2,621.0 | 1,747.3 | **873.7** | -12.3% to -16.8% |
| 3 | **Discount Rate / Cost of Capital (i)** | 0.10 | 0.06 | 0.14 | 1,805.3 | 2,417.1 | **611.8** | -16.5% to -13.3% |
| 4 | **Labour Saving vs Conventional (%)** | 0.60 | 0.40 | 0.70 | 2,532.5 | 1,930.7 | **601.8** | -10.6% to -17.2% |
| 5 | **Transport & Erection Premium (%)** | 2.30 | 1.00 | 3.50 | 1,839.6 | 2,407.4 | **567.8** | -18.6% to -11.7% |
| 6 | **Plant Initial Capex C0 (BDT)** | 613,240,160.20 | 490,592,128.16 | 735,888,192.24 | 1,828.0 | 2,365.6 | **537.6** | -16.4% to -13.6% |
| 7 | **Plant Economic Life (years)** | 15.00 | 10.00 | 20.00 | 2,416.5 | 1,953.5 | **463.0** | -13.3% to -15.7% |
| 8 | **Equipment Premium vs Conventional (%)** | 1.50 | 1.20 | 1.80 | 1,935.5 | 2,258.1 | **322.6** | -15.8% to -14.2% |
| 9 | **Annual Fixed Overhead Fo (BDT)** | 45,150,000.00 | 36,120,000.00 | 54,180,000.00 | 1,946.2 | 2,247.3 | **301.1** | -15.8% to -14.2% |
| 10 | **Formwork Saving vs Conventional (%)** | 0.80 | 0.60 | 0.90 | 2,294.1 | 2,010.3 | **283.8** | -12.8% to -16.1% |

### Key Findings from Sensitivity Analysis:
1. **Dominant Driver — Conventional Price Baseline ($c_{conv}$):** A shift from 18,000 to 14,000 BDT/m² increases breakeven to **15,000 panels/yr**, making precast unviable at low volumes. Conversely, if conventional costs rise to 22,000 BDT/m², breakeven drops to **1,127 panels/yr**.
2. **Floor-to-Panel Ratio ($k$):** Varies breakeven volume across an 874 panel/yr envelope (1,747 to 2,621 panels/yr).
3. **Discount Rate & Labour Savings:** Capital financing rate shifts breakeven by 612 panels/yr, while labour savings shift it by 602 panels/yr.

---

## 5. Monte Carlo Probabilistic Simulation (10,000 Draws)

Deterministic triangular distributions (seed = 42) across all engineering and economic ranges yield the following probabilistic metrics:

| Metric | Projected Value | Analytical Interpretation |
|:---|:---:|:---|
| **Breakeven Volume $N^*$ — P10 (Optimistic)** | **1,430.7 panels/yr** | 10% probability breakeven occurs at or below ~1,431 panels/yr |
| **Breakeven Volume $N^*$ — P50 (Median)** | **2,237.7 panels/yr** | Median projected market breakeven threshold |
| **Breakeven Volume $N^*$ — P90 (Pessimistic)** | **4,539.6 panels/yr** | 90% probability breakeven occurs at or below ~4,540 panels/yr |
| **Probability Precast Cheaper at 2,000 panels/yr** | **39.08%** | Near parity threshold; high sensitivity to conventional pricing |
| **Probability Precast Cheaper at 5,000 panels/yr** | **92.08%** | Overwhelming probability of cost savings at medium commercial scale |
| **Probability Precast Cheaper at 10,000 panels/yr** | **98.76%** | Industrial scale provides near-certain economic superiority |

---

## 6. Assumptions & Data Sources Audit Trail

| Parameter | Value | Categorisation | Citation / Justification |
|:---|:---:|:---:|:---|
| **Conventional Baseline** | 18,000 BDT/m² | Assumed | Core & Shell residential benchmark from SSRN working paper & developer surveys |
| **Conventional Formwork Spend** | 2,000 BDT/m² (11.1%) | Empirical register / Lit | Dhaka 10-storey material register showed formwork is ~46% of structural material spend |
| **Precast Formwork Saving** | -80.0% | Literature-derived | Reusable precision steel casting moulds (>200 pours) replace sacrificial shuttering |
| **Precast Labour Saving** | -60.0% | Literature-derived | Off-site automated plant mechanisation replaces intensive on-site formwork carpentry |
| **Precast Transport Premium** | +230.0% | Literature-derived | Flatbed logistics + mobile crane erection allowance under Dhaka urban traffic conditions |
| **Precast Equipment Premium** | +150.0% | Literature-derived | Reflects capitalisation of batch plant, carousel system, overhead cranes, and gantry |
| **Precast Material Saving** | -8.0% | Literature-derived | Centralised batching plant aggregate weighing, silo cement, and minimized rebar scrap |
| **Panel Unit Area ($A$)** | 12.9 m² | Standard Engineering | Standard $4.3\text{ m} \times 3.0\text{ m}$ load-bearing or infill panel geometry |
| **Floor Area Served Ratio ($k$)** | 1.0 m²/m² | Assumed | Direct 1:1 floor area to panel area equivalence (tested 0.8–1.2) |
| **Plant Asset Life ($n$)** | 15 years | Standard Corporate Finance | Depreciable life of semi-automated precast carousel casting machinery |
| **Cost of Capital ($i$)** | 10.0% | Assumed | Prime commercial industrial lending rate in Bangladesh |
| **Exchange Rate** | 122 BDT / USD | Commercial Benchmark | 2024–2026 Bangladesh foreign exchange conversion rate |

---

## 7. Generated Visualisations

- **Tornado Chart:** `fig_tornado_breakeven.png` (300 DPI, one-at-a-time breakeven variance ranking)
- **Scale Curve:** `fig_scale_curve.png` (300 DPI, projected unit cost vs. production volume with conventional uncertainty envelope)
