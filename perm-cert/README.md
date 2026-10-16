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
| `ipsim perm-cert/estimation/perm.yaml` | One scenario per state: systematic selection after sorting by amount paid, within strata; 400 FFS + 120 MC payments a year; all components share one sample; 200 Monte Carlo samples | `estimation/results/perm/state_<id>/` (domain = `state\|component`) |
| `ipsim perm-cert/estimation/cert.yaml` | SRS of 30 claims; 1,000 Monte Carlo samples per population | `estimation/results/cert/<shape>_p<rate>/` |

Methods: `*_10_expansion.sql`, `*_20_ratio.sql`, `*_30_regression.sql`, and the audit-finding simulation (`*_40_simulation_inputs.sql` + `perm_simulation.py` / `cert_simulation.py`), all scored in `*_90_score.sql`.

- **PERM simulation:** each non-audited payment takes the claims finding (improper share of the payment) of a random audited payment of the same payment type and size class; each beneficiary with no audited payment takes the eligibility finding of a random audited beneficiary. Scored on 25 audited samples per state.
- **CERT simulation:** each non-audited claim takes the improper share of a random audited claim. Scored on 100 audited samples per population. Formulas: [`shared/sql/lib/02_estimators.sql`](../shared/sql/lib/02_estimators.sql). The systematic sample's variance is estimated as if it were stratified SRS, the usual approximation; the study measures how well that works.

## CERT results (SRS of 30 claims)

> **Placeholder.** The CERT runs with the audit-finding microsimulation are in progress; this table will be filled in when they finish.

Coverage of two-sided 95% intervals (%); the parentheses will show the share of intervals entirely above / below the true rate.

| Population | Expansion | Ratio | Regression | Microsimulation (assign) | Microsimulation (resample) |
|---|---|---|---|---|---|
| right-skewed, 5% errors | _pending_ | _pending_ | _pending_ | _pending_ | _pending_ |
| right-skewed, 30% errors | _pending_ | _pending_ | _pending_ | _pending_ | _pending_ |
| right-skewed, 70% errors | _pending_ | _pending_ | _pending_ | _pending_ | _pending_ |
| right-skewed, 95% errors | _pending_ | _pending_ | _pending_ | _pending_ | _pending_ |
| two-spike, 5% errors | _pending_ | _pending_ | _pending_ | _pending_ | _pending_ |
| two-spike, 30% errors | _pending_ | _pending_ | _pending_ | _pending_ | _pending_ |
| two-spike, 70% errors | _pending_ | _pending_ | _pending_ | _pending_ | _pending_ |
| two-spike, 95% errors | _pending_ | _pending_ | _pending_ | _pending_ | _pending_ |
| left-skewed, 5% errors | _pending_ | _pending_ | _pending_ | _pending_ | _pending_ |
| left-skewed, 30% errors | _pending_ | _pending_ | _pending_ | _pending_ | _pending_ |
| left-skewed, 70% errors | _pending_ | _pending_ | _pending_ | _pending_ | _pending_ |
| left-skewed, 95% errors | _pending_ | _pending_ | _pending_ | _pending_ | _pending_ |

All 12 populations will be in `estimation/results/cert/`.
