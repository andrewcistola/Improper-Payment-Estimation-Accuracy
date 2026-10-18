# EIPM (Marketplace APTC)

Advance premium tax credit (APTC) errors in the Federally-facilitated Exchange. The public FFE results report no underpayments (FY 2023–2025), so every error here is an overpayment: gross = overpayments = net. Three measures, each divided by total APTC paid: **gross**, **technically improper** (a required data match was not run, so the whole APTC counts as improper) and **monetary** (APTC paid on income the record does not support). Dollars are national (× 100).

## errors/ — build the population, then apply fake errors

Run: `ipsim eipm/errors/config.yaml` → `errors/output/base/`

| Step | File | What it does |
|---|---|---|
| Population | `01_population.sql` | 150,000 households (1 = 100 real); income, household size, age, benchmark premium; APTC under the enhanced (2021–2025) applicable-percentage schedule; recipients only (142,152 applications) |
| Errors | `02_apply_errors.sql` | At most one error per application. **Technical** (y = whole APTC) with probability p_t = 0.89% × 48%; **monetary** (the supported income is higher by a lognormal factor; APTC recomputed; y = APTC paid − correct APTC) with probability p_m, closed form so that monetary dollars are 52% of the 0.89% target. Strata: five equal-count quintiles of annual APTC (P1..P5) |
| Truth | `03_truth.sql` | True totals and rates (gross, technical, monetary), overall and by stratum |
| Checks | `04_checks.sql` | FY 2025 targets: gross 0.89%, technical 0.43 points, no underpayments; unique ids |

The 48% technical share is the FY 2025 split (0.43 of 0.89 points, $282.44M of $657.46M). The EIPM strata are not public; the APTC quintiles are illustrative and follow the same rule as PERM's payment quintiles.

## estimation/ — sample the population and estimate with each method

Run: `ipsim eipm/estimation/config.yaml` → `estimation/results/base/`

Design (`01_frame.sql`): stratified SRS of 2,000 applications per audit year, Neyman allocation across the five APTC quintiles (n_h ∝ N_h × S_h, S_h = standard deviation of improper APTC dollars; from the population, standing in for prior-year data; allocation in `allocation.json`); 25 audit years. All three measures share one sample.

Methods:
- **Expansion, ratio, regression** (`10_expansion.sql`, `20_ratio.sql`, `30_regression.sql`): the shared estimators with normal intervals ([`shared/sql/lib/02_estimators.sql`](../shared/sql/lib/02_estimators.sql)).
- **Bootstrap simulation, parametric rates** (`40_simulation_inputs.sql` + `simulation.py`; reported): within each APTC quintile, a non-audited application is in error with the audited error rate; an error is monetary with the audited monetary share (its supported ÷ used income ratio drawn from the stratum's audited monetary errors, APTC recomputed), otherwise technical (whole APTC). Before each iteration, the error rate and monetary share are redrawn as Binomial(n, f/n)/n and Binomial(f, g/f)/f. Audited applications keep their findings. 1,000 iterations; mean and 2.5th–97.5th percentiles.
- **Bootstrap simulation, fixed rates** (`--set sim_rates=fixed`; comparison only, `estimation/results_fixed/`): the audited rates in every iteration. Its intervals are far too narrow; see [`manuscripts/`](../manuscripts/).

All methods are scored in `90_score.sql`.

With about 2% of applications in error, an audit of 2,000 holds about 45 errors, only about 9 of them technical: the rare-error regime where normal intervals are least reliable.

## Results (25 audit years)

Each row gives the true value and, over the 25 audit years, the median point estimate and the median upper and lower bounds of the 95% interval. National dollars (× 100); rates are dollars ÷ total payments ($81.7B).

**Dollars**

| Measure | Method | True | Estimated | Upper bound | Lower bound |
|---|---|---|---|---|---|
| Gross (all EIPM errors are overpayments) | Expansion | $0.75B | $0.68B | $0.96B | $0.40B |
|  | Ratio | $0.75B | $0.68B | $0.96B | $0.40B |
|  | Regression | $0.75B | $0.68B | $0.96B | $0.40B |
|  | Bootstrap simulation (parametric rates) | $0.75B | $0.66B | $0.94B | $0.43B |
| Technically improper | Expansion | $0.35B | $0.30B | $0.51B | $0.08B |
|  | Ratio | $0.35B | $0.30B | $0.52B | $0.08B |
|  | Regression | $0.35B | $0.30B | $0.51B | $0.08B |
|  | Bootstrap simulation (parametric rates) | $0.35B | $0.29B | $0.55B | $0.11B |
| Monetary | Expansion | $0.39B | $0.39B | $0.57B | $0.22B |
|  | Ratio | $0.39B | $0.39B | $0.57B | $0.22B |
|  | Regression | $0.39B | $0.39B | $0.57B | $0.22B |
|  | Bootstrap simulation (parametric rates) | $0.39B | $0.37B | $0.50B | $0.26B |

**Rates**

| Measure | Method | True | Estimated | Upper bound | Lower bound |
|---|---|---|---|---|---|
| Gross (all EIPM errors are overpayments) | Expansion | 0.92% | 0.83% | 1.17% | 0.49% |
|  | Ratio | 0.92% | 0.83% | 1.17% | 0.49% |
|  | Regression | 0.92% | 0.83% | 1.17% | 0.49% |
|  | Bootstrap simulation (parametric rates) | 0.92% | 0.81% | 1.16% | 0.53% |
| Technically improper | Expansion | 0.43% | 0.36% | 0.63% | 0.09% |
|  | Ratio | 0.43% | 0.36% | 0.63% | 0.09% |
|  | Regression | 0.43% | 0.36% | 0.63% | 0.09% |
|  | Bootstrap simulation (parametric rates) | 0.43% | 0.35% | 0.67% | 0.13% |
| Monetary | Expansion | 0.48% | 0.48% | 0.70% | 0.26% |
|  | Ratio | 0.48% | 0.48% | 0.70% | 0.26% |
|  | Regression | 0.48% | 0.48% | 0.70% | 0.26% |
|  | Bootstrap simulation (parametric rates) | 0.48% | 0.45% | 0.62% | 0.31% |

**How often the 95% interval contains the truth** (out of 25 audit years; in parentheses, intervals entirely above / entirely below the truth). A valid interval contains it in about 24 of 25.

| Measure | Expansion | Ratio | Regression | Bootstrap simulation (parametric rates) |
|---|---|---|---|---|
| Gross (all EIPM errors are overpayments) | 22/25 (0/3) | 22/25 (0/3) | 22/25 (0/3) | 23/25 (0/2) |
| Technically improper | 19/25 (1/5) | 19/25 (1/5) | 19/25 (1/5) | 20/25 (1/4) |
| Monetary | 22/25 (0/3) | 22/25 (0/3) | 22/25 (0/3) | 22/25 (1/2) |

From [`shared/results/report/by_scenario.csv`](../shared/results/report/by_scenario.csv).
