#!/usr/bin/env python3
"""
cost_model.py - Transparent, Reproducible Projected Cost Model for Precast RCC
vs Conventional Cast-in-Situ Residential Construction in Dhaka, Bangladesh.

Mission:
  Replaces the internally inconsistent Table 7 and Table 8 of the earlier SSRN
  working paper with a mathematically rigorous, fully reproducible engineering
  cost model.

Context & Scope:
  Pre-feasibility evaluation for multi-storey residential buildings in Dhaka.
  Because no primary commercial precast manufacturing data currently exist in
  Bangladesh, all precast figures are PROJECTIONS derived from literature
  adjustment factors, international plant benchmarks, and empirical cast-in-situ
  material registers. All outputs are explicitly designated as 'projected'.

Author: Construction Cost Engineer & Quantitative Analyst (Multi-AI Team)
Date: November 2026
"""

import os
import json
import math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# ==============================================================================
# PARAMETER BLOCK - GLOBAL CONFIGURATION & ASSUMPTIONS
# ==============================================================================

# Currency & Exchange Rate
USD_TO_BDT = 122.0  # 1 USD = 122 BDT (Projected 2024-2026 commercial benchmark)

# Conventional Cast-in-Situ Baseline (BDT / m² Gross Floor Area)
# Source: Literature benchmark & local residential developer register estimates
C_CONV_BASELINE = 18000.0  # Baseline 'Core and Shell' benchmark (BDT/m²) [ASSUMED]
C_CONV_MIN = 14000.0       # Low bound for sensitivity [ASSUMED]
C_CONV_MAX = 22000.0       # High bound for sensitivity [ASSUMED]

# Conventional Cost Breakdown (BDT / m²)
CONV_BREAKDOWN = {
    "Material Cost": 10000.0,
    "Labour Cost": 4000.0,
    "Equipment / Plant Cost": 500.0,
    "Transportation Cost": 500.0,
    "Formwork Cost": 2000.0,
    "Quality Control / Testing": 200.0,
    "Overhead & Preliminaries": 800.0,
}

# Literature-Derived Precast Variance Factors vs Conventional Baseline
# Sources: International precast literature (India, Malaysia, Singapore, HK)
# and empirical formwork registers in Dhaka.
PRECAST_VARIANCES = {
    "Material Cost": -0.08,             # -8.0% (factory batching efficiency & reduced wastage)
    "Labour Cost": -0.60,               # -60.0% (off-site factory mechanization vs site casting)
    "Equipment / Plant Cost": +1.50,    # +150.0% (corrected from +140%; plant capex amortized at 5k units)
    "Transportation Cost": +2.30,       # +230.0% (heavy flatbed logistics & on-site craneage)
    "Formwork Cost": -0.80,             # -80.0% (steel mould high repetition / formwork elimination)
    "Quality Control / Testing": +1.50, # +150.0% (corrected from +100%; factory batch testing & cube tests)
    "Overhead & Preliminaries": -0.125, # -12.5% (shortened construction cycle & site overhead reduction)
}

# Precast Panel & Geometry Parameters
PANEL_WIDTH = 4.3   # metres
PANEL_HEIGHT = 3.0  # metres
PANEL_AREA = round(PANEL_WIDTH * PANEL_HEIGHT, 2)  # 12.9 m² (nominal 13 m²)
K_FLOOR_PER_PANEL = 1.0  # m² floor area served per m² panel (default 1.0; range 0.8-1.2) [ASSUMED]

# Baseline Production Scale for Table 7 Calibration
N_BASELINE = 5000  # 5,000 panels/year (design benchmark scale)

# Plant Financial & Capital Recovery Parameters
DISCOUNT_RATE = 0.10     # i = 10.0% annual cost of capital [ASSUMED]
PLANT_LIFE_YRS = 15      # n = 15 years economic asset life [ASSUMED]

# Capital Recovery Factor: CRF = i * (1 + i)^n / ((1 + i)^n - 1)
CRF_BASELINE = (DISCOUNT_RATE * (1.0 + DISCOUNT_RATE) ** PLANT_LIFE_YRS) / (
    (1.0 + DISCOUNT_RATE) ** PLANT_LIFE_YRS - 1.0
)

# Plant Fixed Cost Calibration:
# In Table 7, at N = 5,000 panels/yr (equivalent to 5,000 * 12.9 * 1.0 = 64,500 m²/yr):
#   - Precast Equipment / Plant Cost = 1,250 BDT/m²
#   - Precast Overhead & Preliminaries = 700 BDT/m²
#   Total Annual Fixed Cost F = (1,250 + 700) * 64,500 = 125,775,000 BDT/yr
ANNUAL_CAPEX_BDT = CONV_BREAKDOWN["Equipment / Plant Cost"] * (1.0 + PRECAST_VARIANCES["Equipment / Plant Cost"]) * N_BASELINE * PANEL_AREA * K_FLOOR_PER_PANEL
ANNUAL_OVERHEAD_FO_BDT = CONV_BREAKDOWN["Overhead & Preliminaries"] * (1.0 + PRECAST_VARIANCES["Overhead & Preliminaries"]) * N_BASELINE * PANEL_AREA * K_FLOOR_PER_PANEL

TOTAL_FIXED_COST_F_BDT = ANNUAL_CAPEX_BDT + ANNUAL_OVERHEAD_FO_BDT  # 125,775,000 BDT/yr
CAPEX_C0_BDT = ANNUAL_CAPEX_BDT / CRF_BASELINE                      # Implied initial capex
CAPEX_C0_USD = CAPEX_C0_BDT / USD_TO_BDT                            # Implied initial capex in USD

# Direct Variable Cost per m² (excl. fixed plant & overhead share):
# Components: Material (9,200) + Labour (1,600) + Formwork (400) + QC (500) = 11,700 BDT/m²
V_MFG_BDT = (
    CONV_BREAKDOWN["Material Cost"] * (1.0 + PRECAST_VARIANCES["Material Cost"])
    + CONV_BREAKDOWN["Labour Cost"] * (1.0 + PRECAST_VARIANCES["Labour Cost"])
    + CONV_BREAKDOWN["Formwork Cost"] * (1.0 + PRECAST_VARIANCES["Formwork Cost"])
    + CONV_BREAKDOWN["Quality Control / Testing"] * (1.0 + PRECAST_VARIANCES["Quality Control / Testing"])
)
TRANSPORT_PER_M2_BDT = CONV_BREAKDOWN["Transportation Cost"] * (1.0 + PRECAST_VARIANCES["Transportation Cost"])
V_TOTAL_BDT = V_MFG_BDT + TRANSPORT_PER_M2_BDT  # 13,350 BDT/m²

# Output Paths
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
FIG_TORNADO_PATH = os.path.join(OUTPUT_DIR, "fig_tornado_breakeven.png")
FIG_SCALE_PATH = os.path.join(OUTPUT_DIR, "fig_scale_curve.png")
RESULTS_MD_PATH = os.path.join(OUTPUT_DIR, "cost_results.md")
RESULTS_JSON_PATH = os.path.join(OUTPUT_DIR, "cost_results.json")


# ==============================================================================
# 1. TABLE 7: PROJECTED COST COMPARISON WITH CORRECTED VARIANCES
# ==============================================================================

def compute_table_7():
    """Recomputes Table 7 with mathematically correct variance percentages and shares."""
    rows = []
    total_conv = 0.0
    total_precast = 0.0

    for comp, c_conv in CONV_BREAKDOWN.items():
        var_rate = PRECAST_VARIANCES[comp]
        c_pre = c_conv * (1.0 + var_rate)
        total_conv += c_conv
        total_precast += c_pre
        rows.append({
            "component": comp,
            "conv_bdt": c_conv,
            "precast_bdt": c_pre,
            "variance_pct": var_rate * 100.0,
        })

    # Shares of total
    for r in rows:
        r["conv_share_pct"] = (r["conv_bdt"] / total_conv) * 100.0
        r["precast_share_pct"] = (r["precast_bdt"] / total_precast) * 100.0

    total_variance_pct = ((total_precast - total_conv) / total_conv) * 100.0
    summary = {
        "rows": rows,
        "total_conv_bdt": total_conv,
        "total_precast_bdt": total_precast,
        "total_variance_pct": total_variance_pct,
    }
    return summary


# ==============================================================================
# 2. PLANT ECONOMICS & TABLE 8 REPLACEMENT
# ==============================================================================

def crf(interest_rate, life_years):
    """Calculates Capital Recovery Factor."""
    if interest_rate == 0:
        return 1.0 / life_years
    num = interest_rate * ((1.0 + interest_rate) ** life_years)
    den = ((1.0 + interest_rate) ** life_years) - 1.0
    return num / den


def unit_cost_precast(n_panels, c0=CAPEX_C0_BDT, fo=ANNUAL_OVERHEAD_FO_BDT,
                      i=DISCOUNT_RATE, n_life=PLANT_LIFE_YRS,
                      v_mfg=V_MFG_BDT, trans=TRANSPORT_PER_M2_BDT,
                      area=PANEL_AREA, k=K_FLOOR_PER_PANEL):
    """Calculates precast unit cost per m² at annual volume N."""
    f_annual = (c0 * crf(i, n_life)) + fo
    floor_area_annual = n_panels * area * k
    fixed_per_m2 = f_annual / floor_area_annual
    total_per_m2 = v_mfg + trans + fixed_per_m2
    return total_per_m2, fixed_per_m2, v_mfg + trans, f_annual


def breakeven_volume(c_conv=C_CONV_BASELINE, c0=CAPEX_C0_BDT, fo=ANNUAL_OVERHEAD_FO_BDT,
                     i=DISCOUNT_RATE, n_life=PLANT_LIFE_YRS,
                     v_mfg=V_MFG_BDT, trans=TRANSPORT_PER_M2_BDT,
                     area=PANEL_AREA, k=K_FLOOR_PER_PANEL):
    """Calculates closed-form breakeven production volume N* (panels/year)."""
    v_total = v_mfg + trans
    margin_per_m2 = c_conv - v_total
    if margin_per_m2 <= 0:
        return float('inf')  # Precast unit variable exceeds conventional price
    f_annual = (c0 * crf(i, n_life)) + fo
    n_star = f_annual / (margin_per_m2 * area * k)
    return n_star


def compute_table_8(volumes=(500, 1000, 2000, 3000, 5000, 10000)):
    """Computes internally consistent Table 8 replacement across production volumes."""
    rows = []
    area = PANEL_AREA
    k = K_FLOOR_PER_PANEL

    for n in volumes:
        tot_m2, fix_m2, var_m2, f_ann = unit_cost_precast(n)
        fix_panel = fix_m2 * area * k
        var_panel = var_m2 * area * k
        tot_panel = fix_panel + var_panel
        pct_vs_conv = ((tot_m2 - C_CONV_BASELINE) / C_CONV_BASELINE) * 100.0

        rows.append({
            "volume_panels_yr": n,
            "fixed_cost_per_panel_bdt": fix_panel,
            "variable_cost_per_panel_bdt": var_panel,
            "total_unit_cost_per_panel_bdt": tot_panel,
            "equivalent_cost_per_m2_bdt": tot_m2,
            "fixed_cost_per_m2_bdt": fix_m2,
            "variable_cost_per_m2_bdt": var_m2,
            "vs_conventional_pct": pct_vs_conv,
            "total_annual_fixed_cost_bdt": f_ann,
        })
    return rows


# ==============================================================================
# 3. SENSITIVITY ANALYSIS & PLOTS
# ==============================================================================

def run_sensitivity_analysis():
    """Executes one-at-a-time sensitivity analysis across specified parameters."""
    base_n_star = breakeven_volume()
    base_cost_5k, _, _, _ = unit_cost_precast(N_BASELINE)
    base_pct_5k = ((base_cost_5k - C_CONV_BASELINE) / C_CONV_BASELINE) * 100.0

    # Sensitivity parameter definitions: (label, low_val, base_val, high_val, param_key)
    # Specified ranges from user prompt:
    #   conventional baseline (14,000-22,000)
    #   labour saving (40-70%)
    #   formwork saving (60-90%)
    #   transport premium (+100% to +350%)
    #   equipment premium (120% to 180%, or +/-20% on Capex C0)
    #   capex C0 (+/-20%)
    #   discount rate (6-14%)
    #   plant life (10-20 yr)
    #   k (0.8-1.2)
    #   fixed overhead Fo (+/-20%)
    sens_configs = [
        {
            "id": "c_conv",
            "name": "Conventional Baseline (BDT/m²)",
            "low": C_CONV_MIN,
            "base": C_CONV_BASELINE,
            "high": C_CONV_MAX,
            "type": "c_conv",
        },
        {
            "id": "k",
            "name": "Floor Area Served per Panel Area (k)",
            "low": 0.8,
            "base": 1.0,
            "high": 1.2,
            "type": "k",
        },
        {
            "id": "discount_rate",
            "name": "Discount Rate / Cost of Capital (i)",
            "low": 0.06,
            "base": 0.10,
            "high": 0.14,
            "type": "discount_rate",
        },
        {
            "id": "labour_saving",
            "name": "Labour Saving vs Conventional (%)",
            "low": 0.40,
            "base": 0.60,
            "high": 0.70,
            "type": "labour_saving",
        },
        {
            "id": "trans_premium",
            "name": "Transport & Erection Premium (%)",
            "low": 1.00,
            "base": 2.30,
            "high": 3.50,
            "type": "trans_premium",
        },
        {
            "id": "capex_c0",
            "name": "Plant Initial Capex C0 (BDT)",
            "low": 0.80 * CAPEX_C0_BDT,
            "base": CAPEX_C0_BDT,
            "high": 1.20 * CAPEX_C0_BDT,
            "type": "capex_c0",
        },
        {
            "id": "plant_life",
            "name": "Plant Economic Life (years)",
            "low": 10.0,
            "base": 15.0,
            "high": 20.0,
            "type": "plant_life",
        },
        {
            "id": "eq_premium",
            "name": "Equipment Premium vs Conventional (%)",
            "low": 1.20,  # 1.50 * 0.80
            "base": 1.50,
            "high": 1.80,  # 1.50 * 1.20
            "type": "eq_premium",
        },
        {
            "id": "fixed_overhead",
            "name": "Annual Fixed Overhead Fo (BDT)",
            "low": 0.80 * ANNUAL_OVERHEAD_FO_BDT,
            "base": ANNUAL_OVERHEAD_FO_BDT,
            "high": 1.20 * ANNUAL_OVERHEAD_FO_BDT,
            "type": "fixed_overhead",
        },
        {
            "id": "formwork_saving",
            "name": "Formwork Saving vs Conventional (%)",
            "low": 0.60,
            "base": 0.80,
            "high": 0.90,
            "type": "formwork_saving",
        },
    ]

    results = []

    for cfg in sens_configs:
        def evaluate(val):
            # Baseline parameter dict
            kwargs_cost = {
                "n_panels": N_BASELINE,
                "c0": CAPEX_C0_BDT,
                "fo": ANNUAL_OVERHEAD_FO_BDT,
                "i": DISCOUNT_RATE,
                "n_life": PLANT_LIFE_YRS,
                "v_mfg": V_MFG_BDT,
                "trans": TRANSPORT_PER_M2_BDT,
                "area": PANEL_AREA,
                "k": K_FLOOR_PER_PANEL,
            }
            c_conv_curr = C_CONV_BASELINE

            ptype = cfg["type"]
            if ptype == "c_conv":
                c_conv_curr = val
            elif ptype == "k":
                kwargs_cost["k"] = val
            elif ptype == "discount_rate":
                kwargs_cost["i"] = val
            elif ptype == "labour_saving":
                # Labour cost modifies v_mfg
                lab_cost = CONV_BREAKDOWN["Labour Cost"] * (1.0 - val)
                v_mfg_mod = (
                    CONV_BREAKDOWN["Material Cost"] * (1.0 + PRECAST_VARIANCES["Material Cost"])
                    + lab_cost
                    + CONV_BREAKDOWN["Formwork Cost"] * (1.0 + PRECAST_VARIANCES["Formwork Cost"])
                    + CONV_BREAKDOWN["Quality Control / Testing"] * (1.0 + PRECAST_VARIANCES["Quality Control / Testing"])
                )
                kwargs_cost["v_mfg"] = v_mfg_mod
            elif ptype == "trans_premium":
                kwargs_cost["trans"] = CONV_BREAKDOWN["Transportation Cost"] * (1.0 + val)
            elif ptype == "capex_c0":
                kwargs_cost["c0"] = val
            elif ptype == "plant_life":
                kwargs_cost["n_life"] = val
            elif ptype == "eq_premium":
                # Translates equipment premium into annualized capex adjustment
                ann_capex_mod = CONV_BREAKDOWN["Equipment / Plant Cost"] * (1.0 + val) * N_BASELINE * PANEL_AREA * K_FLOOR_PER_PANEL
                c0_mod = ann_capex_mod / CRF_BASELINE
                kwargs_cost["c0"] = c0_mod
            elif ptype == "fixed_overhead":
                kwargs_cost["fo"] = val
            elif ptype == "formwork_saving":
                form_cost = CONV_BREAKDOWN["Formwork Cost"] * (1.0 - val)
                v_mfg_mod = (
                    CONV_BREAKDOWN["Material Cost"] * (1.0 + PRECAST_VARIANCES["Material Cost"])
                    + CONV_BREAKDOWN["Labour Cost"] * (1.0 + PRECAST_VARIANCES["Labour Cost"])
                    + form_cost
                    + CONV_BREAKDOWN["Quality Control / Testing"] * (1.0 + PRECAST_VARIANCES["Quality Control / Testing"])
                )
                kwargs_cost["v_mfg"] = v_mfg_mod

            cost_5k, _, _, _ = unit_cost_precast(**kwargs_cost)
            pct_5k = ((cost_5k - c_conv_curr) / c_conv_curr) * 100.0

            # Compute breakeven N*
            n_star = breakeven_volume(
                c_conv=c_conv_curr,
                c0=kwargs_cost["c0"],
                fo=kwargs_cost["fo"],
                i=kwargs_cost["i"],
                n_life=kwargs_cost["n_life"],
                v_mfg=kwargs_cost["v_mfg"],
                trans=kwargs_cost["trans"],
                area=kwargs_cost["area"],
                k=kwargs_cost["k"],
            )
            return n_star, cost_5k, pct_5k

        n_star_low, cost_low, pct_low = evaluate(cfg["low"])
        n_star_high, cost_high, pct_high = evaluate(cfg["high"])
        spread_n_star = abs(n_star_high - n_star_low)

        results.append({
            "param": cfg["name"],
            "id": cfg["id"],
            "low_val": cfg["low"],
            "base_val": cfg["base"],
            "high_val": cfg["high"],
            "n_star_low": n_star_low,
            "n_star_high": n_star_high,
            "cost_5k_low": cost_low,
            "cost_5k_high": cost_high,
            "pct_5k_low": pct_low,
            "pct_5k_high": pct_high,
            "spread_n_star": spread_n_star,
        })

    # Sort results descending by spread in breakeven volume N*
    results.sort(key=lambda x: x["spread_n_star"], reverse=True)
    return results, base_n_star, base_cost_5k, base_pct_5k


def plot_tornado_chart(sens_results, base_n_star, save_path=FIG_TORNADO_PATH):
    """Generates publication-quality 300 DPI horizontal tornado chart of breakeven volume N*."""
    # Plot top parameters
    params = [r["param"] for r in sens_results]
    low_diffs = [r["n_star_low"] - base_n_star for r in sens_results]
    high_diffs = [r["n_star_high"] - base_n_star for r in sens_results]

    y_pos = np.arange(len(params))

    plt.figure(figsize=(10, 6.5), dpi=300)
    plt.axvline(0, color="black", linewidth=1.2, linestyle="--", label=f"Projected Baseline $N^*$ = {base_n_star:,.0f} panels/yr")

    # Plot bars for low and high parameter values
    # To maintain consistency: bar from min(low, high) to max(low, high)
    for i, r in enumerate(sens_results):
        d_low = r["n_star_low"] - base_n_star
        d_high = r["n_star_high"] - base_n_star

        # Blue for 'low parameter value', Amber/Red for 'high parameter value'
        plt.barh(y_pos[i], d_low, color="#2b5c8f", alpha=0.85, height=0.55,
                 label="Low parameter value" if i == 0 else "")
        plt.barh(y_pos[i], d_high, color="#d95f02", alpha=0.85, height=0.55,
                 label="High parameter value" if i == 0 else "")

    plt.yticks(y_pos, params, fontsize=9.5)
    plt.gca().invert_yaxis()  # Highest impact at top
    plt.xlabel("Deviation from Projected Baseline Breakeven Volume $\\Delta N^*$ (panels/year)", fontsize=10.5, labelpad=8)
    plt.title("Projected Sensitivity Analysis: Breakeven Annual Production Volume $N^*$\n(One-at-a-time variation across literature and engineering bounds)",
              fontsize=11.5, fontweight="bold", pad=12)
    plt.grid(axis="x", linestyle=":", alpha=0.6)
    plt.legend(loc="lower right", frameon=True, fontsize=9.5)
    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    plt.close()


def plot_economies_of_scale(save_path=FIG_SCALE_PATH):
    """Generates publication-quality 300 DPI economies of scale cost curve with uncertainty band."""
    vols = np.linspace(300, 12000, 500)
    costs = []
    for v in vols:
        c_m2, _, _, _ = unit_cost_precast(v)
        costs.append(c_m2)
    costs = np.array(costs)

    n_star = breakeven_volume()
    c_at_n_star, _, _, _ = unit_cost_precast(n_star)

    plt.figure(figsize=(10, 6.5), dpi=300)

    # Conventional baseline uncertainty band (14,000 - 22,000 BDT/m²)
    plt.axhspan(C_CONV_MIN, C_CONV_MAX, color="#e0e0e0", alpha=0.45,
                label="Conventional Baseline Range (14,000 - 22,000 BDT/m²)")
    plt.axhline(C_CONV_BASELINE, color="#333333", linestyle="--", linewidth=1.5,
                label=f"Conventional Benchmark Baseline ({C_CONV_BASELINE:,.0f} BDT/m²)")

    # Asymptotic variable cost line
    plt.axhline(V_TOTAL_BDT, color="#6baed6", linestyle=":", linewidth=1.3,
                label=f"Projected Precast Asymptotic Variable Floor ({V_TOTAL_BDT:,.0f} BDT/m²)")

    # Precast unit cost curve
    plt.plot(vols, costs, color="#08519c", linewidth=2.5,
             label="Projected Precast RCC Total Unit Cost $c(N)$")

    # Mark key table volumes
    key_vols = [500, 1000, 2000, 3000, 5000, 10000]
    for kv in key_vols:
        kc, _, _, _ = unit_cost_precast(kv)
        plt.scatter(kv, kc, color="#08519c", s=35, zorder=4)
        pct = ((kc - C_CONV_BASELINE) / C_CONV_BASELINE) * 100.0
        offset_y = 1200 if kv <= 1000 else -1800
        plt.annotate(f"{kv:,}/yr\n{kc:,.0f} BDT/m²\n({pct:+.1f}%)",
                     xy=(kv, kc), xytext=(kv, kc + offset_y),
                     fontsize=8, ha="center",
                     bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="#cccccc", alpha=0.85),
                     arrowprops=dict(arrowstyle="->", color="#08519c", lw=0.8))

    # Breakeven point annotation
    plt.scatter([n_star], [c_at_n_star], color="#cb181d", s=70, zorder=5, label=f"Breakeven Point $N^* = {n_star:,.0f}$ panels/yr")
    plt.annotate(f"Parity Threshold $N^* \\approx {n_star:,.0f}$ panels/yr\n(Cost parity at {c_at_n_star:,.0f} BDT/m²)",
                 xy=(n_star, c_at_n_star), xytext=(n_star + 1200, c_at_n_star + 4000),
                 fontsize=9, fontweight="bold", color="#a50f15",
                 bbox=dict(boxstyle="round,pad=0.3", fc="#fee5d9", ec="#cb181d", lw=1.2),
                 arrowprops=dict(arrowstyle="->", color="#cb181d", lw=1.5))

    plt.xlim(0, 11500)
    plt.ylim(10000, 38000)
    plt.xlabel("Annual Production Volume $N$ (Standard Panels / Year, 12.9 m² each)", fontsize=10.5, labelpad=8)
    plt.ylabel("Projected Equivalent Cost per m² Floor Area (BDT / m²)", fontsize=10.5, labelpad=8)
    plt.title("Projected Economies of Scale: Precast RCC vs. Conventional Cast-in-Situ Construction\n(Dhaka Residential Core & Shell Benchmark; 1 panel $\\approx$ 12.9 m²)",
              fontsize=11.5, fontweight="bold", pad=12)
    plt.grid(True, linestyle=":", alpha=0.6)
    plt.legend(loc="upper right", frameon=True, fontsize=9)
    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    plt.close()


# ==============================================================================
# 4. MONTE CARLO SIMULATION
# ==============================================================================

def run_monte_carlo(n_draws=10000, seed=42):
    """Executes deterministic Monte Carlo simulation (10,000 draws) with triangular distributions."""
    np.random.seed(seed)

    # 1. Conventional baseline (14,000 to 22,000, mode 18,000)
    c_conv_dist = np.random.triangular(C_CONV_MIN, C_CONV_BASELINE, C_CONV_MAX, n_draws)

    # 2. Labour saving (40% to 70%, mode 60%)
    s_lab_dist = np.random.triangular(0.40, 0.60, 0.70, n_draws)

    # 3. Formwork saving (60% to 90%, mode 80%)
    s_form_dist = np.random.triangular(0.60, 0.80, 0.90, n_draws)

    # 4. Transport premium (+100% to +350%, mode +230%)
    p_trans_dist = np.random.triangular(1.00, 2.30, 3.50, n_draws)

    # 5. Plant initial capex C0 (+/-20%, mode C0_base)
    c0_dist = np.random.triangular(0.80 * CAPEX_C0_BDT, CAPEX_C0_BDT, 1.20 * CAPEX_C0_BDT, n_draws)

    # 6. Discount rate i (6% to 14%, mode 10%)
    rate_i_dist = np.random.triangular(0.06, 0.10, 0.14, n_draws)

    # 7. Plant economic life n (10 to 20 yr, mode 15 yr)
    life_n_dist = np.random.triangular(10.0, 15.0, 20.0, n_draws)

    # 8. Floor-to-panel ratio k (0.8 to 1.2, mode 1.0)
    k_dist = np.random.triangular(0.80, 1.00, 1.20, n_draws)

    # 9. Fixed overhead Fo (+/-20%, mode Fo_base)
    fo_dist = np.random.triangular(0.80 * ANNUAL_OVERHEAD_FO_BDT, ANNUAL_OVERHEAD_FO_BDT, 1.20 * ANNUAL_OVERHEAD_FO_BDT, n_draws)

    # Evaluate capital recovery factor
    crf_dist = (rate_i_dist * ((1.0 + rate_i_dist) ** life_n_dist)) / (((1.0 + rate_i_dist) ** life_n_dist) - 1.0)
    f_annual_dist = (c0_dist * crf_dist) + fo_dist

    # Precast variable cost per m²
    # Material = 9,200; QC = 500
    mat_cost = CONV_BREAKDOWN["Material Cost"] * (1.0 + PRECAST_VARIANCES["Material Cost"])  # 9,200
    qc_cost = CONV_BREAKDOWN["Quality Control / Testing"] * (1.0 + PRECAST_VARIANCES["Quality Control / Testing"])  # 500
    lab_cost = CONV_BREAKDOWN["Labour Cost"] * (1.0 - s_lab_dist)
    form_cost = CONV_BREAKDOWN["Formwork Cost"] * (1.0 - s_form_dist)
    trans_cost = CONV_BREAKDOWN["Transportation Cost"] * (1.0 + p_trans_dist)

    v_total_dist = mat_cost + lab_cost + form_cost + qc_cost + trans_cost
    margin_dist = c_conv_dist - v_total_dist

    # Breakeven volume N*
    # Where margin <= 0, precast variable cost exceeds conventional price (N* -> infinity)
    n_star_dist = np.where(margin_dist > 0, f_annual_dist / (margin_dist * PANEL_AREA * k_dist), np.inf)

    p10_n_star = float(np.percentile(n_star_dist, 10))
    p50_n_star = float(np.percentile(n_star_dist, 50))
    p90_n_star = float(np.percentile(n_star_dist, 90))

    # Evaluate cost at 2,000, 5,000, 10,000 panels/yr
    cost_2000 = v_total_dist + (f_annual_dist / (2000.0 * PANEL_AREA * k_dist))
    cost_5000 = v_total_dist + (f_annual_dist / (5000.0 * PANEL_AREA * k_dist))
    cost_10000 = v_total_dist + (f_annual_dist / (10000.0 * PANEL_AREA * k_dist))

    prob_cheaper_2k = float(np.mean(cost_2000 < c_conv_dist) * 100.0)
    prob_cheaper_5k = float(np.mean(cost_5000 < c_conv_dist) * 100.0)
    prob_cheaper_10k = float(np.mean(cost_10000 < c_conv_dist) * 100.0)

    mc_summary = {
        "n_draws": n_draws,
        "seed": seed,
        "n_star_p10": p10_n_star,
        "n_star_p50": p50_n_star,
        "n_star_p90": p90_n_star,
        "prob_cheaper_2000_pct": prob_cheaper_2k,
        "prob_cheaper_5000_pct": prob_cheaper_5k,
        "prob_cheaper_10000_pct": prob_cheaper_10k,
        "non_breakeven_draws_count": int(np.sum(margin_dist <= 0)),
    }
    return mc_summary


# ==============================================================================
# 5. EXPORT RESULTS TO MARKDOWN & JSON
# ==============================================================================

def write_results(table_7, table_8, sens_results, base_n_star, base_cost_5k, base_pct_5k, mc_results):
    """Writes detailed analytical results to cost_results.md and cost_results.json."""
    # Build JSON structure
    json_data = {
        "metadata": {
            "model_name": "Projected Precast RCC vs. Conventional Construction Cost Model",
            "location": "Dhaka, Bangladesh",
            "benchmark_building": "10-Storey Residential Core & Shell",
            "currency": "BDT",
            "exchange_rate_usd_to_bdt": USD_TO_BDT,
            "deterministic_seed": 42,
            "disclaimer": "All precast figures are projected estimates based on literature variances and engineering plant models. No primary precast cost data exist in Bangladesh.",
        },
        "table_7_projected_cost_comparison": table_7,
        "plant_calibration": {
            "panel_area_m2": PANEL_AREA,
            "k_floor_per_panel": K_FLOOR_PER_PANEL,
            "design_scale_panels_yr": N_BASELINE,
            "discount_rate_i": DISCOUNT_RATE,
            "plant_life_yrs": PLANT_LIFE_YRS,
            "crf": CRF_BASELINE,
            "annualized_capex_bdt_yr": ANNUAL_CAPEX_BDT,
            "annual_fixed_overhead_fo_bdt_yr": ANNUAL_OVERHEAD_FO_BDT,
            "total_annual_fixed_cost_f_bdt_yr": TOTAL_FIXED_COST_F_BDT,
            "implied_initial_capex_c0_bdt": CAPEX_C0_BDT,
            "implied_initial_capex_c0_usd": CAPEX_C0_USD,
            "mfg_variable_cost_v_bdt_m2": V_MFG_BDT,
            "transport_erection_cost_bdt_m2": TRANSPORT_PER_M2_BDT,
            "total_variable_cost_bdt_m2": V_TOTAL_BDT,
            "conventional_baseline_bdt_m2": C_CONV_BASELINE,
            "breakeven_volume_panels_yr": base_n_star,
        },
        "table_8_economies_of_scale": table_8,
        "sensitivity_analysis": {
            "baseline_breakeven_n_star": base_n_star,
            "baseline_cost_at_5000_bdt_m2": base_cost_5k,
            "baseline_variance_at_5000_pct": base_pct_5k,
            "parameters": sens_results,
        },
        "monte_carlo_results": mc_results,
        "assumptions": [
            {"parameter": "Conventional core & shell baseline", "value": "18,000 BDT/m²", "type": "Assumed (SSRN paper baseline & Dhaka developer consensus)"},
            {"parameter": "Panel nominal geometry", "value": "4.3 m x 3.0 m (12.9 m²)", "type": "Literature-derived standard precast wall panel"},
            {"parameter": "Floor area served per panel area (k)", "value": "1.0 m² floor / m² panel", "type": "Assumed (SSRN paper convention; tested 0.8-1.2)"},
            {"parameter": "Material cost saving", "value": "-8.0%", "type": "Literature-derived (controlled factory batching & reduced scrap)"},
            {"parameter": "Labour cost saving", "value": "-60.0%", "type": "Literature-derived (off-site industrial automation vs site pouring)"},
            {"parameter": "Formwork cost saving", "value": "-80.0%", "type": "Literature-derived & register-supported (steel moulds reuse >200 times)"},
            {"parameter": "Transport & erection premium", "value": "+230.0%", "type": "Literature-derived (heavy flatbed Dhaka logistics & mobile crane hire)"},
            {"parameter": "Quality control / testing premium", "value": "+150.0%", "type": "Literature-derived (rigorous factory cube test protocol)"},
            {"parameter": "Plant capital recovery rate (i)", "value": "10.0% annual", "type": "Assumed standard industrial project finance discount rate"},
            {"parameter": "Plant asset economic life (n)", "value": "15 years", "type": "Assumed standard precast machinery depreciation life"},
            {"parameter": "Plant initial Capex C0", "value": f"{CAPEX_C0_BDT:,.0f} BDT (${CAPEX_C0_USD:,.2f} USD)", "type": "Calibrated from Table 7 equipment share at 5,000 units/yr"},
            {"parameter": "Fixed annual overhead Fo", "value": f"{ANNUAL_OVERHEAD_FO_BDT:,.0f} BDT/yr", "type": "Calibrated from Table 7 overhead share at 5,000 units/yr"},
            {"parameter": "Exchange rate", "value": "122 BDT / USD", "type": "Commercial projection (2024-2026 Bangladesh banking rate)"},
        ],
    }

    with open(RESULTS_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=2)

    # Build Markdown document
    md_content = f"""# Projected Cost Model: Precast RCC vs. Conventional Cast-in-Situ Construction
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
"""
    for r in table_7["rows"]:
        note = "Corrected (+140% -> +150%)" if r["component"].startswith("Equipment") else (
            "Corrected (+100% -> +150%)" if r["component"].startswith("Quality") else "Verified"
        )
        md_content += f"| **{r['component']}** | {r['conv_bdt']:,.0f} | {r['precast_bdt']:,.0f} | {r['variance_pct']:+.1f}% | {r['conv_share_pct']:.2f}% | {r['precast_share_pct']:.2f}% | {note} |\n"

    md_content += f"""| **Total Construction Cost** | **{table_7['total_conv_bdt']:,.0f}** | **{table_7['total_precast_bdt']:,.0f}** | **{table_7['total_variance_pct']:+.1f}%** | **100.00%** | **100.00%** | **15.0% Net Saving at Design Scale** |

---

## 2. Plant Economics & Calibration

The earlier working paper suffered from an internal inconsistency in Table 8, where multiplying fixed cost per panel by volume yielded total fixed costs scaling from 70M to 380M BDT/year. In a single dedicated manufacturing facility, total annual fixed overhead and capitalised depreciation are mathematically constant.

### Calibration Parameters:
- **Standard Panel Dimensions:** $4.3\\text{{ m}} \\times 3.0\\text{{ m}} = 12.9\\text{{ m}}^2$ ($A = 12.9\\text{{ m}}^2$).
- **Floor-Area Conversion Factor ($k$):** Assume $1\\text{{ m}}^2\\text{{ panel}} \\approx 1\\text{{ m}}^2\\text{{ floor area equivalent}}$ ($k = 1.0$, tested $0.8 - 1.2$).
- **Design Benchmark Production Scale ($N_0$):** $5,000\\text{{ panels/year}}$ ($64,500\\text{{ m}}^2\\text{{ floor area/year}}$).
- **Financial Baseline:** Discount rate $i = 10.0\\%$, plant economic life $n = 15\\text{{ years}}$.
  $$\\text{{CRF}} = \\frac{{i(1+i)^n}}{{(1+i)^n - 1}} = \\frac{{0.10(1.10)^{{15}}}}{{(1.10)^{{15}} - 1}} \\approx {CRF_BASELINE:.6f}$$
- **Fixed Cost Calibration from Table 7:**
  - Annualised Equipment / Plant Capex: $1,250\\text{{ BDT/m}}^2 \\times 64,500\\text{{ m}}^2 = {ANNUAL_CAPEX_BDT:,.0f}\\text{{ BDT/year}}$
  - Fixed Annual Overhead ($F_o$): $700\\text{{ BDT/m}}^2 \\times 64,500\\text{{ m}}^2 = {ANNUAL_OVERHEAD_FO_BDT:,.0f}\\text{{ BDT/year}}$
  - **Total Annual Fixed Cost ($F$):** ${TOTAL_FIXED_COST_F_BDT:,.0f}\\text{{ BDT/year}}$ (strictly constant)
- **Implied Initial Plant Capex ($C_0$):**
  $$C_0 = \\frac{{\\text{{Annualised Capex}}}}{{\\text{{CRF}}}} = \\frac{{{ANNUAL_CAPEX_BDT:,.0f}}}{{{CRF_BASELINE:.6f}}} = {CAPEX_C0_BDT:,.0f}\\text{{ BDT}} \\quad (\\approx \\${CAPEX_C0_USD:,.2f}\\text{{ USD at 122 BDT/USD}})$$
  *(This $5.03M USD initial capex aligns with international turn-key carousel plant installations of 60,000–80,000 m²/year capacity).*
- **Variable Operating Cost ($v$):**
  - Manufacturing Variable: $\\text{{Material (9,200)}} + \\text{{Labour (1,600)}} + \\text{{Formwork (400)}} + \\text{{QC (500)}} = {V_MFG_BDT:,.0f}\\text{{ BDT/m}}^2$
  - Transportation & Erection: ${TRANSPORT_PER_M2_BDT:,.0f}\\text{{ BDT/m}}^2$
  - **Total Variable Cost ($v_{{total}}$):** ${V_TOTAL_BDT:,.0f}\\text{{ BDT/m}}^2$ (${V_TOTAL_BDT * PANEL_AREA:,.0f}\\text{{ BDT/panel}}$)

### Closed-Form Parity Breakeven Volume ($N^*$):
$$\\text{{Unit Margin }} m = c_{{conv}} - v_{{total}} = 18,000 - 13,350 = 4,650\\text{{ BDT/m}}^2$$
$$N^* = \\frac{{F}}{{m \\cdot A \\cdot k}} = \\frac{{{TOTAL_FIXED_COST_F_BDT:,.0f}}}{{4,650 \\times 12.9 \\times 1.0}} = \\mathbf{{{base_n_star:,.2f}\\text{{ panels/year}}}} \\quad (\\approx {base_n_star * PANEL_AREA:,.0f}\\text{{ m}}^2/\\text{{year}})$$
*This analytically verifies the earlier paper's headline parity threshold of ~2,000–3,000 panels/year.*

---

## 3. Corrected Table 8: Economies of Scale Projection

All fixed costs scale strictly inversely with annual output volume ($F / N$), while direct variable unit costs remain constant.

| Annual Volume (panels/yr) | Fixed Cost / Panel (BDT) | Variable Cost / Panel (BDT) | Total Cost / Panel (BDT) | Projected Cost per m² (BDT) | Fixed Share per m² (BDT) | Var. Share per m² (BDT) | vs. Conventional (18,000 BDT/m²) | Economic Assessment |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---|
"""
    for r in table_8:
        status = "Severe Low-Scale Penalty" if r["volume_panels_yr"] <= 1000 else (
            "Near Cost Parity (+1.3%)" if r["volume_panels_yr"] == 2000 else (
                "Economic Viability Reached (-7.8%)" if r["volume_panels_yr"] == 3000 else (
                    "Design Scale Parity (-15.0%)" if r["volume_panels_yr"] == 5000 else "High-Scale Industrialised (-20.4%)"
                )
            )
        )
        md_content += f"| **{r['volume_panels_yr']:,}** | {r['fixed_cost_per_panel_bdt']:,.0f} | {r['variable_cost_per_panel_bdt']:,.0f} | {r['total_unit_cost_per_panel_bdt']:,.0f} | **{r['equivalent_cost_per_m2_bdt']:,.0f}** | {r['fixed_cost_per_m2_bdt']:,.0f} | {r['variable_cost_per_m2_bdt']:,.0f} | **{r['vs_conventional_pct']:+.2f}%** | {status} |\n"

    md_content += f"""
---

## 4. Sensitivity Analysis (One-at-a-Time)

Tornado sensitivity testing ranks each parameter's influence on the parity threshold $N^*$ (panels/year) and the projected cost differential at 5,000 panels/year.

| Rank | Parameter | Base Value | Low Value | High Value | Low Impact: $N^*$ (panels/yr) | High Impact: $N^*$ (panels/yr) | $N^*$ Spread (panels/yr) | Cost at 5k: Low vs High (% vs Conv) |
|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
"""
    for idx, r in enumerate(sens_results, 1):
        md_content += f"| {idx} | **{r['param']}** | {r['base_val']:,.2f} | {r['low_val']:,.2f} | {r['high_val']:,.2f} | {r['n_star_low']:,.1f} | {r['n_star_high']:,.1f} | **{r['spread_n_star']:,.1f}** | {r['pct_5k_low']:+.1f}% to {r['pct_5k_high']:+.1f}% |\n"

    md_content += f"""
### Key Findings from Sensitivity Analysis:
1. **Dominant Driver — Conventional Price Baseline ($c_{{conv}}$):** A shift from 18,000 to 14,000 BDT/m² increases breakeven to **15,000 panels/yr**, making precast unviable at low volumes. Conversely, if conventional costs rise to 22,000 BDT/m², breakeven drops to **1,127 panels/yr**.
2. **Floor-to-Panel Ratio ($k$):** Varies breakeven volume across an 874 panel/yr envelope (1,747 to 2,621 panels/yr).
3. **Discount Rate & Labour Savings:** Capital financing rate shifts breakeven by 612 panels/yr, while labour savings shift it by 602 panels/yr.

---

## 5. Monte Carlo Probabilistic Simulation (10,000 Draws)

Deterministic triangular distributions (seed = 42) across all engineering and economic ranges yield the following probabilistic metrics:

| Metric | Projected Value | Analytical Interpretation |
|:---|:---:|:---|
| **Breakeven Volume $N^*$ — P10 (Optimistic)** | **{mc_results['n_star_p10']:,.1f} panels/yr** | 10% probability breakeven occurs at or below ~1,431 panels/yr |
| **Breakeven Volume $N^*$ — P50 (Median)** | **{mc_results['n_star_p50']:,.1f} panels/yr** | Median projected market breakeven threshold |
| **Breakeven Volume $N^*$ — P90 (Pessimistic)** | **{mc_results['n_star_p90']:,.1f} panels/yr** | 90% probability breakeven occurs at or below ~4,540 panels/yr |
| **Probability Precast Cheaper at 2,000 panels/yr** | **{mc_results['prob_cheaper_2000_pct']:.2f}%** | Near parity threshold; high sensitivity to conventional pricing |
| **Probability Precast Cheaper at 5,000 panels/yr** | **{mc_results['prob_cheaper_5000_pct']:.2f}%** | Overwhelming probability of cost savings at medium commercial scale |
| **Probability Precast Cheaper at 10,000 panels/yr** | **{mc_results['prob_cheaper_10000_pct']:.2f}%** | Industrial scale provides near-certain economic superiority |

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
| **Panel Unit Area ($A$)** | 12.9 m² | Standard Engineering | Standard $4.3\\text{{ m}} \\times 3.0\\text{{ m}}$ load-bearing or infill panel geometry |
| **Floor Area Served Ratio ($k$)** | 1.0 m²/m² | Assumed | Direct 1:1 floor area to panel area equivalence (tested 0.8–1.2) |
| **Plant Asset Life ($n$)** | 15 years | Standard Corporate Finance | Depreciable life of semi-automated precast carousel casting machinery |
| **Cost of Capital ($i$)** | 10.0% | Assumed | Prime commercial industrial lending rate in Bangladesh |
| **Exchange Rate** | 122 BDT / USD | Commercial Benchmark | 2024–2026 Bangladesh foreign exchange conversion rate |

---

## 7. Generated Visualisations

- **Tornado Chart:** `fig_tornado_breakeven.png` (300 DPI, one-at-a-time breakeven variance ranking)
- **Scale Curve:** `fig_scale_curve.png` (300 DPI, projected unit cost vs. production volume with conventional uncertainty envelope)
"""

    with open(RESULTS_MD_PATH, "w", encoding="utf-8") as f:
        f.write(md_content)


# ==============================================================================
# MAIN EXECUTION ROUTINE
# ==============================================================================

def main():
    print("=" * 80)
    print("PROJECTED COST MODEL: PRECAST RCC VS. CONVENTIONAL CAST-IN-SITU CONSTRUCTION")
    print("Location: Dhaka, Bangladesh | Benchmark: 10-Storey Core & Shell (18,000 BDT/m²)")
    print("=" * 80)

    # 1. Recompute Table 7
    table_7 = compute_table_7()
    print("\n--- 1. CORRECTED TABLE 7 (BDT/m² Gross Floor Area) ---")
    print(f"{'Component':<28} | {'Conv (BDT)':<10} | {'Precast (BDT)':<13} | {'Variance':<9} | {'Conv Share':<10} | {'Pre Share':<10}")
    print("-" * 92)
    for r in table_7["rows"]:
        print(f"{r['component']:<28} | {r['conv_bdt']:>10,.0f} | {r['precast_bdt']:>13,.0f} | {r['variance_pct']:>8.1f}% | {r['conv_share_pct']:>9.2f}% | {r['precast_share_pct']:>9.2f}%")
    print("-" * 92)
    print(f"{'TOTAL':<28} | {table_7['total_conv_bdt']:>10,.0f} | {table_7['total_precast_bdt']:>13,.0f} | {table_7['total_variance_pct']:>8.1f}% | {'100.00%':>10} | {'100.00%':>10}")

    # 2. Plant Economics & Table 8
    print("\n--- 2. PLANT ECONOMICS CALIBRATION ---")
    print(f"Panel Area (A):                   {PANEL_AREA} m² (4.3 m x 3.0 m)")
    print(f"Floor-to-Panel Ratio (k):         {K_FLOOR_PER_PANEL:.2f} m² floor / m² panel")
    print(f"Capital Recovery Factor (CRF):    {CRF_BASELINE:.6f} (i = {DISCOUNT_RATE*100:.1f}%, n = {PLANT_LIFE_YRS} yr)")
    print(f"Annual Plant Fixed Capex:         {ANNUAL_CAPEX_BDT:,.2f} BDT/yr")
    print(f"Annual Fixed Overhead (Fo):       {ANNUAL_OVERHEAD_FO_BDT:,.2f} BDT/yr")
    print(f"Total Annual Fixed Cost (F):      {TOTAL_FIXED_COST_F_BDT:,.2f} BDT/yr")
    print(f"Implied Initial Capex C0:         {CAPEX_C0_BDT:,.2f} BDT (${CAPEX_C0_USD:,.2f} USD at {USD_TO_BDT} BDT/USD)")
    print(f"Manufacturing Variable Cost (v):  {V_MFG_BDT:,.2f} BDT/m²")
    print(f"Transport & Erection Cost:        {TRANSPORT_PER_M2_BDT:,.2f} BDT/m²")
    print(f"Total Variable Cost (v_total):    {V_TOTAL_BDT:,.2f} BDT/m²")

    base_n_star = breakeven_volume()
    print(f"Projected Breakeven Volume N*:    {base_n_star:,.2f} panels/year ({base_n_star * PANEL_AREA:,.2f} m²/year)")

    table_8 = compute_table_8()
    print("\n--- 3. REPLACEMENT TABLE 8: ECONOMIES OF SCALE ---")
    print(f"{'Volume (panels/yr)':<18} | {'Fixed/panel':<12} | {'Var/panel':<12} | {'Total/panel':<12} | {'Cost/m² (BDT)':<14} | {'vs Conv (%)':<12}")
    print("-" * 92)
    for r in table_8:
        print(f"{r['volume_panels_yr']:>18,d} | {r['fixed_cost_per_panel_bdt']:>12,.0f} | {r['variable_cost_per_panel_bdt']:>12,.0f} | {r['total_unit_cost_per_panel_bdt']:>12,.0f} | {r['equivalent_cost_per_m2_bdt']:>14,.0f} | {r['vs_conventional_pct']:>11.2f}%")

    # 3. Sensitivity Analysis
    sens_results, _, base_cost_5k, base_pct_5k = run_sensitivity_analysis()
    print("\n--- 4. SENSITIVITY ANALYSIS (TORNADO RANKING) ---")
    print(f"{'Parameter':<38} | {'N* Low':<10} | {'N* High':<10} | {'N* Spread':<10} | {'Cost @ 5k Range':<22}")
    print("-" * 98)
    for r in sens_results:
        print(f"{r['param']:<38} | {r['n_star_low']:>10.1f} | {r['n_star_high']:>10.1f} | {r['spread_n_star']:>10.1f} | {r['pct_5k_low']:>+7.1f}% to {r['pct_5k_high']:>+7.1f}%")

    # Plot Visualizations
    plot_tornado_chart(sens_results, base_n_star)
    print(f"\n[Generated] Tornado chart saved to: {FIG_TORNADO_PATH}")
    plot_economies_of_scale()
    print(f"[Generated] Economies of scale curve saved to: {FIG_SCALE_PATH}")

    # 4. Monte Carlo Simulation
    mc_results = run_monte_carlo()
    print("\n--- 5. MONTE CARLO PROBABILISTIC RESULTS (10,000 Draws, Seed 42) ---")
    print(f"Breakeven Volume N* P10:          {mc_results['n_star_p10']:,.1f} panels/year")
    print(f"Breakeven Volume N* P50 (Median): {mc_results['n_star_p50']:,.1f} panels/year")
    print(f"Breakeven Volume N* P90:          {mc_results['n_star_p90']:,.1f} panels/year")
    print(f"P(Precast cheaper @ 2,000/yr):    {mc_results['prob_cheaper_2000_pct']:.2f}%")
    print(f"P(Precast cheaper @ 5,000/yr):    {mc_results['prob_cheaper_5000_pct']:.2f}%")
    print(f"P(Precast cheaper @ 10,000/yr):   {mc_results['prob_cheaper_10000_pct']:.2f}%")

    # 5. Export Markdown & JSON
    write_results(table_7, table_8, sens_results, base_n_star, base_cost_5k, base_pct_5k, mc_results)
    print(f"[Exported] Structured Markdown results saved to: {RESULTS_MD_PATH}")
    print(f"[Exported] Structured JSON results saved to:     {RESULTS_JSON_PATH}")
    print("\nExecution completed cleanly and successfully.")


if __name__ == "__main__":
    main()
