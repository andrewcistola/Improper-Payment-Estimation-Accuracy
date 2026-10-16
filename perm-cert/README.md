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

Every method is scored on the same 25 audit years per population (audit years 1–25; standard error of coverage about ±4.4 points), from [`shared/results/report/by_scenario.csv`](../shared/results/report/by_scenario.csv).

Coverage of two-sided 95% intervals: the % of audit years in which the interval contains the true rate; the parentheses show the % of audit years in which it lies entirely above / below.

| Population | Expansion | Ratio | Regression | Microsimulation |
|---|---|---|---|---|
| right-skewed, 5% errors | 48.0 (0.0/52.0) | 52.0 (0.0/48.0) | 48.0 (0.0/52.0) | 0.0 (36.0/64.0) |
| right-skewed, 30% errors | 80.0 (0.0/20.0) | 80.0 (4.0/16.0) | 76.0 (8.0/16.0) | 20.0 (60.0/20.0) |
| right-skewed, 70% errors | 84.0 (0.0/16.0) | 80.0 (20.0/0.0) | 76.0 (16.0/8.0) | 12.0 (48.0/40.0) |
| right-skewed, 95% errors | 100.0 (0.0/0.0) | 40.0 (60.0/0.0) | 36.0 (64.0/0.0) | 0.0 (72.0/28.0) |
| two-spike, 5% errors | 76.0 (0.0/24.0) | 80.0 (0.0/20.0) | 76.0 (0.0/24.0) | 76.0 (4.0/20.0) |
| two-spike, 30% errors | 96.0 (4.0/0.0) | 96.0 (4.0/0.0) | 96.0 (4.0/0.0) | 44.0 (24.0/32.0) |
| two-spike, 70% errors | 92.0 (0.0/8.0) | 96.0 (4.0/0.0) | 92.0 (4.0/4.0) | 36.0 (28.0/36.0) |
| two-spike, 95% errors | 100.0 (0.0/0.0) | 64.0 (36.0/0.0) | 64.0 (36.0/0.0) | 56.0 (32.0/12.0) |
| left-skewed, 5% errors | 84.0 (0.0/16.0) | 84.0 (0.0/16.0) | 84.0 (0.0/16.0) | 28.0 (4.0/68.0) |
| left-skewed, 30% errors | 96.0 (0.0/4.0) | 92.0 (4.0/4.0) | 92.0 (4.0/4.0) | 52.0 (28.0/20.0) |
| left-skewed, 70% errors | 96.0 (4.0/0.0) | 96.0 (4.0/0.0) | 96.0 (4.0/0.0) | 36.0 (40.0/24.0) |
| left-skewed, 95% errors | 96.0 (4.0/0.0) | 84.0 (16.0/0.0) | 84.0 (16.0/0.0) | 48.0 (32.0/20.0) |

All 12 populations are in `estimation/results/cert/`.
