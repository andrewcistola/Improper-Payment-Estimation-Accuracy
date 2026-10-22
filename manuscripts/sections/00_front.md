---
title: "Comparative Accuracy of Improper Payment Estimation Methods in Federal Health Programs: A Monte Carlo Evaluation of Analytic Estimators and Audit-Finding Simulation"
author: "Andrew Cistola, PhD, MPH"
date: "October 2026"
---

**Affiliation:** [to be completed by the author]. **Corresponding author:** andrewcistola@pm.me

**Running title:** Comparative accuracy of improper payment estimation methods

**Word count:** about 7,400 (main text, excluding tables and references); abstract about 350; 5 tables, 2 figures; Appendices A–D.

## Abstract

**Background.** The Centers for Medicare & Medicaid Services (CMS) estimates improper payments in Medicare Part C, Medicare Part D, Medicaid (PERM), Marketplace advance premium tax credits (EIPM), and Medicare fee-for-service (CERT) from audited samples, each with a 95% confidence interval. The available projection methods are the design-based expansion, ratio, and regression estimators and audit-finding simulation, which assigns audited findings across the population and reruns the payment rules. These methods have not been compared against a known truth.

**Purpose.** The purpose of this study is to compare the point and interval accuracy of available methods for estimating improper payments in federal health programs.

**Methods.** Five synthetic populations with fabricated errors were calibrated to public FY 2025 aggregates, and each program's production-like audit (990 to 37,651 units) was drawn in 25 independent audit years, with 100 for interval calibration. Expansion, ratio, and regression estimators were compared with simulation that held audited error rates fixed (plug-in) or redrew them from their binomial sampling distributions (parametric bootstrap). Each population was then rebuilt with error probability rising, and falling, with payment size within strata.

**Results.** Plug-in intervals were 5–21% as wide as the analytic intervals and covered the true gross rate in 25% of audit years. Parametric-bootstrap intervals covered in 121 of 125 audit years and were 9–23% narrower than the ratio interval in four programs, but were 5–12% narrower than the estimator's own sampling variability in four programs over 100 audit years. When error probability depended on payment size, the simulation's estimate was biased by 2% to 148% and its interval covered in 0 to 24 of 25 audit years; the ratio estimator remained unbiased with coverage of 22 to 25.

**Conclusions.** Plug-in simulation intervals are invalid. The parametric-bootstrap simulation restores coverage and is more precise in Part D, PERM, and CERT, but both rest on error incidence being independent of payment size within strata. This study recommends the design-based ratio interval as the primary PIIA interval, with the parametric-bootstrap simulation alongside it, and a test of the independence assumption on real audit data before the simulation's precision is used to reduce audit sizes.

**Keywords:** improper payments; bootstrap; Monte Carlo simulation; survey sampling; Medicare; Medicaid; payment integrity; confidence intervals
