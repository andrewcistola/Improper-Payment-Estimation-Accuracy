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
| Overpayments | Expansion | $4.19B | $4.08B | $5.14B | $2.93B |
|  | Ratio | $4.19B | $3.83B | $5.34B | $2.46B |
|  | Regression | $4.19B | $4.02B | $5.35B | $2.48B |
|  | Bootstrap simulation (fixed rates) | $4.19B | $4.19B | $4.28B | $4.09B |
| Underpayments | Expansion | $0.03B | $0.00B | $0.00B | $0.00B |
|  | Ratio | $0.03B | $0.02B | $0.04B | $0.00B |
|  | Regression | $0.03B | $0.02B | $0.04B | $0.00B |
|  | Bootstrap simulation (fixed rates) | $0.03B | $0.04B | $0.05B | $0.03B |
| Gross | Expansion | $4.22B | $4.08B | $5.14B | $2.93B |
|  | Ratio | $4.22B | $3.86B | $5.35B | $2.50B |
|  | Regression | $4.22B | $4.03B | $5.36B | $2.53B |
|  | Bootstrap simulation (fixed rates) | $4.22B | $4.22B | $4.31B | $4.12B |
| Net | Expansion | $4.15B | $4.08B | $5.14B | $2.93B |
|  | Ratio | $4.15B | $3.81B | $5.33B | $2.42B |
|  | Regression | $4.15B | $4.01B | $5.34B | $2.42B |
|  | Bootstrap simulation (fixed rates) | $4.15B | $4.15B | $4.25B | $4.05B |

**Rates**

| Measure | Method | True | Estimated | Upper bound | Lower bound |
|---|---|---|---|---|---|
| Overpayments | Expansion | 3.97% | 3.87% | 4.87% | 2.77% |
|  | Ratio | 3.97% | 3.63% | 5.06% | 2.33% |
|  | Regression | 3.97% | 3.81% | 5.07% | 2.35% |
|  | Bootstrap simulation (fixed rates) | 3.97% | 3.97% | 4.05% | 3.87% |
| Underpayments | Expansion | 0.03% | 0.00% | 0.00% | 0.00% |
|  | Ratio | 0.03% | 0.02% | 0.03% | 0.00% |
|  | Regression | 0.03% | 0.02% | 0.03% | 0.00% |
|  | Bootstrap simulation (fixed rates) | 0.03% | 0.04% | 0.04% | 0.03% |
| Gross | Expansion | 4.00% | 3.87% | 4.87% | 2.77% |
|  | Ratio | 4.00% | 3.65% | 5.07% | 2.37% |
|  | Regression | 4.00% | 3.82% | 5.08% | 2.39% |
|  | Bootstrap simulation (fixed rates) | 4.00% | 4.00% | 4.09% | 3.91% |
| Net | Expansion | 3.93% | 3.87% | 4.87% | 2.77% |
|  | Ratio | 3.93% | 3.61% | 5.05% | 2.30% |
|  | Regression | 3.93% | 3.80% | 5.06% | 2.29% |
|  | Bootstrap simulation (fixed rates) | 3.93% | 3.93% | 4.03% | 3.84% |

**How often the 95% interval contains the truth** (out of 25 audit years; in parentheses, intervals entirely above / entirely below the truth). A valid interval contains it in about 24 of 25.

| Measure | Expansion | Ratio | Regression | Bootstrap simulation (fixed rates) |
|---|---|---|---|---|
| Overpayments | 20/25 (0/5) | 21/25 (0/4) | 20/25 (1/4) | 9/25 (8/8) |
| Underpayments | 0/25 (0/25) | 14/25 (0/11) | 15/25 (0/10) | 15/25 (7/3) |
| Gross | 20/25 (0/5) | 21/25 (0/4) | 20/25 (1/4) | 9/25 (8/8) |
| Net | 20/25 (0/5) | 22/25 (0/3) | 20/25 (1/4) | 9/25 (8/8) |

From [`shared/results/report/by_scenario.csv`](../shared/results/report/by_scenario.csv).
