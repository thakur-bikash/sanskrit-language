#!/usr/bin/env python3
import re
import os
import glob
import zipfile
import tempfile

DIGIT_MAP = str.maketrans('0123456789', '०१२३४५६७८९')

def to_dev(s):
    return s.translate(DIGIT_MAP)

def fix_avagraha(text):
    text = re.sub(r"([ऀ-ॿ])\s*'\s*([ऀ-ॿ])", r'\1ऽ\2', text)
    text = re.sub(r"([ऀ-ॿ])'", r'\1ऽ', text)
    text = re.sub(r"'([ऀ-ॿ])", r'ऽ\1', text)
    return text

PROTECT_RE = re.compile(
    r'\\label\{[^}]+\}'
    r'|\\(?:ref|pageref|nameref|autoref)\{[^}]+\}'
    r'|\\(?:sutraref|skreference)\{[^}]+\}'
    r'|\\hyperref\[[^\]]+\]'
    r'|\\(?:input|include|usepackage|RequirePackage)\{[^}]+\}'
    r'|\\(?:setcounter|addtocounter|stepcounter)\{[^}]+\}\{[^}]*\}'
    r'|\\(?:value|arabic|roman|Roman|alph|Alph|fnsymbol)\{[^}]+\}'
    r'|\\(?:newcounter|renewcounter|newcommand|renewcommand|providecommand)\*?\{[^\}]+\}(?:\[\d+\])?'
    r'|\\(?:fontsize|scalebox|resizebox)\{[^}]*\}\{[^}]*\}'
    r'|\\setstretch\{[^}]+\}'
    r'|\\\\\[[^\]]*\]'
    r'|\\(?:vspace|hspace)\*?\{[^}]+\}'
    r'|\\(?:rule)\{[^}]+\}\{[^}]+\}'
    r'|\\(?:geometry|hypersetup)\{[^}]+\}'
    r'|#\d'
)

def convert_digits_in_file(text):
    lines = text.split('\n')
    result = []
    for line in lines:
        cpos = -1
        skip = False
        for i, ch in enumerate(line):
            if skip:
                skip = False
                continue
            if ch == '\\':
                skip = True
            elif ch == '%':
                cpos = i
                break
        
        content = line[:cpos] if cpos >= 0 else line
        comment = line[cpos:] if cpos >= 0 else ''
        
        protected = {}
        ctr = [0]
        
        def protect_match(m, _p=protected, _c=ctr):
            key = '\x00P%05d\x00' % _c[0]
            _p[key] = m.group(0)
            _c[0] += 1
            return key
            
        content = PROTECT_RE.sub(protect_match, content)
        content = to_dev(content)
        
        for k, v in protected.items():
            content = content.replace(k, v)
            
        result.append(content + comment)
    return '\n'.join(result)

def fix_punctuation(text):
    text = re.sub(r'\?\s*॥', '॥', text)
    text = re.sub(r'\?', '।', text)
    text = re.sub(r'!\s*॥', '॥', text)
    text = re.sub(r'!', '।', text)
    return text

COUNTER_BLOCK = r"""% ── Late-Binding Devanagari Counters ─────────────────────────────────────────
\makeatletter
\def\dev@digits#1{\ifx#1\@nil\else
  \ifx#10०\else\ifx#11१\else\ifx#12२\else\ifx#13३\else\ifx#14४\else
  \ifx#15५\else\ifx#16६\else\ifx#17७\else\ifx#18८\else\ifx#19९\else
  #1\fi\fi\fi\fi\fi\fi\fi\fi\fi\fi
  \expandafter\dev@digits\fi}
\def\devanagaridigits#1{\expandafter\dev@digits\number#1\@nil}

\AtBeginDocument{
  \def\thepart{\devanagaridigits{\c@part}}
  \def\thechapter{\devanagaridigits{\c@chapter}}
  \def\thesection{\thechapter.\devanagaridigits{\c@section}}
  \def\thesubsection{\thesection.\devanagaridigits{\c@subsection}}
  \def\thesubsubsection{\thesubsection.\devanagaridigits{\c@subsubsection}}
  \def\thepage{\devanagaridigits{\c@page}}
  \def\theequation{\devanagaridigits{\c@equation}}
  \def\thefigure{\devanagaridigits{\c@figure}}
  \def\thetable{\devanagaridigits{\c@table}}
}
\makeatother
"""

def fix_xelatex_shaping(text):
    text = re.sub(
        r'\\(setmainfont|newfontfamily|setsansfont|setmonofont)(\\[a-zA-Z]+)?\[([^\]]+)\]\{([^}]+)\}',
        lambda m: f"\\{m.group(1)}{m.group(2) or ''}[{m.group(3)},Script=Devanagari]{{{m.group(4)}}}" if 'Script=Devanagari' not in m.group(3) else m.group(0),
        text
    )
    text = re.sub(
        r'\\(setmainfont|newfontfamily|setsansfont|setmonofont)(\\[a-zA-Z]+)?\{([^}]+)\}',
        r'\\\1\2[Script=Devanagari]{\3}',
        text
    )
    return text

def patch_main_tex(fpath, project):
    if not os.path.exists(fpath):
        return
        
    with open(fpath, 'r', encoding='utf-8') as f:
        text = f.read()

    text = fix_avagraha(text)
    text = fix_xelatex_shaping(text)
        
    text = re.sub(r'% ── Devanagari counters.*?(?=\\begin\{document\})', '', text, flags=re.DOTALL)
    text = re.sub(r'% ── Devanagari Counters Override.*?(?=\\begin\{document\})', '', text, flags=re.DOTALL)
    text = re.sub(r'% ── Late-Binding Devanagari Counters.*?(?=\\begin\{document\})', '', text, flags=re.DOTALL)
        
    text = text.replace('\\begin{document}', COUNTER_BLOCK + '\\begin{document}', 1)
        
    text = re.sub(
        r'(\\hyperref\[sutra:#1\]\{\\textnormal\{\\textbf\{\[)(#1)(\]\}\})',
        r'\1\\devanagaridigits{\2}\3',
        text
    )
    text = re.sub(
        r'(\\textnormal\{\\textbf\{\\small\[SK\\,)(#1)(\]\}\})',
        r'\1\\devanagaridigits{\2}\3',
        text
    )
    text = re.sub(
        r'(\\noindent\\textbf\{#2\}\\quad\\small\{\()(#1)(\)\})',
        r'\1\\devanagaridigits{\2}\3',
        text
    )
    
    with open(fpath, 'w', encoding='utf-8') as f:
        f.write(text)
    print(f"  Patched main.tex: {project}")

def process_pada_files(pada_glob):
    files = sorted(glob.glob(pada_glob))
    total_q = 0
    for fpath in files:
        with open(fpath, 'r', encoding='utf-8') as f:
            text = f.read()
            
        q_before = text.count('?') + text.count('!')
        text = fix_punctuation(text)
        text = fix_avagraha(text)
        text = convert_digits_in_file(text)
        
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(text)
            
        total_q += q_before
        
    print(f"  Processed {len(files)} pada files, ~{total_q} punctuation marks converted")

def process_zip_project(zip_filename):
    if not os.path.exists(zip_filename):
        print(f"  SKIP: {zip_filename} not found.")
        return

    project_name = zip_filename.split('_')[0]
    out_zip_filename = zip_filename.replace('.zip', '_final.zip')

    print(f"\n[{project_name.upper()}]")

    with tempfile.TemporaryDirectory() as tmpdir:
        with zipfile.ZipFile(zip_filename, 'r') as zf:
            zf.extractall(tmpdir)

        patch_main_tex(os.path.join(tmpdir, 'main.tex'), project_name)
        process_pada_files(os.path.join(tmpdir, 'pada_*.tex'))

        with zipfile.ZipFile(out_zip_filename, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
            for root, _, files in os.walk(tmpdir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, tmpdir)
                    zf.write(file_path, arcname)

    print(f"  Created updated archive: {out_zip_filename}")

if __name__ == "__main__":
    zip_files = [
        'bhashya_overleaf_fixed.zip',
        'kashika_overleaf_fixed.zip',
        'kaumudi_overleaf_fixed.zip'
    ]
    
    for zip_file in zip_files:
        process_zip_project(zip_file)
        
    print("\nDone.")
