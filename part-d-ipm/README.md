# Part D IPM

Claim (PDE) errors that flow through the post-IRA benefit to Medicare reinsurance and low-income cost-sharing payments. Estimand: the national **gross improper payment rate**, Σ|y| / Σx over beneficiaries.

## errors/ — build the population, then apply fake errors

Run: `ipsim part-d-ipm/errors/config.yaml` → `errors/output/base/` (about 45 s)

| Step | File | What it does |
|---|---|---|
| Population | `01_population.sql` | 108,000 beneficiaries (1 = 500 real), ~4.3M PDEs; GDC = ingredient cost + dispensing fee + sales tax + vaccine admin fee |
| Errors | `02_candidate_errors.sql` | One candidate error per PDE: missing documentation 75.00% (GDC → 0), pricing 17.86%, drug discrepancy 7.14% |
| Errors | `03_init_calibration.sql` | Starts with no active errors |
| Errors | `04_apply_errors.sql` | Activates each candidate with probability m |
| Errors | `05_benefit.sql` | CY 2025 standard benefit ($590 deductible, $2,000 out-of-pocket cap, Manufacturer Discount Program, 20%/40% reinsurance, LIS copays), run on submitted and corrected PDEs |
| Errors | `06_calibrate.sql` | Sets m to hit gross $4.22B: one linear pass, one proportional refinement (steps 04–06 run three times; see `config.yaml`) |
| Truth | `07_population_truth.sql` | x = direct subsidy + reinsurance + LICS; y = Medicare(submitted) − Medicare(corrected) |
| Checks | `08_checks.sql` | FY 2025 targets: gross 4.00%, over $3.70B, under $0.52B, type shares; unique ids |

Outputs: `population.parquet` (one row per beneficiary), `pde_detail.parquet` (every PDE's submitted vs corrected liability by payer), `truth.json`, `checks.json`. The Parquet files are not committed (98 MB); rebuild them and compare hashes with `manifest.json`.

## estimation/ — sample the population and estimate with each method

Run: `ipsim part-d-ipm/estimation/config.yaml` → `estimation/results/base/`

Two audit designs, as in production:

- **Expansion, ratio, regression** (`10_`–`30_*.sql`): simple random sample of 1,500 beneficiaries (random selection since FY 2025; size not public), 200 audit years. Formulas: [`shared/sql/lib/02_estimators.sql`](../shared/sql/lib/02_estimators.sql).
- **Audit-finding bootstrap simulation** (`40_simulation_inputs.sql` + `simulation.py`). Each audit year has two samples, both drawn once in SQL and fixed for all of that year's iterations:
  - **Audit sample:** 5,000 PDEs drawn from all PDEs, independent of beneficiary (`sim_audit_sample`). Each finding is corrected ÷ submitted GDC.
  - **Beneficiary sample:** 108,000 beneficiaries drawn with replacement (`sim_bene_sample`; the population size, standing in for production's random 1 million).

  In each of 1,000 iterations, every PDE of a beneficiary-sample beneficiary takes the finding of a random audit-sample PDE of the same kind (brand or generic); audited PDEs keep their own finding. The CY 2025 benefit is then rerun. The iteration's rate is Σ|y| ÷ Σx over the beneficiary sample; the estimate is the mean over iterations and the interval the 2.5th–97.5th percentiles. Run on the first 25 audit years; results are reported for audit years 1–25.

All methods are scored in `90_score.sql`.
