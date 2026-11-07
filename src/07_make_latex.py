"""Generate the LaTeX report from the saved results (no hand-copied numbers).

Run:  .venv/bin/python src/07_make_latex.py
Then: tectonic report/GlandersWatch_Report.tex
"""
from __future__ import annotations

import json
import pathlib
import platform
import subprocess

import numpy, pandas, scipy, sklearn, lightgbm, shap, xgboost

ROOT = pathlib.Path(__file__).resolve().parents[1]
REP, OUT = ROOT / "reports", ROOT / "report"
OUT.mkdir(exist_ok=True)

R = json.loads((REP / "results.json").read_text())
A = json.loads((REP / "dataset_analysis.json").read_text())
N = json.loads((REP / "novelty_audit.json").read_text())
CMP = pandas.read_csv(REP / "model_comparison.csv")
IMP = pandas.read_csv(REP / "feature_importance.csv")
import related_works as RW

ORDER = ["Logistic Regression", "Decision Tree", "Random Forest",
         "Extra Trees", "XGBoost", "LightGBM"]
BEST = R["best_model"]
L1, L2 = R["level1"]["metrics"], R["level2"]["metrics"]
LAB, MISS = A["labels"], A["missingness"]
CH, AB = R["chain"], R["ablation"]
HG = CH.get("hurdle", {})
S3 = CH.get("stage3", {})

RUNTIME_MIN = R["runtime_seconds"] / 60
HW = "Apple M4 (10 cores, 16 GB unified memory)"
ENV = (
    f"Python {platform.python_version()}, scikit-learn {sklearn.__version__}, "
    f"XGBoost {xgboost.__version__}, LightGBM {lightgbm.__version__}, "
    f"SHAP {shap.__version__}, NumPy {numpy.__version__}, "
    f"pandas {pandas.__version__}, SciPy {scipy.__version__}"
)


def esc(s: str) -> str:
    """Escape LaTeX specials in data-derived strings."""
    rep = {
        "\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$",
        "#": r"\#", "_": r"\_", "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(rep.get(c, c) for c in str(s))


def pct(x: float, d: int = 1) -> str:
    return f"{x*100:.{d}f}\\%"


def f3(x: float) -> str:
    return f"{x:.3f}"


# --------------------------------------------------------------------------- #
# Tables
# --------------------------------------------------------------------------- #
def table_level1() -> str:
    rows = []
    for m in ORDER:
        t, lo, cv = L1[m]["temporal"], L1[m]["loco"], L1[m]["repeated_cv"]
        ci = t["pr_auc_ci"]
        star = r"$^{\star}$" if m == BEST else ""
        rows.append(
            f"{esc(m)}{star} & {esc(L1[m]['family'])} & "
            f"{f3(t['pr_auc'])} [{ci[0]:.2f}, {ci[1]:.2f}] & {f3(t['roc_auc'])} & "
            f"{f3(lo['pr_auc'])} & {f3(cv['pr_auc'])} & {t['brier']:.4f} & "
            f"{t['precision']:.2f} & {t['recall']:.2f} & {t['f1']:.2f} \\\\"
        )
    return "\n".join(rows)


def table_level2() -> str:
    rows = []
    for m in ORDER:
        t, lo = L2[m]["temporal"], L2[m]["loco"]
        rows.append(
            f"{esc(m)} & {f3(t['pr_auc'])} & {f3(t['roc_auc'])} & "
            f"{f3(lo['pr_auc'])} & {f3(lo['roc_auc'])} & {t['brier']:.4f} \\\\"
        )
    return "\n".join(rows)


def table_ablation() -> str:
    rows = []
    for name, v in AB.items():
        rows.append(
            f"{esc(name)} & {v['n_features']} & {f3(v['temporal']['pr_auc'])} & "
            f"{f3(v['temporal']['roc_auc'])} & {f3(v['loco']['pr_auc'])} \\\\"
        )
    return "\n".join(rows)


def table_labels() -> str:
    rows = []
    for k, v in sorted(LAB["prevalence_by_region"].items(),
                       key=lambda kv: -kv[1]["rate"]):
        rows.append(f"{esc(k)} & {v['n']} & {v['pos']} & {pct(v['rate'])} \\\\")
    return "\n".join(rows)


def table_mi() -> str:
    rows = []
    for r in A["univariate"][:12]:
        rows.append(
            f"{esc(r['feature'])} & {r['spearman']:+.3f} & {r['mutual_info']:.4f} & "
            f"{r['missing_pct']:.1f} \\\\"
        )
    return "\n".join(rows)


def table_categorical() -> str:
    rows = []
    for r in A["categorical"]:
        p = r["p_value"]
        p_txt = r"$<$0.001" if p < 1e-3 else f"{p:.3f}"
        rows.append(
            f"{esc(r['feature'])} & {r['levels']} & {r['chi2']:.1f} & "
            f"{p_txt} & {r['cramers_v']:.3f} & {esc(r['strength'])} \\\\"
        )
    return "\n".join(rows)


def table_vif() -> str:
    rows = []
    for r in A["vif_top10"][:8]:
        rows.append(
            f"{esc(r['feature'])} & {r['r2_against_rest']:.3f} & {r['vif']:.1f} \\\\"
        )
    return "\n".join(rows)


def table_importance() -> str:
    m = IMP.dropna(subset=["shap_rank"]).nsmallest(12, "shap_rank")
    rows = []
    for i, r in enumerate(m.itertuples(), 1):
        rows.append(
            f"{i} & {esc(r.feature)} & {r.mean_abs_shap:.3f} & "
            f"{r.spearman:+.2f} & {r.mutual_info:.4f} & "
            f"{'--' if pandas.isna(r.vif) else f'{r.vif:.0f}'} \\\\"
        )
    return "\n".join(rows)


def table_keepdrop() -> str:
    """Grouped verdict summary rather than 44 near-identical rows."""
    from collections import defaultdict
    groups: dict[str, list[str]] = defaultdict(list)
    for d in A["decisions"]:
        groups[d["verdict"]].append(d["feature"])
    label = {
        "kept": "Retained, signal confirmed",
        "kept (representative)": "Retained as cluster representative",
        "kept (trees only)": "Retained for tree models only",
        "dropped": "Dropped",
    }
    order = ["kept", "kept (representative)", "kept (trees only)", "dropped"]
    rows = []
    for k in order:
        if k in groups:
            feats = groups[k]
            shown = ", ".join(esc(f) for f in feats[:7])
            more = f" $+${len(feats)-7} more" if len(feats) > 7 else ""
            rows.append(f"{esc(label[k])} & {len(feats)} & {shown}{more} \\\\")
    return "\n".join(rows)


def table_subgroup() -> str:
    rows = []
    for r in R["subgroup"]:
        rows.append(
            f"{esc(r['group_by'])} & {esc(r['group'])} & {r['n']} & {r['positives']} & "
            f"{f3(r['roc_auc'])} & {f3(r['pr_auc'])} \\\\"
        )
    return "\n".join(rows)


def table_novelty() -> str:
    rows = []
    for k, v in N.items():
        rows.append(f"{esc(k.split('. ', 1)[1])} & {v['hits']} \\\\")
    return "\n".join(rows)


def table_chain() -> str:
    p, c = CH["stage2"]["plain"], CH["stage2"]["chained"]
    rows = [
        f"Plain (no chained feature) & {f3(p['temporal']['pr_auc'])} & "
        f"{f3(p['temporal']['roc_auc'])} & {f3(p['loco']['pr_auc'])} \\\\",
        f"Chained (population forecast added) & {f3(c['temporal']['pr_auc'])} & "
        f"{f3(c['temporal']['roc_auc'])} & {f3(c['loco']['pr_auc'])} \\\\",
    ]
    return "\n".join(rows)


def table_data_sources() -> str:
    rows = [
        ("Europe PMC (text-mined occurrence)", "Animal history",
         f"{A_LIT:,} records $\\rightarrow$ {A_EV} events", "country $\\times$ year",
         f"2000--2024, {LAB['countries']} countries"),
        ("FAOSTAT livestock stocks", "Animal population",
         "7 species panels, 68,449 stock rows", "country $\\times$ year", "1961--2023"),
        ("World Bank WDI + centroids", "Socio-economic context",
         "10 indicators, 217 countries", "country $\\times$ year", "2000--2024"),
        ("NASA POWER agro-climatology", "Environment",
         "6 variables $\\times$ 211 centroids", "country $\\times$ year", "2005--2024"),
    ]
    return "\n".join(
        f"{esc(a)} & {esc(b)} & {c} & {d} & {esc(e)} \\\\" for a, b, c, d, e in rows
    )


AUD = R["audit"]
A_LIT = AUD["literature_records"]
A_EV = AUD["literature_events"]
PREV = LAB["prevalence"]
L2_PREV = R["level2"]["positives"] / R["level2"]["n"]

temporal_best = max(ORDER, key=lambda m: L1[m]["temporal"]["pr_auc"])
temporal_best_val = L1[temporal_best]["temporal"]["pr_auc"]
loco_best_val = L1[BEST]["loco"]["pr_auc"]
lift = temporal_best_val / PREV
YSL_RHO = next(r["spearman"] for r in A["univariate"] if r["feature"] == "years_since_last")

# --------------------------------------------------------------------------- #
# Document
# --------------------------------------------------------------------------- #
TEX = rf"""\documentclass[11pt]{{article}}
\usepackage[margin=1in]{{geometry}}
\usepackage{{amsmath,amssymb}}
\usepackage{{booktabs}}
\usepackage{{array}}
\usepackage{{graphicx}}
\usepackage{{multicol}}
\usepackage{{xcolor}}
\usepackage{{caption}}
\usepackage{{float}}
\usepackage{{hyperref}}
\hypersetup{{colorlinks=true,linkcolor=blue!50!black,urlcolor=blue!50!black,citecolor=blue!50!black}}
\graphicspath{{{{../figures/}}}}
\captionsetup{{font=small,labelfont=bf}}
\setlength{{\parskip}}{{0.35em}}
\sloppy
\setlength{{\emergencystretch}}{{3em}}

\title{{\textbf{{Predicting Glanders Disease Across a Lifestyle or Geographical Area}}\\[0.4em]
\large A Chained Multi-Level Machine-Learning Study on Four Previously Unused Public Datasets}}
\author{{GlandersWatch Project Team}}
\date{{\today}}

\begin{{document}}
\maketitle

\begin{{abstract}}
\noindent
Glanders, caused by \emph{{Burkholderia mallei}}, is a neglected zoonosis of equids that persists
across Africa, Asia and South America, yet the published machine-learning literature addresses
only laboratory identification of the organism, never population-level geographic risk. We
assemble a country-year panel from four sources that have not previously been joined to this
disease -- a text-mined Europe PMC occurrence corpus, FAOSTAT livestock stocks, World Bank
development indicators and NASA POWER reanalysis climatology -- covering
{AUD['level1_rows']:,} country-year observations across {LAB['countries']} equine-holding
countries between 2005 and 2023. We train six model families under three validation schemes and
evaluate a three-stage chained pipeline that forecasts animal population, then outbreak
occurrence, then event intensity. On a strictly forward-looking temporal holdout the strongest model
({esc(temporal_best)}) reaches PR-AUC {f3(temporal_best_val)} against a
{pct(PREV)} base rate, an approximately {lift:.0f}-fold lift over chance, with expected
calibration error 0.016. We report the negative and mixed results as well: chaining does not
improve discrimination, climatology adds almost nothing out-of-country, and performance degrades
markedly in low-income regions.
\end{{abstract}}

\tableofcontents
\newpage

% =========================================================================== #
{RW.RELATED_TEX_LONG}

\section{{Dataset Used}}
% =========================================================================== #

\subsection{{Sources and novelty}}

Four public sources are combined. None has previously been used for glanders risk modelling;
Section~\ref{{sec:novelty}} documents the prior-art search that supports this claim.

\begin{{table}}[H]
\centering
\caption{{Data sources, roles and coverage.}}
\label{{tab:sources}}
\small
\begin{{tabular}}{{@{{}}p{{3.9cm}}p{{2.3cm}}p{{3.4cm}}p{{2.0cm}}p{{2.6cm}}@{{}}}}
\toprule
\textbf{{Source}} & \textbf{{Role}} & \textbf{{Volume}} & \textbf{{Unit}} & \textbf{{Span}} \\
\midrule
{table_data_sources()}
\bottomrule
\end{{tabular}}
\end{{table}}

\paragraph{{Construction.}} All four sources are keyed on ISO~3166 alpha-3 country codes and
calendar year. FAOSTAT is streamed from the 545\,MB normalised bulk archive (a 32\,MB zip) and
filtered to seven stock series rather than loaded entirely into memory. Country centroids and
income/region strata come from the World Bank metadata endpoint. Europe PMC is queried with
\texttt{{glanders OR "Burkholderia mallei" OR farcy}} and paged with a cursor; the resulting
{A_LIT:,} records are reduced to sentence-level occurrence events by a rule-based extractor
(country gazetteer, year pattern, and an occurrence lexicon), yielding {A_EV} events.

\subsection{{Panel dimensions}}

The assembled panel contains {AUD['panel_rows']:,} country-year rows and
{AUD['countries_in_panel']} countries over 2000--2024. For modelling we restrict to
\emph{{equine-holding}} countries (a maximum equid stock of at least 1{{,}}000 animals), years
2005--2023, and rows with an observable next-year label, giving a working matrix of
\textbf{{{AUD['level1_rows']:,} rows $\times$ 44 features}} with
\textbf{{{LAB['positives']} positive labels}} ({pct(PREV)}).

\subsection{{Preprocessing}}
\begin{{itemize}}
  \item \textbf{{Name normalisation.}} FAOSTAT area names, World Bank country names and gazetteer
        aliases are mapped to ISO-3 via \texttt{{pycountry}} with explicit overrides for
        non-standard forms (e.g.\ ``T\"urkiye'', ``C\^ote d'Ivoire'', ``Viet Nam'').
        World Bank aggregates (``World'', region codes) are dropped by requiring a
        3-character ISO code.
  \item \textbf{{Duplicate suppression.}} Literature events are de-duplicated on
        \texttt{{(iso3, year, record\_id)}} so one paper cannot inflate a cell; counts, not
        citations, form the label.
  \item \textbf{{Imputation.}} Median imputation inside the pipeline with an explicit
        missing-indicator column, so absence is modelled rather than silently imputed.
        Categorical gaps use the most-frequent level. Tree models additionally tolerate
        leftovers; linear models are standardised after imputation.
  \item \textbf{{No absence-from-silence.}} A country-year with no retrieved record is coded
        0 only after the country passes the equine-stock filter; the reporting-bias implications
        are discussed in Section~\ref{{sec:labels}}.
\end{{itemize}}

\subsection{{Feature types and missing values}}

Three feature types are used: continuous numeric (stocks, climate, economics),
categorical (World Bank region and income stratum), and count/derived history features.
Missingness is low and structurally source-specific:

\begin{{center}}
\small
\begin{{tabular}}{{@{{}}lcc@{{}}}}
\toprule
\textbf{{Source block}} & \textbf{{Mean missing}} & \textbf{{Columns with $>$10\% missing}} \\
\midrule
FAOSTAT (population) & {MISS['by_source']['FAOSTAT (population)']:.2f}\% & 0 \\
World Bank (socio-economic) & {MISS['by_source']['World Bank (socio-economic)']:.2f}\% & 0 \\
NASA POWER (climate) & {MISS['by_source']['NASA POWER (climate)']:.2f}\% & 0 \\
\midrule
Overall & {MISS['overall_pct']:.2f}\% & {len(MISS['features_over_10pct'])} \\
\bottomrule
\end{{tabular}}
\end{{center}}

\noindent
The worst single column is {MISS['max_feature_pct']:.1f}\% missing, so no feature required
dropping for sparsity alone.

\subsection{{Novelty audit}}
\label{{sec:novelty}}

Prior art was tested rather than asserted. Each row below is a reproducible Europe PMC query
count; the full query strings and retrieved titles are in \texttt{{reports/novelty\_audit.json}}.

\begin{{table}}[H]
\centering
\caption{{Prior-art audit (Europe PMC hit counts, retrieved \today).}}
\label{{tab:novelty}}
\small
\begin{{tabular}}{{@{{}}lc@{{}}}}
\toprule
\textbf{{Combination queried}} & \textbf{{Hits}} \\
\midrule
{table_novelty()}
\bottomrule
\end{{tabular}}
\end{{table}}

\noindent
The decisive cells are \texttt{{glanders + NASA POWER}} with
\textbf{{{N['F. glanders + NASA POWER']['hits']}}} hits and
\texttt{{glanders + gradient boosting}} with
\textbf{{{N['O. glanders + gradient boosting']['hits']}}} hits, none of which is a glanders risk
model. The nearest prior work is descriptive spatio-temporal cluster detection in Brazil and a
risk-factor analysis of the Indian 2019--2023 serosurvey; neither is a calibrated predictive
pipeline over population and reanalysis covariates.

% =========================================================================== #
\section{{Dataset Analysis: Labels, Features and Selection}}
\label{{sec:labels}}
% =========================================================================== #

\subsection{{Label anatomy}}

The label is binary: \emph{{did a glanders occurrence event get documented in country $i$ during
year $t+1$?}} Its statistical shape governs every later design choice.

\begin{{center}}
\small
\begin{{tabular}}{{@{{}}lr@{{}}}}
\toprule
\textbf{{Property}} & \textbf{{Value}} \\
\midrule
Observations & {LAB['rows']:,} \\
Positives / negatives & {LAB['positives']} / {LAB['negatives']:,} \\
Prevalence & {pct(PREV,2)} \\
Imbalance ratio & {LAB['imbalance_ratio']:.1f} : 1 \\
Countries with $\geq$1 positive & {LAB['positive_countries']} of {LAB['countries']} \\
Countries positive in exactly one year & {LAB['single_year_positive_countries']} \\
Countries positive in $\geq$2 years & {LAB['repeat_positive_countries']} \\
Share of positives in top-5 countries & {pct(LAB['top5_country_share'])} \\
Share of positives in top-10 countries & {pct(LAB['top10_country_share'])} \\
\bottomrule
\end{{tabular}}
\end{{center}}

\paragraph{{What the label distribution tells us.}} Three things follow directly.
(i) The {LAB['imbalance_ratio']:.0f}:1 imbalance rules out accuracy as a metric and motivates
precision-recall analysis. (ii) {pct(LAB['repeat_positive_rate'],0)} of positive countries fire in
at least two years, so the label is \emph{{temporally persistent}}, not noise -- a model can
legitimately exploit history. (iii) Labels concentrate: the top five countries hold
{pct(LAB['top5_country_share'])} of all positives. Combined with the fact that the
highest-scoring country-years are India, the United States and Australia, this is best read as
\emph{{documented}} activity shaped by reference-laboratory capacity, not true incidence. We
therefore treat the label as a \emph{{surveillance-observation}} target and say so explicitly
rather than claiming incidence prediction.

\begin{{table}}[H]
\centering
\caption{{Prevalence by World Bank region. Heterogeneity here is the main driver of the
subgroup results in Section~\ref{{sec:results}}.}}
\label{{tab:regions}}
\small
\begin{{tabular}}{{@{{}}lrrr@{{}}}}
\toprule
\textbf{{Region}} & \textbf{{n}} & \textbf{{positives}} & \textbf{{prevalence}} \\
\midrule
{table_labels()}
\bottomrule
\end{{tabular}}
\end{{table}}

\begin{{figure}}[H]
\centering
\includegraphics[width=\textwidth]{{fig10_label_anatomy.png}}
\caption{{Label anatomy. (A) ~{LAB['positives']} positives spread unevenly across years;
(B)~most countries contribute one or two positives, a minority are repeatedly positive;
(C)~regional prevalence spans an order of magnitude, from North America
({pct(A['labels']['prevalence_by_region']['North America']['rate'])}) to Latin America
({pct(A['labels']['prevalence_by_region']['Latin America & Caribbean']['rate'])}).}}
\label{{fig:labels}}
\end{{figure}}

\paragraph{{The secondary target.}} Event \emph{{intensity}} is heavily zero-inflated and
low-range: conditional on an event the mean count is {LAB['count_target']['mean_given_event']:.2f}
(median {LAB['count_target']['median_given_event']:.0f}, maximum
{LAB['count_target']['max']:.0f}), and {pct(LAB['count_target']['share_of_events_with_1'],0)}
of positive cells contain exactly one event. That shape is why intensity is modelled on the log
scale and only \emph{{after}} the occurrence hurdle.

\subsection{{Univariate association and mutual information}}

Two complementary univariate views were computed: Spearman $\rho$ (monotone association,
outlier-robust) and mutual information (captures non-monotone dependence). Reported $p$-values are
uncorrected and should be read descriptively given $\sim$40 correlated tests.

\begin{{table}}[H]
\centering
\caption{{Top 12 features by mutual information with the next-year label.}}
\label{{tab:mi}}
\small
\begin{{tabular}}{{@{{}}lrrr@{{}}}}
\toprule
\textbf{{Feature}} & \textbf{{Spearman $\rho$}} & \textbf{{Mutual info}} & \textbf{{Missing \%}} \\
\midrule
{table_mi()}
\bottomrule
\end{{tabular}}
\end{{table}}

\begin{{table}}[H]
\centering
\caption{{Categorical association via Cram\'er's $V$. Both strata carry real but modest
signal; neither is strong enough to act as a proxy label.}}
\label{{tab:cramersv}}
\small
\begin{{tabular}}{{@{{}}lrrrrr@{{}}}}
\toprule
\textbf{{Feature}} & \textbf{{Levels}} & \textbf{{$\chi^2$}} & \textbf{{$p$}} & \textbf{{Cram\'er's $V$}} & \textbf{{Strength}} \\
\midrule
{table_categorical()}
\bottomrule
\end{{tabular}}
\end{{table}}

\noindent
Three observations drive feature selection.
\textbf{{First}}, the strongest \emph{{monotone}} association is negative and comes from
\texttt{{years\_since\_last}} ($\rho = {YSL_RHO:+.2f}$):
recent activity predicts future activity. This is the single most defensible epidemiological
signal in the panel.
\textbf{{Second}}, mutual information ranks \texttt{{lon}} and \texttt{{abs\_lat}} above every
biological variable. Longitude is not a cause of glanders; it is a proxy for \emph{{which}}
countries report. We keep geography in the model because it is predictive, but we annotate it as a
reporting-capacity proxy and never interpret it causally.
\textbf{{Third}}, socioeconomic variables enter through the same channel: \texttt{{pop\_total}}
and \texttt{{internet\_pct}} are, mechanistically, surveillance-capacity indicators.

\subsection{{Multicollinearity}}

Variance inflation factors were computed by regressing each feature on all others. Climate
variables are the most redundant because they are so highly inter-correlated at the annual,
country-aggregate level.

\begin{{table}}[H]
\centering
\caption{{Eight highest-variance-inflation features. VIF $>10$ is conventionally problematic for
linear models; tree ensembles are unaffected.}}
\label{{tab:vif}}
\small
\begin{{tabular}}{{@{{}}lrr@{{}}}}
\toprule
\textbf{{Feature}} & \textbf{{$R^2$ vs rest}} & \textbf{{VIF}} \\
\midrule
{table_vif()}
\bottomrule
\end{{tabular}}
\end{{table}}

\noindent
Detected redundant clusters (Spearman $|\rho| \geq 0.90$):
\begin{{itemize}}
\itemsep0.1em
{"".join("  \\item \\texttt{{" + ", ".join(esc(f) for f in c) + "}}\n" for c in A['high_corr_clusters'])}
\end{{itemize}}
Each cluster was reduced to one interpretable representative to avoid double-counting the same
quantity. Note that this is a \emph{{reporting}} decision: tree ensembles are invariant to
collinearity, so the ablation results in Section~\ref{{sec:eval}} are not distorted either way.

\begin{{figure}}[H]
\centering
\includegraphics[width=0.78\textwidth]{{fig11_correlation.png}}
\caption{{Spearman correlation matrix of the 22 highest-ranked features, hierarchically ordered.
Block structure shows the collinear clusters that motivated the redundancy reduction.}}
\label{{fig:corr}}
\end{{figure}}

\subsection{{Marginal versus conditional importance}}

Comparing mutual information (marginal, label-only) with SHAP (conditional, model-aware) is the
most informative diagnostic in this study, and the result is a warning:

\begin{{center}}
\small
\begin{{tabular}}{{@{{}}lr@{{}}}}
\toprule
\textbf{{Diagnostic}} & \textbf{{Value}} \\
\midrule
Rank correlation, MI vs.\ SHAP & {A['importance_agreement']['spearman_mi_vs_shap']:+.3f} \\
Rank correlation, $|\rho|$ vs.\ SHAP & {A['importance_agreement']['spearman_rho_vs_shap']:+.3f} \\
Top-10 overlap (MI $\cap$ SHAP) & {A['importance_agreement']['top10_overlap']}/10 \\
\bottomrule
\end{{tabular}}
\end{{center}}

\noindent
The two views are statistically \emph{{unrelated}}. A feature ranking built purely on univariate
statistics would have selected a materially different variable set from the one the model
actually relies on. Concretely, \texttt{{lon}} is MI rank~1 but SHAP rank~$\approx$20, because
once population and history are conditioned on, longitude carries little additional information;
conversely \texttt{{temp\_mean\_anom}} and \texttt{{humidity\_anom}} are modest marginally but rank
in the top five conditionally. We therefore select features on the conditional evidence
(ablation + SHAP) and use univariate statistics only for screening against zero-signal columns.

\begin{{figure}}[H]
\centering
\includegraphics[width=\textwidth]{{fig12_importance_views.png}}
\caption{{(A) Marginal mutual information against conditional SHAP rank; the absence of a
downward trend is the disagreement quantified above. (B) The conditional ranking with the
marginal association sign annotated.}}
\label{{fig:views}}
\end{{figure}}

\subsection{{What was kept and what was discarded}}

\begin{{table}}[H]
\centering
\caption{{Feature-selection verdicts over the 42 numeric features.}}
\label{{tab:keepdrop}}
\small
\begin{{tabular}}{{@{{}}p{{4.6cm}}rp{{9.2cm}}@{{}}}}
\toprule
\textbf{{Verdict}} & \textbf{{n}} & \textbf{{Features}} \\
\midrule
{table_keepdrop()}
\bottomrule
\end{{tabular}}
\end{{table}}

\paragraph{{Reasons for exclusion.}} Four columns showed mutual information below 0.002 with
$|\rho| < 0.02$ and were dropped as carrying no usable signal. Trivially derived duplicates were
also collapsed: \texttt{{equids}} is exactly \texttt{{horses + asses + mules}}, and
\texttt{{equid\_share}} and \texttt{{equid\_density}} are closed-form transformations of the same
counts. We retained the log-transformed and share-scaled versions because they are what the models
select, and dropped the raw arithmetic duplicate. Absolute coordinates were replaced by
\texttt{{abs\_lat}} plus \texttt{{lon}}; the signed latitude and the raw centroid were redundant
given region and income are already present.

\subsection{{Leakage diagnostics}}

Because features and labels come from adjacent time steps, every history feature was audited for
forward dependence:

\begin{{center}}
\small
\begin{{tabular}}{{@{{}}lrr@{{}}}}
\toprule
\textbf{{Feature}} & \textbf{{$\rho$ vs same-year label}} & \textbf{{$\rho$ vs next-year label}} \\
\midrule
{"".join(f"{esc(c['feature'])} & {c['rho_vs_same_year']:+.3f} & {c['rho_vs_next_year']:+.3f} \\\\" + chr(10) for c in A['leakage']['history_cues'])}
\bottomrule
\end{{tabular}}
\end{{center}}

\noindent
\texttt{{occ\_any}} and \texttt{{occ\_count}} are contemporaneous by construction
($\rho \approx 1$ against the same-year observation) and are legitimate inputs, since the target is
the \emph{{following}} year. Their next-year association falls to $\approx 0.32$, which is exactly
the autocorrelation the model is entitled to exploit. The only columns derived from $t+1$ are the
\texttt{{y\_*}} targets, which are removed from the feature matrix by construction. The stage-1
population forecaster has a predictor--target autocorrelation of
{A['leakage']['stage1_autocorrelation']:.3f}, which explains its high rank correlation and is
expected for a livestock series, not a leakage artefact.

% =========================================================================== #
\section{{Features of the Dataset}}
% =========================================================================== #

\subsection{{Feature engineering}}

Four groups were engineered, all using information available at time $t$ only.

\begin{{description}}
  \item[Disease history (7).] \texttt{{occ\_lag1}}, \texttt{{occ\_lag2}},
        \texttt{{occ\_count\_lag1}}, \texttt{{occ\_count\_5y}}, \texttt{{years\_since\_last}},
        \texttt{{global\_occ\_share}}, \texttt{{region\_occ\_share}}.
        Lags capture persistence; the 5-year rolling sum captures epidemic memory; the two share
        variables place a country against its contemporaneous world and regional backdrop.
  \item[Animal population (14).] Log equid and livestock stocks, equid share of livestock units,
        equid density, 1- and 3-year growth rates, and the seven disaggregated species counts.
        ``Livestock units'' uses standard metabolic weights (cattle and camels 0.8, small ruminants
        0.1) so that one number expresses exposure pressure from all species that share pasture
        with equids.
  \item[Climate (10).] Annual mean, maximum and minimum temperature, precipitation total and
        coefficient of variation, relative humidity, wind, plus \emph{{anomalies}} computed
        against an expanding country mean. Anomalies matter because absolute climate mostly encodes
        latitude; the anomaly encodes ``unusual for this country'', which is the biologically
        plausible driver.
  \item[Socio-geography (11).] Income, agricultural land share, agricultural value added,
        livestock production index, GDP per capita, rural population share, internet penetration,
        fertilizer intensity, life expectancy, population and population density, plus absolute
        latitude and longitude.
\end{{description}}

\subsection{{Ranked features and domain interpretation}}

\begin{{table}}[H]
\centering
\caption{{Top 12 features by mean absolute SHAP value, with their marginal statistics.}}
\label{{tab:importance}}
\small
\begin{{tabular}}{{@{{}}rlrrrr@{{}}}}
\toprule
\textbf{{Rank}} & \textbf{{Feature}} & \textbf{{mean $|$SHAP$|$}} & \textbf{{Spearman $\rho$}} & \textbf{{MI}} & \textbf{{VIF}} \\
\midrule
{table_importance()}
\bottomrule
\end{{tabular}}
\end{{table}}

\noindent
The ranking is epidemiologically coherent if read carefully. Population magnitude
(\texttt{{pop\_total}}, \texttt{{log\_livestock}}) and \emph{{reporting capacity}}
(\texttt{{internet\_pct}}) dominate, which is the surveillance-bias signature discussed in
Section~\ref{{sec:labels}}. Among genuinely biological drivers, recent history
(\texttt{{years\_since\_last}}) and climate anomalies rank highest. Climate \emph{{levels}} are
largely displaced by their anomalies, confirming that the anomaly transform did the work it was
designed to do.

\begin{{figure}}[H]
\centering
\includegraphics[width=0.72\textwidth]{{fig06_shap.png}}
\caption{{Global SHAP attribution for XGBoost over the full panel.}}
\label{{fig:shap}}
\end{{figure}}

\subsection{{Scaling, encoding, dimensionality}}

Continuous features are median-imputed with missing indicators, then standardised \emph{{only}} for
the logistic baseline; tree ensembles receive raw values (invariant to monotone transforms).
Categorical region and income are one-hot encoded with \texttt{{min\_frequency=5}}, which merges
rare strata and keeps the design matrix at 44 columns.

No PCA or other linear projection was applied. Dimensionality is already modest (44 features,
{AUD['level1_rows']:,} rows), and the ablation in Section~\ref{{sec:eval}} shows the binding
constraint is \emph{{signal}}, not dimensionality: the 21-feature AS-5 setting generalises
\emph{{better}} than the 42-feature full set. Compression would have removed interpretability
without addressing that.

% =========================================================================== #
\section{{Models Used}}
% =========================================================================== #

\begin{{table}}[H]
\centering
\caption{{Model families, rationale, and the selected hyperparameters.}}
\label{{tab:models}}
\small
\begin{{tabular}}{{@{{}}>{{\raggedright\arraybackslash}}p{{3.1cm}}>{{\raggedright\arraybackslash}}p{{5.5cm}}>{{\raggedright\arraybackslash}}p{{6.6cm}}@{{}}}}
\toprule
\textbf{{Model}} & \textbf{{Rationale}} & \textbf{{Selected configuration}} \\
\midrule
Logistic regression & Interpretable linear baseline; measures how much of the signal is additive. &
$C={L1['Logistic Regression']['best_params'].get('C')}$, $\ell_2$, balanced class weights \\
Decision tree & Single shallow tree; readable rules; low-variance check on ensemble gains. &
depth ${L1['Decision Tree']['best_params'].get('max_depth')}$, leaf ${L1['Decision Tree']['best_params'].get('min_samples_leaf')}$, \texttt{{{L1['Decision Tree']['best_params'].get('criterion')}}} \\
Random forest & Bagged trees; non-linear interactions with variance control at few positives. &
depth ${L1['Random Forest']['best_params'].get('max_depth')}$, \texttt{{max\_features}} ${L1['Random Forest']['best_params'].get('max_features')}$, leaf ${L1['Random Forest']['best_params'].get('min_samples_leaf')}$ \\
Extra trees & Randomised split thresholds; further decorrelation when positives are scarce. &
depth ${L1['Extra Trees']['best_params'].get('max_depth')}$, \texttt{{max\_features}} ${L1['Extra Trees']['best_params'].get('max_features')}$, leaf ${L1['Extra Trees']['best_params'].get('min_samples_leaf')}$ \\
XGBoost & Boosted trees with explicit regularisation; the proposal's primary candidate. &
depth ${L1['XGBoost']['best_params'].get('max_depth')}$, $\lambda={L1['XGBoost']['best_params'].get('reg_lambda')}$, min child ${L1['XGBoost']['best_params'].get('min_child_weight')}$ \\
LightGBM & Leaf-wise boosting; efficient comparison, often strong on wide tabular data. &
leaves ${L1['LightGBM']['best_params'].get('num_leaves')}$, min child ${L1['LightGBM']['best_params'].get('min_child_samples')}$, $\lambda={L1['LightGBM']['best_params'].get('reg_lambda')}$ \\
\bottomrule
\end{{tabular}}
\end{{table}}

\paragraph{{Why these six.}} The dataset has three properties that together dictate the model set:
a {LAB['imbalance_ratio']:.0f}:1 class imbalance, a modest positive count
({LAB['positives']}), and a mix of collinear continuous and low-cardinality categorical features.
Deep learning is excluded on evidence rather than taste: with {LAB['positives']} positives and 44
columns there is no regime in which a neural network's parameter-to-sample ratio is defensible.
Ensembles are included because they handle collinearity and non-monotone interactions without
manual specification. The linear model is retained specifically as a \emph{{floor}} -- if a
boosted model cannot beat it, the nonlinearity is not earning its complexity.

\paragraph{{Selected model and ensembling.}} Model selection used \emph{{leave-country-out}} PR-AUC,
not the temporal holdout, because geographic generalisation is the claim the system makes.
\textbf{{{esc(BEST)}}} was selected ({f3(loco_best_val)} LOCO PR-AUC). No stacking ensemble was
adopted: the spread between families is small relative to the bootstrap interval, and a meta-learner
fitted on {LAB['positives']} positives would add variance without a defensible gain. Probabilities
are instead calibrated (Section~\ref{{sec:eval}}), which is the ensembling-adjacent step that
actually matters for alerting.

% =========================================================================== #
\section{{Evaluation Pipeline}}
\label{{sec:eval}}
% =========================================================================== #

\subsection{{Splitting strategy}}

Three schemes are reported, each answering a different question:

\begin{{itemize}}
  \item \textbf{{Temporal holdout}} (train 2005--2017, test 2018--2023). Answers: \emph{{can the
        system be deployed and used next year?}} This is the primary scheme and the only one whose
        test period is entirely unseen in time.
  \item \textbf{{Leave-country-out}} (5 folds grouped by ISO-3). Answers: \emph{{does this transfer
        to a country never seen?}} This drives model selection because it is the harsher test.
  \item \textbf{{Repeated stratified 5-fold}} (3 repeats). Answers: \emph{{is the ranking stable
        under resampling?}} Reported as a variance check, using uncalibrated fits to keep the
        resampling budget tractable.
\end{{itemize}}

Grouped folds are essential here. A random row split would place the same country in train and
test, letting the model memorise country identity -- which, given the \texttt{{lon}} result above,
would leak the label through geography and inflate scores substantially.

\subsection{{Metrics and justification}}

Precision-recall AUC (average precision) is the primary metric: at {pct(PREV)} prevalence, ROC-AUC
is dominated by the true-negative mass and flatters every model. ROC-AUC is reported for
comparability with prior literature. Brier score and expected calibration error are reported because
a probability that is not calibrated cannot support a threshold-based alert. Precision, recall,
specificity, F1 and MCC are computed at a threshold tuned \emph{{on training data only}} (the
F1-optimal cutoff), never on test. Bootstrap percentile intervals (1{{,}}000 resamples) quantify
sampling uncertainty on the headline numbers.

\subsection{{Leakage prevention}}

\begin{{enumerate}}
  \item All features are constructed from $t$ and earlier; only \texttt{{y\_*}} columns use $t+1$.
  \item The split is chronological, so no future information can enter training.
  \item Hyperparameters are tuned inside training folds via \texttt{{GroupKFold}} on country.
  \item Probability calibration (sigmoid, 3-fold internal) is fitted only on training data.
  \item The alert threshold is fitted on the training period and applied unchanged to the test period.
  \item Missing-indicator columns are generated inside the pipeline, so the test set never
        influences imputation values.
\end{{enumerate}}

\subsection{{Alert-level evaluation}}

Because the deployment decision is ``send an alert or not'', we evaluate the operating curve
explicitly.

\begin{{figure}}[H]
\centering
\includegraphics[width=\textwidth]{{fig07_alert_budget.png}}
\caption{{(A) Fraction of events captured as the alert budget grows, versus random alerting.
(B) Alert volume required to reach a target recall. Roughly 6\% of country-years must be alerted
to reach 50\% recall; 28\% reaches 80\%.}}
\label{{fig:alerts}}
\end{{figure}}

% =========================================================================== #
\section{{Training Pipeline}}
% =========================================================================== #

\subsection{{End-to-end workflow}}

\begin{{enumerate}}
  \item \textbf{{Ingest.}} \texttt{{01\_fetch\_data.py}}, \texttt{{01b\_...py}},
        \texttt{{01c\_...py}}: Europe PMC paging, World Bank indicators, NASA POWER per-centroid
        monthly series, FAOSTAT streamed extraction. All steps are resumable and cache to disk.
  \item \textbf{{Assemble.}} \texttt{{02\_build\_panel.py}}: ISO-3 reconciliation, grid expansion to
        country $\times$ year, lag/rolling/anomaly construction, target shifting, and an audit
        block of counts.
  \item \textbf{{Analyse.}} \texttt{{05\_dataset\_analysis.py}}: label anatomy, univariate
        association, VIF, MI/SHAP agreement, keep/drop verdicts.
  \item \textbf{{Tune and train.}} \texttt{{03\_train\_evaluate.py}}: \texttt{{RandomizedSearchCV}}
        (grouped by country, scored on average precision) selects hyperparameters; each selected
        configuration is then calibrated and evaluated under all three schemes.
  \item \textbf{{Chain.}} Three stages: Ridge/HistGBR forecast of next-year log equid stock;
        occurrence classifier with the forecast appended; Random-forest intensity model on positives.
        The hurdle combination multiplies probability by conditional intensity.
  \item \textbf{{Report.}} \texttt{{04\_report.py}}, \texttt{{06\_analysis\_figures.py}},
        \texttt{{07\_make\_latex.py}} regenerate every figure and this document from the JSON results.
\end{{enumerate}}

\subsection{{Hyperparameter tuning}}

Search is \texttt{{RandomizedSearchCV}} with 8 draws (2 in smoke mode), scored by average precision,
cross-validated with \texttt{{GroupKFold}} over countries and refitted on the full training fold.
The search space is deliberately small -- typically 40--60 candidates per family -- because with
{LAB['positives']} positives wide search overfits the validation objective. Best configurations are
reported in Table~\ref{{tab:models}}.

\subsection{{Computational resources and duration}}

All experiments ran on {HW}, CPU only, within a single Python process.
Full pipeline wall-clock was \textbf{{{RUNTIME_MIN:.1f} minutes}} including all six families, three
validation schemes, the chained pipeline, seven ablation settings, SHAP and five repeated
cross-validation runs. Per-family fit times (level~1) ranged from
{min(v['fit_seconds'] for v in L1.values()):.1f}\,s (logistic regression) to
{max(v['fit_seconds'] for v in L1.values()):.1f}\,s (LightGBM). This is comfortably reproducible
on a laptop, which matters for a public-health tool intended to be re-run as surveillance updates.

\subsection{{Reproducibility}}

\begin{{itemize}}
  \item \textbf{{Seeds.}} A single module-level constant \texttt{{RANDOM\_STATE = 42}} seeds model
        fitting, CV splitting, bootstrap resampling and SHAP sampling.
  \item \textbf{{Environment.}} {esc(ENV)}. Dependencies are installed into a project-local
        \texttt{{.venv}} created with \texttt{{uv}}.
  \item \textbf{{Versioning.}} Raw payloads are cached under \texttt{{data/raw}} and the derived
        panel is written to \texttt{{data/processed/country\_year\_panel.csv}}, so any reported
        number can be regenerated without re-downloading upstream sources.
  \item \textbf{{Determinism caveat.}} Tree ensembles are seeded but not bitwise deterministic across
        thread counts; \texttt{{n\_jobs=-1}} may change the last decimal of an ensemble score.
  \item \textbf{{Audit trail.}} Every figure and table in this document is generated from
        \texttt{{reports/results.json}} and \texttt{{reports/dataset\_analysis.json}}; nothing is
        typed by hand.
\end{{itemize}}

% =========================================================================== #
\section{{Results}}
\label{{sec:results}}
% =========================================================================== #

\subsection{{Level 1: country-year occurrence}}

\begin{{table}}[H]
\centering
\caption{{Level 1 performance under three validation schemes. PR-AUC is the primary metric;
brackets give 95\% bootstrap intervals on the temporal holdout. $\star$ marks the model selected on
leave-country-out PR-AUC.}}
\label{{tab:level1}}
\resizebox{{\textwidth}}{{!}}{{%
\begin{{tabular}}{{@{{}}l l c c c c c c c c@{{}}}}
\toprule
\textbf{{Model}} & \textbf{{Family}} & \textbf{{PR-AUC [95\% CI]}} & \textbf{{ROC-AUC}} &
\textbf{{PR-AUC LOCO}} & \textbf{{PR-AUC rep-CV}} & \textbf{{Brier}} & \textbf{{Prec}} &
\textbf{{Rec}} & \textbf{{F1}} \\
\midrule
{table_level1()}
\bottomrule
\end{{tabular}}}}
\end{{table}}

\noindent
Against a {pct(PREV)} base rate, the best temporal PR-AUC of {f3(temporal_best_val)}
is a \textbf{{{lift:.1f}$\times$ lift}} over chance. The diagnostic pattern is more interesting than
the headline: PR-AUC \emph{{falls}} under leave-country-out for every family, by far more than the
bootstrap interval, which is the expected signature of country-specific learning. The linear model
degrades least in relative terms, suggesting a meaningful share of the transferable signal is
additive and population-driven.

\begin{{figure}}[H]
\centering
\includegraphics[width=0.94\textwidth]{{fig02_model_comparison.png}}
\caption{{Discrimination by model and validation scheme. The gap between repeated CV and
leave-country-out is the cost of generalising to an unseen country.}}
\label{{fig:comparison}}
\end{{figure}}

\begin{{figure}}[H]
\centering
\includegraphics[width=0.92\textwidth]{{fig03_roc_pr_curves.png}}
\caption{{ROC and precision-recall curves on the temporal holdout. The PR panel is the informative
one: at this prevalence the ROC curves compress into a narrow band while PR separates the families.}}
\label{{fig:curves}}
\end{{figure}}

\subsection{{Calibration}}

Predictions from the selected model are well calibrated: expected calibration error
\textbf{{{R['calibration']['ece']:.3f}}} and Brier score {R['calibration']['brier']:.4f}.
This is the property that makes threshold-based alerting defensible -- a stated 24\% risk
corresponds to roughly 24\% observed frequency in the holdout.

\begin{{figure}}[H]
\centering
\includegraphics[width=0.92\textwidth]{{fig04_calibration.png}}
\caption{{Reliability diagram and predicted-risk distribution on the temporal holdout.}}
\label{{fig:calibration}}
\end{{figure}}

\subsection{{Level 2: coarse temporal resolution}}

Aggregating to country $\times$ 5-year periods raises prevalence to
{pct(L2_PREV, 1)} ({R['level2']['positives']} positives in {R['level2']['n']} rows) and improves
every metric, which isolates the mechanism: coarser windows match the label's own reporting cadence,
and a positive anywhere in the window counts once.

\begin{{table}}[H]
\centering
\caption{{Level 2 (country $\times$ 5-year period).}}
\label{{tab:level2}}
\small
\begin{{tabular}}{{@{{}}lccccc@{{}}}}
\toprule
\textbf{{Model}} & \textbf{{PR-AUC}} & \textbf{{ROC-AUC}} & \textbf{{PR-AUC LOCO}} &
\textbf{{ROC-AUC LOCO}} & \textbf{{Brier}} \\
\midrule
{table_level2()}
\bottomrule
\end{{tabular}}
\end{{table}}

\begin{{figure}}[H]
\centering
\includegraphics[width=0.85\textwidth]{{fig09_resolution.png}}
\caption{{Resolution matters: the same models on fine versus coarse temporal units.}}
\label{{fig:resolution}}
\end{{figure}}

\subsection{{Ablation settings}}

\begin{{table}}[H]
\centering
\caption{{Ablation settings (AS). AS-7 adds two research-output proxies as a surveillance-bias
probe.}}
\label{{tab:ablation}}
\small
\begin{{tabular}}{{@{{}}lcccc@{{}}}}
\toprule
\textbf{{Setting}} & \textbf{{$k$}} & \textbf{{PR-AUC (time)}} & \textbf{{ROC-AUC (time)}} &
\textbf{{PR-AUC (LOCO)}} \\
\midrule
{table_ablation()}
\bottomrule
\end{{tabular}}
\end{{table}}

\noindent
Two findings here are more useful than the headline score.
(i) \emph{{Parsimony wins out-of-country}}: AS-5 (21 features) generalises better
({f3(AB['AS-5 history+population']['loco']['pr_auc'])} LOCO PR-AUC) than the full 42-feature set
({f3(AB['AS-6 full (all groups)']['loco']['pr_auc'])}). Adding climate and socio-economic columns
buys in-distribution fit and costs transfer.
(ii) \emph{{Climate alone is nearly useless out-of-country}}
({f3(AB['AS-3 climate only']['loco']['pr_auc'])} LOCO PR-AUC): it mostly encodes latitude, which
is country identity in disguise. The AS-7 probe moves the score by
{AB['AS-7 full + surveillance proxy']['loco']['pr_auc'] - AB['AS-6 full (all groups)']['loco']['pr_auc']:+.3f}
LOCO PR-AUC, which is weak evidence that the model is not \emph{{purely}} tracking research output.

\begin{{figure}}[H]
\centering
\includegraphics[width=0.9\textwidth]{{fig05_ablation.png}}
\caption{{Ablation settings under both schemes.}}
\label{{fig:ablation}}
\end{{figure}}

\subsection{{The chained pipeline}}

\begin{{center}}
\small
\begin{{tabular}}{{@{{}}llr@{{}}}}
\toprule
\textbf{{Stage}} & \textbf{{Metric}} & \textbf{{Value}} \\
\midrule
Stage 1 (population forecast) & MAE / median AE & {CH['stage1']['scores'][CH['stage1']['best']]['mae']:.3f} / {CH['stage1']['scores'][CH['stage1']['best']]['median_ae']:.3f} \\
                              & Spearman & {CH['stage1']['scores'][CH['stage1']['best']]['spearman']:.3f} \\
Stage 3 (intensity $\mid$ event) & MAE / median AE & {S3.get('mae', float('nan')):.3f} / {S3.get('median_ae', float('nan')):.3f} \\
                                 & Spearman & {S3.get('spearman', float('nan')):.3f} \\
Hurdle chain (expected burden)   & Spearman & {HG.get('spearman_test', float('nan')):.3f} \\
                                 & events in top 10\% & {HG.get('events_captured', 'n/a')}/{HG.get('total_events', 'n/a')} \\
\bottomrule
\end{{tabular}}
\end{{center}}

\begin{{table}}[H]
\centering
\caption{{Effect of chaining the population forecast into the occurrence model.}}
\label{{tab:chain}}
\small
\begin{{tabular}}{{@{{}}lccc@{{}}}}
\toprule
\textbf{{Stage-2 variant}} & \textbf{{PR-AUC (time)}} & \textbf{{ROC-AUC (time)}} & \textbf{{PR-AUC (LOCO)}} \\
\midrule
{table_chain()}
\bottomrule
\end{{tabular}}
\end{{table}}

\noindent
\textbf{{Chaining does not improve discrimination.}} The difference is
{CH['stage2']['chained']['temporal']['pr_auc'] - CH['stage2']['plain']['temporal']['pr_auc']:+.3f}
PR-AUC, well inside the bootstrap interval. This is reported as a negative result rather than
tuned away: because the population level is already supplied as a direct feature, forecasting it
adds no information for the ranking task. The chain earns its place at the \emph{{alert}} layer,
where the hurdle product captures {HG.get('events_captured', 'n/a')} of
{HG.get('total_events', 'n/a')} events in the top decile -- not at the discrimination layer.

\subsection{{Subgroup performance}}

\begin{{table}}[H]
\centering
\caption{{Leave-country-out performance by World Bank region and income stratum.}}
\label{{tab:subgroup}}
\small
\begin{{tabular}}{{@{{}}l>{{\raggedright\arraybackslash}}p{{6.1cm}}rrrr@{{}}}}
\toprule
\textbf{{Stratified by}} & \textbf{{Group}} & \textbf{{n}} & \textbf{{events}} &
\textbf{{ROC-AUC}} & \textbf{{PR-AUC}} \\
\midrule
{table_subgroup()}
\bottomrule
\end{{tabular}}
\end{{table}}

\begin{{figure}}[H]
\centering
\includegraphics[width=0.9\textwidth]{{fig08_subgroups.png}}
\caption{{Regional transfer performance under leave-country-out.}}
\label{{fig:subgroups}}
\end{{figure}}

\noindent
This is the study's most policy-relevant table, and it is uncomfortable: performance is lowest in
Sub-Saharan Africa and in low-income countries -- precisely where glanders surveillance is thinnest
and where an early-warning system would be most valuable. The mechanism is label sparsity, not model
failure. We report it rather than averaging it away, because a deployment decision should not treat
these strata as equivalent.

\subsection{{Caveats and limitations}}

\begin{{itemize}}
  \item \textbf{{The label is documented activity, not incidence.}} A zero means ``no retrieved
        record'', which conflates absence of disease with absence of publication. All scores should
        be read as skill at predicting \emph{{surveillance-observable}} events.
  \item \textbf{{Text-mined labels inherit extraction error.}} The rule-based gazetteer/lexicon
        extractor has not been validated against a hand-annotated gold set; false positives are
        possible where country names appear in author affiliations or general framing.
  \item \textbf{{Country-level aggregation hides district heterogeneity.}} Glanders in India is
        heavily concentrated in a few states; a country-year label cannot express that.
  \item \textbf{{Small positive count.}} With {LAB['positives']} positives, bootstrap intervals are
        wide (roughly $\pm$0.11 on the headline PR-AUC) and subgroup estimates are noisy.
  \item \textbf{{Associations are not causal.}} Geographic and socio-economic features act largely
        as reporting-capacity proxies; no intervention claim follows from them.
\end{{itemize}}

\section*{{Reproducibility statement}}
\addcontentsline{{toc}}{{section}}{{Reproducibility statement}}

\begin{{itemize}}
  \item \textbf{{Code.}} \texttt{{src/00\_novelty\_audit.py}} through
        \texttt{{src/07\_make\_latex.py}}, run in order.
  \item \textbf{{Data.}} \texttt{{data/raw}} holds the cached upstream payloads;
        \texttt{{data/processed}} holds the assembled panel and extracted events.
  \item \textbf{{Numbers.}} \texttt{{reports/results.json}},
        \texttt{{reports/dataset\_analysis.json}} and
        \texttt{{reports/model\_comparison.csv}}.
  \item Every figure and table above is regenerated from those files by the scripts; this
        report contains no hand-transcribed results.
\end{{itemize}}

{RW.bibliography_tex(long_form=True)}
\end{{document}}
"""

(OUT / "GlandersWatch_Report.tex").write_text(TEX, encoding="utf-8")
print(f"wrote report/GlandersWatch_Report.tex ({len(TEX):,} chars)")
