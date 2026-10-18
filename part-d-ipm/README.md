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

- **Beneficiary audit** (`01_frame.sql`): simple random sample of 990 beneficiaries, every PDE reviewed. Used by **ratio** (`20_ratio.sql`) and **regression** (`30_regression.sql`, GREG on payment).
- **PDE audit** (`40_simulation_inputs.sql`): 5,000 PDEs, stratified by claim type: (a) LTC, any cost; (b) non-LTC, lowest decile of GDC; (c) other non-LTC. Neyman allocation, n_h ∝ N_h × S_h (S_h = standard deviation of PDE error dollars; from the population, standing in for prior-year data). Used by:
  - **Expansion** (`simulation.py`, `run_expansion`): each stratum's error rate (audited error dollars ÷ audited GDC) is applied to every PDE in that stratum; the benefit is rerun for all 108,000 beneficiaries. Delta-method interval (each stratum's rate moved ±1 SE, one rerun each way).
  - **Bootstrap simulation, fixed rates** (`simulation.py`): every non-audited PDE in the full population takes a finding from a random audited PDE of its own stratum (audited PDEs keep their own); the benefit is rerun; 1,000 iterations; mean and 2.5th–97.5th percentiles. Reported in the README.
  - **Bootstrap simulation, parametric rates** (`sim_rates: parametric`): before each iteration, each stratum's error rate and partial-error share are redrawn as Binomial(n, f/n)/n and Binomial(f, g/f)/f; partial sizes from the stratum's audited partial errors.

All methods are scored in `90_score.sql`.

## Results (25 audit years)

Each row gives the true value and, over the 25 audit years, the median point estimate and the median upper and lower bounds of the 95% interval. National dollars (× 500); rates are dollars ÷ total payments ($105.6B).

**Dollars**

| Measure | Method | True | Estimated | Upper bound | Lower bound |
|---|---|---|---|---|---|
| Overpayments | Expansion | $1.44B | $1.28B | $1.95B | $0.57B |
|  | Ratio | $1.44B | $1.48B | $2.20B | $0.72B |
|  | Regression | $1.44B | $1.47B | $2.21B | $0.73B |
|  | Bootstrap simulation (fixed rates) | $1.44B | $1.44B | $1.51B | $1.38B |
| Underpayments | Expansion | $0.02B | $-0.00B | $0.00B | $-0.00B |
|  | Ratio | $0.02B | $0.01B | $0.03B | $0.00B |
|  | Regression | $0.02B | $0.01B | $0.02B | $0.00B |
|  | Bootstrap simulation (fixed rates) | $0.02B | $0.02B | $0.03B | $0.02B |
| Gross | Expansion | $1.46B | $1.28B | $1.95B | $0.57B |
|  | Ratio | $1.46B | $1.49B | $2.22B | $0.74B |
|  | Regression | $1.46B | $1.48B | $2.22B | $0.77B |
|  | Bootstrap simulation (fixed rates) | $1.46B | $1.46B | $1.52B | $1.39B |
| Net | Expansion | $1.42B | $1.28B | $1.95B | $0.57B |
|  | Ratio | $1.42B | $1.45B | $2.19B | $0.72B |
|  | Regression | $1.42B | $1.45B | $2.20B | $0.70B |
|  | Bootstrap simulation (fixed rates) | $1.42B | $1.41B | $1.47B | $1.34B |

**Rates**

| Measure | Method | True | Estimated | Upper bound | Lower bound |
|---|---|---|---|---|---|
| Overpayments | Expansion | 1.36% | 1.22% | 1.85% | 0.54% |
|  | Ratio | 1.36% | 1.40% | 2.09% | 0.69% |
|  | Regression | 1.36% | 1.39% | 2.09% | 0.69% |
|  | Bootstrap simulation (fixed rates) | 1.36% | 1.37% | 1.43% | 1.31% |
| Underpayments | Expansion | 0.02% | -0.00% | 0.00% | -0.00% |
|  | Ratio | 0.02% | 0.01% | 0.02% | 0.00% |
|  | Regression | 0.02% | 0.01% | 0.02% | 0.00% |
|  | Bootstrap simulation (fixed rates) | 0.02% | 0.02% | 0.03% | 0.02% |
| Gross | Expansion | 1.38% | 1.22% | 1.85% | 0.54% |
|  | Ratio | 1.38% | 1.41% | 2.10% | 0.70% |
|  | Regression | 1.38% | 1.41% | 2.11% | 0.73% |
|  | Bootstrap simulation (fixed rates) | 1.38% | 1.38% | 1.44% | 1.32% |
| Net | Expansion | 1.34% | 1.22% | 1.85% | 0.54% |
|  | Ratio | 1.34% | 1.37% | 2.07% | 0.68% |
|  | Regression | 1.34% | 1.38% | 2.08% | 0.66% |
|  | Bootstrap simulation (fixed rates) | 1.34% | 1.33% | 1.40% | 1.27% |

**How often the 95% interval contains the truth** (out of 25 audit years; in parentheses, intervals entirely above / entirely below the truth). A valid interval contains it in about 24 of 25.

| Measure | Expansion | Ratio | Regression | Bootstrap simulation (fixed rates) |
|---|---|---|---|---|
| Overpayments | 18/25 (0/7) | 18/25 (1/6) | 20/25 (1/4) | 9/25 (9/7) |
| Underpayments | 0/25 (0/25) | 15/25 (0/10) | 15/25 (0/10) | 10/25 (12/3) |
| Gross | 18/25 (0/7) | 18/25 (1/6) | 20/25 (1/4) | 10/25 (8/7) |
| Net | 19/25 (0/6) | 19/25 (1/5) | 20/25 (1/4) | 11/25 (7/7) |

From [`shared/results/report/by_scenario.csv`](../shared/results/report/by_scenario.csv).
