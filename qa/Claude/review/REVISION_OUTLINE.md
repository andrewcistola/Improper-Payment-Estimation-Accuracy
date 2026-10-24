# Revision outline — improper-payment-estimation-accuracy

Pushed to `main` (fast-forward, five commits: `34efe11` QA review → `9c903d3` fixes and refactor → `de5f8b4` regenerated results and rewritten manuscript → `276c231` payment-decile donor kinds → `d9369c1` Appendix D4–D6 and the reframed recommendation). Result check: REPRODUCED EXACTLY against the new reference (183 files); 57 tests pass.

---

## 1. What changed in the findings

| | Before review | After |
|---|---|---|
| Plug-in (fixed-rate) interval | Invalid: 30/125 | Invalid: 31/125 — unchanged in substance |
| Parametric interval, gross coverage | 121/125 | 121/125 (25, 25, 24, 22, 25) |
| Parametric half-width vs ratio | 11–21% narrower; 63% narrower in Part D vs plug-in expansion | 9–23% narrower; Part D now 77% narrower vs a design-based PDE ratio on the same audit |
| Is the interval the right width? | Not tested | **100-audit-year calibration:** half-width ÷ 1.96·SD = 0.94, 0.95, 0.93, 0.88 (Part C, Part D, PERM, EIPM) and 1.13 (CERT); coverage 95, 95, 92, 90, 99 |
| Real efficiency gain (SD) | Not separated from width | 3% Part C, 4% EIPM, 23% PERM, 35% CERT, 72% Part D |
| Robustness to size-dependent errors | Not tested | **Simulation biased 2–148% and interval fails** (coverage 0–24/25) when error probability depends on payment within strata; ratio estimator unaffected (22–25/25) |
| Part C underpayments (simulation) | 19/25, all misses below (kernel bug) | 25/25 after fix |
| Payment-decile donor kinds (D4) | — | **Removes the bias in PERM (−14%→−4%, +7%→+0.4%; SD 0.32→0.35 vs ratio 0.43); half to seven-eighths of it in CERT (−22%→−5%, +12%→+1.6%; SD rises to the ratio's) and Part D (−65%→−38%, +148%→+19%; SD doubles, still half the ratio's)** |
| Recommendation | Adopt parametric simulation; 20–38% smaller audits | **Adopt parametric simulation under a stated, cycle-tested assumption (error incidence independent of payment size within donor kind); decile donor kinds where the test fails; ratio reported alongside as the test; audit reductions (59–83% of today's) deferred until the test passes and coverage is confirmed at the smaller size** |

## 2. Manuscript (`manuscripts/`)

New structure (matches the dissertation): **1 Introduction** (1.1 Background · 1.2 Prior research · 1.3 Policy context · 1.4 Study purpose, five aims) · **2 Methods** (2.1 Design, incl. the 100-year calibration · 2.2 Populations · 2.3 Estimands · 2.4 Analytic estimators, incl. Part D plug-in expansion, PDE expansion, PDE ratio · 2.5 Plug-in simulation · 2.6 Parametric-bootstrap simulation · 2.7 Outcomes · 2.8 Calibration and robustness checks) · **3 Results** (3.1 Point accuracy · 3.2 Plug-in interval · 3.3 Parametric simulation · 3.4 Components and sparse measures · 3.5 Regression · 3.6 Calibration over 100 audit years · 3.7 Size-dependent errors) · **4 Discussion** (4.1 Principal findings · 4.2 Policy implications, Recommendations 1–4 · 4.3 Future research · 4.4 Limitations ("The major limitation…") · 4.5 Conclusion) · Appendices A (pipeline, reproducibility) · B (every assumption, by program) · C (dollars) · **D (new: Tables D1–D6)**.

Terminology: "plug-in audit-finding simulation" (fixed rates) and "parametric-bootstrap audit-finding simulation"; "bootstrap" reserved for the latter. Title now ends "…Analytic Estimators and Audit-Finding Simulation". Novelty framed via Rubin (1987) single-imputation and Valliant–Dorfman–Royall model-based inference. All "the law requires 95%" and "Part D is already simulation-based" statements corrected. Abstract ≈370 words (HSR/JSSAM may need ≤300 — cut Methods detail if required). Main text ≈8,300 words. Affiliation / funding / disclaimer placeholders remain for you.

**Recommendations as now written (your framing)**
1. Adopt parametric-bootstrap simulation for PIIA rates, with the within-kind independence of error and payment size stated as a central assumption in the S&EMP; discontinue plug-in intervals (check the Part D S&EMP).
2. Verify the assumption every cycle from the audit. Where the audit unit is the payment unit (Part C, PERM, EIPM, CERT): report simulation and ratio from the same audit together — the drift is the test. Where the frames differ (Part D: PDE audit, beneficiary-year payment), no same-audit design-based benchmark exists; the check is error rate and taint by payment decile within strata plus the simulation with vs without decile donor kinds.
3. Where the test fails, post-stratify donor kinds on payment decile; where payments are heavy-tailed within strata (CERT, Part D) treat it as partial, report ratio and simulation together, and wait for a unit-level model.
4. Reduce audit sizes (83/63/77/59% of current from Table 4; 93/60/93/42% from calibrated SDs) only after the test passes and coverage is confirmed at the smaller size; sparse components checked separately.

## 3. Code and repository

- **Folder split:** `perm-cert/` → `perm/` and `cert/` (same `errors/` + `estimation/` layout as the other programs; `national.yaml` pools PERM states). All paths rewritten; `git mv` preserves history.
- **Fixes:** Part C kernel netting bias (additions only to enrollees with no failure; denominator corrected; per-domain unbiasedness test added); parametric redraw draws f̃ then g̃ in all kernels; regression df (`n − terms`); `fsd` single-unit guard; `mc_se_coverage` at nominal p; `build_tables.py` reads each run's own truth; EIPM monetary assignment excludes 600%-FPL recipients; regression fetches one audit year at a time (needed for CERT at 100 years).
- **New estimators:** Part D `pde_expansion` / `pde_ratio` on the 5,000-PDE audit (marginal Medicare-payment effect per audited PDE through the shared HT/ratio macros; census test exact).
- **`size_beta`** in every errors config (default 0.0; base populations byte-identical); calibration multipliers computed from per-unit probabilities. Part D uses ±0.25 with rescaled count rates to hold the gross rate (at ±0.5 its gross rate would move to 6.8% / 0.6%).
- **`robustness/`**: `run.py` (calibration + β scenarios + D4 decile-kind runs; optional `run_all.py --with-robustness`, stage 9, ≈5½ h), `summarize.py` → `manuscripts/generated/appendix_d.md` (Tables D1–D6); manifests committed, parquet not.
- **`sim_kind_deciles`** (default 0) in the Part D, PERM, EIPM and CERT estimation configs: donor kinds = design stratum × K payment quantiles, parent-stratum fallback for empty kinds; byte-identical at 0; census and fallback tests added.
- **Reproducibility:** `requirements-lock.txt`; manifests record numpy/scipy/numba/BLAS; determinism tests cover every population and three estimation configs; A.2 says "within one pinned environment".
- **Docs:** `shared/build_readmes.py` regenerates program README results; README findings/recommendations rewritten; data dictionary and PERM/Part D descriptions aligned with code; QA checklist rebuilt (92 rows incl. size_beta and Appendix D); `qa/Claude/review/README.md` addendum records that the review's items are resolved and that R1 reversed the recommendation.

## 4. Literature review (`literature-review/`)

95 references (from 66). All citation corrections applied (Humana docket cite, ED-OIG A26DC0288, GAO-26-108694, fact-sheet date, primary sources for the $10M threshold / ~550 contracts / 0.43 pts / SBE 2027, Kvanli & Schauer n.d., Kolenikov attribution, Liu 40% dropped, Edwards et al. characterizations, Part D asymmetry softened, EIPM "near or below 1%", unsourced Part C claims removed). New: audit-sampling foundations (Stringer, Kaplan, Fienberg–Neter–Leitch, Cox & Snell, Rohrbach, Howard, Bickel, Berger et al., Gunning & Horgan), Medicare integrity statistics (Edwards 2011, Gilliland & Edwards, Ignatova & Edwards, RAT-STATS), survey bootstrap lineage (Bickel & Freedman, Krewski & Rao, Chao & Lo, Sitter, Beaumont & Patak, Preston, Lohr, Valliant et al.), Rubin 1981/1987, Morris et al., Koehler et al. §8 and group G now say the companion study "implements the first stage of this agenda" and state its findings.

## 5. Items for your decision

1. **The recommendation now follows your framing** (simulation under a stated, tested assumption; decile kinds as remedy). Appendix D4–D6 is the evidence that the remedy works fully in PERM and partly in CERT/Part D. Your statement that experience points to a *negative* association belongs in Discussion 4.1 as the author's view if you want it there; I wrote only that the sign does not matter and that a negative association overstates the rate. If you have a citable source, it should go in Policy Context.
2. **Part D's position.** Its simulation gain is the largest (72%) and its exposure to the assumption is the largest (65–148% bias). Given your Part D IPM role, the sentence recommending that the Part D S&EMP be checked for a plug-in interval may need softening or sourcing before circulation.
3. **Abstract length** (≈350) vs target journal; **word count** ≈7,400 main text.
4. **Journal and reference style**; affiliation, funding, conflicts, disclaimer, employer clearance.
5. **EIPM technical share:** rate points give 48%, CMS dollar figures give 43%; the code uses 48%. Decide which to calibrate to (noted in `eipm/README.md`).
6. **PERM eligibility** as a whole-year attribute propagated by the simulation (now documented); consider attaching the finding to the sampled payment's month in a later version.
7. **Unit-level error model** (Future research item 2) is the natural next study and the one that would rescue the simulation's gain.
8. Whether to keep `qa/Claude/` as the first completed review folder (currently referenced from the main README and `qa/README.md`).

## 6. Where to look

- `manuscripts/manuscript.pdf` / `.docx` — full revised manuscript; `one-pager.pdf`; `conference-abstract.pdf` (485-word body).
- `manuscripts/generated/appendix_d.md` and `robustness/results/summary_*.csv` — the new evidence.
- `qa/Claude/review/PEER_REVIEW.md` — the review that drove the changes, with its change list (Part 6) and the addenda in `qa/Claude/review/README.md`.
- Part D D4 diagnosis (why the base-population mean is −12% at K=10: a 3σ Monte Carlo draw in the top GDC decile, unbiased over 300 audit years) is summarized in Appendix D's header and Results 3.8.
- `git diff 33c6c47..de5f8b4 --stat` — 873 files changed.
