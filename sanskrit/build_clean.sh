#!/bin/bash

master="main.tex"
base="${master%.tex}"
pdf_file="${base}.pdf"
needs_compile=0

# Check if the PDF is missing
if [ ! -f "$pdf_file" ]; then
    needs_compile=1
else
    # Check if ANY .tex file is newer than the PDF
    for file in *.tex; do
        if [ "$file" -nt "$pdf_file" ]; then
            needs_compile=1
            break
        fi
    done
fi

if [ "$needs_compile" -eq 1 ]; then
    # Compile ONLY the master file
    xelatex "$master"
    xelatex "$master"

    # Clean auxiliary files for the master file
    find . -maxdepth 1 -type f -name "${base}.*" ! -name "${base}.tex" ! -name "${base}.pdf" -delete

    # Open the PDF
    xdg-open "$pdf_file" &>/dev/null &
fi
