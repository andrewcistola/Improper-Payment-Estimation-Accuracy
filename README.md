# Bootstrap Simulation in Health Plan Payment Integrity

Does an audit-finding microsimulation estimate CMS improper payment rates validly? In this method, every audited row-level finding is assigned at random to units across the population, the payment function is rerun, and this is repeated 1,000 times. The study compares it with the expansion, ratio and regression estimators. It uses synthetic populations with fabricated errors, so the true improper payment is known. The test is a Monte Carlo study: running 25 audit years to assess how accurate each estimator is when the audit is repeated. A method is valid if its 95% interval contains the fabricated truth in about 95% of audit years.

**One audit per year.** Each audit year has one audit, drawn with the program's design, and every method gets only that audit. The analytic methods estimate their variance from it. The microsimulation assigns its findings exactly as audited, and the audit is never resampled. In Part D, the microsimulation's audit sample (5,000 PDEs) and beneficiary sample (108,000 beneficiaries) are both fixed for the audit year.

**Scope: PIIA improper payment rate estimation.** Recovery and extrapolation uses (contract-level RADV, provider overpayment demands) are out of scope. No PHI, no unit-level data from any source, and nothing non-public: every number is drawn from stated distributions and calibrated only to public aggregate results.

## Structure

Each of the four program folders has the same two parts:

- **`errors/`** builds an error-free population, applies fake errors, records the truth and checks it against public figures.
- **`estimation/`** samples that population with the program's design and estimates the improper payment rate with each method.

| Folder | Application | errors/ | estimation/ |
|---|---|---|---|
| [`part-c-ipm/`](part-c-ipm/) | Risk-score errors on capitated payments (Medicare Advantage) | Enrollees, HCCs, payments → unsupported HCCs, hierarchy moves, missing documentation, additional HCCs | Stratified SRS by risk tercile |
| [`part-d-ipm/`](part-d-ipm/) | Claim errors flowing through the benefit to reinsurance and subsidies | Beneficiaries, PDEs → PDE errors re-run through the post-IRA 2025 benefit | SRS of beneficiaries; the microsimulation uses an audit sample of 5,000 PDEs and a beneficiary sample |
| [`perm-cert/`](perm-cert/) | Individual claim or benefit errors | PERM: state payment universes → claims and eligibility errors (9 states, true eligibility rates 2.00–4.00%). CERT: three skewed payment shapes → all-or-nothing errors at 5–95% | PERM: systematic selection within strata. CERT: SRS of 30 claims |
| [`eipm/`](eipm/) | Beneficiary subsidy eligibility (Marketplace APTC) | FFE applications and APTC → rare income, eligibility and documentation errors | Stratified SRS of ~2,000 |
| [`shared/`](shared/) | Code used by all four | Runner, random numbers, samplers | **The methods, written once**: expansion, ratio and regression (GREG) with normal intervals; the audit-finding microsimulation loop; scoring |
| [`literature-review/`](literature-review/) | Background, program methods, evidence, bibliography | | |

Inside each program, the SQL files are numbered in the order they run, and each file's header states what it does and every probability or formula it uses. Each `config.yaml` lists the files it runs.

## Methods

| Method | Code | Interval |
|---|---|---|
| Expansion | `ipm_expansion` in [`shared/sql/lib/02_estimators.sql`](shared/sql/lib/02_estimators.sql) | Normal (Taylor linearization) |
| Ratio | `ipm_ratio`, same file | Normal (Taylor linearization) |
| Regression (GREG) | `ipm_regression`, same file | Normal (Taylor linearization) |
| Microsimulation (`simulation`) | [`shared/ipsim/simulation.py`](shared/ipsim/simulation.py) + each program's `estimation/*simulation.py` | 2.5th–97.5th percentiles of 1,000 iterations |

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

Add `--set reps=20 sim_reps=3 sim_iterations=100` (20 audit years, 3 of them run through the microsimulation at 100 iterations each) to any estimation run for a quick pilot, `--timing` to see each step's run time, and `--memory-limit 2GB` when running several configs at once.

## Results

Coverage of two-sided 95% intervals: the % of audit years in which the interval contains the true rate. The parentheses show the % of audit years in which the interval lies entirely above / entirely below the true rate; a well-calibrated interval misses about 2.5% on each side.

| Program | Expansion | Ratio | Regression | Microsimulation |
|---|---|---|---|---|
| Part C (n = 4,500) | 92.0 (0.0/8.0) | 96.0 (0.0/4.0) | 96.0 (0.0/4.0) | 28.0 (20.0/52.0) |
| Part D (n = 1,500 beneficiaries; microsimulation: audit sample of 5,000 PDEs) | 96.0 (0.0/4.0) | 96.0 (0.0/4.0) | 96.0 (4.0/0.0) | 32.0 (24.0/44.0) |
| PERM overall (9 states, n = 520 each) | 91.6 (1.3/7.1) | 91.1 (1.3/7.6) | 91.6 (1.3/7.1) | 23.1 (37.8/39.1) |
| PERM eligibility | 88.9 (0.4/10.7) | 88.9 (0.4/10.7) | 88.9 (0.4/10.7) | 27.1 (32.9/40.0) |
| EIPM (n = 2,000) | 88.0 (0.0/12.0) | 88.0 (0.0/12.0) | 88.0 (0.0/12.0) | 16.0 (24.0/60.0) |

Every method is scored on the same 25 audit years (audit years 1–25 of the current runs; each audit year is an independent random sample). With 25 audit years, a coverage near 95% is measured to about ±4.4 points. The PERM rows pool the 9 states (225 audit years, about ±1.5 points). CERT (SRS of 30 claims, 12 populations, 25 audit years each) is in [`perm-cert/README.md`](perm-cert/README.md).

| Program | Audit years reported (every method) | Microsimulation iterations per audit year |
|---|---|---|
| Part C | 25 | 1,000 |
| Part D | 25 (microsimulation: each with its own audit sample of 5,000 PDEs and beneficiary sample of 108,000) | 1,000 |
| PERM | 25 per state | 1,000 |
| EIPM | 25 | 1,000 |
| CERT | 25 per population | 1,000 |

The tables come from [`shared/results/report/by_scenario.csv`](shared/results/report/by_scenario.csv), which puts the fabricated true improper payment next to each scenario's estimates and CIs for audit years 1–25; `by_audit_year.parquet` has every one of those audit years. Each `estimation/results/*/metrics.json` (and [`shared/results/all/summary.json`](shared/results/all/summary.json)) scores every audit year the current runs produced, which is more than 25 for some methods. These are illustrative designs; the sample sizes are not CMS's, and the configs say which values are not public.

## Design principles

1. **SQL does the work.** Generation, errors, the Part D benefit, calibration, sampling, the analytic estimators and scoring are DuckDB SQL. Python runs the files in order and runs the microsimulation loop, which reruns each payment function 1,000 times per audit year (too slow in SQL).
2. **Errors are stated probabilities.** Calibration to a public figure is one closed-form multiplier, logged in `truth.json`.
3. **Every dollar is traceable.** Unit-level detail (HCCs, PDEs, payments) is exported.
4. **Reproducible to the byte.** Random draws are hashes of `(seed, stream, key)` in SQL and seeded PCG64 streams in the microsimulation, money is `DECIMAL`, and floating-point sums run in a fixed order. Reruns give identical files at any thread count; `manifest.json` records SHA-256 hashes.
5. **Checked independently.** The SQL estimators are tested against a separate numpy implementation (`shared/tests/test_estimators.py`), and each microsimulation payment function is tested to reproduce the SQL result to the cent for every unit (`shared/tests/test_simulation.py`).
