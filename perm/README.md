# PERM (Medicaid)

Individual claim or benefit-level errors in Medicaid: payment universes for 9 states, with claims-review errors and eligibility errors. Each state's true eligibility rate is set on a grid from 2.00% to 4.00%. Estimands: each state's gross, eligibility and claims improper payment rates at federal share, Σ y·FMAP / Σ x·FMAP, and the 9 states pooled. Every PERM error is an overpayment, so gross = overpayments = net and underpayments are zero. Dollars are national (× 200). The CERT population, which once shared this folder, is in [`cert/`](../cert/).

## errors/ — build the population, then apply fake errors

| Run | Steps | Output |
|---|---|---|
| `ipsim perm/errors/config.yaml` | `01_population.sql` (payments and strata) → `02_claims_errors.sql` → `03_eligibility_errors.sql` → `04_truth.sql` → `05_checks.sql` | `errors/output/state_elig_grid/` (Parquet not committed: 3.09M payments) |

- **Payments:** FFS claims and monthly managed-care capitations.
- **Strata:** payment type (FFS, MC) × five equal-count quintiles of the amount paid within each state (10 strata per state; `<state>_<type>_P1` .. `_P5`). Quarter is recorded on every payment but is not a stratification variable.
- **Claims errors:** FFS 6.5% of payments (70% all-or-nothing, 30% partial); MC 0.3%. By default the probability does not depend on the amount paid; `--set size_beta=0.5` (default 0) multiplies it by (paid ÷ mean paid within state × payment type)^0.5, capped at 0.95 and recalibrated so expected claims-error dollars are unchanged (`02_claims_errors.sql`). The committed population is size_beta = 0.
- **Eligibility errors:** placed beneficiary by beneficiary in random order, so each state's true rate never exceeds its grid value. Eligibility is a whole-year beneficiary attribute: when a beneficiary is in error, every one of that beneficiary's payments in the year is improper. Real PERM determines eligibility as of the sampled payment's month.
- **Divergences from the real program:** PERM measures 17 states per cycle on a 3-year rotation, with state-specific, precision-driven sample sizes, FFS and managed care as separate components, denied claims in the universe and a claim-level FMAP (90% for expansion adults). Here: 9 states in one cycle, a fixed 520 payments per state-year, equal-count quintiles, one FMAP per state, no denied claims, whole-year eligibility.
- **Checks:** the pooled overall rate matches Medicaid's 6.12%; each state's true eligibility rate matches its grid value; every payment id is unique.


## estimation/ — sample the population and estimate with each method

| Run | Design | Output |
|---|---|---|
| `ipsim perm/estimation/config.yaml` then `national.yaml` | One scenario per state: strata = payment type (FFS, MC) × five equal-count payment quintiles; Neyman allocation of 520 payments per state-year (n_h ∝ N_h × S_h, S_h = standard deviation of gross improper dollars); systematic selection after sorting by amount paid within stratum; all components share one sample; 25 audit years. The systematic sample's variance is estimated with the stratified-SRS formula, the usual approximation (conservative after sorting by size); the study measures how well that works. The eligibility component is estimated from the beneficiaries attached to the sampled payments, so audited beneficiaries are selected in proportion to their number of payments; the estimate is unbiased because eligibility error is independent of payment count by construction. `national.yaml` pools the states: dollars and variances add for the analytic methods; the simulation sums the states' iterations | `estimation/results/state_<id>/` (domain = `state\|component`), `estimation/results/national/` |

Methods: `10_expansion.sql`, `20_ratio.sql`, `30_regression.sql`, and the audit-finding simulation (`40_simulation_inputs.sql` + `simulation.py`), all scored in `90_score.sql`; `95_national.sql` pools the states. Formulas: [`shared/sql/lib/02_estimators.sql`](../shared/sql/lib/02_estimators.sql).

- **Regression** (`30_regression.sql` + [`shared/ipsim/regression.py`](../shared/ipsim/regression.py)): within each design stratum, improper dollars are regressed on the amount paid and, for PERM, month of service and the beneficiary's number of payments and total paid; the models predict every payment or claim, the audit residuals are added, and the interval comes from the residuals. A stratum with fewer than 10 audited errors uses an intercept-only model (expansion within that stratum). In PERM that is every stratum except the largest-payment FFS stratum, which holds about 60% of each state's audit (about 26 errors).

- **Bootstrap simulation:** within each stratum, a non-audited payment is in error with the audited error rate; an error is partial with the audited partial share (its improper share drawn from the stratum's audited partial errors), otherwise the whole payment is improper. A beneficiary with no audited payment is ineligible with the audited beneficiaries' eligibility error rate; an audited beneficiary's whole-year eligibility finding is propagated to all of that beneficiary's payments, audited or not. Parametric rates (reported) redraw the counts before every iteration: the error count f̃ ~ Binomial(n, f/n), then the partial count out of it, g̃ ~ Binomial(f̃, g/f) (0 when f̃ = 0), and the eligibility count Binomial(n_e, f_e/n_e); or fixed rates (`--set sim_rates=fixed`, comparison only, `estimation/results_fixed/`). 25 audit years per state, 1,000 iterations. Same-beneficiary clustering within a payment sample (a few pairs per 520) is ignored by every method.

## Results (25 audit years)

Each row gives the true value and, over the 25 audit years, the median point estimate and the median upper and lower bounds of the 95% interval. National dollars (× 200, federal share); rates are dollars ÷ total payments ($142.0B).

**Dollars**

| Measure | Method | True | Estimated | Upper bound | Lower bound |
|---|---|---|---|---|---|
| Gross | Expansion | $8.65B | $8.57B | $9.74B | $7.42B |
|  | Ratio | $8.65B | $8.52B | $9.70B | $7.38B |
|  | Regression | $8.65B | $8.57B | $9.67B | $7.43B |
|  | Simulation (parametric rates) | $8.65B | $8.49B | $9.40B | $7.61B |
| Eligibility | Expansion | $4.34B | $4.33B | $5.18B | $3.48B |
|  | Ratio | $4.34B | $4.33B | $5.18B | $3.48B |
|  | Regression | $4.34B | $4.36B | $5.21B | $3.52B |
|  | Simulation (parametric rates) | $4.34B | $4.24B | $4.94B | $3.57B |
| Claims | Expansion | $4.44B | $4.50B | $5.26B | $3.63B |
|  | Ratio | $4.44B | $4.52B | $5.28B | $3.67B |
|  | Regression | $4.44B | $4.48B | $5.22B | $3.71B |
|  | Simulation (parametric rates) | $4.44B | $4.43B | $5.06B | $3.81B |

**Rates**

| Measure | Method | True | Estimated | Upper bound | Lower bound |
|---|---|---|---|---|---|
| Gross | Expansion | 6.09% | 6.04% | 6.86% | 5.23% |
|  | Ratio | 6.09% | 6.00% | 6.83% | 5.20% |
|  | Regression | 6.09% | 6.03% | 6.81% | 5.23% |
|  | Simulation (parametric rates) | 6.09% | 5.98% | 6.62% | 5.36% |
| Eligibility | Expansion | 3.06% | 3.05% | 3.64% | 2.45% |
|  | Ratio | 3.06% | 3.05% | 3.65% | 2.45% |
|  | Regression | 3.06% | 3.07% | 3.67% | 2.48% |
|  | Simulation (parametric rates) | 3.06% | 2.99% | 3.48% | 2.51% |
| Claims | Expansion | 3.13% | 3.17% | 3.70% | 2.55% |
|  | Ratio | 3.13% | 3.18% | 3.72% | 2.58% |
|  | Regression | 3.13% | 3.15% | 3.68% | 2.62% |
|  | Simulation (parametric rates) | 3.13% | 3.12% | 3.56% | 2.68% |

**How often the 95% interval contains the truth** (out of 25 audit years; in parentheses, intervals entirely above / entirely below the truth). A valid interval contains it in about 24 of 25.

| Measure | Expansion | Ratio | Regression | Simulation (parametric rates) |
|---|---|---|---|---|
| Gross | 23/25 (0/2) | 23/25 (0/2) | 23/25 (0/2) | 24/25 (0/1) |
| Eligibility | 21/25 (0/4) | 21/25 (0/4) | 21/25 (0/4) | 24/25 (0/1) |
| Claims | 23/25 (0/2) | 23/25 (0/2) | 23/25 (0/2) | 23/25 (1/1) |

From [`shared/results/report/by_scenario.csv`](../shared/results/report/by_scenario.csv) (`python shared/build_readmes.py` regenerates this section).
