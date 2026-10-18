## 1. Background

### 1.1 Improper payment measurement in CMS programs

The Payment Integrity Information Act of 2019 (PIIA) requires a statistically valid estimate of improper payments for every federal program at risk of significant improper payments. OMB's Appendix C to Circular A-123 sets out how agencies produce it (OMB 2021). The Centers for Medicare & Medicaid Services (CMS) runs five such measurements:

- **Medicare Part C** (the Part C Improper Payment Measure, for Medicare Advantage risk adjustment);
- **Medicare Part D** (the Part D Improper Payment Measure, for prescription drug events);
- **Medicaid and CHIP** (Payment Error Rate Measurement, PERM);
- **Marketplace advance premium tax credits** (Exchange Improper Payment Measurement, EIPM);
- **Medicare fee-for-service** (Comprehensive Error Rate Testing, CERT).

Together these programs reported more than $90 billion in improper payments for FY 2025 (CMS 2025a). Each measurement follows the same three steps:

1. Draw a probability sample (the audit).
2. Establish each sampled unit's payment error by medical or eligibility review.
3. Project the sample errors to the program and attach a 95% confidence interval.

The interval is not a formality. Inspectors General review sampling and estimation plans every year, and interval accuracy is an auditable item: the Department of Education OIG has found estimates unreliable because their confidence intervals were inaccurate (ED OIG 2025). Interval width also sets the cost of measurement. Medical record review is the dominant cost of every program, and audit sizes are chosen to meet precision targets, for example ±3 percentage points at 95% confidence for CERT (CMS 2025b).

### 1.2 Analytic estimators and bootstrap simulation

The standard projection methods are design-based estimators with normal-theory intervals (Cochran 1977):

- **Expansion** weights each sampled error up to the population.
- **Ratio** divides the weighted errors by the weighted payments.
- **Regression** (generalized regression, GREG) calibrates to a known auxiliary such as total payments.

Their intervals rely on a central limit argument that is weakest exactly where improper payment data live. Errors are rare, zero-inflated and right-skewed, and often all-or-nothing (Neter and Loebbecke 1975; Kvanli et al. 1998; Edwards et al. 2023).

A second family of methods simulates instead of projecting. The audit's findings (which HCCs failed, which drug claims were wrong and by how much, which applications were ineligible) are assigned at random to the unaudited units of the whole population, and the program's payment function is rerun. Repeating this many times gives a distribution of improper payments. We call this **audit-finding bootstrap simulation**. Part D's published interval is already simulation based (CMS 2023, 2025c).

The approach is attractive for three reasons:

- **Nonlinear payments.** It reruns the actual payment rules, so effects such as the Part D benefit phases, risk-score hierarchies and the APTC schedule are handled exactly rather than through a linear approximation.
- **Every measure at once.** It gives over-, under-, gross and net payments, and any subgroup, from one set of iterations.
- **Traceability.** Every simulated dollar can be traced to an audited finding.

To our knowledge, the comparative accuracy of these methods, and in particular the validity of the simulation's intervals, has not been tested against a known truth. A companion narrative review sets out each program's design and the evidence on interval accuracy in detail (Cistola 2026).

### 1.3 Why validity is in question

The audit-finding bootstrap differs from the textbook bootstrap (Efron and Tibshirani 1993; Mashreghi et al. 2016) in one respect that matters. It never resamples the audit. Each iteration reuses the same audited findings, and the error rates estimated from them, so the spread across iterations reflects only which unaudited units happen to receive errors. The uncertainty in the rates themselves is not represented, and that is the uncertainty a confidence interval is meant to express: what the audit would have found had a different sample been drawn. Section 4.1 shows that this omission is large and predictable.

## 2. Purpose

This study asks: **what is the comparative accuracy of the available methods for estimating improper payments in federal health programs?** The methods are:

- the three design-based analytic estimators in use (expansion, ratio and regression);
- audit-finding bootstrap simulation.

Accuracy has two parts:

- **Point accuracy:** how close the point estimate is to the true improper payment.
- **Interval accuracy:** whether the 95% interval contains the truth in about 95% of repeated audits (coverage) and, among intervals that do, how narrow it is (width). A narrower valid interval is more accurate, because the same precision can then be bought with a smaller, cheaper audit.

The specific aims are to:

1. measure the point and interval accuracy of each method in five synthetic populations designed after the five CMS measurements;
2. explain any failure of the bootstrap simulation interval;
3. test a parametric alternative that corrects it;
4. judge whether the most accurate method could support smaller audits.

Recovery uses of extrapolation (contract-level RADV demands and provider overpayment demands) are out of scope.

## 3. Methods

### 3.1 Study design

This is a Monte Carlo validation study in the design of Edwards et al. (2023):

1. **Population.** For each program, a synthetic population is built and errors are fabricated on it with stated probabilities. The true improper payment is therefore known to the cent.
2. **Audit years.** The program's production audit design is then applied 25 times, each time drawing an independent sample. Each draw is an **audit year**, so the 25 draws show how each estimator behaves when the audit is repeated.
3. **One audit per year.** Each audit year has exactly one audit, and every method gets only that audit. The analytic methods estimate their variance from it. The bootstrap simulation assigns its findings exactly as audited.

All methods are scored on the same 25 audit years. An interval is counted as containing the truth if *lower* ≤ *θ* ≤ *upper*. With 25 audit years, 24 of 25 is the nearest count to the nominal 95% (23.75), and the Monte Carlo standard error of a coverage estimate near 95% is about 4.4 percentage points.

No real data are used. Populations are calibrated only to public aggregate results (Appendix A). Every number in this paper can be regenerated from the public repository (Data and code availability).

### 3.2 Synthetic populations

Table 1 summarizes the five populations; Appendix B gives every assumption.

**Table 1. Populations, audits and true gross improper payment rates**

| Program | Unit (synthetic count; scale) | Payment function | Errors fabricated | Production-like audit per audit year | True gross rate |
|---|---|---|---|---|---|
| Part C | Enrollee (330,253; ×100) | Risk score × county rate × months, with HCC hierarchies | HCCs deleted or moved down the hierarchy, missing documentation (all HCCs lost), HCCs supported but not coded (underpayments) | 990 enrollees, 330 per risk-score tercile | 6.06% |
| Part D | Beneficiary and PDE (108,000; 4.5M PDEs; ×500) | CY 2025 post-IRA standard benefit: reinsurance and low-income cost sharing | Gross drug cost errors on PDEs: 90% full, 10% partial in either direction; 10% of long-term-care PDEs, 2.5% of others | 5,000 PDEs (3 strata, Neyman); ratio and regression use 990 beneficiaries | 1.38% |
| PERM | Payment (3.09M in 9 states; ×200) | Federal share of FFS claims and capitations | Claims-review errors (all-or-nothing or partial) and beneficiary eligibility errors (true state rates 2–4%) | 520 payments per state, payment type × 5 payment quintiles, Neyman, systematic | 6.09% |
| EIPM | Application (142,152; ×100) | APTC under the enhanced applicable-percentage schedule | Overpayments only: technically improper (whole APTC) and monetary (income understated) | 2,000 applications, 5 APTC quintiles, Neyman | 0.92% |
| CERT | Claim (5.34M; ×200) | Claim payment by claim type | Whole-claim and partial overpayments and coding underpayments, calibrated by claim type | 37,651 claims (FY 2025 count per claim type), 5 payment quintiles per type, Neyman | 6.50% |

Each population is calibrated to its FY 2025 public results where those exist:

- Part C: 6.09%; overpayments $21.43B and underpayments $2.23B.
- Medicaid: 6.12%.
- EIPM: 0.89%, of which 0.43 points was technically improper.
- CERT: 6.55% overall, with each of the four claim types matched.

Part D is set below its published 4.00% so that the method is tested in a lower-error regime. Strata that CMS does not publish are illustrative and labeled as such: the EIPM strata, the Part C IPM strata and CERT's service-level strata.

### 3.3 Estimands

**Netting and measures.** For each program the payment error is netted within the payment unit first: the enrollee, beneficiary, payment, application or claim. Then:

- over = Σ max(*y*, 0)
- under = Σ max(−*y*, 0)
- gross = over + under
- net = over − under

Every measure is estimated in dollars with its interval and then divided by the known total payments *X*. The gross rate is the PIIA estimand and the primary outcome. PERM and EIPM errors are all overpayments, so their components are reported instead of over and under: eligibility and claims for PERM, technically improper and monetary for EIPM. CERT also reports gross by claim type.

### 3.4 Analytic estimators

The three analytic estimators use the program's stratified design. Let *N_h*, *n_h* and *w_h = N_h/n_h* be stratum sizes and weights, and let *T̂_y = Σ_h w_h Σ y* and *T̂_x* be the weighted totals. Then:

- **Expansion:** *θ̂ = T̂_y / X*.
- **Ratio:** *θ̂ = T̂_y / T̂_x*.
- **Regression (GREG):** *θ̂ = [T̂_y + b(X − T̂_x)] / X*, with *b* the weighted least-squares slope of *y* on *x* with an intercept.

Variances use the stratified-SRS formula with finite population correction on *y*, on the ratio residual *y − θ̂x*, or on the regression residual (Taylor linearization). Each method reports *θ̂ ± 1.96·SE*.

Two program-specific forms apply:

- **Part C expansion** works in risk-score units: the mean audited over- and under-risk-score error in each tercile × the tercile's size × the national mean county rate × months.
- **Part D expansion** applies each stratum's audited PDE error rate to every PDE in the population, reruns the benefit, and uses a delta-method interval: each stratum's rate is moved by ±1 SE and the benefit is rerun each way.

### 3.5 Audit-finding bootstrap simulation (fixed rates)

Within each donor kind *k*, take the audit's *n_k* audited units:

- *f_k* of them are in error;
- *g_k* of those errors are partial, with sizes *s_1, …, s_{g_k}*.

The donor kind is the sampling stratum. In Part C it is the HCC (20 HCC failure rates and 10 family addition rates).

In each of 1,000 iterations:

1. Every non-audited unit of kind *k* is in error with probability *p_k = f_k/n_k*.
2. Given an error, it is partial with probability *q_k = g_k/f_k*, with its size drawn uniformly from the audited partial sizes. Otherwise it is a whole error.
3. Audited units keep their own findings.
4. The payment function is rerun for every unit, and the measures are summed.

These two steps are the same as giving every unit the finding of a uniformly drawn audited donor of its kind. They only touch units that receive an error, so a 5-million-claim iteration takes milliseconds.

The estimate is the mean of the iteration rates, and the interval is their 2.5th and 97.5th percentiles. When every unit is audited, every iteration returns the exact true rate; this is tested. In Part D, all PDEs of the full population are simulated and the benefit is rerun for every beneficiary.

### 3.6 The parametric-rate alternative

The parametric version changes only one thing. Before each iteration, the rates are redrawn from their sampling distribution given the audit:

*p̃_k = Binomial(n_k, p_k)/n_k*, *q̃_k = Binomial(f_k, q_k)/f_k*

Steps 1–4 then run with *p̃_k* and *q̃_k*. Each iteration therefore represents a different plausible audit outcome as well as a different assignment. Rates with no audited failures stay at zero: no failures are extrapolated to HCCs the audit never saw. Partial sizes are still drawn from the audited list.

This is a parametric bootstrap of the rate parameters (Efron and Tibshirani 1993, ch. 6), applied inside the simulation. We call the two versions **bootstrap simulation (fixed rates)** and **bootstrap simulation (parametric rates)**. It is not a Bayesian bootstrap, and it needs no prior.

### 3.7 Outcomes

For each program, measure and method, over the 25 audit years:

- **Coverage:** the number of intervals containing the truth, and how many lie entirely above or entirely below it.
- **Width:** the median 95% interval half-width, in percentage points of payments and in national dollars.
- **Point accuracy:** the median point estimate, and the mean absolute and mean signed error relative to the true rate.

For the audit-size question, we compare the parametric interval with the analytic interval from the same audit:

- the ratio estimator for Part C, PERM, EIPM and CERT;
- expansion for Part D, the analytic method that uses the same PDE audit.

If interval width scales with 1/√*n*, the audit size at which the parametric method would match the analytic width is (*w_parametric / w_analytic*)² of the current audit.
