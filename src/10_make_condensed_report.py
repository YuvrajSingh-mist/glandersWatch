"""Build the condensed (<=30 page) technical project report.

Run:  .venv/bin/python src/10_make_condensed_report.py
Then: cd report && tectonic GlandersWatch_Final_v2.tex

DESIGN PARITY: the preamble, the contents block and the bibliography block are
taken verbatim from the full builder, so the condensed report is typographically
identical to the 49-page one. Only the body prose and the float selection come
from report_condensed.py. Do not add layout overrides here.
"""
from __future__ import annotations

import importlib.util
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import diagrams as DG  # noqa: E402
import diagrams_platform as DP  # noqa: E402
import related_works as RW  # noqa: E402
import report_condensed as C  # noqa: E402
import report_front as RF  # noqa: E402

# the full builder owns the preamble, the contents block and data injection
_spec = importlib.util.spec_from_file_location(
    "full_builder", ROOT / "src" / "09_make_full_report.py")
FB = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(FB)

OUT = ROOT / "report"
OUT.mkdir(exist_ok=True)

BODY = (
    C.INTRO + C.LIT + C.ARCH + C.METHOD
    + C.MLOPS + C.RAG + C.ALERT + C.RESULTS + C.CONCL
)

# The condensed report drops the ablation and chained-pipeline results, so the shared
# Abstract must not advertise them. Applied here only, so the full report keeps its own
# abstract. Each entry is (old, new) and must match exactly once.
ABSTRACT_EDITS = [
    (
        "Six model families are trained under three validation schemes, and a\n"
        "three-stage chained pipeline is evaluated in which animal population is forecast before occurrence\n"
        "is predicted.",
        "Six model families are trained and compared under three validation schemes.",
    ),
    (
        "Chaining produces no measurable gain in discrimination. An ablation shows climate\n"
        "covariates transfer poorly across countries, and the model performs least well in low-income\n"
        "regions.",
        "The model performs least well in low-income regions, where label sparsity limits what\n"
        "can be learned.",
    ),
]


def condensed_front_matter() -> str:
    fm = RF.FRONT_MATTER
    for old, new in ABSTRACT_EDITS:
        if old not in fm:
            raise SystemExit(f"abstract edit not found: {old[:60]!r}")
        fm = fm.replace(old, new, 1)
    return fm


def build() -> pathlib.Path:
    # FB.PREAMBLE / FB.MIDDLE / FB.BACK are reused unchanged so that margins,
    # spacing, caption skips, contents depth and bibliography all match the full
    # report exactly.
    doc = FB.PREAMBLE + condensed_front_matter() + FB.MIDDLE + BODY + FB.BACK
    doc = doc.replace(r"\begin{document}",
                      "\\input{diagstyles.tex}\n\\begin{document}", 1)

    VALUES = dict(FB.VALUES)
    VALUES["BIBLIOGRAPHY"] = RW.bibliography_tex(long_form=True)
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
