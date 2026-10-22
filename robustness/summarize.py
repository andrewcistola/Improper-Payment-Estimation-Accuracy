"""Tables for Appendix D: interval calibration and robustness to size-dependent errors.

Reads estimates.parquet and truth.json from
    <program>/estimation/results/...          the reported run (25 audit years)
    robustness/results/<program>/calibration  100 audit years, base population
    robustness/results/<program>/beta_*       25 audit years, size-dependent error probability
and writes
    robustness/results/summary_calibration.csv, summary_beta.csv
    manuscripts/generated/appendix_d.md       (Tables D1-D3, assembled by manuscripts/scripts/assemble.py)

For each program, run and method, on the national gross rate:
    true rate, mean estimate, mean absolute error (% of truth), empirical SD of the
    point estimate over the audit years (percentage points), mean 95% half-width
    (points), calibration ratio = mean half-width / (1.96 x empirical SD), and
    coverage (audit years with the truth inside / audit years).
A calibration ratio near 1 means the interval is as wide as the estimator's own
sampling variability; below 1 it is too narrow, above 1 too wide.
"""
import json
import sys
from pathlib import Path

import duckdb
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
GEN = ROOT / "manuscripts" / "generated"
RES = ROOT / "robustness" / "results"

# label, base results folder, robustness folder key, domain of the national gross rate
PROGRAMS = [
    ("Part C", "part-c-ipm/estimation/results/base", "part-c-ipm", "national|gross"),
    ("Part D", "part-d-ipm/estimation/results/base", "part-d-ipm", "national|gross"),
    ("PERM", "perm/estimation/results/national", "perm", "national|gross"),
    ("EIPM", "eipm/estimation/results/base", "eipm", "national|gross"),
    ("CERT", "cert/estimation/results/national", "cert", "national|gross"),
]
METHOD_LABEL = {"expansion": "Expansion", "ratio": "Ratio", "regression": "Regression",
                "pde_expansion": "PDE expansion (marginal)", "pde_ratio": "PDE ratio (marginal)",
                "simulation": "Simulation (parametric rates)"}
ORDER = list(METHOD_LABEL)


def result_dir(prog_key, base_dir, run):
    if run == "base":
        return ROOT / base_dir
    return RES / prog_key / run / Path(base_dir).name   # <run>/base or <run>/national


def summarize(label, folder, domain, run):
    est = folder / "estimates.parquet"
    truth = folder / "truth.json"
    if not est.exists() or not truth.exists():
        return None
    theta = {t["domain"]: t["theta"] for t in json.load(open(truth))}[domain]
    con = duckdb.connect()
    df = con.execute(f"""
        SELECT method, rep, estimate, lower, upper FROM '{est}'
        WHERE domain = ? AND "interval" IN ('normal', 'percentile') ORDER BY method, rep""", [domain]).df()
    rows = []
    for m, g in df.groupby("method", sort=False):
        if m == "fixed":
            continue
        n = len(g)
        sd = g.estimate.std(ddof=1)
        hw = ((g.upper - g.lower) / 2).mean()
        cover = int(((g.lower <= theta) & (theta <= g.upper)).sum())
        rows.append({"program": label, "run": run, "method": m, "audit_years": n,
                     "true_rate_pct": 100 * theta, "mean_estimate_pct": 100 * g.estimate.mean(),
                     "mae_pct_of_truth": 100 * (g.estimate - theta).abs().mean() / theta,
                     "empirical_sd_pts": 100 * sd, "mean_halfwidth_pts": 100 * hw,
                     "calibration_ratio": hw / (1.96 * sd) if sd > 0 else float("nan"),
                     "covered": cover, "coverage_pct": 100 * cover / n})
    return rows


def table(df, title, note):
    out = [f"**{title}**", "",
           "| Program | Method | Audit years | True rate | Mean estimate | MAE (% of truth) | SD of estimate (pts) | Mean half-width (pts) | Half-width ÷ 1.96·SD | Coverage |",
           "|---|---|---|---|---|---|---|---|---|---|"]
    for (prog, _), g in df.groupby(["program", "run"], sort=False):
        g = g.set_index("method").reindex([m for m in ORDER if m in g.method.values]).reset_index()
        for i, r in g.iterrows():
            out.append(f"| {prog if i == 0 else ''} | {METHOD_LABEL.get(r.method, r.method)} | {r.audit_years} | "
                       f"{r.true_rate_pct:.2f}% | {r.mean_estimate_pct:.2f}% | {r.mae_pct_of_truth:.1f}% | "
                       f"{r.empirical_sd_pts:.3f} | {r.mean_halfwidth_pts:.3f} | {r.calibration_ratio:.2f} | "
                       f"{int(r.covered)}/{r.audit_years} |")
    out.append("")
    out.append(f"*{note}*")
    return "\n".join(out)


def main():
    rows = []
    for label, base_dir, key, domain in PROGRAMS:
        runs = ["base", "calibration"] + (sorted(p.name for p in (RES / key).glob("beta_*")) if (RES / key).exists() else [])
        for run in runs:
            r = summarize(label, result_dir(key, base_dir, run), domain, run)
            if r:
                rows.extend(r)
    if not rows:
        sys.exit("no results found")
    df = pd.DataFrame(rows)
    RES.mkdir(parents=True, exist_ok=True)
    df[df.run.isin(["base", "calibration"])].to_csv(RES / "summary_calibration.csv", index=False)
    df[df.run.str.startswith("beta")].to_csv(RES / "summary_beta.csv", index=False)

    parts = []
    cal = df[df.run == "calibration"]
    if len(cal):
        parts.append(table(cal, "Table D1. Interval calibration over 100 audit years (base populations, gross rate)",
                           "SD of estimate = standard deviation of the point estimate across audit years (percentage points). "
                           "Half-width ÷ 1.96·SD near 1 means the interval matches the estimator's own sampling variability; "
                           "below 1, the interval is too narrow. Monte Carlo SE of coverage at 95% with 100 audit years: 2.2 points. "
                           "Bootstrap simulation run at 500 iterations per audit year."))
    for i, b in enumerate(sorted(df.run[df.run.str.startswith("beta")].unique(), reverse=True)):   # +0.5 first (Table D2), then -0.5 (D3)
        val = b.replace("beta_", "").replace("p", "+").replace("m", "-")
        sub = df[df.run == b]
        parts.append(table(sub, f"Table D{i + 2}. Size-dependent error probability, size_beta = {val} (25 audit years, gross rate)",
                           f"Each unit's error probability is multiplied by (payment / stratum mean payment)^{val}, capped at 0.95, "
                           "before calibration to the same public targets; designs, audit sizes and methods are unchanged. "
                           "Bootstrap simulation run at 500 iterations per audit year."))
    GEN.mkdir(parents=True, exist_ok=True)
    (GEN / "appendix_d.md").write_text("\n\n".join(parts) + "\n")
    print(f"wrote {GEN / 'appendix_d.md'} ({len(parts)} tables) and {RES}/summary_*.csv")


if __name__ == "__main__":
    main()
