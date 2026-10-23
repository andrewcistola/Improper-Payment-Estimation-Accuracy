# qa/Claude/review

Independent review of commit 33c6c470 (2026-10-21) by Claude (Anthropic), engaged by the study author.

- `PEER_REVIEW.md` — the full review: literature and framing, code review, re-run, writing, overall assessment, and the consolidated change list (Part 6).
- `QA_Checklist_2026-10-21_Claude.xlsx` — the completed checklist (sections A–H), run log and issues log (19 issues, I-01 to I-19).
- `review_citations.md`, `review_shared_partc_eipm.md`, `review_partd_perm_cert.md` — working reports with file and line references.
- `scripts/` — standalone verification scripts (read the committed populations and results; modify nothing). Run with the project's `.venv` from the repository root.

No sign-off form is included: an AI reviewer cannot attest. The attestation is left for a human signatory, who can start from this folder.

## Addendum, 2026-10-22: changes made in response to this review

The author directed that all recommended changes be made. Commit `9c903d3` (code and documentation fixes, the `perm/`–`cert/` split, the literature-review corrections) and the commit that follows it (regenerated results, the robustness and calibration runs, and the rewritten manuscript) implement the change list in `PEER_REVIEW.md` Part 6. Items I-02 to I-19 are therefore Resolved in the repository even though the Issues log in this folder records them as Open at the time of review; the checklist workbook is left as it was signed off by the reviewer so that the evidence of what was found is preserved.

Of note for a reader of `PEER_REVIEW.md`: the robustness scenario it called for (R1) reversed the manuscript's recommendation. With error probability depending on payment size within strata, the simulation is biased by 3% to 148% and its interval fails, while the ratio estimator is unaffected; the manuscript now recommends the design-based ratio interval as the primary PIIA interval with the parametric-bootstrap simulation alongside it. The calibration run (R3) confirmed the understatement estimated in C1 (ratios 0.88–0.95 in four programs; CERT 1.13). The Part C kernel fix (R2) raised the simulation's underpayment coverage from 19 to 25 of 25. The new Part D PDE-level comparators (R4) are unbiased but heavy-tailed and undercover.

**Update, 2026-10-23.** At the author's direction the recommendation was reframed once more after a further robustness run (Appendix D, Tables D4–D6): parametric-bootstrap simulation is recommended with the within-kind independence of error and payment size stated as a central assumption and tested every cycle against the design-based ratio estimate; where the test fails, the simulation's donor kinds are post-stratified on payment decile (`sim_kind_deciles`), which removed the bias in PERM and most of it in CERT and Part D; audit-size reductions are deferred until the test has passed and coverage is confirmed at the smaller size.
