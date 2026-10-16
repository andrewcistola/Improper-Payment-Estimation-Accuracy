# Part C IPM

Risk-score errors on capitated Medicare Advantage payments. Estimand: the national **gross improper payment rate**, Σ|y| / Σx over enrollees.

## errors/ — build the population, then apply fake errors

Run: `ipsim part-c-ipm/errors/config.yaml` → `errors/output/base/`

| Step | File | What it does |
|---|---|---|
| Population | `01_contracts.sql` | 550 contracts with lognormal enrollment and a coding-intensity factor |
| Population | `02_enrollees_hccs.sql` | 330,000 enrollees (1 = 100 real); HCCs from 10 illustrative families, each with a mild and a severe level |
| Population | `03_payments.sql` | Risk score R0 and payment x = R0 × county rate × months, scaled to $388.72B |
| Errors | `04_apply_errors.sql` | Unsupported HCCs (deleted, or severe→mild hierarchy move), missing documentation, additional HCCs (underpayments); one closed-form multiplier per error type |
| Truth | `05_population_truth.sql` | Strata (risk-score terciles), true totals and rates |
| Checks | `06_checks.sql` | FY 2025 targets: gross 6.09%, over $21.43B, under $2.23B, missing documentation 0.22%; unique ids |

Outputs: `population.parquet` (one row per enrollee), `hcc_detail.parquet` (one row per enrollee × HCC: why each HCC was or wasn't in error), `contracts.parquet`, `truth.json`, `checks.json`, `design.yaml`, `config.yaml`, `manifest.json`.

## estimation/ — sample the population and estimate with each method

Run: `ipsim part-c-ipm/estimation/config.yaml` → `estimation/results/base/`

| File | Method |
|---|---|
| `01_frame.sql` | Estimand (y = \|payment error\|, x = payment) and design: stratified SRS, 1,500 per risk tercile (sizes not public; illustrative) |
| `shared/sql/sample_srs.sql` | 200 audit years |
| `10_expansion.sql` | Expansion: T̂_y / X |
| `20_ratio.sql` | Ratio: T̂_y / T̂_x, linearization SE |
| `30_regression.sql` | Regression (GREG) on payment x |
| `40_simulation_inputs.sql` + `simulation.py` | Audit-finding bootstrap simulation: the audited enrollees' findings are assigned to every other enrollee (HCC level: supported / deleted / hierarchy move, from audited HCCs of the same risk stratum, family and severity; enrollee level: missing documentation and additional HCCs), the risk-score payment is recomputed, 1,000 iterations; mean and 2.5th–97.5th percentiles. The audit is used exactly as audited (never resampled). Run on the first 50 audit years; results are reported for audit years 1–25. |
| `90_score.sql` | Coverage, tail balance, bias, RMSE and width against the truth |

Outputs: `estimates.parquet` (every audit year × method × interval), `metrics.json`, `truth.json`. Formulas: [`shared/sql/lib/02_estimators.sql`](../shared/sql/lib/02_estimators.sql).
