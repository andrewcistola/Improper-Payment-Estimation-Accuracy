## Appendix A. Data process

Every number in this study comes from synthetic populations built from stated probability distributions. No protected health information, no unit-level data from any source and no non-public CMS material (contractor methodology plans, internal error data) were used. Populations are calibrated only to public aggregate results: FY 2025 HHS Agency Financial Report figures and the program-specific CMS result pages cited in Appendix B.

### A.1 Pipeline

Each program folder has two stages, run by one YAML-driven runner (`ipsim`):

1. **`errors/`** builds an error-free population, applies fabricated errors, records the truth and checks it against public figures.
   - Population. Units with their payment amounts and the fields each payment function needs: risk scores and HCCs, PDEs and benefit phases, APTC inputs, claims.
   - Errors. Each unit's candidate error is drawn first, then turned on with a stated probability. Where a public aggregate is used as a target, the probability comes from one closed-form multiplier: the target dollars divided by the expected dollars of the candidates. No iterative tuning is used.
   - Truth. The true improper amount *y* and payment *x* for every unit, and the true over, under, gross and net totals.
   - Checks. Each population is compared with the public aggregates it is calibrated to. Results are written to `checks.json`.
2. **`estimation/`** draws the audits and estimates with each method.
   - Frame and design. Strata, the allocation (Neyman where stated), and the sample size.
   - Audits. 25 independent production audits ("audit years").
   - Estimators. Expansion, ratio and regression (generalized regression with an intercept and payment as auxiliary), with normal 95% intervals from Taylor linearization. These are written once in `shared/sql/lib/02_estimators.sql` and tested against an independent numpy implementation.
   - Bootstrap simulation. Fixed and parametric rates, 1,000 iterations per audit year, run by the shared loop in `shared/ipsim/simulation.py` with each program's kernel.
   - Scoring against the truth.

`shared/report.yaml` joins every estimate to the truth (`shared/results/report/by_scenario.csv`, `by_audit_year.parquet`). `manuscripts/scripts/build_tables.py` produces every table and figure in this manuscript from the parametric-rate results (`<program>/estimation/results/`, the configs' default) and the fixed-rate results from the same audits (`<program>/estimation/results_fixed/`).

### A.2 Reproducibility

- **Random numbers.** In SQL, every random draw is a hash of `(seed, stream, key)`. In the bootstrap simulation, draws come from PCG64 generators seeded by `SeedSequence([scenario seed, audit year])`.
- **Exact arithmetic.** Money is stored as `DECIMAL`, and floating-point sums run in a fixed order.
- **Identical reruns.** Reruns give byte-identical files at any thread count. This is tested in `shared/tests/test_determinism.py`, and `manifest.json` records a SHA-256 hash for every output.
- **Payment functions.** Each program's numpy payment function is tested to reproduce the SQL improper amount to the cent for every unit when given that unit's own audit finding. A census audit is also tested: when every unit is audited, both bootstrap versions must return the exact true rates (`shared/tests/test_simulation.py`).

### A.3 Scale

Each synthetic unit stands for *w* real units:

| Program | *w* |
|---|---|
| Part C | 100 |
| Part D | 500 |
| PERM | 200 |
| EIPM | 100 |
| CERT | 200 |

Rates are scale-free. Dollars are reported at national scale: rate × synthetic payments × *w*.

### A.4 Estimands and netting

- **Netting.** Errors are netted within the payment unit first: the enrollee (Part C), the beneficiary (Part D), the payment (PERM), the application (EIPM) and the claim (CERT).
- **Measures.**
  - Over = Σ max(*y*, 0)
  - Under = Σ max(−*y*, 0)
  - Gross = over + under
  - Net = over − under
- **Rates.** Each total is estimated in dollars with its interval first, then divided by the known total payments *X*.
- **Overpayment-only programs.** PERM and EIPM have only overpayments, so gross = over = net. Their components are reported instead: eligibility and claims for PERM, technically improper and monetary for EIPM.
- **Analytic estimators.** These estimate the rate directly as *T̂_y / X* (expansion), *T̂_y / T̂_x* (ratio) or *[T̂_y + b(X − T̂_x)] / X* (regression), using stratified-SRS variance formulas with finite population correction.

### A.5 Bootstrap simulation, step by step

For one audit year and one iteration:

1. **Rates from the audit.** Within each donor kind (the stratum, or the HCC for Part C), from the *n* audited units:
   - *f* = how many are in error;
   - *g* = how many of those errors are partial;
   - the list of audited partial sizes (taints, income ratios or HCC losses).
2. **Parametric rates only.** Redraw *p* = Binomial(*n*, *f/n*)/*n* and *q* = Binomial(*f*, *g/f*)/*f*.
3. **Assign errors.** Every non-audited unit gets an error with probability *p*, drawn as a Bernoulli process over the unit list.
4. **Partial or whole.** Each error is partial with probability *q*, and its size is drawn uniformly from the audited partial list. Otherwise it is a whole error: the full payment, or the full HCC coefficient.
5. **Audited units** keep their own findings.
6. **Rerun the payment function** for every unit: the risk score × county rate, the Part D benefit, APTC, or claim × taint. Net per unit, then sum to over, under, gross and net, and divide by *X*.

The estimate is the mean of the 1,000 iteration rates. The interval runs from the 2.5th to the 97.5th percentile of those rates.

## Appendix B. Program designs and assumptions

Values marked *illustrative* are not published by CMS. They are set to plausible levels and labeled as such in the configs.

### B.1 Medicare Part C (Medicare Advantage risk adjustment)

**Population** (330,253 enrollees × 100):

- 550 contracts with lognormal enrollment and a coding-intensity factor.
- HCCs from 10 illustrative families, each with a mild and a severe level.
- Payment = risk score × county rate × months, scaled to $388.72B of payments subject to risk adjustment.

**Errors:**

- HCCs not supported by the record: deleted, or moved down the hierarchy (severe to mild).
- Missing documentation: every coded HCC is lost.
- HCCs supported by the record but not coded: underpayments.
- Calibrated to the FY 2025 Part C results: gross 6.09%, overpayments $21.43B, underpayments $2.23B, missing documentation 0.22%.
- The simulated truth is gross 6.06% ($23.57B).

**Audit:** 990 enrollees, 330 per national tercile of the submitted risk score (stratified SRS). The real Part C IPM sample size and strata are not public. The terciles follow the 2012 RADV design.

**Estimators:**

- Expansion works in risk-score units: within each tercile, the mean over and under risk-score error × the tercile's size × the national mean county rate × months.
- Ratio and regression use the enrollee payment.

**Bootstrap simulation:**

- One failure rate per HCC (20). A failed audited instance is one that was deleted, moved, or on a record with missing documentation, and it loses its HCC's mean audited loss.
- One addition rate per family (10).
- An HCC with no audited instance never fails. Rates are not extrapolated to unaudited HCCs.

### B.2 Medicare Part D (prescription drug event errors)

**Population** (108,000 beneficiaries × 500; about 4.5 million PDEs):

- Gross drug cost (GDC) = ingredient cost + dispensing fee + sales tax + vaccine administration fee.
- 4% of beneficiaries are in long-term care (LTC) and fill about twice as many PDEs (illustrative).
- The CY 2025 post-IRA standard benefit is run on submitted and corrected PDEs:
  - $590 deductible and $2,000 out-of-pocket cap;
  - Manufacturer Discount Program;
  - 20% and 40% reinsurance;
  - low-income subsidy copays.
- Payments are direct subsidy + reinsurance + LICS, $105.56B in all.

**Errors:**

- One candidate per PDE. 90% are full errors (GDC → 0) and 10% are partial, with the error share uniform on [−100%, 100%).
- Error probability is 10% for LTC PDEs and 2.5% for other PDEs (illustrative).
- No calibration: the truth is 1.38% gross ($1.46B).
- The FY 2025 Part D result was 4.00%, so this population tests the method at a lower error rate than production.

**Audits:**

- PDE audit of 5,000, in three strata: LTC; non-LTC in the lowest decile of GDC; other non-LTC. Neyman allocation.
  - Used by expansion and by the bootstrap simulation.
  - Expansion applies each stratum's audited error rate to every PDE in the stratum and reruns the benefit. Its interval is a delta-method interval: each stratum rate is moved ±1 SE and the benefit rerun each way.
- Beneficiary audit: an SRS of 990 beneficiaries with every PDE reviewed. Used by ratio and regression.

The two audits differ, so the comparison between methods is between designs as well as estimators.

### B.3 Medicaid PERM (fee-for-service and managed care, claims and eligibility)

**Population** (9 states, 3.09 million payments × 200; 264,565 beneficiaries):

- FFS claims and monthly managed-care capitations.
- Rates are measured at federal share, Σ*y*·FMAP / Σ*x*·FMAP, with $142.0B in federal payments.

**Errors:**

- Claims-review errors: FFS 6.5% of payments (70% all-or-nothing, 30% partial); MC 0.3%.
- Eligibility errors, set beneficiary by beneficiary. Each state's true rate is set on a grid from 2.00% to 4.00%.
- Gross = the whole payment if eligibility is in error, otherwise the claims error.
- Calibrated to the Medicaid FY 2025 rate of 6.12%; the simulated truth is 6.09%.

**Audit:**

- Strata within each state: payment type (FFS, MC) × five equal-count payment quintiles (10 strata).
- Neyman allocation of 520 payments per state-year, with systematic selection after sorting by amount within stratum.
- National pooling:
  - Analytic methods add the state dollar totals and variances.
  - The bootstrap simulation sums the states' iteration totals iteration by iteration.

**Bootstrap simulation:**

- Claims findings are matched within the payment stratum.
- The eligibility error rate is taken from the audited beneficiaries of the state.

### B.4 Marketplace APTC (EIPM, Federally-facilitated Exchange)

**Population** (142,152 applications × 100):

- Households with income, size, age and benchmark premium.
- APTC under the enhanced applicable-percentage schedule for 2021–2025.
- APTC recipients only.

**Errors:**

- FY 2023–2025 public results report no underpayments, so every error is an overpayment.
- *Technical* errors: a required data match was not run, so the whole APTC is improper. 48% of improper dollars, matching FY 2025 (0.43 of 0.89 points).
- *Monetary* errors: the supported income is higher than the income used, by a lognormal factor, and APTC is recomputed. 52% of improper dollars.
- The simulated truth is 0.92% gross, including technical 0.43%.

**Audit:**

- Stratified SRS of 2,000 applications, matching CMS's "approximately 2,000".
- Strata are five equal-count quintiles of annual APTC (illustrative; the EIPM strata are not public), with Neyman allocation.

**Bootstrap simulation:**

- Within each quintile, an error is technical or monetary at the audited shares.
- A monetary error transfers the donor's ratio of supported to used income, and APTC is recomputed for the recipient, clipped to 100–600% FPL.

### B.5 Medicare fee-for-service (CERT)

**Population** (5.34 million claims × 200), in four claim types:

| Claim type | Synthetic claims | FY 2025 payments |
|---|---|---|
| Part A hospital IPPS | 40,000 | $118.5B |
| Part A excluding IPPS | 900,000 | $197.9B |
| Part B | 4,000,000 | $114.1B |
| DMEPOS | 400,000 | $9.4B |

- Amounts are lognormal within type (illustrative spread), scaled to FY 2025 payments ($439.9B in all).
- MAC jurisdictions are not modeled.

**Errors:**

- At most one error per claim.
- Whole-claim overpayments: no or insufficient documentation, medical necessity, other. These are 92% of overpayment dollars.
- Partial coding overpayments: 8% of overpayment dollars, sized 5–60% of the payment.
- Coding underpayments: 5–50% of the payment.
- Per-type rates are closed form, from FY 2025 overpayment and underpayment dollars (Supplemental Improper Payment Data, Tables A1 and A4).
- The simulated truth is 6.50% gross (FY 2025: 6.55%), with $0.92B in underpayments (FY 2025: $1.0B).

**Audit:**

- 37,651 claims, the FY 2025 count of claims reviewed per claim type: IPPS 8,750; Part A excluding IPPS 8,651; Part B 11,600; DMEPOS 8,650.
- Neyman allocation across five equal-count payment quintiles within each type. These stand in for CERT's roughly 100 service-level strata per type, which cannot be rebuilt from public data.
- The production estimator reduces nationally to a separate ratio estimator.
- The Part A-to-B rebilling adjustment is out of scope.

### B.6 Assumptions common to all programs

1. **Review is perfect.** The audit finding equals the truth. There are no reviewer errors and no appeals.
2. **One audit per year.** Each audit year has one audit, and every method gets only that audit.
3. **Errors are independent of selection.** Within a stratum, error probability does not depend on whether a unit is sampled. In PERM, CERT and EIPM it also does not depend on payment size, except through the strata definitions.
4. **Neyman inputs.** Allocations use the population's stratum standard deviations, standing in for prior-year data, which production designs have but this study does not.
5. **Gross is the reported rate.** PIIA gross rates are the primary estimand. Recovery, contract-level RADV extrapolation and provider demands are out of scope.
6. **Unknown payments count as improper,** following CMS practice (for example, missing documentation in Part C).

## Appendix C. Additional results

{{TABLEC1}}

Results for every program, measure, method and audit year, including overpayments, underpayments and net in dollars, are in `shared/results/report/by_scenario.csv` and `by_audit_year.parquet` (analytic methods and parametric rates), and in `manuscripts/generated/results_long.csv` (all five methods, including fixed rates). Each program's README reports the analytic methods and the parametric-rate bootstrap.
