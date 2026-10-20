---
title: "Comparative Accuracy of Improper Payment Estimation Methods in Federal Health Programs: A Monte Carlo Evaluation of Analytic Estimators and Bootstrap Simulation"
author: "Andrew Cistola, PhD, MPH"
date: "October 2026"
---

**Affiliation:** [to be completed by the author]. **Corresponding author:** andrewcistola@pm.me

**Running title:** Comparative accuracy of improper payment estimation methods

**Word count:** about 4,600 (main text, excluding tables and references); abstract about 380; 5 tables, 2 figures; Appendices A–C.

## Abstract

**Background.** The Centers for Medicare & Medicaid Services (CMS) estimates improper payments in Medicare Part C, Medicare Part D, Medicaid (PERM), Marketplace advance premium tax credits (EIPM), and Medicare fee-for-service (CERT) from audited samples, and the law requires that each estimate include a 95% confidence interval. The available projection methods include the analytic expansion, ratio, and regression estimators and audit-finding bootstrap simulation (which assigns audited findings across the population and reruns the payment rules). These methods have not been compared against a known truth.

**Purpose.** The purpose of this study is to compare the accuracy of available methods for estimating improper payments in federal health programs. In this study, accuracy includes both point accuracy and interval accuracy (coverage at the nominal 95% and, after that, width).

**Methods.** This study built five synthetic populations (one per program) with fabricated errors, calibrated each to public FY 2025 aggregates, and drew each program's production-like audit (990 to 37,651 units) in 25 independent audit years. Expansion and ratio estimators with normal intervals and a model-assisted regression estimator (models fit within strata on basic beneficiary variables and the amount paid, with a residual interval) were compared against bootstrap simulation (1,000 iterations). The bootstrap simulation either held error rates fixed at their audited values or redrew them each iteration from their binomial sampling distributions (parametric rates).

**Results.** Bootstrap point estimates were as accurate as or more accurate than the analytic estimates. Fixed-rate bootstrap intervals were 5–21% as wide as the analytic intervals and contained the true gross rate in only 30 of 125 audit-years (24%) because they omit the sampling variance of the audited rates. Parametric-rate intervals contained the true gross rate in 121 of 125 audit-years (96.8%; 23–25 of 25 in every program). These intervals were also 11–21% narrower than the ratio estimator's in four programs and 63% narrower than the same-audit expansion interval in Part D. Measures built from few errors (for example, underpayments) were undercovered by every method.

**Conclusions.** Fixed-rate bootstrap intervals should not be used. Bootstrap simulation with parametric rates produces valid and narrower intervals, and this study recommends it for PIIA improper payment rates. At current precision, this method would permit audits roughly 20–38% smaller, which would reduce review costs without sacrificing accuracy (pending confirmation at reduced sizes).

**Keywords:** improper payments; bootstrap; Monte Carlo simulation; survey sampling; Medicare; Medicaid; payment integrity; confidence intervals
