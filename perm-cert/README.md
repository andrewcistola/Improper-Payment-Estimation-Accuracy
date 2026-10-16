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

## CERT pilot results (SRS of 30 claims, 1,000 samples × 1,000 bootstrap replicates)

Coverage of two-sided 95% intervals (%); the parentheses show the share of intervals entirely above / below the true rate.

| Population | Expansion | Ratio | Percentile | BCa | Bootstrap-t (median width ÷ true rate) |
|---|---|---|---|---|---|
| right-skewed, 5% errors | 55.9 (0.0/44.1) | 57.8 (0.0/42.2) | 63.7 (0.0/36.3) | 68.9 (0.6/30.5) | 78.1 (0.0/21.9), width 8,883 |
| right-skewed, 30% | 78.7 (0.0/21.3) | 82.8 (3.2/14.0) | 90.5 (1.4/8.1) | 91.2 (2.6/6.2) | 97.9 (0.5/1.6), width 2.4 |
| right-skewed, 70% | 84.0 (0.1/15.9) | 82.2 (14.3/3.5) | 89.7 (8.7/1.6) | 90.9 (6.4/2.7) | 97.4 (2.1/0.5), width 1.1 |
| right-skewed, 95% | 83.8 (0.4/15.8) | 58.0 (41.8/0.2) | 64.0 (36.0/0.0) | 70.0 (29.4/0.6) | 78.6 (21.4/0.0), width 470 |
| two-spike, 30% | 92.0 (1.3/6.7) | 92.7 (1.4/5.9) | 94.7 (1.5/3.8) | 97.2 (1.4/1.4) | 99.0 (1.0/0.0), width 1.3 |
| two-spike, 95% | 92.5 (4.5/3.0) | 74.3 (25.5/0.2) | 74.9 (24.5/0.6) | 79.0 (19.9/1.1) | 79.5 (19.8/0.7), width 12 |
| left-skewed, 30% | 92.1 (1.9/6.0) | 91.7 (2.1/6.2) | 93.1 (2.2/4.7) | 94.6 (2.1/3.3) | 98.3 (1.7/0.0), width 1.2 |
| left-skewed, 95% | 89.7 (9.8/0.5) | 78.8 (21.1/0.1) | 78.8 (21.1/0.1) | 78.0 (21.1/0.9) | 78.2 (21.1/0.7), width 67 |

All 12 populations are in `estimation/results/cert/`. With 30 claims:

- **Degenerate samples at the extremes:** at a 5% error rate about 21% of samples hold no errors, and at 95% about 21% hold only errors. These samples give a zero spread and an interval that cannot contain the truth, whatever the method.
- **Middle error rates:** BCa and the percentile bootstrap improve on normal intervals, especially for right-skewed payments.
- **Bootstrap-t:** it over-covers, and its width is unstable when some replicates have a near-zero standard error.
