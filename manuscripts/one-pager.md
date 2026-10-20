---
title: "Comparative Accuracy of Improper Payment Estimation Methods in Federal Health Programs"
---

**Andrew Cistola, PhD, MPH · October 2026 · Full manuscript and code: [github.com/andrewcistola/improper-payment-estimation-accuracy](https://github.com/andrewcistola/improper-payment-estimation-accuracy)**

**Study purpose.** The purpose of this study is to compare the accuracy of available methods for estimating improper payments in federal health programs. CMS audits samples of payments in five programs (Medicare Part C, Medicare Part D, Medicaid PERM, Marketplace APTC EIPM, and Medicare FFS CERT) and projects the errors to a national improper payment rate with a 95% confidence interval. This projection uses either analytic estimators (expansion, ratio, or regression) or *audit-finding bootstrap simulation*, which assigns the audit findings at random across the whole population and reruns the payment rules many times. Accuracy includes point accuracy and interval accuracy (whether the 95% interval contains the truth about 95% of the time, and how narrow it is).

**Methods.** This study built five synthetic populations (one per program) with fabricated errors so that the true improper payment is known. Each population was calibrated only to public FY 2025 results. Each program's production-like audit was then drawn 25 times (25 "audit years"). In every audit year, the improper payment rate was estimated with the expansion, ratio, and regression estimators and with bootstrap simulation, and each 95% interval was checked against the truth. This study used no real or non-public data.

**Finding 1: the standard bootstrap interval is far too narrow.** The bootstrap point estimates are as accurate as, or more accurate than, those of the analytic methods. However, the bootstrap interval is only 5–21% as wide as it should be, and it contained the true rate in **30 of 125** audit-years (24%) as opposed to about 95%. The cause is structural. The simulation reuses the audited error rates in every iteration, so the interval reflects only where the errors land (as opposed to how different the rates would have been with a different audit).

**Finding 2: one change corrects it.** Before each iteration, each error rate is redrawn from its binomial sampling distribution (*parametric rates*). With this change, the interval contained the true rate in **121 of 125** audit-years (96.8%). These results also show that the interval was narrower than the analytic interval from the same audit:

| Gross improper payment rate | Part C | Part D | PERM | EIPM | CERT |
|---|---|---|---|---|---|
| True rate (synthetic) | 6.06% | 1.38% | 6.09% | 0.92% | 6.50% |
| Audit per year | 990 enrollees | 5,000 PDEs | 9 × 520 payments | 2,000 applications | 37,651 claims |
| **Analytic** (ratio; Part D expansion): coverage, half-width | 24/25, ±1.03 | 18/25, ±0.60 | 23/25, ±0.80 | 22/25, ±0.35 | 24/25, ±0.36 |
| **Bootstrap, fixed rates** | 3/25, ±0.05 | 10/25, ±0.06 | 3/25, ±0.10 | 6/25, ±0.05 | 8/25, ±0.07 |
| **Bootstrap, parametric rates** | **24/25, ±0.92** | **25/25, ±0.22** | **24/25, ±0.63** | **23/25, ±0.31** | **25/25, ±0.28** |
| Audit needed for today's analytic precision, if width ∝ 1/√n | ~79% | (see note) | ~63% | ~80% | ~62% |

*Coverage = audit years (of 25) with the truth inside the 95% interval; a valid interval scores about 24. Half-width in percentage points.*

**Recommendation.** CMS should use **bootstrap simulation with parametric rates** for PIIA improper payment rates. This method is valid, produces the most accurate point estimates, and has narrower intervals that leave room to reduce audit sizes by roughly **20–38%** at current precision (for example, about 780 instead of 990 Part C enrollees, 330 instead of 520 PERM payments per state, and 23,300 instead of 37,651 CERT claims). Given that medical record review is the main cost of each measurement, these savings would come without sacrificing accuracy. The analytic interval should be reported alongside it during a transition, and the fixed-rate interval should not be used.

**Limitations.** The audit reductions are projections and must be confirmed directly at the smaller sizes. Measures built from few errors (for example, underpayments) were undercovered by every method and need their own check. The results come from 25 audit years per program (Monte Carlo SE about ±4 points) and from synthetic populations, and strata CMS does not publish are illustrative. *Note:* The only analytic comparator for Part D on the same audit (expansion) is weak, so its larger projected savings are not counted.

**Future research.** Future research should (1) identify the optimal audit size by rerunning each design at 50–80% of the current audit with 200+ audit years; (2) test model + simulation alternatives (hierarchical beta-binomial error rates, unit-level error models feeding the simulation, resampled error sizes, and calibrated BCa intervals); and (3) extend this work to state PERM rates, State-based Exchanges, and one-sided recovery bounds.
