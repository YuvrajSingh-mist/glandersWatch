"""SHAP-based feature selection, computed on the training period only.

The ranking is produced by fitting XGBoost on the temporal training window
(2005-2017) and taking mean absolute SHAP values there. The held-out years are
never used, so choosing features from this ranking cannot leak into the
temporal-holdout evaluation.

The result is written to reports/selected_features.json and consumed by the
training script, so one run of the pipeline reproduces both the selection and
every number that follows from it.

Run standalone:  .venv/bin/python src/shap_select.py
"""
from __future__ import annotations

import json
import pathlib
import sys

import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import ml_core as C  # noqa: E402

REP = ROOT / "reports"
TRAIN_END = 2017
TOP_K = 8


def rank_by_shap(
    df: pd.DataFrame,
    y_col: str = "y_occ_next",
    train_end: int = TRAIN_END,
    sample: int = 600,
    seed: int = C.RANDOM_STATE,
) -> list[dict]:
    """Fit on the training years only and rank numeric features by mean |SHAP|."""
    import shap

    train = df[df.year <= train_end]
    numeric = [c for c in C.FULL if c in df.columns]
    cats = C.CATEGORICAL
    X = train[numeric + cats]
    y = train[y_col].to_numpy().astype(int)

    spec = {s.name: s for s in C.model_zoo(int(y.sum()), int((1 - y).sum()))}["XGBoost"]
    pipe = C.make_pipeline(spec, numeric, cats, {})
    pipe.fit(X, y)

    prep = pipe.named_steps["prep"]
    model = pipe.named_steps["model"]
    Xt = np.asarray(prep.transform(X), dtype=float)
    names = [str(n).replace("num__", "").replace("cat__", "") for n in prep.get_feature_names_out()]

    rng = np.random.RandomState(seed)
    idx = rng.choice(len(Xt), size=min(sample, len(Xt)), replace=False)
    sv = shap.TreeExplainer(model).shap_values(Xt[idx])
    if isinstance(sv, list):
        sv = sv[-1]
    sv = np.asarray(sv)
    if sv.ndim == 3:
        sv = sv[:, :, -1]

    imp = np.abs(sv).mean(axis=0)
    order = np.argsort(imp)[::-1]
    rows = [
        {"feature": names[i], "mean_abs_shap": float(imp[i]), "rank": r + 1}
        for r, i in enumerate(order)
    ]
    return rows


def select(rows: list[dict], k: int = TOP_K) -> dict:
    """Return exactly k features, and nothing else.

    Categorical columns are left out on purpose: the report states a set of eight
    features, the exported dataset has those eight columns, and the model is
    trained on the same eight. Carrying region and income in the model while
    omitting them from the dataset would mean the artefact and the experiment
    disagree.
    """
    numeric_ranked = [r["feature"] for r in rows if r["feature"] in C.FULL]
    chosen = numeric_ranked[:k]
    return {
        "top_k": k,
        "train_end": TRAIN_END,
        "numeric": chosen,
        "categorical": [],          # exactly k features, no extras
        "ranking": rows,
        "n_candidates": len(numeric_ranked),
    }


def main() -> dict:
    from importlib import util as _util

    spec = _util.spec_from_file_location(
        "train_evaluate", ROOT / "src" / "03_train_evaluate.py")
    TE = _util.module_from_spec(spec)
    spec.loader.exec_module(TE)

    df = TE.load_level1()
    rows = rank_by_shap(df)
    payload = select(rows)
    (REP / "selected_features.json").write_text(json.dumps(payload, indent=2))

    n_train = int((df.year <= TRAIN_END).sum())
    print(f"ranked on {n_train:,} training rows (year <= {TRAIN_END}), "
          f"{payload['n_candidates']} candidates")
    print(f"selected top {payload['top_k']} numeric + {len(payload['categorical'])} categorical")
    cum = 0.0
    total = sum(r["mean_abs_shap"] for r in rows if r["feature"] in C.FULL)
    for r in rows[:payload["top_k"]]:
        if r["feature"] not in C.FULL:
            continue
        cum += r["mean_abs_shap"]
        print(f"  {r['rank']:2d}. {r['feature']:24s} {r['mean_abs_shap']:.4f}")
    print(f"cumulative importance of the selection: {cum / total * 100:.1f}%")
    print(f"wrote {(REP / 'selected_features.json').relative_to(ROOT)}")
    return payload


if __name__ == "__main__":
    main()
