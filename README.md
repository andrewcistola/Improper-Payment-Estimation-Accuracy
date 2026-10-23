## Comparative Accuracy of Improper Payment Estimation Methods in Federal Health Programs: A Monte Carlo Evaluation of Analytic Estimators and Bootstrap Simulation

#### **Andrew Cistola, PhD, MPH** 
Manuscript and one-page summary: [`manuscripts/`](manuscripts/) · Companion literature review: [`literature-review/`](literature-review/) · **Replicate the study step by step: [`start-here/`](start-here/)** · Independent review and sign-off: [`qa/`](qa/) 

**Research question.** What is the comparative accuracy of the available methods for estimating improper payments in federal health programs?

The Payment Integrity Information Act of 2019 (PIIA) requires that every federal program at risk of significant improper payments produce a statistically valid estimate of those payments, along with a confidence interval. The Centers for Medicare & Medicaid Services (CMS) produces five such estimates: Medicare Part C, Medicare Part D, Medicaid (the Payment Error Rate Measurement, or PERM), the Marketplace advance premium tax credit (EIPM), and Medicare fee-for-service (the Comprehensive Error Rate Testing program, or CERT). Each program audits a probability sample of payments and projects the audited errors to the program as a whole. Depending on the program, this projection uses either design-based analytic estimators (expansion, ratio, or regression) or audit-finding simulation.

This repository contains a Monte Carlo study of the accuracy of these methods. In this study, accuracy has two parts:
- **Point accuracy:** how close the estimate is to the true improper payment.
- **Interval accuracy:** whether the 95% interval contains the truth in about 95% of repeated audits (coverage) and, among intervals that do, how narrow the interval is (width).

**Approach: Synthetic Data Run through Multiple Audit Years** For each program, this study builds a synthetic population with fabricated errors so that the true improper payment is known. Each population is calibrated only to public FY 2025 aggregates. The program's production-like audit is then drawn in 25 independent audit years, and the estimate and interval from each method are compared with the truth. Each audit year has one audit, drawn with the program's design, and every method uses only that audit. The analytic methods estimate their variance from the audit. The simulation uses the audit findings as audited and, in its parametric-bootstrap version, redraws only the error counts (as opposed to resampling the audit itself). Within each stratum, every population fabricates errors independently of payment size; because that is also the simulation's implicit model, each population is rebuilt with errors that depend on payment size as a robustness check ([`robustness/`](robustness/), Appendix D). In Part D, each audit year draws two audits: a stratified audit of 5,000 PDEs, used by the simulation and by the PDE-level analytic estimators (expansion with a plug-in benefit rerun, and the design-based PDE-level expansion and ratio estimators), and a simple random sample of 990 beneficiaries whose every PDE is reviewed (about 41,000 PDEs), used by the ratio and regression estimators; both are fixed for the audit year.

**Scope: PIIA improper payment rate estimation.** Recovery and extrapolation uses (for example, contract-level RADV or provider overpayment demands) are out of scope. This repository contains no PHI, no unit-level data from any source, and nothing non-public. Every number is drawn from stated distributions and calibrated only to public aggregate results.

**Methods Under Comparison:** This study compares the following approaches.
- **Expansion:** The average error per audited unit (enrollee, beneficiary, claim, or application) is multiplied by the number of units in the population, stratum by stratum. Expansion can apply to payments directly or to parts of a payment function audited separately (for example, risk score error).
- **Ratio:** The audited improper dollars are divided by the audited payments to produce an improper payment rate. This rate is then applied to the program's known total payments.
- **Regression:** Within each stratum, a regression model is fit on the audit using basic beneficiary variables and the amount paid, and this model predicts improper payments for every unit in the population. The prediction errors from the audit are then added back so that the total remains unbiased even if the model is imperfect.
- **Audit-finding simulation:** The audit findings (error rates, partial-error shares, and error sizes) are assigned at random to every unaudited unit, and the payment rules are rerun many times, while audited units keep their own findings. The estimate is the average across iterations, and the 95% interval runs from the 2.5th to the 97.5th percentile. In Part D, two further design-based estimators on the same 5,000-PDE audit (PDE expansion and PDE ratio, built from each audited PDE's marginal effect on Medicare's payment) give the simulation a fair same-audit comparator.

**Confidence Intervals:** Expansion and ratio report a normal 95% interval (the estimate ± 1.96 standard errors, from the stratified design with a finite population correction). Regression uses the same formula on the prediction errors from the audit (residuals) with a t multiplier, so every analytic interval comes from a single audit. This study compared two versions of the simulation:
- **Plug-in (fixed rates):** The audited error rates are reused in every iteration. The point estimates from this version are as accurate as or more accurate than those from the analytic estimators. However, its intervals omit the sampling error of the audited rates and are invalid.
- **Parametric-bootstrap (parametric rates):** Before each iteration, the audited error and partial-error counts are redrawn from their binomial sampling distributions (a parametric bootstrap of the rates). This version is the one reported.

The results below report the parametric version and, for Part D, the design-based PDE-level estimators on the same audit. The full write-up, including the plug-in comparison and the Appendix D calibration and robustness runs, is available in [`manuscripts/`](manuscripts/) (manuscript and one-page summary). An independent re-run and review of the study, and the changes it led to, are in [`qa/Claude/`](qa/Claude/).

## Structure

Each of the five program folders has the same two parts:

- **`errors/`** builds an error-free population, applies fake errors, records the truth and checks it against public figures.
- **`estimation/`** samples that population with the program's design and estimates the improper payment rate with each method.

| Folder | Application | errors/ | estimation/ |
|---|---|---|---|
| [`part-c-ipm/`](part-c-ipm/) | Risk-score errors on capitated payments (Medicare Advantage) | Enrollees, HCCs, payments → unsupported HCCs, hierarchy moves, missing documentation, additional HCCs | Audit of 990 enrollees, 330 per risk-score tercile (stratified SRS); overpayments, underpayments, gross and net |
| [`part-d-ipm/`](part-d-ipm/) | Claim errors flowing through the benefit to reinsurance and subsidies | Beneficiaries, PDEs → PDE errors re-run through the post-IRA 2025 benefit | SRS of beneficiaries; the simulation uses an audit sample of 5,000 PDEs and a beneficiary sample |
| [`perm/`](perm/) | Medicaid claim and eligibility errors | State payment universes → claims and eligibility errors (9 states, true eligibility rates 2.00–4.00%) | Neyman allocation over payment type × quintile, systematic selection, 520 per state; national pooling |
| [`cert/`](cert/) | Medicare FFS claim errors | National claims in four claim types → whole-claim and partial over- and underpayments calibrated to FY 2025 | 37,651 claims, FY 2025 count per claim type, Neyman across payment quintiles |
| [`eipm/`](eipm/) | Beneficiary subsidy eligibility (Marketplace APTC) | FFE applications and APTC → rare overpayments: technically improper (whole APTC) and monetary (income) | Stratified SRS of 2,000, Neyman allocation over APTC quintiles |
| [`shared/`](shared/) | Code used by all five | Runner, random numbers, samplers | **The methods, written once**: expansion and ratio with normal intervals; regression (models fit within strata, residual interval); the audit-finding simulation loop; scoring |
| [`literature-review/`](literature-review/) | Standalone narrative review of the comparative accuracy of improper payment estimation methods (Markdown, PDF, Word) | | |
| [`manuscripts/`](manuscripts/) | Manuscript and one-page summary of the Monte Carlo study | | |
| [`start-here/`](start-here/) | Step-by-step replication guide for readers with no programming experience: software to install, one command that runs every stage, and a check against the published results | | |
| [`qa/`](qa/) | Independent review: a checklist workbook (re-run, every key assumption, results), a holding space for each reviewer's re-run logs and outputs, and a sign-off form | | |
| [`robustness/`](robustness/) | Appendix D: interval calibration over 100 audit years and size-dependent error scenarios (`size_beta`) for every program | | |

Inside each program, the SQL files are numbered in the order they run, and each file's header states what it does and every probability or formula it uses. Each `config.yaml` lists the files it runs.

## Methods

| Method | Code | Interval |
|---|---|---|
| Expansion | `ipm_expansion` in [`shared/sql/lib/02_estimators.sql`](shared/sql/lib/02_estimators.sql); Part C uses a risk-score expansion ([`part-c-ipm/estimation/sql/10_expansion.sql`](part-c-ipm/estimation/sql/10_expansion.sql)) | Normal (Taylor linearization) |
| Ratio | `ipm_ratio`, same file | Normal (Taylor linearization) |
| Regression | [`shared/ipsim/regression.py`](shared/ipsim/regression.py) + each program's `30_regression.sql` (predictors) | Normal (t), from the audit residuals |
| Simulation, parametric rates (`simulation`; reported) | [`shared/ipsim/simulation.py`](shared/ipsim/simulation.py) + each program's `estimation/simulation.py`; `sim_rates: parametric` (default): each stratum's error count redrawn as Binomial(n, rate) and its partial count as Binomial(f̃, share) before every iteration | 2.5th–97.5th percentiles of 1,000 iterations |
| Simulation, plug-in fixed rates (comparison only) | Same, `--set sim_rates=fixed`: the audited rates in every iteration. Results in `<program>/estimation/results_fixed/` | Same |
| Part D PDE expansion and PDE ratio (`pde_expansion`, `pde_ratio`) | [`part-d-ipm/estimation/simulation.py`](part-d-ipm/estimation/simulation.py) (`run_pde_estimators`): each audited PDE's marginal Medicare-payment effect, then the shared expansion / ratio macros | Normal |

## Run

For a step-by-step guide that assumes no programming experience, see [`start-here/`](start-here/README.md). The whole study also runs with one command, `python start-here/run_all.py`. The individual steps are:

```bash
pip install -e ".[all]"                       # duckdb (pinned), pyarrow, numpy, numba, pyyaml, scipy; [all] adds pandas, matplotlib, pytest
# 1. populations (a few minutes)
ipsim part-c-ipm/errors/config.yaml part-d-ipm/errors/config.yaml eipm/errors/config.yaml \
      perm/errors/config.yaml cert/errors/config.yaml
# 2. estimation (each program writes estimation/results/)
ipsim part-c-ipm/estimation/config.yaml part-d-ipm/estimation/config.yaml eipm/estimation/config.yaml \
      perm/estimation/config.yaml perm/estimation/national.yaml cert/estimation/config.yaml
ipsim shared/summary.yaml                     # all metrics in one table
ipsim shared/report.yaml                      # truth vs every estimate and CI, audit years 1-25 (by_scenario.csv, by_audit_year)
python -m pytest -q shared/tests              # tests
```

Add `--set reps=20 sim_reps=3 sim_iterations=100` (20 audit years, 3 of them run through the simulation at 100 iterations each) to any estimation run for a quick pilot, `--timing` to see each step's run time, and `--memory-limit 2GB` when running several configs at once.

## Results

Each row gives the true gross improper payment and, over the 25 audit years, the median point estimate and the median upper and lower bounds of the 95% interval. Gross = overpayments + underpayments, netted within each enrollee, beneficiary or claim first (EIPM and PERM have overpayments only). Dollars are national program dollars: each program's population is scaled by its own factor (Part C × 100, Part D × 500, EIPM × 100, PERM × 200, CERT × 200). Overpayments, underpayments, net, and how often each interval contains the truth are in each program's README ([Part C](part-c-ipm/README.md#results-25-audit-years), [Part D](part-d-ipm/README.md#results-25-audit-years), [PERM](perm/README.md#results-25-audit-years), [EIPM](eipm/README.md#results-25-audit-years), [CERT](cert/README.md#results-25-audit-years)).

**Gross improper payments (national dollars)**

| Program | Method | True gross | Estimated gross | Upper bound | Lower bound |
|---|---|---|---|---|---|
| Part C (audit of 990) | Expansion | $23.57B | $23.92B | $27.96B | $19.69B |
|  | Ratio | $23.57B | $23.82B | $27.81B | $19.83B |
|  | Regression | $23.57B | $23.70B | $27.64B | $19.97B |
|  | Simulation (parametric rates) | $23.57B | $24.01B | $27.73B | $20.47B |
| Part D (PDE audit of 5,000; beneficiary audit of 990, every PDE reviewed) | Expansion | $1.46B | $1.28B | $1.95B | $0.57B |
|  | Ratio | $1.46B | $1.49B | $2.22B | $0.74B |
|  | Regression | $1.46B | $1.52B | $2.19B | $0.89B |
|  | PDE expansion (same audit) | $1.46B | $1.41B | $2.37B | $0.28B |
|  | PDE ratio (same audit) | $1.46B | $1.42B | $2.48B | $0.31B |
|  | Simulation (parametric rates) | $1.46B | $1.46B | $1.70B | $1.23B |
| PERM (9 states, 520 payments each) | Expansion | $8.65B | $8.57B | $9.74B | $7.42B |
|  | Ratio | $8.65B | $8.52B | $9.70B | $7.38B |
|  | Regression | $8.65B | $8.57B | $9.67B | $7.43B |
|  | Simulation (parametric rates) | $8.65B | $8.49B | $9.40B | $7.61B |
| EIPM (2,000 applications) | Expansion | $0.75B | $0.68B | $0.96B | $0.40B |
|  | Ratio | $0.75B | $0.68B | $0.96B | $0.40B |
|  | Regression | $0.75B | $0.69B | $0.96B | $0.41B |
|  | Simulation (parametric rates) | $0.75B | $0.67B | $0.94B | $0.45B |
| CERT (37,651 claims) | Expansion | $28.61B | $28.85B | $30.47B | $27.22B |
|  | Ratio | $28.61B | $28.94B | $30.50B | $27.38B |
|  | Regression | $28.61B | $28.95B | $30.50B | $27.35B |
|  | Simulation (parametric rates) | $28.61B | $28.83B | $30.02B | $27.59B |

**Gross improper payment rates (÷ total payments)**

| Program | Method | True gross | Estimated gross | Upper bound | Lower bound |
|---|---|---|---|---|---|
| Part C (audit of 990) | Expansion | 6.06% | 6.15% | 7.19% | 5.06% |
|  | Ratio | 6.06% | 6.13% | 7.16% | 5.10% |
|  | Regression | 6.06% | 6.10% | 7.11% | 5.14% |
|  | Simulation (parametric rates) | 6.06% | 6.18% | 7.13% | 5.27% |
| Part D (PDE audit of 5,000; beneficiary audit of 990, every PDE reviewed) | Expansion | 1.38% | 1.22% | 1.85% | 0.54% |
|  | Ratio | 1.38% | 1.41% | 2.10% | 0.70% |
|  | Regression | 1.38% | 1.44% | 2.07% | 0.84% |
|  | PDE expansion (same audit) | 1.38% | 1.33% | 2.24% | 0.26% |
|  | PDE ratio (same audit) | 1.38% | 1.34% | 2.35% | 0.29% |
|  | Simulation (parametric rates) | 1.38% | 1.38% | 1.61% | 1.16% |
| PERM (9 states, 520 payments each) | Expansion | 6.09% | 6.04% | 6.86% | 5.23% |
|  | Ratio | 6.09% | 6.00% | 6.83% | 5.20% |
|  | Regression | 6.09% | 6.03% | 6.81% | 5.23% |
|  | Simulation (parametric rates) | 6.09% | 5.98% | 6.62% | 5.36% |
| EIPM (2,000 applications) | Expansion | 0.92% | 0.83% | 1.17% | 0.49% |
|  | Ratio | 0.92% | 0.83% | 1.17% | 0.49% |
|  | Regression | 0.92% | 0.84% | 1.18% | 0.50% |
|  | Simulation (parametric rates) | 0.92% | 0.83% | 1.15% | 0.55% |
| CERT (37,651 claims) | Expansion | 6.50% | 6.56% | 6.93% | 6.19% |
|  | Ratio | 6.50% | 6.58% | 6.93% | 6.22% |
|  | Regression | 6.50% | 6.58% | 6.93% | 6.22% |
|  | Simulation (parametric rates) | 6.50% | 6.55% | 6.82% | 6.27% |

The tables come from [`shared/results/report/by_scenario.csv`](shared/results/report/by_scenario.csv) (audit years 1–25, the same audits for every method); `by_audit_year.parquet` has each audit year. These are illustrative designs; the configs say which values are not public.

## Findings and recommendations

**Findings** (gross rate; 25 audit years per program, 100 for calibration; details in [`manuscripts/`](manuscripts/) and Appendix D):

1. **Plug-in simulation intervals are invalid.** Reusing the audited error rates in every iteration leaves out their sampling error: the interval was 5–21% as wide as the analytic interval and contained the truth in 31 of 125 audit years (25%).
2. **Redrawing the rates restores coverage.** The parametric-rate interval contained the truth in 121 of 125 audit years (96.8%), as opposed to 111 of 125 for the ratio estimator and 108 for regression, and was 9–23% narrower than the ratio interval in Part C, PERM, EIPM and CERT. Over 100 audit years, however, it was 5–12% narrower than the simulation estimator's own sampling variability in four programs (ratio of half-width to 1.96 × empirical SD: 0.94, 0.95, 0.93, 0.88; CERT 1.13), so part of that gain is an interval that is too short.
3. **The real efficiency gain is program-specific.** The standard deviation of the simulation's point estimate over 100 audit years was 3% (Part C), 4% (EIPM), 23% (PERM), 35% (CERT) and 72% (Part D) below the ratio estimator's.
4. **The simulation's accuracy rests on one stated assumption that the analytic estimators do not need.** The simulation borrows only the audited error *counts* and takes every unit's size from the population, so it is unbiased only if error probability is independent of payment size within a donor kind, which the base populations satisfy by construction. When each population was rebuilt with error probability rising with payment size, the simulation ran low by 3% (Part C), 8% (EIPM), 14% (PERM), 22% (CERT) and 65% (Part D) and its interval covered in 24, 21, 6, 0 and 0 of 25 audit years; with error probability falling with payment size it ran high by 9% (Part C), 7% (PERM), 12% (CERT) and 148% (Part D) and low by 2% (EIPM), with coverage of 18, 24, 18, 0 and 0. The ratio estimator stayed within 2% of the truth (5–8% in EIPM and Part D, as in the base population) and covered in 22–25 of 25 in every scenario. **Borrowing findings within payment deciles inside each stratum** (`sim_kind_deciles: 10`) removed the bias in PERM (−14% → −4%, +7% → +0.4%; coverage 22 and 25) at little cost in precision, and removed half to three-quarters of it in CERT (−22% → −5%; +12% → +1.6%) and Part D (−65% → −38%; +148% → +19%), whose payments are heavy-tailed within strata, at the cost of most of the precision gain (Appendix D, Tables D4–D6).
5. **Sparse measures** (underpayments, EIPM technically improper payments) were undercovered by most methods, with misses below the truth; the parametric interval covered them in 19–25 of 25 audit years.
6. **Regression** with basic beneficiary variables changed little; in Part D a better-fitting model narrowed the interval but covered in only 15 of 25 audit years.

**Recommendations:**

1. **Adopt parametric-rate simulation for PIIA improper payment rates, with its central assumption stated:** within each donor kind, error incidence is independent of payment size. Discontinue any plug-in (fixed-rate) simulation interval; the Part D interval algorithm is not public and should be checked for this feature.
2. **Verify the assumption every cycle from the audit itself:** tabulate audited error rates and taints across payment deciles within strata (trend test or logistic regression of error on log payment with stratum effects, pooled across strata and cycles), and report the simulation and the design-based ratio estimate together — a drift between them is the test and costs no additional review.
3. **Where the check shows an association, post-stratify the donor kinds on payment decile.** Where payments within strata are moderately dispersed (as in the PERM population here) this removes the bias and keeps most of the precision; where they are heavy-tailed (CERT, Part D) it is a partial remedy, and the program should report ratio and simulation together and treat their difference as the impact of the assumption until a unit-level error model is validated.
4. **Reduce audit sizes only after the check has passed and coverage has been confirmed at the smaller size.** Projected sizes for today's precision: 83% (Part C), 63% (PERM), 77% (EIPM), 59% (CERT) of the current audit from Table 4, or 93 / 60 / 93 / 42% from the calibrated standard deviations; gross rate only. Check sparse components separately under any method.
5. **Future research** should replace the independence assumption with a unit-level error model fit on the audit, identify the optimal audit size for each program, and extend the design to state PERM eligibility rates, State-based Exchanges and one-sided recovery bounds.

## Design principles

1. **SQL does the work.** Generation, errors, the Part D benefit, calibration, sampling, the analytic estimators and scoring are DuckDB SQL. Python runs the files in order and runs the simulation loop, which reruns each payment function 1,000 times per audit year (too slow in SQL).
2. **Errors are stated probabilities.** Calibration to a public figure is one closed-form multiplier, logged in `truth.json`.
3. **Every dollar is traceable.** Unit-level detail (HCCs, PDEs, payments) is exported.
4. **Reproducible to the byte within one pinned environment.** Random draws are hashes of `(seed, stream, key)` in SQL and seeded PCG64 streams in the simulation, money is `DECIMAL`, and floating-point sums run in a fixed order. Reruns give identical files at any thread count; `manifest.json` records SHA-256 hashes and the DuckDB, numpy, scipy, numba and BLAS versions, and `requirements-lock.txt` pins the versions used for the published results.
5. **Checked independently.** The SQL estimators are tested against a separate numpy implementation (`shared/tests/test_estimators.py`), and each simulation payment function is tested to reproduce the SQL result to the cent for every unit (`shared/tests/test_simulation.py`).
