---
title: "Comparative Accuracy of Improper Payment Estimation Methods in Federal Health Programs: A Monte Carlo Evaluation of Analytic Estimators and Bootstrap Simulation"
---

**Andrew Cistola, PhD, MPH** · [Affiliation]

**Research Objective.** The Payment Integrity Information Act requires statistically valid improper payment estimates, with 95% confidence intervals, for at-risk federal programs. CMS produces five: Medicare Part C, Part D, Medicaid (PERM), Marketplace APTC (EIPM) and Medicare fee-for-service (CERT). Each projects errors from an audited sample, using analytic estimators (expansion, ratio, regression) or audit-finding bootstrap simulation, which assigns audited findings across the population and reruns the payment rules. Medical record review drives measurement cost, and audit sizes are set by interval width. We asked: what is the comparative accuracy of the available methods for estimating improper payments in federal health programs?

**Study Design.** Monte Carlo evaluation against known truth. For each program we built a synthetic population with fabricated errors, calibrated only to public FY 2025 aggregates. Each program's production-like audit (990–37,651 units, stratified, Neyman-allocated where applicable) was drawn in 25 independent audit years. In each, we estimated over-, under-, gross and net improper payments using expansion, ratio and regression estimators with normal intervals and bootstrap simulation with 1,000 iterations, in two versions:
- **Fixed rates:** audited error rates held constant.
- **Parametric rates:** rates redrawn from their binomial sampling distributions each iteration.

The outcomes were point accuracy, coverage (truth inside the 95% interval) and interval width.

**Population Studied.** Synthetic populations of 330,253 Medicare Advantage enrollees, 108,000 Part D beneficiaries (4.5 million drug claims), 3.1 million Medicaid payments, 142,152 Marketplace applications and 5.34 million fee-for-service claims, scaled to national program dollars. No protected health information or non-public data were used.

**Principal Findings.**
- **Point accuracy.** All methods estimated the gross rate accurately. Bootstrap simulation was the most accurate in four programs (mean absolute error 1.5–6.6% of the true rate).
- **Fixed-rate intervals.** These were 5–21% as wide as analytic intervals and contained the truth in only 30 of 125 audit-years (24%), because reusing the audited rates omits their sampling error.
- **Parametric-rate intervals.** These contained the true gross rate in 121 of 125 audit-years (96.8%; 23–25 of 25 per program), against 111 for the ratio estimator. They were 11–21% narrower than ratio intervals in four programs and 63% narrower than the same-audit expansion interval in Part D.
- **Sparse measures.** Measures built from few errors, such as underpayments, were undercovered by every method.

**Conclusions.** Fixed-rate bootstrap simulation, the intuitive version of the method, produces invalid intervals. Redrawing the audited rates from their sampling distribution restores nominal coverage and yields intervals narrower than current analytic intervals. Of the methods compared, bootstrap simulation with parametric rates was the most accurate on both point and interval accuracy.

**Implications for Policy or Practice.** CMS improper payment measurements should adopt bootstrap simulation with parametric rates, and any fixed-rate simulation intervals in use should be reviewed. The precision gain would allow audits roughly 20–38% smaller at current precision, reducing review costs without sacrificing accuracy. Confirming coverage at reduced sizes, with separate checks for sparse components, is the next step.
