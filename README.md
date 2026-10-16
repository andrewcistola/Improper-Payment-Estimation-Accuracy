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
| [`part-c-ipm/`](part-c-ipm/) | Risk-score errors on capitated payments (Medicare Advantage) | Enrollees, HCCs, payments → unsupported HCCs, hierarchy moves, missing documentation, additional HCCs | Stratified SRS by risk tercile |
| [`part-d-ipm/`](part-d-ipm/) | Claim errors flowing through the benefit to reinsurance and subsidies | Beneficiaries, PDEs → PDE errors re-run through the post-IRA 2025 benefit | SRS of beneficiaries; the bootstrap simulation uses an audit sample of 5,000 PDEs and a beneficiary sample |
| [`perm-cert/`](perm-cert/) | Individual claim or benefit errors | PERM: state payment universes → claims and eligibility errors (9 states, true eligibility rates 2.00–4.00%). CERT: three skewed payment shapes → all-or-nothing errors at 5–95% | PERM: systematic selection within strata. CERT: SRS of 30 claims |
| [`eipm/`](eipm/) | Beneficiary subsidy eligibility (Marketplace APTC) | FFE applications and APTC → rare income, eligibility and documentation errors | Stratified SRS of ~2,000 |
| [`shared/`](shared/) | Code used by all four | Runner, random numbers, samplers | **The methods, written once**: expansion, ratio and regression (GREG) with normal intervals; the audit-finding bootstrap simulation loop; scoring |
| [`literature-review/`](literature-review/) | Background, program methods, evidence, bibliography | | |

Inside each program, the SQL files are numbered in the order they run, and each file's header states what it does and every probability or formula it uses. Each `config.yaml` lists the files it runs.

## Methods

| Method | Code | Interval |
|---|---|---|
| Expansion | `ipm_expansion` in [`shared/sql/lib/02_estimators.sql`](shared/sql/lib/02_estimators.sql) | Normal (Taylor linearization) |
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

Each cell counts audit years out of 25: how many of the 95% intervals contain the true rate. The parentheses count the intervals lying entirely above / entirely below the true rate. A valid 95% interval contains the truth in about 24 of 25 audit years, and by chance alone 22 or more happen 97% of the time.

| Program | Expansion | Ratio | Regression | Bootstrap simulation |
|---|---|---|---|---|
| Part C (n = 4,500) | 23/25 (0/2) | 24/25 (0/1) | 24/25 (0/1) | 7/25 (5/13) |
| Part D (n = 1,500 beneficiaries; bootstrap simulation: audit sample of 5,000 PDEs) | 24/25 (0/1) | 24/25 (0/1) | 24/25 (1/0) | 8/25 (6/11) |
| PERM overall (9 states × 25 audit years; n = 520 each) | 206/225 (3/16) | 205/225 (3/17) | 206/225 (3/16) | 52/225 (85/88) |
| PERM eligibility (9 states × 25 audit years) | 200/225 (1/24) | 200/225 (1/24) | 200/225 (1/24) | 61/225 (74/90) |
| EIPM (n = 2,000) | 22/25 (0/3) | 22/25 (0/3) | 22/25 (0/3) | 4/25 (6/15) |

**How close the point estimates get.** Each cell is the average error of the point estimate over the 25 audit years, as a % of the true rate: how far a year's estimate typically lands from the truth. The parentheses give the average signed error (bias): + means estimates run high, − low. Example: Part C expansion is 3.8% of a 6.06% true rate, so a year's estimate is typically about 0.23 percentage points off.

| Program | True rate | Expansion | Ratio | Regression | Bootstrap simulation |
|---|---|---|---|---|---|
| Part C | 6.06% | 3.8% (−0.1%) | 3.7% (−0.1%) | 3.7% (−0.1%) | 3.2% (−1.7%) |
| Part D | 3.98% | 15.6% (+6.5%) | 11.5% (+4.9%) | 9.8% (+5.7%) | 4.6% (−1.2%) |
| PERM overall (9 states) | 5.07–6.99% | 14.8% (−0.3%) | 14.8% (−0.3%) | 14.9% (−0.3%) | 12.5% (−0.1%) |
| PERM eligibility (9 states) | 2.00–4.00% | 25.7% (−0.3%) | 25.8% (−0.3%) | 25.8% (−0.2%) | 19.6% (−0.1%) |
| EIPM | 0.93% | 25.0% (−9.1%) | 25.3% (−9.1%) | 25.6% (−8.9%) | 23.3% (−5.7%) |

Every method is scored on the same 25 audit years: audit years 1–25 of the current runs, each an independent random sample. The PERM rows add up the 9 states, so coverage counts are out of 225 (9 × 25) and errors average over those 225 state-years. CERT (SRS of 30 claims, 12 populations, 25 audit years each) is in [`perm-cert/README.md`](perm-cert/README.md).

| Program | Audit years reported (every method) | Bootstrap simulation iterations per audit year |
|---|---|---|
| Part C | 25 | 1,000 |
| Part D | 25 (bootstrap simulation: each with its own audit sample of 5,000 PDEs and beneficiary sample of 108,000) | 1,000 |
| PERM | 25 per state | 1,000 |
| EIPM | 25 | 1,000 |
| CERT | 25 per population | 1,000 |

The tables come from [`shared/results/report/by_scenario.csv`](shared/results/report/by_scenario.csv), which puts the fabricated true improper payment next to each scenario's estimates and CIs for audit years 1–25; `by_audit_year.parquet` has every one of those audit years. Each `estimation/results/*/metrics.json` (and [`shared/results/all/summary.json`](shared/results/all/summary.json)) scores every audit year the current runs produced, which is more than 25 for some methods. These are illustrative designs; the sample sizes are not CMS's, and the configs say which values are not public.

## Design principles

1. **SQL does the work.** Generation, errors, the Part D benefit, calibration, sampling, the analytic estimators and scoring are DuckDB SQL. Python runs the files in order and runs the bootstrap simulation loop, which reruns each payment function 1,000 times per audit year (too slow in SQL).
2. **Errors are stated probabilities.** Calibration to a public figure is one closed-form multiplier, logged in `truth.json`.
3. **Every dollar is traceable.** Unit-level detail (HCCs, PDEs, payments) is exported.
4. **Reproducible to the byte.** Random draws are hashes of `(seed, stream, key)` in SQL and seeded PCG64 streams in the bootstrap simulation, money is `DECIMAL`, and floating-point sums run in a fixed order. Reruns give identical files at any thread count; `manifest.json` records SHA-256 hashes.
5. **Checked independently.** The SQL estimators are tested against a separate numpy implementation (`shared/tests/test_estimators.py`), and each bootstrap simulation payment function is tested to reproduce the SQL result to the cent for every unit (`shared/tests/test_simulation.py`).
