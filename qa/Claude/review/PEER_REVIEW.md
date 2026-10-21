# Peer Review: Comparative Accuracy of Improper Payment Estimation Methods in Federal Health Programs

**Reviewer:** Claude (Anthropic), acting as an independent health-economics / survey-statistics referee
**Repository version reviewed:** commit `33c6c47068df10f5f7cb56c8bf3c00cdd210a50d` (merge of PR #28, 2026-10-21 14:41 EDT)
**Review dates:** 2026-10-21
**Relationship to the study:** none; did not contribute code, data or text to the version reviewed.
**Re-run folder:** `qa/Claude/` (this folder). Logs, results, verification and the collected `RERUN_SUMMARY.md` are in the sub-folders listed in `qa/reruns/README.md`.

This document has six parts, matching the review request: (1) literature review and framing, (2) code review, (3) the independent re-run, (4) writing and style, (5) overall assessment, and (6) the consolidated change list. The three detailed working reports that feed Parts 1 and 2 are in `review/` (`review_citations.md`, `review_shared_partc_eipm.md`, `review_partd_perm_cert.md`); each cites file and line numbers.

---

## Part 1. Literature review and research-question framing

### 1.1 Is the gap real and important?

Yes. The review documents convincingly that (a) the interval methods used for Part C, Part D and EIPM are not public, (b) state PERM eligibility rates acquire dollar consequences from FY 2030 under P.L. 119-21 §71106, (c) State-based Exchange measurement begins in 2027 with small state samples, and (d) no published study has evaluated any of these methods against a known truth in CMS-style designs. The structural result in the manuscript (a plug-in simulation that never resamples the audit omits the between-audit variance term) is correct and matters for practice.

### 1.2 Framing problems a referee will raise

1. **The companion review over-claims what the manuscript delivers.** Review §8 and reference G say the manuscript "implements the research agenda in Section 8." The agenda calls for survey bootstraps (Rao–Wu, pseudo-population), BCa, bootstrap-*t*, empirical likelihood, hypergeometric bounds, one-sided recovery bounds, an error-rate grid from 0.01 to 0.95, and 10,000 replications per cell. The manuscript tests three analytic estimators and one simulation method at one error rate per program with 25 replications. Revise to "implements the first stage of this agenda."
2. **The two documents contradict each other on two program facts.** The manuscript's Abstract and §1.1 say the law requires a 95% confidence interval; neither PIIA nor M-21-19 specifies a level (M-21-19 says agencies determine the appropriate interval with their statistician), and the review correctly reports PERM's older 90% ±2.5 target. The manuscript §1.2 says the Part D interval "is already simulation based (CMS 2023, 2025c)"; the review §5 correctly says public documents do not name the algorithm. Harmonize both to the review's wording.
3. **The review's own prioritization (RADV and PERM state eligibility "High"; Part C IPM "Low"; CERT "Low–medium") does not lead to the manuscript's recommendation** that CMS adopt parametric-rate simulation for all PIIA rates. In Part C and CERT the analytic intervals already cover at 24–25 of 25; the manuscript's case there rests on width, not on a coverage failure. The Discussion should say this explicitly and reconcile it with the review.
4. **Novelty should be stated more modestly.** The fixed-rate failure is the single-imputation problem (Rubin 1987) and the plug-in problem in parametric-bootstrap theory, demonstrated in a new setting. The manuscript already says the method "is not a Bayesian bootstrap" without citing Rubin (1981). Present the finding as a demonstration, cite the lineage, and the paper becomes stronger rather than weaker.
5. **"Audit-finding bootstrap simulation" is a misnomer for the fixed-rate method.** It resamples nothing that was observed; it is a plug-in microsimulation. Survey Methodology / JOS referees will object. Suggested terminology: "plug-in audit-finding simulation" (fixed rates) and "parametric-bootstrap audit-finding simulation" (parametric rates).
6. **The manuscript does not establish that any CMS program uses a fixed-rate simulation.** The policy claim should be conditional: "if a program's simulation holds the audited rates fixed, its interval is invalid; the Part D S&EMP should be checked."

### 1.3 Citation verification (summary; full table in `review/review_citations.md`)

All 66 review references and all manuscript references were checked. Most are real and correctly characterized. Items that need correction:

| Item | Problem | Fix |
|---|---|---|
| *Humana Inc. v. Becerra*, "801 F. Supp. 3d 624" | The reporter citation could not be found anywhere; the briefs cite only the record. Possibly fabricated. | Cite as *Humana Inc. v. Becerra*, No. 4:23-cv-00909-O (N.D. Tex. Sept. 25, 2025), appeal docketed *Humana v. Kennedy*, No. 25-11293 (5th Cir.). Remove the reporter cite unless confirmed on Westlaw/Lexis. |
| ED OIG (2025) "…for Fiscal Year 2025" (both documents) | The linked/dated report (A25DC0225, May 27, 2025) covers FY 2024. | Cite ED-OIG/A26DC0288 (Aug 4, 2026) for FY 2025, or relabel as FY 2024. |
| GAO (2026) "Payment Integrity: FY 2025 improper payment estimates" | Informal title. | GAO-26-108694, *Agencies' Estimated Improper Payments Increased to $186 Billion in Fiscal Year 2025*, April 27, 2026. |
| CMS (2025a) FY 2025 Improper Payments Fact Sheet | Dated January 15, 2026. | CMS (2026). |
| CMS (2025b) cited for CERT ±3 pts at 95% | The target is stated in the CERT *Introduction* document. | Cite that document (or Appendix N of the Supplemental report). |
| RADV "Fast Facts" cited for "~550 contracts" | Not in the fact sheet. | CMS press release, May 21, 2025, "CMS Rolls Out Aggressive Strategy…" |
| PaymentAccuracy.gov cited for "0.43 of 0.89 points" | Figure is on the CMS EIPM Improper Payment Findings page. | Cite that page. |
| EIPM Program Background cited for SBE start "no earlier than 2027" | Not on that page. | 45 CFR 155.1605. |
| Statutory threshold ($10M and 1.5%, or $100M) cited to a MyChesCo news summary | Weak source. | Cite M-21-19 §II.C directly. |
| Kvanli & Schauer | Undated, unpublished; text says "6–530%" and "30 nonzero errors in the sample". | Cite as n.d., unpublished manuscript hosted by MTC; "5.5–531%"; "about 30 *expected* errors". |
| Kolenikov (2008 slides) attribution of coverage ranking to Kovar, Rao & Wu 1988 | Slides attribute it to Krewski & Rao 1981, Rao & Wu 1988, KRW 1988 and Shao 1996 jointly. | Attribute to the set. |
| Liu (2025) EL "untested above 40%" | No 40% figure in the abstract. | Remove or source. |
| M-21-19 as "the approval route" | OMB reviews but does not formally approve S&EMPs. | "submission route". |
| Edwards, Liu & Delage (2023) | Three over-readings: "no stratification algorithm… viable for more than about half" (the geometric algorithm reached 88%); "R `samptest`" implies a package (it is a function available on request; the stratification algorithms are in CRAN `stratification`); "payment-based strata create left-skewed strata" (paper says "can"). Manuscript §3.1 "follows the design of Edwards et al." overstates the resemblance. | Revise each. |
| PERM Supporting Statement B (OMB ICR 202408-0938-026) | Could not be retrieved; the "systematic selection after sorting by paid amount" and variance claims rest on it. | Verify and add OMB control number 0938-0974. |
| Part D intervals "visibly asymmetric" | FY 2025 is −0.46/+0.48 (essentially symmetric). | Soften. |
| EIPM "rates have stayed under 1%" | FY 2024 was 1.01%. | "near or below 1%". |
| PARG "$115 million a year" | Source says ~$114 million. | Correct. |
| Part C "up to ~7,000 medical records"; "ESRD and hospice entered the sample FY 2024" | No source found. | Source or delete. |
| Manuscript orphans (in list, never cited): Biddle et al. 1990; Davison & Hinkley 1997; King & Madansky 2013; Rao & Wu 1988; Wolter 2007; CMS 2025d, 2026a, 2026b, 2024 (used only implicitly in Appendix B) | | Cite in text or remove; add a reference entry for P.L. 119-21. |
| Manuscript §1.3 cross-reference "Section 4.1 shows that this omission is large" | The omission is shown in §4.2. | Fix. |

Figures checked against CMS: all FY 2025 rates, dollars, confidence intervals, denominators, CERT sample counts and the 0.43-point technically-improper share are correct.

### 1.4 Missing citations (verified; full details in `review/review_citations.md` §D)

- **Audit sampling foundations:** Stringer (1963); Kaplan (1973) *J Accounting Research*; Fienberg, Neter & Leitch (1977) *JASA*; Cox & Snell (1979) *Biometrika* (rare-error model — directly relevant to EIPM and the sparse components); Rohrbach (1993) *Auditing* (variance augmentation to reach nominal coverage — the same problem as §4.2); Howard (1994) *JBES* (bootstrap bound for audit populations); Bickel (1992) *ISR*; Berger, Chiodini & Zenga (2021) *Statistical Papers* (EL for MUS); Gunning & Horgan (2004) *Survey Methodology* and Horgan (2006) *ISR* (geometric stratification, which Edwards et al. found most viable).
- **Medicare integrity statistics:** Edwards (2011) *HSORM* 11:79–94 (ratio vs expansion in Medicare audits — the manuscript compares exactly these and does not cite it); Gilliland & Edwards (2011) *Am Stat*; Ignatova & Edwards (2008) *HSORM*; HHS OIG RAT-STATS (the standard implementation of the normal-theory bounds the review critiques).
- **Survey bootstrap:** Bickel & Freedman (1984) *Ann Stat* (first bootstrap under stratified sampling); Krewski & Rao (1981); Chao & Lo (1985); Sitter (1992) *CJS*; Beaumont & Patak (2012) *ISR*; Preston (2009) *Survey Methodology* (multistage — relevant to PERM); Lohr (2022); Valliant, Dorfman & Royall (2000) — the natural citation for the model-based character of the simulation's width gain.
- **Imputation analogy:** Rubin (1987) *Multiple Imputation for Nonresponse in Surveys* — the between-imputation variance is the exact analogue of the missing Var(E[T̂|A]) term; Rubin (1981) *Ann Stat* (Bayesian bootstrap).
- **Simulation-study methodology:** Morris, White & Crowther (2019) *Stat Med* (ADEMP; Monte Carlo SE for coverage); Koehler, Brown & Haneuse (2009) *Am Stat*.
- **Government:** ED-OIG/A26DC0288 (2026); GAO-26-108694 (2026); CMS Part D IPM Program Background (random 5% beneficiary extrapolation sample).

---

## Part 2. Code review

Two reviewers read every SQL and Python file (one for `shared/`, Part C and EIPM; one for Part D, PERM and CERT), verified the arithmetic with standalone scripts against the committed populations, and compared code to the manuscript's Methods and Appendix. No file in the repository was modified.

### 2.1 What is correct

The stratified-SRS expansion and ratio variances with FPC (`shared/sql/lib/02_estimators.sql`) match a textbook per-unit numpy reference and the exact design SE computed from the population (Part C ratio: reported mean SE 54.65 bp vs exact 54.85 bp; EIPM expansion 17.93 vs 18.63). The SRS sampler has equal inclusion probabilities (χ² = 992.7 on 999 df over 3,000 draws), the systematic sampler gives exactly *n* distinct positions, Neyman allocations (three implementations) are correct, the RNG streams are uniform and independent, the percentile interval and coverage scoring are correct and consistent across methods, the Part D 2025 and 2023 benefit parameters are correct, the PERM national roll-up is a valid combination of independent state estimates, and the CERT closed-form calibration reproduces 6.50% vs the 6.55% target. The reported numbers in the README, abstract, Results and Discussion all trace to `results_long.csv` and `by_scenario.csv`.

### 2.2 Bugs (ordered by effect on results)

| # | Location | Problem | Effect | Fix |
|---|---|---|---|---|
| B1 | `part-c-ipm/estimation/simulation.py:137-143` vs `part-c-ipm/errors/sql/04_apply_errors.sql:125` | The population applies an additional HCC only to enrollees with no overpayment and no missing documentation. The kernel applies the audited addition rate to every recipient lacking the family, including those that also received failures in the iteration, and then nets. Part of the addition is thrown away. | Simulated underpayments run about 8% below the kernel's own linear expectation; in the committed results the simulation's mean `under` is 49.3 bp vs truth 57.4 bp (analytic methods 54–55 bp). This is the unexplained part of the Part C under coverage of 19/25 with all misses below (§4.4). Over and gross are biased down by the same dollars (≈0.8% and ≈1.5% of truth). | Apply additions only to recipients with no failure in the iteration (matches the population rule), or redefine the addition-rate denominator as audited enrollees lacking the family with no overpayment finding. Add a per-domain unbiasedness test; the existing `test_part_c_bootstrap_rates` checks only net to 1% and cannot see this. Re-run Part C. |
| B2 | `part-d-ipm/estimation/simulation.py:204`; `perm_simulation.py:94`; `cert_simulation.py:197` | Parametric redraw uses `q̃ ~ Binomial(f, q)/f` with the *observed* f, not the redrawn f̃ = n·p̃. | Negligible numerically; inconsistent with §3.6 as written. | Draw f̃ first, then q̃ from f̃; or restate §3.6 as conditional on the observed f. |
| B3 | `shared/ipsim/regression.py:110` | df = n − (#strata) − terms, but `terms` already counts one intercept per model stratum, so intercepts are subtracted twice. | Negligible at n = 990 (t = 1.96241 vs 1.96240); wrong in principle and would matter for small post-strata. | `df = n − terms`. |
| B4 | `shared/ipsim/regression.py:82,92` | The "fewer than 10 audited errors → intercept-only" fallback counts errors in *any* domain. A Part C tercile with 3 audited underpayments still gets a 5-term model for `national|under` if it has ≥10 overpayments. | Overfitting risk for sparse domains; §3.4 describes the rule per stratum without this qualifier. | Count errors in the domain being estimated, or state the rule as implemented. |
| B5 | `part-c-ipm/errors/config.yaml:39-42` → `errors/output/base/design.yaml` | Design block says 1,500 per tercile (4,500); estimation uses 330 (990). | Metadata only (the QA example issue I-01). | Reference the estimation allocation or drop sizes from `design.yaml`. |
| B6 | `README.md:14`; `shared/ipsim/simulation.py:27-28` | "beneficiary sample (108,000 beneficiaries)" — 108,000 is the population; the simulation uses no beneficiary sample; ratio/regression use an SRS of 990. | Misstates the design. | Correct both. |
| B7 | `perm-cert/README.md:17`; `perm-cert/errors/perm.yaml:46`; `perm_01_population.sql:11-13`; `shared/data_dictionary.md:110` | Describe five equal-dollar strata within state × quarter × payment type; the code builds five equal-count quintiles within state × payment type with no quarter and Neyman allocation. | Reader cannot reproduce the design from the docs. | Align text with code (`design.yaml` is written from `perm.yaml:design`). |
| B8 | `perm-cert/README.md:40` | "Systematic sample's variance estimated as if stratified SRS" sits under the CERT bullet; CERT is SRS, the statement is about PERM. | Misattribution. | Move; also state it in manuscript §3.4. |
| B9 | `shared/sql/lib/02_estimators.sql:144-145` | `mc_se_coverage` uses the observed p, so it is 0 at 25/25. | Cosmetic (manuscript correctly uses 4.4 points). | Use nominal p or Wilson. |
| B10 | `shared/sql/lib/01_stats.sql:60-62` via `part-c-ipm/estimation/sql/10_expansion.sql:38` | `fsd` divides by count − 1 with no guard; a stratum of one unit gives a NULL interval. | Not triggered at 330/stratum. | Guard as `ipm_moments` does. |
| B11 | `manuscripts/scripts/build_tables.py:57` | Joins parametric estimates to the fixed-run `truth.json`. | Same truth today; fragile. | Read each run's own truth. |
| B12 | `part-d-ipm/estimation/simulation.py:190-191` vs `errors/sql/07_population_truth.sql:68` | "In error" defined as `cor != sub` in the kernel but `active` in truth; a partial with e ≈ 0 rounds to equality. | Negligible. | Document, or define `active` as `cand_gdc <> gdc`. |

### 2.3 Correctness concerns that bear on the conclusions

**C1. The parametric interval appears to understate the simulation estimator's own sampling variability by roughly 7–10% in Part C and EIPM.** Redrawing the production audit many times from the committed populations (2,000 Part C audits; 300 EIPM audits) and applying a linearized version of the simulation's plug-in estimator gives a true SD of about 50.8 bp (Part C gross) and 17.8 bp (EIPM gross), against reported parametric SEs of 47.2 and 16.1 bp; the ratio estimator's reported SE (54.65 and 17.92) matches its exact design SE. If this holds for the full kernel, the genuine efficiency gain of the simulation estimator over the ratio estimator is about 7.5% (Part C) and 4% (EIPM), not the 11% in Table 4, the audit-size shares become about 86% and 92% rather than 79% and 80%, and the expected coverage of the parametric interval is about 92–93%, which 25 audit years cannot distinguish from 95%. The omitted variance has three identifiable sources in the code: error sizes are held fixed (`f_loss` at `part-c-ipm/estimation/simulation.py:104,133`; the income-ratio list at `eipm/estimation/simulation.py:94,114`); the 30 Part C rates are redrawn as independent binomials (`simulation.py:126-127`) although a contract coding-intensity factor (`01_contracts.sql:17`, `04_apply_errors.sql:42`) and missing documentation correlate them within an audit; and the redraw conditions on the realized n_k. This check is approximate (linearized estimator); the clean test is to run ≥200 audit years and compare the parametric half-width to the empirical SD of the simulation's point estimate, which the existing pipeline can do with `--set reps=200`.

**C2. The width and point-accuracy advantage of the simulation is model-dependent, and the model is true by construction.** Every program's error-application SQL activates errors independently of payment size within stratum (`part-d-ipm/errors/sql/04_apply_errors.sql:8`; `cert_02_apply_errors.sql:18` — in CERT it does not even vary by stratum; Part C checked: failed and supported HCCs have identical mean months and county rate). The simulation borrows only count rates from the audit and takes every recipient's error size from the population; the dollar-weighted ratio and expansion estimators do not assume this and pay for it in variance. This is the whole explanation of the Part D "63% narrower" headline: on the same 5,000-PDE audit the expansion's point estimate has an empirical SD of 0.54 pts against 0.11 for the simulation, because specialty PDEs (lognormal(8.3, 0.6), 0.6–0.8% of PDEs) carry 31–33% of error dollars and a dollar-weighted rate is at their mercy while a count rate is not. In the manuscript's own language (§4.3) this is a model-*based*, not model-assisted, gain. Appendix B.6 item 3 lists the independence assumption for PERM, CERT and EIPM only and omits Part C and Part D, the two programs where it matters most. **A robustness scenario with payment-dependent error probability (and size-correlated taints, and optionally within-stratum clustering) is required before the recommendation can stand; see change R1.**

**C3. Part D has no fair same-audit analytic comparator.** (a) The ratio and regression comparators use a different audit that reviews every PDE of 990 beneficiaries, about 41,000 PDEs — eight times the review volume of the 5,000-PDE audit — so they are not "a smaller audit." (b) The "expansion" on the PDE audit applies a uniform haircut GDC × (1 − r_h) to every PDE (`simulation.py:228`) and reruns the nonlinear benefit; that plug-in, not "the stratum-average rates," is the source of the −5.7% bias, and its delta-method SE (0.37) understates its own sampling SD (0.54), so §4.3's "its delta-method interval is wide" has the direction wrong. A fair comparator exists: compute each audited PDE's marginal Medicare-payment effect (rerun the beneficiary with only that PDE corrected) and apply the shared HT/ratio macros over PDEs. Until that is implemented, the Part D width result should leave the Abstract and Conclusion.

**C4. Twenty-five audit years cannot support the ordering claims.** Per-program coverage counts of 23, 24 and 25 are indistinguishable (MC SE 4.4 points); §4.3's "equal or higher coverage in every program" and the pooled 121/125 vs 111/125 read as established orderings. Report the width-to-empirical-SD ratio alongside coverage, and either increase to ≥200 audit years for the gross rate (the simulation stages are the only slow part) or hedge the Abstract and Conclusion to match §5.4.

**C5. The simulation is given population structure and the error-generating model that the analytic estimators are denied.** HCC lists, severity, county rate and months (Part C); benchmark, household size, income and months (EIPM); every PDE's GDC (Part D); whole-year beneficiary eligibility status (PERM). The donor kinds and size rules mirror exactly how the errors were fabricated. The manuscript says this in one clause (§4.3 "known structure of the population"); it should say it plainly in Methods and treat the regression estimator with richer predictors as the fair model-assisted comparator.

**C6. PERM eligibility in the simulation uses a whole-year beneficiary attribute.** `perm_simulation.py:80-84,107-108` applies an audited beneficiary's eligibility finding to all of their payments and flags non-audited beneficiaries as units; real PERM determines eligibility as of the sampled payment's month. Audited beneficiaries are selected with probability proportional to their number of payments; the estimate is unbiased only because eligibility error is independent of payment count by construction. Not stated anywhere.

**C7. Smaller items.** Part D's lowest-decile stratum gets n_h ≈ 4 under Neyman (so f = 0 in most years and 418,573 PDEs are assigned no errors); Part D underpayments are structurally tiny ($0.02B vs FY 2025 $0.52B) because of the error configuration, so "underpayments stay hard" is a property of this configuration; `brand` and `specialty` are drawn independently (`01_population.sql:38-39`), so 85% of the $4,000 specialty PDEs are treated as generic (40% reinsurance, no manufacturer discount); EIPM assigns monetary findings to applications at the 600% FPL cap that cannot have them (`02_apply_errors.sql:51` vs `simulation.py:108-115`), a small downward bias beyond the one stated in B.4; the PERM systematic-after-sort variance uses the SRS formula (conservative; consistent with 23/25) and should be stated in §3.4.

### 2.4 Assumptions in code that the manuscript does not state

Appendix B should add, by program (file references in the working reports):

- **All programs:** error probability independent of payment size within stratum applies to Part C and Part D too (B.6.3); Neyman inputs are the population SD of the *true* error (stated, but note it favors the analytic estimators); the four measures share one audit; percentile interval uses linear interpolation on 1,000 draws; fixed and parametric runs share the scenario seed.
- **Part C:** additional HCCs only when no overpayment and no missing documentation; half of unsupported severe HCCs are hierarchy moves, mild HCCs always deleted; chart-review HCCs have 3× the failure probability (15% of draws); contract coding intensity lognormal(−0.08, 0.40) multiplies every HCC's failure probability; probabilities capped at 0.95; missing documentation only with ≥1 HCC, p = 0.003 × multiplier; 85% full-year, months uniform 1–11 otherwise, demographic score 0.35 + 0.30·Kumaraswamy(2,3); the expansion prices risk-score error with one national mean of county rate × months; **a failed HCC loses the HCC's mean audited loss, not a draw from the list** (§3.5 step 2, §3.6 and A.5 step 4 say "drawn uniformly" — B.1 is right, the method sections are wrong); the 30 rates are redrawn as independent binomials given the realized n_k; §5.3's "two binomial draws per stratum" is 30 draws per iteration in Part C.
- **Part D:** brand (15%) and specialty independent; all LIS enrollees pay $4.90/$12.15 (no $1.60/$4.80 tier, no $0 for institutionalized duals — this overstates the enrollee share in the LTC stratum that carries 25% of error dollars); direct subsidy is a constant per beneficiary chosen to hit $105.56B (no risk adjustment, DIR or risk corridors); the manufacturer discount affects plan liability only and never enters Medicare's payment or y (B.2 lists it as part of the payment function); one plan year; PDE counts lognormal(3.3, 0.9); low-cost stratum = lowest decile of non-LTC GDC; expansion = uniform haircut plug-in; **the 5,000-PDE stratified audit and the 990-beneficiary SRS are not the published design** (§3.2's illustrative list omits Part D; `config.yaml:49` labels only the beneficiary audit).
- **PERM:** whole-year eligibility attribute propagated to all payments; one FMAP per state; no denied claims; MC capitation 380 × lognormal(0, 0.45); FFS partial taint Kumaraswamy(2,2); systematic-after-sort variance = SRS formula; within-beneficiary clustering ignored (≈4–5 same-beneficiary pairs per 520; fine, worth a sentence). Divergences from real PERM to state: 9 states in one cycle rather than 17 per cycle on a 3-year rotation; fixed 520 rather than state-specific precision-driven sizes; equal-count quintiles rather than dollar strata drawn quarterly; claim-level FMAP (90% for expansion adults) not modeled.
- **EIPM:** income-ratio factor max(r, 1/r), r ~ lognormal(0, 0.35); supported income capped at 600% FPL; monetary candidate with correct APTC ≥ x is "none"; household size 1 + ⌊4u^1.6⌋; age 21–64 uniform; FPL 100 + lognormal(4.6, 0.75) capped 600; 75% full-year; benchmark age-rated; applicable percentage falls back to 8.5% outside bands; Neyman uses population gross y, largest-remainder rounding, minimum 2 per stratum.
- **CERT:** error probability independent of claim size *and* of stratum; underpayments are all partial coding errors; no denied claims (so no CERT-style underpayments from improper denials); no MAC jurisdictions; real CERT strata are claim type × jurisdiction (the "≈100 service-level strata per type" in B.5 is supported by the CERT Methodology document and should cite it); 37,651 should cite Supplemental Table A1.
- **Regression:** fallback counts errors in any domain and requires n_m ≥ terms + 5; plain (not g-weighted) residuals, within-stratum s² with ddof = 1; the point estimate for gross/net is linear in over/under but the interval is not.

### 2.5 Manuscript claims not matched by the code or evidence

1. §4.1 "only rerunning the benefit captures this effect… the stratum-average rates used by expansion run 5.7% low" — the expansion does rerun the benefit; the bias comes from the uniform-haircut plug-in on a nonlinear function.
2. §4.3 "Its delta-method interval is wide" — it is too narrow for its own variability (C3).
3. §3.7, §4.3, Table 4 "the only analytic method on the same PDE audit" — the only one *implemented* (C3).
4. §3.5 steps 1–2 and "equivalent to giving every unit the finding of a uniformly drawn audited donor" — not true for Part C (mean loss) and only approximately for EIPM.
5. §3.3/A.4 "netted within the payment unit" — true of the population; the Part C kernel nets across mechanisms the population never combines (B1).
6. §4.3 "two sources" of the width gain — omits the understatement in C1 and the model-dependence in C2.
7. §4.4 Part C underpayments 19/25 attributed to sparsity — partly B1.
8. §5.3 "two binomial draws per stratum per iteration" — 30 per iteration in Part C.
9. A.2 "byte-identical at any thread count… tested in test_determinism.py" — tested only for EIPM and Part C errors and EIPM estimation; numpy `Generator` streams and LAPACK `lstsq` are not pinned, so "identical" holds within one pinned environment.
10. A.1 "expansion and ratio tested against an independent numpy implementation" — true for the shared macros, not for the Part C risk-score expansion or the Part D expansion.
11. `shared/tests/test_simulation.py:61` refers to a README discussion of gross bias that does not exist.

### 2.6 Test suite and packaging

Strong: independent per-unit numpy references for the shared estimators, cent-exact payment-function tests, the census check, sampler and RNG tests. Gaps, in order of what they would have caught here: (1) no test that any interval attains nominal coverage or that a reported SE matches the empirical SD on a toy population with thousands of replicates — the only kind of test that would reveal C1; (2) no per-domain unbiasedness test for the Part C kernel at production audit size — would have caught B1; (3) no independent SE check for `regression.py` when predictors are used, and no df test; (4) no test of `ipm_score`, `report.sql` or `build_tables.py` arithmetic; (5) no reference test of the Part C or Part D expansions; (6) tolerances of 1–3% in the bootstrap-rate tests are loose relative to the biases that matter. Packaging: `numpy`, `scipy` and `pyarrow` float while the simulation's randomness is numpy `Generator`; add a lock file and record numpy/scipy/numba/BLAS versions in `manifest.json` (`engine.py:230-233` records only duckdb and python); `requirements.txt` duplicates `pyproject.toml` by hand; `build_tables.py` hard-codes scale factors that already live in the populations and in `report.sql`; `--set k=v` overrides only `defaults`, so a scenario-level key silently wins (document, since the robustness scenario will rely on this).

---

## Part 3. Independent re-run (QA checklist sections A–H)

**Outcome: REPRODUCED EXACTLY.** All 183 published output files are byte-for-byte identical to the files produced here (`verification/verify_check.txt`, `verification/file_inventory.csv`: 0 rows with `NO`); the 38 automated tests pass; the single-thread EIPM run (checklist E2) gives identical SHA-256 fingerprints for all five output files.

**Environment** (`logs/run_2026-10-21_145729/environment.txt`): a fresh `git clone` of commit `33c6c470…` into an empty folder; Linux 6.18 x86_64, 2 cores, 7.8 GB; Python 3.13.16; DuckDB 1.5.6, numpy 2.5.4, numba 0.68.0, pyarrow 26.0.0, scipy 1.18.1. Setup followed `start-here/README.md` steps 1–5 without deviation.

**Runs** (`RERUN_SUMMARY.md`, `logs/`): quick trial 2m 28s ("Your setup works"); full replication started 14:57 ET. The first run was stopped by the reviewer's own background-process time limit during Stage 3 (the fixed-rate CERT run) and was resumed as the guide prescribes (`--only 3`, then `--from 4`); every stage finished once, in order. Stage times: 1 — 1m 17s; 2 — 1h 05m 15s; 3 — 1h 02m 59s; 4 — 58m 23s; 5–8 — about 1 minute, all within 10% of the published times.

**Checklist** (`review/QA_Checklist_2026-10-21_Claude.xlsx`): 90 tasks; 74 Pass, 15 Fail, 1 N/A (H4, the signed attestation, which an AI reviewer cannot provide). Every Fail carries an issue ID. Section B (re-run) and section D's numerical checks (README tables, manuscript tables and text, one-pager, abstract, Table 1, figures, calibration targets, truth files, the hand-recomputed Part C median and coverage count) all pass. The Fails are in section C (code vs description), D14–D15 (conclusions and limitations), F3–F4 (references and disclosures) and G4 (data dictionary).

**Issues log:** 19 issues — 4 Major (I-02 Part C kernel netting bias; I-03 parametric interval narrower than its estimator's true SD; I-04 model-dependent width gain, robustness scenario needed; I-05 Part D comparator), 13 Minor, 2 Notes. The example issue I-01 (Part C `design.yaml` sample size) is confirmed. Because four Major issues are open, the Summary sheet reads NOT YET ready to sign; this is the correct state until the author decides on the changes in Part 6.

**Review folder contents:** this document; the completed checklist; `review_citations.md`, `review_shared_partc_eipm.md`, `review_partd_perm_cert.md` (working reports with file and line references); `scripts/` (the standalone verification scripts used for the numerical checks, which read the committed populations and results and modify nothing).

---

## Part 4. Writing and style

The manuscript is clear and the numbers are right. The edits below bring it to the register of the dissertation and of the journals named in `manuscripts/README.md` (JSSAM, HSORM, Survey Methodology) and *Health Services Research*.

### 4.1 Structure (match the dissertation)

1. Rename and reorder to: **1 Introduction** (1.1 Background, 1.2 Prior Research, 1.3 Policy Context, 1.4 Study Purpose); **2 Methods**; **3 Results**; **4 Discussion** (4.1 Principal Findings, 4.2 Policy Implications with "Recommendation 1 – …", "Recommendation 2 – …", 4.3 Future Research, 4.4 Limitations, 4.5 Conclusion). The current Purpose (§2), Future Research (§6) and Conclusion (§7) are free-standing sections.
2. Write Recommendations as numbered, titled paragraphs ("Recommendation 1 – Adopt parametric-rate simulation for the gross rate", "Recommendation 2 – Discontinue fixed-rate intervals", "Recommendation 3 – Confirm coverage at reduced audit sizes before reducing them") addressed to policy makers and stakeholders.
3. Open Limitations with "The major limitation of this study is the number of audit years…" and open Future Research items with "Future research should…".
4. Move the law-of-total-variance derivation (§4.2) and the √(n/N) table from Results to Methods (as the expected behaviour) or to Discussion (as the explanation); Results should narrate what was observed ("These results show that…").
5. Results §4.1 has an unnumbered inline table followed by `{{TABLE3}}`, so Table 3 appears twice in different forms; §4.3 and §4.4 likewise contain inline tables that duplicate Tables 4 and 5. Keep one table per result and narrate the rest in prose.
6. Convert the bulleted Methods and Results to prose paragraphs. The dissertation uses bullets only for enumerations that are read as lists; the manuscript uses them for argument, which journals will not accept.

### 4.2 Register and word choice

- Replace conversational phrasing: "The interval is not a formality", "far too narrow", "simply too short", "it is important to establish what the bootstrap simulation does well", "It should be clearly noted that", "barely been tested", "visibly asymmetric", "the answer is consistent", "None of these programs comes close", "This is not a tuning problem". Prefer "These results show that the fixed-rate interval is substantially narrower than its sampling variability implies."
- "audit-years" (hyphenated) and "audit years" both appear; use "audit years" throughout. "Audit-finding bootstrap simulation" should be renamed as in Part 1.2(5).
- Use "as opposed to", "for example", "In addition", "However", "Given that", "Rather" as connectives (already present in places); remove "namely", "exactly where", "the opposite of what".
- In-text citations in the dissertation form: "A 2023 study by Edwards et al. showed…", "Kvanli and Schauer found…", rather than parenthetical stacks.
- Define each acronym once (PIIA, OMB, CMS, PERM, EIPM, CERT, HCC, PDE, APTC, LTC, LIS, GDC, FPL, MAC, SRS, FPC, SE) at first use in the main text; several (GDC, LIS, FPL, SRS) are first defined in the Appendix.
- Measured hedging: "likely", "may", "it is not clear whether" in place of "will", "would permit", "is simply".

### 4.3 Abstract and front matter

- The abstract is about 380 words; HSR and JSSAM allow 250–300. Cut the methods detail and the Part D width figure.
- Remove "the law requires that each estimate include a 95% confidence interval" (Part 1.2(2)).
- Remove "would permit audits roughly 20–38% smaller" from the Abstract and Conclusion until C1, C2 and R1 are resolved; keep it in Discussion as a projection.
- Complete affiliation, funding, conflicts and the employer disclaimer before any circulation.

### 4.4 Literature review

- Replace the in-line hyperlinks with numbered or author–year references; a journal will not take URLs in running text. Replace secondary sources (MyChesCo, Milliman, STAT, BPC, a conference bio) with the primary documents (M-21-19, the court opinion and docket, the statute, the CMS press release) and keep the secondary ones only where they add something.
- Remove time-stamped editorial statements ("appeared skeptical of the government's position") that will be stale on publication.
- Apply the corrections in Part 1.3.

### 4.5 One-pager and conference abstract

Both are consistent with the manuscript. Apply the same hedging to "20–38%" and the Part D 63% figure, and change "The simulation reuses the audited error rates…" to the plug-in/parametric terminology once adopted. The one-pager's Part D footnote already says the comparator is weak; after C3 it should say there is no fair same-audit comparator.

---

## Part 5. Overall assessment

**Worth.** This is a useful and publishable study. The replication package is unusually complete (one-command reproduction, byte-level manifests, a QA workbook, synthetic data only), the estimator code is correct, and the central structural point — a simulation that reuses the audited rates reports the reassignment variance and not the sampling variance, and its interval shrinks as the population grows — is right, easy to communicate, and directly actionable by any program that extrapolates by simulation. The parametric-rate correction is the right first fix and costs nothing to implement.

**Robustness.** The evidence currently supports two conclusions firmly and two weakly:

- *Firm:* fixed-rate intervals are invalid (30/125, width 5–21% of analytic); the parametric point estimate is at least as accurate as the analytic estimators under the stated assumptions.
- *Firm with a caveat:* parametric intervals cover at about the nominal rate for the gross rate (121/125), but with 25 audit years per program the data cannot distinguish 96.8% from 92%, and an approximate Monte Carlo check suggests the interval is 7–10% too narrow for its own estimator in Part C and EIPM.
- *Weak:* "narrower than the analytic interval" and "20–38% smaller audits." Part of the narrowness is the understatement above; the rest is a model-based gain that holds because errors were fabricated independently of payment size within strata, and in Part D the comparator is not a fair one. The recommendation to CMS rests on the weak pair.

**Reasonable steps to make it better, in order:**

1. Fix B1 and re-run Part C; add the per-domain unbiasedness and SE-calibration tests so the fix is guarded.
2. Run the gross rate with ≥200 audit years for every program (only the simulation stages are slow) and report, per program and method, the empirical SD of the point estimate, the mean half-width ÷ (1.96 × empirical SD), and coverage with its Monte Carlo SE (Morris et al. 2019). This settles C1 and C4 with the existing pipeline.
3. Build the robustness scenario (R1 below): payment-dependent error probability, size-correlated taints, optional within-stratum clustering, calibrated to the same true rates; report Appendix D. If the simulation's width-to-SD ratio falls well below 1 while the ratio estimator's holds, narrow Recommendation 1 to "parametric rates plus a unit-level error model" (already Future Research item 2).
4. Implement a fair Part D same-audit analytic comparator (marginal payment effect per audited PDE, then HT/ratio over PDEs) or drop the Part D width comparison from the headline results.
5. Reframe novelty (Rubin 1987, Valliant–Dorfman–Royall 2000), rename the fixed-rate method, state every assumption in Part 2.4, and harmonize the two documents (Part 1.2).
6. Apply the writing edits in Part 4 and the citation corrections in Part 1.3.

With steps 1–4 done the paper would be a strong submission to *Survey Methodology* or JSSAM; without them, a referee at either journal will ask for exactly these before accepting the recommendation.

---

## Part 6. Consolidated change list

Ordered by priority. **R** = results-affecting (requires a re-run and changes a reported number); **M** = manuscript/review text; **D** = repository documentation and code hygiene.

### Tier 1 — needed before the recommendation can stand

| # | Change | Where | Why |
|---|---|---|---|
| R1 | **Add the robustness scenario** as a sub-folder (`robustness/` with one config per program) and **Appendix D**: (a) error probability rising with log(payment) within stratum (and a falling variant); (b) partial-error size correlated with payment; (c) optional within-stratum clustering (contract / provider / state effect). Recalibrate each with the same closed-form multiplier so the true gross rate matches the base run. Same 25 audit years and designs, every method; report coverage, width, and half-width ÷ (1.96 × empirical SD). Point to it from Limitations and the Recommendation. | new `robustness/`; `manuscripts/sections/04_appendix.md`; §5.2, §5.4 | Part 2 C2 / I-04 |
| R2 | **Fix the Part C kernel netting bias** (apply additions only to recipients with no failure in the iteration, or redefine the addition-rate denominator), add a per-domain unbiasedness test at production audit size, re-run Part C (both rate versions) and regenerate tables. | `part-c-ipm/estimation/simulation.py:137-143`; `shared/tests/test_simulation.py` | I-02 |
| R3 | **Run the gross rate with ≥200 audit years** for all five programs (`--set reps=200`) and add to Table 2 (or a new table): empirical SD of the point estimate, mean half-width ÷ (1.96 × SD), and coverage with its Monte Carlo SE (Morris et al. 2019). Re-derive the width ratios and audit-size projections from these. Consider resampling partial sizes and modeling correlated HCC rates if the ratio is below 1. | configs; `manuscripts/scripts/build_tables.py` | I-03, I-14 |
| R4 | **Part D comparator:** implement a PDE-level HT/ratio estimator on the 5,000-PDE audit using each audited PDE's marginal Medicare-payment effect (or state plainly that no fair same-audit comparator exists) and remove the 63% / 37% / "13% of the audit" figures from the Abstract and Conclusion. Correct §4.1 (the expansion does rerun the benefit; the bias is the uniform-haircut plug-in) and §4.3 (its interval is too narrow for its own SD, not wide). Note that the 990-beneficiary audit reviews ≈41,000 PDEs. | `part-d-ipm/estimation/`; §3.4, §3.7, §4.1, §4.3, §5.4, Abstract, §7 | I-05 |
| M1 | **Hedge the headline** until R1–R4 are in: Abstract and Conclusion say "valid and narrower" and "would permit audits roughly 20–38% smaller"; move the audit-size projection to Discussion as a projection and state the 25-audit-year limit there. | `00_front.md`, `03_future_conclusion_refs.md` | I-14 |

### Tier 2 — correctness of the description (no re-run)

| # | Change | Where | Why |
|---|---|---|---|
| M2 | State every assumption in Part 2.4 in Appendix B, by program; extend B.6 item 3 (independence from payment) to Part C and Part D; add Part D's PDE strata and both audit sizes to the "illustrative" list in §3.2. | `04_appendix.md`, `01_background_methods.md` | I-11 |
| M3 | Correct the method text to match the Part C kernel: a failed HCC loses the HCC's mean audited loss (§3.5 step 2, §3.6, A.5 step 4); "equivalent to a uniformly drawn donor" does not hold for Part C; §5.3 "two draws per stratum" → 30 draws per iteration in Part C. | §3.5, §3.6, §5.3, A.5 | I-10 |
| M4 | Rename the methods: "plug-in audit-finding simulation" (fixed rates) and "parametric-bootstrap audit-finding simulation" (parametric rates); reserve "bootstrap" for the latter. | throughout; README; one-pager; abstract | Part 1.2(5) |
| M5 | Reframe novelty: present the fixed-rate failure as the single-imputation / plug-in problem demonstrated in the CMS setting; cite Rubin (1987), Rubin (1981), Valliant, Dorfman & Royall (2000); describe the width gain as model-based. | §1.3, §3.6, §4.2, §4.3 | Part 1.2(4), Part 2 C2 |
| M6 | Make the policy claim conditional: "if a program's simulation holds the audited rates fixed…"; note that no CMS program is shown to use a fixed-rate simulation and that the Part D S&EMP should be checked. | §5.1, §5.2 | Part 1.2(6) |
| M7 | Harmonize the two documents: remove "the law requires a 95% confidence interval"; change "the published Part D interval is already simulation based" to the review's wording; change review §8 and reference G to "implements the first stage of this agenda"; reconcile the review's program priorities (Part C low, CERT low–medium) with the manuscript's blanket recommendation. | Abstract, §1.1, §1.2; review §8, refs G | I-17 |
| D1 | `README.md:14` and `shared/ipsim/simulation.py:27-28`: remove the "108,000-beneficiary sample"; the simulation uses no beneficiary sample; ratio/regression use an SRS of 990. | | I-08 |
| D2 | PERM documentation: `perm-cert/README.md:17,40`, `perm.yaml:46`, `perm_01_population.sql` header, `shared/data_dictionary.md:110` — describe the design the code implements (equal-count quintiles within state × type, Neyman, systematic after sort, variance as SRS); state the whole-year eligibility propagation (or attach the finding to the sampled payment only). | | I-09, I-18 |
| D3 | `part-c-ipm/errors/config.yaml:39-42`: reference the estimation allocation or drop sample sizes from `design.yaml`. | | I-01 |

### Tier 3 — code hygiene and tests

| # | Change | Where | Why |
|---|---|---|---|
| D4 | Parametric redraw: draw f̃ = Binomial(n, p) first, then q̃ = Binomial(f̃, q)/f̃; or restate §3.6 as conditional on the observed f. | `part-d-ipm/estimation/simulation.py:204`; `perm_simulation.py:94`; `cert_simulation.py:197` | I-06 |
| D5 | Regression: `df = n − terms`; count the <10-error fallback per domain or document the rule as implemented. | `shared/ipsim/regression.py:82,92,110` | I-07 |
| D6 | Add tests: (a) coverage and SE-calibration on a toy population with thousands of replicates for ratio and the parametric simulation; (b) per-domain unbiasedness of each kernel at production audit size; (c) regression SE and df with predictors; (d) `ipm_score`, `report.sql` and `build_tables.py` arithmetic; (e) reference tests for the Part C and Part D expansions. Tighten the 1–3% tolerances. | `shared/tests/` | I-16 |
| D7 | Guard `fsd` against a single-unit stratum; make `build_tables.py` read each run's own `truth.json`; fix `mc_se_coverage` (nominal p or Wilson). | `shared/sql/lib/01_stats.sql`; `build_tables.py:57`; `02_estimators.sql:144` | I-15, I-16 |
| D8 | Reproducibility: add a lock file (`pip freeze` / `uv.lock`), record numpy/scipy/numba/BLAS versions in `manifest.json`, derive `requirements.txt` from `pyproject.toml`, extend `test_determinism.py` to every program, and change A.2 to "identical within one pinned environment". Document that `--set k=v` overrides `defaults` only (the robustness scenario will depend on this). | `pyproject.toml`; `engine.py:230-233,262`; A.2 | I-13 |
| D9 | Record the pre-IRA reference and the `test_simulation.py:61` README reference correctly (there is no README discussion of gross bias). | `shared/tests/test_simulation.py` | Part 2.5(11) |

### Tier 4 — references and writing

| # | Change | Where | Why |
|---|---|---|---|
| M8 | Apply the citation corrections in Part 1.3 (ED OIG year/number; Humana reporter cite; GAO number; CMS fact-sheet year; CERT precision source; RADV "~550" source; EIPM 0.43-point source; SBE 2027 source; statutory threshold source; Kvanli & Schauer, Kolenikov, Liu, Edwards et al. characterizations; orphan references; P.L. 119-21 entry; §1.3 cross-reference). | manuscript References; review §3–§6, References | I-12 |
| M9 | Add the missing citations in Part 1.4, especially Edwards (2011) HSORM (ratio vs expansion in Medicare audits), Cox & Snell (1979), Rohrbach (1993), Howard (1994), Bickel & Freedman (1984), Rubin (1987), Valliant–Dorfman–Royall (2000), Morris–White–Crowther (2019). | §1.2, §1.3, §3.1, §3.6, §4.4; review §4, §6, Group C–E | Part 1.4 |
| M10 | Restructure to the dissertation outline (Introduction with Background / Prior Research / Policy Context / Study Purpose; Methods; Results; Discussion with numbered "Recommendation N – …", Future Research, Limitations opening with "The major limitation of this study…", Conclusion); move the law-of-total-variance derivation out of Results; remove duplicate inline tables; convert bulleted argument to prose; define acronyms once in the main text; replace conversational phrasing; standardize "audit years"; cut the abstract to ≤300 words. | all sections | Part 4 |
| M11 | Literature review: replace in-line URLs with references; replace secondary sources (MyChesCo, Milliman, STAT, BPC, conference bio) with primary documents; remove time-stamped editorial statements; fix "under 1%", "$115 million", "visibly asymmetric", the one-sided/two-sided RADV bound description, and the unsourced Part C facts (7,000 records; ESRD/hospice). | review §3, §5, §6 | Part 1.3 |
| M12 | Complete affiliation, funding, conflicts, disclaimer and employer/agency clearance before circulation. | `00_front.md`, `03_future_conclusion_refs.md` | I-19 |
| M13 | One-pager and conference abstract: apply M1, M4 and the Part D wording from R4. | `manuscripts/one-pager.md`, `conference-abstract.md` | Part 4.5 |
