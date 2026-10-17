# Part D IPM

Claim (PDE) errors that flow through the post-IRA benefit to Medicare reinsurance and low-income cost-sharing payments. Four measures: **overpayments**, **underpayments**, **gross** (over + under) and **net** (over − under). Each beneficiary's payment error (reinsurance + LICS) is netted first; totals are divided by all reported Part D payments (direct subsidy + reinsurance + LICS, $105.56B). Dollars are national (× 500).

## errors/ — build the population, then apply fake errors

Run: `ipsim part-d-ipm/errors/config.yaml` → `errors/output/base/` (about 45 s)

| Step | File | What it does |
|---|---|---|
| Population | `01_population.sql` | 108,000 beneficiaries (1 = 500 real), ~4.5M PDEs; GDC = ingredient cost + dispensing fee + sales tax + vaccine admin fee. 4% of beneficiaries are in long-term care (LTC) and fill about twice as many PDEs (illustrative) |
| Errors | `02_candidate_errors.sql` | One candidate error per PDE, as a share e of GDC: 90% full errors (e = 100%, GDC → 0), 10% partial errors with e uniform on [−100%, 100%) (e < 0 is an underpayment; −100% means the correct GDC is double) |
| Errors | `03_init_calibration.sql` | Starts with no active errors |
| Errors | `04_apply_errors.sql` | Activates each candidate with probability m, or 10m for LTC claims |
| Errors | `05_benefit.sql` | CY 2025 standard benefit ($590 deductible, $2,000 out-of-pocket cap, Manufacturer Discount Program, 20%/40% reinsurance, LIS copays), run on submitted and corrected PDEs |
| Errors | `06_calibrate.sql` | Sets m to hit gross $4.22B: one linear pass, one proportional refinement (steps 04–06 run three times; see `config.yaml`) |
| Truth | `07_population_truth.sql` | x = direct subsidy + reinsurance + LICS; y = Medicare(submitted) − Medicare(corrected) |
| Checks | `08_checks.sql` | FY 2025 targets: gross 4.00% (calibrated), over $3.70B and under $0.52B (reported: with 90% full errors, underpayments cannot reach 14% of overpayments), full/partial shares; unique ids |

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
