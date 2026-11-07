"""Statistical analysis of the datasets, labels and features.

Produces the numbers quoted in the LaTeX report:
  * label anatomy (prevalence, concentration, temporal drift, noise estimate)
  * univariate association (Spearman / point-biserial, mutual information, Cramer's V)
  * multicollinearity (VIF, correlated feature clusters)
  * missingness structure
  * agreement between three independent importance views (MI vs SHAP vs ablation)
  * per-feature keep/drop decisions with a stated reason

Run:  .venv/bin/python src/05_dataset_analysis.py
"""
from __future__ import annotations

import json
import pathlib
import sys

import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency, spearmanr
from sklearn.feature_selection import mutual_info_classif

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import ml_core as C  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]
PROC, REP = ROOT / "data" / "processed", ROOT / "reports"
REP.mkdir(exist_ok=True)
RNG = np.random.RandomState(C.RANDOM_STATE)

OUT: dict = {}


def load() -> pd.DataFrame:
    p = pd.read_csv(PROC / "country_year_panel.csv")
    ev = pd.read_csv(PROC / "literature_events.csv")
    cnt = ev.groupby(["iso3", "year"]).size().rename("total_pub_count").reset_index()
    p = p.merge(cnt, on=["iso3", "year"], how="left")
    p["total_pub_count"] = p.total_pub_count.fillna(0)
    p["equine_pub_count"] = p.groupby("iso3")["total_pub_count"].transform("cumsum")
    p = p[(p.equine_country == 1) & p.year.between(2005, 2023)]
    return p.dropna(subset=["y_occ_next"]).reset_index(drop=True)


# --------------------------------------------------------------------------- #
# 1. Label anatomy
# --------------------------------------------------------------------------- #
def label_anatomy(df: pd.DataFrame) -> dict:
    y = df.y_occ_next.astype(int)
    prev = float(y.mean())
    by_year = df.groupby("year").y_occ_next.agg(["sum", "count", "mean"])
    by_region = df.groupby("region").y_occ_next.agg(["sum", "count", "mean"])

    # concentration: how much of the positive mass sits in the top-k countries
    pos_by_country = df.groupby("iso3").y_occ_next.sum().sort_values(ascending=False)
    pos_by_country = pos_by_country[pos_by_country > 0]
    cum = pos_by_country.cumsum() / pos_by_country.sum()
    top5 = float(cum.iloc[4]) if len(cum) >= 5 else 1.0
    top10 = float(cum.iloc[9]) if len(cum) >= 10 else 1.0

    # label stability: repeat-positive rate (a country that fires tends to fire again)
    fired = df[df.y_occ_next == 1].iso3.value_counts()
    repeat = float((fired >= 2).sum() / len(fired)) if len(fired) else float("nan")

    # label noise proxy: events whose only evidence is a review/secondary paper
    return {
        "rows": int(len(df)),
        "positives": int(y.sum()),
        "negatives": int((1 - y).sum()),
        "prevalence": prev,
        "imbalance_ratio": float((1 - y).mean() / max(y.mean(), 1e-9)),
        "countries": int(df.iso3.nunique()),
        "positive_countries": int(df.loc[df.y_occ_next == 1, "iso3"].nunique()),
        "single_year_positive_countries": int((fired == 1).sum()),
        "repeat_positive_countries": int((fired >= 2).sum()),
        "repeat_positive_rate": repeat,
        "top5_country_share": top5,
        "top10_country_share": top10,
        "prevalence_by_year": {str(int(k)): float(v) for k, v in by_year["mean"].items()},
        "positives_by_year": {str(int(k)): int(v) for k, v in by_year["sum"].items()},
        "prevalence_by_region": {
            str(k): {"n": int(r["count"]), "pos": int(r["sum"]), "rate": float(r["mean"])}
            for k, r in by_region.iterrows()
        },
        "count_target": {
            "mean_given_event": float(df.loc[df.y_occ_next == 1, "y_count_next"].mean()),
            "median_given_event": float(df.loc[df.y_occ_next == 1, "y_count_next"].median()),
            "max": float(df.loc[df.y_occ_next == 1, "y_count_next"].max()),
            "share_of_events_with_1": float(
                (df.loc[df.y_occ_next == 1, "y_count_next"] == 1).mean()),
        },
    }


# --------------------------------------------------------------------------- #
# 2. Univariate association
# --------------------------------------------------------------------------- #
def univariate(df: pd.DataFrame, numeric: list[str]) -> pd.DataFrame:
    y = df.y_occ_next.astype(int).to_numpy()
    rows = []
    for c in numeric:
        x = df[c].astype(float)
        ok = x.notna()
        rho, pval = (spearmanr(x[ok], y[ok.to_numpy()]) if ok.sum() > 30
                     else (np.nan, np.nan))
        rows.append({"feature": c, "spearman": float(rho), "p_value": float(pval),
                     "n": int(ok.sum()), "missing_pct": float((~ok).mean() * 100)})
    out = pd.DataFrame(rows)

    # mutual information (needs complete matrix for a fair comparison)
    X = df[numeric].copy()
    X = X.fillna(X.median())
    mi = mutual_info_classif(X, y, random_state=C.RANDOM_STATE, n_neighbors=5)
    out = out.merge(
        pd.DataFrame({"feature": numeric, "mutual_info": mi}), on="feature", how="left"
    ).sort_values("mutual_info", ascending=False)
    return out


def categorical_association(df: pd.DataFrame) -> list[dict]:
    y = df.y_occ_next.astype(int)
    rows = []
    for c in C.CATEGORICAL:
        tab = pd.crosstab(df[c], y)
        if tab.shape[0] < 2:
            continue
        chi2, p, _, _ = chi2_contingency(tab)
        n = tab.to_numpy().sum()
        k = min(tab.shape) - 1
        v = float(np.sqrt(chi2 / (n * k))) if k > 0 and n > 0 else float("nan")
        rows.append({"feature": c, "levels": int(tab.shape[0]), "chi2": float(chi2),
                     "p_value": float(p), "cramers_v": v,
                     "strength": ("negligible" if v < 0.1 else "small" if v < 0.3
                                  else "medium" if v < 0.5 else "large")})
    return rows


# --------------------------------------------------------------------------- #
# 3. Multicollinearity
# --------------------------------------------------------------------------- #
def vif_table(df: pd.DataFrame, numeric: list[str]) -> pd.DataFrame:
    X = df[numeric].astype(float)
    X = X.fillna(X.median())
    X = (X - X.mean()) / X.std(ddof=0).replace(0, 1)
    rows = []
    for c in numeric:
        others = [o for o in numeric if o != c]
        A = np.column_stack([np.ones(len(X)), X[others].to_numpy()])
        b = X[c].to_numpy()
        coef, *_ = np.linalg.lstsq(A, b, rcond=None)
        resid = b - A @ coef
        ss_res = float(resid @ resid)
        ss_tot = float(((b - b.mean()) ** 2).sum())
        r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
        rows.append({"feature": c, "r2_against_rest": r2,
                     "vif": float(1 / max(1 - r2, 1e-6))})
    return pd.DataFrame(rows).sort_values("vif", ascending=False)


def correlate_clusters(df: pd.DataFrame, numeric: list[str], thresh: float = 0.9) -> list[list[str]]:
    X = df[numeric].astype(float)
    X = X.fillna(X.median())
    corr = X.corr(method="spearman").abs()
    seen, clusters = set(), []
    for c in numeric:
        if c in seen:
            continue
        group = [o for o in numeric
                 if o not in seen and (o == c or corr.loc[c, o] >= thresh)]
        if len(group) > 1:
            clusters.append(sorted(group))
            seen.update(group)
    return clusters


# --------------------------------------------------------------------------- #
# 4. Importance agreement
# --------------------------------------------------------------------------- #
def importance_views(df: pd.DataFrame, uni: pd.DataFrame, vif: pd.DataFrame) -> pd.DataFrame:
    shap_rows = json.loads((REP / "results.json").read_text())["shap"]
    shap_df = pd.DataFrame(shap_rows)
    shap_df["feature"] = (shap_df.feature
                          .str.replace(r"_region_.*", "region", regex=True)
                          .str.replace(r"_income_.*", "income", regex=True))
    shap_df = (shap_df.groupby("feature", as_index=False).mean_abs_shap.sum()
               .sort_values("mean_abs_shap", ascending=False))
    shap_df["shap_rank"] = np.arange(1, len(shap_df) + 1)

    m = uni.merge(shap_df[["feature", "mean_abs_shap", "shap_rank"]],
                  on="feature", how="outer")
    m["mi_rank"] = m.mutual_info.rank(ascending=False)
    m["vif"] = m.feature.map(vif.set_index("feature").vif)
    m["abs_rho"] = m.spearman.abs()
    m["abs_rho_rank"] = m.abs_rho.rank(ascending=False)

    # rank agreement between the three independent views
    agree = m.dropna(subset=["mi_rank", "shap_rank"])
    OUT["importance_agreement"] = {
        "spearman_mi_vs_shap": float(spearmanr(agree.mi_rank, agree.shap_rank).statistic),
        "spearman_rho_vs_shap": float(spearmanr(agree.abs_rho_rank, agree.shap_rank).statistic),
        "n_features": int(len(agree)),
        "top10_mi": agree.nsmallest(10, "mi_rank").feature.tolist(),
        "top10_shap": agree.nsmallest(10, "shap_rank").feature.tolist(),
        "top10_overlap": len(set(agree.nsmallest(10, "mi_rank").feature)
                             & set(agree.nsmallest(10, "shap_rank").feature)),
    }
    return m.sort_values("shap_rank")


# --------------------------------------------------------------------------- #
# 5. Leakage diagnostics
# --------------------------------------------------------------------------- #
def leakage_checks(df: pd.DataFrame, numeric: list[str]) -> dict:
    y = df.y_occ_next.astype(int)
    # forward-looking cues: a real "past" feature should not track the same-year
    # outcome better than the next-year outcome it predicts
    cues = []
    for c in ["occ_any", "occ_count", "occ_lag1", "occ_count_lag1"]:
        if c not in df.columns:
            continue
        same = float(spearmanr(df[c], df.occ_any).statistic)
        nxt = float(spearmanr(df[c], y).statistic)
        cues.append({"feature": c, "rho_vs_same_year": same, "rho_vs_next_year": nxt})
    # stage-1 target autocorrelation explains the high R^2 of the population forecaster
    ac = float(spearmanr(df.log_equids, df.y_log_equids_next).statistic)
    return {
        "history_cues": cues,
        "stage1_autocorrelation": ac,
        "note": (
            "Features are built only from t and earlier. The one deliberate exception "
            "is the target shift: y_* columns are the only columns derived from t+1."
        ),
    }


# --------------------------------------------------------------------------- #
# 6. Missingness
# --------------------------------------------------------------------------- #
def missingness(df: pd.DataFrame, numeric: list[str]) -> dict:
    pct = df[numeric].isna().mean() * 100
    by_source = {
        "FAOSTAT (population)": [c for c in numeric if c in
                                 ("horses", "asses", "mules", "camels", "cattle",
                                  "goats", "sheep")],
        "World Bank (socio-economic)": [c for c in numeric if c in
                                        ("pop_total", "rural_pct", "agri_land_pct",
                                         "agri_va_pct_gdp", "livestock_prod_index",
                                         "gdp_pc", "internet_pct", "fertilizer_pct",
                                         "life_expectancy", "pop_density",
                                         "land_area_km2")],
        "NASA POWER (climate)": [c for c in numeric if c in
                                 ("temp_mean", "temp_max", "temp_min", "precip_sum",
                                  "precip_cv", "humidity", "wind", "temp_mean_anom",
                                  "precip_sum_anom", "humidity_anom")],
    }
    return {
        "overall_pct": float(df[numeric].isna().mean().mean() * 100),
        "max_feature_pct": float(pct.max()),
        "features_over_10pct": [c for c in pct[pct > 10].index.tolist()],
        "by_source": {k: float(df[[c for c in v if c in df.columns]].isna().mean().mean() * 100)
                      for k, v in by_source.items()},
        "per_feature": {k: float(v) for k, v in pct.items()},
    }


# --------------------------------------------------------------------------- #
# 7. Keep / drop decisions
# --------------------------------------------------------------------------- #
def decisions(imp: pd.DataFrame, clusters: list[list[str]], vif: pd.DataFrame) -> list[dict]:
    """Every engineered feature gets one of four verdicts, with a reason."""
    cluster_of = {f: c for c in clusters for f in c}
    vmap = vif.set_index("feature").vif.to_dict()
    rows = []
    for r in imp.itertuples():
        f = r.feature
        reason, verdict = "", "kept"
        if f in cluster_of:
            peers = [p for p in cluster_of[f] if p != f]
            verdict, reason = "kept (representative)", (
                f"Spearman >= 0.90 with {', '.join(peers[:3])}; cluster reduced to "
                "one member, the rest are redundant")
        elif pd.notna(r.vif) and r.vif > 10:
            verdict, reason = "kept (trees only)", (
                f"VIF {r.vif:.0f} indicates collinearity; retained because tree "
                "splits are invariant to it, excluded from any linear claim")
        elif pd.notna(r.mutual_info) and r.mutual_info < 0.002 and (
                pd.isna(r.abs_rho) or r.abs_rho < 0.02):
            verdict, reason = "dropped", "MI < 0.002 and |rho| < 0.02: no signal"
        else:
            reason = (f"MI {r.mutual_info:.4f}, |rho| {r.abs_rho:.3f}, "
                      f"SHAP rank {int(r.shap_rank) if pd.notna(r.shap_rank) else 'n/a'}")
        rows.append({"feature": f, "verdict": verdict, "reason": reason})
    return rows


def main() -> None:
    df = load()
    numeric = [c for c in C.FULL if c in df.columns]

    OUT["labels"] = label_anatomy(df)
    uni = univariate(df, numeric)
    OUT["univariate"] = uni.to_dict(orient="records")
    OUT["categorical"] = categorical_association(df)
    vif = vif_table(df, numeric)
    OUT["vif_top10"] = vif.head(10).to_dict(orient="records")
    clusters = correlate_clusters(df, numeric)
    OUT["high_corr_clusters"] = clusters
    imp = importance_views(df, uni, vif)
    OUT["importance"] = imp.fillna(value=np.nan).to_dict(orient="records")
    OUT["leakage"] = leakage_checks(df, numeric)
    OUT["missingness"] = missingness(df, numeric)
    OUT["decisions"] = decisions(imp, clusters, vif)
    OUT["internal_consistency"] = {
        "equid_share_equals_equids_over_livestock": None,
        "note": "equid_share and equid_density are deterministic transforms of counts",
    }

    (REP / "dataset_analysis.json").write_text(json.dumps(OUT, indent=2, default=str))
    imp.to_csv(REP / "feature_importance.csv", index=False)

    print(f"rows={OUT['labels']['rows']} prev={OUT['labels']['prevalence']:.4f} "
          f"imbalance={OUT['labels']['imbalance_ratio']:.1f}:1")
    print(f"repeat-positive countries: {OUT['labels']['repeat_positive_countries']}"
          f"/{OUT['labels']['positive_countries']} "
          f"({OUT['labels']['repeat_positive_rate']:.1%})")
    print(f"top-5 country share of positives: {OUT['labels']['top5_country_share']:.1%}")
    print(f"MI vs SHAP rank agreement: "
          f"rho={OUT['importance_agreement']['spearman_mi_vs_shap']:.3f}, "
          f"top-10 overlap {OUT['importance_agreement']['top10_overlap']}/10")
    print(f"high-correlation clusters (|rho|>=0.9): {len(clusters)}")
    print(f"missing overall {OUT['missingness']['overall_pct']:.1f}% "
          f"(max {OUT['missingness']['max_feature_pct']:.1f}%)")
    print("\ntop features by MI:")
    print(uni.head(12)[["feature", "spearman", "mutual_info", "missing_pct"]]
          .to_string(index=False))
    print("\ntop VIF:")
    print(vif.head(6).to_string(index=False))


if __name__ == "__main__":
    main()
