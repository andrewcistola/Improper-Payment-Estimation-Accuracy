# Part D under the pre-IRA benefit (reference)

A robustness check, not part of the reported results. The same synthetic population, the same PDE errors and the same 25 audit years as the reported Part D results are re-run with Medicare's payment computed under the **pre-IRA CY 2023 standard benefit** instead of the post-IRA CY 2025 benefit. The question is whether the methods compare the same way when the payment rules, and with them the size and distribution of the payment error, change. The README tables and `shared/report.yaml` are unchanged and use the post-IRA results.

## Benefit designs

| | Post-IRA, CY 2025 (reported) | Pre-IRA, CY 2023 (this reference) |
|---|---|---|
| Deductible | $590 | $505 |
| Initial coverage | 25% enrollee; plan 65% and manufacturer 10% (brand) or plan 75% (generic) | 25% enrollee, 75% plan, to $4,660 total drug cost |
| Coverage gap | None | Non-LIS: 25% enrollee; brand 70% manufacturer discount and 5% plan; generic 75% plan. LIS: 100% standard share, paid by LICS except the copay |
| Catastrophic threshold | $2,000 out of pocket | $7,400 true out of pocket (manufacturer discount counts) |
| Catastrophic phase | Enrollee 0; plan 60%; manufacturer 20% (brand); Medicare reinsurance 20% (brand) / 40% (generic) | Enrollee 5% (LIS: 0, paid by LICS); plan 15%; Medicare reinsurance 80% |
| LIS copays | $4.90 generic / $12.15 brand | $4.15 generic / $10.35 brand |

Code: `errors/pre_ira.yaml` → `errors/sql/05_benefit_pre_ira.sql` (population) and `estimation/pre_ira.yaml` (estimation; `medicare_cents_pre_ira` in `estimation/simulation.py`, tested to reproduce the SQL to the cent). Simplification: the catastrophic minimum copays ($4.15 / $10.35) are not applied; enrollee coinsurance there is 5%.

## Populations

| | Post-IRA (reported) | Pre-IRA (reference) |
|---|---|---|
| Total payments (national) | $105.56B | $105.56B |
| Reinsurance | $32.81B | $52.60B |
| Low-income cost sharing | $11.94B | $20.35B |
| Direct subsidy | $60.81B | $32.61B |
| True overpayments | $1.44B | $2.96B |
| True underpayments | $0.02B | $0.03B |
| True gross rate | 1.38% | 2.83% |
| Beneficiaries with a payment error | 19.81% | 14.32% |
| Beneficiaries reaching the catastrophic phase | 14.04% | 5.18% |

PDE error rates are identical in both (10% of LTC claims, 2.5% of others; 90% full errors). The pre-IRA payment error is about twice as large because Medicare reinsurance pays 80% of catastrophic costs and LICS covers LIS cost sharing through the coverage gap; fewer beneficiaries have a payment error because a non-LIS enrollee's error below the catastrophic threshold changes only plan and enrollee liability.

## Gross improper payment rate (25 audit years)

Median point estimate and median 95% half-width; coverage = audit years with the truth inside the interval (in parentheses, intervals entirely above / below the truth).

| Method | Post-IRA: estimate (truth 1.38%) | Post-IRA: half-width | Post-IRA: coverage | Pre-IRA: estimate (truth 2.83%) | Pre-IRA: half-width | Pre-IRA: coverage |
|---|---|---|---|---|---|---|
| Expansion | 1.22% | ±0.60 | 18/25 (0/7) | 2.49% | ±1.20 | 19/25 (0/6) |
| Ratio | 1.41% | ±0.67 | 18/25 (1/6) | 2.55% | ±1.32 | 18/25 (1/6) |
| Regression | 1.44% | ±0.58 | 15/25 (4/6) | 3.14% | ±1.14 | 15/25 (4/6) |
| Bootstrap (fixed rates) | 1.38% | ±0.06 | 10/25 (8/7) | 2.82% | ±0.13 | 11/25 (7/7) |
| Bootstrap (parametric rates) | 1.38% | ±0.22 | 25/25 (0/0) | 2.81% | ±0.44 | 25/25 (0/0) |

## Every measure, pre-IRA (25 audit years)

| Measure | True | Method | Median estimate | Median half-width | Coverage | Mean absolute error (% of truth) |
|---|---|---|---|---|---|---|
| Overpayments | $2.96B (2.80%) | Expansion | $2.63B (2.49%) | ±$1.27B | 19/25 (0/6) | 30.7% |
|  |  | Ratio | $2.64B (2.50%) | ±$1.40B | 18/25 (1/6) | 25.9% |
|  |  | Regression | $3.29B (3.12%) | ±$1.21B | 15/25 (4/6) | 33.4% |
|  |  | Bootstrap (fixed rates) | $2.95B (2.79%) | ±$0.14B | 12/25 (6/7) | 6.4% |
|  |  | Bootstrap (parametric rates) | $2.94B (2.79%) | ±$0.47B | 23/25 (0/2) | 6.4% |
| Underpayments | $0.03B (0.03%) | Expansion | $0.00B (0.00%) | ±$0.00B | 0/25 (0/25) | 100.0% |
|  |  | Ratio | $0.01B (0.01%) | ±$0.02B | 10/25 (0/15) | 90.3% |
|  |  | Regression | $0.01B (0.01%) | ±$0.01B | 8/25 (1/16) | 97.1% |
|  |  | Bootstrap (fixed rates) | $0.04B (0.04%) | ±$0.01B | 12/25 (11/2) | 52.6% |
|  |  | Bootstrap (parametric rates) | $0.04B (0.04%) | ±$0.03B | 21/25 (4/0) | 53.0% |
| Gross | $2.99B (2.83%) | Expansion | $2.63B (2.49%) | ±$1.27B | 19/25 (0/6) | 30.6% |
|  |  | Ratio | $2.69B (2.55%) | ±$1.40B | 18/25 (1/6) | 25.3% |
|  |  | Regression | $3.32B (3.14%) | ±$1.21B | 15/25 (4/6) | 32.9% |
|  |  | Bootstrap (fixed rates) | $2.97B (2.82%) | ±$0.14B | 11/25 (7/7) | 6.4% |
|  |  | Bootstrap (parametric rates) | $2.97B (2.81%) | ±$0.47B | 25/25 (0/0) | 6.4% |
| Net | $2.92B (2.77%) | Expansion | $2.63B (2.49%) | ±$1.27B | 19/25 (0/6) | 30.8% |
|  |  | Ratio | $2.64B (2.50%) | ±$1.41B | 18/25 (1/6) | 26.5% |
|  |  | Regression | $3.17B (3.00%) | ±$1.21B | 15/25 (4/6) | 33.9% |
|  |  | Bootstrap (fixed rates) | $2.91B (2.76%) | ±$0.14B | 13/25 (5/7) | 6.5% |
|  |  | Bootstrap (parametric rates) | $2.91B (2.76%) | ±$0.46B | 23/25 (0/2) | 6.4% |

## Coverage of every measure: post-IRA vs pre-IRA

| Measure | Expansion | Ratio | Regression | Bootstrap (fixed rates) | Bootstrap (parametric rates) |
|---|---|---|---|---|---|
| Overpayments, Post-IRA | 18/25 | 18/25 | 16/25 | 9/25 | 25/25 |
| Overpayments, Pre-IRA | 19/25 | 18/25 | 15/25 | 12/25 | 23/25 |
| Underpayments, Post-IRA | 0/25 | 15/25 | 13/25 | 10/25 | 20/25 |
| Underpayments, Pre-IRA | 0/25 | 10/25 | 8/25 | 12/25 | 21/25 |
| Gross, Post-IRA | 18/25 | 18/25 | 15/25 | 10/25 | 25/25 |
| Gross, Pre-IRA | 19/25 | 18/25 | 15/25 | 11/25 | 25/25 |
| Net, Post-IRA | 19/25 | 19/25 | 16/25 | 11/25 | 24/25 |
| Net, Pre-IRA | 19/25 | 18/25 | 15/25 | 13/25 | 23/25 |

## Conclusion

The methods compare the same way under both benefit designs. Under the pre-IRA benefit, the true gross rate doubles (1.38% to 2.83%), and every interval roughly doubles in width with it. The ranking is unchanged:
- **Parametric-rate bootstrap:** contains the true gross rate in 25 of 25 audit years, with a median half-width of ±0.44 points, against ±1.32 for the ratio estimator.
- **Analytic estimators:** cover in 15–19 of 25.
- **Fixed-rate bootstrap:** remains far too narrow (11 of 25).
- **Underpayments:** stay hard for every method.

The study's conclusions about Part D do not depend on the benefit design.
