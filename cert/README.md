# CERT (Medicare fee-for-service)

A national claims universe of the four CERT claim types (Part A hospital IPPS, Part A excluding IPPS, Part B, DMEPOS), calibrated to the FY 2025 CERT results by claim type; no MAC jurisdictions. Four measures, netted per claim: **overpayments**, **underpayments**, **gross** and **net**, each ÷ total payments, plus gross by claim type. Dollars are national (× 200). The PERM population, which once shared this folder, is in [`perm/`](../perm/).

## errors/ — build the population, then apply fake errors

| Run | Steps | Output |
|---|---|---|
| `ipsim cert/errors/config.yaml` | `01_population.sql` (claims and strata) → `02_apply_errors.sql` → `03_truth.sql` → `04_checks.sql` | `errors/output/national/` (Parquet not committed: 5.34M claims) |

- **Claims:** 5.34 million synthetic claims (1 = 200 real): IPPS 40,000, Part A excluding IPPS 900,000, Part B 4,000,000, DMEPOS 400,000. Amounts are lognormal within claim type (illustrative spread), scaled so each type's total × 200 equals its FY 2025 payments ($118.5B, $197.9B, $114.1B, $9.4B; $439.9B in all).
- **Strata:** claim type × five equal-count payment quintiles (20). CERT's real strata are claim type × MAC jurisdiction, and its universe includes denied claims; neither can be rebuilt from public data, so the quintiles stand in for the jurisdictions and denied claims are not modeled.
- **Errors:** at most one per claim. Whole-claim overpayments (no or insufficient documentation, medical necessity, other: 92% of overpayment dollars), partial coding overpayments (8%, a uniform 5–60% of the payment) and coding underpayments (a uniform 5–50% of the payment). Rates are closed form per claim type, from the FY 2025 overpayment and underpayment dollars (Supplemental Improper Payment Data, Tables A1 and A4). By default errors do not depend on claim size; `--set size_beta=0.5` (default 0) multiplies each claim's probabilities by (paid ÷ mean paid within claim type)^0.5, capped so a claim's total error probability stays at or below 0.95, with the closed-form rates recalibrated from the per-claim probabilities so every FY 2025 target still holds (`02_apply_errors.sql`). The committed population is size_beta = 0.
- **Checks:** overall gross 6.50% (FY 2025: 6.55%), gross by claim type within 0.3 points, underpayments $0.92B (FY 2025: $1.0B), payments $439.9B, unique ids.


## estimation/ — sample the population and estimate with each method

| Run | Design | Output |
|---|---|---|
| `ipsim cert/estimation/config.yaml` | Stratified SRS of 37,651 claims: the FY 2025 claims reviewed per claim type (IPPS 8,750; Part A excluding IPPS 8,651; Part B 11,600; DMEPOS 8,650), Neyman allocation across the type's payment quintiles (`allocation.json`); 25 audit years. `02_sample.sql` draws the same SRS as `shared/sql/sample_srs.sql`, faster for 5.3M claims | `estimation/results/national/` (domain = `national\|over/under/gross/net`, `<claim type>\|gross`) |

Methods: `10_expansion.sql`, `20_ratio.sql`, `30_regression.sql`, and the audit-finding simulation (`40_simulation_inputs.sql` + `simulation.py`), all scored in `90_score.sql`. Formulas: [`shared/sql/lib/02_estimators.sql`](../shared/sql/lib/02_estimators.sql).

- **Regression** (`30_regression.sql` + [`shared/ipsim/regression.py`](../shared/ipsim/regression.py)): within each design stratum, improper dollars are regressed on the amount paid (CERT claims carry no beneficiary variables); the models predict every claim, the audit residuals are added, and the interval comes from the residuals. A stratum with fewer than 10 audited errors uses an intercept-only model (expansion within that stratum); nearly every CERT stratum has enough errors for the model (the smallest-payment Part A excluding IPPS stratum, about 79 claims, usually does not).

- **Bootstrap simulation:** the same two steps within each claim type × quintile stratum: a non-audited claim is in error with the audited error rate; an error is partial with the audited partial share (its improper share, over or under, drawn from the stratum's audited partial errors), otherwise the whole claim is improper. Parametric rates (reported; counts redrawn as for PERM) or fixed rates (comparison only, `estimation/results_fixed/`). 25 audit years, 1,000 iterations. `--set sim_kind_deciles=K` (default 0) post-stratifies the simulation's donor kinds only, into each claim type × quintile stratum × K equal-count amount-paid quantiles within it (computed on the population), leaving the audit design and the analytic estimators unchanged; a kind with no audited claim borrows its stratum's pooled rates and partial sizes (robustness Appendix D, Tables D4–D6).

## Results (25 audit years)

Each row gives the true value and, over the 25 audit years, the median point estimate and the median upper and lower bounds of the 95% interval. National dollars (× 200); rates are dollars ÷ total payments ($439.9B).

**Dollars**

| Measure | Method | True | Estimated | Upper bound | Lower bound |
|---|---|---|---|---|---|
| Overpayments | Expansion | $27.69B | $27.93B | $29.50B | $26.33B |
|  | Ratio | $27.69B | $27.98B | $29.53B | $26.40B |
|  | Regression | $27.69B | $27.98B | $29.53B | $26.40B |
|  | Simulation (parametric rates) | $27.69B | $27.97B | $29.16B | $26.74B |
| Underpayments | Expansion | $0.92B | $0.89B | $1.01B | $0.75B |
|  | Ratio | $0.92B | $0.88B | $1.01B | $0.75B |
|  | Regression | $0.92B | $0.89B | $1.01B | $0.76B |
|  | Simulation (parametric rates) | $0.92B | $0.91B | $0.99B | $0.83B |
| Gross | Expansion | $28.61B | $28.85B | $30.47B | $27.22B |
|  | Ratio | $28.61B | $28.94B | $30.50B | $27.38B |
|  | Regression | $28.61B | $28.95B | $30.50B | $27.35B |
|  | Simulation (parametric rates) | $28.61B | $28.83B | $30.02B | $27.59B |
| Net | Expansion | $26.77B | $26.97B | $28.59B | $25.32B |
|  | Ratio | $26.77B | $27.07B | $28.58B | $25.38B |
|  | Regression | $26.77B | $27.05B | $28.57B | $25.38B |
|  | Simulation (parametric rates) | $26.77B | $27.07B | $28.29B | $25.86B |
| Gross: Part A IPPS | Expansion | $3.58B | $3.63B | $3.98B | $3.29B |
|  | Ratio | $3.58B | $3.63B | $3.98B | $3.29B |
|  | Regression | $3.58B | $3.63B | $3.97B | $3.28B |
|  | Simulation (parametric rates) | $3.58B | $3.63B | $3.97B | $3.30B |
| Gross: Part A excl. IPPS | Expansion | $13.10B | $13.26B | $14.69B | $11.75B |
|  | Ratio | $13.10B | $13.21B | $14.56B | $11.85B |
|  | Regression | $13.10B | $13.18B | $14.55B | $11.82B |
|  | Simulation (parametric rates) | $13.10B | $13.19B | $14.19B | $12.16B |
| Gross: Part B | Expansion | $9.64B | $9.46B | $10.15B | $8.80B |
|  | Ratio | $9.64B | $9.50B | $10.19B | $8.81B |
|  | Regression | $9.64B | $9.50B | $10.18B | $8.82B |
|  | Simulation (parametric rates) | $9.64B | $9.54B | $10.11B | $8.99B |
| Gross: DMEPOS | Expansion | $2.30B | $2.27B | $2.37B | $2.16B |
|  | Ratio | $2.30B | $2.28B | $2.38B | $2.17B |
|  | Regression | $2.30B | $2.28B | $2.38B | $2.17B |
|  | Simulation (parametric rates) | $2.30B | $2.29B | $2.38B | $2.20B |

**Rates**

| Measure | Method | True | Estimated | Upper bound | Lower bound |
|---|---|---|---|---|---|
| Overpayments | Expansion | 6.30% | 6.35% | 6.71% | 5.99% |
|  | Ratio | 6.30% | 6.36% | 6.71% | 6.00% |
|  | Regression | 6.30% | 6.36% | 6.71% | 6.00% |
|  | Simulation (parametric rates) | 6.30% | 6.36% | 6.63% | 6.08% |
| Underpayments | Expansion | 0.21% | 0.20% | 0.23% | 0.17% |
|  | Ratio | 0.21% | 0.20% | 0.23% | 0.17% |
|  | Regression | 0.21% | 0.20% | 0.23% | 0.17% |
|  | Simulation (parametric rates) | 0.21% | 0.21% | 0.22% | 0.19% |
| Gross | Expansion | 6.50% | 6.56% | 6.93% | 6.19% |
|  | Ratio | 6.50% | 6.58% | 6.93% | 6.22% |
|  | Regression | 6.50% | 6.58% | 6.93% | 6.22% |
|  | Simulation (parametric rates) | 6.50% | 6.55% | 6.82% | 6.27% |
| Net | Expansion | 6.09% | 6.13% | 6.50% | 5.76% |
|  | Ratio | 6.09% | 6.15% | 6.50% | 5.77% |
|  | Regression | 6.09% | 6.15% | 6.50% | 5.77% |
|  | Simulation (parametric rates) | 6.09% | 6.15% | 6.43% | 5.88% |
| Gross: Part A IPPS | Expansion | 3.02% | 3.07% | 3.36% | 2.77% |
|  | Ratio | 3.02% | 3.07% | 3.36% | 2.78% |
|  | Regression | 3.02% | 3.06% | 3.35% | 2.77% |
|  | Simulation (parametric rates) | 3.02% | 3.06% | 3.35% | 2.79% |
| Gross: Part A excl. IPPS | Expansion | 6.62% | 6.70% | 7.42% | 5.94% |
|  | Ratio | 6.62% | 6.67% | 7.36% | 5.99% |
|  | Regression | 6.62% | 6.66% | 7.35% | 5.97% |
|  | Simulation (parametric rates) | 6.62% | 6.67% | 7.17% | 6.14% |
| Gross: Part B | Expansion | 8.45% | 8.29% | 8.90% | 7.72% |
|  | Ratio | 8.45% | 8.33% | 8.93% | 7.72% |
|  | Regression | 8.45% | 8.33% | 8.93% | 7.73% |
|  | Simulation (parametric rates) | 8.45% | 8.36% | 8.86% | 7.88% |
| Gross: DMEPOS | Expansion | 24.44% | 24.12% | 25.26% | 22.96% |
|  | Ratio | 24.44% | 24.26% | 25.36% | 23.12% |
|  | Regression | 24.44% | 24.20% | 25.30% | 23.10% |
|  | Simulation (parametric rates) | 24.44% | 24.36% | 25.29% | 23.45% |

**How often the 95% interval contains the truth** (out of 25 audit years; in parentheses, intervals entirely above / entirely below the truth). A valid interval contains it in about 24 of 25.

| Measure | Expansion | Ratio | Regression | Simulation (parametric rates) |
|---|---|---|---|---|
| Overpayments | 24/25 (1/0) | 24/25 (1/0) | 24/25 (1/0) | 25/25 (0/0) |
| Underpayments | 23/25 (0/2) | 23/25 (0/2) | 23/25 (0/2) | 21/25 (0/4) |
| Gross | 25/25 (0/0) | 24/25 (1/0) | 24/25 (1/0) | 25/25 (0/0) |
| Net | 24/25 (1/0) | 24/25 (1/0) | 24/25 (1/0) | 25/25 (0/0) |
| Gross: Part A IPPS | 24/25 (1/0) | 24/25 (1/0) | 24/25 (1/0) | 23/25 (2/0) |
| Gross: Part A excl. IPPS | 24/25 (1/0) | 23/25 (2/0) | 24/25 (1/0) | 25/25 (0/0) |
| Gross: Part B | 25/25 (0/0) | 23/25 (0/2) | 23/25 (0/2) | 25/25 (0/0) |
| Gross: DMEPOS | 24/25 (0/1) | 24/25 (0/1) | 24/25 (0/1) | 25/25 (0/0) |

From [`shared/results/report/by_scenario.csv`](../shared/results/report/by_scenario.csv) (`python shared/build_readmes.py` regenerates this section).
