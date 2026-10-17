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

Each row gives the true value and, over the 25 audit years, the median point estimate and the median upper and lower bounds of the 95% interval. National dollars (× 100); rates are dollars ÷ total payments ($388.7B).

**Dollars**

| Measure | Method | True | Estimated | Upper bound | Lower bound |
|---|---|---|---|---|---|
| Overpayments | Expansion | $21.34B | $22.00B | $25.97B | $17.76B |
|  | Ratio | $21.34B | $21.92B | $25.75B | $17.74B |
|  | Regression | $21.34B | $22.07B | $26.02B | $18.09B |
|  | Bootstrap simulation | $21.34B | $21.99B | $22.18B | $21.80B |
| Underpayments | Expansion | $2.23B | $2.07B | $3.09B | $1.05B |
|  | Ratio | $2.23B | $2.05B | $3.11B | $1.00B |
|  | Regression | $2.23B | $2.08B | $3.08B | $0.98B |
|  | Bootstrap simulation | $2.23B | $1.88B | $1.93B | $1.82B |
| Gross | Expansion | $23.57B | $23.92B | $27.96B | $19.69B |
|  | Ratio | $23.57B | $23.82B | $27.81B | $19.83B |
|  | Regression | $23.57B | $23.94B | $27.78B | $20.05B |
|  | Bootstrap simulation | $23.57B | $23.56B | $23.76B | $23.35B |
| Net | Expansion | $19.10B | $19.79B | $24.12B | $15.50B |
|  | Ratio | $19.10B | $19.85B | $23.89B | $15.37B |
|  | Regression | $19.10B | $19.63B | $23.57B | $15.36B |
|  | Bootstrap simulation | $19.10B | $19.87B | $20.10B | $19.65B |

**Rates**

| Measure | Method | True | Estimated | Upper bound | Lower bound |
|---|---|---|---|---|---|
| Overpayments | Expansion | 5.49% | 5.66% | 6.68% | 4.57% |
|  | Ratio | 5.49% | 5.64% | 6.62% | 4.56% |
|  | Regression | 5.49% | 5.68% | 6.69% | 4.65% |
|  | Bootstrap simulation | 5.49% | 5.66% | 5.70% | 5.61% |
| Underpayments | Expansion | 0.57% | 0.53% | 0.79% | 0.27% |
|  | Ratio | 0.57% | 0.53% | 0.80% | 0.26% |
|  | Regression | 0.57% | 0.53% | 0.79% | 0.25% |
|  | Bootstrap simulation | 0.57% | 0.48% | 0.50% | 0.47% |
| Gross | Expansion | 6.06% | 6.15% | 7.19% | 5.06% |
|  | Ratio | 6.06% | 6.13% | 7.16% | 5.10% |
|  | Regression | 6.06% | 6.16% | 7.15% | 5.16% |
|  | Bootstrap simulation | 6.06% | 6.06% | 6.11% | 6.01% |
| Net | Expansion | 4.91% | 5.09% | 6.20% | 3.99% |
|  | Ratio | 4.91% | 5.11% | 6.15% | 3.95% |
|  | Regression | 4.91% | 5.05% | 6.06% | 3.95% |
|  | Bootstrap simulation | 4.91% | 5.11% | 5.17% | 5.06% |

**How often the 95% interval contains the truth** (out of 25 audit years; in parentheses, intervals entirely above / entirely below the truth). A valid interval contains it in about 24 of 25.

| Measure | Expansion | Ratio | Regression | Bootstrap simulation |
|---|---|---|---|---|
| Overpayments | 25/25 (0/0) | 25/25 (0/0) | 24/25 (1/0) | 3/25 (13/9) |
| Underpayments | 21/25 (0/4) | 21/25 (0/4) | 21/25 (0/4) | 2/25 (4/19) |
| Gross | 25/25 (0/0) | 24/25 (1/0) | 24/25 (1/0) | 3/25 (12/10) |
| Net | 25/25 (0/0) | 25/25 (0/0) | 25/25 (0/0) | 2/25 (15/8) |

From [`shared/results/report/by_scenario.csv`](../shared/results/report/by_scenario.csv).
