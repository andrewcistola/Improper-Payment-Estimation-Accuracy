## 6. Future research

1. **Optimal audit sizes.** The audit-size figures in Table 4 are projections from a 1/√*n* scaling. The direct test is to rerun each program's design at reduced audit sizes (for example 50%, 65% and 80% of current) with at least 200 audit years. This would find the smallest audit at which the parametric interval still covers the truth in 95% of audit years for the gross rate and for the components CMS reports. Allocation should be reconsidered at the same time. Neyman allocation minimizes the variance of the analytic estimator, not of the simulation. The cost of review differs by stratum (an inpatient record costs more to review than a Part B claim), so cost-weighted allocation (*n_h* ∝ *N_h S_h / √c_h*) belongs in the same study.
2. **Model + simulation alternatives.** The parametric version models only the rates. Several extensions are natural:
   - **Hierarchical Bayesian error models.** Beta-binomial rates pooled across strata, HCCs or states would give zero-failure HCCs and small strata a plausible nonzero rate instead of a fixed zero. Their posterior predictive draws would replace the binomial redraw.
   - **Unit-level error models.** Logistic or zero-inflated regression of error probability and error size on unit features (payment amount, provider type, drug class, HCC count) would feed the simulation. This model-assisted microsimulation would use the full population's auxiliary data and could narrow intervals further where the features predict error.
   - **Resampling the size distribution.** Partial sizes could be resampled with replacement within each iteration, so that uncertainty in error size enters alongside uncertainty in the rates.
   - **Calibrated intervals.** BCa or double-bootstrap calibration could be applied to the iteration distribution to correct remaining tail imbalance in sparse components (Efron 1987; Hall 1988).
3. **Settings beyond the PIIA national rate.** The study can be extended to:
   - state-level PERM eligibility rates, which carry federal match consequences from FY 2030 (P.L. 119-21);
   - State-based Exchange measurement from 2027;
   - contract-level RADV, where the interval becomes a lower bound for recovery and one-sided coverage matters.
4. **Validation on real audits.** Under an appropriate data use agreement, the synthetic results can be checked against held-out real audit samples, in particular the share of partial errors and whether error probability depends on payment size, which this study assumes away within strata.

## 7. Conclusion

On the question of comparative accuracy, the answer is consistent across the five programs studied. In every program, audit-finding bootstrap simulation with fixed rates produces point estimates as accurate as the analytic estimators, but intervals far too narrow to be valid. The cause is structural: the audit is never resampled, so the interval omits the sampling error of the rates. Redrawing the rates from their binomial sampling distribution before each iteration restores nominal coverage for the gross rate in every program. Those intervals are also narrower than the analytic intervals from the same audit in all five programs: 11–21% narrower than the ratio estimator in four, and much narrower than expansion in Part D. We recommend parametric-rate bootstrap simulation for improper payment rate estimation. Its precision gain gives CMS room to reduce audit sizes, and with them review costs, without losing accuracy, subject to direct confirmation at the reduced sizes.

## Data and code availability

All code, configuration, synthetic populations (or their SHA-256 manifests where a population is too large to commit), results and the scripts that build every table and figure in this paper are in the public repository [andrewcistola/improper-payment-estimation-accuracy](https://github.com/andrewcistola/improper-payment-estimation-accuracy). The repository contains no protected health information, no unit-level data from any source and no non-public CMS material.

## Funding, conflicts of interest and disclaimer

[To be completed by the author before submission: funding source, employer and contract relationships, and a statement that the views are the author's own and do not represent CMS or any other organization.]

## References

- Biddle GC, Bruton CM, Siegel AF (1990). Computer-intensive methods in auditing: bootstrap difference and ratio estimation. *Auditing: A Journal of Practice & Theory* 9(3):92–114.
- CMS (2023). FY 2023 Medicare Part D Error Rate Findings and Results. Centers for Medicare & Medicaid Services.
- CMS (2025a). Fiscal Year 2025 Improper Payments Fact Sheet. Centers for Medicare & Medicaid Services.
- CMS (2025b). 2025 Medicare Fee-for-Service Supplemental Improper Payment Data. Centers for Medicare & Medicaid Services.
- CMS (2025c). FY 2025 Medicare Part D Error Rate Findings and Results. Centers for Medicare & Medicaid Services.
- CMS (2025d). FY 2025 Medicare Part C Error Rate Findings and Results. Centers for Medicare & Medicaid Services.
- CMS (2026a). Exchange Improper Payment Measurement: Program Background and Improper Payment Findings. Centers for Medicare & Medicaid Services.
- CMS (2026b). Medicare Fee-for-Service Comprehensive Error Rate Testing (CERT) Methodology. Centers for Medicare & Medicaid Services.
- CMS (2024). Payment Error Rate Measurement, Supporting Statement Part B (OMB ICR 202408-0938-026).
- Cistola A (2026). Methods for estimating improper payments in federal health programs: a narrative review of their comparative accuracy. Companion review, `literature-review/` in the study repository.
- Cochran WG (1977). *Sampling Techniques*, 3rd ed. Wiley.
- Davison AC, Hinkley DV (1997). *Bootstrap Methods and Their Application*. Cambridge University Press.
- Department of Education OIG (2025). U.S. Department of Education's Compliance with Payment Integrity Information Act Reporting Requirements for Fiscal Year 2025.
- Edwards D, Liu P, Delage A (2023). Model-based stratification of payment populations in Medicare integrity investigations. *Survey Methodology* 49(2):607–626.
- Efron B (1987). Better bootstrap confidence intervals. *Journal of the American Statistical Association* 82(397):171–185.
- Efron B, Tibshirani RJ (1993). *An Introduction to the Bootstrap*. Chapman & Hall.
- Hall P (1988). Theoretical comparison of bootstrap confidence intervals. *Annals of Statistics* 16(3):927–953.
- Hesterberg TC (2015). What teachers should know about the bootstrap. *The American Statistician* 69(4):371–386.
- King B, Madansky A (2013). On sampling design issues when dealing with zeros. *Journal of Survey Statistics and Methodology* 1(2):144–170.
- Kvanli AH, Shen YK, Deng LY (1998). Construction of confidence intervals for the mean of a population containing many zero values. *Journal of Business & Economic Statistics* 16(3):362–368.
- Mashreghi Z, Haziza D, Léger C (2016). A survey of bootstrap methods in finite population sampling. *Statistics Surveys* 10:1–52.
- Neter J, Loebbecke JK (1975). *Behavior of Major Statistical Estimators in Sampling Accounting Populations: An Empirical Study*. AICPA.
- OMB (2021). Memorandum M-21-19, Appendix C to Circular A-123: Requirements for Payment Integrity Improvement. Office of Management and Budget.
- Payment Integrity Information Act of 2019, Pub. L. 116-117.
- Rao JNK, Wu CFJ (1988). Resampling inference with complex survey data. *Journal of the American Statistical Association* 83(401):231–241.
- Wolter KM (2007). *Introduction to Variance Estimation*, 2nd ed. Springer.
