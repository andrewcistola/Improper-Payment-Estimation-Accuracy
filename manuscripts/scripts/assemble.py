"""Assemble manuscripts/manuscript.md from the section sources and the generated tables.

Sections live in manuscripts/sections/*.md (front matter, text, appendix); tables
come from manuscripts/generated/tables.md (build_tables.py). A {{TABLEn}} or
{{TABLEC1}} marker in a section is replaced by that table; {{APPENDIXD}} by
manuscripts/generated/appendix_d.md (robustness/summarize.py).
Run from the repository root after build_tables.py:
    python manuscripts/scripts/assemble.py
"""
import re
from pathlib import Path

M = Path(__file__).resolve().parents[1]
tables = {}
for block in (M / "generated" / "tables.md").read_text().split("\n\n**Table ")[0:]:
    block = block if block.startswith("**Table ") else "**Table " + block
    key = re.match(r"\*\*Table (\w+)\.", block).group(1)
    tables[key] = block.strip()
text = "\n\n".join((M / "sections" / f).read_text().strip() for f in
                   ["00_front.md", "01_introduction.md", "02_methods.md", "03_results.md",
                    "04_discussion.md", "05_appendix.md"])
text = re.sub(r"\{\{TABLE(\w+)\}\}", lambda m: tables[m.group(1)], text)
appendix_d = M / "generated" / "appendix_d.md"
text = text.replace("{{APPENDIXD}}", appendix_d.read_text().strip() if appendix_d.exists()
                    else "*(Appendix D tables not built: run `python robustness/run.py`.)*")
assert "{{" not in text
(M / "manuscript.md").write_text(text + "\n")
print(f"manuscript.md: {len(text.split()):,} words")
