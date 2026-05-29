#!/bin/bash
# build_clean.sh

master="main.tex"
base="${master%.tex}"
pdf_file="${base}.pdf"
needs_compile=0

# ── Decide whether to compile ────────────────────────────────────────────────
if [ ! -f "$pdf_file" ]; then
    needs_compile=1
else
    # Walk ALL .tex files in the tree, not just the root level
    while IFS= read -r -d '' file; do
        if [ "$file" -nt "$pdf_file" ]; then
            needs_compile=1
            break
        fi
    done < <(find . -name "*.tex" -print0)
fi

# ── Compile ──────────────────────────────────────────────────────────────────
if [ "$needs_compile" -eq 1 ]; then
    xelatex "$master"
    xelatex "$master"   # second pass for cross-references / headers

    # Remove auxiliary files created beside main.tex
    find . -maxdepth 1 -type f -name "${base}.*" \
        ! -name "${base}.tex" \
        ! -name "${base}.pdf" \
        -delete

    xdg-open "$pdf_file" &>/dev/null &
else
    echo "PDF is up to date."
fi
