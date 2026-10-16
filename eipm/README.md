# EIPM (Marketplace APTC)

Beneficiary subsidy eligibility errors on advance premium tax credits in the Federally-facilitated Exchange. Estimand: the **gross APTC improper payment rate**, Σ|y| / Σx over applications.

## errors/ — build the population, then apply fake errors

Run: `ipsim eipm/errors/config.yaml` → `errors/output/base/`

| Step | File | What it does |
|---|---|---|
| Population | `01_population.sql` | 150,000 households (1 = 100 real); income, household size, age, benchmark premium; APTC under the enhanced (2021–2025) applicable-percentage schedule; recipients only |
| Errors | `02_apply_errors.sql` | Rare errors: income misstatement (APTC recomputed at true income), eligibility failure and missing documentation (whole APTC); one closed-form multiplier |
| Truth | `03_truth.sql` | True totals and rates, overall and by income-band stratum |
| Checks | `04_checks.sql` | FY 2025 target: 0.89%; unique ids |

## estimation/ — sample the population and estimate with each method

Run: `ipsim eipm/estimation/config.yaml` → `estimation/results/base/`

Design: stratified SRS of 2,000 applications, 500 per income band (EIPM strata not public; illustrative), 200 Monte Carlo samples. Methods: `10_expansion.sql`, `20_ratio.sql`, `30_regression.sql`, `40_simulation.sql` (bootstrap), scored in `90_score.sql`. Formulas: [`shared/sql/lib/02_estimators.sql`](../shared/sql/lib/02_estimators.sql).

With roughly 1.5% of applications in error, each sample holds only about 30 errors, the regime where normal intervals are least reliable.
