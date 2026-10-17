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

Four measures, each estimated by every method as dollars with a 95% interval and then divided by the known total payments: **overpayments**, **underpayments**, **gross** (over + under) and **net** (over − under). An enrollee is an overpayment or an underpayment by the sign of its net risk score change. Dollars are shown at national scale (× 100: one synthetic enrollee stands for 100).

| File | Method |
|---|---|
| `01_frame.sql` | Estimands (the four measures; x = payment) and design: an audit of 990 enrollees, 330 in each national tercile of the original risk score (stratified SRS) |
| `shared/sql/sample_srs.sql` | 25 audit years |
| `10_expansion.sql` | **Expansion** in risk score units: in each tercile, the audited enrollees' average overpayment and underpayment risk score errors × the tercile's size × the national average county rate (monthly rate × months, over all enrollees). Stratified-SRS variance |
| `20_ratio.sql` | **Ratio**: weighted dollars in error ÷ weighted payments of the audited enrollees, linearization SE |
| `30_regression.sql` | **Regression** (GREG) on payment: predicted values summed over every enrollee (equivalent to GREG with an intercept); gross and net from the over and under totals |
| `40_simulation_inputs.sql` + `simulation.py` | **Bootstrap simulation**, using rates from the audit year's audit. One combined failure rate for each of the 20 HCCs: an audited instance counts as failed if it was deleted, moved down the hierarchy, or on a record with missing documentation. A failed instance loses its HCC's average audited loss. An HCC with no audited instances gets no failures (no extrapolation). One addition rate for each of the 10 families. Every HCC instance and eligible enrollee in the full population is drawn at these rates; audited enrollees keep their own findings; payments are recomputed for all 330,253 enrollees; 1,000 iterations; mean and 2.5th–97.5th percentiles |
| `90_score.sql` | Coverage, tail balance, bias, RMSE and width against the truth |

Outputs: `estimates.parquet` (every audit year × method × interval), `metrics.json`, `truth.json`. Formulas: [`shared/sql/lib/02_estimators.sql`](../shared/sql/lib/02_estimators.sql).

## Results (25 audit years)

Each row averages the 25 audit years: the true value, the average estimate, and the average upper and lower bounds of the 95% interval. National dollars (× 100); rates are dollars ÷ total payments ($388.7B).

**Dollars**

| Measure | Method | True | Estimated | Upper bound | Lower bound |
|---|---|---|---|---|---|
| Overpayments | Expansion | $21.34B | $21.72B | $25.79B | $17.65B |
|  | Ratio | $21.34B | $21.65B | $25.72B | $17.58B |
|  | Regression | $21.34B | $21.70B | $25.68B | $17.72B |
|  | Bootstrap simulation | $21.34B | $21.63B | $21.82B | $21.43B |
| Underpayments | Expansion | $2.23B | $2.10B | $3.10B | $1.11B |
|  | Ratio | $2.23B | $2.13B | $3.16B | $1.09B |
|  | Regression | $2.23B | $2.12B | $3.15B | $1.08B |
|  | Bootstrap simulation | $2.23B | $1.92B | $1.97B | $1.87B |
| Gross | Expansion | $23.57B | $23.83B | $27.99B | $19.66B |
|  | Ratio | $23.57B | $23.77B | $27.94B | $19.61B |
|  | Regression | $23.57B | $23.82B | $27.91B | $19.73B |
|  | Bootstrap simulation | $23.57B | $23.55B | $23.75B | $23.34B |
| Net | Expansion | $19.10B | $19.62B | $23.83B | $15.40B |
|  | Ratio | $19.10B | $19.52B | $23.76B | $15.28B |
|  | Regression | $19.10B | $19.59B | $23.73B | $15.45B |
|  | Bootstrap simulation | $19.10B | $19.70B | $19.91B | $19.50B |

**Rates**

| Measure | Method | True | Estimated | Upper bound | Lower bound |
|---|---|---|---|---|---|
| Overpayments | Expansion | 5.49% | 5.59% | 6.63% | 4.54% |
|  | Ratio | 5.49% | 5.57% | 6.62% | 4.52% |
|  | Regression | 5.49% | 5.58% | 6.61% | 4.56% |
|  | Bootstrap simulation | 5.49% | 5.56% | 5.61% | 5.51% |
| Underpayments | Expansion | 0.57% | 0.54% | 0.80% | 0.28% |
|  | Ratio | 0.57% | 0.55% | 0.81% | 0.28% |
|  | Regression | 0.57% | 0.54% | 0.81% | 0.28% |
|  | Bootstrap simulation | 0.57% | 0.49% | 0.51% | 0.48% |
| Gross | Expansion | 6.06% | 6.13% | 7.20% | 5.06% |
|  | Ratio | 6.06% | 6.12% | 7.19% | 5.04% |
|  | Regression | 6.06% | 6.13% | 7.18% | 5.08% |
|  | Bootstrap simulation | 6.06% | 6.06% | 6.11% | 6.01% |
| Net | Expansion | 4.91% | 5.05% | 6.13% | 3.96% |
|  | Ratio | 4.91% | 5.02% | 6.11% | 3.93% |
|  | Regression | 4.91% | 5.04% | 6.10% | 3.97% |
|  | Bootstrap simulation | 4.91% | 5.07% | 5.12% | 5.02% |

**How often the 95% interval contains the truth** (out of 25 audit years; in parentheses, intervals entirely above / entirely below the truth). A valid interval contains it in about 24 of 25.

| Measure | Expansion | Ratio | Regression | Bootstrap simulation |
|---|---|---|---|---|
| Overpayments | 25/25 (0/0) | 25/25 (0/0) | 24/25 (1/0) | 3/25 (13/9) |
| Underpayments | 21/25 (0/4) | 21/25 (0/4) | 21/25 (0/4) | 2/25 (4/19) |
| Gross | 25/25 (0/0) | 24/25 (1/0) | 24/25 (1/0) | 3/25 (12/10) |
| Net | 25/25 (0/0) | 25/25 (0/0) | 25/25 (0/0) | 2/25 (15/8) |

From [`shared/results/report/by_scenario.csv`](../shared/results/report/by_scenario.csv).
