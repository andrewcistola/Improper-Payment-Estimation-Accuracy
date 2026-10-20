## 4. Results

Table 2 provides, for each program, the median point estimate, median interval half-width, and coverage of the gross rate under every method. Figures 1 and 2 summarize width and coverage. National-dollar equivalents are provided in Appendix Table C1.

{{TABLE2}}

![Figure 1. Median 95% interval half-width for the gross rate, as a percentage of the true gross rate, over 25 audit years. Analytic comparator: ratio estimator (Part D: expansion, the analytic method that uses the same PDE audit as the bootstrap simulation).](generated/fig1_width.png)

![Figure 2. Number of the 25 audit years in which the 95% interval for the gross rate contains the true rate. The dashed line marks the nominal 95% (23.75 of 25).](generated/fig2_coverage.png)

### 4.1 The bootstrap point estimate is accurate

Before evaluating intervals, it is important to establish what the bootstrap simulation does well. The bootstrap point estimate is at least as accurate as the best analytic estimator in every program. It ties in Part C and is more accurate in the other four programs (Table 3):

| Program | Bootstrap mean absolute error (% of truth) | Best analytic mean absolute error | Expansion |
|---|---|---|---|
| Part C | 5.6% | 5.7% | |
| PERM | 4.4% | 5.3% (regression) | |
| EIPM | 16.6% | 17.6% | |
| CERT | 1.5% | 2.2% | |
| Part D | 6.6% | 23.4% (ratio, on the 990-beneficiary audit) | 30.5% (on the same PDE audit) |

The Part D difference reflects the benefit design. A PDE error changes Medicare's liability by an amount that depends on where the beneficiary sits in the benefit, and only rerunning the benefit captures this effect. The stratum-average rates used by expansion run 5.7% low.

The fixed and parametric versions produce the same point estimate to within 0.2 percentage points of relative error because the binomial redraw is centered on the audited rates. Signed errors for the bootstrap are within ±1% of the truth in every program except EIPM.

In EIPM, every method runs 5–8% low. Technically improper errors are rare (about 9 per audit) and large (the whole APTC), so in most audit years the sample contains fewer than the expected number, and the median estimate falls below the mean. This is a small-sample property of the data (as opposed to a property of any one method). The further 2–3% shortfall for the bootstrap in EIPM comes from moving the income ratio of a monetary error to an application at a different point of the APTC schedule (Appendix B.4).

{{TABLE3}}

### 4.2 The bootstrap interval problem

The fixed-rate bootstrap interval is far too narrow in every program. Its median half-width is 5% to 21% of the half-width of the analytic interval from the same audit (Table 4), and it contains the true gross rate in only 3 to 10 of 25 audit years (Figure 2). The misses fall on both sides about equally. For example, in Part C, 12 intervals lie entirely above the truth and 10 lie entirely below. These results show that the problem is not bias. Rather, the interval is centered correctly and is simply too short.

{{TABLE4}}

The cause is structural. The true sampling variance of an estimated improper total *T̂* can be written by the law of total variance, conditioning on the audit *A*:

  Var(*T̂*) = E[Var(*T̂* | *A*)] + Var(E[*T̂* | *A*]).

The fixed-rate bootstrap holds the audit, and therefore the rates *p_k* and *q_k*, fixed. Its iterations vary only in which unaudited units receive errors. As a result, its spread estimates only the first term (the *reassignment* variance). This term grows with the population size *N*, roughly as *N p(1 − p)* times the mean squared error size. The second term is the variance of the rates themselves across possible audits, which is the term a confidence interval exists to express. This term grows with *N²/n*.

The ratio of the two standard deviations is therefore roughly √(*n*/*N*), and the observed ratios follow this pattern:

| Program | √(*n*/*N*) | Observed fixed-rate width, share of analytic |
|---|---|---|
| Part C (990 of 330,253 enrollees) | 5.5% | 5% |
| EIPM (2,000 of 142,152 applications) | 11.9% | 13% |
| CERT (37,651 of 5.34 million claims) | 8.4% | 21% |
| PERM (520 of about 343,000 payments per state) | 3.9% | 13% |
| Part D (5,000 of about 4.5 million PDEs) | 3.3% | 10% |

The ratio is higher than √(*n*/*N*) in three programs:

- **CERT:** Inpatient claims are sampled at 22%, which inflates the reassignment term.
- **PERM and Part D:** Error sizes vary more because whole payments of very different amounts can be in error and the benefit is nonlinear.

None of these programs comes close to the analytic width.

More iterations do not solve this problem. Additional iterations estimate the reassignment spread more precisely but do not add the missing term. In addition, the interval becomes *narrower* as the population grows relative to the audit, which is the opposite of what a sampling interval should do. A larger program with the same audit would report greater precision than a smaller one.

### 4.3 The parametric alternative

The parametric version adds the missing term directly. Before each iteration, each rate is redrawn from its binomial sampling distribution given the audit (Section 3.6), so the iteration distribution spans plausible audit outcomes in addition to plausible assignments.

This change restores coverage of the gross rate in every program: 24, 25, 24, 23, and 25 of 25 audit years for Part C, Part D, PERM, EIPM, and CERT. In total, this is 121 of 125 audit-years (96.8%), as opposed to 30 of 125 (24%) with fixed rates. No parametric interval for the gross rate lay entirely above the truth, and all four misses were below.

The parametric intervals are also narrower than the analytic intervals from the same audit (Table 4, Figure 1):

| Program | Parametric half-width, share of analytic |
|---|---|
| Part C | 89% |
| EIPM | 89% |
| PERM | 79% |
| CERT | 79% |
| Part D (against expansion on the same PDE audit) | 37% |

The parametric intervals also achieved equal or higher coverage than the analytic intervals in every program:

| Program | Parametric | Analytic |
|---|---|---|
| Part C | 24/25 | 24/25 (ratio), 25/25 (expansion) |
| PERM | 24/25 | 23/25 |
| EIPM | 23/25 | 22/25 |
| CERT | 25/25 | 24/25 (ratio), 25/25 (expansion) |
| Part D | 25/25 | 15–18/25 |

In dollars (Appendix Table C1):

- **PERM:** The parametric interval is ±$0.90B around a median of $8.46B, as opposed to ±$1.13B for the ratio estimator.
- **CERT:** ±$1.24B around $28.81B, as opposed to ±$1.57B.
- **Part C:** ±$3.57B around $23.62B, as opposed to ±$4.02B.

The gain in width has two sources:

- **The known structure of the population.** The simulation reruns the payment function over the known payment, HCCs, benefit position, or APTC inputs of every unit. The simulation is therefore a model-assisted estimator that uses the auxiliary information of the full population, whereas the ratio estimator uses only total payments.
- **The list of partial sizes is held fixed.** The audited list of partial error sizes is reused (as opposed to resampled), which leaves out some uncertainty in error size. The coverage results suggest that this omission is small for the gross rate, but it is a reason to extend the method (Section 6).

The Part D gain is the largest and the least certain. The only analytic method on the same PDE audit is expansion. Its delta-method interval is wide and its point estimate runs low, so the 37% likely understates what a well-specified analytic interval on that audit could achieve.

### 4.4 Components and sparse measures

Table 5 provides the coverage of every reported measure. For the large components, the parametric version matched or exceeded the analytic methods:

{{TABLE5}}


- **Part C:** overpayments 24/25 and net 24/25.
- **Part D:** overpayments 25/25 and net 24/25.
- **PERM:** eligibility 24/25 (analytic 21/25) and claims 23/25.
- **EIPM:** monetary 22/25.
- **CERT:** overpayments and net 25/25, and every claim type 24–25/25.

The exceptions are the sparse measures (those built from a handful of audited errors):

| Measure | True rate | Parametric | Ratio | Expansion |
|---|---|---|---|---|
| Part C underpayments | 0.57% | 19/25 | 21/25 | |
| Part D underpayments | 0.02% | 20/25 | 15/25 | 0/25 |
| EIPM technically improper | 0.43% | 20/25 | 19/25 | |
| CERT underpayments | 0.21% | 20/25 | 23/25 | |

Every method undercovers these measures, and the misses fall mainly below the truth. The interval lies under the truth in audit years whose sample happened to contain few of the rare errors. This is the zero-inflated, right-skewed setting in which normal-theory intervals are known to fail (Kvanli et al. 1998; Hesterberg 2015). The parametric bootstrap does not avoid this problem because a binomial redraw centered on a low audited rate remains low. The gross rate is protected because the sparse component is a small share of it.

### 4.5 Regression with beneficiary variables

The regression estimator fits a least-squares model within each stratum on the audit used by the ratio estimator, using basic beneficiary variables and the amount paid. It then predicts every population unit and adds the weighted audit residuals. The additional variables changed little:
- **Part C, PERM, EIPM, and CERT:** Coverage of the gross rate was 23, 23, 23, and 24 of 25. Width and point accuracy were within a few percent of those of the ratio estimator.
- **Part D:** Drug cost and reaching the catastrophic phase explain part of the beneficiary payment error, and the interval narrowed from ±0.67 (ratio) to ±0.58 points. However, coverage fell to 15 of 25, and the point estimate ran 7.8% high on average.

With few large errors in a 990-beneficiary audit, a better-fitting model leaves residuals that understate the true sampling variance. This is the overfitting risk of model-assisted estimation with small samples (McConville et al. 2020). In PERM, all but the largest-payment fee-for-service stratum had too few audited errors for a model and used the intercept-only fallback, which is equivalent to expansion within the stratum.

Across the five programs, regression covered the true gross rate in 108 of 125 audit years (86.4%), as opposed to 111 for the ratio estimator and 121 for the parametric bootstrap.

## 5. Discussion

### 5.1 Principal findings

In five synthetic populations designed after the five CMS improper payment measurements, audit-finding bootstrap simulation produced point estimates as accurate as, or more accurate than, the expansion, ratio, and regression estimators. However, its fixed-rate interval was invalid in every program, covering the truth in 24% of audit years when 95% was intended. This failure is not a tuning problem. Because the audit is never resampled, the interval measures only how the audited rates scatter across the population (as opposed to how much those rates would change with a different audit). Its width also shrinks toward zero as the population grows. Given these findings, any production use of a fixed-rate audit-finding simulation for PIIA intervals should be reviewed.

Redrawing the rates from their binomial sampling distribution before each iteration corrects the interval with a change of a few lines of code and no additional review. This version covered the true gross rate in 96.8% of audit years. Its intervals were 11–21% narrower than those of the ratio estimator in four programs, and much narrower than those of expansion in Part D.

### 5.2 Recommendation

This study recommends that CMS improper payment measurements adopt **bootstrap simulation with parametric rates** for the gross improper payment rate and its interval, with the analytic ratio interval reported alongside it during a transition period. This recommendation rests on three findings:

1. **Validity:** coverage at the nominal level for the gross rate in every program.
2. **Accuracy:** the most accurate point estimates of the methods studied.
3. **Precision:** narrower intervals than the analytic methods from the same audit.

The cost case rests on precision. A narrower interval at the same coverage means that the current precision can be reached with fewer records reviewed. If width scales with 1/√*n*, the parametric method would match the current width of the analytic interval with about:

| Program | Share of the current audit | Audit size |
|---|---|---|
| Part C | 79% | about 780 enrollees instead of 990 |
| EIPM | 80% | about 1,600 applications instead of 2,000 |
| PERM | 63% | about 330 payments per state-year instead of 520 |
| CERT | 62% | about 23,300 claims instead of 37,651 |

This represents a 20–38% reduction in medical record and eligibility reviews, which dominate the cost of each measurement. The projected reduction for Part D is larger still but rests on a weaker comparator (Section 4.3).

These figures are projections (as opposed to demonstrated results), and they apply only to the gross rate. Two conditions should precede any reduction:

- **Confirm coverage at the reduced size.** Coverage must be confirmed directly at the smaller audit sizes (Section 6).
- **Protect sparse components.** Components that CMS reports separately and that rest on few errors (underpayments and technically improper payments) need their own precision check because their coverage was already below nominal under every method.

### 5.3 Implementation

The parametric version runs on the same audit data as the fixed version. It adds two binomial draws per stratum per iteration, and at 1,000 iterations it ran in seconds (EIPM, Part C) to minutes (CERT, 5.3 million claims) on a two-core machine.

The method is fully specified by the audit and the payment function. It can therefore be written into a Sampling and Estimation Methodology Plan and tested by an Inspector General with the same census check used in this study: auditing every unit must return the true rate exactly. Rates with no audited failures stay at zero. This is a conservative choice that keeps the simulation from inventing errors the audit never observed.

### 5.4 Limitations

1. **Number of audit years.** Coverage was estimated from 25 audit years per program. The Monte Carlo standard error is about 4.4 points, so 23/25 and 25/25 are not statistically distinguishable. The consistency across five programs and 22 measures is the stronger evidence, but a larger replication is needed.
2. **Synthetic populations.** The populations are synthetic and calibrated only to public aggregates. It should be clearly noted that:
   - Error mechanisms, partial-error shares, and the independence of errors from payment size within strata are assumptions.
   - Strata the agencies do not publish (EIPM, Part C IPM, and CERT service-level strata) are illustrative.
   - MAC jurisdictions and the CERT Part A-to-B rebilling adjustment are not modeled.
3. **Perfect review.** Review is assumed to be error-free and final, with no appeals.
4. **Part D design differences.** The Part D analytic comparators use a different audit (990 beneficiaries) or a different interval construction (delta method), so the Part D comparisons mix design and estimator.
5. **Fixed error sizes.** The parametric version does not resample the distribution of error sizes. Coverage suggests that this matters little for the gross rate, but it may contribute to the undercoverage of sparse components.
6. **Scope.** This study addresses two-sided PIIA rate intervals. Recovery uses rely on one-sided lower bounds, which were not tested.
