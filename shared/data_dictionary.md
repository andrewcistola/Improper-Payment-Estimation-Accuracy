# Data dictionary

## errors/ outputs

Columns shared by every `population.parquet`:

| Column | Type | Meaning |
|---|---|---|
| `unit_id` | BIGINT | Sampling unit id (claim, enrollee, beneficiary, payment, application) |
| `stratum` | VARCHAR | Production design stratum (see `design.yaml`) |
| `x` | DECIMAL(18,2) | Amount paid for the unit (USD) |
| `y` | DECIMAL(18,2) | True improper amount; positive = overpayment, negative = underpayment |
| `error_type` | VARCHAR | Mechanism that produced `y`; `none` if `y = 0` |
| `w_pop` | DOUBLE | Real units represented by one synthetic unit (scale weight) |

### cert (`perm-cert/errors/output/cert/<shape>_<model>_p<rate>`)

Shared columns only. Shapes: `right` (N = 59,804), `two_spike` (N = 249), `left` (N = 570). Exactly round(p·N) units are in error.

### part-c-ipm (`part-c-ipm/errors/output/base`)

`population.parquet` has one row per enrollee:

| Column | Meaning |
|---|---|
| `contract_id` | MA contract |
| `months` | Enrollee-months in the payment year |
| `county_rate` | Monthly county rate (USD) |
| `demo_score` | Demographic part of the risk score |
| `n_hcc` | Payment HCCs submitted (after hierarchy) |
| `risk_orig` | Submitted risk score R0 |
| `risk_validated` | Risk score supported by the medical record |
| `delta_r` | R0 − risk_validated (3 decimals; discrete steps) |
| `x` | R0 × county_rate × months |
| `y` | delta_r × county_rate × months |

Strata: `low` / `medium` / `high` terciles of `risk_orig`.

`hcc_detail.parquet` has one row per enrollee × HCC family:

| Column | Meaning |
|---|---|
| `fam` | HCC family |
| `severe` | Severe level coded |
| `chart_review` | HCC sourced from chart review |
| `coef_*` | Family coefficients |
| `p_unsupported` | Probability the HCC is unsupported |
| `validation` | `supported`, `deleted` or `hierarchy_move` |
| `err_coef` | Risk-score error from this HCC |

`contracts.parquet` gives each contract's enrollment, coding `intensity` and base county rate.

### part-d-ipm (`part-d-ipm/errors/output/base`)

`population.parquet` has one row per beneficiary:

| Column | Meaning |
|---|---|
| `lis` | Low-income subsidy enrollee |
| `n_pde` | Number of PDEs |
| `gdc_sub` / `gdc_cor` | Annual gross drug cost, submitted / corrected |
| `reins_sub` | Medicare reinsurance on the submitted PDEs |
| `lics_sub` | Low-income cost-sharing subsidy on the submitted PDEs |
| `reached_catastrophic` | Submitted spending reached the catastrophic phase |
| `n_err_pde` | Number of PDEs in error |
| `direct_subsidy` | Prospective Medicare payment; constant, never in error |
| `x` | direct_subsidy + reinsurance + LICS |
| `y` | Medicare(submitted) − Medicare(corrected) |

`pde_detail.parquet` has one row per PDE:

| Column | Meaning |
|---|---|
| `ingredient_cost`, `dispensing_fee`, `sales_tax`, `vaccine_admin_fee` | GDC components |
| `gdc_submitted` / `gdc_corrected` | GDC before and after review |
| `cand_type` / `cand_dir` | Candidate error type and direction |
| `active` | Candidate error is active |
| `ded_sub` / `ini_sub` / `cat_sub` | Submitted GDC in the deductible, initial and catastrophic phases |
| `*_sub` / `*_cor` | Liability by payer (reinsurance, LICS, plan, manufacturer), submitted vs corrected |

### perm (`perm-cert/errors/output/perm/state_elig_grid`)

`population.parquet` has one row per payment:

| Column | Meaning |
|---|---|
| `state_id` | State |
| `bene_id` | Beneficiary |
| `payment_type` | `FFS` or `MC` |
| `month` | Month 1–12 of the July–June year |
| `quarter` | Quarter 1–4 |
| `fmap` | Federal share |
| `y_claims` | Claims-review error |
| `y_elig` | Eligibility error (= `x` if the beneficiary is in error) |
| `y` | Overall error = claims + eligibility − overlap |
| `claims_error_type`, `elig_error_type` | Error mechanism for each component |

`stratum` is `<state>_Q<q>_<type>_S<k>`: five equal-dollar strata per state × quarter × type. Rates are computed at federal share: Σ y·fmap / Σ x·fmap.

### eipm (`eipm/errors/output/base`)

`population.parquet` has one row per APTC application:

| Column | Meaning |
|---|---|
| `region` | Region 1–4 |
| `hh_size` | Household size |
| `age` | Age of primary applicant |
| `fpl_pct` | Income as % of the poverty guideline |
| `months` | Months enrolled |
| `benchmark_month` | Benchmark (SLCSP) monthly premium |
| `aptc_month` | Monthly APTC |
| `x` | aptc_month × months |
| `y` | APTC paid − correct APTC |

Strata are income bands: `A_lt150`, `B_150_250`, `C_250_400`, `D_ge400`.

### truth.json

- `overall`: population totals and rates.
- `by.<level>.<key>`: the same quantities by stratum, state or error type.
- `by.calibration`: the multipliers and calibration passes.

Dollar truths are national-scale, i.e. multiplied by `w_pop`.

`checks.json` lists each calibration check: metric, value, target, difference, tolerance and pass/FAIL.

## estimation/ outputs

`estimates.parquet` has one row per audit year × domain × method × interval:

| Column | Meaning |
|---|---|
| `method` | `expansion`, `ratio`, `regression` or `simulation` (the audit-finding bootstrap simulation) |
| `interval` | `normal` (expansion, ratio, regression) or `percentile` (simulation: 2.5th–97.5th percentile of the 1,000 iteration rates) |
| `rep` | Audit year (Monte Carlo replicate) number |
| `domain` | What is estimated: `national` (Part D, EIPM, CERT); `national\|over`, `national\|under`, `national\|gross`, `national\|net` (Part C: overpayments, underpayments, gross = over + under, net = over − under); or `<state>\|<component>` for PERM |
| `estimate` | Estimated improper payment rate (simulation: mean of the 1,000 iteration rates) |
| `se` | Standard error: analytic for expansion, ratio and regression; standard deviation of the 1,000 iteration rates for simulation |
| `lower`, `upper` | Two-sided 95% interval |

`metrics.json` has one record per domain × method × interval:

| Field | Meaning |
|---|---|
| `theta` | True rate in the population |
| `coverage` | Share of samples whose interval contains `theta` (target 0.95) |
| `mc_se_coverage` | Standard error of `coverage` from the number of audit years |
| `above`, `below` | Share of intervals entirely above / below `theta` (target 0.025 each) |
| `n_undefined` | Intervals that could not be formed (counted as not covering) |
| `rel_bias`, `rel_rmse` | Bias and RMSE of the point estimate, relative to `theta` |
| `rel_width` | Mean interval width relative to `theta` |
| `median_rel_width` | Median interval width relative to `theta` (robust to a few very wide intervals) |
| `mean_se`, `empirical_se` | Average reported SE vs the standard deviation of the estimates across samples |

`truth.json` (estimation) gives the frame totals per domain: X (paid), Y (improper) and theta = Y / X.

## shared/results/report/

The report covers audit years 1 to `audit_years` (25, set in `shared/report.yaml`), the same audit years for every method.

`by_audit_year.parquet` (and `by_audit_year.csv` when regenerated) has one row per program × scenario × domain × method × interval × audit year:

| Column | Meaning |
|---|---|
| `true_rate` | Fabricated improper payment rate in the population |
| `audit_year` | Audit year (Monte Carlo replicate) number |
| `estimate`, `lower`, `upper` | Point estimate and 95% CI from this audit year |
| `error`, `rel_error` | Point estimate minus the true rate, and that difference ÷ the true rate |
| `truth_in_ci` | `inside` (CI contains the truth), `above` (whole CI above it), `below`, or `undefined` |
| `total_paid_usd`, `true_improper_usd`, `estimate_usd`, `lower_usd`, `upper_usd` | Total payments and the same values in national dollars: rate × payments × `w_pop`, each program's own factor (Part C 100, Part D 500, EIPM 100, PERM 200, CERT 1) |

`by_scenario.csv` has one row per program × scenario × domain × method × interval:

| Column | Meaning |
|---|---|
| `true_rate`, `true_improper_usd` | The fabricated truth |
| `year1_estimate`, `year1_lower`, `year1_upper`, `year1_truth_in_ci` | Audit year 1 as a worked example |
| `mean_estimate`, `mean_lower`, `mean_upper` | Averages over the reported audit years |
| `mean_estimate_usd`, `mean_lower_usd`, `mean_upper_usd`, `total_paid_usd` | The same averages in national dollars, and total payments |
| `mean_error`, `mean_abs_error` | Average signed error (bias) and average absolute error of the point estimate, in rate units |
| `mean_rel_error`, `mean_abs_rel_error` | The same, relative to the true rate |
| `n_audit_years`, `n_truth_inside`, `n_ci_above_truth`, `n_ci_below_truth`, `n_undefined` | Counts over the reported audit years |
| `pct_truth_inside` | % of reported audit years whose CI contains the truth (equals `coverage` in metrics.json when both cover the same audit years) |
