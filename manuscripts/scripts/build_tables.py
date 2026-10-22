"""Build every number, table and figure in the manuscript from repo files.

Inputs (all committed or rebuilt by the estimation configs):
  <program>/estimation/results_fixed/<scenario>/estimates.parquet, truth.json
      expansion, ratio, regression (Part D also: pde_expansion, pde_ratio on the
      5,000-PDE audit) and the plug-in simulation with fixed rates
      (run with --set sim_rates=fixed)
  <program>/estimation/results/<scenario>/estimates.parquet
      the same audits, bootstrap simulation with parametric rates (the default)
Every statistic uses audit years 1-25 (the same audits for every method).

Outputs (manuscripts/generated/):
  results_long.csv     one row per program x domain x method: truth, median
                       estimate, median half-width, coverage counts (rates and
                       national dollars)
  tables.md            the manuscript's results tables (Markdown)
  fig1_width.png, fig2_coverage.png

Run from the repository root:  python manuscripts/scripts/build_tables.py
"""
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "manuscripts" / "generated"
OUT.mkdir(parents=True, exist_ok=True)

# program label, results dir (fixed), results dir (parametric), national scale, design label
PROGRAMS = [
    ("Part C", "part-c-ipm/estimation/results_fixed/base", "part-c-ipm/estimation/results/base", 100,
     "990 enrollees, 330 per risk-score tercile"),
    ("Part D", "part-d-ipm/estimation/results_fixed/base", "part-d-ipm/estimation/results/base", 500,
     "5,000 PDEs (Neyman, 3 strata); ratio and regression: 990 beneficiaries, every PDE reviewed"),
    ("PERM", "perm/estimation/results_fixed/national", "perm/estimation/results/national", 200,
     "9 states x 520 payments (Neyman, 10 strata per state)"),
    ("EIPM", "eipm/estimation/results_fixed/base", "eipm/estimation/results/base", 100,
     "2,000 applications (Neyman, 5 APTC quintiles)"),
    ("CERT", "cert/estimation/results_fixed/national", "cert/estimation/results/national", 200,
     "37,651 claims (4 claim types x 5 quintiles, Neyman within type)"),
]
METHODS = [("expansion", "Expansion"), ("ratio", "Ratio"), ("regression", "Regression"),
           ("pde_expansion", "PDE expansion (same audit)"), ("pde_ratio", "PDE ratio (same audit)"),
           ("fixed", "Simulation (plug-in, fixed rates)"), ("parametric", "Simulation (parametric rates)")]
# pde_expansion / pde_ratio exist only for Part D (design-based estimators on the 5,000-PDE audit);
# a program without a method is simply skipped in every table

con = duckdb.connect()
parts = []
for prog, fixed, param, scale, _ in PROGRAMS:
    f, p = ROOT / fixed, ROOT / param
    if not (f / "estimates.parquet").exists() or not (p / "estimates.parquet").exists():
        raise SystemExit(f"missing results for {prog}: {f} or {p}")
    parts.append(f"""
      SELECT '{prog}' AS program, {scale}::DOUBLE AS scale, e.domain,
             CASE WHEN e.method = 'simulation' THEN 'fixed' ELSE e.method END AS method,
             e.rep, e.estimate, e.lower, e.upper, t.theta, t.X
      FROM '{f}/estimates.parquet' e JOIN read_json('{f}/truth.json') t USING (domain) WHERE e.rep <= 25
      UNION ALL
      SELECT '{prog}', {scale}, e.domain, 'parametric', e.rep, e.estimate, e.lower, e.upper, t.theta, t.X
      FROM '{p}/estimates.parquet' e JOIN read_json('{p}/truth.json') t USING (domain)
      WHERE e.rep <= 25 AND e.method = 'simulation'""")
con.execute("CREATE TABLE est AS " + " UNION ALL ".join(parts))
con.execute("""
CREATE TABLE res AS
SELECT program, domain, method, count(*) AS n_years,
       any_value(theta) AS true_rate,
       median(estimate) AS med_estimate,
       median((upper - lower) / 2) AS med_halfwidth,
       median(lower) AS med_lower, median(upper) AS med_upper,
       any_value(theta * X * scale) AS true_usd,
       median(estimate * X * scale) AS med_estimate_usd,
       median((upper - lower) / 2 * X * scale) AS med_halfwidth_usd,
       avg(abs(estimate - theta) / theta) AS mean_abs_rel_error,
       avg((estimate - theta) / theta) AS mean_rel_error,
       count(*) FILTER (WHERE lower <= theta AND theta <= upper) AS inside,
       count(*) FILTER (WHERE lower > theta) AS above,
       count(*) FILTER (WHERE upper < theta) AS below
FROM est GROUP BY program, domain, method
""")
assert con.execute("SELECT min(n_years), max(n_years) FROM res").fetchone() == (25, 25)
con.execute(f"COPY (SELECT * FROM res ORDER BY program, domain, method) TO '{OUT}/results_long.csv' (HEADER)")

order = {m: i for i, (m, _) in enumerate(METHODS)}
label = dict(METHODS)
pct = lambda v: f"{100 * v:.2f}%"
MEASURE = {"over": "Overpayments", "under": "Underpayments", "gross": "Gross", "net": "Net",
           "technical": "Technically improper", "monetary": "Monetary", "eligibility": "Eligibility", "claims": "Claims",
           "ipps": "Gross: Part A IPPS", "part_a_other": "Gross: Part A excl. IPPS", "part_b": "Gross: Part B",
           "dmepos": "Gross: DMEPOS"}
mlabel = lambda d: MEASURE[d.split("|")[1]] if d.startswith("national|") else MEASURE[d.split("|")[0]]
pts = lambda v: f"±{100 * v:.2f}"
usd = lambda v: f"${v / 1e9:,.2f}B"


def rows(domain_of):
    out = {}
    for prog, *_ in PROGRAMS:
        d = domain_of(prog)
        r = con.execute("SELECT * FROM res WHERE program = ? AND domain = ?", [prog, d]).fetchdf()
        out[prog] = {m: r[r.method == m].iloc[0] for m in order if (r.method == m).any()}
    return out


gross = rows(lambda p: "national|gross")
md = []

# Table 2: gross, all methods
md.append("**Table 2. Gross improper payment rate: median estimate, median 95% interval half-width and coverage over 25 audit years**\n")
md.append("| Program (audit) | True rate | Method | Median estimate | Median half-width (points) | Truth inside (above / below) |")
md.append("|---|---|---|---|---|---|")
for prog, *_rest in PROGRAMS:
    design = _rest[3]
    for i, (m, ml) in enumerate(m for m in METHODS if m[0] in gross[prog]):
        r = gross[prog][m]
        md.append(f"| {prog + ' (' + design + ')' if i == 0 else ''} | {pct(r.true_rate) if i == 0 else ''} | {ml} | "
                  f"{pct(r.med_estimate)} | {pts(r.med_halfwidth)} | {r.inside}/25 ({r.above}/{r.below}) |")
md.append("")

# Table 3: dollars for gross
md.append("**Table C1. Gross improper payments in national dollars (medians over 25 audit years)**\n")
md.append("| Program | True gross | Method | Estimated gross | Lower bound | Upper bound |")
md.append("|---|---|---|---|---|---|")
for prog, *_ in PROGRAMS:
    for i, (m, ml) in enumerate(m for m in METHODS if m[0] in gross[prog]):
        r = gross[prog][m]
        lo = r.med_lower * r.true_usd / r.true_rate
        hi = r.med_upper * r.true_usd / r.true_rate
        md.append(f"| {prog if i == 0 else ''} | {usd(r.true_usd) if i == 0 else ''} | {ml} | {usd(r.med_estimate_usd)} | {usd(lo)} | {usd(hi)} |")
md.append("")

# Table 4: interval problem summary and audit-size implication
cmp_method = {"Part C": "ratio", "Part D": "pde_ratio", "PERM": "ratio", "EIPM": "ratio", "CERT": "ratio"}
md.append("**Table 4. The fixed-rate interval problem and the parametric alternative (gross rate)**\n")
md.append("| Program | Analytic comparator | Analytic half-width | Fixed-rate half-width (share of analytic) | Fixed-rate coverage | Parametric half-width (share of analytic) | Parametric coverage | Audit size giving the analytic width, if width ∝ 1/√n |")
md.append("|---|---|---|---|---|---|---|---|")
for prog, *_ in PROGRAMS:
    a = gross[prog][cmp_method[prog]]
    fx, pa = gross[prog]["fixed"], gross[prog]["parametric"]
    sf, sp = fx.med_halfwidth / a.med_halfwidth, pa.med_halfwidth / a.med_halfwidth
    md.append(f"| {prog} | {label[cmp_method[prog]]} | {pts(a.med_halfwidth)} | {pts(fx.med_halfwidth)} ({100 * sf:.0f}%) | "
              f"{fx.inside}/25 | {pts(pa.med_halfwidth)} ({100 * sp:.0f}%) | {pa.inside}/25 | {100 * sp ** 2:.0f}% of the audit |")
md.append("")

# Table 5: every domain, coverage
md.append("**Table 5. Coverage of every measure (truth inside the 95% interval, out of 25 audit years; above / below)**\n")
md.append("| Program | Measure | True rate | " + " | ".join(ml for _, ml in METHODS) + " |")
md.append("|---|---|---|" + "---|" * len(METHODS))
for prog, *_ in PROGRAMS:
    doms = [d for (d,) in con.execute("SELECT DISTINCT domain FROM res WHERE program = ? ORDER BY domain", [prog]).fetchall()]
    key = lambda d: (not d.startswith("national"), ["over", "under", "gross", "net", "technical", "monetary", "eligibility", "claims"].index(d.split("|")[1]) if d.startswith("national") else 0, d)
    for d in sorted(doms, key=key):
        r = con.execute("SELECT * FROM res WHERE program = ? AND domain = ?", [prog, d]).fetchdf().set_index("method")
        cells = [f"{r.loc[m, 'inside']}/25 ({r.loc[m, 'above']}/{r.loc[m, 'below']})" if m in r.index else "—" for m, _ in METHODS]
        md.append(f"| {prog} | {mlabel(d)} | {pct(r.loc['ratio', 'true_rate'])} | " + " | ".join(cells) + " |")
md.append("")

# Table 6: point accuracy (gross)
md.append("**Table 3. Accuracy of the gross point estimate: average absolute error, as % of the true rate (average signed error)**\n")
md.append("| Program | " + " | ".join(ml for _, ml in METHODS) + " |")
md.append("|---|" + "---|" * len(METHODS))
for prog, *_ in PROGRAMS:
    md.append(f"| {prog} | " + " | ".join(f"{100 * gross[prog][m].mean_abs_rel_error:.1f}% ({100 * gross[prog][m].mean_rel_error:+.1f}%)" if m in gross[prog] else "—" for m, _ in METHODS) + " |")
md.append("")
(OUT / "tables.md").write_text("\n".join(md) + "\n")

# Figures -------------------------------------------------------------------
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# reference palette, light mode (validated): slots 1-3 blue, orange, aqua
C = {"analytic": "#2a78d6", "fixed": "#eb6834", "parametric": "#1baf7a"}
TXT, TXT2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": GRID, "axes.labelcolor": TXT2,
                     "xtick.color": TXT2, "ytick.color": TXT2, "axes.titlecolor": TXT})
progs = [p for p, *_ in PROGRAMS]
series = [("analytic", "Analytic (ratio; Part D: PDE ratio, same audit)"), ("fixed", "Simulation, plug-in (fixed rates)"),
          ("parametric", "Simulation, parametric rates")]


def value(prog, s, field):
    m = cmp_method[prog] if s == "analytic" else s
    return gross[prog][m][field]


for fig_name, field, ylabel, title, fmt in [
    ("fig1_width.png", "med_halfwidth", "Median 95% half-width, % of true gross rate",
     "Interval half-width relative to the true gross rate", lambda v: f"{v:.0f}%"),
    ("fig2_coverage.png", "inside", "Audit years with the truth inside the interval (of 25)",
     "Coverage of the gross rate over 25 audit years", lambda v: f"{v:.0f}")]:
    fig, ax = plt.subplots(figsize=(7.2, 3.9), dpi=200)
    w = 0.26
    for j, (s, sl) in enumerate(series):
        vals = [value(p, s, field) / (value(p, s, "true_rate") if field == "med_halfwidth" else 1) * (100 if field == "med_halfwidth" else 1)
                for p in progs]
        xs = [i + (j - 1) * (w + 0.02) for i in range(len(progs))]
        bars = ax.bar(xs, vals, w, color=C[s], label=sl, edgecolor="white", linewidth=1.5, zorder=2)
        for x, v in zip(xs, vals):
            ax.text(x, v + (0.3 if field == "inside" else 0.4), fmt(v), ha="center", va="bottom", fontsize=7,
                    color=TXT2, zorder=4, bbox=dict(boxstyle="square,pad=0.1", facecolor="white", edgecolor="none"))
    if field == "inside":
        ax.axhline(23.75, color=TXT2, linewidth=1, linestyle=(0, (3, 3)), zorder=3, label="Nominal 95% (23.75 of 25)")
        ax.set_ylim(0, 28)
    ax.set_xticks(range(len(progs)), progs)
    ax.set_ylabel(ylabel)
    ax.set_title(title, loc="left", fontsize=10)
    ax.grid(axis="y", color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.legend(frameon=False, fontsize=7.5, loc="upper left", ncol=2 if field == "inside" else 3, bbox_to_anchor=(0, -0.1))
    fig.tight_layout()
    fig.savefig(OUT / fig_name, facecolor="white")
    plt.close(fig)
print((OUT / "tables.md").read_text())
