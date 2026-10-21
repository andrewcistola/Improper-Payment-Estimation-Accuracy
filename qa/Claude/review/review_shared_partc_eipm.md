# Review report: shared/, part-c-ipm/, eipm/, manuscripts/scripts, manuscript Methods/Appendix

All paths are relative to `/tmp/claude-0/-home-claude/42cb9023-b3be-56b3-ab9a-06a6ce4302a7/scratchpad/repo/`. Numerical checks were run read-only from `/tmp/claude-0/-home-claude/42cb9023-b3be-56b3-ab9a-06a6ce4302a7/scratchpad/agent_b/` (scripts `q1.py`–`q9.py` are there) against the committed populations and `estimates.parquet` files.

---

## 1. BUGS

### 1.1 Part C simulation: additions are drawn independently of HCC failures, but the population never co-generates them, so netting biases underpayments down ~8%
- **Where:** `part-c-ipm/estimation/simulation.py:137-143` vs `part-c-ipm/errors/sql/04_apply_errors.sql:125`.
- **What:** In `errors/`, an additional HCC is only applied when `NOT missing_doc AND hcc_err = 0 AND family not coded` (line 125). In the kernel, every non-audited enrollee lacking family f gains it with probability `a_rate[f]` *regardless* of whether that same enrollee also received HCC failures in the iteration; `dr[gain] -= mild` is then netted against the failure losses before `over`/`under` are split (line 141-143). The audited rate `a_rate = added / eligible` (line 117) is already P(add ∧ no overpayment | lacks f), so applying it to enrollees who will be overpaid and then netting throws part of it away.
- **Effect (measured, `q8.py`):** across 8 synthetic audits, simulated `national|under` averaged 8.1% below the kernel's own linear expectation. In the committed results the simulation's mean under estimate is 49.3 bp vs truth 57.4 bp (−14%; the extra is 25-rep noise), vs 54.1–55.0 bp for the analytic methods. Table 5 shows sim under 19/25 (0/6 below) vs 21/25 analytic; the manuscript does not attribute this. Over and gross are biased down by the same dollars (≈0.8% and ≈1.5% of truth), within noise at 25 reps.
- **Fix:** either (a) in `iterate`, only apply additions to recipients whose `dr == 0` after failures (matching the population rule), or (b) define the addition rate's denominator as audited enrollees lacking f *with no overpayment finding*, and document the assumption either way. The `test_part_c_bootstrap_rates` test (`shared/tests/test_simulation.py:58-72`) checks only net to 1% and cannot see this.

### 1.2 Regression degrees of freedom double-count the intercepts
- **Where:** `shared/ipsim/regression.py:110`: `df = len(yk) - len(strata_d) - terms`, where `terms` already includes one intercept per model stratum (line 97 counts `matrix_rank(zm)` with the intercept column). When model strata = design strata (Part C, EIPM), the H intercepts are subtracted twice.
- **Effect:** negligible here (df 972 vs 975 → t = 1.96241 vs 1.96240), but wrong in principle and would matter for small post-strata.
- **Fix:** `df = max(1, len(yk) - terms)` (terms already counts intercepts), or `len(yk) - len(strata_d) - slopes`.

### 1.3 `design.yaml` written by errors/ contradicts the estimation design
- **Where:** `part-c-ipm/errors/config.yaml:39-42` writes `n: 1500` per tercile (4,500) to `errors/output/base/design.yaml`; `part-c-ipm/estimation/config.yaml:26-28` samples 330 per tercile (990). The manuscript (Table 1, B.1) says 990.
- **Fix:** make `design` reference the estimation allocation, or drop the sample sizes from `design.yaml`.

### 1.4 `mc_se_coverage` is degenerate at 0/25 or 25/25
- **Where:** `shared/sql/lib/02_estimators.sql:144-145` uses the *observed* p in `sqrt(p(1-p)/n)`, which returns 0 when coverage is 25/25 (several cells). The manuscript correctly reports ≈4.4 pts (nominal p=0.95). Use the nominal or a Wilson-based SE, or state that the field is the plug-in estimate.

### 1.5 `fsd`/`favg` in Part C expansion with a stratum of one unit
- **Where:** `shared/sql/lib/01_stats.sql:60-62` divides by `count(v) - 1`; `part-c-ipm/estimation/sql/10_expansion.sql:38` calls `fsd(z)` per stratum. If any `samp_h = 1` (possible via `least(count(*), n_h)` in `sample_srs.sql:26`) this is a division by zero → NULL interval, scored as "undefined". `ipm_moments` (02_estimators.sql:60-62) guards this; the Part C expansion does not. Not triggered at 330/stratum.

### 1.6 Minor
- `shared/ipsim/regression.py:92`: the "fewer than 10 audited errors" fallback counts units with `y != 0` in **any** domain (`err_units`, line 82). For `national|under` in Part C a tercile with ~3 audited underpayments still gets a 5-term model if it has ≥10 overpayments. The manuscript (§3.4) describes the threshold per stratum without this qualifier; it is a documented-intent mismatch and an overfitting risk for sparse domains.
- `shared/sql/report.sql:47-55` hard-codes `w_pop` per program while every `population.parquet` carries `w_pop`. Duplication only, values agree.
- `manuscripts/scripts/build_tables.py:57` joins the **parametric** estimates to the **fixed-run** `truth.json` (`'{f}/truth.json'`). Same truth today, fragile if seeds ever diverge.

No errors were found in: stratified-SRS expansion/ratio variances with FPC (`02_estimators.sql:66-96`; verified against a textbook per-unit numpy reference and against the exact design SE from the population — Part C ratio: reported mean SE 54.65 bp vs exact 54.85 bp; EIPM expansion 17.93 vs 18.63), the ratio linearization, the single-auxiliary GREG macro, the Part C risk-score expansion, the SRS sampler (equal inclusion: χ² = 992.7 on 999 df over 3,000 reps; no unit repeated; same sample across domains), the systematic sampler (exactly n distinct positions, inclusion n/N), EIPM Neyman allocation (largest remainder, min 2, excess removed from largest stratum), RNG uniformity/independence (lag-1 corr −0.003, cross-rep corr 0.0002), `bernoulli_positions`, the percentile interval (Hyndman-Fan 7), coverage scoring (rate vs rate, consistent across methods), and the median/MAE formulas in `build_tables.py`.

---

## 2. CORRECTNESS CONCERNS

### 2.1 The parametric interval understates the simulation estimator's own sampling variance by ~7–10%; roughly half of the "narrower interval" finding is this, not efficiency
I computed the true sampling SD of the simulation's point estimator by redrawing the production audit many times from the committed populations (`q7.py`: 2,000 Part C audits; `q9.py`: 300 EIPM audits × 12 iterations):

| Program, gross | Parametric reported SE (mean over 25 yrs) | Empirical SD of sim estimate (25 yrs) | **True SD of sim estimator (my MC)** | Analytic reported SE | Exact design SE |
|---|---|---|---|---|---|
| Part C | 47.2 bp | 43.1 | **50.8** | ratio 54.65 | 54.85 |
| EIPM | 16.1 bp | 17.6 | **17.8** | ratio 17.92 | 18.63 |

So the parametric half-width is 7% (Part C) and 10% (EIPM) too short relative to its own estimator's true variability, while the ratio SE is essentially exact. The genuine efficiency gain of the simulation estimator over the ratio estimator is 7.5% (Part C) and 4% (EIPM), not the 11% in Table 4. Expected coverage of an interval 7–10% too narrow is ≈92–93%, which 25 audit years cannot distinguish from 95% (MC SE 4.4 pts). The audit-size projections (Table 4, §5.2) inherit this: using the true SDs, Part C would need ≈86% of the audit (not 79%) and EIPM ≈92% (not 80%).

Sources of the omitted variance (all visible in code):
- Error **sizes** are fixed: `f_loss` (mean audited loss per HCC) at `part-c-ipm/estimation/simulation.py:104,133`; the income-ratio list at `eipm/estimation/simulation.py:94,114`. The manuscript acknowledges this (§4.3, Limitation 5) but calls it "small"; the numbers above say it is about half the claimed gain.
- Rates are redrawn **independently** across the 20 HCCs / 10 families (`simulation.py:126-127`), but in one audit they are positively correlated: contract `intensity` multiplies every HCC's failure probability (`04_apply_errors.sql:42`) and missing documentation fails every HCC of an enrollee (`simulation.py:77`). Independent binomials understate the variance of the summed rate.
- The redraw conditions on the audit's realized `n_k` (HCC instances), ignoring that `n_k` itself varies across audits.

Recommend: report the empirical SD of the simulation estimate over many more audit years (≥200), or compare interval half-width to the estimator's true SD, before claiming width advantages.

### 2.2 The simulation uses population information the analytic estimators are denied
- Part C: `cm_by_hcc` structure — every enrollee's HCC list, severity, county rate and months (`40_simulation_inputs.sql`); EIPM: every application's benchmark, household size, income and months. The manuscript says so (§4.3 "known structure of the population") but the comparison with the ratio estimator (which uses only X) is then between estimators with different information sets. A fairer analytic comparator is the regression estimator with the same predictors; in Part C/EIPM it is given only 4–5 linear predictors, not the HCC lists.
- Part C expansion is priced with a population-wide `c_bar = favg(county_rate*months)` (`10_expansion.sql:23-25`) — also population information, unstated as such.

### 2.3 The simulation is told the true error-generating structure
- The HCC-level donor kinds (family × severity) and the "failure ⇒ lose mean L_k" rule mirror exactly how errors were fabricated (`04_apply_errors.sql`). The EIPM kernel transfers the lognormal income ratio and recomputes APTC with the exact schedule, again mirroring `02_apply_errors.sql:34-37`. Point accuracy of the bootstrap (§4.1) is therefore partly a consequence of specifying the right model; the manuscript should say this plainly.

### 2.4 Independence assumptions that the populations happen to satisfy
- Both kernels assume error probability is independent of county rate × months (Part C) and of everything but stratum (EIPM). In these populations it is (checked: failed vs supported HCCs have identical mean months and county rate). B.6.3 states this for PERM/CERT/EIPM only; it should also be stated for Part C, where it is also assumed.

### 2.5 EIPM: assigning monetary findings to applications that cannot have them
- `eipm/errors/sql/02_apply_errors.sql:51` makes "monetary" conditional on `cand_correct_aptc < x`; the kernel (`simulation.py:108-115`) assigns the audited monetary rate to all recipients, including those at the 600% FPL cap where the recomputed APTC equals x (y = 0). Small (≈1.6% of applications) but it is a downward bias the manuscript attributes only to "a different point of the schedule" (§4.1, B.4).

### 2.6 25 audit years
- 23/25, 24/25, 25/25 are statistically indistinguishable; the "equal or higher coverage" tables (§4.3) and the 121/125 pooled count mix five populations whose per-program MC SE is 4.4 pts. The paper says this in §5.4 but §4.3/§5.2 read as if the ordering is established.

### 2.7 Neyman allocation uses the true y SD (EIPM)
- `eipm/estimation/sql/01_frame.sql:34-37`. Stated in B.6.4; worth noting it favours the analytic estimators (Neyman minimizes *their* variance), which the manuscript notes in §6.1.

---

## 3. ASSUMPTIONS IN CODE NOT STATED IN MANUSCRIPT

| # | Assumption | File:line | Should appear in |
|---|---|---|---|
| 1 | Additional HCCs only when the enrollee has no overpayment and no missing documentation | `part-c-ipm/errors/sql/04_apply_errors.sql:125` | B.1 Errors (and §4.4, as the cause of sim under bias) |
| 2 | Half of unsupported *severe* HCCs are hierarchy moves; mild HCCs are always deleted | `04_apply_errors.sql:93` | B.1 |
| 3 | Chart-review-sourced HCCs have 3× the unsupported probability; 15% of HCC draws are chart-review; 35% of draws severe | `04_apply_errors.sql:42`; `02_enrollees_hccs.sql:51-52` | B.1 |
| 4 | Contract coding intensity lognormal(−0.08, 0.40) multiplies every HCC's failure probability | `01_contracts.sql:17` | B.1 (and §2.1 above: induces within-audit rate correlation) |
| 5 | Error probabilities capped at 0.95 | `04_apply_errors.sql:67,91,112,114` | B.1 |
| 6 | Missing documentation only for enrollees with ≥1 HCC; p_md = 0.003 × multiplier | `04_apply_errors.sql:112` | B.1 |
| 7 | 85% full-year enrollees; otherwise months uniform 1–11; demo score 0.35 + 0.30·Kumaraswamy(2,3) | `02_enrollees_hccs.sql:35-40` | B.1 Population |
| 8 | Part C expansion prices risk-score error with one national mean of county_rate × months over *all* enrollees | `10_expansion.sql:23-25` | §3.4 "Part C expansion" (currently ambiguous) |
| 9 | Failed HCC loses the HCC's **mean** audited loss (not a draw from the list) | `part-c-ipm/estimation/simulation.py:104,133` | §3.5 step 2 / A.5 step 4 say "drawn uniformly from the audited partial list" |
| 10 | Addition rate denominator = audited enrollees lacking family f; parametric redraw uses that count | `simulation.py:114-117,127` | §3.6 |
| 11 | Parametric redraw treats the 30 Part C rates as independent binomials given the realized n_k | `simulation.py:126-127` | §3.6 |
| 12 | Simulation's audit is the `national\|gross` domain sample | `simulation.py:92` | A.5 (fine, but say the four measures share one audit) |
| 13 | Regression fallback: errors counted in any domain, and n_m ≥ terms + 5; df formula | `shared/ipsim/regression.py:82,92,110` | §3.4 |
| 14 | Regression uses plain (not g-weighted) residuals, within-stratum s² with ddof=1 | `regression.py:109` | §3.4 |
| 15 | EIPM: income ratio factor max(r, 1/r), r ~ lognormal(0, 0.35); supported income capped at 600% FPL; monetary candidate with correct APTC ≥ x is "none" | `eipm/errors/sql/02_apply_errors.sql:30,34,51` | B.4 Errors |
| 16 | EIPM: household size 1 + ⌊4u^1.6⌋, age 21–64 uniform, FPL 100 + lognormal(4.6, 0.75) capped 600, 75% full-year, benchmark age-rated 1.8%/yr × size × region factors | `01_population.sql:17-39` | B.4 Population |
| 17 | EIPM applicable % falls back to 8.5% outside bands | `01_population.sql:28`; `simulation.py:43` | B.4 |
| 18 | EIPM Neyman: S_h from population *gross* y, largest-remainder rounding, min 2 per stratum, excess removed from largest stratum | `eipm/estimation/sql/01_frame.sql:33-47` | B.4 Audit |
| 19 | Fixed and parametric runs share the scenario seed, hence identical audits (needed for "same audits" claims) | `results*/base/config.yaml` (only `sim_rates` differs) | A.1 |
| 20 | Percentile interval uses linear interpolation (type 7) on 1,000 draws | `shared/ipsim/simulation.py:206` | A.5 |
| 21 | Point estimate reported for the regression's gross/net is linear in over/under but its interval is not | `regression.py` docstring | §3.4 |

---

## 4. MANUSCRIPT CLAIMS NOT MATCHED BY CODE

1. **§3.5 steps 1–2, §3.6 ("Partial sizes are still drawn from the audited list"), A.5 step 4:** Part C does *not* draw sizes; a failed HCC loses the fixed mean `f_loss[k]` (`part-c-ipm/estimation/simulation.py:133`). B.1 says "mean audited loss" — the generic method sections and B.1 disagree.
2. **§3.5 "Steps 1 and 2 are equivalent to giving every unit the finding of a uniformly drawn audited donor of its kind":** not true for Part C (mean loss) and only approximately for EIPM (ratio applied to a different income, clipped).
3. **§3.3 / A.4 "netted within the payment unit":** true of the population and of the analytic estimators; the Part C simulation nets *across* mechanisms that the population never combines (Bug 1.1).
4. **§3.4 "A stratum with fewer than 10 audited errors ... uses an intercept-only model":** code counts errors in any domain, not the domain being estimated (`regression.py:82`).
5. **§3.4 "degrees of freedom reduced by the strata and model terms fitted":** implemented, but intercepts are subtracted twice (Bug 1.2).
6. **§4.3 "The gain in width has two sources":** omits that the interval is ~7–10% narrower than the estimator's true sampling SD (§2.1) — a third source that is not a gain.
7. **§4.4 / Table 5 Part C underpayments 19/25 (0/6 below):** attributed to sparsity; part of it is the netting bias of Bug 1.1 (sim mean 49 bp vs truth 57 bp while analytic means are 54–55 bp).
8. **§5.3 "adds two binomial draws per stratum per iteration":** Part C adds 30 draws (20 HCC + 10 family) per iteration, none per stratum.
9. **Table 1 / B.1 "990 enrollees, 330 per tercile":** matches estimation config but not `errors/output/base/design.yaml` (1,500 per tercile), which the repo presents as the design record.
10. **A.2 "Reruns produce byte-identical files at any thread count ... tested in test_determinism.py":** tested only for EIPM and Part C errors/ and EIPM estimation; not for Part C estimation, Part D, PERM, CERT. Also the regression (LAPACK `lstsq`) and numpy `Generator` streams are not pinned (see §6), so "identical" holds within one environment only.
11. **A.1 "Expansion and ratio ... tested against an independent numpy implementation":** true for the shared macros, but the Part C expansion (`10_expansion.sql`, risk-score units) is not covered by `test_estimators.py`.
12. **`shared/tests/test_simulation.py:61` docstring "gross is not [unbiased], see the README":** no README discusses this.
13. **`shared/data_dictionary.md:110`** describes PERM strata as "five equal-dollar strata per state × quarter × type" while the manuscript B.3 says payment type × five equal-count payment quintiles (10 per state). Out of my program scope but the dictionary is in scope; flag for the other reviewer.
14. **`shared/data_dictionary.md:30-47`** omits Part C `population.parquet` columns `missing_doc`, `add_fam`, `add_coef`, `stratum`-level details that `40_simulation_inputs.sql` relies on.

---

## 5. TEST SUITE ASSESSMENT

**Would catch real errors:** `test_estimators.py` (independent per-unit numpy reference for expansion/ratio/GREG, census → zero variance), `test_stats.py` (norm_cdf/ppf vs scipy to 2e-7/2e-9, quantile vs numpy, order-independent `fsum`), `test_rng.py` (the SRS-overlap test is a good guard against the multi-arg hash bug it documents), `test_sampler.py` (exact sizes, no duplicates, shared sample across domains, weights sum to N), `test_simulation.py` exactness tests (payment functions reproduce SQL to the cent; census → exact rates; `bernoulli_positions`; `RowSet.assign` same-kind and audited-never-recipient), `test_regression.py` (intercept-only ≡ expansion to 1e-9; linearity; exact fit → zero residual variance).

**Gaps (ranked by what they'd have caught here):**
1. **No test that any interval attains its nominal coverage** on a toy population with many replicates (e.g., 2,000 SRS draws from a toy frame → ratio and parametric-sim coverage ≈ 95%, parametric SE ≈ empirical SD). This is the only kind of test that would reveal §2.1 (7–10% SE understatement) and is cheap on a toy.
2. **No unbiasedness test for Part C `under`/`over` separately**: `test_part_c_bootstrap_rates` checks net to 1% with 20 iterations and 50% audited; under is 10% of net, so an 8% under bias is invisible. A per-domain check with a production-size audit would have caught Bug 1.1.
3. **No independent check of `regression.py`'s SE** when predictors are actually used (only intercept-only and exact-fit cases). Comparing to `ipm_regression` with `reg_predictors=[x]` and one model stratum, and checking the df, would do it.
4. **No test of `ipm_score`** (coverage counting, `n_undefined`, above/below, rel_width) or of `report.sql`/`build_tables.py` arithmetic (dollar conversion, `sp**2` audit-size projection).
5. **No test of SRS inclusion-probability uniformity** (I checked χ²; add it) or of the systematic sampler's inclusion probability with a fractional interval.
6. **Part C `10_expansion.sql`** has no reference test.
7. `test_determinism.py` requires full engine runs; the Part C/EIPM estimation determinism test runs only EIPM.
8. Tolerances in `test_*_bootstrap_rates_unbiased` (1–3%) are loose relative to the biases that matter (gross ≈ 0.1%; under ≈ 8%).
9. `test_eipm_bootstrap_rates_unbiased` targets "the audited half's own gross rate" rather than the truth, which bakes in the acknowledged 1–2% transfer bias instead of measuring it.

---

## 6. REPRODUCIBILITY / PACKAGING

- `pyproject.toml:10` / `requirements.txt` pin `duckdb==1.5.6` and `numba==0.68.0` but leave `numpy>=2.0`, `scipy>=1.11`, `pyarrow>=17` floating. The simulation's randomness is numpy `Generator` (`binomial`, `geometric`, `integers`, `random`), whose bit-streams NumPy does not guarantee stable across minor versions; `lstsq` depends on the LAPACK build. The claim of byte-identical reruns therefore needs a lock file (`pip freeze` or `uv.lock`) and the manifest should record numpy/scipy/numba/BLAS versions (`shared/ipsim/engine.py:230-233` records only duckdb and python). The venv in the repo runs Python 3.13.16, numpy 2.5.4, scipy 1.18.1.
- `requirements.txt` duplicates `pyproject.toml` dependencies by hand; one should derive from the other.
- `build_tables.py` uses `fetchdf()` → pandas (optional extra `all`); it `raise SystemExit` if any program's results are missing, so a partial reproduction (e.g., Part C + EIPM only, the committed populations) cannot regenerate the tables. Consider skipping missing programs with a warning.
- `build_tables.py` hard-codes `scale` and design labels per program (lines 29-39), duplicating `w_pop` in the populations and `report.sql:47-55`.
- `engine.py:120-122` `lookups`: `v.setdefault(var, spec["map"][v[spec["by"]]])` raises `KeyError` with no message if a grid value is missing from the map. Minor.
- `engine.py:262` `--set k=v` only overrides `defaults`; a scenario-level override of the same key silently wins. Document or apply after scenario merge.
- CLI: `ipsim` entry point and `python -m ipsim` both work (`__main__.py`). `shared/ipsim.egg-info` is present in the tree (gitignored, fine).
- `results_fixed/` and `results/` configs differ only in `sim_rates` (verified by diff), so the "same audits" claim holds for the committed runs.
- The manuscript's reproducibility statement (A.2) should say "identical within one pinned environment" unless the numpy stream and LAPACK are pinned.

---

## Summary of the highest-priority items
1. **Part C netting bias (Bug 1.1)** — real ~8% downward bias in simulated underpayments; fix the kernel or the rate denominator and re-run.
2. **Parametric interval understates its estimator's sampling SD by 7–10% (§2.1)** — about half of the headline "11–21% narrower" and the audit-size projections; 25 audit years cannot detect it. Quantify with ≥200 audit years or against the estimator's true SD before publication.
3. **Fix the regression df** and the `design.yaml` sample sizes; align §3.5/§3.6/A.5 text with the Part C "mean loss" implementation.
4. Add a coverage/SE-calibration test on a toy population and per-domain unbiasedness tests for Part C; pin numpy/scipy and record versions in manifests.