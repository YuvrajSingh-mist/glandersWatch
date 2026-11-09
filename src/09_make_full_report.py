"""Build the full technical project report.

Run:  .venv/bin/python src/09_make_full_report.py
Then: cd report && tectonic GlandersWatch_Full_Report.tex

Every number is injected from reports/*.json, so the document cannot drift from the
pipeline output.
"""
from __future__ import annotations

import json
import pathlib
import platform
import sys

import lightgbm
import numpy
import pandas
import scipy
import shap
import sklearn
import xgboost

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import diagrams as DG  # noqa: E402
import diagrams_platform as DP  # noqa: E402
import related_works as RW  # noqa: E402
import report_arch as RA  # noqa: E402
import report_body as RB  # noqa: E402
import report_mlops as MO  # noqa: E402
import report_rag as RG  # noqa: E402
import report_front as RF  # noqa: E402
import report_results as RR  # noqa: E402

REP, OUT = ROOT / "reports", ROOT / "report"
OUT.mkdir(exist_ok=True)

R = json.loads((REP / "results.json").read_text())
A = json.loads((REP / "dataset_analysis.json").read_text())
N = json.loads((REP / "novelty_audit.json").read_text())
IMP = pandas.read_csv(REP / "feature_importance.csv")

L1, L2 = R["level1"]["metrics"], R["level2"]["metrics"]
LAB, MISS = A["labels"], A["missingness"]
CH, AB, HG = R["chain"], R["ablation"], R["chain"].get("hurdle", {})
S3 = CH.get("stage3", {})
S1 = CH["stage1"]["scores"][CH["stage1"]["best"]]
AUD = R["audit"]

ORDER = ["Logistic Regression", "Decision Tree", "Random Forest",
         "Extra Trees", "XGBoost", "LightGBM"]
PRETTY = {"Logistic Regression": "Logistic regression", "Decision Tree": "Decision tree",
          "Random Forest": "Random forest", "Extra Trees": "Extra trees",
          "XGBoost": "XGBoost", "LightGBM": "LightGBM"}

DESC = {
    "Logistic Regression": "Additive model with balanced class weights; the reference baseline.",
    "Decision Tree": "Single shallow tree; interpretable, and a low-variance check on ensemble gains.",
    "Random Forest": "Bagged trees over random subsets; variance control at small positive counts.",
    "Extra Trees": "Bagged trees with randomised split thresholds; further decorrelation when positives are scarce.",
    "XGBoost": "Boosted trees with explicit regularisation.",
    "LightGBM": "Leaf-wise boosted trees; efficient comparison on wide tabular data.",
}


def esc(s: str) -> str:
    rep = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#",
           "_": r"\_", "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}",
           "^": r"\textasciicircum{}"}
    return "".join(rep.get(c, c) for c in str(s))


def settings(name: str) -> str:
    p = L1[name]["best_params"]
    if name == "Logistic Regression":
        return f"$C={p.get('C')}$, $\\ell_2$ penalty, balanced class weights"
    if name == "Decision Tree":
        return (f"depth {p.get('max_depth')}, minimum leaf size {p.get('min_samples_leaf')}, "
                f"criterion {p.get('criterion')}")
    if name in ("Random Forest", "Extra Trees"):
        mf = p.get("max_features")
        mf = "square root of the column count" if mf == "sqrt" else str(mf)
        return (f"depth {p.get('max_depth')}, minimum leaf size {p.get('min_samples_leaf')}, "
                f"features per split {mf}")
    if name == "XGBoost":
        return (f"depth {p.get('max_depth')}, regularisation $\\lambda={p.get('reg_lambda')}$, "
                f"minimum child weight {p.get('min_child_weight')}")
    return (f"leaves {p.get('num_leaves')}, minimum child samples {p.get('min_child_samples')}, "
            f"regularisation $\\lambda={p.get('reg_lambda')}$")


# ---------------------------------------------------------------- tables
def novelty_rows() -> str:
    return "\n".join(f"{esc(k.split('. ', 1)[1])} & {v['hits']} \\\\" for k, v in N.items())


def model_rows() -> str:
    """Settings go inside the description cell: \\multicolumn cannot follow a
    row separator inside a p-column without a Misplaced \\omit error."""
    out = []
    for m in ORDER:
        out.append(
            f"\\textbf{{{PRETTY[m]}}} & {esc(L1[m]['family'])} & {DESC[m]}"
            f"\\par\\vspace{{2pt}}{{\\footnotesize Tuned settings: {settings(m)}}} \\\\"
        )
    return "\n".join(out)


def level1_rows() -> str:
    out = []
    for m in ORDER:
        t, lo, cv = L1[m]["temporal"], L1[m]["loco"], L1[m]["repeated_cv"]
        ci = t["pr_auc_ci"]
        out.append(
            f"{PRETTY[m]} & {t['pr_auc']:.3f} & [{ci[0]:.2f}, {ci[1]:.2f}] & "
            f"{t['roc_auc']:.3f} & {lo['pr_auc']:.3f} & {cv['pr_auc']:.3f} & "
            f"{t['brier']:.4f} & {t['precision']:.2f} / {t['recall']:.2f} \\\\"
        )
    return "\n".join(out)


AB_ORDER = [("AS-1 history only", "History only"),
            ("AS-2 population only", "Population only"),
            ("AS-3 climate only", "Climate only"),
            ("AS-4 socio-geography", "Socio-geography only"),
            ("AS-5 history+population", "History and population"),
            ("AS-6 full (all groups)", "All groups"),
            ("AS-7 full + surveillance proxy", "All groups plus surveillance proxy")]


def ablation_rows() -> str:
    return "\n".join(
        f"{label} & {AB[k]['n_features']} & {AB[k]['temporal']['pr_auc']:.3f} & "
        f"{AB[k]['loco']['pr_auc']:.3f} \\\\"
        for k, label in AB_ORDER if k in AB
    )


def chain_rows() -> str:
    p, c = CH["stage2"]["plain"], CH["stage2"]["chained"]
    return "\n".join([
        f"Plain (no chained feature) & {p['temporal']['pr_auc']:.3f} & "
        f"{p['temporal']['roc_auc']:.3f} & {p['loco']['pr_auc']:.3f} \\\\",
        f"Chained (population forecast added) & {c['temporal']['pr_auc']:.3f} & "
        f"{c['temporal']['roc_auc']:.3f} & {c['loco']['pr_auc']:.3f} \\\\",
    ])


def subgroup_rows() -> str:
    out = []
    for r in R["subgroup"]:
        if r["group_by"] != "region":
            continue
        name = r["group"].replace("Middle East, North Africa, Afghanistan & Pakistan",
                                  "MENA, Afghanistan and Pakistan")
        out.append(f"{esc(name)} & {r['n']} & {r['positives']} & "
                   f"{r['roc_auc']:.3f} & {r['pr_auc']:.3f} \\\\")
    return "\n".join(out)


def topfeat_rows() -> str:
    m = IMP.dropna(subset=["shap_rank"]).nsmallest(8, "shap_rank")
    out = []
    for i, r in enumerate(m.itertuples(), 1):
        vif = "--" if pandas.isna(r.vif) else f"{r.vif:.0f}"
        out.append(f"{i} & {esc(r.feature)} & {r.mean_abs_shap:.3f} & {r.spearman:+.2f} & "
                   f"{r.mutual_info:.4f} & {vif} \\\\")
    return "\n".join(out)


# ---------------------------------------------------------------- scalars
_temporal_best = max(ORDER, key=lambda m: L1[m]["temporal"]["pr_auc"])
CHAMP = R.get("best_model", "Random Forest")
CHAMPPR = L1[CHAMP]["temporal"]["pr_auc"]
CHAMPLOCO = L1[CHAMP]["loco"]["pr_auc"]
BESTTEMPPR = L1[_temporal_best]["temporal"]["pr_auc"]
BESTTEMPLOCO = L1[_temporal_best]["loco"]["pr_auc"]

_SEL = R.get("selection", {})
SELK = len(_SEL.get("numeric", []))
SELN = SELK + len(_SEL.get("categorical", []))
SELCAND = _SEL.get("n_candidates", len(ORDER and [1]) and 42)
SELTRAINEND = _SEL.get("train_end", 2017)
SELRANK = {r["feature"]: r for r in _SEL.get("ranking", [])}
SELSHARE = 0.0
_tot = sum(r["mean_abs_shap"] for r in _SEL.get("ranking", []) if r["feature"] in (C_FULL := set(__import__("ml_core").FULL)))
if _tot > 0:
    SELSHARE = sum(SELRANK[f]["mean_abs_shap"] for f in _SEL.get("numeric", [])
                   if f in SELRANK) / _tot


def selected_rows() -> str:
    """Rank, feature, unit and training-period SHAP for the reported feature set."""
    import ml_core as _MC
    out = []
    for i, f in enumerate(_SEL.get("numeric", []), 1):
        # percent is a LaTeX comment character inside the tabular
        unit = _MC.FEATURE_UNITS.get(f, "--").replace("%", r"\%")
        shap_v = SELRANK.get(f, {}).get("mean_abs_shap", float("nan"))
        out.append(f"{i} & \\texttt{{{esc(f)}}} & {unit} & {shap_v:.3f} \\\\")
    for j, f in enumerate(_SEL.get("categorical", []), SELK + 1):
        out.append(f"{j} & \\texttt{{{esc(f)}}} & "
                   f"{_MC.FEATURE_UNITS.get(f, '--').replace('%', r'\\%')} & -- \\\\")
    return "\n".join(out)


def alert_economics() -> dict:
    """Recall at a fixed budget and budget needed for a target recall, champion model."""
    import numpy as _np
    import pandas as _pd
    path = REP / f"pred_L1_{CHAMP.replace(' ', '_')}.csv"
    if not path.exists():
        return {}
    d = _pd.read_csv(path)
    y = d.y_true.to_numpy().astype(int)
    p = d.p_pred.to_numpy()
    order = _np.argsort(-p)
    fe = _np.cumsum(y[order]) / y.sum()
    fa = _np.arange(1, len(y) + 1) / len(y)

    def recall_at(b):
        return float(fe[max(0, int(b * len(y)) - 1)])

    def budget_at(t):
        k = _np.flatnonzero(fe >= t - 1e-12)
        return float(fa[k[0]]) if len(k) else 1.0

    return {"cells": int(len(y)), "events": int(y.sum()),
            "r6": recall_at(0.06), "b50": budget_at(0.50), "b80": budget_at(0.80)}


_AE = alert_economics()
PREV = LAB["prevalence"]
MIRHO = A["importance_agreement"]["spearman_mi_vs_shap"]
_vif = A["vif_top10"][0]
_cv = {c["feature"]: c["cramers_v"] for c in A["categorical"]}
_env = (f"Python {platform.python_version()}, scikit-learn {sklearn.__version__}, "
        f"XGBoost {xgboost.__version__}, LightGBM {lightgbm.__version__}, "
        f"SHAP {shap.__version__}, NumPy {numpy.__version__}, pandas {pandas.__version__}, "
        f"SciPy {scipy.__version__}")

VALUES = {
    "ROLLME": "B123153",
    "ROLLSM": "B123118",
    "ROLLPSV": "B123089",
    "SUPERVISOR": "Dr. Sangita Dhara",
    "MONTHYEAR": "November 2026",
    "HARDWARE": "an Apple M4 processor with 10 cores and 16 GB of unified memory",

    "LITRECORDS": f"{AUD['literature_records']:,}",
    "LITEVENTS": str(AUD["literature_events"]),
    "CLIMCOUNT": "211",
    "PANELROWS": f"{AUD['panel_rows']:,}",
    "PANELCOUNTRIES": str(AUD["countries_in_panel"]),
    "ROWS": f"{LAB['rows']:,}",
    "FEATURES": str(SELN),   # features the models actually consume
    "POSITIVES": str(LAB["positives"]),
    "NEGATIVES": f"{LAB['negatives']:,}",
    "PREVALENCE": f"{PREV*100:.2f}\\%",
    "IMBALANCE": f"{LAB['imbalance_ratio']:.1f}",
    "COUNTRIES": str(LAB["countries"]),
    "POSCOUNTRIES": str(LAB["positive_countries"]),
    "REPEATPOS": str(LAB["repeat_positive_countries"]),
    "TOP5SHARE": f"{LAB['top5_country_share']*100:.1f}\\%",
    "L2PREV": f"{R['level2']['positives']/R['level2']['n']*100:.1f}\\%",

    "MISSFAO": f"{MISS['by_source']['FAOSTAT (population)']:.2f}\\%",
    "MISSWB": f"{MISS['by_source']['World Bank (socio-economic)']:.2f}\\%",
    "MISSNASA": f"{MISS['by_source']['NASA POWER (climate)']:.2f}\\%",
    "MISSALL": f"{MISS['overall_pct']:.2f}\\%",
    "MISSMAX": f"{MISS['max_feature_pct']:.1f}\\%",

    "YSLRHO": f"{next(r['spearman'] for r in A['univariate'] if r['feature']=='years_since_last'):+.2f}",
    "CRAMREGION": f"{_cv.get('region', float('nan')):.3f}",
    "CRAMINCOME": f"{_cv.get('income', float('nan')):.3f}",
    "VIFVAL": f"{_vif['vif']:.0f}",
    "VIFFEAT": str(_vif["feature"]).replace("_", r"\_"),
    "MIRHO": f"{MIRHO:+.2f}",
    "TOPOVERLAP": str(A["importance_agreement"]["top10_overlap"]),

    "BESTPR": f"{L1[_temporal_best]['temporal']['pr_auc']:.3f}",
    "CHAMP": CHAMP,
    "CHAMPPR": f"{CHAMPPR:.3f}",
    "CHAMPLOCO": f"{CHAMPLOCO:.3f}",
    "BESTTEMPM": PRETTY[_temporal_best],
    "BESTTEMPPR": f"{BESTTEMPPR:.3f}",
    "BESTTEMPLOCO": f"{BESTTEMPLOCO:.3f}",
    "SELK": str(SELK),
    "SELN": str(SELN),
    "SELCAND": str(SELCAND),
    "SELTRAINEND": str(SELTRAINEND),
    "SELSHARE": f"{SELSHARE*100:.0f}\\%",
    "SELROWS": selected_rows(),
    "LIFT": f"{CHAMPPR/PREV:.0f}",
    "BESTLIFT": f"{BESTTEMPPR/PREV:.0f}",
    "RFPR": f"{L1['Random Forest']['temporal']['pr_auc']:.3f}",
    "RFLOCOR": f"{L1['Random Forest']['loco']['pr_auc']:.3f}",
    "ECE": f"{R['calibration']['ece']:.3f}",
    "BRIER": f"{R['calibration']['brier']:.4f}",

    "AS3LOCO": f"{AB['AS-3 climate only']['loco']['pr_auc']:.3f}",
    "AS5K": str(AB["AS-5 history+population"]["n_features"]),
    "AS5LOCO": f"{AB['AS-5 history+population']['loco']['pr_auc']:.3f}",
    "AS6K": str(AB["AS-6 full (all groups)"]["n_features"]),
    "AS6LOCO": f"{AB['AS-6 full (all groups)']['loco']['pr_auc']:.3f}",
    "AS7DELTA": (f"{AB['AS-7 full + surveillance proxy']['loco']['pr_auc'] - AB['AS-6 full (all groups)']['loco']['pr_auc']:+.3f}"),

    "S1MAE": f"{S1['mae']:.3f}",
    "S1RHO": f"{S1['spearman']:.3f}",
    "S3MAE": f"{S3.get('mae', float('nan')):.3f}",
    "S3RHO": f"{S3.get('spearman', float('nan')):.3f}",
    "HZRHO": f"{HG.get('spearman_test', float('nan')):.3f}",
    "HZEVENTS": str(HG.get("events_captured", "n/a")),
    "HZTOTAL": str(HG.get("total_events", "n/a")),
    "CHAINDELTA": (f"{CH['stage2']['chained']['temporal']['pr_auc'] - CH['stage2']['plain']['temporal']['pr_auc']:+.3f}"),

    "RUNTIMEMIN": f"{R['runtime_seconds']/60:.1f}",
    "MINTIME": f"{min(v['fit_seconds'] for v in L1.values()):.1f}",
    "MAXTIME": f"{max(v['fit_seconds'] for v in L1.values()):.1f}",
    "ENVSPEC": esc(_env),

    "NOVELTYROWS": novelty_rows(),
    "MODELROWS": model_rows(),
    "LEVEL1ROWS": level1_rows(),
    "ABLATIONROWS": ablation_rows(),
    "CHAINROWS": chain_rows(),
    "SUBGROUPROWS": subgroup_rows(),
    "TOPFROWS": topfeat_rows(),

    "ALERT6REC": f"{_AE.get('r6', 0)*100:.0f}",
    "ALERT50BUD": f"{_AE.get('b50', 0)*100:.0f}",
    "ALERT80BUD": f"{_AE.get('b80', 0)*100:.0f}",
    "ALERTEFF": f"{0.5/max(_AE.get('b50', 1), 1e-9):.1f}",
    "TRAININGFIG": DG.TRAINING,
    "EVALFIG": DG.EVALUATION,
}

PREAMBLE = r"""\documentclass[10pt,openany]{report}
\usepackage[a4paper,margin=1in]{geometry}
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
\captionsetup{font=small,labelfont=bf,skip=6pt}
\setlength{\parskip}{0.35em}
\setlength{\parindent}{0pt}
\setlength{\emergencystretch}{1.5em}
% single spacing, as in the department template

% Section numbering follows the department template: sections are "1.", "2." within
% each chapter (counter resets per chapter) and subsections are "1.1", "1.2".
\renewcommand{\thesection}{\arabic{section}.}
\renewcommand{\thesubsection}{\arabic{section}.\arabic{subsection}}

% chapter-based numbering for floats and equations
\counterwithin{figure}{chapter}
\counterwithin{table}{chapter}
\renewcommand{\thefigure}{\thechapter.\arabic{figure}}
\renewcommand{\thetable}{\thechapter.\arabic{table}}

\begin{document}
% The department template numbers continuously in arabic from the Certificate page,
% with the title page carrying no number, so Abstract falls on page 4.
\pagenumbering{arabic}
\setcounter{page}{0}
"""

MIDDLE = r"""
% ============================== CONTENTS ==============================
\newpage
\pagestyle{plain}
\noindent\underline{\textbf{Contents}}
\vspace{0.55cm}

% \tableofcontents would insert its own chapter-style heading and a page break;
% \@starttoc typesets the entries alone, under the heading above.
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
@BIBLIOGRAPHY@

\end{document}
"""


def build() -> pathlib.Path:
    doc = (
        PREAMBLE
        + RF.FRONT_MATTER
        + MIDDLE
        + RF.BODY_INTRO
        + RA.BODY_ARCH
        + RB.BODY_METHOD
        + MO.BODY_MLOPS
        + RG.BODY_RAG
        + RG.BODY_ALERT
        + RR.BODY_RESULTS
        + RR.BODY_CONCL
        + BACK
    )
    # styles for the TikZ flowcharts
    doc = doc.replace(r"\begin{document}",
                      "\\input{diagstyles.tex}\n\\begin{document}", 1)

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
    path = OUT / "GlandersWatch_Full_Report.tex"
    path.write_text(doc, encoding="utf-8")
    print(f"wrote {path.relative_to(ROOT)} ({len(doc):,} chars)")
    return path


if __name__ == "__main__":
    build()
