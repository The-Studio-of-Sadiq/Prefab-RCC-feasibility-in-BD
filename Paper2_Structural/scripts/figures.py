"""Paper 2 figures from exported tables. Run from repo root."""
import csv, os, json
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
A = 'Paper2_Structural/analysis'; OUT = os.path.join(A, 'figures'); os.makedirs(OUT, exist_ok=True)
V = [('M0 cast-in-situ', 'tables_cis_baseline', '#222222', '-'), ('M1 emulative', 'tables_pc_M1', '#1f77b4', '--'),
     ('M2 semi-rigid central', 'tables_pc_M2', '#2ca02c', '-.'), ('M3 semi-rigid low', 'tables_pc_M3', '#ff7f0e', ':'),
     ('M4 dry connections', 'tables_pc_M4', '#d62728', '-')]
Cd, I = 5.0, 1.0
fig, axs = plt.subplots(1, 2, figsize=(9, 5), dpi=300, sharey=True)
for ax, (case, dr) in zip(axs, (('EQx', 'X'), ('EQy', 'Y'))):
    for lab, d, col, ls in V:
        rows = list(csv.DictReader(open(os.path.join(A, d, 'Story Drifts.csv'), encoding='utf-8')))
        mx = {}
        for r in rows:
            if r['OutputCase'] == case and r['Direction'] == dr:
                s = int(r['Story'][5:]); mx[s] = max(mx.get(s, 0), float(r['Drift']) * Cd / I)
        st = sorted(mx); ax.plot([mx[s] * 100 for s in st], st, ls, color=col, lw=1.6, label=lab, marker='o', ms=3)
    ax.axvline(2.0, color='k', lw=1, ls='--'); ax.text(1.97, 9.6, 'BNBC limit 2.0%', ha='right', fontsize=8)
    ax.set_xlabel(f'Design storey drift Cd·δ/I (%)  — {case}'); ax.grid(alpha=.3); ax.set_xlim(0, 2.2)
axs[0].set_ylabel('Storey'); axs[0].set_yticks(range(1, 11)); axs[1].legend(fontsize=7.5, loc='lower right')
fig.tight_layout(); fig.savefig(os.path.join(OUT, 'fig_drift_profiles.png'))
cmp = json.load(open(os.path.join(A, 'variant_comparison.json')))
fig, axs = plt.subplots(1, 3, figsize=(10, 3.6), dpi=300)
labs = [r['variant'] for r in cmp]
axs[0].bar(labs, [r['Ty'] for r in cmp], color='#4c72b0'); axs[0].axhline(0.876, ls='--', c='k', lw=1); axs[0].set_title('Fundamental period Ty (s)', fontsize=9); axs[0].text(0, 0.9, '1.4Ta', fontsize=7)
axs[1].bar(labs, [r['drift_y'] * 100 for r in cmp], color='#dd8452'); axs[1].axhline(2.0, ls='--', c='k', lw=1); axs[1].set_title('Max design drift, EQy (%)', fontsize=9)
axs[2].bar(labs, [r['wall_share_y'] * 100 for r in cmp], color='#55a868'); axs[2].set_ylim(70, 100); axs[2].set_title('Wall share of base shear, Y (%)', fontsize=9)
for a in axs: a.tick_params(labelsize=7); a.grid(axis='y', alpha=.3)
fig.tight_layout(); fig.savefig(os.path.join(OUT, 'fig_variant_summary.png'))
print('figures saved')
