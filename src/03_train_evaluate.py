"""Level 1-3 model training, chaining and multi-level evaluation.

Run:  .venv/bin/python src/03_train_evaluate.py
Writes reports/*.json|csv and figures/*.png
"""
from __future__ import annotations

import json
import os
import pathlib
import sys
import time
import warnings

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import Ridge
from scipy.stats import spearmanr
from sklearn.metrics import mean_absolute_error, median_absolute_error, r2_score
from sklearn.model_selection import GroupKFold, RandomizedSearchCV, StratifiedKFold
from sklearn.pipeline import Pipeline

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import ml_core as C  # noqa: E402

warnings.filterwarnings("ignore")
ROOT = pathlib.Path(__file__).resolve().parents[1]
PROC, REP = ROOT / "data" / "processed", ROOT / "reports"
REP.mkdir(exist_ok=True)
RNG = np.random.RandomState(C.RANDOM_STATE)

RESULTS: dict = {"level1": {}, "level2": {}, "chain": {}, "ablation": {},
                 "subgroup": [], "calibration": {}, "shap": [], "audit": {}}
COMP_ROWS: list[dict] = []


def log(msg: str) -> None:
    print(msg, flush=True)


# --------------------------------------------------------------------------- #
# Data
# --------------------------------------------------------------------------- #
def load_level1() -> pd.DataFrame:
    p = pd.read_csv(PROC / "country_year_panel.csv")
    # research-output proxies for the surveillance-bias ablation (AS-7)
    ev = pd.read_csv(PROC / "literature_events.csv")
    cnt = ev.groupby(["iso3", "year"]).size().rename("total_pub_count").reset_index()
    p = p.merge(cnt, on=["iso3", "year"], how="left")
    p["total_pub_count"] = p.total_pub_count.fillna(0)
    p["equine_pub_count"] = p.groupby("iso3")["total_pub_count"].transform("cumsum")

    p = p[p.equine_country == 1].copy()
    p = p[p.year.between(2005, 2023)]
    p = p.dropna(subset=["y_occ_next"])
    p["y_occ_next"] = p.y_occ_next.astype(int)
    return p.sort_values(["year", "iso3"]).reset_index(drop=True)


def load_level2(level1: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for t0 in (2005, 2010, 2015, 2020):
        block = level1[level1.year == t0].copy()
        if block.empty:
            continue
        fut = level1[(level1.year > t0) & (level1.year <= t0 + 4)]
        agg = fut.groupby("iso3").agg(
            y_occ_period=("y_occ_next", "max"),
            y_count_period=("y_count_next", "sum"),
        )
        block = block.merge(agg, left_on="iso3", right_index=True, how="left")
        block["y_occ_period"] = block.y_occ_period.fillna(0).astype(int)
        block["period_start"] = t0
        rows.append(block)
    out = pd.concat(rows, ignore_index=True)
    return out.dropna(subset=["y_occ_period"]).reset_index(drop=True)


# --------------------------------------------------------------------------- #
# Tuning + fitting
# --------------------------------------------------------------------------- #
def tune_model(spec: C.ModelSpec, X, y, groups, numeric, cats, n_iter=8, seed=0):
    pipe = C.make_pipeline(spec, numeric, cats, {})
    if not spec.param_dist:
        return pipe, {}
    n_splits = min(3, max(2, int(pd.Series(groups).nunique() / 20)))
    cv = GroupKFold(n_splits=n_splits)
    grid = {f"model__{k}": v for k, v in spec.param_dist.items()}
    search = RandomizedSearchCV(
        pipe,
        grid,
        n_iter=n_iter,
        scoring="average_precision",
        cv=list(cv.split(X, y, groups)),
        random_state=C.RANDOM_STATE + seed,
        n_jobs=-1,
        refit=True,
        error_score="raise",
    )
    search.fit(X, y, groups=groups)
    best = {k.replace("model__", ""): v for k, v in search.best_params_.items()}
    return search.best_estimator_, best


def fit_calibrated(pipe, X, y, method="sigmoid"):
    """Platt/isotonic calibration fitted only on training folds."""
    n_pos = int(np.sum(y))
    if n_pos < 15:
        pipe.fit(X, y)
        return pipe
    cal = CalibratedClassifierCV(clone(pipe), method=method, cv=3)
    cal.fit(X, y)
    return cal


def predict_proba(model, X) -> np.ndarray:
    return model.predict_proba(X)[:, 1]


# --------------------------------------------------------------------------- #
# Schemes
# --------------------------------------------------------------------------- #
def scheme_temporal(pipe, X, y, years, train_end=2017):
    tr = years <= train_end
    te = years > train_end
    model = fit_calibrated(clone(pipe), X[tr], y[tr])
    p_tr = predict_proba(model, X[tr])
    p_te = predict_proba(model, X[te])
    thr = C.best_f1_threshold(y[tr], p_tr)
    m = C.compute_metrics(y[te], p_te, threshold=thr)
    m["ece"] = C.expected_calibration_error(y[te], p_te)
    m["pr_auc_ci"] = C.bootstrap_ci(y[te], p_te, "pr_auc")
    m["roc_auc_ci"] = C.bootstrap_ci(y[te], p_te, "roc_auc")
    return m, p_te, y[te], years[te], te


def scheme_loco(pipe, X, y, groups):
    gkf = GroupKFold(n_splits=5)
    oof = np.zeros(len(y))
    for tr, te in gkf.split(X, y, groups):
        model = fit_calibrated(clone(pipe), X.iloc[tr], y[tr])
        oof[te] = predict_proba(model, X.iloc[te])
    thr = C.best_f1_threshold(y, oof)
    m = C.compute_metrics(y, oof, threshold=thr)
    m["ece"] = C.expected_calibration_error(y, oof)
    return m, oof


def scheme_repeated(pipe, X, y, n_repeats=3):
    """Stability check: raw (uncalibrated) fits, ranking metrics only."""
    scores = []
    oof_all = []
    for r in range(n_repeats):
        skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=C.RANDOM_STATE + r)
        oof = np.zeros(len(y))
        for tr, te in skf.split(X, y):
            model = clone(pipe).fit(X.iloc[tr], y[tr])
            oof[te] = predict_proba(model, X.iloc[te])
        thr = C.best_f1_threshold(y, oof)
        scores.append(C.compute_metrics(y, oof, threshold=thr))
        oof_all.append(oof)
    agg = pd.DataFrame(scores)
    out = {k: float(agg[k].mean()) for k in agg.columns if k != "threshold"}
    out["roc_auc_sd"] = float(agg.roc_auc.std())
    out["pr_auc_sd"] = float(agg.pr_auc.std())
    return out, np.mean(oof_all, axis=0)


def run_level(
    df: pd.DataFrame,
    target: str,
    numeric: list[str],
    cats: list[str],
    level_name: str,
    time_col: str = "year",
    temp_cut: int = 2017,
    n_iter: int = 8,
) -> dict:
    X = df[numeric + cats]
    y = df[target].to_numpy().astype(int)
    groups = df.iso3.to_numpy()
    times = df[time_col].to_numpy()
    n_pos, n_neg = int(y.sum()), int((1 - y).sum())
    log(f"\n=== {level_name}: n={len(df)} pos={n_pos} ({n_pos/len(df)*100:.1f}%) "
        f"features={len(numeric + cats)} ===")

    fitted: dict[str, object] = {}
    out: dict[str, dict] = {}
    for spec in C.model_zoo(n_pos, n_neg):
        t0 = time.time()
        pipe, params = tune_model(spec, X, y, groups, numeric, cats, n_iter=n_iter)
        fitted[spec.name] = pipe
        m_temp, p_te, y_te, yr_te, te_mask = scheme_temporal(pipe, X, y, times, temp_cut)
        pd.DataFrame({
            "iso3": df.iso3.to_numpy()[te_mask],
            "year": yr_te,
            "y_true": y_te,
            "p_pred": p_te,
        }).to_csv(
            REP / f"pred_{level_name.split()[0]}_{spec.name.replace(' ', '_')}.csv", index=False
        )
        m_loco, oof_loco = scheme_loco(pipe, X, y, groups)
        m_rep, oof_rep = scheme_repeated(pipe, X, y)
        out[spec.name] = {
            "family": spec.family,
            "best_params": {k: (v if not isinstance(v, np.integer) else int(v))
                            for k, v in params.items()},
            "temporal": m_temp,
            "loco": m_loco,
            "repeated_cv": m_rep,
            "fit_seconds": round(time.time() - t0, 1),
        }
        for scheme, m in (("temporal_holdout", m_temp), ("leave_country_out", m_loco),
                          ("repeated_stratified_cv", m_rep)):
            for metric in ("roc_auc", "pr_auc", "brier", "f1", "precision",
                           "recall", "mcc", "specificity"):
                if metric in m:
                    COMP_ROWS.append({"level": level_name, "scheme": scheme,
                                      "model": spec.name, "metric": metric,
                                      "value": m[metric]})
        log(f"  {spec.name:20s} AUROC {m_temp['roc_auc']:.3f} | PR-AUC "
            f"{m_temp['pr_auc']:.3f} | LOC O PR-AUC {m_loco['pr_auc']:.3f} | "
            f"CV PR-AUC {m_rep['pr_auc']:.3f}  ({time.time()-t0:.0f}s)")
    _ = (p_te, y_te, yr_te, oof_loco, oof_rep)
    return {"metrics": out, "n": len(df), "positives": n_pos}


# --------------------------------------------------------------------------- #
# Chained model (population -> occurrence -> intensity)
# --------------------------------------------------------------------------- #
def run_chain(df: pd.DataFrame, base_model_name: str, best_params: dict | None = None) -> dict:
    log("\n=== Chained pipeline (stage 1 population -> stage 2 occurrence -> stage 3 intensity) ===")
    numeric = [c for c in C.FULL if c in df.columns]
    cats = C.CATEGORICAL
    X = df[numeric + cats]
    y = df.y_occ_next.to_numpy().astype(int)
    groups = df.iso3.to_numpy()
    years = df.year.to_numpy()

    # ---------- Stage 1: forecast next-year log equid stock ----------
    Xn = df[numeric].fillna(df[numeric].median())
    y1 = df.y_log_equids_next.to_numpy()
    ok = ~np.isnan(y1)
    s1_scores = {}
    for name, est in (
        ("Ridge", Ridge(alpha=1.0)),
        ("HistGBR", HistGradientBoostingRegressor(max_iter=300, learning_rate=0.06,
                                                  max_depth=3, random_state=C.RANDOM_STATE)),
    ):
        gkf = GroupKFold(n_splits=5)
        oof = np.full(len(df), np.nan)
        for tr, te in gkf.split(Xn, y1, groups):
            m = clone(est).fit(Xn.iloc[tr][ok[tr]], y1[tr][ok[tr]])
            oof[te] = m.predict(Xn.iloc[te])
        mae = mean_absolute_error(y1[ok], oof[ok])
        r2 = r2_score(y1[ok], oof[ok])
        s1_scores[name] = {
            "mae": float(mae),
            "median_ae": float(median_absolute_error(y1[ok], oof[ok])),
            "spearman": float(spearmanr(y1[ok], oof[ok]).statistic),
            "r2_outlier_sensitive": float(r2),
        }
        df[f"stage1_{name}"] = oof
    best_s1 = min(s1_scores, key=lambda k: s1_scores[k]["mae"])
    df["stage1_equid_pred"] = df[f"stage1_{best_s1}"]
    log(f"  stage-1 best: {best_s1} {s1_scores[best_s1]}")

    # ---------- Stage 2: occurrence with chained feature ----------
    specs = {s.name: s for s in C.model_zoo(int(y.sum()), int((1 - y).sum()))}
    spec = specs[base_model_name]
    res = {"stage1": {"best": best_s1, "scores": s1_scores}, "stage2": {}}

    for tag, cols in (("plain", numeric), ("chained", numeric + ["stage1_equid_pred"])):
        Xv = df[cols + cats]
        # temporal
        tr, te = years <= 2017, years > 2017
        pipe = C.make_pipeline(spec, cols, cats, best_params or {})
        model = fit_calibrated(clone(pipe), Xv[tr], y[tr])
        p_tr, p_te = predict_proba(model, Xv[tr]), predict_proba(model, Xv[te])
        thr = C.best_f1_threshold(y[tr], p_tr)
        mt = C.compute_metrics(y[te], p_te, threshold=thr)
        mt["ece"] = C.expected_calibration_error(y[te], p_te)
        # LOCO
        gkf = GroupKFold(n_splits=5)
        oof = np.zeros(len(y))
        for a, b in gkf.split(Xv, y, groups):
            mm = fit_calibrated(clone(pipe), Xv.iloc[a], y[a])
            oof[b] = predict_proba(mm, Xv.iloc[b])
        ml = C.compute_metrics(y, oof, threshold=C.best_f1_threshold(y, oof))
        ml["ece"] = C.expected_calibration_error(y, oof)
        res["stage2"][tag] = {"temporal": mt, "loco": ml}
        log(f"  stage-2 {tag:8s} temporal PR-AUC {mt['pr_auc']:.3f} | "
            f"AUROC {mt['roc_auc']:.3f} | LOC O PR-AUC {ml['pr_auc']:.3f}")

    # ---------- Stage 3: intensity among positives (hurdle component) ----------
    pos = df[df.y_occ_next == 1]
    Xp = pos[numeric + cats]
    yp = np.log1p(pos.y_count_next.to_numpy())
    reg = Pipeline(
        [
            ("prep", C.build_preprocessor(numeric, cats=cats)),
            ("model", RandomForestRegressor(
                n_estimators=400, min_samples_leaf=2, max_features=0.4,
                random_state=C.RANDOM_STATE, n_jobs=-1)),
        ]
    )
    tr, te = pos.year.to_numpy() <= 2017, pos.year.to_numpy() > 2017
    if len(pos) >= 60 and te.sum() >= 8 and tr.sum() >= 30:
        m3 = reg.fit(Xp[tr], yp[tr])
        pred = m3.predict(Xp[te])
        res["stage3"] = {
            "n_train": int(tr.sum()), "n_test": int(te.sum()),
            "mae": float(mean_absolute_error(yp[te], pred)),
            "median_ae": float(median_absolute_error(yp[te], pred)),
            "spearman": float(spearmanr(yp[te], pred).statistic),
        }
        log(f"  stage-3 intensity  MAE {res['stage3']['mae']:.3f} | "
            f"median AE {res['stage3']['median_ae']:.3f} | rho {res['stage3']['spearman']:.3f}")

    # ---------- Hurdle chain: E[events] = P(occurrence) x E[count | occurrence] ----------
    # Stage-2 temporal model already exists; reuse the pipeline build here.
    Xv = df[numeric + cats]
    ytr, yte = years <= 2017, years > 2017
    pipe = C.make_pipeline(spec, numeric, cats, best_params or {})
    occ = fit_calibrated(clone(pipe), Xv[ytr], y[ytr])
    p_all = predict_proba(occ, Xv)
    mu_all = reg.predict(Xv)
    expected = p_all * np.expm1(mu_all)
    actual = df.y_count_next.to_numpy()
    if yte.sum() > 0:
        rho_chain = float(spearmanr(actual[yte], expected[yte]).statistic)
        res["hurdle"] = {
            "spearman_test": rho_chain,
            "mae_test": float(mean_absolute_error(actual[yte], expected[yte])),
            "spearman_occurrence_only": float(spearmanr(actual[yte], p_all[yte]).statistic),
        }
        # alert-level: how many real events are captured by the top-k% risk cells
        k = max(1, int(0.10 * yte.sum()))
        order = np.argsort(-expected[yte])
        top = np.zeros(yte.sum(), dtype=bool)
        top[order[:k]] = True
        res["hurdle"]["top10pct_alert_precision"] = float(
            actual[yte][top].sum() / max(expected[yte][top].sum(), 1e-9))
        res["hurdle"]["events_captured"] = int(actual[yte][top].sum())
        res["hurdle"]["total_events"] = int(actual[yte].sum())
        log(f"  hurdle chain: rho(events) {rho_chain:.3f} | occurrence-only rho "
            f"{res['hurdle']['spearman_occurrence_only']:.3f} | top-10% alerts capture "
            f"{res['hurdle']['events_captured']}/{res['hurdle']['total_events']} events")
    return res


# --------------------------------------------------------------------------- #
# Ablations (AS settings)
# --------------------------------------------------------------------------- #
def run_ablations(df: pd.DataFrame, model_name: str = "XGBoost") -> dict:
    log("\n=== Ablation settings (AS) ===")
    cats = C.CATEGORICAL
    y = df.y_occ_next.to_numpy().astype(int)
    groups = df.iso3.to_numpy()
    years = df.year.to_numpy()
    spec = {s.name: s for s in C.model_zoo(int(y.sum()), int((1 - y).sum()))}[model_name]
    out = {}
    setups = dict(C.ABLATIONS)
    setups["AS-7 full + surveillance proxy"] = C.FULL + C.SURVEILLANCE_PROXY
    for name, cols in setups.items():
        cols = [c for c in cols if c in df.columns]
        X = df[cols + cats]
        pipe = C.make_pipeline(spec, cols, cats, {})
        tr, te = years <= 2017, years > 2017
        model = fit_calibrated(clone(pipe), X[tr], y[tr])
        p_te = predict_proba(model, X[te])
        m = C.compute_metrics(y[te], p_te, threshold=C.best_f1_threshold(y[tr], predict_proba(model, X[tr])))
        gkf = GroupKFold(n_splits=5)
        oof = np.zeros(len(y))
        for a, b in gkf.split(X, y, groups):
            mm = fit_calibrated(clone(pipe), X.iloc[a], y[a])
            oof[b] = predict_proba(mm, X.iloc[b])
        ml = C.compute_metrics(y, oof, threshold=C.best_f1_threshold(y, oof))
        out[name] = {"n_features": len(cols), "temporal": m, "loco": ml}
        log(f"  {name:34s} k={len(cols):2d} temporal PR-AUC {m['pr_auc']:.3f} "
            f"AUROC {m['roc_auc']:.3f} | LOC O {ml['pr_auc']:.3f}")
    return out


# --------------------------------------------------------------------------- #
# Subgroups + SHAP
# --------------------------------------------------------------------------- #
def run_subgroups(df: pd.DataFrame, oof: np.ndarray, model_label: str) -> list[dict]:
    d = df.copy()
    d["p"] = oof
    rows = []
    for col in ("region", "income"):
        for val, g in d.groupby(col):
            if len(g) < 60 or g.y_occ_next.nunique() < 2:
                continue
            m = C.compute_metrics(g.y_occ_next.to_numpy(), g.p.to_numpy())
            rows.append({"group_by": col, "group": val, "model": model_label,
                         "n": len(g), "positives": int(g.y_occ_next.sum()),
                         "roc_auc": m["roc_auc"], "pr_auc": m["pr_auc"],
                         "brier": m["brier"]})
    return rows


def run_shap(df: pd.DataFrame, model_name: str = "XGBoost") -> list[dict]:
    import shap

    log("\n=== SHAP attribution ===")
    numeric = [c for c in C.FULL if c in df.columns]
    cats = C.CATEGORICAL
    X = df[numeric + cats]
    y = df.y_occ_next.to_numpy().astype(int)
    spec = {s.name: s for s in C.model_zoo(int(y.sum()), int((1 - y).sum()))}[model_name]
    pipe = C.make_pipeline(spec, numeric, cats, {})
    pipe.fit(X, y)
    prep = pipe.named_steps["prep"]
    model = pipe.named_steps["model"]
    Xt = prep.transform(X)
    names = prep.get_feature_names_out()
    Xt = np.asarray(Xt, dtype=float)
    idx = RNG.choice(len(Xt), size=min(600, len(Xt)), replace=False)
    explainer = shap.TreeExplainer(model)
    sv = explainer.shap_values(Xt[idx])
    if isinstance(sv, list):
        sv = sv[-1]
    sv = np.asarray(sv)
    if sv.ndim == 3:
        sv = sv[:, :, -1]
    imp = np.abs(sv).mean(axis=0)
    order = np.argsort(imp)[::-1][:25]
    rows = [{"feature": str(names[i]).replace("num__", "").replace("cat__", ""),
             "mean_abs_shap": float(imp[i])} for i in order]
    np.save(REP / "shap_values.npy", sv)
    np.save(REP / "shap_sample.npy", Xt[idx])
    (REP / "shap_feature_names.json").write_text(json.dumps([str(n) for n in names]))
    for r in rows[:15]:
        log(f"  {r['feature']:38s} {r['mean_abs_shap']:.4f}")
    return rows


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
FAST = os.environ.get("GW_FAST") == "1"


def main() -> None:
    t_start = time.time()
    l1 = load_level1()
    audit = json.loads((PROC / "audit.json").read_text())
    RESULTS["audit"] = {k: v for k, v in audit.items() if k != "missing_pct"}
    RESULTS["audit"]["level1_rows"] = int(len(l1))
    RESULTS["audit"]["level1_positives"] = int(l1.y_occ_next.sum())
    RESULTS["audit"]["level1_prevalence"] = float(l1.y_occ_next.mean())

    numeric = [c for c in C.FULL if c in l1.columns]
    cats = C.CATEGORICAL
    RESULTS["level1"] = run_level(l1, "y_occ_next", numeric, cats, "L1 country-year",
                                  n_iter=2 if FAST else 8)

    # best model by LOC O PR-AUC (geographic generalisation is the honest criterion)
    best = max(RESULTS["level1"]["metrics"].items(),
               key=lambda kv: kv[1]["loco"]["pr_auc"])[0]
    RESULTS["best_model"] = best
    log(f"\n>> best model (leave-country-out PR-AUC): {best}")

    # chain
    RESULTS["chain"] = run_chain(
        l1, best, RESULTS["level1"]["metrics"][best]["best_params"])

    # ablation
    if not FAST:
        RESULTS["ablation"] = run_ablations(l1, "XGBoost")

    # subgroups using the best model's LOC O predictions
    X = l1[numeric + cats]
    spec = {s.name: s for s in C.model_zoo(int(l1.y_occ_next.sum()),
                                           int((1 - l1.y_occ_next).sum()))}[best]
    best_params = RESULTS["level1"]["metrics"][best]["best_params"]
    pipe = C.make_pipeline(spec, numeric, cats, best_params)
    gkf = GroupKFold(n_splits=5)
    y = l1.y_occ_next.to_numpy().astype(int)
    oof = np.zeros(len(y))
    for a, b in gkf.split(X, y, l1.iso3.to_numpy()):
        mm = fit_calibrated(clone(pipe), X.iloc[a], y[a])
        oof[b] = predict_proba(mm, X.iloc[b])
    RESULTS["subgroup"] = run_subgroups(l1, oof, best)
    np.save(REP / "loco_oof.npy", oof)
    l1[["iso3", "year", "y_occ_next"]].assign(pred=oof).to_csv(
        REP / "loco_predictions.csv", index=False)

    # calibration table for the best model (temporal holdout)
    tr, te = l1.year.to_numpy() <= 2017, l1.year.to_numpy() > 2017
    mtemp = fit_calibrated(clone(pipe), X[tr], y[tr])
    p_te = predict_proba(mtemp, X[te])
    RESULTS["calibration"] = {
        "model": best,
        "reliability": C.reliability_curve(y[te], p_te),
        "ece": C.expected_calibration_error(y[te], p_te),
        "brier": float(C.brier_score_loss(y[te], p_te)),
    }

    # SHAP
    if not FAST:
        RESULTS["shap"] = run_shap(l1, "XGBoost")

    # Level 2 (coarse resolution)
    l2 = load_level2(l1)
    RESULTS["level2"] = run_level(
        l2, "y_occ_period", numeric, cats, "L2 country-period", time_col="period_start",
        temp_cut=2010, n_iter=2 if FAST else 6,
    )

    pd.DataFrame(COMP_ROWS).to_csv(REP / "model_comparison.csv", index=False)
    RESULTS["runtime_seconds"] = round(time.time() - t_start, 1)
    (REP / "results.json").write_text(json.dumps(RESULTS, indent=2, default=str))
    log(f"\nDone in {RESULTS['runtime_seconds']/60:.1f} min -> reports/results.json")


if __name__ == "__main__":
    main()
