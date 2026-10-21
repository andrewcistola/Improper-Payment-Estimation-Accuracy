# Peer-review report: citation verification and literature framing

**Documents reviewed**
- `/tmp/claude-0/-home-claude/42cb9023-b3be-56b3-ab9a-06a6ce4302a7/scratchpad/repo/literature-review/improper-payment-estimation-accuracy-literature-review.md` (66 annotated references, Sections 1–9)
- `/tmp/claude-0/-home-claude/42cb9023-b3be-56b3-ab9a-06a6ce4302a7/scratchpad/repo/manuscripts/manuscript.md` (Background §1, Purpose §2, Methods §3, Discussion §5–6, References, Appendix B)

**Verification key.** ✅ verified against the source (fetched or confirmed by an independent bibliographic record); ⚠️ exists but citation details or characterization need correction; ❓ unverified (what I tried is stated). Several publisher sites (Project Euclid, Springer, PMC, CRAN, omb.report, crossref API, nap.edu front matter, Milliman) were behind bot-walls or permission gates in this session; those items were cross-checked through secondary bibliographic records (RePEc/IDEAS, numdam, SAS/Stata documentation reference lists, zbMATH/MaRDI) and are labelled accordingly.

---

## (A) Citation-by-citation verification

### A.1 Literature review — Group A: statute, guidance, program methodology

| # | Reference as written | Verified? | Issues | Suggested correction |
|---|---|---|---|---|
| 1 | PIIA 2019, P.L. 116-117 (Mar 2, 2020) | ✅ | None. | — |
| 2 | OMB (2021) M-21-19, Appendix C to A-123 | ✅ | Annotation says "the approval route for changing an interval method." M-21-19 states OMB does **not** formally approve S&EMPs; the plan and checklist are *submitted* (due June 30). Also: M-21-19 does **not** prescribe a 95% CI — it says agencies "must work with their statistician to determine the appropriate confidence interval." | Reword annotation: "the submission route (OMB review, not formal approval)." Cite M-21-19 directly (not the MyChesCo article) for the $10M/1.5% or $100M threshold, which M-21-19 §II.C states. Date: March 5, 2021. |
| 3 | CMS (2026) PIM Ch. 8, Rev. 13762 | ✅ | Rev. 13762 issued 05-27-26 confirmed. §8.4.5 contains all four quoted elements: one-sided 90% lower limit as demand; "may not be feasible to guarantee 90 percent coverage in all circumstances"; "standard statistics texts and journals"; demand reduced to total payment in frame when LB exceeds it. §8.4.4.2 seed documentation confirmed. | Section cite in text (§8.4.5) is correct; note §8.4 itself carries Rev. 906 (09-26-19). |
| 4 | CMS (2012) RADV Final Payment Error Calculation Methodology (Feb 24, 2012) | ✅ | 201 enrollees (67/stratum), three community-risk-score strata, stratified expansion, 99% CI z=2.575, LB less FFS Adjuster — all confirmed. | — |
| 5 | CMS (2025) PY 2019 RADV Methods (June 25/26, 2025) | ✅ | Version 2 dated June 25, 2025 (URL says 6-26-25). Top-decile frame, n=35, FPC (N−n)/N, z=1.645, PE = ΔR̄ × Σcᵢ, point-estimate recovery if LB>0 — confirmed. Minimum frame of 30 confirmed. | Date as "June 25, 2025 (v2)". See §B.4 on "one-sided" labelling. |
| 6 | CMS (2026) PY 2021 RADV Methods (May 29, 2026) | ✅ | Top-quartile frame; 35/50/100/200 by frame-size stratum; enrollee-month-weighted mean; Taylor expansion for partial-year; t(n−1); FPC; collect sampled enrollees only, extrapolation "reserved" — all confirmed. Document does **not** say whether 90% is one- or two-sided. | Say "lower bound of the 90 percent confidence interval, t(n−1)" without asserting one-sidedness. |
| 7 | CMS (2025) RADV Audits Fast Facts (July 2025) | ⚠️ | Fact sheet confirms "ALL RADV-eligible MAO contracts" from PY 2019 and 35–200 enrollees **starting PY 2020** (35 before). It does **not** contain the "~550 contracts" figure used in §5. | Source the ~550 figure to CMS press release, "CMS Rolls Out Aggressive Strategy to Enhance and Accelerate Medicare Advantage Audits" (May 21, 2025), https://www.cms.gov/newsroom/press-releases/cms-rolls-out-aggressive-strategy-enhance-and-accelerate-medicare-advantage-audits. |
| 8 | CMS (2023) RADV final rule, 88 FR 6643 (Feb 1, 2023) | ✅ | Full title: "Medicare and Medicaid Programs; Policy and Technical Changes to the Medicare Advantage, Medicare Prescription Drug Benefit, PACE, Medicaid FFS, and Medicaid Managed Care Programs for Years 2020 and 2021," 88 FR 6643–6665, FR Doc. 2023-01942, RIN 0938-AT59, CMS-4185-F2. Confirms: extrapolation from PY 2018; no FFS Adjuster; "We are not adopting any specific sampling or extrapolated audit methodology." | Add full title and doc number. |
| 9 | CMS (2025) FY 2025 Part C Error Rate Findings | ✅ | 6.09%; $23.67B gross; $19.20B net (4.94%); $21.43B over/$2.23B under; $388.72B denominator; missing documentation 0.22% ($869M). CY2020 change to underpayment calculation confirmed. **Not in document:** ESRD/hospice entering sample in FY 2024; sample size; confidence interval. | Mark the ESRD/hospice claim with its actual source or delete. |
| 10 | CMS (2023, 2025) FY 2023 and FY 2025 Part D Findings | ✅ | FY 2023: 3.72%, $3.35B, CI $2.63–4.17B (2.92–4.63%); methodology wording quoted exactly. FY 2025: 4.00%, $4.23B, CI $3.77–4.71B (3.57–4.46%), 75.00% missing/invalid documentation, random beneficiary selection replacing cohort for CY 2023. **Neither document says the interval is produced by resampling/simulation.** | Keep; fix characterization (see §B.2). |
| 11 | CMS (2025) PERM Manual (April 2025) | ✅ | Three cycles, rolling national rate, ERC eligibility review tied to sampled payments confirmed. Manual does **not** describe systematic selection or payment strata. | — |
| 12 | CMS (2024) PERM Supporting Statement B, OMB ICR 202408-0938-026 | ❓ | omb.report PDF failed twice (client error, proxy 403 on direct download). Could not confirm "systematic selection within payment strata after sorting by paid amount" or variance formulas. | Keep but verify; add OMB control no. 0938-0974 and the ICR reference. Until verified, soften "systematic after sorting" to "per the supporting statement" or confirm wording. |
| 13 | CMS, PERM Improper Payment Rate Calculation presentation | ✅ | Claims rate (FFS+MC weighted) + eligibility − overlap; three-cycle rolling national rate confirmed. No variance material. | — |
| 14 | CMS (2025) 2025 Medicare FFS Supplemental Improper Payment Data | ✅ | 6.55% (Table A1 shows 6.6% rounded), CI 5.9–7.2%; $28.8B; over $27.9B/under $1.0B; 49,061 sampled/37,651 reviewed; per-type counts 8,750/8,651/11,600/8,650; rates 3.1% IPPS–24.1% DMEPOS; error shares 53.0/15.3/12.0/11.1/8.5; claims Jul 1 2023–Jun 30 2024. Methodology = Appendix N. | — |
| 15 | CMS (2026) CERT Methodology (data.cms.gov, Jan 2026) | ✅ | ~100 service-level strata per type; <20 two-digit TOB strata for Part A excl. IPPS; generalized estimator → separate ratio estimator nationally; contractor clusters weighted by expenditure share; 37,500–50,000 claims. | — |
| 16 | CMS, Introduction to the CERT Program | ✅ | Four claim-type strata; ~37,500 reviewed; "Minimum of 95 percent confidence interval of plus or minus 3 percent"; paid and denied claims; 75-day/60-day documentation windows. | — |
| 17 | PaymentAccuracy.gov (2026) APTC program page | ⚠️ | FY2022–FY2025 overpayments, $0 underpayments FY2023–25, technically improper $282.44M (FY25), margin ±0.54 confirmed. **The "0.43 of 0.89 points" figure is not on this page**; it is on CMS's EIPM "Improper Payment Findings" page. FY 2025 rate not displayed on PaymentAccuracy.gov (only 99.1% accuracy). | Cite CMS EIPM Improper Payment Findings page for 0.43/0.89 (it states "In FY 2025, 0.43% of 0.89% was made up of Technically Improper Payments"). |
| 18 | CMS (2026) EIPM Program Background | ⚠️ | "approximately 2,000" applications confirmed. Page does **not** mention SBE start date; it describes CY 2024 scope. | Source the SBE 2027 date to 45 CFR 155.1605 (applicability "beginning January 1, 2027"). |
| 19 | 45 CFR §§155.1600–155.1650 (SEIPM) | ✅ | §155.1605 applicability Jan 1, 2027; §155.1610 three-year cycle; §155.1620 aggregate sample size allocated by expenditures/precision/prior rates; §155.1630 difference resolution and appeals. | — |
| 20 | P.L. 119-21 §71106, via BPC (2026) | ✅ | BPC article (Apr 8, 2026) confirms 3% eligibility threshold, disallowance from Oct 1, 2029, removal of good-faith waiver (42 CFR 431.1010). | Cite the statute directly in addition to BPC. |

### A.2 Literature review — Group B: oversight, litigation, commentary

| # | Reference | Verified? | Issues | Correction |
|---|---|---|---|---|
| 21 | GAO (2026) "Payment Integrity: FY 2025 improper payment estimates" | ⚠️ | Exists: **GAO-26-108694**, *Payment Integrity: Agencies' Estimated Improper Payments Increased to $186 Billion in Fiscal Year 2025*, April 27, 2026. $186B and MA $23.7B (6.1%) confirmed; IG reliability concern confirmed. | Use exact title and report number. |
| 22 | GAO (2016) GAO-16-76 | ✅ | Title correct; dated April 8, 2016 (released May 9, 2016). Findings on contract selection and timeliness confirmed; does not address extrapolation method. | — |
| 23 | HHS OIG (2026) OAS-26-17-042 | ✅ | *HHS Met Many Requirements, but Did Not Fully Comply With PIIA for FY 2025*, August 2026 (letter July 29, 2026). Evaluated S&EMPs for CCDF, Medicare FFS, and Part D's revised plan. | Add title. |
| 24 | ED OIG (2025) "Compliance with PIIA" — linked as "FY 2025 review" | ⚠️ | The linked report (A25DC0225, May 27, 2025) covers **FY 2024**. The FY 2025 report is **ED-OIG/A26DC0288, August 4, 2026** (same finding: nonrandom student-level sampling → unreliable CIs; repeat finding since FY 2019). | Either cite A25DC0225 as "FY 2024 compliance" or cite A26DC0288 (2026) for FY 2025. Same fix needed in the manuscript (see A.9). |
| 25 | *Humana Inc. v. Becerra*, 801 F. Supp. 3d 624 (N.D. Tex. 2025); *Humana v. Kennedy*, No. 25-11293 (5th Cir.) | ❓/✅ | Decision (Sept 25, 2025, Chief Judge O'Connor, N.D. Tex., No. 4:23-cv-00909-O) and procedural APA vacatur confirmed. Fifth Circuit No. 25-11293 and caption *Humana v. Kennedy* confirmed; oral argument Oct 5, 2026 confirmed. **The reporter citation "801 F. Supp. 3d 624" could not be found anywhere** — the appellate briefs cite only the record (ROA.26912-27); no WL or F. Supp. 3d cite surfaced. Treat as unverified/possibly fabricated. The "government opening brief" URL (2026.03.21) was not fetched. | Cite as *Humana Inc. v. Becerra*, No. 4:23-cv-00909-O (N.D. Tex. Sept. 25, 2025), appeal docketed, *Humana Inc. v. Kennedy*, No. 25-11293 (5th Cir.). Remove the reporter cite unless confirmed on Westlaw/Lexis. |
| 26 | Milliman (2025); STAT (Oct 5, 2026) | ⚠️/✅ | STAT confirmed (panel "skeptical"). Milliman page blocked (permission gate); secondary sources (Crowell, Epstein Becker) confirm the same facts. | Fine; consider replacing Milliman with a law-firm alert or the opinion itself. |
| 27 | Marshall T (2025) AHLA | ✅ | Tyler Marshall (BRG), *Health Law Weekly*, AHLA Payers, Plans, and Managed Care PG, Sept 5, 2025. Compares 2012/PY2018/PY2019. | Add "Health Law Weekly, September 5, 2025". |
| 28 | MACPAC, PERM subtopic | ✅ | 90% ±2.5 national (IPERIA); CMS goal 95% ±3 state; sample ranges confirmed. | — |

### A.3 Literature review — Group C: audit sampling

| # | Reference | Verified? | Issues | Correction |
|---|---|---|---|---|
| 29 | Neter & Loebbecke (1975), AICPA | ✅ | *Auditing Research Monograph No. 2*. Finding ("many widely used statistical procedures may not be reliable … especially when the error rate is low") confirmed via NRC 1988 bibliography. | Add "Auditing Research Monograph No. 2. New York: AICPA." |
| 30 | NRC Panel on Nonstandard Mixtures (1988) | ✅ | *Statistical Models and Analysis in Auditing: A Study of Statistical Models and Methods for Analyzing Nonstandard Mixtures of Distributions in Auditing*, National Academy Press, 91 pp., ISBN 0-309-07817-2. | Add full subtitle/ISBN. Optionally also cite the journal version (Panel, *Statistical Science* 4(1), 1989, pp. 2–33 — not fetched; verify). |
| 31 | Biddle, Bruton & Siegel (1990) | ✅ | *Auditing: A Journal of Practice & Theory* 9(3):92–114. | — |
| 32 | Kvanli, Shen & Deng (1998) | ✅ | *JBES* 16(3):362–368 (July). Parametric mixture likelihood-ratio interval; normal intervals unreliable with many zeros. | — |
| 33 | Kvanli & Schauer, "The Bootstrap: What the Government Auditor Should Know" | ⚠️ | Hosted on MTC site; **undated, no venue**; authors Kvanli (UNT) and Schauer (WA Dept. of Revenue). Numbers: traditional 0.3–2.3% ✅; BCa 3.2–4.5% ✅; increase 5.5–530.6% (text says 6–530%) ✅-ish; gain flattens after ~30 **expected** errors ✅; 12 real samples, 3.4–547.7% ✅; 2/5/10% populations, exponential errors ($800 mean), 5,000 samples/cell, 1,000 BCa resamples ✅. Nominal: 90% two-sided = 95% one-sided lower ✅. | Cite as "Kvanli AH, Schauer R (n.d.). Unpublished manuscript, hosted by the Multistate Tax Commission." Change "6–530%" to "5.5–531%". |
| 34 | Helmers (2000) *Biometrika* 87(3):689–694 | ✅ | Upper bound for total error; empirical Cornish–Fisher + bootstrap calibration; author warns it fails with 0–1 errors in small n. | — |
| 35 | Edwards, Ward-Besser, Lasecki et al. (2003) HSORM 4(4):241–263 | ✅ | Full author list: Edwards D, Ward-Besser G, Lasecki J, Parker B, Wieduwilt K, Wu F, Moorhead P. | Add full authors. |
| 36 | Gilliland & Feng (2010) HSORM 10(3):154–164 | ✅ | — | — |
| 37 | Edwards, Gilliland, Ward-Besser, Lasecki (2015) JSSAM 3(4):504–523 | ✅ | DOI 10.1093/jssam/smv025. | Add DOI. |
| 38 | King & Madansky (2013) JSSAM 1(2):144–170 | ✅ (via Edwards et al. 2023 reference list) | Quote "it is quite possible to destroy the achieved confidence level by stratifying carelessly" is from K&M, as cited by Edwards. Direct access blocked (crossref). | — |
| 39 | Edwards, Liu & Delage (2023) *Survey Methodology* 49(2):607–626 | ✅ | Issue dated Dec 2023, released Jan 3, 2024. Several characterizations need fixing — see §B.1. | — |
| 40 | Liu P (2025) ISI WSC | ✅ | CPS abstract, 65th ISI WSC 2025; "preliminary" results; EL at n=30–90 more often maintains 90%. The abstract does **not** say "above 40%" error. | Drop the "40%" threshold or source it. |

### A.4 Literature review — Group D: bootstrap theory

| # | Reference | Verified? | Notes |
|---|---|---|---|
| 41 | Efron (1979) *Ann Stat* 7(1):1–26 | ✅ | — |
| 42 | Efron (1987) *JASA* 82(397):171–185 | ✅ | — |
| 43 | Hall (1988) *Ann Stat* 16(3):927–953 | ✅ (standard record; Euclid blocked) | — |
| 44 | Efron & Tibshirani (1993) Chapman & Hall | ✅ | "ch. 6" for the parametric bootstrap is §6.5 of that chapter — fine. |
| 45 | DiCiccio & Efron (1996) *Stat Sci* 11(3):189–228 | ✅ | Pages 189–212 article + discussion to 228. |
| 46 | Davison & Hinkley (1997) CUP | ✅ | — |
| 47 | Hesterberg (2015) *Am Stat* 69(4):371–386 | ✅ | Full title includes subtitle "Resampling in the Undergraduate Statistics Curriculum"; DOI 10.1080/00031305.2015.1089789. Abstract confirms percentile intervals less accurate than t in small samples. Add subtitle. |
| 48 | Giacomini, Politis & White (2013) *Econometric Theory* 29(3):567–589 | ✅ | Citation confirmed. The specific claims (one resample per outer replication; does not cover BCa) are consistent with the method but were not verifiable from the abstract pages available. |

### A.5 Literature review — Group E: survey bootstrap

| # | Reference | Verified? | Notes |
|---|---|---|---|
| 49 | McCarthy & Snowden (1985) *Vital and Health Statistics* Ser. 2 No. 95 | ✅ | DHHS Pub. 85-1369. |
| 50 | Rao & Wu (1988) *JASA* 83(401):231–241 | ✅ | — |
| 51 | Kovar, Rao & Wu (1988) *CJS* 16(Suppl):25–45 | ✅ | — |
| 52 | Rao, Wu & Yue (1992) *Survey Methodology* 18(2):209–217 | ✅ | — |
| 53 | Sitter (1992) *JASA* 87(419):755–765 | ✅ | This is the mirror-match paper. Consider also Sitter (1992) *CJS* 20:135–154 (comparison of three bootstraps). |
| 54 | Booth, Butler & Hall (1994) *JASA* 89(428):1282–1289 | ✅ | DOI 10.2307/2290991. |
| 55 | Shao & Tu (1995) Springer | ✅ | — |
| 56 | Wolter (2007) 2nd ed. Springer | ✅ | — |
| 57 | Kolenikov (2010) *Stata Journal* 10(2):165–199; 2008 SNASUG slides | ✅ | Slides attribute the coverage ranking to Krewski & Rao (1981), Rao & Wu (1988), Kovar, Rao & Wu (1988) and Shao (1996) collectively — not to KRW 1988 alone. Adjust attribution. |
| 58 | Antal & Tillé (2011) *JASA* 106(494):534–543 | ✅ | — |
| 59 | Mashreghi, Haziza & Léger (2016) *Statistics Surveys* 10:1–52 | ✅ | DOI 10.1214/16-SS113. The attributed claim (naive iid bootstrap ignores FPC and overstates variance) is standard but could not be checked against the text (Euclid blocked). |

### A.6 Literature review — Group F

| # | Reference | Verified? | Notes |
|---|---|---|---|
| 60 | Cochran (1977) 3rd ed. Wiley | ✅ | Edwards et al. cite pp. 39–44 for the skew principle; consider adding page range. |
| 61 | Chen, Chen & Rao (2003) *CJS* 31(1):53–68 | ✅ | — |
| 62 | Zhou & Tu (2000) *Biometrics* 56:1118–1125 | ✅ | Issue 4 not confirmed but consistent (Dec 2000). |
| 63 | Tian (2005) *Stat Med* 24(20):3223–3232 | ✅ | DOI 10.1002/sim.2169. |
| 64 | Barber & Thompson (2000) *Stat Med* 19(23):3219–3236 | ✅ | Start page confirmed; DOI 10.1002/1097-0258(20001215)19:23<3219::AID-SIM623>3.0.CO;2-P. |
| 65 | Li & Ding (2017) *JASA* 112(520):1759–1769 | ✅ | — |
| 66 | Cistola (2026) companion | n/a | Self-reference. |

### A.7 Literature review — in-text facts not tied to a reference entry

| Claim (location) | Status |
|---|---|
| PARG: 11 contracts, "$115 million a year" (§3) | ⚠️ Bio says ~$114 million. Change to "about $114 million". |
| Part C contractor "up to ~7,000 medical records a year" (§5 table) | ❓ No source given; not in any CMS document fetched. Source or delete. |
| ESRD and hospice enrollees added to Part C sample FY 2024 (§5) | ❓ Not in FY 2025 findings document. Source or delete. |
| Part D sample size "Not stated publicly" (§5 table) | ⚠️ CMS Part D IPM Program Background page states findings are "applied to a randomly selected 5% sample of the Part D beneficiary population" for extrapolation. Note this (it is the simulation/extrapolation sample, not the audit sample). |
| PERM "selected systematically after sorting by paid amount" (§5) | ❓ Supporting statement unreachable; RY 2022 slides confirm five payment strata but not systematic selection. |
| "HHS was not fully PIIA-compliant for FY 2025" (§3) | ✅ Confirmed by OAS-26-17-042. |
| EIPM "Rates have stayed under 1%" (§5) | ❌ FY 2024 was 1.01%. Change to "near or below 1%". |
| CMS 2022 press release "FFE improper payment rate less than 1%" | ❓ Not fetched; consistent with FY 2022 0.62%. |
| HHS FY 2022 Performance Plan (Part D simulation) | ✅ Page confirms a beneficiary sample is run "through a simulation"; no interval detail. |
| RY 2027 PERM eligibility only | ✅ |
| Fifth Circuit argument Oct 5, 2026, panel skeptical | ✅ |

### A.8 Manuscript — reference list

| Reference as written | Verified? | Issues / correction |
|---|---|---|
| Biddle, Bruton & Siegel (1990) | ✅ | **Orphan** — never cited in text. Cite (e.g., §1.2) or remove. |
| CMS (2023) FY 2023 Part D Findings | ✅ | See §B.2 on what it supports. |
| CMS (2025a) FY 2025 Improper Payments Fact Sheet | ⚠️ | Fact sheet is dated **January 15, 2026** → should be CMS (2026). It reports no CIs. |
| CMS (2025b) 2025 Supplemental Improper Payment Data | ⚠️ | Cited for the ±3-point CERT target (§1.1); that target is stated in the CERT *Introduction* document, not confirmed in the supplemental report body (Appendix N not readable). Cite the Introduction document or Appendix N explicitly. |
| CMS (2025c) FY 2025 Part D Findings | ✅ | — |
| CMS (2025d) FY 2025 Part C Findings | ✅ | **Orphan** in main text (used implicitly in Appendix B). Add in-text cite at §3.2 calibration list. |
| CMS (2026a) EIPM Program Background and Findings | ✅ | Orphan in main text; cite at §3.2. |
| CMS (2026b) CERT Methodology | ✅ | Orphan; cite at §3.2/Appendix B.5. |
| CMS (2024) PERM Supporting Statement B | ❓ | Unreachable (see A.1 #12). Orphan in main text. |
| Cistola (2026) companion review | n/a | — |
| Cochran (1977) | ✅ | — |
| Davison & Hinkley (1997) | ✅ | **Orphan.** |
| Department of Education OIG (2025) "…for Fiscal Year 2025" | ❌ | **Wrong year/report.** The 2025 report (A25DC0225, May 27, 2025) covers FY 2024. The FY 2025 report is A26DC0288, Aug 4, 2026. Fix either the FY or the year/number. |
| Edwards, Liu & Delage (2023) | ✅ | — |
| Efron (1987); Efron & Tibshirani (1993); Hall (1988); Hesterberg (2015) | ✅ | — |
| King & Madansky (2013) | ✅ | **Orphan.** |
| Johns & Rosenbaum (2024) IRS | ✅ | Add: Research, Applied Analytics & Statistics, Dec 23, 2024; method is Detection Controlled Estimation (model-based). Characterization "model-based extrapolation of random audits" is fair. |
| Kvanli, Shen & Deng (1998) | ✅ | — |
| Mashreghi et al. (2016) | ✅ | — |
| McConville, Moisen & Frescino (2020) *Forests* 11(2):244 | ✅ | DOI 10.3390/f11020244. Paper documents negative bias of the standard variance estimator growing with model size — supports the §4.5 claim reasonably. |
| Neter & Loebbecke (1975) | ✅ | Add "Auditing Research Monograph No. 2". |
| OMB (2021) M-21-19 | ✅ | Does **not** require 95% (see §B.5). |
| PIIA, Pub. L. 116-117 | ✅ | — |
| Rao & Wu (1988) | ✅ | **Orphan.** |
| Särndal, Swensson & Wretman (1992) | ✅ | — |
| Wolter (2007) | ✅ | **Orphan.** |
| *In-text but no entry:* P.L. 119-21 (§6) | ⚠️ | Add a reference entry. |

### A.9 FY 2025 figures quoted (both documents) vs CMS fact sheet / PaymentAccuracy.gov

| Program | Quoted | Source value | OK? |
|---|---|---|---|
| Medicare FFS | 6.55%, $28.83B, CI 5.9–7.2% | 6.55%, $28.83B; CI 5.9–7.2% (Supplemental Table A1) | ✅ |
| Part C | 6.09%, $23.67B (gross), $19.20B net, $388.72B denom | identical | ✅ |
| Part D | 4.00% (3.57–4.46%), $4.23B ($3.77–4.71B) | identical | ✅ |
| Medicaid | 6.12%, $37.39B | identical | ✅ |
| CHIP | 7.05%, $1.37B | identical | ✅ |
| APTC (FFE) | 0.89%, $657.46M, ±0.54, 0.43 pts technically improper | identical (0.43 from CMS EIPM findings page) | ✅ (fix source) |
| "> $90 billion" total | sum ≈ $96.2B | ✅ |
| Data years | Part C/D CY 2023; APTC BY 2023; CERT Jul 2023–Jun 2024; PERM 3 cycles | ✅ |
| "HHS AFR, reported November 2025; CMS fact sheet" | Fact sheet dated Jan 15, 2026 | ⚠️ date |

---

## (B) Mischaracterizations and inaccurate claims in text

**B.1 Edwards, Liu & Delage (2023) — three over-readings (lit review §6).**
- Quote: *"no stratification algorithm tested was viable for more than about half of 104 populations."* The paper says *"in no case did any algorithm (except Geo) achieve viability for more than about half of the test populations"*; the geometric algorithm reached 91/104 (88%) in one design cell. → Revise: "no stratification algorithm except the geometric (Geo) algorithm was viable for more than about half of the 104 populations."
- Table row *"Edwards et al. 2023 (R `samptest`)"* implies an R package. `samptest` is the authors' Monte Carlo testing *function*, available on request; the stratification algorithms come from the CRAN package `stratification`. → Revise wording.
- Quote: *"Payment-based strata create left-skewed overpayment strata at high error rates, and King and Madansky (2013) warn…"* — the paper presents this as a risk of careless design, not an automatic consequence of payment stratification. → "can create".
- Manuscript §3.1: *"This study is a Monte Carlo validation study that follows the design of Edwards et al. (2023)."* Edwards et al. test designs on 104 real populations under an all-or-nothing model with thousands of Monte Carlo draws; the manuscript uses five synthetic populations and 25 replications. "Follows the design" overstates the resemblance. → "adopts the Monte Carlo design-testing logic of Edwards et al. (2023), applied to synthetic populations."

**B.2 Part D interval "already simulation based" (manuscript §1.2: *"The published Part D interval is already simulation based (CMS 2023, 2025c)"*; lit review annotation: *"evidence that Part D already uses simulation-based intervals"*).** The FY 2023 document says CMS reduced "the number of simulation iterations to align to statistical literature" and aligned "the confident interval calculation to the estimation method." The FY 2025 document says nothing about simulation. Neither states that the CI is read from simulation iterations. The lit review itself (§5) correctly says *"Public documents do not name the algorithm."* The manuscript is inconsistent with its companion. → Revise to: "CMS describes the Part D estimate as simulation-based and has altered the number of simulation iterations and the interval method; the interval algorithm itself is not public (CMS 2023, 2025c)."

**B.3 Part D intervals "visibly asymmetric" (lit review §5).** FY 2025: $3.77–4.71B around $4.23B is −0.46/+0.48 (rate 3.57–4.46 around 4.00: −0.43/+0.46) — essentially symmetric. FY 2023: −0.72/+0.82, mildly asymmetric. The inference "consistent with a percentile-type resampling interval on a right-skewed error distribution" rests on very weak evidence. → Soften to "slightly asymmetric in FY 2023 and nearly symmetric in FY 2025, so the published intervals do not by themselves reveal the algorithm."

**B.4 "One-sided, z = 1.645" labelled a 90% bound (lit review §5 table rows for PY 2019 and PY 2021; §4 "PY 2019–2021 RADV use a 90% interval's lower limit").** z = 1.645 is the lower limit of a two-sided 90% interval, which is a one-sided 95% bound — the very confusion the lit review warns about in §4. The PY 2021 document says "lower bound of the 90 percent confidence interval" with t(n−1) and does not specify sidedness. → Describe as "lower limit of a two-sided 90% interval (one-sided 95% bound), z = 1.645 (PY 2019) / t(n−1) (PY 2021)."

**B.5 "the law requires that each estimate include a 95% confidence interval" (manuscript Abstract) and "attach a 95% confidence interval" (§1.1 step 3).** Neither PIIA nor M-21-19 requires 95%; M-21-19 says agencies must "work with their statistician to determine the appropriate confidence interval." PERM's own statutory precision target (IPERIA, per MACPAC) was 90% ±2.5. The lit review (§3) states this correctly; the manuscript contradicts it. → "requires a statistically valid estimate with a confidence interval; CMS programs report 95% intervals."

**B.6 EIPM "Rates have stayed under 1%" (lit review §5).** FY 2024 was 1.01%. → Correct.

**B.7 ED OIG precedent labelled "FY 2025 review" (lit review §3, §B) and "for Fiscal Year 2025" with year 2025 (manuscript).** The linked/dated report covers FY 2024. The FY 2025 report exists (A26DC0288, Aug 4, 2026) with the same finding. → Fix year/report number in both documents.

**B.8 "~550 eligible contracts a year ([CMS RADV fact sheet])" (lit review §5).** Not in the fact sheet. → Cite the May 21, 2025 CMS press release.

**B.9 Kvanli & Schauer attribution details (lit review §6).** "6–530%" → "5.5–531%"; "gain fades after roughly 30 nonzero errors in the sample" → the paper's variable is *expected* number of errors (EE ≈ 30), which also matters because the authors conclude the minimum-nonzero rule (NZ) is not what drives the gain. Also note that the study is undated and unpublished.

**B.10 Kolenikov attribution (lit review §6).** The coverage ranking bootstrap > BRR > jackknife > linearization is presented in the 2008 slides as a synthesis of Krewski & Rao (1981), Rao & Wu (1988), Kovar, Rao & Wu (1988) and Shao (1996), not as "Kovar, Rao & Wu 1988" alone. → Attribute to the set, or cite KRW 1988 directly after reading it.

**B.11 Empirical likelihood "untested at error rates above 40%" (lit review §4 table, §6 table).** Liu (2025) says EL "had not been tested at high error rates"; no 40% figure. → Remove or source.

**B.12 "M-21-19 … the approval route for changing an interval method" (lit review §B annotation).** OMB does not formally approve S&EMPs. → "submission/review route".

**B.13 PaymentAccuracy.gov cited for "0.43 of the 0.89 points" (lit review §5).** The figure is on CMS's EIPM Improper Payment Findings page, not PaymentAccuracy.gov.

**B.14 Manuscript §1.3 / §4.2: "Section 4.1 shows that this omission is large and predictable."** §4.1 is about point accuracy; the omission is shown in §4.2. Cross-reference error.

**B.15 Terminology: "audit-finding bootstrap simulation."** The fixed-rate method does not resample anything observed; it is a plug-in microsimulation (a stochastic reconstruction of the population under point-estimated rates). Survey Methodology/JOS referees will object to calling it a "bootstrap." The parametric-rate version is a parametric bootstrap of the rates (correctly described in §3.6). Recommend renaming the fixed-rate method ("plug-in audit-finding simulation") and reserving "bootstrap" for the parametric version; also connect it explicitly to the single- vs. multiple-imputation distinction (Rubin 1987), which is the exact analogue of the omitted between-audit variance term.

---

## (C) Consistency and framing assessment

**C.1 Does the lit review identify a gap the manuscript addresses?** Partly. The review's stated gap (§6, §9) is that no published study compares analytic, design-bootstrap, and audit-finding simulation intervals against known truth in the five CMS designs, and that "the validity of audit-finding simulation intervals (with or without uncertainty in the rates) has not been tested." The manuscript addresses the last clause (fixed vs. parametric rates) and the analytic comparators. It does **not** test anything the review spends most of §6–§8 on: Rao–Wu/rescaled or pseudo-population survey bootstraps, BCa, bootstrap-*t*, empirical likelihood, hypergeometric/minimum-sum bounds, one-sided recovery bounds, RADV, state-level PERM eligibility thresholds. The review's §8 research agenda specifies 10,000 replications per cell, an error-rate grid from 0.01 to 0.95, Monte Carlo SE reporting, and a pre-registered "viable" criterion; the manuscript uses 25 replications at a single error rate per program with an MC SE of ~4.4 points. The sentence in the review (§8) *"This is the approach of the companion Monte Carlo evaluation, which applies this agenda to all five programs"* and the Group G annotation *"implements the research agenda in Section 8"* **over-claim**. Revise to "implements the first stage of this agenda (analytic estimators versus audit-finding simulation at production error rates)."

**C.2 Internal contradictions between the two documents.**
- 95% CI "required by law" (manuscript) vs. 90% ±2.5 statutory PERM target (review).
- Part D interval "already simulation based" (manuscript) vs. "public documents do not name the algorithm" (review).
- Review §7 rates Part C IPM as "Low" bootstrap priority ("the CLT should hold, and coverage gains will likely be small") and CERT "Low–medium"; the manuscript then recommends CMS adopt parametric-rate simulation for *all* PIIA rates, including Part C and CERT, and finds the analytic intervals already cover adequately there (24–25/25). The manuscript's recommendation rests on width, not on a coverage failure of the incumbent method — the review's framing (coverage failure) and the manuscript's finding (incumbent coverage is fine for gross rates at ~6%) should be reconciled explicitly.
- Review stresses "number of nonzero errors" as the controlling factor and predicts normal-theory failure in the rare-error regime; the manuscript's sparse-component results (Part C under, Part D under, EIPM technically improper, CERT under; misses "mainly below") confirm this and match Cochran's skew principle (right skew → liberal upper limit). The manuscript should say so and cite the review's framing; currently §4.4 cites only Kvanli et al. 1998 and Hesterberg 2015.

**C.3 Novelty and importance.**
- The structural finding (plug-in simulation omits the between-audit variance term; its width shrinks with N/n) is correct and important for practice, but it follows directly from the law of total variance and is the same phenomenon as single imputation understating variance (Rubin 1987) and as the "plug-in" problem in parametric bootstrap theory. The manuscript should present it as a *demonstration in the CMS setting* rather than a discovery, and cite Rubin (1987) and Rubin (1981) (it already says "not a Bayesian bootstrap" without citing the Bayesian bootstrap).
- The manuscript does not establish that any CMS program actually uses a fixed-rate simulation. The policy value therefore depends on Part D's undocumented algorithm; the claim should be framed as "if any program's simulation holds audited rates fixed, its interval is invalid; the Part D S&EMP should be checked."
- The "20–38% smaller audits" conclusion is a 1/√n extrapolation from 25 replications in which 96.8% vs ~89–92% coverage are not statistically distinguishable per program, and in which sparse components under-cover under every method. The abstract's "valid and narrower" and "would permit audits roughly 20–38% smaller" should be hedged more than "pending confirmation." A JOS/Survey Methodology referee will require ≥1,000 replications (MC SE ≈ 0.7 points at 95%) before accepting a coverage-plus-width ranking; the review's own §8 says 10,000.
- The width gain is attributed (§4.3) partly to the simulation being "a model-assisted estimator that uses the auxiliary information of the full population." This is a model-*based* (not model-assisted) argument: the intervals are valid only if the error process is independent of payment size within strata — exactly the assumption the manuscript concedes (§5.4 item 2) it imposed when building the populations. The lit review does not flag this; it should, and the manuscript should test a misspecified population (error probability increasing with payment) before recommending adoption.
- Is the gap real? Yes: PIIA interval methods for Part C/Part D/EIPM are not publicly documented; PERM state eligibility estimates acquire dollar consequences from FY 2030; SBE measurement begins 2027 with small samples. The review documents this convincingly. The manuscript, however, addresses the *least* consequential part of that gap (two-sided national PIIA rates at moderate error rates with large n), while the review's own prioritization puts RADV and PERM state eligibility first.

**C.4 Methods–framing alignment issues a referee will raise.**
- Review §4 lists Satterthwaite/t df and linearization for ratio variance; manuscript uses z = 1.96 for expansion/ratio, t for regression. Justify or harmonize.
- Review §6 says survey bootstraps need ≥2 units per stratum and discusses FPC; manuscript's PERM design has 10 strata × 52 units per state and CERT samples IPPS at 22% — the FPC matters and the manuscript's reassignment-variance argument (§4.2) depends on it. Fine, but state the FPC treatment in §3.5–3.6.
- The manuscript's Part D analytic comparators are on a different audit (990 beneficiaries vs. 5,000 PDEs); the 63% narrower / 13%-of-audit claim is acknowledged as weak but still appears in the abstract and conclusion. Remove from abstract.

---

## (D) Missing citations a referee would expect (all verified unless noted)

**D.1 Audit-sampling foundations (add to lit review §4 "MUS / Stringer-type bounds" row and §6; manuscript §1.2)**
- Stringer KW (1963). Practical aspects of statistical sampling in auditing. *Proceedings of the Business and Economic Statistics Section, American Statistical Association*, 405–411. — origin of the Stringer bound/MUS (the review names "Stringer-type bounds" with no citation).
- Kaplan RS (1973). Statistical sampling in auditing with auxiliary information estimators. *Journal of Accounting Research* 11(2):238–258. — first to recognize the mixture-population problem for difference/ratio/regression estimators (NRC 1988 credits Kaplan 1973a,b).
- Fienberg SE, Neter J, Leitch RA (1977). Estimating the total overstatement error in accounting populations. *Journal of the American Statistical Association* 72(358):295–302. — multinomial bound.
- Leslie DA, Teitlebaum AD, Anderson RJ (1979). *Dollar-Unit Sampling: A Practical Guide for Auditors.* Toronto: Copp Clark Pitman. (Some lists give 1980.)
- Cox DR, Snell EJ (1979). On sampling and the estimation of rare errors. *Biometrika* 66(1):125–132. DOI 10.1093/biomet/66.1.125. — the canonical rare-error model; directly relevant to EIPM/sparse components.
- Bickel PJ (1992). Inference and auditing: the Stringer bound. *International Statistical Review* 60(2):197–209. DOI 10.2307/1403650.
- Pap G, van Zuijlen MCA (1996). On the asymptotic behaviour of the Stringer bound. *Statistica Neerlandica* 50(3):367–389.
- Rohrbach KJ (1993). Variance augmentation to achieve nominal coverage probability in sampling from audit populations. *Auditing: A Journal of Practice & Theory* 12(2):79–97 (start page 79 confirmed; end page to verify). — directly on the manuscript's coverage problem.
- Howard RC (1994). A combined bound for errors in auditing based on Hoeffding's inequality and the bootstrap. *Journal of Business & Economic Statistics* 12(2):437–448. — bootstrap bound for audit populations; belongs next to Biddle et al. (1990) and Helmers (2000).
- Berger YG, Chiodini PM, Zenga M (2021). Bounds for monetary-unit sampling in auditing: an adjusted empirical likelihood approach. *Statistical Papers* 62(6):2739–2761. DOI 10.1007/s00362-020-01209-w. — modern EL for MUS; the review's EL row cites only Chen–Chen–Rao and Liu.
- Frost PA, Tamura H (1986). Accuracy of auxiliary information interval estimation in statistical auditing. *Journal of Accounting Research* 24(1):57–75. — **existence confirmed via NRC 1988 citations ("Frost and Tamura 1986, 1987"); volume/pages not independently confirmed in this session — verify before use.**
- Horgan JM (2006). Stratification of skewed populations: a review. *International Statistical Review* 74(1):67–76; Gunning P, Horgan JM (2004). A new algorithm for the construction of stratum boundaries in skewed populations. *Survey Methodology* 30(2):159–166. — the geometric stratification that Edwards et al. found most often viable.

**D.2 Medicare integrity-audit statistics (add to lit review Group C; manuscript §1.2/§6)**
- Edwards D (2011). On stratified sampling and ratio estimation in Medicare and Medicaid benefit integrity investigations. *Health Services and Outcomes Research Methodology* 11:79–94. DOI 10.1007/s10742-011-0073-7. — the only published treatment of ratio vs. expansion estimation in Medicare audits; the manuscript compares exactly these.
- Gilliland D, Edwards D (2011). Using randomized confidence limits to balance risk: an application to Medicare investigations. *The American Statistician* 65(3):149–153.
- Ignatova I, Edwards D (2008). Probe samples and the minimum sum method for Medicare fraud investigations. *HSORM* 8:209–221.
- Norris M (2018). Sample design for audit populations. arXiv:1802.03778 (preprint). — hypergeometric generative model, expansion-vs-ratio criterion, optimal strata for Medicaid audits.
- HHS OIG (2024). *Medicare Advantage Compliance Audit of Specific Diagnosis Codes That MediGold (Contract H3668) Submitted to CMS*, A-07-20-01198, February 2024. — example of OIG practice: stratified 210 enrollee-years, "lower limit of a two-sided 90-percent confidence interval"; illustrates the recovery setting the review discusses.
- HHS OIG, RAT-STATS statistical software (2019 release; 2010 User Guide), https://www.oig.hhs.gov/compliance/rat-stats/ — the de facto standard implementation of the normal-theory bounds the review critiques.
- CMS (2025). Press release, "CMS Rolls Out Aggressive Strategy to Enhance and Accelerate Medicare Advantage Audits," May 21, 2025 — source for ~550 contracts and 35→200 enrollees.

**D.3 Survey bootstrap and finite-population resampling (lit review Group E; manuscript §1.3)**
- Bickel PJ, Freedman DA (1984). Asymptotic normality and the bootstrap in stratified sampling. *Annals of Statistics* 12(2):470–482. — first bootstrap under stratified sampling; missing from a list that includes Booth–Butler–Hall.
- Krewski D, Rao JNK (1981). Inference from stratified samples: properties of the linearization, jackknife and balanced repeated replication methods. *Annals of Statistics* 9(5):1010–1019.
- Chao M-T, Lo S-H (1985). A bootstrap method for finite populations. *Sankhyā A* 47:399–405; Gross ST (1980). Median estimation in sample surveys. *Proceedings of the Section on Survey Research Methods, ASA*, 181–184. — the without-replacement/pseudo-population lineage the review's §4 table names.
- Sitter RR (1992). Comparing three bootstrap methods for survey data. *Canadian Journal of Statistics* 20(2):135–154.
- Beaumont J-F, Patak Z (2012). On the generalized bootstrap for sample surveys with special attention to Poisson sampling. *International Statistical Review* 80(1):127–148. DOI 10.1111/j.1751-5823.2011.00166.x.
- Preston J (2009). Rescaled bootstrap for stratified multistage sampling. *Survey Methodology* 35(2):227–234. — relevant to PERM's two-phase/multistage structure.
- Chen S, Haziza D, Mashreghi Z (2022). A comparison of existing bootstrap algorithms for multi-stage sampling designs. *Stats* 5(2):521–537.
- Lohr SL (2022). *Sampling: Design and Analysis*, 3rd ed. Boca Raton: Chapman & Hall/CRC (ISBN 9780367279509); Valliant R, Dever JA, Kreuter F (2018). *Practical Tools for Designing and Weighting Survey Samples*, 2nd ed. Cham: Springer (DOI 10.1007/978-3-319-93632-1); Valliant R, Dorfman AH, Royall RM (2000). *Finite Population Sampling and Inference: A Prediction Approach*. Wiley. — the last is the natural citation for the model-based character of the simulation's width gain (§C.3).

**D.4 Parametric bootstrap / imputation analogy (manuscript §1.3, §3.6, §4.2)**
- Rubin DB (1987). *Multiple Imputation for Nonresponse in Surveys*. New York: Wiley. — the between-imputation variance component is the exact analogue of the manuscript's missing "Var(E[T̂|A])" term; single imputation = fixed-rate simulation.
- Rubin DB (1981). The Bayesian bootstrap. *Annals of Statistics* 9(1):130–134. — the manuscript says the method "is not a Bayesian bootstrap" without citing it.
- Rao JNK (2011). Impact of frequentist and Bayesian methods on survey sampling practice: a selective appraisal. *Statistical Science* 26(2):240–256. DOI 10.1214/10-STS346. — optional, situates design-based vs model-based inference.

**D.5 Simulation-study methodology and Monte Carlo error (manuscript §3.1, §3.7, §5.4; lit review §8)**
- Morris TP, White IR, Crowther MJ (2019). Using simulation studies to evaluate statistical methods. *Statistics in Medicine* 38(11):2074–2102. — ADEMP framework; reporting MC SE for coverage; the manuscript's 25-replication design and "4.4 points" MC SE should be framed with this.
- Koehler E, Brown E, Haneuse SJ-PA (2009). On the assessment of Monte Carlo error in simulation-based statistical analyses. *The American Statistician* 63(2):155–162. DOI 10.1198/tast.2009.0030.
- White IR (2010). simsum: Analyses of simulation studies including Monte Carlo error. *Stata Journal* 10(3):369–385. (Details from the IDEAS record; article not opened.)

**D.6 Government documents to add**
- ED OIG (2026). *U.S. Department of Education's Compliance with Payment Integrity Information Reporting Requirements for Fiscal Year 2025*, ED-OIG/A26DC0288, August 4, 2026. — the correct FY 2025 precedent.
- GAO (2026). *Payment Integrity: Agencies' Estimated Improper Payments Increased to $186 Billion in Fiscal Year 2025*, GAO-26-108694, April 27, 2026. — correct title for the existing entry.
- CMS, Medicare Part D IPM Program Background page (random 5% beneficiary sample; validation findings applied and extrapolated) — fills the review's "not stated publicly" gap partially.

**Items requested but not found/verified:** a specific "Medicare FFS Rubin-style finite population inference" paper — I found nothing matching that description beyond Li & Ding (2017), already cited; Hidiroglou (2001) two-phase variance and Kott & Stukel (1997) two-phase jackknife exist in Statistics Canada's catalogue (12-001-X19970023621) but I did not confirm volume/pages, so I have not listed them as ready-to-use.

---

## URLs that could not be read in this session (for the author to check manually)
- https://omb.report/icr/202408-0938-026/doc/145713901.pdf and .../202408-0938-025/doc/145714301.pdf (PERM supporting statements) — client error / proxy 403
- https://projecteuclid.org/euclid.ssu/1458047831 ; https://www.projecteuclid.org/euclid.aos/1176350933 ; https://www.projecteuclid.org/euclid.ss/1177012665 — bot wall
- https://www.milliman.com/en/insight/federal-court-vacates-2023-rule-cms-radv-audits — permission gate
- https://cran.r-project.org/web/packages/svrep/vignettes/bootstrap-replicates.html ; https://www.mdpi.com/2571-905X/5/2/31 ; https://api.crossref.org/… ; https://www.nap.edu/read/1363/chapter/1 — permission gate
- https://www.arxiv.org/abs/1411.5279 — rate-limited
- https://pmc.ncbi.nlm.nih.gov/articles/PMC535558 — CAPTCHA

No files in the repository were modified.