"""Render the literature review as a standalone paper.

Word: pandoc, with native (editable) equations.
PDF: HTML + wkhtmltopdf with the manuscript's print stylesheet; display
equations ($$ ... $$) are drawn as PNG images with matplotlib mathtext,
because wkhtmltopdf has no math renderer.
Run from the repository root:  python manuscripts/scripts/render_review.py
"""
import re
import subprocess
import tempfile
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
LR = ROOT / "literature-review"
SRC = LR / "improper-payment-estimation-accuracy-literature-review.md"
STEM = SRC.stem
CSS = ROOT / "manuscripts" / "scripts" / "print.css"

subprocess.run(["pandoc", SRC.name, "-o", f"{STEM}.docx", "--resource-path=."], cwd=LR, check=True)

with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    k = 0

    def draw(m):
        global k
        k += 1
        tex = " ".join(m.group(1).split()).replace(r"\!", "")
        fig = plt.figure(figsize=(0.01, 0.01))
        fig.text(0, 0, f"${tex}$", fontsize=13)
        out = tmp / f"eq{k}.png"
        fig.savefig(out, dpi=200, bbox_inches="tight", pad_inches=0.05, transparent=False, facecolor="white")
        plt.close(fig)
        return f'<p style="text-align:center"><img src="{out}" style="max-width:95%; height:auto; zoom:0.5"></p>'

    md = re.sub(r"\$\$\n(.*?)\n\$\$", draw, SRC.read_text(), flags=re.S)
    (tmp / "review.md").write_text(md)
    html = LR / f"{STEM}.html"
    subprocess.run(["pandoc", str(tmp / "review.md"), "-s", "--embed-resources", f"--resource-path={LR}:{tmp}",
                    "--css", str(CSS), "-o", str(html)], check=True)
    subprocess.run(["wkhtmltopdf", "-q", "--enable-local-file-access", "-s", "Letter", "-T", "18mm", "-B", "18mm",
                    "-L", "16mm", "-R", "16mm", str(html), str(LR / f"{STEM}.pdf")], check=True,
                   stderr=subprocess.DEVNULL)
print(f"rendered {STEM}.docx, .html, .pdf ({k} equations)")
