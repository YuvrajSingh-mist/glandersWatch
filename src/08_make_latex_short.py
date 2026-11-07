"""Condensed (short) LaTeX report - essentials only.

Run:  .venv/bin/python src/08_make_latex_short.py
"""
from __future__ import annotations

import json
import pathlib
import platform

import lightgbm, numpy, pandas, scipy, shap, sklearn, xgboost

ROOT = pathlib.Path(__file__).resolve().parents[1]
REP, OUT = ROOT / "reports", ROOT / "report"
OUT.mkdir(exist_ok=True)

R = json.loads((REP / "results.json").read_text())
A = json.loads((REP / "dataset_analysis.json").read_text())
IMP = pandas.read_csv(REP / "feature_importance.csv")
import related_works as RW
import diagrams as DG
N = json.loads((REP / "novelty_audit.json").read_text())

ORDER = ["Logistic Regression", "Decision Tree", "Random Forest",
         "Extra Trees", "XGBoost", "LightGBM"]
BEST = R["best_model"]
L1, L2 = R["level1"]["metrics"], R["level2"]["metrics"]
LAB, MISS = A["labels"], A["missingness"]
CH, AB = R["chain"], R["ablation"]
HG, S3 = CH.get("hurdle", {}), CH.get("stage3", {})
AUD = R["audit"]
PREV = LAB["prevalence"]
L2_PREV = R["level2"]["positives"] / R["level2"]["n"]

SEQ = ["Logistic regression", "Decision tree", "Random forest",
       "Extra trees", "XGBoost", "LightGBM"]
NAME = {"Logistic regression": "Logistic Regression", "Decision tree": "Decision Tree",
        "Random forest": "Random Forest", "Extra trees": "Extra Trees",
        "XGBoost": "XGBoost", "LightGBM": "LightGBM"}


def esc(s: str) -> str:
    rep = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$",
           "#": r"\#", "_": r"\_", "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}",
           "^": r"\textasciicircum{}"}
    return "".join(rep.get(c, c) for c in str(s))


def f3(x):
    return f"{x:.3f}"


# ---------------------------------------------------------------- tables
def t_sources() -> str:
    rows = [
        ("Europe PMC, text-mined occurrences", "Animal history",
         f"{AUD['literature_records']:,} records / {AUD['literature_events']} events"),
        ("FAOSTAT livestock stocks (7 species)", "Animal population", "68,449 stock rows, 1961--2023"),
        ("World Bank WDI + centroids", "Socio-economic context", "10 indicators, 217 countries"),
        ("NASA POWER agro-climatology", "Environment", "6 variables, 211 centroids"),
    ]
    return "\n".join(f"{a} & {b} & {c} \\\\" for a, b, c in rows)


def t_labels() -> str:
    rows = [
        ("Observations", f"{LAB['rows']:,}"),
        ("Positives / negatives", f"{LAB['positives']} / {LAB['negatives']:,}"),
        ("Prevalence", f"{PREV*100:.2f}\\%"),
        ("Imbalance ratio", f"{LAB['imbalance_ratio']:.1f} : 1"),
        ("Countries with any positive", f"{LAB['positive_countries']} / {LAB['countries']}"),
        ("Repeat-positive countries", f"{LAB['repeat_positive_countries']} ({LAB['repeat_positive_rate']*100:.0f}\\%)"),
        ("Positives in top-5 countries", f"{LAB['top5_country_share']*100:.1f}\\%"),
    ]
    return "\n".join(f"{a} & {b} \\\\" for a, b in rows)


def t_features() -> str:
    m = IMP.dropna(subset=["shap_rank"]).nsmallest(8, "shap_rank")
    rows = []
    for i, r in enumerate(m.itertuples(), 1):
        vif = "--" if pandas.isna(r.vif) else f"{r.vif:.0f}"
        rows.append(f"{i} & {esc(r.feature)} & {r.mean_abs_shap:.3f} & "
                    f"{r.spearman:+.2f} & {r.mutual_info:.4f} & {vif} \\\\")
    return "\n".join(rows)


def t_models() -> str:
    rows = []
    for m in SEQ:
        p = L1[NAME[m]]["best_params"]
        if m == "Logistic regression":
            cfg = f"$C={p.get('C')}$, $\\ell_2$, balanced"
        elif m == "Decision tree":
            cfg = f"depth {p.get('max_depth')}, leaf {p.get('min_samples_leaf')}"
        elif m in ("Random forest", "Extra trees"):
            cfg = (f"depth {p.get('max_depth')}, leaf {p.get('min_samples_leaf')}, "
                   f"mtry {p.get('max_features')}")
        elif m == "XGBoost":
            cfg = f"depth {p.get('max_depth')}, $\\lambda$={p.get('reg_lambda')}"
        else:
            cfg = f"leaves {p.get('num_leaves')}, min child {p.get('min_child_samples')}"
        rows.append(f"{m} & {esc(L1[NAME[m]]['family'])} & {cfg} \\\\")
    return "\n".join(rows)


def t_l1() -> str:
    rows = []
    for m in SEQ:
        v = L1[NAME[m]]
        t, lo, cv = v["temporal"], v["loco"], v["repeated_cv"]
        ci = t["pr_auc_ci"]
        star = r"$^{\star}$" if NAME[m] == BEST else ""
        rows.append(
            f"{m}{star} & {f3(t['pr_auc'])} [{ci[0]:.2f},{ci[1]:.2f}] & {f3(t['roc_auc'])} & "
            f"{f3(lo['pr_auc'])} & {f3(cv['pr_auc'])} & {t['brier']:.4f} & "
            f"{t['precision']:.2f} & {t['recall']:.2f} \\\\"
        )
    return "\n".join(rows)


def t_ablation() -> str:
    keep = ["AS-1 history only", "AS-2 population only", "AS-3 climate only",
            "AS-5 history+population", "AS-6 full (all groups)"]
    rows = []
    for k in keep:
        v = AB[k]
        rows.append(f"{esc(k)} & {v['n_features']} & {f3(v['temporal']['pr_auc'])} & "
                    f"{f3(v['loco']['pr_auc'])} \\\\")
    return "\n".join(rows)


def t_subgroup() -> str:
    rows = []
    for r in R["subgroup"]:
        if r["group_by"] != "region":
            continue
        name = r["group"].replace("Middle East, North Africa, Afghanistan & Pakistan",
                                  "MENA, Afghanistan \\& Pakistan")
        rows.append(f"{esc(name)} & {r['n']} & {r['positives']} & "
                    f"{f3(r['roc_auc'])} & {f3(r['pr_auc'])} \\\\")
    return "\n".join(rows)


temporal_best = max(ORDER, key=lambda m: L1[m]["temporal"]["pr_auc"])
temporal_val = L1[temporal_best]["temporal"]["pr_auc"]
loco_sel = L1[BEST]["loco"]["pr_auc"]
lift = temporal_val / PREV
mi_rho = A["importance_agreement"]["spearman_mi_vs_shap"]
top_overlap = A["importance_agreement"]["top10_overlap"]
CHAIN_CHANGE = (CH["stage2"]["chained"]["temporal"]["pr_auc"]
                - CH["stage2"]["plain"]["temporal"]["pr_auc"])
S1 = CH["stage1"]["scores"][CH["stage1"]["best"]]


# ------------------------------------------------------------------ #
# Simple-language body (src/simple_body.py); placeholders filled here.
# ------------------------------------------------------------------ #
import simple_body

_rows = IMP.dropna(subset=["shap_rank"]).nsmallest(8, "shap_rank")
TOP_FEATURES = "\n".join(
    f"{i} & {esc(r.feature)} & {r.mean_abs_shap:.3f} & {r.spearman:+.2f} & "
    f"{r.mutual_info:.4f} & {'--' if pandas.isna(r.vif) else f'{r.vif:.0f}'} \\\\"
    for i, r in enumerate(_rows.itertuples(), 1)
)
MI_RHO = f"{A['importance_agreement']['spearman_mi_vs_shap']:+.2f}"
MISS_FAO = f"{MISS['by_source']['FAOSTAT (population)']:.2f}\\%"
MISS_WB = f"{MISS['by_source']['World Bank (socio-economic)']:.2f}\\%"
MISS_NASA = f"{MISS['by_source']['NASA POWER (climate)']:.2f}\\%"
MISS_ALL = f"{MISS['overall_pct']:.2f}\\%"
MISS_MAX = f"{MISS['max_feature_pct']:.1f}\\%"
_vif = A['vif_top10'][0]
VIF_VAL = f"{_vif['vif']:.0f}"
VIF_FEAT = str(_vif['feature']).replace('_', r'\_')
_cv = {c['feature']: c['cramers_v'] for c in A['categorical']}
CRAMV_REGION = f"{_cv.get('region', float('nan')):.3f}"
CRAMV_INCOME = f"{_cv.get('income', float('nan')):.3f}"
PANEL_ROWS = f"{AUD['panel_rows']:,}"
PANEL_COUNTRIES = str(AUD['countries_in_panel'])
RUNTIME = f"{R['runtime_seconds']/60:.1f} minutes"
BEST_PR = f"{temporal_val:.3f}"
LIFT = f"{lift:.0f}"
ECE = f"{R['calibration']['ece']:.3f}"
CHAIN_CHG = f"{CHAIN_CHANGE:+.3f}"


# ---- models table: family + plain-language description + real tuned settings
_DESC = {
    "Logistic Regression": "Adds the inputs with fixed weights and squashes the total into a "
                           "0--1 score. The honest baseline: if the complex models cannot beat "
                           "it, the complexity is not worth it.",
    "Decision Tree": "A flowchart of yes/no questions, for example ``horses $>$ 10,000? then "
                     "last outbreak $<$ 2 years ago?''. Easy to read, but one tree is weak, "
                     "which is part of why we included it.",
    "Random Forest": "500 trees, each trained on a random part of the data, then they vote. "
                     "Fixes the single tree's habit of memorising.",
    "Extra Trees": "Same idea, with splits chosen more randomly. Extra randomness helps when "
                   "examples are scarce, as they are here.",
    "XGBoost": "Trees built one after another, each fixing the previous mistakes. The strongest "
               "standard method for tables like ours.",
    "LightGBM": "Same family as XGBoost with a faster algorithm. A speed comparison, often "
                "slightly better on wide data.",
}

def _params(name: str) -> str:
    p = L1[name]["best_params"]
    if name == "Logistic Regression":
        return f"$C={p.get('C')}$, $\\ell_2$ penalty, balanced class weights"
    if name == "Decision Tree":
        return (f"depth {p.get('max_depth')}, minimum leaf size {p.get('min_samples_leaf')}, "
                f"split criterion {p.get('criterion')}")
    if name in ("Random Forest", "Extra Trees"):
        mf = p.get("max_features")
        mf_txt = "square root of the column count" if mf == "sqrt" else str(mf)
        return (f"depth {p.get('max_depth')}, minimum leaf size {p.get('min_samples_leaf')}, "
                f"features per split {mf_txt}")
    if name == "XGBoost":
        return (f"depth {p.get('max_depth')}, "
                f"regularisation $\\lambda={p.get('reg_lambda')}$, "
                f"minimum child weight {p.get('min_child_weight')}")
    return (f"leaves {p.get('num_leaves')}, minimum child samples "
            f"{p.get('min_child_samples')}, regularisation $\\lambda={p.get('reg_lambda')}$")

MODELS_TABLE = "\n".join(
    f"{NAME[m]} & {esc(L1[NAME[m]]['family'])} & {_DESC[NAME[m]]}"
    f"\\par\\vspace{{3pt}}{{\\scriptsize Tuned settings: \\emph{{{_params(NAME[m])}}}}} \\\\"
    for m in SEQ
)

RESULTS_TABLE = "\n".join(
    f"{m} & {L1[NAME[m]]['temporal']['pr_auc']:.3f} & "
    f"[{L1[NAME[m]]['temporal']['pr_auc_ci'][0]:.2f}, {L1[NAME[m]]['temporal']['pr_auc_ci'][1]:.2f}] & "
    f"{L1[NAME[m]]['temporal']['roc_auc']:.3f} & {L1[NAME[m]]['loco']['pr_auc']:.3f} & "
    f"{L1[NAME[m]]['temporal']['precision']:.2f} & {L1[NAME[m]]['temporal']['recall']:.2f} \\\\"
    for m in SEQ
)

_AB = ["AS-1 history only", "AS-2 population only", "AS-3 climate only",
       "AS-5 history+population", "AS-6 full (all groups)"]
_PRETTY = {"AS-1 history only": "History only",
           "AS-2 population only": "Animal population only",
           "AS-3 climate only": "Climate only",
           "AS-5 history+population": "History + population",
           "AS-6 full (all groups)": "Everything"}
ABLATION_TABLE = "\n".join(
    f"{_PRETTY[k]} & {AB[k]['n_features']} & {AB[k]['temporal']['pr_auc']:.3f} & "
    f"{AB[k]['loco']['pr_auc']:.3f} \\\\" for k in _AB
)

SUBGROUP_TABLE = "\n".join(
    f"{esc(r['group'].replace('Middle East, North Africa, Afghanistan & Pakistan', 'MENA, Afghanistan and Pakistan'))} & "
    f"{r['n']} & {r['positives']} & {r['roc_auc']:.3f} & {r['pr_auc']:.3f} \\\\"
    for r in R["subgroup"] if r["group_by"] == "region"
)

SIMPLE_BODY = (simple_body.BODY
    .replace(r"\section{Dataset Used}", RW.RELATED_TEX + "\n" + r"\section{Dataset Used}", 1)
    .replace("TOP_FEATURES", TOP_FEATURES)
    .replace("MI_RHO", MI_RHO)
    .replace("MISS_FAO", MISS_FAO)
    .replace("MISS_WB", MISS_WB)
    .replace("MISS_NASA", MISS_NASA)
    .replace("MISS_ALL", MISS_ALL)
    .replace("MISS_MAX", MISS_MAX)
    .replace("VIF_VAL", VIF_VAL)
    .replace("VIF_FEAT", VIF_FEAT)
    .replace("CRAMV_REGION", CRAMV_REGION)
    .replace("CRAMV_INCOME", CRAMV_INCOME)
    .replace("PANEL_ROWS", PANEL_ROWS)
    .replace("PANEL_COUNTRIES", PANEL_COUNTRIES)
    .replace("RUNTIME", RUNTIME)
    .replace("BEST_PR", BEST_PR)
    .replace("LIFT", LIFT)
    .replace("ECE", ECE)
    .replace("CHAIN_CHANGE", CHAIN_CHG)
    .replace("RESULTS_TABLE", RESULTS_TABLE)
    .replace("ABLATION_TABLE", ABLATION_TABLE)
    .replace("SUBGROUP_TABLE", SUBGROUP_TABLE)
    .replace("MODELS_TABLE", MODELS_TABLE)
    .replace("FIGURE_ALGORITHMS", DG.ALGORITHMS)
    .replace("FIGURE_EVALFLOW", DG.EVALUATION)
    .replace("FIGURE_TRAINFLOW", DG.TRAINING)
    .replace("FIGURE_SHAP", DG.SHAP))

OUT.joinpath("diagstyles.tex").write_text(DG.STYLES, encoding="utf-8")

TEX = rf"""\documentclass[10pt]{{article}}
\usepackage[margin=0.85in]{{geometry}}
\usepackage{{amsmath}}
\usepackage{{booktabs}}
\usepackage{{array}}
\usepackage{{graphicx}}
\usepackage{{float}}
\usepackage{{multicol}}
\usepackage{{xcolor}}
\usepackage{{tikz}}
\usepackage{{hyperref}}
\hypersetup{{colorlinks=true,linkcolor=blue!45!black,urlcolor=blue!45!black,
  pdftitle={{Predicting Glanders Disease Across a Lifestyle or Geographical Area}},
  pdfauthor={{GlandersWatch Project Team}},
  pdfsubject={{Chained multi-level machine-learning evaluation}}}}
\usetikzlibrary{{shapes.geometric,arrows.meta,positioning,fit,backgrounds,calc,decorations.pathreplacing}}
\graphicspath{{{{../figures/}}}}
\setlength{{\parskip}}{{0.28em}}
\raggedbottom
\sloppy

\title{{\textbf{{Predicting Glanders Disease Across a Lifestyle or Geographical Area}}\\[0.3em]
\large Chained Multi-Level Machine Learning on Four Unused Datasets}}
\author{{GlandersWatch Project Team}}
\date{{\today}}

\begin{{document}}
\input{{diagstyles.tex}}
\maketitle

\noindent
\textbf{{What this project does, in short.}} Glanders is a dangerous bacterial disease of
horses and donkeys. We asked one question: can we predict, using only public data,
which countries will report glanders next year?

We combined four data sources that had never been used for this disease: published
research papers, farm animal counts, World Bank statistics, and NASA climate records.
We then trained six machine learning models and tested them on future years and on
countries the models had never seen.

The result is a working early-warning model. It ranks likely countries about ten times
better than random guessing, and its stated probabilities turned out to be trustworthy.
Warning only about 6\% of the world each year would catch roughly half of all reported
outbreaks. The honest limitations are that the model works less well in countries it has
not seen, and that it largely learns \emph{{which countries report}} disease rather than
\emph{{where}} disease is. Both points are discussed openly in Section~9.

% =====================================================================
{SIMPLE_BODY}

{RW.bibliography_tex()}
\end{{document}}
"""

OUT.joinpath("GlandersWatch_Simple.tex").write_text(TEX, encoding="utf-8")
print(f"wrote report/GlandersWatch_Simple.tex ({len(TEX):,} chars)")
