## Appendix A. Data process

Every number in this study comes from synthetic populations built from stated probability distributions. This study used no protected health information, no unit-level data from any source, and no non-public CMS material (for example, contractor methodology plans or internal error data). Populations are calibrated only to public aggregate results, namely the FY 2025 figures in the CMS improper payments fact sheet and the program-specific CMS result documents cited in Appendix B.

### A.1 Pipeline

Each program folder has two stages, run by one YAML-driven runner (`ipsim`). The `errors/` stage builds an error-free population, applies fabricated errors, records the truth, and checks it against public figures. The candidate error for each unit is drawn first and then turned on with a stated probability; where a public aggregate is used as a target, the probability comes from one closed-form multiplier (the target dollars divided by the expected dollars of the candidates), and no iterative tuning is used. The true improper amount *y* and payment *x* of every unit, and the true over, under, gross, and net totals, are recorded, and each population is compared with the public aggregates it is calibrated to (`checks.json`). The `estimation/` stage draws the audits and estimates with each method: the strata, the allocation (Neyman where stated), and the sample size; 25 independent production audits; the expansion and ratio estimators with normal 95% intervals, written once in `shared/sql/lib/02_estimators.sql` and tested against an independent numpy implementation; the regression estimator (`shared/ipsim/regression.py`, predictors from each program's `30_regression.sql`, tested in `shared/tests/test_regression.py`); the Part D PDE-level estimators (`part-d-ipm/estimation/simulation.py`); the plug-in and parametric simulations, 1,000 iterations per audit year, run by the shared loop in `shared/ipsim/simulation.py` with each program's kernel; and scoring against the truth. The Part C risk-score expansion and the Part D plug-in expansion are program-specific and are not covered by the shared estimator tests.

The file `shared/report.yaml` joins every estimate to the truth (`shared/results/report/by_scenario.csv`, `by_audit_year.parquet`). `manuscripts/scripts/build_tables.py` produces every table and figure in the main text from the parametric-rate results (`<program>/estimation/results/`, the configs' default) and the fixed-rate results from the same audits (`<program>/estimation/results_fixed/`). `robustness/run.py` and `robustness/summarize.py` produce Appendix D.

### A.2 Reproducibility

In SQL, every random draw is a hash of `(seed, stream, key)`. In the simulation, draws come from PCG64 generators seeded by `SeedSequence([scenario seed, audit year])`. Money is stored as `DECIMAL`, and floating-point sums run in a fixed order. Reruns produce byte-identical files at any thread count within one pinned software environment: the simulation's random streams come from numpy and the regression from LAPACK, so `requirements-lock.txt` records the exact package versions used for the published results, and every `manifest.json` records a SHA-256 hash of each output together with the DuckDB, numpy, scipy, numba and BLAS versions. Thread-count invariance is tested for every program's population and for three estimation configs in `shared/tests/test_determinism.py`. Each program's numpy payment function is tested to reproduce the SQL improper amount to the cent for every unit when given that unit's own audit finding, and a census audit is tested: when every unit is audited, both simulation versions must return the exact true rates (`shared/tests/test_simulation.py`). The Part C kernel is additionally tested to be unbiased for over, under, gross, and net at the production audit size.

### A.3 Scale

Each synthetic unit stands for *w* real units: 100 in Part C, 500 in Part D, 200 in PERM, 100 in EIPM, and 200 in CERT. Rates are scale-free. Dollars are reported at national scale as rate × synthetic payments × *w*.

### A.4 Estimands and netting

Errors are first netted within the payment unit (the enrollee for Part C, the beneficiary for Part D, the payment for PERM, the application for EIPM, and the claim for CERT). Over = Σ max(*y*, 0), under = Σ max(−*y*, 0), gross = over + under, and net = over − under. Each total is estimated in dollars with its interval and then divided by the known total payments *X*. PERM and EIPM have only overpayments, so gross = over = net and their components are reported instead. The Part D PDE-level estimators define the measures at the PDE level (Section 2.4).

### A.5 Simulation, step by step

For one audit year and one iteration: (1) within each donor kind (the stratum, or the HCC for Part C), from the *n* audited units, *f* is how many are in error, *g* how many of those errors are partial, and the audited partial sizes (taints, income ratios) or mean HCC losses are listed; (2) parametric rates only: redraw *f̃* = Binomial(*n*, *f/n*) and *g̃* = Binomial(*f̃*, *g/f*), and set *p* = *f̃/n*, *q* = *g̃/f̃*; (3) every non-audited unit gets an error with probability *p*, drawn as a Bernoulli process over the unit list; (4) each error is partial with probability *q* and its size is drawn uniformly from the audited partial list, otherwise it is a whole error; in Part C a failed HCC loses that HCC's mean audited loss, and additions are applied only to enrollees with no failure in the iteration; (5) audited units keep their own findings; (6) the payment function is rerun for every unit, errors are netted per unit, summed to over, under, gross, and net, and divided by *X*. All four measures share one audit. The estimate is the mean of the 1,000 iteration rates, and the interval runs from the 2.5th to the 97.5th percentile (linear interpolation). The fixed and parametric runs share the scenario seed, so they use identical audits.

## Appendix B. Program designs and assumptions

Values marked *illustrative* are not published by CMS. These values are set to plausible levels and labeled as such in the configs. The population and error parameters below are stated in each program's `errors/config.yaml` and the headers of its SQL files.

### B.1 Medicare Part C (Medicare Advantage risk adjustment)

*Population* (330,253 enrollees × 100): 550 contracts with lognormal enrollment and a contract coding-intensity factor, lognormal(−0.08, 0.40), that multiplies every HCC's failure probability; HCCs from 10 illustrative families, each with a mild and a severe level, 35% of draws severe and 15% chart-review sourced; payment = risk score × county rate × months, scaled to $388.72B of payments subject to risk adjustment; 85% of enrollees full-year, the rest uniform over 1–11 months; demographic score 0.35 + 0.30 × Kumaraswamy(2, 3).

*Errors:* HCCs not supported by the record are deleted, or, for half of the unsupported severe HCCs, moved down the hierarchy to the mild level; chart-review HCCs have three times the failure probability; missing documentation (probability 0.003 × the coding-intensity multiplier, enrollees with at least one HCC) loses every coded HCC; HCCs supported by the record but not coded (underpayments) are added only to enrollees with no overpayment and no missing documentation; all probabilities are capped at 0.95. Calibrated to the FY 2025 Part C results (gross 6.09%, overpayments $21.43B, underpayments $2.23B, missing documentation 0.22%); the simulated truth is gross 6.06% ($23.57B).

*Audit:* 990 enrollees, 330 per national tercile of the submitted risk score (stratified SRS). The actual Part C IPM sample size and strata are not public, so the terciles follow the 2012 RADV design (illustrative).

*Estimators:* expansion works in risk-score units, within each tercile the mean over and under risk-score error × the tercile's size × one national mean of county rate × months over all enrollees; ratio uses the enrollee payment; regression uses payment, demographic score, months enrolled, and number of HCCs within each tercile. The simulation uses one failure rate per HCC (20) and one addition rate per family (10); a failed audited instance is one that was deleted, moved, or on a record with missing documentation, and it loses its HCC's mean audited loss; the addition rate's denominator is audited enrollees lacking the family with no overpayment finding; an HCC with no audited instance never fails; the 30 rates are redrawn independently in the parametric version, although the coding-intensity factor and missing documentation correlate them within an audit.

### B.2 Medicare Part D (prescription drug event errors)

*Population* (108,000 beneficiaries × 500; about 4.5 million PDEs): gross drug cost (GDC) = ingredient cost + dispensing fee + sales tax + vaccine administration fee; PDE counts lognormal(3.3, 0.9) over one plan year with no mid-year enrollment; 4% of beneficiaries in long-term care (LTC) fill about twice as many PDEs (illustrative); 25% receive the low-income subsidy (LIS); 15% of PDEs are brand and 3% of beneficiaries have specialty drugs, drawn independently, so most high-cost specialty PDEs are treated as generic for benefit purposes. The CY 2025 post-IRA standard benefit is run on submitted and corrected PDEs: $590 deductible, 25% initial coinsurance, $2,000 out-of-pocket cap, manufacturer discount program (10% initial, 20% catastrophic, affecting plan liability only and never Medicare's payment), reinsurance of 20% (applicable drugs) and 40% (non-applicable) in the catastrophic phase, and LIS copays of $4.90/$12.15 for every LIS enrollee (the $1.60/$4.80 and $0 tiers are not modeled). Payments are a constant direct subsidy per beneficiary (no risk adjustment, DIR or risk corridors) plus reinsurance plus low-income cost sharing, $105.56B in all.

*Errors:* one candidate per PDE; 90% are full errors (GDC → 0) and 10% are partial, with the error share uniform on [−100%, 100%); the activation probability is 10% for LTC PDEs and 2.5% for other PDEs (illustrative) and does not depend on GDC, brand or specialty. This population is not calibrated; the truth is 1.38% gross ($1.46B), below the FY 2025 result of 4.00%, with underpayments of $0.02B (FY 2025: $0.52B), so underpayments are structurally sparser than in production.

*Audits* (both illustrative; CMS publishes neither): a PDE audit of 5,000 in three strata (LTC; non-LTC in the lowest decile of GDC; other non-LTC) with Neyman allocation, used by the plug-in expansion, the PDE expansion and PDE ratio, and the simulation; the lowest-decile stratum receives about 4 PDEs under Neyman, so its audited rate is usually zero. A beneficiary audit, an SRS of 990 beneficiaries with every PDE reviewed (about 41,000 PDEs), used by ratio and regression. The beneficiary audit therefore reviews about eight times as many PDEs as the PDE audit.

### B.3 Medicaid PERM (fee-for-service and managed care, claims and eligibility)

*Population* (9 states, 3.09 million payments × 200; 264,565 beneficiaries): FFS claims and monthly managed-care capitations (380 × lognormal(0, 0.45)); one FMAP per state; no denied or zero-paid claims. Rates are measured at federal share, Σ*y*·FMAP / Σ*x*·FMAP, with $142.0B in federal payments.

*Errors:* claims-review errors on 6.5% of FFS payments (70% all-or-nothing, 30% partial with taint Kumaraswamy(2, 2)) and 0.3% of MC payments, independent of payment size within stratum; eligibility errors set beneficiary by beneficiary as a whole-year attribute, with each state's true rate on a grid from 2.00% to 4.00%; gross is the whole payment if the beneficiary is ineligible, otherwise the claims error. Calibrated to the Medicaid FY 2025 rate of 6.12%; the simulated truth is 6.09%. Real PERM measures 17 states per cycle on a three-year rotation with state-specific, precision-driven sample sizes and claim-level FMAP; this population stands in for one cycle.

*Audit:* within each state, payment type (FFS, MC) × five equal-count payment quintiles (10 strata); Neyman allocation of 520 payments per state-year with systematic selection after sorting by amount within stratum; the variance formula treats the systematic sample as a stratified SRS (conservative). National pooling adds the state dollar totals and variances for the analytic methods and sums the states' iteration totals iteration by iteration for the simulation. Within-beneficiary clustering of payments is ignored (a few same-beneficiary pairs per 520-payment sample).

*Simulation:* claims findings are matched within the payment stratum. The eligibility error rate is taken from the audited beneficiaries of the state, who are selected in proportion to their number of payments, and an audited beneficiary's whole-year eligibility status is applied to all of that beneficiary's payments; this is consistent with the population but differs from real PERM, which determines eligibility as of the sampled payment's month.

### B.4 Marketplace APTC (EIPM, Federally-facilitated Exchange)

*Population* (142,152 applications × 100): households with income (100% + lognormal(4.6, 0.75) percent of FPL, capped at 600%), size (1 + ⌊4u^1.6⌋), age (21–64, uniform), and an age-rated benchmark premium; 75% full-year; APTC under the enhanced applicable-percentage schedule for 2021–2025 (8.5% above the top band); APTC recipients only.

*Errors:* because the FY 2023–2025 public results report no underpayments, every error is an overpayment. Technical errors (a required data match was not run, so the whole APTC is improper) are 48% of improper dollars, matching FY 2025 (0.43 of 0.89 points). Monetary errors raise the supported income by a factor max(*r*, 1/*r*) with *r* ~ lognormal(0, 0.35), capped at 600% FPL, and APTC is recomputed; a candidate whose recomputed APTC is not lower than the APTC paid is not an error. Both are independent of APTC within stratum. The simulated truth is 0.92% gross, including technical 0.43%.

*Audit:* stratified SRS of 2,000 applications, matching CMS's "approximately 2,000"; strata are five equal-count quintiles of annual APTC (illustrative) with Neyman allocation from the population gross *y* (largest-remainder rounding, minimum two per stratum).

*Simulation:* within each quintile, an error is technical or monetary at the audited shares; a monetary error transfers the donor's ratio of supported to used income, and APTC is recomputed for the recipient, clipped to 100–600% FPL.

### B.5 Medicare fee-for-service (CERT)

*Population* (5.34 million claims × 200) in four claim types: Part A hospital IPPS (40,000 synthetic claims; $118.5B), Part A excluding IPPS (900,000; $197.9B), Part B (4,000,000; $114.1B), and DMEPOS (400,000; $9.4B). Amounts are lognormal within type (illustrative spread), scaled to FY 2025 payments ($439.9B in all). MAC jurisdictions and denied claims are not modeled.

*Errors:* at most one error per claim, with probability independent of claim size and of stratum within type. Whole-claim overpayments (no or insufficient documentation, medical necessity, other) are 92% of overpayment dollars; partial coding overpayments are 8%, sized 5–60% of the payment; underpayments are all partial coding errors sized 5–50% of the payment. Per-type rates are closed form from the FY 2025 overpayment and underpayment dollars (Supplemental Improper Payment Data, Tables A1 and A4). The simulated truth is 6.50% gross (FY 2025: 6.55%), with $0.92B in underpayments (FY 2025: $1.0B).

*Audit:* 37,651 claims, the FY 2025 count of claims reviewed per claim type (IPPS 8,750; Part A excluding IPPS 8,651; Part B 11,600; DMEPOS 8,650), with Neyman allocation across five equal-count payment quintiles within each type. These stand in for CERT's service-level strata within claim type and its MAC-jurisdiction strata, which cannot be rebuilt from public data. The production estimator reduces nationally to a separate ratio estimator (CMS 2026b). The Part A-to-B rebilling adjustment is out of scope.

### B.6 Assumptions common to all programs

1. *Review is perfect.* The audit finding equals the truth, with no reviewer error and no appeals.
2. *One audit per year.* Each audit year has one audit, and every method uses only that audit.
3. *Errors are independent of selection and of payment size within strata.* Within a stratum, error probability does not depend on whether a unit is sampled, and in every program it does not depend on the unit's payment, GDC, APTC or other characteristics except through the strata definitions. This assumption is relaxed in Appendix D.
4. *Neyman inputs.* Allocations use the stratum standard deviations of the true errors in the population as a stand-in for prior-year data, which favors the analytic estimators whose variance Neyman allocation minimizes.
5. *Gross is the reported rate.* PIIA gross rates are the primary estimand. Recovery, contract-level RADV extrapolation, and provider demands are out of scope.
6. *Unknown payments count as improper,* following CMS practice (for example, missing documentation in Part C).
7. *The regression fallback* to an intercept-only model is decided by the number of audited errors in any measure, so that the same model serves every measure.

## Appendix C. Additional results

{{TABLEC1}}

Results for every program, measure, method, and audit year (including overpayments, underpayments, and net in dollars) are available in `shared/results/report/by_scenario.csv` and `by_audit_year.parquet` (analytic methods and parametric rates), and in `manuscripts/generated/results_long.csv` (all methods, including fixed rates). Each program's README reports the analytic methods and the parametric-rate simulation.

## Appendix D. Interval calibration, robustness to size-dependent errors, and payment-decile donor kinds

Tables D1–D3 are described in Sections 2.8 and 3.6–3.7. Tables D4–D6 repeat the base and size-dependent populations with the simulation's donor kinds post-stratified into ten payment quantiles within each design stratum (`sim_kind_deciles: 10`; `robustness/run.py --only d4`). Part C is omitted from D4–D6 because its donor kinds are HCCs, whose coefficients do not depend on the enrollee's payment. In Part D the top GDC decile of the largest stratum holds about 61% of the true improper dollars and its rate is estimated from about ten audited failures per audit year, so the simulation's standard deviation roughly doubles; in the 25 audit years reported here that kind drew 220 failures against 265 expected, which accounts for the −12% mean in Table D4 (over 300 audit years the same estimator averages 0.99 of the truth).

{{APPENDIXD}}
