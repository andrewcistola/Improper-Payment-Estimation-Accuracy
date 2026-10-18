#!/usr/bin/env bash
# Render the manuscript (HTML, PDF, Word) and the one-pager (HTML, PDF).
# Run from the repository root after build_tables.py and assemble.py.
# Needs pandoc and wkhtmltopdf.
set -euo pipefail
cd "$(dirname "$0")/.."
pandoc manuscript.md -o manuscript.docx --resource-path=.
pandoc manuscript.md -s --embed-resources --resource-path=. --css scripts/print.css -o manuscript.html
wkhtmltopdf -q --enable-local-file-access -s Letter -T 18mm -B 18mm -L 16mm -R 16mm manuscript.html manuscript.pdf
pandoc one-pager.md -s --embed-resources --css scripts/onepager.css -o one-pager.html
wkhtmltopdf -q --enable-local-file-access -s Letter -T 10mm -B 10mm -L 11mm -R 11mm one-pager.html one-pager.pdf
pandoc conference-abstract.md -o conference-abstract.docx
pandoc conference-abstract.md -s --embed-resources --css scripts/print.css -o conference-abstract.html
wkhtmltopdf -q --enable-local-file-access -s Letter -T 18mm -B 18mm -L 18mm -R 18mm conference-abstract.html conference-abstract.pdf

# Literature review (standalone paper): Word with native equations; PDF via HTML
cd ..
python3 manuscripts/scripts/render_review.py
