# Part D IPM

Claim (PDE) errors that flow through the post-IRA benefit to Medicare reinsurance and low-income cost-sharing payments. Four measures: **overpayments**, **underpayments**, **gross** (over + under) and **net** (over − under). Each beneficiary's payment error (reinsurance + LICS) is netted first; totals are divided by all reported Part D payments (direct subsidy + reinsurance + LICS, $105.56B). Dollars are national (× 500).

## errors/ — build the population, then apply fake errors

Run: `ipsim part-d-ipm/errors/config.yaml` → `errors/output/base/` (about 45 s)

| Step | File | What it does |
|---|---|---|
| Population | `01_population.sql` | 108,000 beneficiaries (1 = 500 real), ~4.5M PDEs; GDC = ingredient cost + dispensing fee + sales tax + vaccine admin fee. 4% of beneficiaries are in long-term care (LTC) and fill about twice as many PDEs (illustrative). Brand (15% of PDEs) and specialty (25% of the PDEs of the 3% of beneficiaries who use specialty drugs) are drawn independently, so most specialty PDEs are generic for the benefit (40% reinsurance, no manufacturer discount) |
| Errors | `02_candidate_errors.sql` | One candidate error per PDE, as a share e of GDC: 90% full errors (e = 100%, GDC → 0), 10% partial errors with e uniform on [−100%, 100%) (e < 0 is an underpayment; −100% means the correct GDC is double) |
| Errors | `03_init_calibration.sql` | Error rates used as stated: no calibration |
| Errors | `04_apply_errors.sql` | Activates each candidate with probability 2.5%, or 10% for LTC claims. Within LTC and non-LTC the probability is independent of GDC (and of brand and specialty) when `size_beta` = 0.0 (the reported population). Sensitivity: `--set size_beta=0.5` multiplies the rate by (GDC ÷ mean GDC of the PDE's LTC or non-LTC group)^0.5, capped at 0.95, so incidence rises with claim size; the stated rate then holds for a mean-sized claim |
| Errors | `05_benefit.sql` | CY 2025 standard benefit ($590 deductible, $2,000 out-of-pocket cap, Manufacturer Discount Program, 20%/40% reinsurance, LIS copays), run on submitted and corrected PDEs. The manufacturer discount reduces plan liability only; it does not enter the Medicare payment (reinsurance + LICS) |
| Truth | `07_population_truth.sql` | x = direct subsidy + reinsurance + LICS; y = Medicare(submitted) − Medicare(corrected). The direct subsidy is one constant per beneficiary, set so total payments equal $105.56B (no risk adjustment, DIR or risk corridors). All LIS beneficiaries pay the full-subsidy copays ($4.90 generic / $12.15 brand); the $1.60/$4.80 and $0 LIS tiers are not modeled |
| Checks | `08_checks.sql` | Claim error rates (10% LTC, 2.5% other) and full/partial shares; gross, over and under reported against FY 2025 (4.00%, $3.70B, $0.52B) but not calibrated to them; unique ids |

Outputs: `population.parquet` (one row per beneficiary), `pde_detail.parquet` (every PDE's submitted vs corrected liability by payer), `truth.json`, `checks.json`. The Parquet files are not committed (about 113 MB); rebuild them and compare hashes with `manifest.json`.

## estimation/ — sample the population and estimate with each method

Run: `ipsim part-d-ipm/estimation/config.yaml` → `estimation/results/base/`

Two audits per audit year (25 audit years). Neither is the published FY 2025 Part D IPM design (CMS reports a random beneficiary sample with simulation-based extrapolation and does not publish strata or sizes): the 990 and 5,000 sizes and the PDE strata are illustrative.

- **Beneficiary audit** (`01_frame.sql`): simple random sample of 990 beneficiaries, every PDE reviewed — about 41,000 PDEs, roughly eight times the review volume of the PDE audit. Used by **ratio** (`20_ratio.sql`) and **regression** (`30_regression.sql` + `shared/ipsim/regression.py`): within post-strata (LTC; LIS; other), beneficiary payment error is regressed on Medicare payment, gross drug cost, number of PDEs and whether the beneficiary reached the catastrophic phase; the models predict every beneficiary, the audit residuals are added, and the interval comes from the residuals.
- **PDE audit** (`40_simulation_inputs.sql`): 5,000 PDEs, stratified by claim type: (a) LTC, any cost; (b) non-LTC, lowest decile of GDC; (c) other non-LTC. Neyman allocation, n_h ∝ N_h × S_h (S_h = standard deviation of PDE error dollars; from the population, standing in for prior-year data). Because low-cost PDEs carry almost no error dollars, stratum (b) gets the minimum of about 4 PDEs (724 / 4 / 4,272 in the base population) and usually has no error in it. Used by:
  - **Expansion (plug-in benefit rerun)** (`simulation.py`, `run_expansion`; method `expansion`): each stratum's dollar error rate r_h (audited error dollars ÷ audited GDC) is applied as a uniform haircut to every PDE in that stratum, corrected GDC = GDC × (1 − r_h), and the benefit is rerun for all 108,000 beneficiaries. It does rerun the benefit; its bias comes from the haircut: real errors remove whole PDEs from a few beneficiaries, which moves them across benefit phases, while a 2–3% haircut on every PDE barely does, so its point estimate runs low. Delta-method interval (each stratum's rate moved ±1 SE, one rerun each way); this SE carries only the uncertainty of r_h and understates the method's own sampling SD (its intervals are too narrow, not too wide).
  - **PDE-level expansion and ratio** (`simulation.py`, `run_pde_estimators`; methods `pde_expansion`, `pde_ratio`): the design-based analytic comparator on the same audit. For each audited PDE the marginal Medicare-payment effect y_i = Medicare(all PDEs as submitted) − Medicare(same, only this PDE corrected) is computed with the tested numpy benefit (one rerun of the beneficiary per audited PDE in error). `pde_expansion` is the stratified-SRS Horvitz–Thompson total of y_i with FPC; `pde_ratio` is the ratio to the PDE's submitted GDC times the population GDC total (GDC is the only PDE-level payment proxy known for every PDE; Medicare's payment is defined per beneficiary). Both divide by total payments X and use the variance formulas in `shared/sql/lib/02_estimators.sql` (`ipm_expansion`, `ipm_ratio`) on the table `pde_sample`. For these two methods over, under, gross and net are defined at the PDE level (y_i signed: over = Σ max(y_i, 0), under = Σ max(−y_i, 0), gross = Σ |y_i|, net = Σ y_i); beneficiary netting does not apply. They reproduce the beneficiary-netted truth exactly when no beneficiary has more than one PDE in error, and are scored against that truth like the other methods.
  - **Bootstrap simulation, parametric rates** (`simulation.py`; reported): every non-audited PDE in the full population takes a finding from its own stratum: before each iteration the stratum's audited counts are redrawn, f̃ ~ Binomial(n, f/n) PDEs in error and then g̃ ~ Binomial(f̃, g/f) partial among them (rates p = f̃/n, q = g̃/f̃, with q = 0 when f̃ = 0); a PDE is in error at that rate, and partial sizes come from the stratum's audited partial errors (audited PDEs keep their own). The benefit is rerun; 1,000 iterations; mean and 2.5th–97.5th percentiles. The simulation assumes error incidence is independent of GDC within a stratum, which is true of the population by construction (`size_beta` = 0.0); its advantage over the analytic methods is model-dependent.
  - **Bootstrap simulation, fixed rates** (`--set sim_rates=fixed`; comparison only, `estimation/results_fixed/`): the audited rates in every iteration. Its intervals are far too narrow; see [`manuscripts/`](../manuscripts/).

All methods are scored in `90_score.sql`. The results tables below predate `pde_expansion` and `pde_ratio` and the redraw of f̃; they are regenerated by `start-here/run_all.py`.

## Results (25 audit years)

Each row gives the true value and, over the 25 audit years, the median point estimate and the median upper and lower bounds of the 95% interval. National dollars (× 500); rates are dollars ÷ total payments ($105.6B). The PDE expansion and PDE ratio estimators define over, under, gross and net at the PDE level (no netting within beneficiaries).

**Dollars**

| Measure | Method | True | Estimated | Upper bound | Lower bound |
|---|---|---|---|---|---|
| Overpayments | Expansion | $1.44B | $1.28B | $1.95B | $0.57B |
|  | Ratio | $1.44B | $1.48B | $2.20B | $0.72B |
|  | Regression | $1.44B | $1.51B | $2.17B | $0.85B |
|  | PDE expansion (same audit) | $1.44B | $1.40B | $2.36B | $0.26B |
|  | PDE ratio (same audit) | $1.44B | $1.41B | $2.35B | $0.29B |
|  | Simulation (parametric rates) | $1.44B | $1.44B | $1.68B | $1.21B |
| Underpayments | Expansion | $0.02B | $-0.00B | $0.00B | $-0.00B |
|  | Ratio | $0.02B | $0.01B | $0.03B | $0.00B |
|  | Regression | $0.02B | $0.01B | $0.02B | $0.00B |
|  | PDE expansion (same audit) | $0.02B | $0.01B | $0.02B | $0.00B |
|  | PDE ratio (same audit) | $0.02B | $0.01B | $0.02B | $0.00B |
|  | Simulation (parametric rates) | $0.02B | $0.02B | $0.04B | $0.01B |
| Gross | Expansion | $1.46B | $1.28B | $1.95B | $0.57B |
|  | Ratio | $1.46B | $1.49B | $2.22B | $0.74B |
|  | Regression | $1.46B | $1.52B | $2.19B | $0.89B |
|  | PDE expansion (same audit) | $1.46B | $1.41B | $2.37B | $0.28B |
|  | PDE ratio (same audit) | $1.46B | $1.42B | $2.48B | $0.31B |
|  | Simulation (parametric rates) | $1.46B | $1.46B | $1.70B | $1.23B |
| Net | Expansion | $1.42B | $1.28B | $1.95B | $0.57B |
|  | Ratio | $1.42B | $1.45B | $2.19B | $0.72B |
|  | Regression | $1.42B | $1.49B | $2.15B | $0.84B |
|  | PDE expansion (same audit) | $1.42B | $1.39B | $2.35B | $0.24B |
|  | PDE ratio (same audit) | $1.42B | $1.34B | $2.30B | $0.27B |
|  | Simulation (parametric rates) | $1.42B | $1.41B | $1.65B | $1.18B |

**Rates**

| Measure | Method | True | Estimated | Upper bound | Lower bound |
|---|---|---|---|---|---|
| Overpayments | Expansion | 1.36% | 1.22% | 1.85% | 0.54% |
|  | Ratio | 1.36% | 1.40% | 2.09% | 0.69% |
|  | Regression | 1.36% | 1.43% | 2.06% | 0.80% |
|  | PDE expansion (same audit) | 1.36% | 1.33% | 2.23% | 0.24% |
|  | PDE ratio (same audit) | 1.36% | 1.33% | 2.22% | 0.27% |
|  | Simulation (parametric rates) | 1.36% | 1.37% | 1.59% | 1.15% |
| Underpayments | Expansion | 0.02% | -0.00% | 0.00% | -0.00% |
|  | Ratio | 0.02% | 0.01% | 0.02% | 0.00% |
|  | Regression | 0.02% | 0.01% | 0.02% | 0.00% |
|  | PDE expansion (same audit) | 0.02% | 0.01% | 0.02% | 0.00% |
|  | PDE ratio (same audit) | 0.02% | 0.01% | 0.02% | 0.00% |
|  | Simulation (parametric rates) | 0.02% | 0.02% | 0.04% | 0.01% |
| Gross | Expansion | 1.38% | 1.22% | 1.85% | 0.54% |
|  | Ratio | 1.38% | 1.41% | 2.10% | 0.70% |
|  | Regression | 1.38% | 1.44% | 2.07% | 0.84% |
|  | PDE expansion (same audit) | 1.38% | 1.33% | 2.24% | 0.26% |
|  | PDE ratio (same audit) | 1.38% | 1.34% | 2.35% | 0.29% |
|  | Simulation (parametric rates) | 1.38% | 1.38% | 1.61% | 1.16% |
| Net | Expansion | 1.34% | 1.22% | 1.85% | 0.54% |
|  | Ratio | 1.34% | 1.37% | 2.07% | 0.68% |
|  | Regression | 1.34% | 1.41% | 2.03% | 0.80% |
|  | PDE expansion (same audit) | 1.34% | 1.32% | 2.23% | 0.22% |
|  | PDE ratio (same audit) | 1.34% | 1.27% | 2.18% | 0.25% |
|  | Simulation (parametric rates) | 1.34% | 1.34% | 1.57% | 1.11% |

**How often the 95% interval contains the truth** (out of 25 audit years; in parentheses, intervals entirely above / entirely below the truth). A valid interval contains it in about 24 of 25.

| Measure | Expansion | Ratio | Regression | PDE expansion (same audit) | PDE ratio (same audit) | Simulation (parametric rates) |
|---|---|---|---|---|---|---|
| Overpayments | 18/25 (0/7) | 18/25 (1/6) | 16/25 (4/5) | 16/25 (0/9) | 17/25 (0/8) | 24/25 (0/1) |
| Underpayments | 0/25 (0/25) | 15/25 (0/10) | 13/25 (2/10) | 15/25 (0/10) | 15/25 (0/10) | 20/25 (4/1) |
| Gross | 18/25 (0/7) | 18/25 (1/6) | 15/25 (4/6) | 16/25 (0/9) | 17/25 (0/8) | 25/25 (0/0) |
| Net | 19/25 (0/6) | 19/25 (1/5) | 16/25 (4/5) | 16/25 (0/9) | 17/25 (0/8) | 23/25 (0/2) |

From [`shared/results/report/by_scenario.csv`](../shared/results/report/by_scenario.csv) (`python shared/build_readmes.py` regenerates this section).
