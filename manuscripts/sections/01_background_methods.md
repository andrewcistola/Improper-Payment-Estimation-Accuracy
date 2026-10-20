## 1. Background

### 1.1 Improper payment measurement in CMS programs

The Payment Integrity Information Act of 2019 (PIIA) requires a statistically valid estimate of improper payments for every federal program at risk of significant improper payments. Appendix C to the Office of Management and Budget (OMB) Circular A-123 sets out how agencies produce this estimate (OMB 2021). The Centers for Medicare & Medicaid Services (CMS) runs five such measurements:

- **Medicare Part C** (the Part C Improper Payment Measure, for Medicare Advantage risk adjustment);
- **Medicare Part D** (the Part D Improper Payment Measure, for prescription drug events);
- **Medicaid and CHIP** (Payment Error Rate Measurement, PERM);
- **Marketplace advance premium tax credits** (Exchange Improper Payment Measurement, EIPM);
- **Medicare fee-for-service** (Comprehensive Error Rate Testing, CERT).

Together, these programs reported more than $90 billion in improper payments for FY 2025 (CMS 2025a). Each measurement follows the same three steps:

1. Draw a probability sample (the audit).
2. Establish the payment error for each sampled unit through medical or eligibility review.
3. Project the sample errors to the program and attach a 95% confidence interval.

The interval is not a formality. Inspectors General review sampling and estimation plans every year, and interval accuracy is an auditable item. For example, the Department of Education Office of Inspector General (OIG) has found estimates unreliable because their confidence intervals were inaccurate (ED OIG 2025). Interval width also sets the cost of measurement. Medical record review is the dominant cost of every program, and audit sizes are chosen to meet precision targets (for example, ±3 percentage points at 95% confidence for CERT; CMS 2025b).

### 1.2 Analytic estimators and bootstrap simulation

The standard projection methods are design-based estimators with normal-theory intervals (Cochran 1977):

- **Expansion** weights each sampled error up to the population.
- **Ratio** divides the weighted errors by the weighted payments.
- **Regression** fits a model of the error on characteristics known for every unit, predicts the whole population, and adds the weighted sample residuals (model-assisted estimation; Särndal et al. 1992).

The intervals for these estimators rely on a central limit argument that is weakest exactly where improper payment data are found. Errors are rare, zero-inflated, right-skewed, and often all-or-nothing (Neter and Loebbecke 1975; Kvanli et al. 1998; Edwards et al. 2023).

A second family of methods simulates (as opposed to projects). The audit findings (which HCCs failed, which drug claims were wrong and by how much, and which applications were ineligible) are assigned at random to the unaudited units of the whole population, and the program's payment function is rerun. Repeating this process many times produces a distribution of improper payments. This study calls this approach **audit-finding bootstrap simulation**. The published Part D interval is already simulation based (CMS 2023, 2025c).

This approach is attractive for three reasons:

- **Nonlinear payments.** The simulation reruns the actual payment rules, so effects such as the Part D benefit phases, risk-score hierarchies, and the APTC schedule are handled exactly (as opposed to through a linear approximation).
- **Every measure at once.** One set of iterations produces over-, under-, gross, and net payments, along with any subgroup.
- **Traceability.** Every simulated dollar can be traced to an audited finding.

To the author's knowledge, the comparative accuracy of these methods (and in particular the validity of the simulation intervals) has not been tested against a known truth. A companion narrative review describes the design of each program and the evidence on interval accuracy in detail (Cistola 2026).

### 1.3 Why validity is in question

The audit-finding bootstrap differs from the textbook bootstrap (Efron and Tibshirani 1993; Mashreghi et al. 2016) in one important respect: it never resamples the audit. Each iteration reuses the same audited findings, and the error rates estimated from them, so the spread across iterations reflects only which unaudited units happen to receive errors. The uncertainty in the rates themselves is not represented. However, this is the uncertainty a confidence interval is meant to express, namely what the audit would have found had a different sample been drawn. Section 4.1 shows that this omission is large and predictable.

## 2. Purpose

The purpose of this study is to compare the accuracy of **available methods for estimating improper payments in federal health programs**. The methods are:

- three design-based analytic estimators (expansion, ratio, and a model-assisted regression estimator);
- audit-finding bootstrap simulation.

In this study, accuracy has two parts:

- **Point accuracy:** how close the point estimate is to the true improper payment.
- **Interval accuracy:** whether the 95% interval contains the truth in about 95% of repeated audits (coverage) and, among intervals that do, how narrow the interval is (width). A narrower valid interval is more accurate because the same precision can then be achieved with a smaller and less costly audit.

The specific aims of this study are to:

1. measure the point and interval accuracy of each method in five synthetic populations designed after the five CMS measurements;
2. explain any failure of the bootstrap simulation interval;
3. test a parametric alternative that corrects this failure;
4. determine whether the most accurate method could support smaller audits.

Recovery uses of extrapolation (contract-level RADV demands and provider overpayment demands) are out of scope.

## 3. Methods

### 3.1 Study design

This study is a Monte Carlo validation study that follows the design of Edwards et al. (2023):

1. **Population.** For each program, a synthetic population is built, and errors are fabricated on it with stated probabilities. The true improper payment is therefore known to the cent.
2. **Audit years.** The program's production audit design is then applied 25 times, each time drawing an independent sample. Each draw is an **audit year**, so the 25 draws show how each estimator behaves when the audit is repeated.
3. **One audit per year.** Each audit year has exactly one audit, and every method uses only that audit. The analytic methods estimate their variance from this audit. The bootstrap simulation assigns the audit findings exactly as audited.

All methods are scored on the same 25 audit years. An interval is counted as containing the truth if *lower* ≤ *θ* ≤ *upper*. With 25 audit years, 24 of 25 is the nearest count to the nominal 95% (23.75), and the Monte Carlo standard error of a coverage estimate near 95% is about 4.4 percentage points.

This study uses no real data. Populations are calibrated only to public aggregate results (Appendix A). Every number in this paper can be regenerated from the public repository (Data and code availability).

### 3.2 Synthetic populations

Table 1 summarizes the five populations, and Appendix B provides every assumption.

**Table 1. Populations, audits and true gross improper payment rates**

| Program | Unit (synthetic count; scale) | Payment function | Errors fabricated | Production-like audit per audit year | True gross rate |
|---|---|---|---|---|---|
| Part C | Enrollee (330,253; ×100) | Risk score × county rate × months, with HCC hierarchies | HCCs deleted or moved down the hierarchy, missing documentation (all HCCs lost), HCCs supported but not coded (underpayments) | 990 enrollees, 330 per risk-score tercile | 6.06% |
| Part D | Beneficiary and PDE (108,000; 4.5M PDEs; ×500) | CY 2025 post-IRA standard benefit: reinsurance and low-income cost sharing | Gross drug cost errors on PDEs: 90% full, 10% partial in either direction; 10% of long-term-care PDEs, 2.5% of others | 5,000 PDEs (3 strata, Neyman); ratio and regression use 990 beneficiaries | 1.38% |
| PERM | Payment (3.09M in 9 states; ×200) | Federal share of FFS claims and capitations | Claims-review errors (all-or-nothing or partial) and beneficiary eligibility errors (true state rates 2–4%) | 520 payments per state, payment type × 5 payment quintiles, Neyman, systematic | 6.09% |
| EIPM | Application (142,152; ×100) | APTC under the enhanced applicable-percentage schedule | Overpayments only: technically improper (whole APTC) and monetary (income understated) | 2,000 applications, 5 APTC quintiles, Neyman | 0.92% |
| CERT | Claim (5.34M; ×200) | Claim payment by claim type | Whole-claim and partial overpayments and coding underpayments, calibrated by claim type | 37,651 claims (FY 2025 count per claim type), 5 payment quintiles per type, Neyman | 6.50% |

Each population is calibrated to its FY 2025 public results where those results exist:

- Part C: 6.09%; overpayments $21.43B and underpayments $2.23B.
- Medicaid: 6.12%.
- EIPM: 0.89%, of which 0.43 points was technically improper.
- CERT: 6.55% overall, with each of the four claim types matched.

Part D is set below its published 4.00% so that the methods are tested in a lower-error setting. Strata that CMS does not publish (the EIPM strata, the Part C IPM strata, and the CERT service-level strata) are illustrative and labeled as such.

### 3.3 Estimands

**Netting and measures.** For each program, the payment error is first netted within the payment unit (the enrollee, beneficiary, payment, application, or claim). The measures are then defined as:

- over = Σ max(*y*, 0)
- under = Σ max(−*y*, 0)
- gross = over + under
- net = over − under

Every measure is estimated in dollars with its interval and then divided by the known total payments *X*. The gross rate is the PIIA estimand and the primary outcome. Because PERM and EIPM errors are all overpayments, their components are reported instead of over and under (eligibility and claims for PERM; technically improper and monetary for EIPM). CERT also reports gross by claim type.

### 3.4 Analytic estimators

The three analytic estimators use the program's stratified design. Let *N_h*, *n_h*, and *w_h = N_h/n_h* be the stratum sizes and weights, and let *T̂_y = Σ_h w_h Σ y* and *T̂_x* be the weighted totals. The estimators are:

- **Expansion:** *θ̂ = T̂_y / X*.
- **Ratio:** *θ̂ = T̂_y / T̂_x*.
- **Regression (model-assisted):** Within each model stratum *m*, the audited *y* is regressed by design-weighted least squares on an intercept and the unit's predictors **z** (basic beneficiary variables plus the amount paid). The fitted models predict every population unit, and the estimate adds the weighted audit residuals: *θ̂ = [Σ_U ŷ + Σ_s w (y − ŷ)] / X*. The predictors are:
  - Part C: payment, demographic score, months enrolled, and number of HCCs, within risk-score terciles.
  - Part D: Medicare payment, gross drug cost, number of PDEs, and reaching the catastrophic phase, within post-strata (long-term care, low-income subsidy, other).
  - PERM: amount paid, month, and the beneficiary's number of payments and total paid.
  - EIPM: APTC, age, household size, income, and months.
  - CERT: amount paid (the claims carry no beneficiary variables).

  The model is fit on the same audit as the ratio estimator (for Part D, the 990-beneficiary audit). A stratum with fewer than 10 audited errors, or with too few units for the model, uses an intercept-only model, which is equivalent to expansion within that stratum. This approach follows model-assisted estimation as used in forest inventory (McConville et al. 2020) and model-based extrapolation of random audits in tax-gap estimation (Johns and Rosenbaum 2024).

Variances use the stratified-SRS formula with a finite population correction applied to *y* (expansion), to the ratio residual *y − θ̂x* (ratio), or to the model residual *y − ŷ* (regression), all from the single audit. Expansion and ratio report *θ̂ ± 1.96·SE*. Regression uses a *t* multiplier, with degrees of freedom reduced by the strata and model terms fitted.

Two program-specific forms apply:

- **Part C expansion** works in risk-score units. The mean audited over- and under-risk-score error in each tercile is multiplied by the tercile's size, the national mean county rate, and months.
- **Part D expansion** applies the audited PDE error rate for each stratum to every PDE in the population, reruns the benefit, and uses a delta-method interval. Each stratum's rate is moved by ±1 SE, and the benefit is rerun each way.

### 3.5 Audit-finding bootstrap simulation (fixed rates)

Within each donor kind *k*, take the *n_k* audited units from the audit:

- *f_k* of them are in error;
- *g_k* of those errors are partial, with sizes *s_1, …, s_{g_k}*.

The donor kind is the sampling stratum. In Part C, the donor kind is the HCC (20 HCC failure rates and 10 family addition rates).

In each of 1,000 iterations:

1. Every non-audited unit of kind *k* is in error with probability *p_k = f_k/n_k*.
2. Given an error, the unit is partial with probability *q_k = g_k/f_k*, with its size drawn uniformly from the audited partial sizes. Otherwise, the error is whole.
3. Audited units keep their own findings.
4. The payment function is rerun for every unit, and the measures are summed.

Steps 1 and 2 are equivalent to giving every unit the finding of a uniformly drawn audited donor of its kind. These steps only touch units that receive an error, so a 5-million-claim iteration takes milliseconds.

The estimate is the mean of the iteration rates, and the interval is their 2.5th and 97.5th percentiles. When every unit is audited, every iteration returns the exact true rate (this property is tested). In Part D, all PDEs of the full population are simulated, and the benefit is rerun for every beneficiary.

### 3.6 The parametric-rate alternative

The parametric version changes only one thing. Before each iteration, the rates are redrawn from their sampling distribution given the audit:

*p̃_k = Binomial(n_k, p_k)/n_k*, *q̃_k = Binomial(f_k, q_k)/f_k*

Steps 1–4 then run with *p̃_k* and *q̃_k*. Each iteration therefore represents a different plausible audit outcome in addition to a different assignment. Rates with no audited failures stay at zero, so no failures are extrapolated to HCCs the audit never observed. Partial sizes are still drawn from the audited list.

This version is a parametric bootstrap of the rate parameters (Efron and Tibshirani 1993, ch. 6) applied inside the simulation. This study calls the two versions **bootstrap simulation (fixed rates)** and **bootstrap simulation (parametric rates)**. The parametric version is not a Bayesian bootstrap and requires no prior.

### 3.7 Outcomes

For each program, measure, and method, the following outcomes are calculated over the 25 audit years:

- **Coverage:** the number of intervals containing the truth, and how many lie entirely above or entirely below it.
- **Width:** the median 95% interval half-width, in percentage points of payments and in national dollars.
- **Point accuracy:** the median point estimate, and the mean absolute and mean signed error relative to the true rate.

To address the audit-size question, this study compares the parametric interval with the analytic interval from the same audit:

- the ratio estimator for Part C, PERM, EIPM, and CERT;
- expansion for Part D (the analytic method that uses the same PDE audit).

If interval width scales with 1/√*n*, the audit size at which the parametric method would match the analytic width is (*w_parametric / w_analytic*)² of the current audit.
