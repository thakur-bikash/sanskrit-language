#!/usr/bin/env python3
"""
Fix Sanskrit Mahabhashya LaTeX files:
  1. Convert \\sref{...} labels from Roman/IAST to Devanagari
  2. Remove commas from Sanskrit prose lines
  3. Replace full stops with single danda (।) mid-passage
     and double danda (॥) at the end of each passage
  4. Update the \\sref macro in main.tex to drop \\latinfont
"""

import re
import os

# ── digit mapping ──────────────────────────────────────────
DIGIT_MAP = str.maketrans('0123456789', '०१२३४५६७८९')

def to_dev(s: str) -> str:
    return s.translate(DIGIT_MAP)


# ── label conversion ───────────────────────────────────────
def convert_label(raw: str) -> str:
    """Turn a Roman/IAST \\sref label into Devanagari text."""
    label = raw.strip().replace('~', ' ').strip()

    # Pasp.N  or  Pasp.N.M  → पस्पशाह्निकम् N / N।M
    m = re.match(r'^Pasp\.\s*(.+)$', label)
    if m:
        num = m.group(1).strip()
        num = to_dev(num).replace('.', '।')
        return f'पस्पशाह्निकम् {num}'

    # Śs.N  Śs.N.M  Śs.N-M.K  → शिक्षा ...
    m = re.match(r'^[Śś]s\.\s*(.*)$', label)
    if m:
        rest = m.group(1).strip()
        if rest:
            rest = to_dev(rest).replace('.', '।')
            return f'शिक्षा {rest}'
        return 'शिक्षा'

    # Pure numeric  N  /  N.M  /  N.M.P  /  N.M.P.Q
    if re.match(r'^[\d.\-]+$', label):
        return to_dev(label).replace('.', '।')

    # Fallback: at least convert digits
    return to_dev(label)


# ── Sanskrit prose processing ──────────────────────────────
def process_sanskrit_line(text: str) -> str:
    """
    For one passage line:
      • remove commas
      • replace every internal  ' . '  with  ' । '
      • replace the trailing   ' .'  with  ' ॥'
        (or append  ' ॥'  if the line has no trailing period,
         e.g. refrain lines that just repeat the topic word)
    """
    # Remove commas (not part of classical Sanskrit orthography)
    text = re.sub(r'\s*,\s*', ' ', text)
    text = re.sub(r'  +', ' ', text).strip()

    if not text:
        return text

    # Internal sentence boundaries
    # Case 1: classic ' . ' (spaces on both sides)
    text = re.sub(r' \. ', ' । ', text)
    # Case 2: 'word. ' (period glued to previous word, space after)
    text = re.sub(r'(\S)\. ', r'\1 । ', text)

    # End-of-passage period
    # Case A: ' .' or 'word.' at end of line → ॥
    if re.search(r'\.\s*$', text):
        text = re.sub(r'\.\s*$', ' ॥', text)
    else:
        # No trailing period (refrain / topic-repeat line) – add ॥
        if not (text.endswith('।') or text.endswith('॥')):
            text += ' ॥'

    return text


# ── file-level processing ──────────────────────────────────
def process_content_file(content: str) -> str:
    """Process any chapter / pas / other .tex file."""
    lines = content.split('\n')
    result = []

    for line in lines:
        stripped = line.strip()

        # ── \\sref{LABEL}% lines ──
        m = re.match(r'^\s*\\sref\{([^}]*)\}%?\s*$', stripped)
        if m:
            new_label = convert_label(m.group(1))
            result.append(f'\\sref{{{new_label}}}%')
            continue

        # ── LaTeX command / comment / blank lines – leave untouched ──
        if not stripped or stripped.startswith('\\') or stripped.startswith('%'):
            result.append(line)
            continue

        # ── Sanskrit prose line ──
        result.append(process_sanskrit_line(stripped))

    return '\n'.join(result)


def update_main_tex(content: str) -> str:
    """
    Remove \\latinfont from the \\sref macro so that the Devanagari
    labels are rendered in the main Devanagari font.
    """
    # Replace only the relevant fragment inside the macro definition
    old = r'{\footnotesize\color{refgray}\latinfont[\thinspace#1\thinspace]}'
    new = r'{\footnotesize\color{refgray}[\thinspace#1\thinspace]}'
    updated = content.replace(old, new)
    if updated == content:
        print("  [!] main.tex macro fragment not found – check manually")
    return updated


# ── main ───────────────────────────────────────────────────
WORK_DIR = '/home/claude/patanjali'
OUT_DIR  = '/home/claude/patanjali_fixed'

os.makedirs(OUT_DIR, exist_ok=True)

FILES = [
    'main.tex',
    'pas.tex',
    'other.tex',
    'ch_01.tex',
    'ch_02.tex',
    'ch_03.tex',
    'ch_05.tex',
    'ch_06.tex',
    'ch_07.tex',
    'ch_08.tex',
]

for fname in FILES:
    src = os.path.join(WORK_DIR, fname)
    dst = os.path.join(OUT_DIR,  fname)

    with open(src, encoding='utf-8') as f:
        content = f.read()

    if fname == 'main.tex':
        result = update_main_tex(content)
    else:
        result = process_content_file(content)

    with open(dst, 'w', encoding='utf-8') as f:
        f.write(result)

    # Quick stats
    orig_dots   = content.count(' . ')
    new_single  = result.count('।')
    new_double  = result.count('॥')
    orig_commas = content.count(',')
    new_commas  = result.count(',')
    print(f'{fname:15s}  periods→dandas: {orig_dots:5d} → {new_single}।+{new_double}॥ '
          f'| commas: {orig_commas} → {new_commas}')

print('\nDone. Output in', OUT_DIR)
