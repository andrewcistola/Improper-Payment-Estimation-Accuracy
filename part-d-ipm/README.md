# Part D IPM

Claim (PDE) errors that flow through the post-IRA benefit to Medicare reinsurance and low-income cost-sharing payments. Four measures: **overpayments**, **underpayments**, **gross** (over + under) and **net** (over − under). Each beneficiary's payment error (reinsurance + LICS) is netted first; totals are divided by all reported Part D payments (direct subsidy + reinsurance + LICS, $105.56B). Dollars are national (× 500).

## errors/ — build the population, then apply fake errors

Run: `ipsim part-d-ipm/errors/config.yaml` → `errors/output/base/` (about 45 s)

| Step | File | What it does |
|---|---|---|
| Population | `01_population.sql` | 108,000 beneficiaries (1 = 500 real), ~4.5M PDEs; GDC = ingredient cost + dispensing fee + sales tax + vaccine admin fee. 4% of beneficiaries are in long-term care (LTC) and fill about twice as many PDEs (illustrative) |
| Errors | `02_candidate_errors.sql` | One candidate error per PDE, as a share e of GDC: 90% full errors (e = 100%, GDC → 0), 10% partial errors with e uniform on [−100%, 100%) (e < 0 is an underpayment; −100% means the correct GDC is double) |
| Errors | `03_init_calibration.sql` | Error rates used as stated: no calibration |
| Errors | `04_apply_errors.sql` | Activates each candidate with probability 2.5%, or 10% for LTC claims |
| Errors | `05_benefit.sql` | CY 2025 standard benefit ($590 deductible, $2,000 out-of-pocket cap, Manufacturer Discount Program, 20%/40% reinsurance, LIS copays), run on submitted and corrected PDEs |
| Truth | `07_population_truth.sql` | x = direct subsidy + reinsurance + LICS; y = Medicare(submitted) − Medicare(corrected) |
| Checks | `08_checks.sql` | Claim error rates (10% LTC, 2.5% other) and full/partial shares; gross, over and under reported against FY 2025 (4.00%, $3.70B, $0.52B) but not calibrated to them; unique ids |

Outputs: `population.parquet` (one row per beneficiary), `pde_detail.parquet` (every PDE's submitted vs corrected liability by payer), `truth.json`, `checks.json`. The Parquet files are not committed (98 MB); rebuild them and compare hashes with `manifest.json`.

## estimation/ — sample the population and estimate with each method

Run: `ipsim part-d-ipm/estimation/config.yaml` → `estimation/results/base/`

Two audits per audit year (25 audit years):

- **Beneficiary audit** (`01_frame.sql`): simple random sample of 990 beneficiaries, every PDE reviewed. Used by **ratio** (`20_ratio.sql`) and **regression** (`30_regression.sql` + `shared/ipsim/regression.py`): within post-strata (LTC; LIS; other), beneficiary payment error is regressed on Medicare payment, gross drug cost, number of PDEs and whether the beneficiary reached the catastrophic phase; the models predict every beneficiary, the audit residuals are added, and the interval comes from the residuals.
- **PDE audit** (`40_simulation_inputs.sql`): 5,000 PDEs, stratified by claim type: (a) LTC, any cost; (b) non-LTC, lowest decile of GDC; (c) other non-LTC. Neyman allocation, n_h ∝ N_h × S_h (S_h = standard deviation of PDE error dollars; from the population, standing in for prior-year data). Used by:
  - **Expansion** (`simulation.py`, `run_expansion`): each stratum's error rate (audited error dollars ÷ audited GDC) is applied to every PDE in that stratum; the benefit is rerun for all 108,000 beneficiaries. Delta-method interval (each stratum's rate moved ±1 SE, one rerun each way).
  - **Bootstrap simulation, parametric rates** (`simulation.py`; reported): every non-audited PDE in the full population takes a finding from its own stratum: before each iteration, the stratum's error rate and partial-error share are redrawn as Binomial(n, f/n)/n and Binomial(f, g/f)/f, a PDE is in error at that rate, and partial sizes come from the stratum's audited partial errors (audited PDEs keep their own). The benefit is rerun; 1,000 iterations; mean and 2.5th–97.5th percentiles.
  - **Bootstrap simulation, fixed rates** (`--set sim_rates=fixed`; comparison only, `estimation/results_fixed/`): the audited rates in every iteration. Its intervals are far too narrow; see [`manuscripts/`](../manuscripts/).

All methods are scored in `90_score.sql`.

## Results (25 audit years)

Each row gives the true value and, over the 25 audit years, the median point estimate and the median upper and lower bounds of the 95% interval. National dollars (× 500); rates are dollars ÷ total payments ($105.6B).

**Dollars**

| Measure | Method | True | Estimated | Upper bound | Lower bound |
|---|---|---|---|---|---|
| Overpayments | Expansion | $1.44B | $1.28B | $1.95B | $0.57B |
|  | Ratio | $1.44B | $1.48B | $2.20B | $0.72B |
|  | Regression | $1.44B | $1.51B | $2.17B | $0.85B |
|  | Bootstrap simulation (parametric rates) | $1.44B | $1.44B | $1.68B | $1.21B |
| Underpayments | Expansion | $0.02B | $0.00B | $0.00B | $0.00B |
|  | Ratio | $0.02B | $0.01B | $0.03B | $0.00B |
|  | Regression | $0.02B | $0.01B | $0.02B | $0.00B |
|  | Bootstrap simulation (parametric rates) | $0.02B | $0.02B | $0.04B | $0.01B |
| Gross | Expansion | $1.46B | $1.28B | $1.95B | $0.57B |
|  | Ratio | $1.46B | $1.49B | $2.22B | $0.74B |
|  | Regression | $1.46B | $1.52B | $2.19B | $0.89B |
|  | Bootstrap simulation (parametric rates) | $1.46B | $1.46B | $1.69B | $1.23B |
| Net | Expansion | $1.42B | $1.28B | $1.95B | $0.57B |
|  | Ratio | $1.42B | $1.45B | $2.19B | $0.72B |
|  | Regression | $1.42B | $1.49B | $2.15B | $0.84B |
|  | Bootstrap simulation (parametric rates) | $1.42B | $1.41B | $1.63B | $1.18B |

**Rates**

| Measure | Method | True | Estimated | Upper bound | Lower bound |
|---|---|---|---|---|---|
| Overpayments | Expansion | 1.36% | 1.22% | 1.85% | 0.54% |
|  | Ratio | 1.36% | 1.40% | 2.09% | 0.69% |
|  | Regression | 1.36% | 1.43% | 2.06% | 0.80% |
|  | Bootstrap simulation (parametric rates) | 1.36% | 1.37% | 1.59% | 1.15% |
| Underpayments | Expansion | 0.02% | 0.00% | 0.00% | 0.00% |
|  | Ratio | 0.02% | 0.01% | 0.02% | 0.00% |
|  | Regression | 0.02% | 0.01% | 0.02% | 0.00% |
|  | Bootstrap simulation (parametric rates) | 0.02% | 0.02% | 0.04% | 0.01% |
| Gross | Expansion | 1.38% | 1.22% | 1.85% | 0.54% |
|  | Ratio | 1.38% | 1.41% | 2.10% | 0.70% |
|  | Regression | 1.38% | 1.44% | 2.07% | 0.84% |
|  | Bootstrap simulation (parametric rates) | 1.38% | 1.38% | 1.60% | 1.16% |
| Net | Expansion | 1.34% | 1.22% | 1.85% | 0.54% |
|  | Ratio | 1.34% | 1.37% | 2.07% | 0.68% |
|  | Regression | 1.34% | 1.41% | 2.03% | 0.80% |
|  | Bootstrap simulation (parametric rates) | 1.34% | 1.33% | 1.55% | 1.12% |

**How often the 95% interval contains the truth** (out of 25 audit years; in parentheses, intervals entirely above / entirely below the truth). A valid interval contains it in about 24 of 25.

| Measure | Expansion | Ratio | Regression | Bootstrap simulation (parametric rates) |
|---|---|---|---|---|
| Overpayments | 18/25 (0/7) | 18/25 (1/6) | 16/25 (4/5) | 25/25 (0/0) |
| Underpayments | 0/25 (0/25) | 15/25 (0/10) | 13/25 (2/10) | 20/25 (4/1) |
| Gross | 18/25 (0/7) | 18/25 (1/6) | 15/25 (4/6) | 25/25 (0/0) |
| Net | 19/25 (0/6) | 19/25 (1/5) | 16/25 (4/5) | 24/25 (0/1) |

From [`shared/results/report/by_scenario.csv`](../shared/results/report/by_scenario.csv).
