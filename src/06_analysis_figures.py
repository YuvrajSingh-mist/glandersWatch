"""Figures for the dataset / label / feature analysis.

Run:  .venv/bin/python src/06_analysis_figures.py
"""
from __future__ import annotations

import json
import pathlib
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import leaves_list, linkage

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import ml_core as C  # noqa: E402
from importlib import import_module  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]
PROC, REP, FIG = ROOT / "data" / "processed", ROOT / "reports", ROOT / "figures"
FIG.mkdir(exist_ok=True)

plt.rcParams.update({
    "figure.dpi": 150, "font.size": 8.5,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.alpha": 0.22, "axes.titlesize": 9.5,
    "axes.titleweight": "bold", "figure.facecolor": "white",
})
BLUE, ORANGE, TEAL, GREY, INK = "#2563eb", "#ea580c", "#0d9488", "#94a3b8", "#1f2933"

A = json.loads((REP / "dataset_analysis.json").read_text())
IMP = pd.read_csv(REP / "feature_importance.csv")

ana = import_module("05_dataset_analysis")
DF = ana.load()


def save(fig, name):
    fig.tight_layout()
    fig.savefig(FIG / name, bbox_inches="tight")
    plt.close(fig)
    print("figure:", name)


# --------------------------------------------------------------------------- #
def fig_labels() -> None:
    lab = A["labels"]
    years = sorted(int(k) for k in lab["prevalence_by_year"])
    prev = [lab["prevalence_by_year"][str(y)] * 100 for y in years]
    pos = [lab["positives_by_year"][str(y)] for y in years]

    fig, axes = plt.subplots(1, 3, figsize=(12, 3.5))
    ax = axes[0]
    ax.bar(years, pos, color=BLUE, alpha=0.85, width=0.75)
    ax2 = ax.twinx()
    ax2.plot(years, prev, color=ORANGE, lw=1.8, marker="o", ms=3)
    ax2.set_ylabel("prevalence (%)", color=ORANGE)
    ax2.tick_params(axis="y", colors=ORANGE)
    ax2.grid(False)
    ax.set_ylabel("positive country-years", color=BLUE)
    ax.set_xlabel("year")
    ax.set_title("A. Label volume and prevalence")
    ax.set_xticks(range(2005, 2024, 4))

    ax = axes[1]
    counts = DF.groupby("iso3").y_occ_next.sum()
    counts = counts[counts > 0].astype(int).value_counts().sort_index()
    ax.bar(counts.index, counts.values, color=TEAL, alpha=0.85)
    ax.set_xlabel("positive years per country")
    ax.set_ylabel("countries")
    ax.set_title(f"B. Label concentration\n(labels sit in {lab['positive_countries']}"
                 f"/{lab['countries']} countries)")

    ax = axes[2]
    reg = pd.Series({k: v["rate"] for k, v in lab["prevalence_by_region"].items()}).sort_values()
    regn = pd.Series({k: v["n"] for k, v in lab["prevalence_by_region"].items()})
    y = np.arange(len(reg))
    ax.barh(y, reg.values * 100, color=[BLUE if r < 0.1 else ORANGE for r in reg.values])
    ax.set_yticks(y)
    ax.set_yticklabels([r[:34] for r in reg.index], fontsize=6.8)
    ax.set_xlabel("prevalence (%)")
    ax.set_title("C. Regional prevalence")
    for yi, (r, n) in enumerate(zip(reg.values, regn.reindex(reg.index).values)):
        ax.text(r * 100 + 0.4, yi, f"{r*100:.1f} (n={int(n)})", va="center", fontsize=6)
    save(fig, "fig10_label_anatomy.png")


def fig_correlation() -> None:
    top = IMP.nsmallest(22, "shap_rank").feature.tolist()
    top = [f for f in top if f in DF.columns]
    X = DF[top].astype(float)
    X = X.fillna(X.median())
    corr = X.corr(method="spearman")
    order = leaves_list(linkage(1 - corr.abs().to_numpy(), method="average"))
    corr = corr.iloc[order, order]

    fig, ax = plt.subplots(figsize=(7.6, 6.4))
    im = ax.imshow(corr, cmap="RdBu_r", vmin=-1, vmax=1)
    ax.set_xticks(range(len(corr)))
    ax.set_xticklabels(corr.columns, rotation=90, fontsize=6.5)
    ax.set_yticks(range(len(corr)))
    ax.set_yticklabels(corr.index, fontsize=6.5)
    ax.set_title("Spearman correlation, 22 highest-ranked features\n"
                 "(clusters of |rho| >= 0.90 are redundant)")
    ax.grid(False)
    fig.colorbar(im, ax=ax, shrink=0.75, label="Spearman rho")
    save(fig, "fig11_correlation.png")


def fig_importance_views() -> None:
    m = IMP.dropna(subset=["mutual_info", "shap_rank"]).copy()
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))

    ax = axes[0]
    sc = ax.scatter(m.mutual_info, m.shap_rank, s=26, c=m.abs_rho, cmap="viridis")
    for r in m.nsmallest(6, "shap_rank").itertuples():
        ax.annotate(r.feature, (r.mutual_info, r.shap_rank), fontsize=6.5,
                    xytext=(3, 3), textcoords="offset points")
    ax.invert_yaxis()
    ax.set_xlabel("mutual information with the label")
    ax.set_ylabel("SHAP rank (1 = most important)")
    ax.set_title(f"A. Marginal vs conditional importance\n"
                 f"rank correlation rho = {A['importance_agreement']['spearman_mi_vs_shap']:.2f}")
    fig.colorbar(sc, ax=ax, shrink=0.85, label="|Spearman with label|")

    ax = axes[1]
    top = m.nsmallest(14, "shap_rank").iloc[::-1]
    y = np.arange(len(top))
    ax.barh(y, top.mean_abs_shap, color=BLUE, alpha=0.85)
    for yi, r in enumerate(top.itertuples()):
        ax.text(r.mean_abs_shap + 0.01, yi, f"rho={r.spearman:+.2f}",
                va="center", fontsize=6, color=GREY)
    ax.set_yticks(y)
    ax.set_yticklabels(top.feature, fontsize=7)
    ax.set_xlabel("mean |SHAP| (log-odds)")
    ax.set_title("B. Conditional attribution with marginal sign")
    save(fig, "fig12_importance_views.png")


def fig_diagnostics() -> None:
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.4))

    ax = axes[0]
    src = A["missingness"]["by_source"]
    names = list(src)
    vals = [src[n] for n in names]
    ax.bar(names, vals, color=[TEAL, BLUE, ORANGE], alpha=0.85)
    for i, v in enumerate(vals):
        ax.text(i, v + 0.06, f"{v:.2f}%", ha="center", fontsize=7.5)
    ax.set_ylabel("mean missing (%)")
    ax.set_title(f"A. Missingness by source (overall {A['missingness']['overall_pct']:.1f}%)")
    ax.set_xticklabels([n.split(" (")[0] for n in names], fontsize=7.5)

    ax = axes[1]
    vif = pd.DataFrame(A["vif_top10"])
    y = np.arange(len(vif))[::-1]
    ax.barh(y, vif.vif, color=[ORANGE if v > 10 else BLUE for v in vif.vif])
    ax.axvline(10, ls="--", color=INK, lw=1)
    ax.text(10.5, 0.2, "VIF = 10", fontsize=7, color=INK)
    ax.set_yticks(y)
    ax.set_yticklabels(vif.feature, fontsize=7)
    ax.set_xscale("log")
    ax.set_xlabel("VIF (log scale)")
    ax.set_title("B. Multicollinearity of the 10 worst features")
    save(fig, "fig13_diagnostics.png")


if __name__ == "__main__":
    fig_labels()
    fig_correlation()
    fig_importance_views()
    fig_diagnostics()


# --------------------------------------------------------------------------- #
def fig_background() -> None:
    """Two motivating figures placed after the introduction's background section.

    A: where the susceptible equid population is.
    B: how much glanders activity has been documented each year.
    """
    panel = pd.read_csv(PROC / "country_year_panel.csv")
    ev = pd.read_csv(PROC / "literature_events.csv")

    # --- A: top countries by equid population, split by species ---------------
    yr = 2019 if (panel.year == 2019).any() else int(panel.year.max())
    snap = panel[panel.year == yr].copy()
    snap["total"] = snap[["horses", "asses", "mules"]].sum(axis=1)
    top = snap.nlargest(14, "total").iloc[::-1]

    fig, axes = plt.subplots(1, 2, figsize=(11.6, 3.9))
    ax = axes[0]
    left = np.zeros(len(top))
    for col, colour, label in (("horses", BLUE, "horses"),
                               ("asses", ORANGE, "asses / donkeys"),
                               ("mules", TEAL, "mules")):
        ax.barh(top.iso3, top[col] / 1e6, left=left / 1e6, color=colour, label=label, height=0.74)
        left = left + top[col].to_numpy()
    ax.set_xlabel(f"equids, millions (FAOSTAT stocks, {yr})")
    ax.set_title(f"A. Susceptible population, fourteen largest countries")
    ax.legend(fontsize=7.5, frameon=False, loc="lower right")

    # --- B: documented occurrence events per year ----------------------------
    ax = axes[1]
    yrs = np.arange(2005, 2024)
    counts = [int((ev.year == y).sum()) for y in yrs]
    ax.bar(yrs, counts, color=GREY, width=0.72)
    win = pd.Series(counts).rolling(3, center=True, min_periods=1).mean()
    ax.plot(yrs, win, color=BLUE, lw=2, label="three-year mean")
    ax.set_xlabel("year")
    ax.set_ylabel("documented occurrence events")
    ax.set_title("B. Glanders activity recorded in the literature")
    ax.legend(fontsize=7.5, frameon=False, loc="upper left")
    ax.annotate("open-access publishing grows,\nso this is not incidence",
                xy=(2013, 20), fontsize=7, color=INK, ha="left", va="top")

    save(fig, "fig14_background.png")


if __name__ == "__main__":
    fig_background()
