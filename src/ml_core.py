"""Shared machinery for the GlandersWatch chained multi-level evaluation.

Contents
--------
FEATURES          feature groups used by the ablation settings (AS-1 .. AS-6)
build_preprocessor  leakage-safe column transformer
model_zoo          the six model families (five core + logistic baseline)
metrics            discrimination / calibration / threshold metrics
schemes            temporal holdout, leave-country-out, repeated stratified CV
"""
from __future__ import annotations

import warnings
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import ExtraTreesClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    f1_score,
    log_loss,
    matthews_corrcoef,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier

warnings.filterwarnings("ignore")
RANDOM_STATE = 42

# --------------------------------------------------------------------------- #
# Feature groups
# --------------------------------------------------------------------------- #
HISTORY = [
    "occ_lag1", "occ_lag2", "occ_count_lag1", "occ_count_5y",
    "years_since_last", "global_occ_share", "region_occ_share",
]
POPULATION = [
    "log_equids", "log_livestock", "equid_share", "equid_density",
    "equid_growth_1y", "equid_growth_3y", "horses", "asses", "mules",
    "cattle", "goats", "sheep", "camels", "livestock_prod_index",
]
CLIMATE = [
    "temp_mean", "temp_max", "temp_min", "precip_sum", "precip_cv",
    "humidity", "wind", "temp_mean_anom", "precip_sum_anom", "humidity_anom",
]
SOCIO = [
    "gdp_pc", "rural_pct", "agri_land_pct", "agri_va_pct_gdp", "internet_pct",
    "fertilizer_pct", "life_expectancy", "pop_total", "pop_density",
]
GEO = ["abs_lat", "lon"]
CATEGORICAL = ["region", "income"]

FULL = HISTORY + POPULATION + CLIMATE + SOCIO + GEO
CHAIN_FEATURE = "stage1_equid_pred"

ABLATIONS = {
    "AS-1 history only": HISTORY,
    "AS-2 population only": POPULATION,
    "AS-3 climate only": CLIMATE,
    "AS-4 socio-geography": SOCIO + GEO,
    "AS-5 history+population": HISTORY + POPULATION,
    "AS-6 full (all groups)": FULL,
}
# AS-7 (surveillance-bias probe) is built separately: full + research-output proxy.
SURVEILLANCE_PROXY = ["equine_pub_count", "total_pub_count"]


def build_preprocessor(
    numeric: list[str], scale: bool = False, cats: list[str] | None = None
) -> ColumnTransformer:
    num_steps = [("imp", SimpleImputer(strategy="median", add_indicator=True))]
    if scale:
        num_steps.append(("sc", StandardScaler()))
    blocks = [("num", Pipeline(num_steps), numeric)]
    if cats:
        blocks.append(
            (
                "cat",
                Pipeline(
                    [
                        ("imp", SimpleImputer(strategy="most_frequent")),
                        ("oh", OneHotEncoder(handle_unknown="ignore", min_frequency=5)),
                    ]
                ),
                cats,
            )
        )
    return ColumnTransformer(blocks, remainder="drop")


# --------------------------------------------------------------------------- #
# Model zoo
# --------------------------------------------------------------------------- #
@dataclass
class ModelSpec:
    name: str
    family: str
    factory: object
    param_dist: dict = field(default_factory=dict)
    scale: bool = False
    calibrate: bool = True


N_POS = 172  # used only to size scale_pos_weight defaults; overwritten at runtime


def model_zoo(n_pos: int, n_neg: int) -> list[ModelSpec]:
    spw = max(n_neg / max(n_pos, 1), 1.0)
    return [
        ModelSpec(
            "Logistic Regression",
            "linear",
            lambda **kw: LogisticRegression(
                max_iter=4000, class_weight="balanced", random_state=RANDOM_STATE, **kw
            ),
            {"C": [0.01, 0.1, 0.3, 1.0, 3.0], "penalty": ["l2"], "solver": ["lbfgs"]},
            scale=True,
        ),
        ModelSpec(
            "Decision Tree",
            "tree",
            lambda **kw: DecisionTreeClassifier(
                class_weight="balanced", random_state=RANDOM_STATE, **kw
            ),
            {
                "max_depth": [2, 3, 4, 5, 7],
                "min_samples_leaf": [1, 5, 10, 20, 40],
                "criterion": ["gini", "entropy"],
            },
        ),
        ModelSpec(
            "Random Forest",
            "bagged trees",
            lambda **kw: RandomForestClassifier(
                n_estimators=500, class_weight="balanced_subsample",
                random_state=RANDOM_STATE, n_jobs=-1, **kw
            ),
            {
                "max_depth": [4, 6, 8, None],
                "min_samples_leaf": [1, 3, 5, 10],
                "max_features": ["sqrt", 0.3],
            },
        ),
        ModelSpec(
            "Extra Trees",
            "bagged trees",
            lambda **kw: ExtraTreesClassifier(
                n_estimators=500, class_weight="balanced_subsample",
                random_state=RANDOM_STATE, n_jobs=-1, **kw
            ),
            {
                "max_depth": [4, 6, 8, None],
                "min_samples_leaf": [1, 3, 5, 10],
                "max_features": ["sqrt", 0.3],
            },
        ),
        ModelSpec(
            "XGBoost",
            "boosted trees",
            lambda **kw: __import__("xgboost").XGBClassifier(
                n_estimators=400, learning_rate=0.05, subsample=0.9,
                colsample_bytree=0.8, scale_pos_weight=spw, eval_metric="logloss",
                tree_method="hist", random_state=RANDOM_STATE, n_jobs=-1, **kw
            ),
            {
                "max_depth": [2, 3, 4, 5],
                "min_child_weight": [1, 3, 5, 10],
                "reg_lambda": [0.5, 1.0, 3.0],
            },
        ),
        ModelSpec(
            "LightGBM",
            "boosted trees",
            lambda **kw: __import__("lightgbm").LGBMClassifier(
                n_estimators=400, learning_rate=0.05, subsample=0.9,
                colsample_bytree=0.8, class_weight="balanced", random_state=RANDOM_STATE,
                n_jobs=-1, verbose=-1, **kw
            ),
            {
                "num_leaves": [7, 15, 31],
                "min_child_samples": [5, 10, 20, 40],
                "reg_lambda": [0.0, 1.0, 3.0],
            },
        ),
    ]


def make_pipeline(spec: ModelSpec, numeric: list[str], cats: list[str], params: dict):
    pipe = Pipeline(
        [
            ("prep", build_preprocessor(numeric, scale=spec.scale, cats=cats)),
            ("model", spec.factory()),
        ]
    )
    if params:
        pipe.set_params(**{f"model__{k}": v for k, v in params.items()})
    return pipe


# --------------------------------------------------------------------------- #
# Metrics
# --------------------------------------------------------------------------- #
def best_f1_threshold(y: np.ndarray, p: np.ndarray) -> float:
    grid = np.unique(np.round(np.clip(p, 0, 1), 4))
    if len(grid) > 400:
        grid = np.unique(np.quantile(grid, np.linspace(0, 1, 400)))
    best, thr = -1.0, 0.5
    for t in grid:
        f = f1_score(y, (p >= t).astype(int), zero_division=0)
        if f > best:
            best, thr = f, float(t)
    return thr


def compute_metrics(y: np.ndarray, p: np.ndarray, threshold: float | None = None) -> dict:
    y = np.asarray(y).astype(int)
    p = np.asarray(p, dtype=float)
    out: dict[str, float] = {}
    out["n"] = int(len(y))
    out["positives"] = int(y.sum())
    out["roc_auc"] = float(roc_auc_score(y, p)) if y.min() != y.max() else float("nan")
    out["pr_auc"] = float(average_precision_score(y, p)) if y.min() != y.max() else float("nan")
    out["brier"] = float(brier_score_loss(y, np.clip(p, 1e-6, 1 - 1e-6)))
    out["log_loss"] = float(log_loss(y, np.clip(p, 1e-6, 1 - 1e-6), labels=[0, 1]))
    if threshold is None:
        threshold = best_f1_threshold(y, p)
    pred = (p >= threshold).astype(int)
    out["threshold"] = float(threshold)
    out["precision"] = float(precision_score(y, pred, zero_division=0))
    out["recall"] = float(recall_score(y, pred, zero_division=0))
    out["specificity"] = float(((pred == 0) & (y == 0)).sum() / max((y == 0).sum(), 1))
    out["f1"] = float(f1_score(y, pred, zero_division=0))
    out["mcc"] = float(matthews_corrcoef(y, pred)) if len(np.unique(pred)) > 1 else 0.0
    out["false_alerts"] = int(((pred == 1) & (y == 0)).sum())
    out["missed_events"] = int(((pred == 0) & (y == 1)).sum())
    out["alerts_sent"] = int(pred.sum())
    return out


def reliability_curve(y: np.ndarray, p: np.ndarray, n_bins: int = 8) -> list[dict]:
    y = np.asarray(y).astype(int)
    p = np.asarray(p, dtype=float)
    edges = np.quantile(p, np.linspace(0, 1, n_bins + 1))
    edges = np.unique(edges)
    out = []
    for lo, hi in zip(edges[:-1], edges[1:]):
        m = (p >= lo) & (p <= hi)
        if m.sum() < 5:
            continue
        out.append(
            {
                "bin_low": float(lo),
                "bin_high": float(hi),
                "mean_pred": float(p[m].mean()),
                "observed": float(y[m].mean()),
                "n": int(m.sum()),
            }
        )
    return out


def expected_calibration_error(y: np.ndarray, p: np.ndarray, n_bins: int = 10) -> float:
    curve = reliability_curve(y, p, n_bins)
    total = sum(c["n"] for c in curve) or 1
    return float(sum(abs(c["observed"] - c["mean_pred"]) * c["n"] for c in curve) / total)


def bootstrap_ci(
    y: np.ndarray, p: np.ndarray, metric: str = "pr_auc",
    n_boot: int = 1000, seed: int = 7
) -> tuple[float, float]:
    """Percentile bootstrap CI for a ranking metric (resamples observations)."""
    y = np.asarray(y).astype(int)
    p = np.asarray(p, dtype=float)
    rng = np.random.RandomState(seed)
    vals = []
    n = len(y)
    for _ in range(n_boot):
        idx = rng.randint(0, n, n)
        yy, pp = y[idx], p[idx]
        if yy.min() == yy.max():
            continue
        vals.append(
            roc_auc_score(yy, pp) if metric == "roc_auc" else average_precision_score(yy, pp)
        )
    if not vals:
        return (float("nan"), float("nan"))
    return (float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5)))
