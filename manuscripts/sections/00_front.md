---
title: "Comparative Accuracy of Improper Payment Estimation Methods in Federal Health Programs: A Monte Carlo Evaluation of Analytic Estimators and Bootstrap Simulation"
author: "Andrew Cistola, PhD, MPH"
date: "October 2026"
---

**Affiliation:** [to be completed by the author]. **Corresponding author:** andrewcistola@pm.me

**Running title:** Comparative accuracy of improper payment estimation methods

**Word count:** about 4,400 (main text, excluding tables and references); abstract about 330; 5 tables, 2 figures; Appendices A–C.

## Abstract

**Background.** CMS estimates improper payments in Medicare Part C, Part D, Medicaid (PERM), Marketplace APTC (EIPM) and Medicare fee-for-service (CERT) from audited samples, with 95% confidence intervals required by law. The available projection methods, the analytic expansion, ratio and regression estimators and audit-finding bootstrap simulation (which assigns audited findings across the population and reruns the payment rules), have not been compared against a known truth.

**Purpose.** To answer the question: what is the comparative accuracy of the available methods for estimating improper payments in federal health programs? Accuracy means point accuracy and interval accuracy (coverage at the nominal 95%, then width).

**Methods.** We built five synthetic populations, one per program, with fabricated errors and calibrated to public FY 2025 aggregates, and drew each program's production-like audit (990 to 37,651 units) in 25 independent audit years. We compared expansion and ratio estimators with normal intervals and a model-assisted regression estimator (models fit within strata on basic beneficiary variables and the amount paid, residual interval) against bootstrap simulation (1,000 iterations) with error rates held fixed at their audited values or redrawn each iteration from their binomial sampling distributions (parametric rates).

**Results.** Bootstrap point estimates were as accurate as or more accurate than the analytic estimates. Fixed-rate bootstrap intervals were 5–21% as wide as the analytic intervals and contained the true gross rate in 30 of 125 audit-years (24%), because they omit the sampling variance of the audited rates. Parametric-rate intervals contained it in 121 of 125 (96.8%; 23–25 of 25 in every program) and were 11–21% narrower than the ratio estimator's in four programs and 63% narrower than the same-audit expansion interval in Part D. Measures built from few errors, such as underpayments, were undercovered by every method.

**Conclusions.** Fixed-rate bootstrap intervals should not be used. Bootstrap simulation with parametric rates gives valid, narrower intervals, and we recommend it for PIIA improper payment rates. Its precision would permit audits roughly 20–38% smaller at current precision, reducing review costs without sacrificing accuracy, pending confirmation at reduced sizes.

**Keywords:** improper payments; bootstrap; Monte Carlo simulation; survey sampling; Medicare; Medicaid; payment integrity; confidence intervals
