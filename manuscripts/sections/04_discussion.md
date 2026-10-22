## 4. Discussion

### 4.1 Principal findings

In five synthetic populations designed after the five CMS improper payment measurements, this study compared the expansion, ratio, and model-assisted regression estimators with audit-finding simulation in its plug-in and parametric-bootstrap versions. Four findings stand out.

First, the plug-in simulation interval is invalid in every program. Because the audit is never resampled, the interval measures only how the audited rates scatter across the population, as opposed to how much those rates would change with a different audit; it covered the true gross rate in 25% of audit years when 95% was intended, and its width shrinks toward zero as the population grows relative to the audit. This is the single-imputation problem of Rubin (1987) in a new setting, and it is not a tuning problem that more iterations can fix.

Second, redrawing the audited error and partial counts from their binomial sampling distributions before each iteration restores coverage of the gross rate: 121 of 125 audit years over the five programs, and 90 to 99 of 100 in the longer calibration run. The correction is a few lines of code and requires no additional record review. In Part C, Part D, PERM, and EIPM the resulting interval is still 5–12% narrower than the simulation estimator's own sampling variability, because the error sizes are held fixed and the rates of different donor kinds are redrawn independently; in CERT it is 13% wider.

Third, the simulation's narrower interval is partly efficiency and partly under-coverage, and the balance differs by program. Over 100 audit years, the standard deviation of the simulation's point estimate was 3% below the ratio estimator's in Part C and 4% below in EIPM, so in those programs most of the narrower interval in Table 4 is an interval that is too short. In PERM (23%), CERT (35%), and Part D (72%) the efficiency gain is real. It comes from the simulation using the payments, HCCs, benefit positions, and APTC inputs of every population unit, which makes it a model-based estimator in the sense of Valliant, Dorfman and Royall (2000): it borrows only the audited error counts and takes every unit's error size from the population.

Fourth, and most important for policy, that model is a condition, not a convenience. When the populations were rebuilt so that error probability rises with payment size within strata, the simulation's point estimate ran low by 3% in Part C, 8% in EIPM, 14% in PERM, 22% in CERT, and 65% in Part D, and its interval covered the truth in 24, 21, 6, 0, and 0 of 25 audit years. When error probability falls with payment size, the estimate ran high by 9% in Part C, 7% in PERM, and 148% in Part D, with coverage of 18, 18, and 0. The design-based estimators were unaffected: the ratio estimator covered in 22 to 25 of 25 audit years in every scenario, and its bias stayed within 2% except in EIPM (where every method runs 5–6% low in every scenario) and Part D (5–8%). The simulation's advantage therefore depends on an assumption the analytic estimators do not need, and in the programs where the advantage is largest (Part D, CERT, PERM) the penalty for the assumption failing is also largest. Whether real audit findings satisfy the assumption is an empirical question that the public record does not answer. Pricing discrepancies on specialty drugs, documentation failures on high-cost inpatient stays, and eligibility errors on high-utilization beneficiaries are all plausible mechanisms by which they would not.

### 4.2 Policy implications

**Recommendation 1 – Discontinue plug-in simulation intervals.** Any CMS measurement whose interval comes from a simulation that reuses the audited error rates in every iteration should replace it. The Part D interval algorithm is not public; its Sampling and Estimation Methodology Plan should be checked for this feature, and if present the interval should be recomputed with parametric rates for the current cycle. This change costs nothing in record review and can be verified by the census check used here (auditing every unit must return the true rate exactly).

**Recommendation 2 – Report the design-based ratio interval as the primary PIIA interval, with the parametric-bootstrap simulation alongside it.** The ratio estimator was within 2% of the truth and held close to nominal coverage in every population and every robustness scenario, because its validity rests on the sampling design alone. The parametric-bootstrap simulation should be reported with it where a program already simulates, so that the two can be compared: a simulation estimate that drifts from the ratio estimate is itself evidence that error incidence depends on unit characteristics within strata. A program that reports the simulation as its only estimate has no such check.

**Recommendation 3 – Treat the simulation's precision gain as conditional, and test the condition before relying on it.** The gain is real in PERM, CERT, and Part D under the stated model. Before it is used to justify a smaller audit, three things should be done: (a) compare audited error rates across payment quantiles within each stratum, which the audit data already permit; (b) stratify or post-stratify the simulation's donor kinds finely enough on payment that the within-stratum dependence is small; and (c) confirm coverage directly at the reduced audit size with a Monte Carlo study on a population built to match the observed dependence. If interval width scales with 1/√*n*, the parametric interval would match the current ratio interval at about 83% of the Part C audit, 63% of PERM, 77% of EIPM, and 59% of CERT (Table 4); from the calibrated standard deviations these shares are about 93%, 60%, 93%, and 42%. These figures are projections (as opposed to demonstrated results), apply only to the gross rate, and hold only where the independence assumption does.

**Recommendation 4 – Protect sparse components.** Components that CMS reports separately and that rest on few audited errors (underpayments, technically improper payments) were undercovered by every method, with the misses below the truth. They need their own precision check under any method, and a reduction in audit size for the gross rate should not be taken to extend to them.

### 4.3 Future research

Future research should first identify the audit size at which each program's interval still covers the truth at the nominal rate, by rerunning each design at reduced sizes (for example 50%, 65%, and 80% of current) with at least 200 audit years, for the gross rate and for the components CMS reports. Allocation should be reconsidered at the same time: Neyman allocation minimizes the variance of the analytic estimator (as opposed to the simulation), and the cost of review differs by stratum, so cost-weighted allocation (*n_h* ∝ *N_h S_h* / √*c_h*) belongs in the same study.

Second, future research should replace the simulation's independence assumption with a model. A unit-level error model (logistic or zero-inflated regression of error probability and size on payment, provider type, drug class, or HCC count), fit on the audit and used to assign findings in the simulation, would retain the simulation's use of population structure while removing the assumption that Appendix D shows to be decisive; its coverage should be tested on populations built with size-dependent errors. Hierarchical models that pool rates across strata, HCCs, or states would give zero-failure strata a plausible nonzero rate, and resampling the partial-size list within each iteration, together with a joint rather than independent redraw of correlated rates, would address the 5–12% under-coverage found in the calibration run. BCa or double-bootstrap calibration (Efron 1987; Hall 1988) could be applied to the iteration distribution for sparse components.

Third, the same design should be extended to the settings where interval accuracy carries dollar consequences: state-level PERM eligibility rates, which carry federal match consequences beginning in FY 2030 (P.L. 119-21); State-based Exchange measurement beginning in 2027; and contract-level RADV, where the interval becomes a one-sided lower bound for recovery. Finally, under an appropriate data use agreement, the two assumptions this study had to make, the share of partial errors and the independence of error probability from payment size within strata, should be checked against held-out real audit samples.

### 4.4 Limitations

The major limitation of this study is that its populations are synthetic. They are calibrated only to public aggregates, and the error mechanisms, partial-error shares, and, in the main results, the independence of errors from payment size within strata are assumptions. Appendix D shows that the last assumption decides the comparison, and the real degree of dependence is unknown. Strata and audit sizes that the agencies do not publish (EIPM, Part C IPM, both Part D audits, and CERT's service-level and jurisdiction strata) are illustrative; MAC jurisdictions, denied claims, and the CERT Part A-to-B rebilling adjustment are not modeled; PERM is one cycle of nine states rather than a three-year rotation of seventeen; Part D's underpayments are structurally sparser than in production.

Second, the main results rest on 25 audit years per program, for which the Monte Carlo standard error of a coverage estimate is 4.4 points, so coverage counts of 22 to 25 cannot be distinguished. The 100-audit-year calibration run (standard error 2.2 points) and the width-to-standard-deviation ratio are the stronger evidence, and they show the parametric interval to be 5–12% too narrow in four programs.

Third, review is assumed to be error-free and final, with no appeals, and every method is given the same perfect findings.

Fourth, the Part D comparison mixes designs and estimators. The ratio and regression comparators use a different audit that reviews about 41,000 PDEs, the plug-in expansion is biased by construction, and the design-based PDE estimators on the same audit, while unbiased, inherit heavy-tailed audited error dollars that make their normal intervals undercover. No analytic method on the 5,000-PDE audit is a clean benchmark, and the Part D width figures should be read with that in mind.

Fifth, the parametric version redraws the rates of different donor kinds independently and holds the audited error sizes fixed, which is why its interval is somewhat too narrow; it is also only one of several ways the audit's uncertainty could be propagated.

Sixth, this study addresses two-sided PIIA rate intervals. Recovery uses rely on one-sided lower bounds, which were not tested, and no CMS program is shown here to use a plug-in simulation; the policy case for Recommendation 1 is conditional on that being so.

### 4.5 Conclusion

On the question of comparative accuracy, the answer has two parts. Audit-finding simulation with fixed rates produces point estimates as accurate as the analytic estimators but intervals far too narrow to be valid, because the audit is never resampled and the sampling error of the rates is omitted; redrawing the rates from their binomial sampling distribution restores nominal coverage for the gross rate. However, the simulation's accuracy and its narrower interval rest on error incidence being independent of payment size within strata, an assumption the populations satisfied by construction and the design-based estimators do not need; when it fails, the simulation is biased and its interval misses, while the ratio estimator does not. This study therefore recommends that CMS programs discontinue any plug-in simulation interval, report the design-based ratio interval as the primary PIIA interval with the parametric-bootstrap simulation alongside it, and treat the simulation's precision gain, which is real in Part D, PERM, and CERT under the stated model, as a reason to test the independence assumption on real audit data and to develop unit-level error models, rather than as a basis for smaller audits today.

## Data and code availability

All code, configuration, synthetic populations (or their SHA-256 manifests where a population is too large to commit), results, the robustness and calibration runs, and the scripts that build every table and figure in this paper are available in the public repository [andrewcistola/improper-payment-estimation-accuracy](https://github.com/andrewcistola/improper-payment-estimation-accuracy). The repository contains no protected health information, no unit-level data from any source, and no non-public CMS material. An independent re-run and review of the study, with the issues it raised and the changes made in response, is in the repository's `qa/` folder.

## Funding, conflicts of interest and disclaimer

[To be completed by the author before submission: funding source, employer and contract relationships, and a statement that the views are the author's own and do not represent CMS or any other organization.]

## References

- Biddle GC, Bruton CM, Siegel AF (1990). Computer-intensive methods in auditing: bootstrap difference and ratio estimation. *Auditing: A Journal of Practice & Theory* 9(3):92–114.
- Bickel PJ, Freedman DA (1984). Asymptotic normality and the bootstrap in stratified sampling. *Annals of Statistics* 12(2):470–482.
- CMS (2023). FY 2023 Medicare Part D Error Rate Findings and Results. Centers for Medicare & Medicaid Services.
- CMS (2025b). 2025 Medicare Fee-for-Service Supplemental Improper Payment Data. Centers for Medicare & Medicaid Services.
- CMS (2025c). FY 2025 Medicare Part D Error Rate Findings and Results. Centers for Medicare & Medicaid Services.
- CMS (2025d). FY 2025 Medicare Part C Error Rate Findings and Results. Centers for Medicare & Medicaid Services.
- CMS (2026a). Fiscal Year 2025 Improper Payments Fact Sheet (January 15, 2026). Centers for Medicare & Medicaid Services.
- CMS (2026b). Medicare Fee-for-Service Comprehensive Error Rate Testing (CERT) Methodology; Introduction to the Comprehensive Error Rate Testing Program. Centers for Medicare & Medicaid Services.
- CMS (2026c). Exchange Improper Payment Measurement: Improper Payment Findings. Centers for Medicare & Medicaid Services.
- Cistola A (2026). Methods for estimating improper payments in federal health programs: a narrative review of their comparative accuracy. Companion review, `literature-review/` in the study repository.
- Cochran WG (1977). *Sampling Techniques*, 3rd ed. Wiley.
- Cox DR, Snell EJ (1979). On sampling and the estimation of rare errors. *Biometrika* 66(1):125–132.
- Department of Education Office of Inspector General (2026). U.S. Department of Education's Compliance with Payment Integrity Information Reporting Requirements for Fiscal Year 2025. ED-OIG/A26DC0288, August 4, 2026.
- Edwards D (2011). On stratified sampling and ratio estimation in Medicare and Medicaid benefit integrity investigations. *Health Services and Outcomes Research Methodology* 11:79–94.
- Edwards D, Liu P, Delage A (2023). Model-based stratification of payment populations in Medicare integrity investigations. *Survey Methodology* 49(2):607–626.
- Efron B (1987). Better bootstrap confidence intervals. *Journal of the American Statistical Association* 82(397):171–185.
- Efron B, Tibshirani RJ (1993). *An Introduction to the Bootstrap*. Chapman & Hall.
- Hall P (1988). Theoretical comparison of bootstrap confidence intervals. *Annals of Statistics* 16(3):927–953.
- Hesterberg TC (2015). What teachers should know about the bootstrap: resampling in the undergraduate statistics curriculum. *The American Statistician* 69(4):371–386.
- Howard RC (1994). A combined bound for errors in auditing based on Hoeffding's inequality and the bootstrap. *Journal of Business & Economic Statistics* 12(2):437–448.
- Johns D, Rosenbaum D (2024). *Distribution of Tax Year 2014–2015 Individual Income Tax and Self-Employment Tax Underreporting Tax Gap*. Internal Revenue Service, Research, Applied Analytics & Statistics.
- Kvanli AH, Shen YK, Deng LY (1998). Construction of confidence intervals for the mean of a population containing many zero values. *Journal of Business & Economic Statistics* 16(3):362–368.
- Mashreghi Z, Haziza D, Léger C (2016). A survey of bootstrap methods in finite population sampling. *Statistics Surveys* 10:1–52.
- McConville KS, Moisen GG, Frescino TS (2020). A tutorial on model-assisted estimation with application to forest inventory. *Forests* 11(2):244.
- Morris TP, White IR, Crowther MJ (2019). Using simulation studies to evaluate statistical methods. *Statistics in Medicine* 38(11):2074–2102.
- Neter J, Loebbecke JK (1975). *Behavior of Major Statistical Estimators in Sampling Accounting Populations: An Empirical Study*. Auditing Research Monograph No. 2. AICPA.
- OMB (2021). Memorandum M-21-19, Appendix C to Circular A-123: Requirements for Payment Integrity Improvement (March 5, 2021). Office of Management and Budget.
- Payment Integrity Information Act of 2019, Pub. L. 116-117.
- P.L. 119-21 (2025), §71106.
- Rao JNK, Wu CFJ (1988). Resampling inference with complex survey data. *Journal of the American Statistical Association* 83(401):231–241.
- Rohrbach KJ (1993). Variance augmentation to achieve nominal coverage probability in sampling from audit populations. *Auditing: A Journal of Practice & Theory* 12(2):79–97.
- Rubin DB (1981). The Bayesian bootstrap. *Annals of Statistics* 9(1):130–134.
- Rubin DB (1987). *Multiple Imputation for Nonresponse in Surveys*. Wiley.
- Särndal CE, Swensson B, Wretman J (1992). *Model Assisted Survey Sampling*. Springer.
- Valliant R, Dorfman AH, Royall RM (2000). *Finite Population Sampling and Inference: A Prediction Approach*. Wiley.
- 45 CFR §155.1605 (State Exchange improper payment measurement, applicability).
