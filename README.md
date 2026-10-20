## Comparative Accuracy of Improper Payment Estimation Methods in Federal Health Programs: A Monte Carlo Evaluation of Analytic Estimators and Bootstrap Simulation

#### **Andrew Cistola, PhD, MPH** 
Manuscript and one-page summary: [`manuscripts/`](manuscripts/) · Companion literature review: [`literature-review/`](literature-review/) 

**Research question.** What is the comparative accuracy of the available methods for estimating improper payments in federal health programs?

The Payment Integrity Information Act of 2019 (PIIA) requires that every federal program at risk of significant improper payments produce a statistically valid estimate of those payments, along with a confidence interval. The Centers for Medicare & Medicaid Services (CMS) produces five such estimates: Medicare Part C, Medicare Part D, Medicaid (the Payment Error Rate Measurement, or PERM), the Marketplace advance premium tax credit (EIPM), and Medicare fee-for-service (the Comprehensive Error Rate Testing program, or CERT). Each program audits a probability sample of payments and projects the audited errors to the program as a whole. Depending on the program, this projection uses either design-based analytic estimators (expansion, ratio, or regression) or audit-finding bootstrap simulation.

This repository contains a Monte Carlo study of the accuracy of these methods. In this study, accuracy has two parts:
- **Point accuracy:** how close the estimate is to the true improper payment.
- **Interval accuracy:** whether the 95% interval contains the truth in about 95% of repeated audits (coverage) and, among intervals that do, how narrow the interval is (width).

**Approach: Synthetic Data Run through Multiple Audit Years** For each program, this study builds a synthetic population with fabricated errors so that the true improper payment is known. Each population is calibrated only to public FY 2025 aggregates. The program's production-like audit is then drawn in 25 independent audit years, and the estimate and interval from each method are compared with the truth. Each audit year has one audit, drawn with the program's design, and every method uses only that audit. The analytic methods estimate their variance from the audit. The bootstrap simulation uses the audit findings as audited and redraws only the error rates (as opposed to resampling the audit itself). In Part D, both the audit sample used by the bootstrap simulation (5,000 PDEs) and the beneficiary sample (108,000 beneficiaries) are fixed for the audit year.

**Scope: PIIA improper payment rate estimation.** Recovery and extrapolation uses (for example, contract-level RADV or provider overpayment demands) are out of scope. This repository contains no PHI, no unit-level data from any source, and nothing non-public. Every number is drawn from stated distributions and calibrated only to public aggregate results.

**Methods Under Comparison:** This study compares the following approaches.
- **Expansion:** The average error per audited unit (enrollee, beneficiary, claim, or application) is multiplied by the number of units in the population, stratum by stratum. Expansion can apply to payments directly or to parts of a payment function audited separately (for example, risk score error).
- **Ratio:** The audited improper dollars are divided by the audited payments to produce an improper payment rate. This rate is then applied to the program's known total payments.
- **Regression:** Within each stratum, a regression model is fit on the audit using basic beneficiary variables and the amount paid, and this model predicts improper payments for every unit in the population. The prediction errors from the audit are then added back so that the total remains unbiased even if the model is imperfect.
- **Bootstrap Simulation:** The audit findings (error rates, partial-error shares, and error sizes) are assigned at random to every unaudited unit, and the payment rules are rerun many times, while audited units keep their own findings. The estimate is the average across iterations, and the 95% interval runs from the 2.5th to the 97.5th percentile.

**Confidence Intervals:** Expansion and ratio report a normal 95% interval (the estimate ± 1.96 standard errors, from the stratified design with a finite population correction). Regression uses the same formula on the prediction errors from the audit (residuals) with a t multiplier, so every analytic interval comes from a single audit. This study compared two versions of the bootstrap simulation:
- **Fixed rates:** The audited error rates are reused in every iteration. The point estimates from this version are as accurate as or more accurate than those from the analytic estimators. However, its intervals contained the truth in only 24% of audit years because they omit the sampling error of the audited rates.
- **Parametric rates:** Before each iteration, the audited error rates are redrawn from their binomial sampling distribution. The intervals from this version contained the true gross rate in 96.8% of audit years and were narrower than the analytic intervals from the same audit in all five programs.

The results below report the parametric version. The full write-up, including the fixed-rate comparison, is available in [`manuscripts/`](manuscripts/) (manuscript and one-page summary).

## Structure

Each of the four program folders has the same two parts:

- **`errors/`** builds an error-free population, applies fake errors, records the truth and checks it against public figures.
- **`estimation/`** samples that population with the program's design and estimates the improper payment rate with each method.

| Folder | Application | errors/ | estimation/ |
|---|---|---|---|
| [`part-c-ipm/`](part-c-ipm/) | Risk-score errors on capitated payments (Medicare Advantage) | Enrollees, HCCs, payments → unsupported HCCs, hierarchy moves, missing documentation, additional HCCs | Audit of 990 enrollees, 330 per risk-score tercile (stratified SRS); overpayments, underpayments, gross and net |
| [`part-d-ipm/`](part-d-ipm/) | Claim errors flowing through the benefit to reinsurance and subsidies | Beneficiaries, PDEs → PDE errors re-run through the post-IRA 2025 benefit | SRS of beneficiaries; the bootstrap simulation uses an audit sample of 5,000 PDEs and a beneficiary sample |
| [`perm-cert/`](perm-cert/) | Individual claim or benefit errors | PERM: state payment universes → claims and eligibility errors (9 states, true eligibility rates 2.00–4.00%). CERT: national Medicare FFS claims, four claim types → whole-claim and partial over- and underpayments calibrated to FY 2025 | PERM: Neyman allocation over payment type × quintile, systematic selection, 520 per state. CERT: 37,651 claims, FY 2025 count per claim type, Neyman across payment quintiles |
| [`eipm/`](eipm/) | Beneficiary subsidy eligibility (Marketplace APTC) | FFE applications and APTC → rare overpayments: technically improper (whole APTC) and monetary (income) | Stratified SRS of 2,000, Neyman allocation over APTC quintiles |
| [`shared/`](shared/) | Code used by all four | Runner, random numbers, samplers | **The methods, written once**: expansion and ratio with normal intervals; regression (models fit within strata, residual interval); the audit-finding bootstrap simulation loop; scoring |
| [`literature-review/`](literature-review/) | Standalone narrative review of the comparative accuracy of improper payment estimation methods (Markdown, PDF, Word) | | |
| [`manuscripts/`](manuscripts/) | Manuscript and one-page summary of the Monte Carlo study | | |

Inside each program, the SQL files are numbered in the order they run, and each file's header states what it does and every probability or formula it uses. Each `config.yaml` lists the files it runs.

## Methods

| Method | Code | Interval |
|---|---|---|
| Expansion | `ipm_expansion` in [`shared/sql/lib/02_estimators.sql`](shared/sql/lib/02_estimators.sql); Part C uses a risk-score expansion ([`part-c-ipm/estimation/sql/10_expansion.sql`](part-c-ipm/estimation/sql/10_expansion.sql)) | Normal (Taylor linearization) |
| Ratio | `ipm_ratio`, same file | Normal (Taylor linearization) |
| Regression | [`shared/ipsim/regression.py`](shared/ipsim/regression.py) + each program's `30_regression.sql` (predictors) | Normal (t), from the audit residuals |
| Bootstrap simulation, parametric rates (`simulation`; reported) | [`shared/ipsim/simulation.py`](shared/ipsim/simulation.py) + each program's `estimation/*simulation.py`; `sim_rates: parametric` (default): each stratum's error rate and partial-error share redrawn as Binomial(n, rate)/n before every iteration | 2.5th–97.5th percentiles of 1,000 iterations |
| Bootstrap simulation, fixed rates (comparison only) | Same, `--set sim_rates=fixed`: the audited rates in every iteration. Results in `<program>/estimation/results_fixed/` | Same |

## Run

```bash
pip install -e .                              # duckdb (pinned), pyarrow, numpy, numba, pyyaml
# 1. populations (a few minutes)
ipsim part-c-ipm/errors/config.yaml part-d-ipm/errors/config.yaml eipm/errors/config.yaml \
      perm-cert/errors/perm.yaml perm-cert/errors/cert.yaml
# 2. estimation (each program writes estimation/results/)
ipsim part-c-ipm/estimation/config.yaml part-d-ipm/estimation/config.yaml eipm/estimation/config.yaml \
      perm-cert/estimation/perm.yaml perm-cert/estimation/perm_national.yaml perm-cert/estimation/cert.yaml
ipsim shared/summary.yaml                     # all metrics in one table
ipsim shared/report.yaml                      # truth vs every estimate and CI, audit years 1-25 (by_scenario.csv, by_audit_year)
python -m pytest -q shared/tests              # tests
```

Add `--set reps=20 sim_reps=3 sim_iterations=100` (20 audit years, 3 of them run through the bootstrap simulation at 100 iterations each) to any estimation run for a quick pilot, `--timing` to see each step's run time, and `--memory-limit 2GB` when running several configs at once.

## Results

Each row gives the true gross improper payment and, over the 25 audit years, the median point estimate and the median upper and lower bounds of the 95% interval. Gross = overpayments + underpayments, netted within each enrollee, beneficiary or claim first (EIPM and PERM have overpayments only). Dollars are national program dollars: each program's population is scaled by its own factor (Part C × 100, Part D × 500, EIPM × 100, PERM × 200, CERT × 200). Overpayments, underpayments, net, and how often each interval contains the truth are in each program's README ([Part C](part-c-ipm/README.md#results-25-audit-years), [Part D](part-d-ipm/README.md#results-25-audit-years), [PERM](perm-cert/README.md#perm-results-25-audit-years), [EIPM](eipm/README.md#results-25-audit-years), [CERT](perm-cert/README.md#cert-results-25-audit-years)).

**Gross improper payments (national dollars)**

| Program | Method | True gross | Estimated gross | Upper bound | Lower bound |
|---|---|---|---|---|---|
| Part C (audit of 990) | Expansion | $23.57B | $23.92B | $27.96B | $19.69B |
|  | Ratio | $23.57B | $23.82B | $27.81B | $19.83B |
|  | Regression | $23.57B | $23.70B | $27.64B | $19.97B |
|  | Bootstrap simulation (parametric rates) | $23.57B | $23.62B | $27.23B | $20.09B |
| Part D (PDE audit of 5,000; beneficiary audit of 990) | Expansion | $1.46B | $1.28B | $1.95B | $0.57B |
|  | Ratio | $1.46B | $1.49B | $2.22B | $0.74B |
|  | Regression | $1.46B | $1.52B | $2.19B | $0.89B |
|  | Bootstrap simulation (parametric rates) | $1.46B | $1.46B | $1.69B | $1.23B |
| PERM (9 states, 520 payments each) | Expansion | $8.65B | $8.57B | $9.74B | $7.42B |
|  | Ratio | $8.65B | $8.52B | $9.70B | $7.38B |
|  | Regression | $8.65B | $8.57B | $9.67B | $7.43B |
|  | Bootstrap simulation (parametric rates) | $8.65B | $8.46B | $9.39B | $7.59B |
| EIPM (2,000 applications) | Expansion | $0.75B | $0.68B | $0.96B | $0.40B |
|  | Ratio | $0.75B | $0.68B | $0.96B | $0.40B |
|  | Regression | $0.75B | $0.69B | $0.96B | $0.41B |
|  | Bootstrap simulation (parametric rates) | $0.75B | $0.66B | $0.94B | $0.43B |
| CERT (37,651 claims) | Expansion | $28.61B | $28.85B | $30.47B | $27.22B |
|  | Ratio | $28.61B | $28.94B | $30.50B | $27.38B |
|  | Regression | $28.61B | $28.95B | $30.50B | $27.35B |
|  | Bootstrap simulation (parametric rates) | $28.61B | $28.81B | $30.02B | $27.47B |

**Gross improper payment rates (÷ total payments)**

| Program | Method | True gross | Estimated gross | Upper bound | Lower bound |
|---|---|---|---|---|---|
| Part C (audit of 990) | Expansion | 6.06% | 6.15% | 7.19% | 5.06% |
|  | Ratio | 6.06% | 6.13% | 7.16% | 5.10% |
|  | Regression | 6.06% | 6.10% | 7.11% | 5.14% |
|  | Bootstrap simulation (parametric rates) | 6.06% | 6.08% | 7.01% | 5.17% |
| Part D (PDE audit of 5,000; beneficiary audit of 990) | Expansion | 1.38% | 1.22% | 1.85% | 0.54% |
|  | Ratio | 1.38% | 1.41% | 2.10% | 0.70% |
|  | Regression | 1.38% | 1.44% | 2.07% | 0.84% |
|  | Bootstrap simulation (parametric rates) | 1.38% | 1.38% | 1.60% | 1.16% |
| PERM (9 states, 520 payments each) | Expansion | 6.09% | 6.04% | 6.86% | 5.23% |
|  | Ratio | 6.09% | 6.00% | 6.83% | 5.20% |
|  | Regression | 6.09% | 6.03% | 6.81% | 5.23% |
|  | Bootstrap simulation (parametric rates) | 6.09% | 5.96% | 6.61% | 5.34% |
| EIPM (2,000 applications) | Expansion | 0.92% | 0.83% | 1.17% | 0.49% |
|  | Ratio | 0.92% | 0.83% | 1.17% | 0.49% |
|  | Regression | 0.92% | 0.84% | 1.18% | 0.50% |
|  | Bootstrap simulation (parametric rates) | 0.92% | 0.81% | 1.16% | 0.53% |
| CERT (37,651 claims) | Expansion | 6.50% | 6.56% | 6.93% | 6.19% |
|  | Ratio | 6.50% | 6.58% | 6.93% | 6.22% |
|  | Regression | 6.50% | 6.58% | 6.93% | 6.22% |
|  | Bootstrap simulation (parametric rates) | 6.50% | 6.55% | 6.82% | 6.25% |

The tables come from [`shared/results/report/by_scenario.csv`](shared/results/report/by_scenario.csv) (audit years 1–25, the same audits for every method); `by_audit_year.parquet` has each audit year. These are illustrative designs; the configs say which values are not public.

## Findings and recommendations

**Findings** (gross rate, 25 audit years per program; details in [`manuscripts/`](manuscripts/)):

1. **Point accuracy.** Every method estimated the gross rate closely. The bootstrap simulation was as accurate as or more accurate than the analytic estimators in every program, with a mean absolute error of 1.5–6.6% of the true rate (and 16.6% in EIPM, where rare errors affected every method).
2. **Coverage.** The parametric-rate bootstrap interval contained the truth in 121 of 125 audit years (96.8%), as opposed to 111 of 125 (88.8%) for the ratio estimator and 108 of 125 (86.4%) for regression. The fixed-rate bootstrap (not shown in the tables) contained the truth in only 30 of 125. Reusing the audited rates in every iteration leaves out their sampling error.
3. **Width.** The parametric interval was 11–21% narrower than the ratio interval in Part C, PERM, EIPM, and CERT, and 63% narrower than the Part D expansion interval from the same PDE audit.
4. **Sparse measures.** Measures built from few audited errors (underpayments and EIPM technically improper payments) were undercovered by every method. The parametric bootstrap covered these measures in 19–20 of 25 audit years.
5. **Regression.** Fitting models within strata on basic beneficiary variables plus the amount paid changed little. In Part C, PERM, EIPM, and CERT, coverage and width were within about one audit year and a few percent of the ratio estimator. In Part D, drug cost and reaching the catastrophic phase narrowed the interval, but the interval covered the truth in only 15 of 25 audit years. With few large errors, the residuals of a better-fitting model understate the variance.

**Recommendations:**

1. **Use bootstrap simulation with parametric rates** for PIIA improper payment rates, and report the analytic ratio interval alongside it during a transition period.
2. **Do not use fixed-rate bootstrap intervals.**
3. **Consider smaller audits.** At current precision, the narrower intervals would allow audits roughly 20–38% smaller (Part C, PERM, EIPM, and CERT), which would lower review costs. These are projections, and two steps should come first:
   - confirm coverage directly at the reduced sizes;
   - check sparse components separately.
4. **Future research** should identify the optimal audit size for each program and test model + simulation alternatives (for example, hierarchical error rates, unit-level error models, resampled error sizes, and calibrated intervals).

## Design principles

1. **SQL does the work.** Generation, errors, the Part D benefit, calibration, sampling, the analytic estimators and scoring are DuckDB SQL. Python runs the files in order and runs the bootstrap simulation loop, which reruns each payment function 1,000 times per audit year (too slow in SQL).
2. **Errors are stated probabilities.** Calibration to a public figure is one closed-form multiplier, logged in `truth.json`.
3. **Every dollar is traceable.** Unit-level detail (HCCs, PDEs, payments) is exported.
4. **Reproducible to the byte.** Random draws are hashes of `(seed, stream, key)` in SQL and seeded PCG64 streams in the bootstrap simulation, money is `DECIMAL`, and floating-point sums run in a fixed order. Reruns give identical files at any thread count; `manifest.json` records SHA-256 hashes.
5. **Checked independently.** The SQL estimators are tested against a separate numpy implementation (`shared/tests/test_estimators.py`), and each bootstrap simulation payment function is tested to reproduce the SQL result to the cent for every unit (`shared/tests/test_simulation.py`).
