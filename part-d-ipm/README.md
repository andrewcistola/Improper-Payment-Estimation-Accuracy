# Part D IPM

Claim (PDE) errors that flow through the post-IRA benefit to Medicare reinsurance and low-income cost-sharing payments. Estimand: the national **gross improper payment rate**, Σ|y| / Σx over beneficiaries.

## errors/ — build the population, then apply fake errors

Run: `ipsim part-d-ipm/errors/config.yaml` → `errors/output/base/` (about 45 s)

| Step | File | What it does |
|---|---|---|
| Population | `01_population.sql` | 108,000 beneficiaries (1 = 500 real), ~4.3M PDEs; GDC = ingredient cost + dispensing fee + sales tax + vaccine admin fee |
| Errors | `02_candidate_errors.sql` | One candidate error per PDE: missing documentation 75.00% (GDC → 0), pricing 17.86%, drug discrepancy 7.14% |
| Errors | `03_init_calibration.sql` | Starts with no active errors |
| Errors | `04_apply_errors.sql` | Activates each candidate with probability m |
| Errors | `05_benefit.sql` | CY 2025 standard benefit ($590 deductible, $2,000 out-of-pocket cap, Manufacturer Discount Program, 20%/40% reinsurance, LIS copays), run on submitted and corrected PDEs |
| Errors | `06_calibrate.sql` | Sets m to hit gross $4.22B: one linear pass, one proportional refinement (steps 04–06 run three times; see `config.yaml`) |
| Truth | `07_population_truth.sql` | x = direct subsidy + reinsurance + LICS; y = Medicare(submitted) − Medicare(corrected) |
| Checks | `08_checks.sql` | FY 2025 targets: gross 4.00%, over $3.70B, under $0.52B, type shares; unique ids |

Outputs: `population.parquet` (one row per beneficiary), `pde_detail.parquet` (every PDE's submitted vs corrected liability by payer), `truth.json`, `checks.json`. The Parquet files are not committed (98 MB); rebuild them and compare hashes with `manifest.json`.

## estimation/ — sample the population and estimate with each method

Run: `ipsim part-d-ipm/estimation/config.yaml` → `estimation/results/base/`

Design: simple random sample of 1,500 beneficiaries (random selection since FY 2025; size not public), 200 Monte Carlo samples. Methods: `10_expansion.sql`, `20_ratio.sql`, `30_regression.sql`, `40_simulation.sql` (bootstrap), scored in `90_score.sql`. Formulas: [`shared/sql/lib/02_estimators.sql`](../shared/sql/lib/02_estimators.sql).
