# Code review: Part D, PERM, CERT (subagent report, 2026-10-21)

## 0. Part D expansion 5x noisier than simulation (same 5,000-PDE audit) — NOT a bug
- Expansion (part-d-ipm/estimation/simulation.py:235-243) uses dollar-weighted stratum rate r_h = Σ(sub−cor)/Σsub; error dollars heavy-tailed (specialty PDEs lognormal(8.3,0.6) ≈ $4,000+, 0.6–0.8% of PDEs but 31–33% of error dollars). Rel SE of r_h 0.59 (LTC)/0.50 (other) → ≈0.55 pts, matches observed 0.54.
- Simulation (simulation.py:196-214) borrows only count rates p=f/n, q=g/f; each recipient's size is its own GDC from the population. Rel SE of p 0.11/0.096 → ≈0.11 pts, matches.
- So the Part D "37% of analytic width / 13% of audit" headline is a consequence of the simulation's implicit model (incidence independent of GDC within stratum) being true by construction (04_apply_errors.sql:8). Present as model-dependent.
- Expansion's delta-method SE understates its own sampling SD by ~32% (0.37 vs 0.54); all 7 misses below. Manuscript §4.3 "Its delta-method interval is wide" has the direction wrong.
- 108,000 vs 990: code uses SRS of 990 (config.yaml:25-26, 01_frame.sql:29-33). README.md:14 ("beneficiary sample (108,000 beneficiaries)") and shared/ipsim/simulation.py:27-28 docstring are wrong/stale.
- The 990-beneficiary audit reviews every PDE ≈ 41,000 PDEs — ~8x the review volume of the 5,000-PDE audit; not stated.

## 1. Bugs
1. README.md:14 — 108,000 "sample"; fix to "beneficiary audit (990, ratio and regression only)".
2. shared/ipsim/simulation.py:27-28 — stale docstring about Part D beneficiary sample.
3. perm-cert/README.md:17; perm.yaml:46 ("allocation: equal across quarters and strata"); perm_01_population.sql:11-13 describe "5 equal-dollar payment strata within state × quarter × payment type"; code builds equal-count quintiles within state × payment type, no quarter, Neyman. Align docs (design.yaml is auto-written from perm.yaml:design).
4. perm-cert/README.md:40 — "systematic sample's variance estimated as if stratified SRS" is under the CERT bullet; applies to PERM only.
5. part-d-ipm simulation.py:204; perm_simulation.py:94; cert_simulation.py:197 — parametric redraw draws q̃ ~ Bin(f, q)/f with observed f, not redrawn f̃ = n·p̃. Negligible, but not what §3.6 implies. Fix code or restate formula as conditional on observed f.
6. part-d simulation.py:190-191 vs 07_population_truth.sql:68 — "in error" defined as cor != sub vs active; partial e≈0 rounds to equality. Negligible.
No arithmetic bugs in benefit phases, LICS, Neyman largest-remainder, systematic/SRS selection, 02_estimators.sql, delta-method variance, PERM national pooling (perm_95_national.sql:40-56), CERT closed-form calibration.

## 2. Correctness / design concerns
2.1 Part D simulation uses population auxiliary info under an assumption true by construction; B.6 item 3 omits Part D.
2.2 Part D comparator not apples to apples: (a) ratio/regression use a different, ~41,000-PDE audit; (b) "expansion" applies uniform haircut GDC×(1−r_h) to every PDE (simulation.py:228) then reruns nonlinear benefit — source of the −5.7% bias; a fair same-audit analytic comparator exists (marginal Medicare payment effect per audited PDE, then HT/ratio over PDEs). "Only analytic comparator on the same audit" should read "only one implemented".
2.3 Part D stratum b (lowest decile non-LTC) gets n_h≈4 under Neyman; f=0 most years; Neyman inputs from population truth (40_simulation_inputs.sql:47).
2.4 Part D underpayments structurally tiny ($0.02B vs real $0.52B; under/gross 1.4% vs real 12%) — a property of configuration, not of Part D.
2.5 brand and specialty drawn independently (01_population.sql:38-39): 85% of $4,000 specialty PDEs treated as generic (40% reinsurance, no MDP).
2.6 PERM eligibility: simulation applies an audited beneficiary's whole-year status to all their payments (perm_simulation.py:80-84,107-108); real PERM determines eligibility as of the sampled payment's month. Audited beneficiaries selected ∝ number of payments (size-biased); unbiased only because eligibility error independent of payment count by construction. Not stated.
2.7 PERM national roll-up correct (T=Σθ̂_s X_s, Var=Σ(se_s X_s)²; iteration-wise pooling valid, seeds differ by state).
2.8 PERM systematic-after-sort variance uses SRS formula (conservative) — not in manuscript §3.4.
2.9 PERM within-beneficiary clustering ignored (≈4–5 same-beneficiary pairs per 520) — fine, worth a sentence.
2.10 Neyman inputs from truth in all programs (stated in B.6.4).

## 3. Program-fact accuracy
- Part D CY2025 parameters correct ($590, $2,000, 25%, plan 65/75, catastrophic plan 60%/reins 20% applicable/40% non-applicable, MDP 10/20, LIS $4.90/$12.15). Simplifications to state: LIS ≤100% FPL ($1.60/$4.80) and institutionalized duals ($0) not modeled (overstates enrollee share for LTC); MDP phase-in for LIS; biosimilars/selected drugs; DIR; risk corridors.
- Pre-IRA CY2023 correct ($505/$4,660/$7,400, 70% CGDP, 80% reinsurance, LIS $4.15/$10.35); discount applied to full GDC incl. dispensing fee; catastrophic min copays not applied (stated).
- Part D IPM real design: random beneficiary sample since FY2025, simulation-based extrapolation; FY2025 4.00%, $4.23B, over $3.70B, under $0.52B, denominator $105.56B, CI 3.57–4.46%; 75% missing documentation. The 5,000-PDE stratified audit and 990 SRS are NOT the published design; manuscript §3.2 must list Part D strata/sizes as illustrative (config.yaml:49 labels only the beneficiary audit).
- PERM real: 17 states/cycle, 3-year rotation, state-specific precision-driven sizes, FFS/MC separate components, denied claims in universe, claim-level FMAP (90% expansion adults). Divergences: 9 states/one cycle; fixed 520; equal-count quintiles; one FMAP per state; no denied claims; whole-year eligibility.
- CERT real: claims submitted incl. denied, strata = claim type × MAC jurisdiction, dollar-weighted ratio, A-to-B rebilling adjustment. "~100 service-level strata per type" (B.5) not found in public CERT docs — verify or drop. "±3 pts at 95%" — OMB allows ±2.5 at 90% or ±3 at 95%; confirm CERT's statement. 37,651 should cite Table A1.
- FY2025 headline figures match CMS fact sheet.

## 4. Assumptions in code not in manuscript
- Part D: error prob independent of GDC/brand/specialty within LTC/non-LTC (04_apply_errors.sql:8) → B.6.3
- brand (15%) and specialty independent; specialty mostly generic for benefit → B.2
- all LIS pay $4.90/$12.15 → B.2
- direct subsidy constant per beneficiary to hit $105.56B; no risk adjustment/DIR/corridors → B.2
- one plan year, PDE counts lognormal(3.3,0.9) → B.2
- low-cost stratum = lowest decile of non-LTC GDC; n_h≈4 → B.2 Audits
- expansion = uniform haircut plug-in → §3.4, §4.1
- q redrawn conditional on observed f → §3.6
- PERM eligibility whole-year attribute; propagated to all payments → B.3/§3.5
- one FMAP per state; no denied claims; MC capitation 380×lognormal(0,0.45) → B.3
- FFS partial taint Kumaraswamy(2,2) → B.3
- systematic-after-sort variance = SRS formula → §3.4
- CERT error prob independent of claim size AND stratum (cert_02_apply_errors.sql:18) → B.6.3
- CERT underpayments all partial coding → B.5

## 5. Manuscript claims not matched
1. §4.1 "only rerunning the benefit captures this effect… stratum-average rates used by expansion run 5.7% low" — expansion does rerun the benefit; bias is from uniform-haircut plug-in.
2. §4.3 "delta-method interval is wide" — it is too narrow for its own variability.
3. §3.7/§4.3/Table 4 "only analytic method on the same PDE audit" → "only one implemented"; 990-bene audit ≈ 41,000 PDEs (→ §5.4 item 4).
4. §3.2 illustrative strata list omits Part D.
5. B.6.3 omits Part D.
6. B.2 lists MDP in payment function; it affects plan liability only (05_benefit.sql:60).
7. B.3 matches code but perm-cert/README.md:17 and perm.yaml:46 contradict.
8. B.5 "~100 service-level strata" unsupported; cite CERT methodology for separate ratio.
9. §1.1 CERT precision statement — verify.
10. §3.6 q̃ formula vs code.
12. A.1 "tested against independent numpy implementation" does not cover Part D run_expansion.
13. README.md:14 contradicts manuscript (990).
