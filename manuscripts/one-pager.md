---
title: "Comparative Accuracy of Improper Payment Estimation Methods in Federal Health Programs"
---

**Andrew Cistola, PhD, MPH · October 2026 · Full manuscript and code: [github.com/andrewcistola/improper-payment-estimation-accuracy](https://github.com/andrewcistola/improper-payment-estimation-accuracy)**

**Study purpose.** The purpose of this study is to compare the accuracy of available methods for estimating improper payments in federal health programs. CMS audits samples of payments in five programs (Medicare Part C, Medicare Part D, Medicaid PERM, Marketplace APTC EIPM, and Medicare FFS CERT) and projects the errors to a national improper payment rate with a 95% confidence interval. This projection uses either design-based analytic estimators (expansion, ratio, or regression) or *audit-finding simulation*, which assigns the audit findings at random across the whole population and reruns the payment rules many times. Accuracy includes point accuracy and interval accuracy (whether the 95% interval contains the truth about 95% of the time, and how narrow it is).

**Methods.** This study built five synthetic populations (one per program) with fabricated errors so that the true improper payment is known, calibrated only to public FY 2025 results. Each program's production-like audit was drawn 25 times (25 "audit years"), and 100 times to check interval calibration. In every audit year the rate was estimated with every method and each 95% interval was checked against the truth. Each population was then rebuilt with errors more likely on large payments, and again on small payments, to test an assumption the simulation depends on. No real or non-public data were used.

**Finding 1: the plug-in simulation interval is far too narrow.** When the audited error rates are reused in every iteration, the interval reflects only where the errors land (as opposed to how different the rates would have been with a different audit). It is 5–21% as wide as it should be and contained the true rate in **31 of 125** audit years (25%).

**Finding 2: redrawing the rates corrects it.** Redrawing the audited error counts from their binomial sampling distribution before each iteration (*parametric rates*) raised coverage to **121 of 125** audit years, and the interval was narrower than the analytic interval from the same audit. Over 100 audit years, however, the parametric interval was 5–12% narrower than the simulation estimator's own sampling variability in four programs, so part of the gain is an interval that is too short. The real efficiency gain over the ratio estimator was 3% (Part C), 4% (EIPM), 23% (PERM), 35% (CERT) and 72% (Part D).

| Gross improper payment rate, 25 audit years | Part C | Part D | PERM | EIPM | CERT |
|---|---|---|---|---|---|
| True rate (synthetic) | 6.06% | 1.38% | 6.09% | 0.92% | 6.50% |
| Audit per year | 990 enrollees | 5,000 PDEs | 9 × 520 payments | 2,000 applications | 37,651 claims |
| **Ratio estimator** (Part D: PDE ratio, same audit): coverage, half-width | 24/25, ±1.03 | 17/25, ±0.91 | 23/25, ±0.80 | 22/25, ±0.35 | 24/25, ±0.36 |
| **Simulation, plug-in (fixed rates)** | 3/25, ±0.05 | 10/25, ±0.06 | 3/25, ±0.10 | 7/25, ±0.04 | 8/25, ±0.07 |
| **Simulation, parametric rates** | **25/25, ±0.94** | **25/25, ±0.21** | **24/25, ±0.63** | **22/25, ±0.30** | **25/25, ±0.28** |
| Simulation when errors depend on payment size: bias, coverage | −3% / +9%; 24, 18 | −65% / +148%; 0, 0 | −14% / +7%; 6, 18 | −8% / −2%; 21, 24 | −22% / +12%; 0, 0 |
| Ratio estimator in the same scenarios: coverage | 25, 23 | 22, 22 | 25, 25 | 23, 24 | 25, 23 |

*Coverage = audit years (of 25) with the truth inside the 95% interval; a valid interval scores about 24. Half-width in percentage points. Last two rows: errors more likely on large payments / on small payments.*

**Finding 3: the simulation's advantage rests on one stated assumption, which can be checked and partly repaired.** The simulation borrows only the audited error *counts* and takes every unit's size from the population, so it is accurate only if error probability does not depend on payment size within a donor kind. When it does, the simulation is biased by 2% to 148% (in the direction opposite to the association) and its narrow interval misses, while the design-based ratio estimator stays unbiased and covers in 22–25 of 25 audit years. Borrowing findings within payment deciles inside each stratum removes the bias in PERM (−14% → −4%; +7% → +0.4%) at little cost in precision, and removes half to three-quarters of it in CERT and Part D, whose payments are heavy-tailed within strata, at the cost of most of the precision gain.

**Recommendations.** (1) Adopt parametric-bootstrap simulation for PIIA improper payment rates, with the within-kind independence of error and payment size stated as a central assumption in the methodology plan; discontinue any plug-in interval (the Part D algorithm is not public and should be checked). (2) Verify the assumption every cycle from the audit: tabulate error rates and taints across payment deciles within strata, and report the simulation and the design-based ratio estimate together — a drift between them is the test. (3) Where the check fails, borrow findings within payment deciles; where payments are heavy-tailed within strata, report ratio and simulation together and treat their difference as the impact of the assumption. (4) Reduce audit sizes (projected 59–83% of today's for the same width) only after the check has passed and coverage has been confirmed at the smaller size; check sparse components separately.

**Limitations.** The populations are synthetic and calibrated to public aggregates only; strata CMS does not publish are illustrative; 25 audit years give a Monte Carlo SE of about 4 points on coverage (2 points for the 100-year run); the Part D comparators are weak because audited error dollars are heavy-tailed; review is assumed perfect; one-sided recovery bounds were not tested.

**Future research.** Future research should (1) replace the simulation's independence assumption with a unit-level error model fit on the audit, which would succeed where payment deciles run out, and test it on populations with size-dependent errors; (2) identify the optimal audit size by rerunning each design at 50–80% of the current audit with 200+ audit years; and (3) extend this work to state PERM eligibility rates, State-based Exchanges, and one-sided recovery bounds.
