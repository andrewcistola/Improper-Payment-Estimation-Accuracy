**Table D1. Interval calibration over 100 audit years (base populations, gross rate)**

| Program | Method | Audit years | True rate | Mean estimate | MAE (% of truth) | SD of estimate (pts) | Mean half-width (pts) | Half-width ÷ 1.96·SD | Coverage |
|---|---|---|---|---|---|---|---|---|---|
| Part C | Expansion | 100 | 6.06% | 6.06% | 7.0% | 0.540 | 1.068 | 1.01 | 95/100 |
|  | Ratio | 100 | 6.06% | 6.05% | 6.8% | 0.518 | 1.063 | 1.05 | 97/100 |
|  | Regression | 100 | 6.06% | 6.05% | 6.9% | 0.518 | 1.034 | 1.02 | 96/100 |
|  | Simulation (parametric rates) | 100 | 6.06% | 6.06% | 6.8% | 0.500 | 0.922 | 0.94 | 95/100 |
| Part D | Expansion | 100 | 1.38% | 1.37% | 32.6% | 0.579 | 0.828 | 0.73 | 76/100 |
|  | Ratio | 100 | 1.38% | 1.36% | 22.3% | 0.410 | 0.668 | 0.83 | 82/100 |
|  | Regression | 100 | 1.38% | 1.38% | 22.0% | 0.385 | 0.514 | 0.68 | 76/100 |
|  | PDE expansion (marginal) | 100 | 1.38% | 1.40% | 51.7% | 0.953 | 1.291 | 0.69 | 67/100 |
|  | PDE ratio (marginal) | 100 | 1.38% | 1.40% | 51.2% | 0.927 | 1.265 | 0.70 | 68/100 |
|  | Simulation (parametric rates) | 100 | 1.38% | 1.36% | 6.9% | 0.114 | 0.213 | 0.95 | 95/100 |
| PERM | Expansion | 100 | 6.09% | 6.00% | 6.0% | 0.449 | 0.830 | 0.94 | 91/100 |
|  | Ratio | 100 | 6.09% | 6.00% | 6.0% | 0.446 | 0.818 | 0.94 | 91/100 |
|  | Regression | 100 | 6.09% | 6.00% | 5.9% | 0.438 | 0.791 | 0.92 | 91/100 |
|  | Simulation (parametric rates) | 100 | 6.09% | 6.05% | 4.6% | 0.345 | 0.630 | 0.93 | 92/100 |
| EIPM | Expansion | 100 | 0.92% | 0.90% | 16.2% | 0.191 | 0.362 | 0.97 | 92/100 |
|  | Ratio | 100 | 0.92% | 0.90% | 16.1% | 0.191 | 0.362 | 0.97 | 92/100 |
|  | Regression | 100 | 0.92% | 0.90% | 16.4% | 0.193 | 0.361 | 0.95 | 92/100 |
|  | Simulation (parametric rates) | 100 | 0.92% | 0.89% | 16.2% | 0.184 | 0.316 | 0.88 | 90/100 |
| CERT | Expansion | 100 | 6.50% | 6.52% | 2.4% | 0.186 | 0.376 | 1.03 | 96/100 |
|  | Ratio | 100 | 6.50% | 6.53% | 2.5% | 0.192 | 0.370 | 0.98 | 95/100 |
|  | Regression | 100 | 6.50% | 6.53% | 2.5% | 0.194 | 0.368 | 0.97 | 93/100 |
|  | Simulation (parametric rates) | 100 | 6.50% | 6.52% | 1.6% | 0.125 | 0.276 | 1.13 | 99/100 |

*SD of estimate = standard deviation of the point estimate across audit years (percentage points). Half-width ÷ 1.96·SD near 1 means the interval matches the estimator's own sampling variability; below 1, the interval is too narrow. Monte Carlo SE of coverage at 95% with 100 audit years: 2.2 points. Bootstrap simulation run at 500 iterations per audit year.*

**Table D2. Size-dependent error probability, size_beta = +0.5 (25 audit years, gross rate)**

| Program | Method | Audit years | True rate | Mean estimate | MAE (% of truth) | SD of estimate (pts) | Mean half-width (pts) | Half-width ÷ 1.96·SD | Coverage |
|---|---|---|---|---|---|---|---|---|---|
| Part C | Expansion | 25 | 6.04% | 5.83% | 7.4% | 0.506 | 1.114 | 1.12 | 24/25 |
|  | Ratio | 25 | 6.04% | 6.05% | 6.7% | 0.526 | 1.140 | 1.11 | 25/25 |
|  | Regression | 25 | 6.04% | 6.07% | 7.1% | 0.556 | 1.058 | 0.97 | 23/25 |
|  | Simulation (parametric rates) | 25 | 6.04% | 5.86% | 6.5% | 0.468 | 0.916 | 1.00 | 24/25 |
| Part D | Expansion | 25 | 1.41% | 1.04% | 37.6% | 0.526 | 0.762 | 0.74 | 15/25 |
|  | Ratio | 25 | 1.41% | 1.52% | 30.4% | 0.567 | 0.846 | 0.76 | 22/25 |
|  | Regression | 25 | 1.41% | 1.58% | 34.2% | 0.597 | 0.667 | 0.57 | 18/25 |
|  | PDE expansion (marginal) | 25 | 1.41% | 1.18% | 45.0% | 0.744 | 1.225 | 0.84 | 17/25 |
|  | PDE ratio (marginal) | 25 | 1.41% | 1.20% | 45.3% | 0.761 | 1.220 | 0.82 | 17/25 |
|  | Simulation (parametric rates) | 25 | 1.41% | 0.49% | 64.9% | 0.071 | 0.130 | 0.94 | 0/25 |
| PERM | Expansion | 25 | 6.10% | 6.18% | 6.4% | 0.511 | 1.045 | 1.04 | 25/25 |
|  | Ratio | 25 | 6.10% | 6.18% | 6.3% | 0.507 | 1.005 | 1.01 | 25/25 |
|  | Regression | 25 | 6.10% | 6.16% | 6.4% | 0.516 | 0.906 | 0.90 | 23/25 |
|  | Simulation (parametric rates) | 25 | 6.10% | 5.26% | 13.8% | 0.330 | 0.588 | 0.91 | 6/25 |
| EIPM | Expansion | 25 | 0.93% | 0.87% | 17.6% | 0.190 | 0.351 | 0.94 | 23/25 |
|  | Ratio | 25 | 0.93% | 0.87% | 17.6% | 0.190 | 0.350 | 0.94 | 23/25 |
|  | Regression | 25 | 0.93% | 0.87% | 17.6% | 0.190 | 0.350 | 0.94 | 23/25 |
|  | Simulation (parametric rates) | 25 | 0.93% | 0.85% | 17.8% | 0.179 | 0.307 | 0.87 | 21/25 |
| CERT | Expansion | 25 | 6.44% | 6.45% | 2.5% | 0.199 | 0.494 | 1.27 | 25/25 |
|  | Ratio | 25 | 6.44% | 6.45% | 2.5% | 0.199 | 0.474 | 1.22 | 25/25 |
|  | Regression | 25 | 6.44% | 6.46% | 2.5% | 0.206 | 0.452 | 1.12 | 25/25 |
|  | Simulation (parametric rates) | 25 | 6.44% | 5.05% | 21.5% | 0.084 | 0.250 | 1.52 | 0/25 |

*Each unit's error probability is multiplied by (payment / stratum mean payment)^+0.5, capped at 0.95, before calibration to the same public targets; designs, audit sizes and methods are unchanged. Bootstrap simulation run at 500 iterations per audit year.*

**Table D3. Size-dependent error probability, size_beta = -0.5 (25 audit years, gross rate)**

| Program | Method | Audit years | True rate | Mean estimate | MAE (% of truth) | SD of estimate (pts) | Mean half-width (pts) | Half-width ÷ 1.96·SD | Coverage |
|---|---|---|---|---|---|---|---|---|---|
| Part C | Expansion | 25 | 6.04% | 6.58% | 9.7% | 0.515 | 1.069 | 1.06 | 21/25 |
|  | Ratio | 25 | 6.04% | 6.14% | 6.9% | 0.504 | 1.028 | 1.04 | 23/25 |
|  | Regression | 25 | 6.04% | 6.15% | 6.8% | 0.508 | 1.016 | 1.02 | 23/25 |
|  | Simulation (parametric rates) | 25 | 6.04% | 6.60% | 10.9% | 0.548 | 0.954 | 0.89 | 18/25 |
| Part D | Expansion | 25 | 1.39% | 1.60% | 26.5% | 0.502 | 0.622 | 0.63 | 22/25 |
|  | Ratio | 25 | 1.39% | 1.32% | 16.4% | 0.295 | 0.489 | 0.85 | 22/25 |
|  | Regression | 25 | 1.39% | 1.47% | 20.0% | 0.347 | 0.405 | 0.60 | 19/25 |
|  | PDE expansion (marginal) | 25 | 1.39% | 1.36% | 40.2% | 0.698 | 0.810 | 0.59 | 16/25 |
|  | PDE ratio (marginal) | 25 | 1.39% | 1.37% | 38.9% | 0.695 | 0.817 | 0.60 | 16/25 |
|  | Simulation (parametric rates) | 25 | 1.39% | 3.45% | 148.4% | 0.189 | 0.322 | 0.87 | 0/25 |
| PERM | Expansion | 25 | 6.10% | 6.14% | 5.5% | 0.419 | 0.787 | 0.96 | 25/25 |
|  | Ratio | 25 | 6.10% | 6.14% | 5.4% | 0.424 | 0.779 | 0.94 | 25/25 |
|  | Regression | 25 | 6.10% | 6.15% | 5.5% | 0.433 | 0.746 | 0.88 | 23/25 |
|  | Simulation (parametric rates) | 25 | 6.10% | 6.55% | 7.3% | 0.300 | 0.640 | 1.09 | 18/25 |
| EIPM | Expansion | 25 | 0.91% | 0.87% | 16.1% | 0.174 | 0.348 | 1.02 | 24/25 |
|  | Ratio | 25 | 0.91% | 0.87% | 16.1% | 0.173 | 0.348 | 1.02 | 24/25 |
|  | Regression | 25 | 0.91% | 0.87% | 16.1% | 0.173 | 0.346 | 1.02 | 24/25 |
|  | Simulation (parametric rates) | 25 | 0.91% | 0.90% | 13.0% | 0.161 | 0.310 | 0.98 | 24/25 |
| CERT | Expansion | 25 | 6.52% | 6.57% | 1.9% | 0.155 | 0.294 | 0.97 | 23/25 |
|  | Ratio | 25 | 6.52% | 6.57% | 1.9% | 0.160 | 0.300 | 0.96 | 23/25 |
|  | Regression | 25 | 6.52% | 6.57% | 1.9% | 0.160 | 0.293 | 0.94 | 23/25 |
|  | Simulation (parametric rates) | 25 | 6.52% | 7.32% | 12.2% | 0.163 | 0.278 | 0.87 | 0/25 |

*Each unit's error probability is multiplied by (payment / stratum mean payment)^-0.5, capped at 0.95, before calibration to the same public targets; designs, audit sizes and methods are unchanged. Bootstrap simulation run at 500 iterations per audit year.*

**Table D4. Simulation donor kinds post-stratified by payment decile, sim_kind_deciles = 10, base populations (25 audit years, gross rate)**

| Program | Method | Audit years | True rate | Mean estimate | MAE (% of truth) | SD of estimate (pts) | Mean half-width (pts) | Half-width ÷ 1.96·SD | Coverage |
|---|---|---|---|---|---|---|---|---|---|
| Part D | Expansion | 25 | 1.38% | 1.30% | 30.5% | 0.543 | 0.727 | 0.68 | 18/25 |
|  | Ratio | 25 | 1.38% | 1.38% | 23.4% | 0.465 | 0.659 | 0.72 | 18/25 |
|  | Regression | 25 | 1.38% | 1.49% | 27.9% | 0.473 | 0.548 | 0.59 | 15/25 |
|  | PDE expansion (marginal) | 25 | 1.38% | 1.32% | 42.0% | 0.735 | 1.112 | 0.77 | 16/25 |
|  | PDE ratio (marginal) | 25 | 1.38% | 1.34% | 41.9% | 0.757 | 1.107 | 0.75 | 17/25 |
|  | Simulation (parametric rates) | 25 | 1.38% | 1.22% | 15.9% | 0.243 | 0.508 | 1.07 | 21/25 |
| PERM | Expansion | 25 | 6.09% | 6.00% | 5.5% | 0.428 | 0.824 | 0.98 | 23/25 |
|  | Ratio | 25 | 6.09% | 6.01% | 5.6% | 0.432 | 0.813 | 0.96 | 23/25 |
|  | Regression | 25 | 6.09% | 6.00% | 5.3% | 0.410 | 0.785 | 0.98 | 23/25 |
|  | Simulation (parametric rates) | 25 | 6.09% | 6.05% | 4.8% | 0.349 | 0.668 | 0.98 | 23/25 |
| EIPM | Expansion | 25 | 0.92% | 0.86% | 17.7% | 0.201 | 0.351 | 0.89 | 22/25 |
|  | Ratio | 25 | 0.92% | 0.86% | 17.6% | 0.200 | 0.351 | 0.89 | 22/25 |
|  | Regression | 25 | 0.92% | 0.87% | 18.1% | 0.204 | 0.350 | 0.88 | 23/25 |
|  | Simulation (parametric rates) | 25 | 0.92% | 0.86% | 16.7% | 0.186 | 0.326 | 0.89 | 22/25 |
| CERT | Expansion | 25 | 6.50% | 6.55% | 2.2% | 0.169 | 0.382 | 1.16 | 25/25 |
|  | Ratio | 25 | 6.50% | 6.55% | 2.3% | 0.171 | 0.376 | 1.12 | 24/25 |
|  | Regression | 25 | 6.50% | 6.55% | 2.3% | 0.169 | 0.374 | 1.13 | 24/25 |
|  | Simulation (parametric rates) | 25 | 6.50% | 6.56% | 2.0% | 0.168 | 0.335 | 1.02 | 23/25 |

*Donor-kind post-stratification of the bootstrap simulation (`sim_kind_deciles = 10`): each non-audited unit receives findings only from audited units of its own design stratum AND its own payment decile within that stratum (10 equal-count quantiles of the payment variable, computed on the population; Part D: submitted gross drug cost per PDE, PERM: the payment, EIPM: annual APTC, CERT: amount paid), so that error incidence can vary with payment size within a stratum. The audit design, strata, allocation and the analytic estimators are unchanged (their rows equal those of the corresponding table above up to Monte Carlo seeding); Part C is omitted because its HCC donor kinds already carry this structure. A kind with no audited unit borrows its parent stratum's pooled counts, partial sizes and parametric redraw; a kind with audited units but no failure assigns none, as before. Bootstrap simulation run at 500 iterations per audit year.*

**Table D5. Simulation donor kinds post-stratified by payment decile, sim_kind_deciles = 10, size_beta = +0.5 populations (25 audit years, gross rate)**

| Program | Method | Audit years | True rate | Mean estimate | MAE (% of truth) | SD of estimate (pts) | Mean half-width (pts) | Half-width ÷ 1.96·SD | Coverage |
|---|---|---|---|---|---|---|---|---|---|
| Part D | Expansion | 25 | 1.41% | 1.04% | 37.6% | 0.526 | 0.762 | 0.74 | 15/25 |
|  | Ratio | 25 | 1.41% | 1.52% | 30.4% | 0.567 | 0.846 | 0.76 | 22/25 |
|  | Regression | 25 | 1.41% | 1.58% | 34.2% | 0.597 | 0.667 | 0.57 | 18/25 |
|  | PDE expansion (marginal) | 25 | 1.41% | 1.18% | 45.0% | 0.744 | 1.225 | 0.84 | 17/25 |
|  | PDE ratio (marginal) | 25 | 1.41% | 1.20% | 45.3% | 0.761 | 1.220 | 0.82 | 17/25 |
|  | Simulation (parametric rates) | 25 | 1.41% | 0.87% | 38.3% | 0.235 | 0.459 | 1.00 | 15/25 |
| PERM | Expansion | 25 | 6.10% | 6.18% | 6.4% | 0.511 | 1.045 | 1.04 | 25/25 |
|  | Ratio | 25 | 6.10% | 6.18% | 6.3% | 0.507 | 1.005 | 1.01 | 25/25 |
|  | Regression | 25 | 6.10% | 6.16% | 6.4% | 0.516 | 0.906 | 0.90 | 23/25 |
|  | Simulation (parametric rates) | 25 | 6.10% | 5.88% | 5.9% | 0.394 | 0.691 | 0.90 | 22/25 |
| EIPM | Expansion | 25 | 0.93% | 0.87% | 17.6% | 0.190 | 0.351 | 0.94 | 23/25 |
|  | Ratio | 25 | 0.93% | 0.87% | 17.6% | 0.190 | 0.350 | 0.94 | 23/25 |
|  | Regression | 25 | 0.93% | 0.87% | 17.6% | 0.190 | 0.350 | 0.94 | 23/25 |
|  | Simulation (parametric rates) | 25 | 0.93% | 0.85% | 17.6% | 0.178 | 0.317 | 0.91 | 23/25 |
| CERT | Expansion | 25 | 6.44% | 6.45% | 2.5% | 0.199 | 0.494 | 1.27 | 25/25 |
|  | Ratio | 25 | 6.44% | 6.45% | 2.5% | 0.199 | 0.474 | 1.22 | 25/25 |
|  | Regression | 25 | 6.44% | 6.46% | 2.5% | 0.206 | 0.452 | 1.12 | 25/25 |
|  | Simulation (parametric rates) | 25 | 6.44% | 6.10% | 5.3% | 0.149 | 0.350 | 1.19 | 13/25 |

*Donor-kind post-stratification of the bootstrap simulation (`sim_kind_deciles = 10`): each non-audited unit receives findings only from audited units of its own design stratum AND its own payment decile within that stratum (10 equal-count quantiles of the payment variable, computed on the population; Part D: submitted gross drug cost per PDE, PERM: the payment, EIPM: annual APTC, CERT: amount paid), so that error incidence can vary with payment size within a stratum. The audit design, strata, allocation and the analytic estimators are unchanged (their rows equal those of the corresponding table above up to Monte Carlo seeding); Part C is omitted because its HCC donor kinds already carry this structure. A kind with no audited unit borrows its parent stratum's pooled counts, partial sizes and parametric redraw; a kind with audited units but no failure assigns none, as before. Bootstrap simulation run at 500 iterations per audit year.*

**Table D6. Simulation donor kinds post-stratified by payment decile, sim_kind_deciles = 10, size_beta = -0.5 populations (25 audit years, gross rate)**

| Program | Method | Audit years | True rate | Mean estimate | MAE (% of truth) | SD of estimate (pts) | Mean half-width (pts) | Half-width ÷ 1.96·SD | Coverage |
|---|---|---|---|---|---|---|---|---|---|
| Part D | Expansion | 25 | 1.39% | 1.60% | 26.5% | 0.502 | 0.622 | 0.63 | 22/25 |
|  | Ratio | 25 | 1.39% | 1.32% | 16.4% | 0.295 | 0.489 | 0.85 | 22/25 |
|  | Regression | 25 | 1.39% | 1.47% | 20.0% | 0.347 | 0.405 | 0.60 | 19/25 |
|  | PDE expansion (marginal) | 25 | 1.39% | 1.36% | 40.2% | 0.698 | 0.810 | 0.59 | 16/25 |
|  | PDE ratio (marginal) | 25 | 1.39% | 1.37% | 38.9% | 0.695 | 0.817 | 0.60 | 16/25 |
|  | Simulation (parametric rates) | 25 | 1.39% | 1.64% | 23.0% | 0.288 | 0.556 | 0.98 | 23/25 |
| PERM | Expansion | 25 | 6.10% | 6.14% | 5.5% | 0.419 | 0.787 | 0.96 | 25/25 |
|  | Ratio | 25 | 6.10% | 6.14% | 5.4% | 0.424 | 0.779 | 0.94 | 25/25 |
|  | Regression | 25 | 6.10% | 6.15% | 5.5% | 0.433 | 0.746 | 0.88 | 23/25 |
|  | Simulation (parametric rates) | 25 | 6.10% | 6.13% | 4.1% | 0.317 | 0.613 | 0.98 | 25/25 |
| EIPM | Expansion | 25 | 0.91% | 0.87% | 16.1% | 0.174 | 0.348 | 1.02 | 24/25 |
|  | Ratio | 25 | 0.91% | 0.87% | 16.1% | 0.173 | 0.348 | 1.02 | 24/25 |
|  | Regression | 25 | 0.91% | 0.87% | 16.1% | 0.173 | 0.346 | 1.02 | 24/25 |
|  | Simulation (parametric rates) | 25 | 0.91% | 0.86% | 14.3% | 0.158 | 0.328 | 1.06 | 23/25 |
| CERT | Expansion | 25 | 6.52% | 6.57% | 1.9% | 0.155 | 0.294 | 0.97 | 23/25 |
|  | Ratio | 25 | 6.52% | 6.57% | 1.9% | 0.160 | 0.300 | 0.96 | 23/25 |
|  | Regression | 25 | 6.52% | 6.57% | 1.9% | 0.160 | 0.293 | 0.94 | 23/25 |
|  | Simulation (parametric rates) | 25 | 6.52% | 6.63% | 2.4% | 0.173 | 0.290 | 0.86 | 20/25 |

*Donor-kind post-stratification of the bootstrap simulation (`sim_kind_deciles = 10`): each non-audited unit receives findings only from audited units of its own design stratum AND its own payment decile within that stratum (10 equal-count quantiles of the payment variable, computed on the population; Part D: submitted gross drug cost per PDE, PERM: the payment, EIPM: annual APTC, CERT: amount paid), so that error incidence can vary with payment size within a stratum. The audit design, strata, allocation and the analytic estimators are unchanged (their rows equal those of the corresponding table above up to Monte Carlo seeding); Part C is omitted because its HCC donor kinds already carry this structure. A kind with no audited unit borrows its parent stratum's pooled counts, partial sizes and parametric redraw; a kind with audited units but no failure assigns none, as before. Bootstrap simulation run at 500 iterations per audit year.*
