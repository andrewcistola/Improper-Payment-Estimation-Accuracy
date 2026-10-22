"""Rewrite the results section of each program README from shared/results/report/by_scenario.csv.

Everything from the line "## Results (25 audit years)" to the end of each README is
regenerated; the text above it is left alone. Run from the repository root after
shared/report.yaml:

    python shared/build_readmes.py
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
B = pd.read_csv(ROOT / "shared/results/report/by_scenario.csv")

METHODS = [("expansion", "Expansion"), ("ratio", "Ratio"), ("regression", "Regression"),
           ("pde_expansion", "PDE expansion (same audit)"), ("pde_ratio", "PDE ratio (same audit)"),
           ("simulation", "Simulation (parametric rates)")]
MEASURE = {"over": "Overpayments", "under": "Underpayments", "gross": "Gross", "net": "Net",
           "technical": "Technically improper", "monetary": "Monetary", "eligibility": "Eligibility", "claims": "Claims",
           "ipps": "Gross: Part A IPPS", "part_a_other": "Gross: Part A excl. IPPS", "part_b": "Gross: Part B",
           "dmepos": "Gross: DMEPOS"}
ORDER = ["over", "under", "gross", "net", "eligibility", "claims", "technical", "monetary",
         "ipps", "part_a_other", "part_b", "dmepos"]

# README path, program key in by_scenario, scenario filter, scale text, total payments text
PROGRAMS = [
    ("part-c-ipm/README.md", "part-c-ipm", "base", "× 100", "$388.7B"),
    ("part-d-ipm/README.md", "part-d-ipm", "base", "× 500", "$105.6B"),
    ("eipm/README.md", "eipm", "base", "× 100", "$81.7B"),
    ("perm/README.md", "perm", "national", "× 200, federal share", "$142.0B"),
    ("cert/README.md", "cert", "national", "× 200", "$439.9B"),
]


def mlabel(d):
    key = d.split("|")[1] if d.startswith("national|") or d.split("|")[0].isdigit() else d.split("|")[0]
    return MEASURE.get(key, key)


def mkey(d):
    key = d.split("|")[1] if d.startswith("national|") else d.split("|")[0]
    return ORDER.index(key) if key in ORDER else 99


def section(prog, scenario, scale, X):
    s = B[(B.program == prog) & (B.scenario == scenario)]
    doms = sorted(s.domain.unique(), key=mkey)
    methods = [(m, l) for m, l in METHODS if (s.method == m).any()]
    out = ["## Results (25 audit years)", "",
           f"Each row gives the true value and, over the 25 audit years, the median point estimate and the median "
           f"upper and lower bounds of the 95% interval. National dollars ({scale}); rates are dollars ÷ total payments ({X})."
           + (" The PDE expansion and PDE ratio estimators define over, under, gross and net at the PDE level (no netting within beneficiaries)." if prog == "part-d-ipm" else ""),
           ""]
    for title, usd in [("**Dollars**", True), ("**Rates**", False)]:
        out += [title, "", "| Measure | Method | True | Estimated | Upper bound | Lower bound |", "|---|---|---|---|---|---|"]
        for d in doms:
            first = True
            for m, l in methods:
                r = s[(s.domain == d) & (s.method == m)]
                if r.empty:
                    continue
                r = r.iloc[0]
                if usd:
                    f = lambda v: f"${v / 1e9:.2f}B"
                    vals = (r.true_improper_usd, r.median_estimate_usd, r.median_upper_usd, r.median_lower_usd)
                else:
                    f = lambda v: f"{100 * v:.2f}%"
                    vals = (r.true_rate, r.median_estimate, r.median_upper, r.median_lower)
                out.append(f"| {mlabel(d) if first else ''} | {l} | " + " | ".join(f(v) for v in vals) + " |")
                first = False
        out.append("")
    out += ["**How often the 95% interval contains the truth** (out of 25 audit years; in parentheses, intervals "
            "entirely above / entirely below the truth). A valid interval contains it in about 24 of 25.", "",
            "| Measure | " + " | ".join(l for _, l in methods) + " |", "|---|" + "---|" * len(methods)]
    for d in doms:
        cells = []
        for m, _ in methods:
            r = s[(s.domain == d) & (s.method == m)]
            cells.append("—" if r.empty else f"{int(r.iloc[0].n_truth_inside)}/25 ({int(r.iloc[0].n_ci_above_truth)}/{int(r.iloc[0].n_ci_below_truth)})")
        out.append(f"| {mlabel(d)} | " + " | ".join(cells) + " |")
    out += ["", "From [`shared/results/report/by_scenario.csv`](../shared/results/report/by_scenario.csv) "
            "(`python shared/build_readmes.py` regenerates this section).", ""]
    return "\n".join(out)


for path, prog, scenario, scale, X in PROGRAMS:
    p = ROOT / path
    text = p.read_text()
    head = text.split("## Results (25 audit years)")[0].rstrip() + "\n\n"
    p.write_text(head + section(prog, scenario, scale, X))
    print("rewrote", path)
