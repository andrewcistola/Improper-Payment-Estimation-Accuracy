# Bootstrap Simulation in Health Plan Payment Integrity

Does an audit-finding bootstrap simulation estimate CMS improper payment rates validly? In this method, every audited row-level finding is assigned at random to units across the population, the payment function is rerun, and this is repeated 1,000 times. The study compares it with the expansion, ratio and regression estimators. It uses synthetic populations with fabricated errors, so the true improper payment is known. The test is a Monte Carlo study: running 25 audit years to assess how accurate each estimator is when the audit is repeated. A method is valid if its 95% interval contains the fabricated truth in about 95% of audit years.

**One audit per year.** Each audit year has one audit, drawn with the program's design, and every method gets only that audit. The analytic methods estimate their variance from it. The bootstrap simulation assigns its findings exactly as audited, and the audit is never resampled. In Part D, the bootstrap simulation's audit sample (5,000 PDEs) and beneficiary sample (108,000 beneficiaries) are both fixed for the audit year.

**Scope: PIIA improper payment rate estimation.** Recovery and extrapolation uses (contract-level RADV, provider overpayment demands) are out of scope. No PHI, no unit-level data from any source, and nothing non-public: every number is drawn from stated distributions and calibrated only to public aggregate results.

## Structure

Each of the four program folders has the same two parts:

- **`errors/`** builds an error-free population, applies fake errors, records the truth and checks it against public figures.
- **`estimation/`** samples that population with the program's design and estimates the improper payment rate with each method.

| Folder | Application | errors/ | estimation/ |
|---|---|---|---|
| [`part-c-ipm/`](part-c-ipm/) | Risk-score errors on capitated payments (Medicare Advantage) | Enrollees, HCCs, payments → unsupported HCCs, hierarchy moves, missing documentation, additional HCCs | Audit of 990 enrollees, 330 per risk-score tercile (stratified SRS); overpayments, underpayments, gross and net |
| [`part-d-ipm/`](part-d-ipm/) | Claim errors flowing through the benefit to reinsurance and subsidies | Beneficiaries, PDEs → PDE errors re-run through the post-IRA 2025 benefit | SRS of beneficiaries; the bootstrap simulation uses an audit sample of 5,000 PDEs and a beneficiary sample |
| [`perm-cert/`](perm-cert/) | Individual claim or benefit errors | PERM: state payment universes → claims and eligibility errors (9 states, true eligibility rates 2.00–4.00%). CERT: three skewed payment shapes → all-or-nothing errors at 5–95% | PERM: systematic selection within strata. CERT: SRS of 30 claims |
| [`eipm/`](eipm/) | Beneficiary subsidy eligibility (Marketplace APTC) | FFE applications and APTC → rare income, eligibility and documentation errors | Stratified SRS of ~2,000 |
| [`shared/`](shared/) | Code used by all four | Runner, random numbers, samplers | **The methods, written once**: expansion, ratio and regression (GREG) with normal intervals; the audit-finding bootstrap simulation loop; scoring |
| [`literature-review/`](literature-review/) | Background, program methods, evidence, bibliography | | |

Inside each program, the SQL files are numbered in the order they run, and each file's header states what it does and every probability or formula it uses. Each `config.yaml` lists the files it runs.

## Methods

| Method | Code | Interval |
|---|---|---|
| Expansion | `ipm_expansion` in [`shared/sql/lib/02_estimators.sql`](shared/sql/lib/02_estimators.sql); Part C uses a risk-score expansion ([`part-c-ipm/estimation/sql/10_expansion.sql`](part-c-ipm/estimation/sql/10_expansion.sql)) | Normal (Taylor linearization) |
| Ratio | `ipm_ratio`, same file | Normal (Taylor linearization) |
| Regression (GREG) | `ipm_regression`, same file | Normal (Taylor linearization) |
| Bootstrap simulation (`simulation`) | [`shared/ipsim/simulation.py`](shared/ipsim/simulation.py) + each program's `estimation/*simulation.py` | 2.5th–97.5th percentiles of 1,000 iterations |

## Run

```bash
pip install -e .                              # duckdb (pinned), pyarrow, numpy, numba, pyyaml
# 1. populations (about 1 minute; run cert.yaml before cert_benchmark.yaml)
ipsim part-c-ipm/errors/config.yaml part-d-ipm/errors/config.yaml eipm/errors/config.yaml \
      perm-cert/errors/perm.yaml perm-cert/errors/cert.yaml perm-cert/errors/cert_benchmark.yaml
# 2. estimation (each program writes estimation/results/)
ipsim part-c-ipm/estimation/config.yaml part-d-ipm/estimation/config.yaml eipm/estimation/config.yaml \
      perm-cert/estimation/perm.yaml perm-cert/estimation/cert.yaml
ipsim shared/summary.yaml                     # all metrics in one table
ipsim shared/report.yaml                      # truth vs every estimate and CI, audit years 1-25 (by_scenario.csv, by_audit_year)
python -m pytest -q shared/tests              # tests
```

Add `--set reps=20 sim_reps=3 sim_iterations=100` (20 audit years, 3 of them run through the bootstrap simulation at 100 iterations each) to any estimation run for a quick pilot, `--timing` to see each step's run time, and `--memory-limit 2GB` when running several configs at once.

## Results

> **Reworking program by program.** Each program's audit design, population and methods are being revised in turn. Part C and Part D are done; the other programs are placeholders until theirs is.

Each row gives the true gross improper payment and, over the 25 audit years, the median point estimate and the median upper and lower bounds of the 95% interval. Gross = overpayments + underpayments, netted within each enrollee or beneficiary first. Dollars are national program dollars: each program's population is scaled by its own factor (Part C × 100, Part D × 500, EIPM × 100, PERM × 200; CERT is not scaled). Overpayments, underpayments, net, and how often each interval contains the truth are in each program's README ([Part C](part-c-ipm/README.md#results-25-audit-years), [Part D](part-d-ipm/README.md#results-25-audit-years)).

**Gross improper payments (national dollars)**

| Program | Method | True gross | Estimated gross | Upper bound | Lower bound |
|---|---|---|---|---|---|
| Part C (audit of 990) | Expansion | $23.57B | $23.92B | $27.96B | $19.69B |
|  | Ratio | $23.57B | $23.82B | $27.81B | $19.83B |
|  | Regression | $23.57B | $23.94B | $27.78B | $20.05B |
|  | Bootstrap simulation (fixed rates) | $23.57B | $23.56B | $23.76B | $23.35B |
| Part D (PDE audit of 5,000; beneficiary audit of 990) | Expansion | $1.46B | $1.28B | $1.95B | $0.57B |
|  | Ratio | $1.46B | $1.49B | $2.22B | $0.74B |
|  | Regression | $1.46B | $1.48B | $2.22B | $0.77B |
|  | Bootstrap simulation (fixed rates) | $1.46B | $1.46B | $1.52B | $1.39B |
| PERM | | _pending rework_ | | | |
| EIPM | | _pending rework_ | | | |
| CERT | | _pending rework_ | | | |

**Gross improper payment rates (÷ total payments)**

| Program | Method | True gross | Estimated gross | Upper bound | Lower bound |
|---|---|---|---|---|---|
| Part C (audit of 990) | Expansion | 6.06% | 6.15% | 7.19% | 5.06% |
|  | Ratio | 6.06% | 6.13% | 7.16% | 5.10% |
|  | Regression | 6.06% | 6.16% | 7.15% | 5.16% |
|  | Bootstrap simulation (fixed rates) | 6.06% | 6.06% | 6.11% | 6.01% |
| Part D (PDE audit of 5,000; beneficiary audit of 990) | Expansion | 1.38% | 1.22% | 1.85% | 0.54% |
|  | Ratio | 1.38% | 1.41% | 2.10% | 0.70% |
|  | Regression | 1.38% | 1.41% | 2.11% | 0.73% |
|  | Bootstrap simulation (fixed rates) | 1.38% | 1.38% | 1.44% | 1.32% |
| PERM | | _pending rework_ | | | |
| EIPM | | _pending rework_ | | | |
| CERT | | _pending rework_ | | | |

The tables come from [`shared/results/report/by_scenario.csv`](shared/results/report/by_scenario.csv) (audit years 1–25, the same audits for every method); `by_audit_year.parquet` has each audit year. These are illustrative designs; the configs say which values are not public.

## Design principles

1. **SQL does the work.** Generation, errors, the Part D benefit, calibration, sampling, the analytic estimators and scoring are DuckDB SQL. Python runs the files in order and runs the bootstrap simulation loop, which reruns each payment function 1,000 times per audit year (too slow in SQL).
2. **Errors are stated probabilities.** Calibration to a public figure is one closed-form multiplier, logged in `truth.json`.
3. **Every dollar is traceable.** Unit-level detail (HCCs, PDEs, payments) is exported.
4. **Reproducible to the byte.** Random draws are hashes of `(seed, stream, key)` in SQL and seeded PCG64 streams in the bootstrap simulation, money is `DECIMAL`, and floating-point sums run in a fixed order. Reruns give identical files at any thread count; `manifest.json` records SHA-256 hashes.
5. **Checked independently.** The SQL estimators are tested against a separate numpy implementation (`shared/tests/test_estimators.py`), and each bootstrap simulation payment function is tested to reproduce the SQL result to the cent for every unit (`shared/tests/test_simulation.py`).
