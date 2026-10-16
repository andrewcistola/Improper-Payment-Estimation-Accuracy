# PERM / CERT

Individual claim or benefit-level errors. Two populations share this folder; files are prefixed `perm_` or `cert_`.

- **PERM** (Medicaid): payment universes for 9 states, with claims-review errors and eligibility errors. Each state's true eligibility rate is set on a grid from 2.00% to 4.00%. Estimands: each state's overall, eligibility and claims improper payment rates at federal share, Σ y·FMAP / Σ x·FMAP.
- **CERT** (claims stress family): the three payment shapes of Edwards, Liu & Delage (2023) (right-skewed, two-spike, left-skewed), each with all-or-nothing errors at 5%, 30%, 70% and 95% of claims. Estimand: the claim improper payment rate, Σy / Σx.

## errors/ — build the populations, then apply fake errors

| Run | Steps | Output |
|---|---|---|
| `ipsim perm-cert/errors/perm.yaml` | `perm_01_population.sql` (payments and strata) → `perm_02_claims_errors.sql` → `perm_03_eligibility_errors.sql` → `perm_04_truth.sql` → `perm_05_checks.sql` | `errors/output/perm/state_elig_grid/` |
| `ipsim perm-cert/errors/cert.yaml` | `cert_01_population.sql` (claims) → `cert_02_apply_errors.sql` | `errors/output/cert/<shape>_all_or_nothing_p<rate>/` |
| `ipsim perm-cert/errors/cert_benchmark.yaml` | `cert_benchmark.sql`: reruns the published Edwards et al. design to check that the CERT shapes behave as published | `errors/output/cert_benchmark/` |

PERM details:
- **Payments:** FFS claims and monthly managed-care capitations.
- **Strata:** 5 equal-dollar payment-size strata within each state × quarter × payment type.
- **Claims errors:** FFS 6.5% of payments (70% all-or-nothing, 30% partial); MC 0.3%.
- **Eligibility errors:** placed beneficiary by beneficiary in random order, so each state's true rate never exceeds its grid value.
- **Checks:** the pooled overall rate matches Medicaid's 6.12%; each state's true eligibility rate matches its grid value; every payment id is unique.

## estimation/ — sample the populations and estimate with each method

| Run | Design | Output |
|---|---|---|
| `ipsim perm-cert/estimation/perm.yaml` | One scenario per state: systematic selection after sorting by amount paid, within strata; 400 FFS + 120 MC payments a year; all components share one sample; 200 audit years | `estimation/results/perm/state_<id>/` (domain = `state\|component`) |
| `ipsim perm-cert/estimation/cert.yaml` | SRS of 30 claims; 1,000 audit years per population | `estimation/results/cert/<shape>_p<rate>/` |

Methods: `*_10_expansion.sql`, `*_20_ratio.sql`, `*_30_regression.sql`, and the audit-finding microsimulation (`*_40_simulation_inputs.sql` + `perm_simulation.py` / `cert_simulation.py`), all scored in `*_90_score.sql`.

- **PERM simulation:** each non-audited payment takes the claims finding (improper share of the payment) of a random audited payment of the same payment type and size class; each beneficiary with no audited payment takes the eligibility finding of a random audited beneficiary. Scored on the first 25 audit years per state.
- **CERT simulation:** each non-audited claim takes the improper share of a random audited claim. Scored on the first 100 audit years per population. Formulas: [`shared/sql/lib/02_estimators.sql`](../shared/sql/lib/02_estimators.sql). The systematic sample's variance is estimated as if it were stratified SRS, the usual approximation; the study measures how well that works.

## CERT results (SRS of 30 claims)

> **Microsimulation runs in progress.** The microsimulation column will be filled in when the runs finish. The expansion, ratio and regression results are final (1,000 audit years per population; standard error of coverage about ±0.7 points).

Coverage of two-sided 95% intervals: the % of audit years in which the interval contains the true rate; the parentheses show the % of audit years in which it lies entirely above / below.

| Population | Expansion | Ratio | Regression | Microsimulation |
|---|---|---|---|---|
| right-skewed, 5% errors | 55.9 (0.0/44.1) | 57.8 (0.0/42.2) | 54.0 (1.9/44.1) | _pending_ |
| right-skewed, 30% errors | 78.7 (0.0/21.3) | 82.8 (3.2/14.0) | 72.6 (8.2/19.2) | _pending_ |
| right-skewed, 70% errors | 84.0 (0.1/15.9) | 82.2 (14.3/3.5) | 72.7 (18.5/8.8) | _pending_ |
| right-skewed, 95% errors | 83.8 (0.4/15.8) | 58.0 (41.8/0.2) | 55.2 (43.2/1.6) | _pending_ |
| two-spike, 5% errors | 74.8 (0.0/25.2) | 73.6 (0.0/26.4) | 66.6 (0.0/33.4) | _pending_ |
| two-spike, 30% errors | 92.0 (1.3/6.7) | 92.7 (1.4/5.9) | 91.9 (1.8/6.3) | _pending_ |
| two-spike, 70% errors | 94.4 (3.2/2.4) | 94.5 (4.1/1.4) | 94.4 (4.1/1.5) | _pending_ |
| two-spike, 95% errors | 92.5 (4.5/3.0) | 74.3 (25.5/0.2) | 73.7 (25.5/0.8) | _pending_ |
| left-skewed, 5% errors | 75.9 (0.2/23.9) | 75.9 (0.2/23.9) | 75.7 (0.4/23.9) | _pending_ |
| left-skewed, 30% errors | 92.1 (1.9/6.0) | 91.7 (2.1/6.2) | 91.7 (2.2/6.1) | _pending_ |
| left-skewed, 70% errors | 94.1 (4.4/1.5) | 93.4 (5.4/1.2) | 92.5 (6.0/1.5) | _pending_ |
| left-skewed, 95% errors | 89.7 (9.8/0.5) | 78.8 (21.1/0.1) | 78.0 (21.9/0.1) | _pending_ |

All 12 populations are in `estimation/results/cert/`.
