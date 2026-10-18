# PERM / CERT

Individual claim or benefit-level errors. Two populations share this folder; files are prefixed `perm_` or `cert_`.

- **PERM** (Medicaid): payment universes for 9 states, with claims-review errors and eligibility errors. Each state's true eligibility rate is set on a grid from 2.00% to 4.00%. Estimands: each state's gross, eligibility and claims improper payment rates at federal share, Σ y·FMAP / Σ x·FMAP, and the 9 states pooled. Every PERM error is an overpayment, so gross = overpayments = net and underpayments are zero.
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
| `ipsim perm-cert/estimation/perm.yaml` then `perm_national.yaml` | One scenario per state: strata = payment type (FFS, MC) × five equal-count payment quintiles; Neyman allocation of 520 payments per state-year (n_h ∝ N_h × S_h, S_h = standard deviation of gross improper dollars); systematic selection after sorting by amount paid within stratum; all components share one sample; 25 audit years. `perm_national.yaml` pools the states: dollars and variances add for the analytic methods; the bootstrap simulation sums the states' iterations | `estimation/results/perm/state_<id>/` (domain = `state\|component`), `estimation/results/perm/national/` |
| `ipsim perm-cert/estimation/cert.yaml` | SRS of 30 claims; 1,000 audit years per population | `estimation/results/cert/<shape>_p<rate>/` |

Methods: `*_10_expansion.sql`, `*_20_ratio.sql`, `*_30_regression.sql`, and the audit-finding bootstrap simulation (`*_40_simulation_inputs.sql` + `perm_simulation.py` / `cert_simulation.py`), all scored in `*_90_score.sql`.

- **PERM bootstrap simulation:** within each stratum, a non-audited payment is in error with the audited error rate; an error is partial with the audited partial share (its improper share drawn from the stratum's audited partial errors), otherwise the whole payment is improper. A beneficiary with no audited payment is ineligible with the audited beneficiaries' eligibility error rate. Fixed rates (README) or parametric rates (`sim_rates: parametric`: each rate redrawn as Binomial(n, rate)/n before every iteration). 25 audit years per state, 1,000 iterations.
- **CERT bootstrap simulation:** each non-audited claim takes the improper share of a random audited claim. Run on the first 100 audit years per population; results are reported for audit years 1–25. Formulas: [`shared/sql/lib/02_estimators.sql`](../shared/sql/lib/02_estimators.sql). The systematic sample's variance is estimated as if it were stratified SRS, the usual approximation; the study measures how well that works.

## CERT results (SRS of 30 claims)

Every method is scored on the same 25 audit years per population (audit years 1–25), from [`shared/results/report/by_scenario.csv`](../shared/results/report/by_scenario.csv).

Each cell counts audit years out of 25: how many of the 95% intervals contain the true rate; the parentheses count the intervals entirely above / entirely below it. A valid 95% interval contains the truth in about 24 of 25.

| Population | Expansion | Ratio | Regression | Bootstrap simulation |
|---|---|---|---|---|
| right-skewed, 5% errors | 12/25 (0/13) | 13/25 (0/12) | 12/25 (0/13) | 0/25 (9/16) |
| right-skewed, 30% errors | 20/25 (0/5) | 20/25 (1/4) | 19/25 (2/4) | 5/25 (15/5) |
| right-skewed, 70% errors | 21/25 (0/4) | 20/25 (5/0) | 19/25 (4/2) | 3/25 (12/10) |
| right-skewed, 95% errors | 25/25 (0/0) | 10/25 (15/0) | 9/25 (16/0) | 0/25 (18/7) |
| two-spike, 5% errors | 19/25 (0/6) | 20/25 (0/5) | 19/25 (0/6) | 19/25 (1/5) |
| two-spike, 30% errors | 24/25 (1/0) | 24/25 (1/0) | 24/25 (1/0) | 11/25 (6/8) |
| two-spike, 70% errors | 23/25 (0/2) | 24/25 (1/0) | 23/25 (1/1) | 9/25 (7/9) |
| two-spike, 95% errors | 25/25 (0/0) | 16/25 (9/0) | 16/25 (9/0) | 14/25 (8/3) |
| left-skewed, 5% errors | 21/25 (0/4) | 21/25 (0/4) | 21/25 (0/4) | 7/25 (1/17) |
| left-skewed, 30% errors | 24/25 (0/1) | 23/25 (1/1) | 23/25 (1/1) | 13/25 (7/5) |
| left-skewed, 70% errors | 24/25 (1/0) | 24/25 (1/0) | 24/25 (1/0) | 9/25 (10/6) |
| left-skewed, 95% errors | 24/25 (1/0) | 21/25 (4/0) | 21/25 (4/0) | 12/25 (8/5) |

Average error of the point estimate over the 25 audit years, as a % of the true rate (in parentheses, the average signed error: + high, − low):

| Population | True rate | Expansion | Ratio | Regression | Bootstrap simulation |
|---|---|---|---|---|---|
| right-skewed, 5% errors | 4.82% | 66.9% (−47.1%) | 75.3% (−36.3%) | 70.1% (−44.0%) | 66.8% (−11.4%) |
| right-skewed, 30% errors | 30.37% | 55.4% (+8.2%) | 37.7% (+2.7%) | 36.8% (+5.7%) | 20.0% (+8.5%) |
| right-skewed, 70% errors | 70.10% | 28.8% (+4.9%) | 13.7% (+3.9%) | 14.9% (+1.2%) | 8.9% (+2.3%) |
| right-skewed, 95% errors | 95.15% | 14.0% (−3.8%) | 4.1% (+2.2%) | 4.2% (+2.2%) | 3.5% (+0.8%) |
| two-spike, 5% errors | 4.09% | 60.7% (+5.5%) | 59.8% (+4.4%) | 62.5% (+5.7%) | 60.6% (+10.4%) |
| two-spike, 30% errors | 29.67% | 23.1% (−1.1%) | 23.0% (−2.4%) | 22.8% (−1.4%) | 24.7% (−4.0%) |
| two-spike, 70% errors | 69.62% | 12.1% (−4.2%) | 10.4% (−2.6%) | 10.7% (−3.0%) | 9.5% (−1.3%) |
| two-spike, 95% errors | 94.45% | 6.7% (+1.6%) | 3.5% (+1.5%) | 3.5% (+1.5%) | 3.6% (+1.9%) |
| left-skewed, 5% errors | 4.95% | 44.4% (−19.5%) | 44.2% (−19.6%) | 45.4% (−19.8%) | 49.1% (−16.7%) |
| left-skewed, 30% errors | 30.04% | 23.2% (+3.7%) | 23.3% (+3.0%) | 23.8% (+2.1%) | 22.2% (+1.6%) |
| left-skewed, 70% errors | 69.97% | 10.2% (+1.3%) | 10.5% (+1.8%) | 10.6% (+2.0%) | 10.5% (+2.1%) |
| left-skewed, 95% errors | 95.11% | 3.2% (0.0%) | 3.0% (−0.7%) | 3.1% (−0.6%) | 3.0% (−0.6%) |

All 12 populations are in `estimation/results/cert/`.
