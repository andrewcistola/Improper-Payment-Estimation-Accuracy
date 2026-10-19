# PERM / CERT

Individual claim or benefit-level errors. Two populations share this folder; files are prefixed `perm_` or `cert_`.

- **PERM** (Medicaid): payment universes for 9 states, with claims-review errors and eligibility errors. Each state's true eligibility rate is set on a grid from 2.00% to 4.00%. Estimands: each state's gross, eligibility and claims improper payment rates at federal share, Σ y·FMAP / Σ x·FMAP, and the 9 states pooled. Every PERM error is an overpayment, so gross = overpayments = net and underpayments are zero.
- **CERT** (Medicare FFS): a national claims universe of the four CERT claim types (Part A hospital IPPS, Part A excluding IPPS, Part B, DMEPOS), calibrated to the FY 2025 CERT results by claim type; no MAC jurisdictions. Four measures, netted per claim: **overpayments**, **underpayments**, **gross** and **net**, each ÷ total payments, plus gross by claim type. Dollars are national (× 200).

## errors/ — build the populations, then apply fake errors

| Run | Steps | Output |
|---|---|---|
| `ipsim perm-cert/errors/perm.yaml` | `perm_01_population.sql` (payments and strata) → `perm_02_claims_errors.sql` → `perm_03_eligibility_errors.sql` → `perm_04_truth.sql` → `perm_05_checks.sql` | `errors/output/perm/state_elig_grid/` |
| `ipsim perm-cert/errors/cert.yaml` | `cert_01_population.sql` (claims and strata) → `cert_02_apply_errors.sql` → `cert_03_truth.sql` → `cert_04_checks.sql` | `errors/output/cert/national/` (Parquet not committed: 5.34M claims) |

PERM details:
- **Payments:** FFS claims and monthly managed-care capitations.
- **Strata:** 5 equal-dollar payment-size strata within each state × quarter × payment type.
- **Claims errors:** FFS 6.5% of payments (70% all-or-nothing, 30% partial); MC 0.3%.
- **Eligibility errors:** placed beneficiary by beneficiary in random order, so each state's true rate never exceeds its grid value.
- **Checks:** the pooled overall rate matches Medicaid's 6.12%; each state's true eligibility rate matches its grid value; every payment id is unique.

CERT details:
- **Claims:** 5.34 million synthetic claims (1 = 200 real): IPPS 40,000, Part A excluding IPPS 900,000, Part B 4,000,000, DMEPOS 400,000. Amounts are lognormal within claim type (illustrative spread), scaled so each type's total × 200 equals its FY 2025 payments ($118.5B, $197.9B, $114.1B, $9.4B; $439.9B in all).
- **Strata:** claim type × five equal-count payment quintiles (20). CERT's own service-level strata (about 100 per claim type) cannot be rebuilt from public data; the quintiles stand in for them.
- **Errors:** at most one per claim. Whole-claim overpayments (no or insufficient documentation, medical necessity, other: 92% of overpayment dollars), partial coding overpayments (8%, a uniform 5–60% of the payment) and coding underpayments (a uniform 5–50% of the payment). Rates are closed form per claim type, from the FY 2025 overpayment and underpayment dollars (Supplemental Improper Payment Data, Tables A1 and A4). Errors do not depend on claim size.
- **Checks:** overall gross 6.50% (FY 2025: 6.55%), gross by claim type within 0.3 points, underpayments $0.92B (FY 2025: $1.0B), payments $439.9B, unique ids.

## estimation/ — sample the populations and estimate with each method

| Run | Design | Output |
|---|---|---|
| `ipsim perm-cert/estimation/perm.yaml` then `perm_national.yaml` | One scenario per state: strata = payment type (FFS, MC) × five equal-count payment quintiles; Neyman allocation of 520 payments per state-year (n_h ∝ N_h × S_h, S_h = standard deviation of gross improper dollars); systematic selection after sorting by amount paid within stratum; all components share one sample; 25 audit years. `perm_national.yaml` pools the states: dollars and variances add for the analytic methods; the bootstrap simulation sums the states' iterations | `estimation/results/perm/state_<id>/` (domain = `state\|component`), `estimation/results/perm/national/` |
| `ipsim perm-cert/estimation/cert.yaml` | Stratified SRS of 37,651 claims: the FY 2025 claims reviewed per claim type (IPPS 8,750; Part A excluding IPPS 8,651; Part B 11,600; DMEPOS 8,650), Neyman allocation across the type's payment quintiles (`allocation.json`); 25 audit years. `cert_02_sample.sql` draws the same SRS as `shared/sql/sample_srs.sql`, faster for 5.3M claims | `estimation/results/cert/national/` (domain = `national\|over/under/gross/net`, `<claim type>\|gross`) |

Methods: `*_10_expansion.sql`, `*_20_ratio.sql`, `*_30_regression.sql`, and the audit-finding bootstrap simulation (`*_40_simulation_inputs.sql` + `perm_simulation.py` / `cert_simulation.py`), all scored in `*_90_score.sql`.

- **Regression** (`*_30_regression.sql` + [`shared/ipsim/regression.py`](../shared/ipsim/regression.py)): within each design stratum, improper dollars are regressed on the amount paid and, for PERM, month of service and the beneficiary's number of payments and total paid (CERT claims carry no beneficiary variables); the models predict every payment or claim, the audit residuals are added, and the interval comes from the residuals. A stratum with fewer than 10 audited errors uses an intercept-only model (expansion within that stratum). In PERM that is every stratum except the largest-payment FFS stratum, which holds about 60% of each state's audit (about 26 errors); in CERT nearly every stratum has enough errors for the model (the smallest-payment Part A excluding IPPS stratum, about 79 claims, usually does not).

- **PERM bootstrap simulation:** within each stratum, a non-audited payment is in error with the audited error rate; an error is partial with the audited partial share (its improper share drawn from the stratum's audited partial errors), otherwise the whole payment is improper. A beneficiary with no audited payment is ineligible with the audited beneficiaries' eligibility error rate. Parametric rates (reported; each rate redrawn as Binomial(n, rate)/n before every iteration) or fixed rates (`--set sim_rates=fixed`, comparison only, `estimation/results_fixed/`). 25 audit years per state, 1,000 iterations.
- **CERT bootstrap simulation:** the same two steps within each claim type × quintile stratum: a non-audited claim is in error with the audited error rate; an error is partial with the audited partial share (its improper share, over or under, drawn from the stratum's audited partial errors), otherwise the whole claim is improper. Parametric rates (reported) or fixed rates (comparison only, `estimation/results_fixed/`). 25 audit years, 1,000 iterations. Formulas: [`shared/sql/lib/02_estimators.sql`](../shared/sql/lib/02_estimators.sql). The systematic sample's variance is estimated as if it were stratified SRS, the usual approximation; the study measures how well that works.

## PERM results (25 audit years)

Each row gives the true value and, over the 25 audit years, the median point estimate and the median upper and lower bounds of the 95% interval. National dollars (× 200, federal share); rates are dollars ÷ total payments ($142.0B).

**Dollars**

| Measure | Method | True | Estimated | Upper bound | Lower bound |
|---|---|---|---|---|---|
| Gross (all PERM errors are overpayments) | Expansion | $8.65B | $8.57B | $9.74B | $7.42B |
|  | Ratio | $8.65B | $8.52B | $9.70B | $7.38B |
|  | Regression | $8.65B | $8.57B | $9.67B | $7.43B |
|  | Bootstrap simulation (parametric rates) | $8.65B | $8.46B | $9.39B | $7.59B |
| Eligibility | Expansion | $4.34B | $4.33B | $5.18B | $3.48B |
|  | Ratio | $4.34B | $4.33B | $5.18B | $3.48B |
|  | Regression | $4.34B | $4.36B | $5.21B | $3.52B |
|  | Bootstrap simulation (parametric rates) | $4.34B | $4.24B | $4.97B | $3.54B |
| Claims | Expansion | $4.44B | $4.50B | $5.26B | $3.63B |
|  | Ratio | $4.44B | $4.52B | $5.28B | $3.67B |
|  | Regression | $4.44B | $4.48B | $5.22B | $3.71B |
|  | Bootstrap simulation (parametric rates) | $4.44B | $4.41B | $5.03B | $3.82B |

**Rates**

| Measure | Method | True | Estimated | Upper bound | Lower bound |
|---|---|---|---|---|---|
| Gross (all PERM errors are overpayments) | Expansion | 6.09% | 6.04% | 6.86% | 5.23% |
|  | Ratio | 6.09% | 6.00% | 6.83% | 5.20% |
|  | Regression | 6.09% | 6.03% | 6.81% | 5.23% |
|  | Bootstrap simulation (parametric rates) | 6.09% | 5.96% | 6.61% | 5.34% |
| Eligibility | Expansion | 3.06% | 3.05% | 3.64% | 2.45% |
|  | Ratio | 3.06% | 3.05% | 3.65% | 2.45% |
|  | Regression | 3.06% | 3.07% | 3.67% | 2.48% |
|  | Bootstrap simulation (parametric rates) | 3.06% | 2.98% | 3.50% | 2.49% |
| Claims | Expansion | 3.13% | 3.17% | 3.70% | 2.55% |
|  | Ratio | 3.13% | 3.18% | 3.72% | 2.58% |
|  | Regression | 3.13% | 3.15% | 3.68% | 2.62% |
|  | Bootstrap simulation (parametric rates) | 3.13% | 3.10% | 3.54% | 2.69% |

**How often the 95% interval contains the truth** (out of 25 audit years; in parentheses, intervals entirely above / entirely below the truth). A valid interval contains it in about 24 of 25.

| Measure | Expansion | Ratio | Regression | Bootstrap simulation (parametric rates) |
|---|---|---|---|---|
| Gross (all PERM errors are overpayments) | 23/25 (0/2) | 23/25 (0/2) | 23/25 (0/2) | 24/25 (0/1) |
| Eligibility | 21/25 (0/4) | 21/25 (0/4) | 21/25 (0/4) | 24/25 (0/1) |
| Claims | 23/25 (0/2) | 23/25 (0/2) | 23/25 (0/2) | 23/25 (1/1) |

From [`shared/results/report/by_scenario.csv`](../shared/results/report/by_scenario.csv).

## CERT results (25 audit years)

Each row gives the true value and, over the 25 audit years, the median point estimate and the median upper and lower bounds of the 95% interval. National dollars (× 200); rates are dollars ÷ total payments ($9.4B).

**Dollars**

| Measure | Method | True | Estimated | Upper bound | Lower bound |
|---|---|---|---|---|---|
| Overpayments | Expansion | $27.69B | $27.93B | $29.50B | $26.33B |
|  | Ratio | $27.69B | $27.98B | $29.53B | $26.40B |
|  | Regression | $27.69B | $27.98B | $29.53B | $26.40B |
|  | Bootstrap simulation (parametric rates) | $27.69B | $27.94B | $29.13B | $26.63B |
| Underpayments | Expansion | $0.92B | $0.89B | $1.01B | $0.75B |
|  | Ratio | $0.92B | $0.88B | $1.01B | $0.75B |
|  | Regression | $0.92B | $0.89B | $1.01B | $0.76B |
|  | Bootstrap simulation (parametric rates) | $0.92B | $0.91B | $0.99B | $0.84B |
| Gross | Expansion | $28.61B | $28.85B | $30.47B | $27.22B |
|  | Ratio | $28.61B | $28.94B | $30.50B | $27.38B |
|  | Regression | $28.61B | $28.95B | $30.50B | $27.35B |
|  | Bootstrap simulation (parametric rates) | $28.61B | $28.81B | $30.02B | $27.47B |
| Net | Expansion | $26.77B | $26.97B | $28.59B | $25.32B |
|  | Ratio | $26.77B | $27.07B | $28.58B | $25.38B |
|  | Regression | $26.77B | $27.05B | $28.57B | $25.38B |
|  | Bootstrap simulation (parametric rates) | $26.77B | $27.07B | $28.26B | $25.78B |
| Gross: Part A hospital IPPS | Expansion | $3.58B | $3.63B | $3.98B | $3.29B |
|  | Ratio | $3.58B | $3.63B | $3.98B | $3.29B |
|  | Regression | $3.58B | $3.63B | $3.97B | $3.28B |
|  | Bootstrap simulation (parametric rates) | $3.58B | $3.64B | $3.99B | $3.30B |
| Gross: Part A excluding IPPS | Expansion | $13.10B | $13.26B | $14.69B | $11.75B |
|  | Ratio | $13.10B | $13.21B | $14.56B | $11.85B |
|  | Regression | $13.10B | $13.18B | $14.55B | $11.82B |
|  | Bootstrap simulation (parametric rates) | $13.10B | $13.17B | $14.22B | $12.17B |
| Gross: Part B | Expansion | $9.64B | $9.46B | $10.15B | $8.80B |
|  | Ratio | $9.64B | $9.50B | $10.19B | $8.81B |
|  | Regression | $9.64B | $9.50B | $10.18B | $8.82B |
|  | Bootstrap simulation (parametric rates) | $9.64B | $9.55B | $10.10B | $9.00B |
| Gross: DMEPOS | Expansion | $2.30B | $2.27B | $2.37B | $2.16B |
|  | Ratio | $2.30B | $2.28B | $2.38B | $2.17B |
|  | Regression | $2.30B | $2.28B | $2.38B | $2.17B |
|  | Bootstrap simulation (parametric rates) | $2.30B | $2.29B | $2.37B | $2.20B |

**Rates**

| Measure | Method | True | Estimated | Upper bound | Lower bound |
|---|---|---|---|---|---|
| Overpayments | Expansion | 6.30% | 6.35% | 6.71% | 5.99% |
|  | Ratio | 6.30% | 6.36% | 6.71% | 6.00% |
|  | Regression | 6.30% | 6.36% | 6.71% | 6.00% |
|  | Bootstrap simulation (parametric rates) | 6.30% | 6.35% | 6.62% | 6.05% |
| Underpayments | Expansion | 0.21% | 0.20% | 0.23% | 0.17% |
|  | Ratio | 0.21% | 0.20% | 0.23% | 0.17% |
|  | Regression | 0.21% | 0.20% | 0.23% | 0.17% |
|  | Bootstrap simulation (parametric rates) | 0.21% | 0.21% | 0.23% | 0.19% |
| Gross | Expansion | 6.50% | 6.56% | 6.93% | 6.19% |
|  | Ratio | 6.50% | 6.58% | 6.93% | 6.22% |
|  | Regression | 6.50% | 6.58% | 6.93% | 6.22% |
|  | Bootstrap simulation (parametric rates) | 6.50% | 6.55% | 6.82% | 6.25% |
| Net | Expansion | 6.09% | 6.13% | 6.50% | 5.76% |
|  | Ratio | 6.09% | 6.15% | 6.50% | 5.77% |
|  | Regression | 6.09% | 6.15% | 6.50% | 5.77% |
|  | Bootstrap simulation (parametric rates) | 6.09% | 6.15% | 6.42% | 5.86% |
| Gross: Part A hospital IPPS | Expansion | 3.02% | 3.07% | 3.36% | 2.77% |
|  | Ratio | 3.02% | 3.07% | 3.36% | 2.78% |
|  | Regression | 3.02% | 3.06% | 3.35% | 2.77% |
|  | Bootstrap simulation (parametric rates) | 3.02% | 3.07% | 3.37% | 2.78% |
| Gross: Part A excluding IPPS | Expansion | 6.62% | 6.70% | 7.42% | 5.94% |
|  | Ratio | 6.62% | 6.67% | 7.36% | 5.99% |
|  | Regression | 6.62% | 6.66% | 7.35% | 5.97% |
|  | Bootstrap simulation (parametric rates) | 6.62% | 6.66% | 7.19% | 6.15% |
| Gross: Part B | Expansion | 8.45% | 8.29% | 8.90% | 7.72% |
|  | Ratio | 8.45% | 8.33% | 8.93% | 7.72% |
|  | Regression | 8.45% | 8.33% | 8.93% | 7.73% |
|  | Bootstrap simulation (parametric rates) | 8.45% | 8.37% | 8.85% | 7.89% |
| Gross: DMEPOS | Expansion | 24.44% | 24.12% | 25.26% | 22.96% |
|  | Ratio | 24.44% | 24.26% | 25.36% | 23.12% |
|  | Regression | 24.44% | 24.20% | 25.30% | 23.10% |
|  | Bootstrap simulation (parametric rates) | 24.44% | 24.35% | 25.22% | 23.43% |

**How often the 95% interval contains the truth** (out of 25 audit years; in parentheses, intervals entirely above / entirely below the truth). A valid interval contains it in about 24 of 25.

| Measure | Expansion | Ratio | Regression | Bootstrap simulation (parametric rates) |
|---|---|---|---|---|
| Overpayments | 24/25 (1/0) | 24/25 (1/0) | 24/25 (1/0) | 25/25 (0/0) |
| Underpayments | 23/25 (0/2) | 23/25 (0/2) | 23/25 (0/2) | 20/25 (0/5) |
| Gross | 25/25 (0/0) | 24/25 (1/0) | 24/25 (1/0) | 25/25 (0/0) |
| Net | 24/25 (1/0) | 24/25 (1/0) | 24/25 (1/0) | 25/25 (0/0) |
| Gross: Part A hospital IPPS | 24/25 (1/0) | 24/25 (1/0) | 24/25 (1/0) | 24/25 (1/0) |
| Gross: Part A excluding IPPS | 24/25 (1/0) | 23/25 (2/0) | 24/25 (1/0) | 25/25 (0/0) |
| Gross: Part B | 25/25 (0/0) | 23/25 (0/2) | 23/25 (0/2) | 25/25 (0/0) |
| Gross: DMEPOS | 24/25 (0/1) | 24/25 (0/1) | 24/25 (0/1) | 25/25 (0/0) |

From [`shared/results/report/by_scenario.csv`](../shared/results/report/by_scenario.csv).
