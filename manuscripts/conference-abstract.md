---
title: "Comparative Accuracy of Improper Payment Estimation Methods in Federal Health Programs: A Monte Carlo Evaluation of Analytic Estimators and Audit-Finding Simulation"
---

**Andrew Cistola, PhD, MPH** · [Affiliation]

**Research Objective.** The Payment Integrity Information Act requires statistically valid improper payment estimates, with confidence intervals, for at-risk federal programs. CMS produces five: Medicare Part C, Part D, Medicaid (PERM), Marketplace APTC (EIPM), and Medicare fee-for-service (CERT). Each projects errors from an audited sample using design-based analytic estimators (expansion, ratio, regression) or audit-finding simulation, which assigns audited findings across the population and reruns the payment rules. The purpose of this study is to compare the accuracy of available methods for estimating improper payments in federal health programs.

**Study Design.** Monte Carlo evaluation against a known truth. A synthetic population per program, with fabricated errors, was calibrated only to public FY 2025 aggregates. Each program's production-like audit (990–37,651 units) was drawn in 25 independent audit years, and in 100 for interval calibration. Improper payments were estimated with expansion, ratio, and regression estimators and with simulation (1,000 iterations) in two versions: plug-in (audited error rates held fixed) and parametric bootstrap (rates redrawn from their binomial sampling distributions). Each population was then rebuilt with error probability rising, and falling, with payment size within strata, and the simulation rerun with donor kinds post-stratified on payment decile. Outcomes were point accuracy, coverage, width, and half-width relative to the estimator's empirical standard deviation.

**Population Studied.** Synthetic populations of 330,253 Medicare Advantage enrollees, 108,000 Part D beneficiaries (4.5 million drug claims), 3.1 million Medicaid payments, 142,152 Marketplace applications, and 5.34 million fee-for-service claims, scaled to national dollars. No real or non-public data were used.

**Principal Findings.**
- **Plug-in intervals are invalid.** They were 5–21% as wide as analytic intervals and contained the truth in 31 of 125 audit years (25%), because reusing the audited rates omits their sampling error.
- **Parametric-bootstrap intervals restore coverage.** They contained the true gross rate in 121 of 125 audit years and were 9–23% narrower than the ratio interval in four programs; over 100 audit years the simulation's standard deviation was 3–4% (Part C, EIPM) to 23–72% (PERM, CERT, Part D) below the ratio estimator's.
- **The simulation's advantage rests on one assumption.** When error probability rose or fell with payment size, the simulation's estimate was biased by 2% to 148% and its interval covered in 0 to 24 of 25 audit years; the ratio estimator remained unbiased (22 to 25). Payment-decile donor kinds removed the bias in PERM and most of it in CERT and Part D.
- **Sparse measures** (underpayments, technically improper payments) were undercovered by every method.

**Conclusions.** Plug-in simulation intervals should be discontinued. Redrawing the audited rates produces valid intervals, and the simulation is more precise where payment rules are nonlinear, on one assumption the design-based ratio estimator does not need: that error incidence is independent of payment size within each donor kind.

**Implications for Policy or Practice.** CMS measurements should adopt parametric-bootstrap simulation with the independence assumption stated and tested every cycle (against the design-based ratio estimate where the audit and payment units coincide, and from the within-stratum error pattern where they do not), use payment-decile donor kinds where the test fails, and defer audit-size reductions until the test has passed and coverage is confirmed at the smaller size. Unit-level error models are the natural next step.
