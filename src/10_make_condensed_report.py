"""Build the condensed (<=30 page) technical project report.

Run:  .venv/bin/python src/10_make_condensed_report.py
Then: cd report && tectonic GlandersWatch_Final_v2.tex

The same VALUES dictionary as the full builder is reused, so every number is
still injected from reports/*.json. Only the prose and the float selection
differ from the full report.
"""
from __future__ import annotations

import importlib.util
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import diagrams as DG  # noqa: E402
import diagrams_platform as DP  # noqa: E402
import related_works as RW  # noqa: E402
import report_condensed as C  # noqa: E402
import report_front as RF  # noqa: E402

# the full builder owns data injection and the table row builders
_spec = importlib.util.spec_from_file_location(
    "full_builder", ROOT / "src" / "09_make_full_report.py")
FB = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(FB)

OUT = ROOT / "report"
OUT.mkdir(exist_ok=True)

PREAMBLE = r"""\documentclass[10pt,openany]{report}
\usepackage[a4paper,margin=0.8in,top=0.75in,bottom=0.75in]{geometry}
\usepackage{lmodern}
\usepackage[T1]{fontenc}
\usepackage{textcomp}
\usepackage{amsmath,amssymb}
\usepackage{graphicx}
\usepackage{booktabs}
\usepackage{array}
\usepackage{longtable}
\usepackage{multicol}
\usepackage{float}
\usepackage{tikz}
\usepackage{xcolor}
\usepackage{setspace}
\usepackage{caption}
\usepackage{hyperref}
\usetikzlibrary{shapes.geometric,arrows.meta,positioning,fit,backgrounds,calc,decorations.pathreplacing}

\hypersetup{
  colorlinks=true,
  linkcolor=black,
  citecolor=black,
  urlcolor=blue!45!black,
  pdftitle={GlandersWatch: A Modular Platform for Glanders Risk Prediction, Retrieval-Augmented Explanation and Owner Alerting},
  pdfauthor={Pedapatruni Shanmuk Vardhan, Shaktimayee Mohanty, Yuvraj Singh},
  pdfsubject={B.Tech Project Report, International Institute of Information Technology, Bhubaneswar}
}

\graphicspath{{../figures/}}
\captionsetup{font=small,labelfont=bf,skip=3pt}
\setlength{\parskip}{0.2em}
\setlength{\parindent}{0pt}
\linespread{0.98}
\setlength{\emergencystretch}{1.5em}
\setlength{\textfloatsep}{8pt plus 2pt minus 2pt}
\setlength{\floatsep}{6pt plus 2pt minus 2pt}
\setlength{\intextsep}{6pt plus 2pt minus 2pt}
\raggedbottom

\renewcommand{\thesection}{\arabic{section}.}
\renewcommand{\thesubsection}{\arabic{section}.\arabic{subsection}}

\counterwithin{figure}{chapter}
\counterwithin{table}{chapter}
\renewcommand{\thefigure}{\thechapter.\arabic{figure}}
\renewcommand{\thetable}{\thechapter.\arabic{table}}

\begin{document}
\pagenumbering{arabic}
\setcounter{page}{0}
"""

MIDDLE = r"""
% ============================== CONTENTS ==============================
\newpage
\pagestyle{plain}
\setcounter{tocdepth}{0}
\noindent\underline{\textbf{Contents}}
\vspace{0.4cm}
% \par is required: the underline box above leaves TeX in horizontal mode, and
% \@starttoc emits vertical material, which would raise "missing \item".
\par
\makeatletter
\@starttoc{toc}
\makeatother
"""

BACK = r"""
% ============================== REFERENCES ==============================
\newpage
\chapter*{Bibliography}
\addcontentsline{toc}{chapter}{Bibliography}
\renewcommand{\bibname}{}
\begin{spacing}{0.95}
\footnotesize
@BIBLIOGRAPHY@
\end{spacing}

\end{document}
"""

BODY = (
    C.INTRO + C.LIT + C.ARCH + C.METHOD
    + C.MLOPS + C.RAG + C.ALERT + C.RESULTS + C.CONCL
)


def breakable_refs(tex: str) -> str:
    """Insert break points in DOIs and URLs so a narrow column cannot overflow."""
    import re as _re

    def split_token(m: "_re.Match") -> str:
        tok = m.group(0)
        for ch in ("/", ".", "-", "_"):
            tok = tok.replace(ch, ch + r"\allowbreak{}")
        return tok

    return _re.sub(r"(?:doi:|https?://|www\.)\S+", split_token, tex)


def scale_figures(doc: str) -> str:
    """Shrink raster figure widths so floats pack tighter."""
    def repl(m: re.Match) -> str:
        return f"width={float(m.group(1)) * 0.84:.2f}\\textwidth"
    return re.sub(r"width=(0\.[0-9]+)\\textwidth", repl, doc)


def build() -> pathlib.Path:
    doc = PREAMBLE + RF.FRONT_MATTER + MIDDLE + BODY + BACK
    doc = doc.replace(r"\begin{document}",
                      "\\input{diagstyles.tex}\n\\begin{document}", 1)
    doc = scale_figures(doc)

    VALUES = dict(FB.VALUES)
    VALUES["BIBLIOGRAPHY"] = breakable_refs(RW.bibliography_tex(long_form=True))
    for k, v in VALUES.items():
        doc = doc.replace(f"@{k}@", str(v))

    leftover = [t for t in doc.split("@") if t.isupper() and len(t) > 3]
    if leftover:
        print("WARNING: unresolved tokens:", sorted(set(leftover))[:10])

    (OUT / "diagstyles.tex").write_text(DG.STYLES, encoding="utf-8")
    for name, tex in [("fig_architecture", DP.ARCHITECTURE),
                      ("fig_serving", DP.SERVING),
                      ("fig_rag", DP.RAG),
                      ("fig_alertflow", DP.ALERT)]:
        (OUT / f"{name}.tex").write_text(tex, encoding="utf-8")

    path = OUT / "GlandersWatch_Final_v2.tex"
    path.write_text(doc, encoding="utf-8")
    print(f"wrote {path.relative_to(ROOT)} ({len(doc):,} chars)")
    return path


if __name__ == "__main__":
    build()
