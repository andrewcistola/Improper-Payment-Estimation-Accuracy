"""Validation checks (orchestration only; the work is in src/sql).

  calibration : truth.json vs public targets, with stated tolerances
  benchmark   : Edwards, Liu & Delage (2023) Fig. 4.1 coverage pattern
  smoke       : production-style samples recover the truth on average

Run:  python -m ipsim.validate [calibration|benchmark|smoke|all]
Writes output/validation/<check>.json and a combined report.md.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import duckdb

from .engine import ROOT, SQL_DIR

OUT = ROOT / "output"
VAL = OUT / "validation"

# --------------------------------------------------------------------- #
# Public targets (handoff table; FY 2025 unless noted). Tolerances are in
# absolute rate points unless the name says otherwise.
TARGETS = [
    # program, scenario, json path, target, tolerance, source
    ("partc", "base", "overall.gross_rate", 0.0609, 0.0010, "Part C IPM FY2025 gross 6.09%"),
    ("partc", "base", "overall.overpayments", 21.43e9, 0.02, "overpayments $21.43B (rel. tol)"),
    ("partc", "base", "overall.underpayments", 2.23e9, 0.02, "underpayments $2.23B (rel. tol)"),
    ("partc", "base", "overall.md_rate", 0.0022, 0.0005, "missing documentation 0.22%"),
    ("partc", "base", "overall.payments", 388.72e9, 0.001, "payments $388.72B (rel. tol)"),
    ("partd", "base", "overall.gross_rate", 0.0400, 0.0010, "Part D IPM FY2025 gross 4.00%"),
    ("partd", "base", "overall.overpayments", 3.70e9, 0.05, "overpayments $3.70B (rel. tol)"),
    ("partd", "base", "overall.underpayments", 0.52e9, 0.10, "underpayments $0.52B (rel. tol)"),
    ("partd", "base", "by.error_type_share.pde_count.missing_documentation", 0.7500, 0.01, "75.00% of errors"),
    ("partd", "base", "by.error_type_share.pde_count.pricing", 0.1786, 0.01, "17.86% of errors"),
    ("partd", "base", "by.error_type_share.pde_count.drug_discrepancy", 0.0714, 0.01, "7.14% of errors"),
    ("partd", "base", "overall.payments", 105.56e9, 0.001, "payments $105.56B (rel. tol)"),
    ("perm", "state_elig_grid", "overall.overall_rate", 0.0612, 0.0030, "Medicaid FY2025 6.12% (pooled sanity check)"),
    ("eipm", "base", "overall.gross_rate", 0.0089, 0.0010, "EIPM FY2025 0.89%"),
]
REL = {"overpayments", "underpayments", "payments"}


def _get(d, path):
    for k in path.split("."):
        d = d[k]
    return d


def calibration():
    rows = []
    for prog, scen, path, target, tol, src in TARGETS:
        f = OUT / prog / scen / "truth.json"
        if not f.exists():
            rows.append(dict(program=prog, metric=path, status="missing"))
            continue
        val = _get(json.loads(f.read_text()), path)
        rel = path.split(".")[-1] in REL
        diff = (val / target - 1) if rel else (val - target)
        rows.append(dict(program=prog, scenario=scen, metric=path, value=val, target=target,
                         diff=diff, tolerance=tol, relative=rel,
                         status="pass" if abs(diff) <= tol else "FAIL", source=src))
    # PERM: every state's true eligibility rate is at or just below its grid value
    f = OUT / "perm" / "state_elig_grid" / "truth.json"
    if f.exists():
        t = json.loads(f.read_text())
        cfg = json.loads((OUT / "perm" / "state_elig_grid" / "manifest.json").read_text())
        import yaml
        states = yaml.safe_load((OUT / "perm" / "state_elig_grid" / "config.yaml").read_text())["variables"]["states"]
        for s in states:
            v = t["by"]["state"][str(s["state_id"])]["elig_rate"]
            ok = v <= s["elig_rate"] + 1e-12 and s["elig_rate"] - v < 0.0002
            rows.append(dict(program="perm", scenario="state_elig_grid",
                             metric=f"state {s['state_id']} elig_rate", value=v, target=s["elig_rate"],
                             diff=v - s["elig_rate"], tolerance=0.0002, relative=False,
                             status="pass" if ok else "FAIL",
                             source="grid value; must not exceed, within 0.02 pt"))
    return rows


# --------------------------------------------------------------------- #
def _con():
    con = duckdb.connect()
    for lib in sorted((SQL_DIR / "lib").glob("*.sql")):
        con.execute(lib.read_text())
    return con


def _setvars(con, **kw):
    for k, v in kw.items():
        con.execute(f"SET VARIABLE {k} = ?", [v])


def benchmark(reps=4000, n=30, seed=7):
    con = _con()
    _setvars(con, seed=seed, reps=reps, n=n,
             pop_glob=str(OUT / "ffs_stress" / "*all_or_nothing*" / "population.parquet"))
    con.execute((SQL_DIR / "validate" / "ffs_benchmark.sql").read_text())
    rows = con.execute("SELECT shape, error_rate, coverage, mc_se, rel_bias FROM benchmark").fetchall()
    out = []
    for shape, p, cov, se, bias in rows:
        # published pattern: right-skewed holds ~90%; two-spike and left fall
        # below 90% once the error rate exceeds 0.6
        if shape == "right":
            expect, ok = ">= 0.89", cov >= 0.89 - 2 * se
        elif p > 0.6:
            expect, ok = "< 0.90", cov < 0.90
        else:
            expect, ok = "(no claim)", True
        out.append(dict(shape=shape, error_rate=p, coverage=cov, mc_se=se, rel_bias=bias,
                        expected=expect, status="pass" if ok else "FAIL"))
    return out


# --------------------------------------------------------------------- #
# Smoke tests: one production-style design per program. Each entry gives
# the SQL that builds pop(unit_id, stratum, y, x), the allocation, the
# selection rule, and how to read the truth.
SMOKE = {
    "ffs_stress": dict(
        scen="right_all_or_nothing_p0.30",
        pop="SELECT unit_id, stratum, y::DOUBLE AS y, x::DOUBLE AS x FROM read_parquet('{p}')",
        alloc="SELECT 'all' AS stratum, 30 AS n_h", selection="srs",
        stat="t_expansion", truth=lambda t: t["overall"]["y_tot"], label="total improper $"),
    "partc": dict(
        scen="base",
        pop="SELECT unit_id, stratum, abs(y)::DOUBLE AS y, x::DOUBLE AS x FROM read_parquet('{p}')",
        alloc="SELECT * FROM (VALUES ('low',1500),('medium',1500),('high',1500)) t(stratum,n_h)",
        selection="srs", stat="rate", truth=lambda t: t["overall"]["gross_rate"], label="gross rate"),
    "partd": dict(
        scen="base",
        pop="SELECT unit_id, stratum, abs(y)::DOUBLE AS y, x::DOUBLE AS x FROM read_parquet('{p}')",
        alloc="SELECT 'all' AS stratum, 1500 AS n_h", selection="srs",
        stat="rate", truth=lambda t: t["overall"]["gross_rate"], label="gross rate"),
    "eipm": dict(
        scen="base",
        pop="SELECT unit_id, stratum, abs(y)::DOUBLE AS y, x::DOUBLE AS x FROM read_parquet('{p}')",
        alloc="SELECT * FROM (VALUES ('A_lt150',500),('B_150_250',500),('C_250_400',500),('D_ge400',500)) t(stratum,n_h)",
        selection="srs", stat="rate", truth=lambda t: t["overall"]["gross_rate"], label="gross rate"),
    "perm": dict(
        scen="state_elig_grid",
        # state 5 (true eligibility rate at the 3% threshold); federal share
        pop="SELECT unit_id, stratum, (y * fmap)::DOUBLE AS y, (x * fmap)::DOUBLE AS x "
            "FROM read_parquet('{p}') WHERE state_id = 5",
        alloc="SELECT DISTINCT stratum, CASE WHEN stratum LIKE '%FFS%' THEN 20 ELSE 6 END AS n_h "
              "FROM read_parquet('{p}') WHERE state_id = 5",
        selection="systematic", stat="rate",
        truth=lambda t: t["by"]["state"]["5"]["overall_rate"], label="state 5 overall rate"),
    "radv": dict(
        scen="base",
        # contract 11 frame (n = 100). Ratio of sum(dR*months) to sum(months)
        # = the production month-weighted mean Delta-R.
        pop="SELECT unit_id, stratum, (delta_r * months)::DOUBLE AS y, months::DOUBLE AS x "
            "FROM read_parquet('{p}') WHERE in_frame AND contract_id = 11",
        alloc="SELECT '11' AS stratum, 100 AS n_h", selection="srs",
        stat="rate", truth=lambda t: t["by"]["contract"]["11"]["mean_dr_m"],
        label="contract 11 month-weighted mean dR"),
}


def smoke(reps=300, seed=11, programs=None):
    out = []
    for prog, s in SMOKE.items():
        if programs and prog not in programs:
            continue
        d = OUT / prog / s["scen"]
        p = d / "population.parquet"
        if not p.exists():
            out.append(dict(program=prog, status="missing"))
            continue
        con = _con()
        con.execute("CREATE TABLE pop AS " + s["pop"].format(p=p))
        con.execute("CREATE TABLE alloc AS " + s["alloc"].format(p=p))
        X = con.execute("SELECT sum(x) FROM pop").fetchone()[0]
        _setvars(con, seed=seed, reps=reps, selection=s["selection"], X_total=X)
        con.execute((SQL_DIR / "estimate" / "sample.sql").read_text())
        con.execute((SQL_DIR / "estimate" / "estimators.sql").read_text())
        n_per_rep = con.execute("SELECT min(c), max(c) FROM (SELECT count(*) c FROM sample GROUP BY rep)").fetchone()
        mean, sd = con.execute(f"SELECT avg({s['stat']}), stddev_samp({s['stat']}) FROM estimates").fetchone()
        ratio_mean, reg_mean = con.execute("SELECT avg(t_ratio), avg(t_regression) FROM estimates").fetchone()
        truth = s["truth"](json.loads((d / "truth.json").read_text()))
        z = (mean - truth) / (sd / reps ** 0.5) if sd else 0.0
        out.append(dict(program=prog, scenario=s["scen"], estimand=s["label"], selection=s["selection"],
                        reps=reps, sample_size=n_per_rep[0], truth=truth, mean_estimate=mean,
                        rel_bias=mean / truth - 1 if truth else None, z_bias=z,
                        status="pass" if abs(z) < 3.5 else "FAIL"))
        con.close()
    return out


# --------------------------------------------------------------------- #
def _md_table(rows, cols):
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for r in rows:
        cells = []
        for c in cols:
            v = r.get(c, "")
            if isinstance(v, float):
                v = f"{v:.4g}" if abs(v) >= 1e4 or abs(v) < 1e-3 and v != 0 else f"{v:.4f}"
            cells.append(str(v))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def main(argv=None):
    which = (argv or sys.argv[1:] or ["all"])[0]
    VAL.mkdir(parents=True, exist_ok=True)
    report = ["# Validation report", "",
              "Generated by `python -m ipsim.validate`. Every number below is recomputed from the "
              "files in `output/`.", ""]
    if which in ("calibration", "all"):
        r = calibration()
        (VAL / "calibration.json").write_text(json.dumps(r, indent=2) + "\n")
        report += ["## Calibration to public aggregates", "",
                   _md_table(r, ["program", "metric", "value", "target", "diff", "tolerance", "status", "source"]), ""]
    if which in ("benchmark", "all"):
        r = benchmark()
        (VAL / "benchmark.json").write_text(json.dumps(r, indent=2) + "\n")
        report += ["## Benchmark: Edwards, Liu & Delage (2023), SRS n = 30, one-sided 90% normal bound", "",
                   _md_table(r, ["shape", "error_rate", "coverage", "mc_se", "rel_bias", "expected", "status"]), ""]
    if which in ("smoke", "all"):
        r = smoke()
        (VAL / "smoke.json").write_text(json.dumps(r, indent=2) + "\n")
        report += ["## Smoke test: production-style designs recover the truth", "",
                   "Pass if |mean estimate - truth| < 3.5 Monte Carlo SE.", "",
                   _md_table(r, ["program", "estimand", "selection", "sample_size", "reps", "truth",
                                 "mean_estimate", "rel_bias", "z_bias", "status"]), ""]
    (VAL / "report.md").write_text("\n".join(report))
    print("\n".join(report))


if __name__ == "__main__":
    main()
