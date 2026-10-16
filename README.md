# Bootstrap Simulation in Health Plan Payment Integrity

Do bootstrap ("simulation") intervals estimate CMS improper payment rates more accurately than the normal-theory intervals used today? This repository answers that with synthetic populations whose true improper payments are known. Each program's sampling design is rerun hundreds of times, and every estimator is scored against the truth.

**Scope: PIIA improper payment rate estimation.** Recovery and extrapolation uses (contract-level RADV, provider overpayment demands) are out of scope. No PHI, no unit-level data from any source, and nothing non-public: every number is drawn from stated distributions and calibrated only to public aggregate results.

## Structure

Each of the four program folders has the same two parts:

- **`errors/`** builds an error-free population, applies fake errors, records the truth and checks it against public figures.
- **`estimation/`** samples that population with the program's design and estimates the improper payment rate with each method.

| Folder | Application | errors/ | estimation/ |
|---|---|---|---|
| [`part-c-ipm/`](part-c-ipm/) | Risk-score errors on capitated payments (Medicare Advantage) | Enrollees, HCCs, payments → unsupported HCCs, hierarchy moves, missing documentation, additional HCCs | Stratified SRS by risk tercile |
| [`part-d-ipm/`](part-d-ipm/) | Claim errors flowing through the benefit to reinsurance and subsidies | Beneficiaries, PDEs → PDE errors re-run through the post-IRA 2025 benefit | SRS of beneficiaries |
| [`perm-cert/`](perm-cert/) | Individual claim or benefit errors | PERM: state payment universes → claims and eligibility errors (9 states, true eligibility rates 2.00–4.00%). CERT: three skewed payment shapes → all-or-nothing errors at 5–95% | PERM: systematic selection within strata. CERT: SRS of 30 claims |
| [`eipm/`](eipm/) | Beneficiary subsidy eligibility (Marketplace APTC) | FFE applications and APTC → rare income, eligibility and documentation errors | Stratified SRS of ~2,000 |
| [`shared/`](shared/) | Code used by all four | Runner, random numbers, samplers | **The four methods, written once**: expansion, ratio, regression (GREG), simulation (rescaled bootstrap: percentile, bootstrap-t, BCa); scoring |
| [`literature-review/`](literature-review/) | Background, program methods, evidence, bibliography | | |
| `aim-1/` … `aim-4/` | Specific Aims (to be defined) | | |

Inside each program, the SQL files are numbered in the order they run, and each file's header states what it does and every probability or formula it uses. Each `config.yaml` lists the files it runs.

## Run

```bash
pip install -e .                              # duckdb (pinned), pyarrow, numpy, pyyaml
# 1. populations (about 1 minute; run cert.yaml before cert_benchmark.yaml)
ipsim part-c-ipm/errors/config.yaml part-d-ipm/errors/config.yaml eipm/errors/config.yaml \
      perm-cert/errors/perm.yaml perm-cert/errors/cert.yaml perm-cert/errors/cert_benchmark.yaml
# 2. estimation (each program writes estimation/results/)
ipsim part-c-ipm/estimation/config.yaml part-d-ipm/estimation/config.yaml eipm/estimation/config.yaml \
      perm-cert/estimation/perm.yaml perm-cert/estimation/cert.yaml
ipsim shared/summary.yaml                     # all metrics in one table
ipsim shared/report.yaml                      # truth vs every estimate and CI (by_scenario.csv, by_sample)
python -m pytest -q shared/tests              # tests
```

Add `--set reps=20 boot_reps=100` to any estimation run for a quick pilot, and `--timing` to see each step's run time.

## First results (pilot settings: 200 samples × 500 bootstrap replicates; CERT 1,000 × 1,000)

Coverage of two-sided 95% intervals, in %. The parentheses show the share of intervals lying entirely above / entirely below the true rate; a well-calibrated interval misses about 2.5% on each side. The Monte Carlo standard error of coverage is about ±1.5 points (±0.7 for CERT).

| Program | Expansion | Ratio | Regression | Bootstrap percentile | Bootstrap BCa | Bootstrap-t |
|---|---|---|---|---|---|---|
| Part C (n = 4,500) | 94.5 (2.0/3.5) | 95.0 (2.5/2.5) | 96.0 (1.5/2.5) | 94.5 (3.0/2.5) | 94.0 (3.5/2.5) | 94.0 (3.0/3.0) |
| Part D (n = 1,500) | 94.0 (0.5/5.5) | 94.0 (0.5/5.5) | 90.5 (4.0/5.5) | 94.5 (0.5/5.0) | 93.0 (3.5/3.5) | 95.0 (2.0/3.0) |
| PERM overall (9 states, n = 520 each) | 92.6 (1.2/6.2) | 92.5 (1.3/6.2) | 92.8 (1.2/6.1) | 92.8 (1.6/5.6) | 93.6 (2.4/4.0) | 95.4 (1.6/3.1) |
| PERM eligibility | 91.0 (0.4/8.6) | 90.9 (0.4/8.7) | 90.9 (0.4/8.6) | 91.3 (1.1/7.6) | 92.8 (2.0/5.2) | 96.1 (0.7/3.2) |
| EIPM (n = 2,000) | 91.0 (1.0/8.0) | 91.0 (1.0/8.0) | 91.0 (1.0/8.0) | 90.5 (1.0/8.5) | 90.0 (2.5/7.5) | 92.5 (2.5/5.0) |

What the pilot shows:

- **Large samples behave.** In Part C every method covers about 95%, with balanced tails.
- **Skew pushes the misses below the truth.** In Part D, PERM and EIPM, normal-theory intervals undercover or miss mostly on the low side: the interval lies below the true rate far more often than above it.
- **Bootstrap-t restores coverage and balance, at a cost in width.** It is the only method near 95% with balanced tails in Part D and PERM, and it is the best in EIPM (92.5%). Its intervals are wider, though: for PERM eligibility the median width is 1.68× the true rate, against 1.18× for normal intervals.
- **The percentile bootstrap does not fix the skew.** Its coverage and tail pattern track the normal interval's.
- **Rare errors defeat every method.** EIPM has about 30 errors per sample, and nothing reaches 95%.
- **Small samples fail at the extremes.** In CERT (30 claims), samples with no errors (5% error rate) or only errors (95% error rate) give degenerate estimates. Every method fails there, and bootstrap-t intervals become extremely wide. See [`perm-cert/README.md`](perm-cert/README.md).

Per-program details are in each `estimation/results/*/metrics.json`, and everything in one table is in [`shared/results/all/summary.json`](shared/results/all/summary.json). [`shared/results/report/by_scenario.csv`](shared/results/report/by_scenario.csv) puts the fabricated true improper payment next to each scenario's estimates and CIs; `by_sample.parquet` has every sample. These are pilot runs on illustrative designs; the sample sizes are not CMS's, and the configs say which values are not public.

## Design principles

1. **SQL does the work.** Generation, errors, the Part D benefit, calibration, sampling, estimation and scoring are DuckDB SQL. Python only runs the files in order.
2. **Errors are stated probabilities.** Calibration to a public figure is one closed-form multiplier, logged in `truth.json`.
3. **Every dollar is traceable.** Unit-level detail (HCCs, PDEs, payments) is exported.
4. **Reproducible to the byte.** Random draws are hashes of `(seed, stream, key)`, money is `DECIMAL`, and floating-point sums run in a fixed order. Reruns give identical files at any thread count; `manifest.json` records SHA-256 hashes.
5. **Checked independently.** The SQL estimators are tested against a separate numpy implementation (`shared/tests/test_estimators.py`).
