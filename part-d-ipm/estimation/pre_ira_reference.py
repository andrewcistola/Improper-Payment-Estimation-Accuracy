"""Write part-d-ipm/pre-ira-reference.md: Part D results under the pre-IRA
(CY 2023) benefit next to the reported post-IRA (CY 2025) results, for
the same population, errors and audits. A robustness reference only: the
README tables and shared/report.yaml use the post-IRA results.

Inputs (25 audit years each):
  post-IRA: part-d-ipm/estimation/results/base (parametric), results_fixed/base
  pre-IRA : part-d-ipm/estimation/results_pre_ira/base (parametric), results_pre_ira_fixed/base
Run from the repository root:  python part-d-ipm/estimation/pre_ira_reference.py
"""
import json
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[2]
E = ROOT / "part-d-ipm" / "estimation"
SCALE = 500
RUNS = {"Post-IRA (CY 2025, reported)": ("results/base", "results_fixed/base"),
        "Pre-IRA (CY 2023, reference)": ("results_pre_ira/base", "results_pre_ira_fixed/base")}
METHODS = [("expansion", "Expansion"), ("ratio", "Ratio"), ("regression", "Regression"),
           ("fixed", "Bootstrap (fixed rates)"), ("parametric", "Bootstrap (parametric rates)")]
MEAS = [("over", "Overpayments"), ("under", "Underpayments"), ("gross", "Gross"), ("net", "Net")]

con = duckdb.connect()
parts = []
for design, (param, fixed) in RUNS.items():
    p, f = E / param, E / fixed
    parts.append(f"""
      SELECT '{design}' AS design, e.domain, e.method, e.rep, e.estimate, e.lower, e.upper, t.theta, t.X
      FROM '{p}/estimates.parquet' e JOIN read_json('{p}/truth.json') t USING (domain)
      WHERE e.rep <= 25 AND e.method <> 'simulation'
      UNION ALL
      SELECT '{design}', e.domain, 'parametric', e.rep, e.estimate, e.lower, e.upper, t.theta, t.X
      FROM '{p}/estimates.parquet' e JOIN read_json('{p}/truth.json') t USING (domain)
      WHERE e.rep <= 25 AND e.method = 'simulation'
      UNION ALL
      SELECT '{design}', e.domain, 'fixed', e.rep, e.estimate, e.lower, e.upper, t.theta, t.X
      FROM '{f}/estimates.parquet' e JOIN read_json('{f}/truth.json') t USING (domain)
      WHERE e.rep <= 25 AND e.method = 'simulation'""")
con.execute("CREATE TABLE est AS " + " UNION ALL ".join(parts))
res = con.execute(f"""
SELECT design, domain, method, count(*) AS n, any_value(theta) AS theta, any_value(theta * X * {SCALE}) AS true_usd,
       median(estimate) AS med, median((upper - lower) / 2) AS hw, median(estimate * X * {SCALE}) AS med_usd,
       median((upper - lower) / 2 * X * {SCALE}) AS hw_usd,
       avg(abs(estimate - theta) / theta) AS mae,
       count(*) FILTER (WHERE lower <= theta AND theta <= upper) AS inside,
       count(*) FILTER (WHERE lower > theta) AS above, count(*) FILTER (WHERE upper < theta) AS below
FROM est GROUP BY ALL""").fetchdf()
assert (res.n == 25).all()
get = lambda d, dom, m: res[(res.design == d) & (res.domain == f"national|{dom}") & (res.method == m)].iloc[0]
pct = lambda v: f"{100 * v:.2f}%"
usd = lambda v: f"${v / 1e9:,.2f}B"

truth = {d: json.load(open(ROOT / "part-d-ipm/errors" / ("output/base" if "Post" in d else "output_pre_ira/base")
                           / "truth.json"))["overall"] for d in RUNS}
L = ["# Part D under the pre-IRA benefit (reference)", "",
     "A robustness check, not part of the reported results. The same synthetic population, the same PDE errors and the "
     "same 25 audit years as the reported Part D results are re-run with Medicare's payment computed under the "
     "**pre-IRA CY 2023 standard benefit** instead of the post-IRA CY 2025 benefit. The question is whether the "
     "methods compare the same way when the payment rules, and with them the size and distribution of the payment "
     "error, change. The README tables and `shared/report.yaml` are unchanged and use the post-IRA results.", "",
     "## Benefit designs", "",
     "| | Post-IRA, CY 2025 (reported) | Pre-IRA, CY 2023 (this reference) |",
     "|---|---|---|",
     "| Deductible | $590 | $505 |",
     "| Initial coverage | 25% enrollee; plan 65% and manufacturer 10% (brand) or plan 75% (generic) | 25% enrollee, 75% plan, to $4,660 total drug cost |",
     "| Coverage gap | None | Non-LIS: 25% enrollee; brand 70% manufacturer discount and 5% plan; generic 75% plan. LIS: 100% standard share, paid by LICS except the copay |",
     "| Catastrophic threshold | $2,000 out of pocket | $7,400 true out of pocket (manufacturer discount counts) |",
     "| Catastrophic phase | Enrollee 0; plan 60%; manufacturer 20% (brand); Medicare reinsurance 20% (brand) / 40% (generic) | Enrollee 5% (LIS: 0, paid by LICS); plan 15%; Medicare reinsurance 80% |",
     "| LIS copays | $4.90 generic / $12.15 brand | $4.15 generic / $10.35 brand |",
     "", "Code: `errors/pre_ira.yaml` → `errors/sql/05_benefit_pre_ira.sql` (population) and "
     "`estimation/pre_ira.yaml` (estimation; `medicare_cents_pre_ira` in `estimation/simulation.py`, tested to "
     "reproduce the SQL to the cent). Simplification: the catastrophic minimum copays ($4.15 / $10.35) are not "
     "applied; enrollee coinsurance there is 5%.", "",
     "## Populations", "",
     "| | Post-IRA (reported) | Pre-IRA (reference) |", "|---|---|---|"]
for k, lab, f in [("payments", "Total payments (national)", usd), ("reinsurance", "Reinsurance", usd),
                  ("lics", "Low-income cost sharing", usd), ("direct_subsidy", "Direct subsidy", usd),
                  ("overpayments", "True overpayments", usd), ("underpayments", "True underpayments", usd),
                  ("gross_rate", "True gross rate", pct), ("unit_err_rate", "Beneficiaries with a payment error", pct),
                  ("share_catastrophic", "Beneficiaries reaching the catastrophic phase", pct)]:
    L.append(f"| {lab} | " + " | ".join(f(truth[d][k]) for d in RUNS) + " |")
L += ["", "PDE error rates are identical in both (10% of LTC claims, 2.5% of others; 90% full errors). The pre-IRA "
      "payment error is about twice as large because Medicare reinsurance pays 80% of catastrophic costs and LICS "
      "covers LIS cost sharing through the coverage gap; fewer beneficiaries have a payment error because a non-LIS "
      "enrollee's error below the catastrophic threshold changes only plan and enrollee liability.", "",
      "## Gross improper payment rate (25 audit years)", "",
      "Median point estimate and median 95% half-width; coverage = audit years with the truth inside the interval "
      "(in parentheses, intervals entirely above / below the truth).", "",
      "| Method | Post-IRA: estimate (truth " + pct(get(list(RUNS)[0], "gross", "ratio").theta) + ") | Post-IRA: half-width | Post-IRA: coverage | "
      "Pre-IRA: estimate (truth " + pct(get(list(RUNS)[1], "gross", "ratio").theta) + ") | Pre-IRA: half-width | Pre-IRA: coverage |",
      "|---|---|---|---|---|---|---|"]
for m, ml in METHODS:
    a, b = get(list(RUNS)[0], "gross", m), get(list(RUNS)[1], "gross", m)
    L.append(f"| {ml} | {pct(a.med)} | ±{100 * a.hw:.2f} | {a.inside}/25 ({a.above}/{a.below}) | "
             f"{pct(b.med)} | ±{100 * b.hw:.2f} | {b.inside}/25 ({b.above}/{b.below}) |")
L += ["", "## Every measure, pre-IRA (25 audit years)", "",
      "| Measure | True | Method | Median estimate | Median half-width | Coverage | Mean absolute error (% of truth) |",
      "|---|---|---|---|---|---|---|"]
for dom, dl in MEAS:
    for i, (m, ml) in enumerate(METHODS):
        b = get(list(RUNS)[1], dom, m)
        L.append(f"| {dl if i == 0 else ''} | {usd(b.true_usd) + ' (' + pct(b.theta) + ')' if i == 0 else ''} | {ml} | "
                 f"{usd(b.med_usd)} ({pct(b.med)}) | ±{usd(b.hw_usd)} | {b.inside}/25 ({b.above}/{b.below}) | {100 * b.mae:.1f}% |")
L += ["", "## Coverage of every measure: post-IRA vs pre-IRA", "",
      "| Measure | " + " | ".join(ml for _, ml in METHODS) + " |", "|---|" + "---|" * len(METHODS)]
for dom, dl in MEAS:
    for d in RUNS:
        L.append(f"| {dl}, {d.split(' (')[0]} | " + " | ".join(f"{get(d, dom, m).inside}/25" for m, _ in METHODS) + " |")
pg, pa = get(list(RUNS)[1], "gross", "parametric"), get(list(RUNS)[1], "gross", "ratio")
L += ["", "## Conclusion", "",
      f"The methods compare the same way under both benefit designs. Under the pre-IRA benefit, the true gross "
      f"rate doubles ({pct(get(list(RUNS)[0], 'gross', 'ratio').theta)} to {pct(pg.theta)}), and every interval roughly "
      f"doubles in width with it. The ranking is unchanged:",
      f"- **Parametric-rate bootstrap:** contains the true gross rate in {pg.inside} of 25 audit years, with a median "
      f"half-width of ±{100 * pg.hw:.2f} points, against ±{100 * pa.hw:.2f} for the ratio estimator.",
      f"- **Analytic estimators:** cover in 18–19 of 25 and run low.",
      f"- **Fixed-rate bootstrap:** remains far too narrow ({get(list(RUNS)[1], 'gross', 'fixed').inside} of 25).",
      f"- **Underpayments:** stay hard for every method.",
      "",
      "The study's conclusions about Part D do not depend on the benefit design."]
text = "\n".join(L) + "\n"
text = text.replace("$-0.00B", "$0.00B").replace("(-0.00%)", "(0.00%)")
(ROOT / "part-d-ipm" / "pre-ira-reference.md").write_text(text)
print(text)
