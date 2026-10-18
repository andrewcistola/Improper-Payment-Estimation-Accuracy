---
title: "Comparative Accuracy of Improper Payment Estimation Methods in Federal Health Programs"
---

**Andrew Cistola, PhD, MPH · October 2026 · Full manuscript and code: [github.com/andrewcistola/improper-payment-estimation-accuracy](https://github.com/andrewcistola/improper-payment-estimation-accuracy)**

**The question.** What is the comparative accuracy of the available methods for estimating improper payments in federal health programs? CMS audits samples of payments in five programs and projects the errors to a national improper payment rate with a 95% confidence interval: Medicare Part C, Medicare Part D, Medicaid (PERM), Marketplace APTC (EIPM) and Medicare FFS (CERT). The projection uses analytic estimators (expansion, ratio, regression) or *audit-finding bootstrap simulation*, which assigns the audit's findings at random across the whole population and reruns the payment rules many times. Accuracy means point accuracy and interval accuracy: whether the 95% interval contains the truth about 95% of the time, and how narrow it is.

**How we tested it.** We built five synthetic populations, one per program, with fabricated errors so that the true improper payment is known. Each was calibrated only to public FY 2025 results. We drew each program's production-like audit 25 times (25 "audit years"). In every audit year we estimated the improper payment rate with the expansion, ratio and regression estimators and with bootstrap simulation, and checked whether each 95% interval contained the truth. No real or non-public data were used.

**Finding 1: the standard bootstrap interval is far too narrow.** The bootstrap's point estimates are as accurate as, or more accurate than, the analytic methods. Its interval, however, is only 5–21% as wide as it should be, and it contained the true rate in **30 of 125** audit-years (24%) instead of about 95%. The cause is structural. The simulation reuses the audit's error rates in every iteration, so the interval reflects only where the errors land, not how different the rates would have been with a different audit.

**Finding 2: one change fixes it.** Before each iteration, redraw each error rate from its binomial sampling distribution (*parametric rates*). With that change the interval contained the true rate in **121 of 125** audit-years (96.8%). It was also narrower than the analytic interval from the same audit:

| Gross improper payment rate | Part C | Part D | PERM | EIPM | CERT |
|---|---|---|---|---|---|
| True rate (synthetic) | 6.06% | 1.38% | 6.09% | 0.92% | 6.50% |
| Audit per year | 990 enrollees | 5,000 PDEs | 9 × 520 payments | 2,000 applications | 37,651 claims |
| **Analytic** (ratio; Part D expansion): coverage, half-width | 24/25, ±1.03 | 18/25, ±0.60 | 23/25, ±0.80 | 22/25, ±0.35 | 24/25, ±0.36 |
| **Bootstrap, fixed rates** | 3/25, ±0.05 | 10/25, ±0.06 | 3/25, ±0.10 | 6/25, ±0.05 | 8/25, ±0.07 |
| **Bootstrap, parametric rates** | **24/25, ±0.92** | **25/25, ±0.22** | **24/25, ±0.63** | **23/25, ±0.31** | **25/25, ±0.28** |
| Audit needed for today's analytic precision, if width ∝ 1/√n | ~79% | (see note) | ~63% | ~80% | ~62% |

*Coverage = audit years (of 25) with the truth inside the 95% interval; a valid interval scores about 24. Half-width in percentage points.*

**Recommendation.** Use **bootstrap simulation with parametric rates** for PIIA improper payment rates. It is valid, it gives the most accurate point estimates, and its narrower intervals leave room to cut audit sizes by roughly **20–38%** at current precision. That could mean about 780 instead of 990 Part C enrollees, 330 instead of 520 PERM payments per state, and 23,300 instead of 37,651 CERT claims. Medical record review is the main cost of each measurement, so the savings would come without giving up accuracy. Keep the analytic interval alongside it during a transition. Do not use the fixed-rate interval.

**Caveats.** The audit reductions are projections and must be confirmed directly at the smaller sizes. Measures built from few errors, such as underpayments, were undercovered by every method and need their own check. The results come from 25 audit years per program (Monte Carlo SE about ±4 points) and synthetic populations; strata CMS does not publish are illustrative. *Note:* Part D's only analytic comparator on the same audit (expansion) is weak, so its larger projected saving is not counted.

**Next.** (1) Find the optimal audit size by rerunning each design at 50–80% of the current audit with 200+ audit years. (2) Test model + simulation alternatives: hierarchical (beta-binomial) error rates, unit-level error models feeding the simulation, resampled error sizes, and calibrated (BCa) intervals. (3) Extend to state PERM rates, State-based Exchanges and one-sided recovery bounds.
