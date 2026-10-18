# Manuscripts

The study written up for submission, plus a one-page summary for sharing.

| File | What it is |
|---|---|
| [`manuscript.md`](manuscript.md) | Full manuscript: background, purpose, methods, results (the fixed-rate interval problem, then the parametric alternative), discussion and recommendation, future research, references, and Appendices A (data process), B (program designs and assumptions) and C (additional results). Also rendered as [`manuscript.pdf`](manuscript.pdf), [`manuscript.docx`](manuscript.docx) and `manuscript.html` |
| [`one-pager.md`](one-pager.md) | One-page summary of the findings and recommendation. Also [`one-pager.pdf`](one-pager.pdf) and `one-pager.html` |
| `sections/` | Manuscript source, one file per part. Edit these, not `manuscript.md` |
| `generated/` | Built from results, never edited by hand: `tables.md` (Tables 2–5 and C1), `results_long.csv` (every program × measure × method), `fig1_width.png`, `fig2_coverage.png` |
| `scripts/` | `build_tables.py` (tables and figures from the results), `assemble.py` (sections + tables → `manuscript.md`), `render.sh` (PDF, Word and HTML) and the print stylesheets |

## Rebuild

From the repository root, after the estimation runs:

```bash
python manuscripts/scripts/build_tables.py   # tables and figures
python manuscripts/scripts/assemble.py       # manuscript.md
manuscripts/scripts/render.sh                # PDF, Word, HTML (needs pandoc and wkhtmltopdf)
```

`build_tables.py` reads the parametric-rate results (`<program>/estimation/results/`, the default and the results reported in the program READMEs) and the fixed-rate results from the same audits (`<program>/estimation/results_fixed/`), run with `--set sim_rates=fixed`:

```bash
ipsim part-c-ipm/estimation/config.yaml --out part-c-ipm/estimation/results_fixed --set sim_rates=fixed
ipsim part-d-ipm/estimation/config.yaml --out part-d-ipm/estimation/results_fixed --set sim_rates=fixed
ipsim perm-cert/estimation/perm.yaml --out perm-cert/estimation/results_fixed/perm --set sim_rates=fixed
ipsim perm-cert/estimation/perm_national.yaml --out perm-cert/estimation/results_fixed/perm --set perm_results_dir=perm-cert/estimation/results_fixed/perm
ipsim eipm/estimation/config.yaml --out eipm/estimation/results_fixed --set sim_rates=fixed
ipsim perm-cert/estimation/cert.yaml --out perm-cert/estimation/results_fixed/cert --set sim_rates=fixed
```

## Before submission

- Complete the affiliation and the funding, conflicts of interest and disclaimer section (marked in brackets).
- Choose a journal and apply its reference style. Methodological fits include the *Journal of Survey Statistics and Methodology*, *Health Services and Outcomes Research Methodology* and *Survey Methodology*.
- Unlinked classic references are cited from standard bibliographic records and should be checked against the originals.
