# Data dictionary

Columns shared by every `population.parquet`:

| Column | Type | Meaning |
|---|---|---|
| `unit_id` | BIGINT | Sampling unit id (claim, enrollee, beneficiary, payment, application) |
| `stratum` | VARCHAR | Production design stratum (see `design.yaml`) |
| `x` | DECIMAL(18,2) | Amount paid for the unit (USD) |
| `y` | DECIMAL(18,2) | True improper amount; positive = overpayment, negative = underpayment |
| `error_type` | VARCHAR | Mechanism that produced `y`; `none` if `y = 0` |
| `w_pop` | DOUBLE | Real units represented by one synthetic unit (scale weight) |

## ffs_stress (`<shape>_<model>_p<rate>`)

Shared columns only. Shapes: `right` (N = 59,804), `two_spike` (N = 249), `left` (N = 570). Exactly round(p·N) units are in error.

## partc / radv (`population.parquet`)

| Column | Meaning |
|---|---|
| `contract_id` | MA contract |
| `months` | Enrollee-months in the payment year |
| `county_rate` | Monthly county rate (USD) |
| `demo_score` | Demographic part of the risk score |
| `n_hcc` | Payment HCCs submitted (after hierarchy) |
| `risk_orig` | Submitted risk score R0 |
| `risk_radv` | Risk score supported by the record |
| `delta_r` | R0 − R_radv (3 decimals; discrete steps) |
| `x` | R0 × county_rate × months |
| `y` | delta_r × county_rate × months |

RADV only:

| Column | Meaning |
|---|---|
| `pred_score` | Prediction-model probability that ΔR > 0 |
| `eligible` | Enrollee has ≥ 1 HCC |
| `in_frame` | Enrollee is in the top quartile of eligible enrollees by `pred_score` within the contract |

Part C strata: `low` / `medium` / `high` terciles of `risk_orig`. RADV strata: `stratum = contract_id`.

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

`frames.parquet` (RADV) has one row per audited contract: `frame_n` and `sample_n`. `contracts.parquet` gives each contract's enrollment, coding `intensity` and base county rate.

## partd

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

## perm

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

## eipm

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

## truth.json

- `overall`: population totals and rates.
- `by.<level>.<key>`: the same quantities by stratum, state, contract or error type.
- `by.calibration`: the multipliers and calibration passes.

Dollar truths are national-scale, i.e. multiplied by `w_pop`.
