"""Figures + markdown report for the GlandersWatch chained evaluation.

Run:  .venv/bin/python src/04_report.py
"""
from __future__ import annotations

import json
import pathlib

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import precision_recall_curve, roc_curve

ROOT = pathlib.Path(__file__).resolve().parents[1]
REP, FIG, PROC = ROOT / "reports", ROOT / "figures", ROOT / "data" / "processed"
FIG.mkdir(exist_ok=True)

plt.rcParams.update({
    "figure.dpi": 150,
    "font.size": 9,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.alpha": 0.25,
    "axes.titlesize": 10,
    "axes.titleweight": "bold",
    "figure.facecolor": "white",
})

INK = "#1f2933"
BLUE = "#2563eb"
ORANGE = "#ea580c"
TEAL = "#0d9488"
GREY = "#94a3b8"
PALETTE = ["#1f2933", "#2563eb", "#0d9488", "#ea580c", "#7c3aed", "#be123c"]

R = json.loads((REP / "results.json").read_text())
L1 = pd.read_csv(PROC / "country_year_panel.csv")
EV = pd.read_csv(PROC / "literature_events.csv")
COMP = pd.read_csv(REP / "model_comparison.csv")

MODEL_ORDER = ["Logistic Regression", "Decision Tree", "Random Forest",
               "Extra Trees", "XGBoost", "LightGBM"]


def save(fig, name: str) -> None:
    fig.tight_layout()
    fig.savefig(FIG / name, bbox_inches="tight")
    plt.close(fig)
    print("figure:", name)


# --------------------------------------------------------------------------- #
# 1. Dataset coverage / audit
# --------------------------------------------------------------------------- #
def fig_coverage() -> None:
    fig, axes = plt.subplots(1, 2, figsize=(11, 3.8), gridspec_kw={"width_ratios": [1, 1.6]})

    by_year = EV.groupby("year").size().reindex(range(2005, 2025), fill_value=0)
    ax = axes[0]
    ax.bar(by_year.index, by_year.values, color=BLUE, alpha=0.85, width=0.75)
    ax.set_title("A. Literature-mined glanders events by year")
    ax.set_xlabel("event year")
    ax.set_ylabel("events")
    ax.set_xticks(range(2005, 2025, 3))

    top = EV.groupby("iso3").size().sort_values(ascending=False).head(18).index
    mat = (
        EV[EV.iso3.isin(top)]
        .pivot_table(index="iso3", columns="year", values="record_id", aggfunc="count")
        .reindex(top)
        .reindex(columns=range(2005, 2025))
        .fillna(0)
    )
    ax = axes[1]
    im = ax.imshow(np.log1p(mat.values), aspect="auto", cmap="YlGnBu")
    ax.set_yticks(range(len(mat.index)))
    ax.set_yticklabels(mat.index, fontsize=7)
    ax.set_xticks(range(0, 20, 4))
    ax.set_xticklabels(range(2005, 2025, 4))
    ax.set_title("B. Reported activity by country (log events)")
    ax.grid(False)
    fig.colorbar(im, ax=ax, shrink=0.8, label="log(1+events)")
    save(fig, "fig01_dataset_coverage.png")


# --------------------------------------------------------------------------- #
# 2. Model comparison
# --------------------------------------------------------------------------- #
def fig_comparison() -> None:
    metrics = [("pr_auc", "PR-AUC (average precision)"), ("roc_auc", "ROC-AUC")]
    schemes = [("temporal_holdout", "Temporal holdout (2018-23)"),
               ("leave_country_out", "Leave-country-out CV"),
               ("repeated_stratified_cv", "Repeated stratified CV")]
    fig, axes = plt.subplots(len(metrics), 1, figsize=(10, 6.2), sharex=True)
    x = np.arange(len(MODEL_ORDER))
    w = 0.26
    for ax, (metric, label) in zip(axes, metrics):
        for i, (scheme, slabel) in enumerate(schemes):
            sub = COMP[(COMP.level == "L1 country-year") & (COMP.scheme == scheme)
                       & (COMP.metric == metric)]
            vals = [float(sub[sub.model == m].value.iloc[0]) if (sub.model == m).any()
                    else np.nan for m in MODEL_ORDER]
            ax.bar(x + (i - 1) * w, vals, w, label=slabel, color=PALETTE[i], alpha=0.9)
        ax.set_ylabel(label)
        ax.set_ylim(0, 1)
    prev = R["audit"]["level1_prevalence"]
    axes[0].axhline(prev, ls="--", lw=1, color=GREY)
    axes[0].text(len(MODEL_ORDER) - 0.4, prev + 0.02, f"prevalence {prev:.1%}",
                 ha="right", fontsize=7, color=GREY)
    axes[0].legend(ncol=3, fontsize=7, frameon=False, loc="upper left")
    axes[0].set_title("Level 1 (country-year, n=3,078): discrimination by scheme")
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(MODEL_ORDER, rotation=12)
    save(fig, "fig02_model_comparison.png")


# --------------------------------------------------------------------------- #
# 3. ROC / PR curves
# --------------------------------------------------------------------------- #
def fig_curves() -> None:
    fig, axes = plt.subplots(1, 2, figsize=(9.5, 4.1))
    for i, m in enumerate(MODEL_ORDER):
        f = REP / f"pred_L1_{m.replace(' ', '_')}.csv"
        if not f.exists():
            continue
        d = pd.read_csv(f)
        y, p = d.y_true.to_numpy(), d.p_pred.to_numpy()
        fpr, tpr, _ = roc_curve(y, p)
        pr, rc, _ = precision_recall_curve(y, p)
        axes[0].plot(fpr, tpr, color=PALETTE[i], lw=1.6,
                     label=f"{m} ({np.trapezoid(tpr, fpr):.3f})")
        axes[1].plot(rc, pr, color=PALETTE[i], lw=1.6, label=m)
    axes[0].plot([0, 1], [0, 1], ls=":", color=GREY, lw=1)
    axes[0].set_xlabel("false positive rate")
    axes[0].set_ylabel("true positive rate")
    axes[0].set_title("A. ROC - temporal holdout")
    axes[0].legend(fontsize=6.5, frameon=False, loc="lower right")
    axes[1].axhline(R["audit"]["level1_prevalence"], ls="--", lw=1, color=GREY)
    axes[1].set_xlabel("recall")
    axes[1].set_ylabel("precision")
    axes[1].set_title("B. Precision-recall - temporal holdout")
    axes[1].set_xlim(0, 1)
    save(fig, "fig03_roc_pr_curves.png")


# --------------------------------------------------------------------------- #
# 4. Calibration
# --------------------------------------------------------------------------- #
def fig_calibration() -> None:
    cal = R["calibration"]
    rel = pd.DataFrame(cal["reliability"])
    best = cal["model"]
    d = pd.read_csv(REP / f"pred_L1_{best.replace(' ', '_')}.csv")
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.6))
    ax = axes[0]
    ax.plot([0, 1], [0, 1], ls=":", color=GREY)
    ax.plot(rel.mean_pred, rel.observed, "o-", color=BLUE, lw=1.6, ms=5)
    ax.set_xlabel("predicted probability")
    ax.set_ylabel("observed event rate")
    ax.set_title(f"A. Reliability - {best}\nECE={cal['ece']:.3f}, Brier={cal['brier']:.3f}")
    ax = axes[1]
    ax.hist(d.p_pred, bins=25, color=TEAL, alpha=0.75)
    ax.set_yscale("log")
    ax.set_xlabel("predicted probability")
    ax.set_ylabel("country-years (log)")
    ax.set_title("B. Predicted risk distribution (holdout)")
    save(fig, "fig04_calibration.png")


# --------------------------------------------------------------------------- #
# 5. Ablation
# --------------------------------------------------------------------------- #
def fig_ablation() -> None:
    ab = R["ablation"]
    names = list(ab)
    temp = [ab[n]["temporal"]["pr_auc"] for n in names]
    loco = [ab[n]["loco"]["pr_auc"] for n in names]
    fig, ax = plt.subplots(figsize=(8.4, 3.8))
    y = np.arange(len(names))
    ax.barh(y - 0.19, temp, 0.36, color=BLUE, label="temporal holdout")
    ax.barh(y + 0.19, loco, 0.36, color=ORANGE, label="leave-country-out")
    ax.set_yticks(y)
    ax.set_yticklabels(names, fontsize=8)
    ax.invert_yaxis()
    ax.axvline(R["audit"]["level1_prevalence"], ls="--", lw=1, color=GREY)
    ax.set_xlabel("PR-AUC")
    ax.set_title("Ablation settings (XGBoost, fixed parameters)")
    ax.legend(fontsize=7.5, frameon=False, loc="lower right")
    for yi, v in zip(y, temp):
        ax.text(v + 0.008, yi - 0.19, f"{v:.3f}", va="center", fontsize=7)
    for yi, v in zip(y, loco):
        ax.text(v + 0.008, yi + 0.19, f"{v:.3f}", va="center", fontsize=7)
    save(fig, "fig05_ablation.png")


# --------------------------------------------------------------------------- #
# 6. SHAP
# --------------------------------------------------------------------------- #
def fig_shap() -> None:
    rows = R["shap"][:15]
    if not rows:
        return
    fig, ax = plt.subplots(figsize=(7.4, 4.4))
    names = [r["feature"] for r in rows][::-1]
    vals = [r["mean_abs_shap"] for r in rows][::-1]
    ax.barh(names, vals, color=BLUE, alpha=0.85)
    ax.set_xlabel("mean |SHAP| (log-odds)")
    ax.set_title("Global feature attribution - XGBoost, full panel")
    save(fig, "fig06_shap.png")


# --------------------------------------------------------------------------- #
# 7. Alert-level evaluation
# --------------------------------------------------------------------------- #
def fig_alerts() -> None:
    best = "Random Forest"
    d = pd.read_csv(REP / f"pred_L1_{best.replace(' ', '_')}.csv")
    y, p = d.y_true.to_numpy().astype(int), d.p_pred.to_numpy()
    order = np.argsort(-p)
    y_sorted = y[order]
    k = np.arange(1, len(y) + 1)
    frac_alerts = k / len(y)
    frac_events = np.cumsum(y_sorted) / y.sum()

    targets = np.linspace(0.05, 1.0, 60)
    budget = np.array([
        frac_alerts[np.flatnonzero(frac_events >= t - 1e-12)[0]]
        if np.any(frac_events >= t - 1e-12) else 1.0
        for t in targets
    ])
    budget = np.maximum.accumulate(budget)
    print("  alert budget:", {f"{t:.0%}": f"{b:.1%}" for t, b in zip(targets[::12], budget[::12])})

    fig, axes = plt.subplots(1, 2, figsize=(9.4, 3.8))
    ax = axes[0]
    ax.plot(frac_alerts * 100, frac_events * 100, color=BLUE, lw=2,
            label=f"{best} (temporal holdout)")
    ax.plot([0, 100], [0, 100], ls=":", color=GREY, label="random alerting")
    ax.set_xlabel("% of country-years alerted")
    ax.set_ylabel("% of events captured")
    ax.set_title(f"A. Alert budget vs events captured ({y.sum()} events, {len(y)} cells)")
    ax.legend(fontsize=7.5, frameon=False, loc="lower right")

    ax = axes[1]
    ax.plot(targets * 100, budget * 100, color=ORANGE, lw=2)
    ax.set_xlabel("target recall (%)")
    ax.set_ylabel("% of country-years alerted")
    ax.set_title("B. Alert volume required to reach a recall target")
    for t in (0.5, 0.8, 0.9):
        i = np.argmin(np.abs(targets - t))
        ax.plot(targets[i] * 100, budget[i] * 100, "o", color=INK, ms=4)
        ax.annotate(f"{budget[i]*100:.0f}%", (targets[i] * 100, budget[i] * 100),
                    xytext=(4, -12), textcoords="offset points", fontsize=7.5)
    save(fig, "fig07_alert_budget.png")


# --------------------------------------------------------------------------- #
# 8. Subgroups + level 2
# --------------------------------------------------------------------------- #
def fig_subgroups() -> None:
    best = R["calibration"]["model"]
    d = pd.read_csv(REP / f"pred_L1_{best.replace(' ', '_')}.csv").sort_values("p_pred", ascending=False)
    t5 = md_table(
        [[r.iso3, r.year, f"{r.p_pred:.3f}", int(r.y_true)] for r in d.head(15).itertuples()],
        ["Country", "Year", "Predicted risk", "Observed event"],
    )

    sg = pd.DataFrame(R["subgroup"])
    if sg.empty:
        return
    sg = sg[sg.group_by == "region"].sort_values("roc_auc")
    fig, ax = plt.subplots(figsize=(8, 3.4))
    y = np.arange(len(sg))
    ax.barh(y - 0.18, sg.roc_auc, 0.34, color=BLUE, label="ROC-AUC")
    ax.barh(y + 0.18, sg.pr_auc, 0.34, color=ORANGE, label="PR-AUC")
    ax.set_yticks(y)
    ax.set_yticklabels([g[:38] for g in sg.group], fontsize=7.5)
    ax.set_xlim(0, 1)
    ax.set_xlabel("score")
    ax.set_title("Leave-country-out performance by region")
    ax.legend(fontsize=7.5, frameon=False, loc="lower right")
    for yi, (a, p_, n) in enumerate(zip(sg.roc_auc, sg.pr_auc, sg.n)):
        ax.text(a + 0.01, yi - 0.18, f"{a:.2f}", va="center", fontsize=6.5)
        ax.text(p_ + 0.01, yi + 0.18, f"{p_:.2f} (n={n})", va="center", fontsize=6.5)
    save(fig, "fig08_subgroups.png")


def fig_levels() -> None:
    rows = []
    for level in ("L1 country-year", "L2 country-period"):
        for m in MODEL_ORDER:
            sub = COMP[(COMP.level == level) & (COMP.scheme == "temporal_holdout")
                       & (COMP.metric == "pr_auc") & (COMP.model == m)]
            if not sub.empty:
                rows.append({"level": level, "model": m, "pr_auc": float(sub.value.iloc[0])})
    d = pd.DataFrame(rows)
    fig, ax = plt.subplots(figsize=(8, 3.4))
    x = np.arange(len(MODEL_ORDER))
    for i, (level, g) in enumerate(d.groupby("level")):
        g = g.set_index("model").reindex(MODEL_ORDER)
        ax.bar(x + (i - 0.5) * 0.36, g.pr_auc, 0.36,
               color=[BLUE, ORANGE][i], label=f"{level}", alpha=0.9)
    ax.set_xticks(x)
    ax.set_xticklabels(MODEL_ORDER, rotation=12)
    ax.set_ylabel("PR-AUC")
    ax.set_title("Resolution matters: fine (country-year) vs coarse (country-period)")
    ax.legend(fontsize=7.5, frameon=False)
    save(fig, "fig09_resolution.png")


# --------------------------------------------------------------------------- #
# Markdown report
# --------------------------------------------------------------------------- #
def md_table(rows: list[list], header: list[str]) -> str:
    out = ["| " + " | ".join(header) + " |", "|" + "|".join(["---"] * len(header)) + "|"]
    for r in rows:
        out.append("| " + " | ".join(str(c) for c in r) + " |")
    return "\n".join(out)


def write_report() -> None:
    N_CLIMATE = len(json.loads((ROOT / "data/raw/nasa_power_country_climate.json").read_text()))
    l1 = R["level1"]["metrics"]
    l2 = R["level2"]["metrics"]
    prev = R["audit"]["level1_prevalence"]

    rows = []
    for m in MODEL_ORDER:
        t, lo, cv = l1[m]["temporal"], l1[m]["loco"], l1[m]["repeated_cv"]
        ci = t["pr_auc_ci"]
        rows.append([
            m, l1[m]["family"],
            f"{t['pr_auc']:.3f} ({ci[0]:.2f}-{ci[1]:.2f})",
            f"{t['roc_auc']:.3f}", f"{lo['pr_auc']:.3f}", f"{cv['pr_auc']:.3f}",
            f"{t['brier']:.4f}", f"{t['precision']:.2f}", f"{t['recall']:.2f}",
            f"{t['f1']:.2f}", f"{t['threshold']:.2f}",
        ])
    t1 = md_table(
        rows,
        ["Model", "Family", "PR-AUC (95% CI)", "ROC-AUC", "PR-AUC LOCO",
         "PR-AUC rep-CV", "Brier", "Prec", "Rec", "F1", "Threshold"],
    )

    rows2 = []
    for m in MODEL_ORDER:
        t, lo = l2[m]["temporal"], l2[m]["loco"]
        rows2.append([m, f"{t['pr_auc']:.3f}", f"{t['roc_auc']:.3f}",
                      f"{lo['pr_auc']:.3f}", f"{lo['roc_auc']:.3f}", f"{t['brier']:.4f}"])
    t2 = md_table(rows2, ["Model", "PR-AUC", "ROC-AUC", "PR-AUC LOCO", "ROC-AUC LOCO", "Brier"])

    ab = R["ablation"]
    t3 = md_table(
        [[n, ab[n]["n_features"], f"{ab[n]['temporal']['pr_auc']:.3f}",
          f"{ab[n]['temporal']['roc_auc']:.3f}", f"{ab[n]['loco']['pr_auc']:.3f}"]
         for n in ab],
        ["Ablation setting", "k", "PR-AUC (time)", "ROC-AUC (time)", "PR-AUC (LOCO)"],
    )

    best = R["calibration"]["model"]
    d = pd.read_csv(REP / f"pred_L1_{best.replace(' ', '_')}.csv").sort_values("p_pred", ascending=False)
    t5 = md_table(
        [[r.iso3, r.year, f"{r.p_pred:.3f}", int(r.y_true)] for r in d.head(15).itertuples()],
        ["Country", "Year", "Predicted risk", "Observed event"],
    )

    sg = pd.DataFrame(R["subgroup"])
    t4 = md_table(
        [[r.group_by, r.group, r.n, r.positives, f"{r.roc_auc:.3f}", f"{r.pr_auc:.3f}"]
         for r in sg.itertuples()],
        ["Grouped by", "Group", "n", "events", "ROC-AUC", "PR-AUC"],
    )

    chain = R["chain"]
    s1 = chain["stage1"]
    s2 = chain["stage2"]
    hz = chain.get("hurdle", {})

    na = json.loads((REP / "novelty_audit.json").read_text()) if (REP / "novelty_audit.json").exists() else {}
    novelty_rows = [[k.split(". ", 1)[1], v["hits"]] for k, v in na.items()]
    t0 = md_table(novelty_rows, ["Europe PMC query", "Hits"])
    best_temporal = max(l1[m]["temporal"]["pr_auc"] for m in MODEL_ORDER)
    best_temporal_name = max(MODEL_ORDER, key=lambda m: l1[m]["temporal"]["pr_auc"])

    md = f"""# GlandersWatch - Chained Multi-Level ML Evaluation

## 0. Novelty audit (reproducible prior-art check, Europe PMC)

{t0}

`glanders + NASA POWER` returns **0** records and `glanders + gradient boosting` returns
**{na.get("O. glanders + gradient boosting", {}).get("hits", "n/a")}** records, none of which is a glanders
risk model. The nearest prior art is descriptive spatio-temporal cluster detection in Brazil and a
risk-factor analysis of the 2019-2023 Indian serosurvey - neither is a predictive, calibrated,
chained ML pipeline over livestock-census and reanalysis covariates.


*Generated by `src/03_train_evaluate.py` + `src/04_report.py`; raw numbers in `reports/results.json`.*

## 1. Datasets (all unused in glanders ML before this study)

| # | Source | Role | Granularity | Coverage |
|---|--------|------|-------------|----------|
| 1 | Europe PMC full corpus query (`glanders OR "Burkholderia mallei" OR farcy`) | animal history - text-mined occurrence events | country x year | {R['audit']['literature_records']:,} records, {R['audit']['literature_events']} extracted events |
| 2 | FAOSTAT livestock stocks (horses, asses, mules, camels, cattle, goats, sheep) | animal population - exposure denominator | country x year | 1961-2023 |
| 3 | World Bank WDI (10 indicators) + country centroids | socio-agricultural context, reporting capacity | country x year | 2000-2024 |
| 4 | NASA POWER agro-climatology (T2M, T2M max/min, precipitation, humidity, wind) | environmental covariates | country x year | 2005-2024, {N_CLIMATE} centroids |

**Panel:** {R['audit']['level1_rows']:,} country-year rows, {R['audit']['level1_positives']} positive labels,
{R['audit']['equine_countries']} equine-holding countries, prevalence {prev:.2%}.

## 2. Level 1 - country-year occurrence (temporal holdout 2018-2023)

{t1}

Selected by leave-country-out PR-AUC: **{R['best_model']}**.
Prevalence {prev:.3f} -> the best temporal PR-AUC ({best_temporal:.3f}, {best_temporal_name}) is a
lift of roughly {best_temporal/prev:.1f}x over chance.

## 3. Level 2 - coarse resolution (country x 5-year period)

{t2}

## 4. Ablation settings

{t3}

## 5. Chained pipeline

Stage 1 (population forecast, leave-country-out):
`{s1['best']}` MAE {s1['scores'][s1['best']]['mae']:.3f}, median AE {s1['scores'][s1['best']]['median_ae']:.3f},
Spearman {s1['scores'][s1['best']]['spearman']:.3f}.

Stage 2 (occurrence) with and without the chained population signal:

| Variant | PR-AUC (temporal) | ROC-AUC | PR-AUC (LOCO) |
|---|---|---|---|
| plain | {s2['plain']['temporal']['pr_auc']:.3f} | {s2['plain']['temporal']['roc_auc']:.3f} | {s2['plain']['loco']['pr_auc']:.3f} |
| chained | {s2['chained']['temporal']['pr_auc']:.3f} | {s2['chained']['temporal']['roc_auc']:.3f} | {s2['chained']['loco']['pr_auc']:.3f} |

Stage 3 (intensity | occurrence): MAE {chain.get('stage3', {}).get('mae', float('nan')):.3f},
Spearman {chain.get('stage3', {}).get('spearman', float('nan')):.3f}.

Hurdle chain (P x intensity) ranks next-year event burden with Spearman {hz.get('spearman_test', float('nan')):.3f};
the top-10% highest-risk cells capture **{hz.get('events_captured', 'n/a')}/{hz.get('total_events', 'n/a')}** observed events.

## 5b. Highest-risk cells in the temporal holdout

{t5}

## 6. Subgroup performance (leave-country-out)

{t4}

## 7. Calibration

Model `{R['calibration']['model']}`: ECE {R['calibration']['ece']:.3f}, Brier {R['calibration']['brier']:.4f}.

## 8. Figures

`figures/fig01_dataset_coverage.png` ... `fig09_resolution.png`.
"""
    (REP / "RESULTS.md").write_text(md)
    print("report: reports/RESULTS.md")


if __name__ == "__main__":
    fig_coverage()
    fig_comparison()
    fig_curves()
    fig_calibration()
    fig_ablation()
    fig_shap()
    fig_alerts()
    fig_subgroups()
    fig_levels()
    write_report()
