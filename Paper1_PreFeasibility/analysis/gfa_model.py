"""Floor-area (GFA) restatement of the projected precast cost model.

Imports the parameters from cost_model.py and restates throughput in m2 of
gross floor area (GFA) per year, which does not depend on the panel-to-floor
conversion factor k. Panel counts are reported only as a k-dependent range.
All results are PROJECTIONS. Run from the repository root:
    python Paper1_PreFeasibility/analysis/gfa_model.py
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cost_model as cm  # noqa: E402

F = cm.TOTAL_FIXED_COST_F_BDT          # BDT/yr, calibrated at the design scale
V = cm.V_TOTAL_BDT                      # BDT/m2 GFA, manufacturing + transport/erection
C_CONV = cm.C_CONV_BASELINE             # BDT/m2 GFA, assumed
DESIGN_GFA = cm.N_BASELINE * cm.PANEL_AREA * cm.K_FLOOR_PER_PANEL  # 64,500 m2/yr
BUILDING_GFA = 20.0 * 15.0 * 10        # 3,000 m2: 20 m x 15 m, 10 storeys (repo ETABS model)

# Panel area needed per m2 of GFA for a large-panel residential building.
# 1/k = 2.0-3.0 m2 of panel per m2 floor (slabs + bearing/shear walls) -> k = 0.33-0.50.
K_RANGE = (1 / 3.0, 1 / 2.0)


def cost_at(q_gfa):
    return V + F / q_gfa


q_star = F / (C_CONV - V)

rows = []
for q in (6_450, 12_900, 25_800, 38_700, 64_500, 129_000):
    c = cost_at(q)
    rows.append({
        "gfa_per_yr": q,
        "buildings_3000m2": q / BUILDING_GFA,
        "cost_bdt_m2": c,
        "vs_conv_pct": 100 * (c / C_CONV - 1),
        "panels_k_low": q / (cm.PANEL_AREA * K_RANGE[0]),
        "panels_k_high": q / (cm.PANEL_AREA * K_RANGE[1]),
    })

# Monte Carlo in GFA units (k removed: it does not affect GFA-based results).
rng = np.random.default_rng(42)
n = 10_000
tri = rng.triangular
c_conv = tri(cm.C_CONV_MIN, C_CONV, cm.C_CONV_MAX, n)
s_lab = tri(0.40, 0.60, 0.70, n)
s_form = tri(0.60, 0.80, 0.90, n)
p_trans = tri(1.00, 2.30, 3.50, n)
c0 = tri(0.8 * cm.CAPEX_C0_BDT, cm.CAPEX_C0_BDT, 1.2 * cm.CAPEX_C0_BDT, n)
i = tri(0.06, 0.10, 0.14, n)
life = tri(10.0, 15.0, 20.0, n)
fo = tri(0.8 * cm.ANNUAL_OVERHEAD_FO_BDT, cm.ANNUAL_OVERHEAD_FO_BDT, 1.2 * cm.ANNUAL_OVERHEAD_FO_BDT, n)

b = cm.CONV_BREAKDOWN
# Variable cost per m2 GFA: materials, labour, formwork, QC (manufacturing) + transport.
v_mfg = (b["Material Cost"] * 0.92 + b["Labour Cost"] * (1 - s_lab)
         + b["Formwork Cost"] * (1 - s_form) + b["Quality Control / Testing"] * 2.5)
v_tot = v_mfg + b["Transportation Cost"] * (1 + p_trans)
crf = i * (1 + i) ** life / ((1 + i) ** life - 1)
f_ann = c0 * crf + fo
margin = c_conv - v_tot
q_star_mc = np.where(margin > 0, f_ann / margin, np.inf)

mc = {
    "q_star_p10": float(np.percentile(q_star_mc, 10)),
    "q_star_p50": float(np.percentile(q_star_mc, 50)),
    "q_star_p90": float(np.percentile(q_star_mc, 90)),
    "share_no_breakeven": float(np.mean(~np.isfinite(q_star_mc))),
}
for q in (25_800, 64_500, 129_000):
    mc[f"p_cheaper_at_{q}"] = float(np.mean(v_tot + f_ann / q < c_conv))

out = {
    "assumptions": {
        "F_bdt_per_yr": F, "v_total_bdt_m2": V, "c_conv_bdt_m2": C_CONV,
        "design_gfa_m2_yr": DESIGN_GFA, "building_gfa_m2": BUILDING_GFA,
        "k_range_floor_per_panel": K_RANGE,
        "note": "F was calibrated so that Table 7's plant and overhead allowances are recovered "
                "at the design throughput (64,500 m2 GFA/yr). The breakeven therefore follows "
                "from Table 7's assumptions; it is not an independent estimate.",
    },
    "q_star_m2_gfa_per_yr": q_star,
    "q_star_buildings_3000m2": q_star / BUILDING_GFA,
    "q_star_panels_range": [q_star / (cm.PANEL_AREA * k) for k in K_RANGE],
    "scale_table": rows,
    "monte_carlo": mc,
}
path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gfa_results.json")
with open(path, "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=2)

print(f"Breakeven Q* = {q_star:,.0f} m2 GFA/yr = {q_star / BUILDING_GFA:.1f} x 3,000 m2 buildings/yr")
print(f"  panel-equivalents (k=0.33-0.50): {out['q_star_panels_range'][1]:,.0f}-{out['q_star_panels_range'][0]:,.0f} panels/yr")
print("GFA/yr | bldgs | BDT/m2 | vs conv | panels (k=.5-.33)")
for r in rows:
    print(f"{r['gfa_per_yr']:>7,} | {r['buildings_3000m2']:5.1f} | {r['cost_bdt_m2']:7,.0f} | {r['vs_conv_pct']:+6.1f}% | "
          f"{r['panels_k_high']:,.0f}-{r['panels_k_low']:,.0f}")
print("MC:", {k: (round(v) if 'q_star' in k else round(v, 3)) for k, v in mc.items()})

# --- Figure: projected unit cost vs annual floor-area output -------------------
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

q = np.linspace(4_000, 140_000, 600)
fig, ax = plt.subplots(figsize=(9, 5.5), dpi=300)
ax.axhspan(cm.C_CONV_MIN, cm.C_CONV_MAX, color="0.92", label="Assumed conventional range (14,000–22,000 BDT/m²)")
ax.axhline(C_CONV, color="0.25", ls="--", lw=1.2, label="Assumed conventional baseline (18,000 BDT/m²)")
ax.axhline(V, color="#4a90c2", ls=":", lw=1.2, label=f"Projected variable cost floor ({V:,.0f} BDT/m²)")
ax.plot(q, cost_at(q), color="#0b4f9c", lw=2.2, label="Projected precast unit cost")
ax.axvspan(mc["q_star_p10"], mc["q_star_p90"], color="#d9534f", alpha=0.10, label="Simulated parity P10–P90")
ax.plot([q_star], [C_CONV], "o", color="#c0392b", ms=7, label=f"Deterministic parity ≈ {q_star:,.0f} m²/yr")
ax.set_xlim(0, 140_000)
ax.set_ylim(10_000, 36_000)
ax.set_xlabel("Annual plant output (m² gross floor area per year)")
ax.set_ylabel("Projected cost (BDT per m² GFA)")
sec = ax.secondary_xaxis("top", functions=(lambda x: x / BUILDING_GFA, lambda b: b * BUILDING_GFA))
sec.set_xlabel("Equivalent 3,000 m² ten-storey buildings per year")
ax.grid(alpha=0.3)
ax.legend(fontsize=7.5, loc="upper right")
fig.tight_layout()
fig.savefig(os.path.join(os.path.dirname(os.path.abspath(__file__)), "fig_scale_curve_gfa.png"))
print("saved fig_scale_curve_gfa.png")
