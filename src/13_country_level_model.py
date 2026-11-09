"""Country-level view: predict which countries are glanders-reporting countries.

Run:  .venv/bin/python src/13_country_level_model.py

The country-year model in 03_train_evaluate.py asks whether a country reports glanders
in one particular year. That is a hard, sparse question: 169 positives over 2,880 rows.
This script asks the coarser question a surveillance planner actually acts on: is this
country a glanders country at all, over the whole observation window?

One row per country, features averaged over 2005-2023, target 1 if the country reports
glanders in any year. Because there is one row per country there is no country grouping
to hold out, so validation is leave-one-out over countries.

The country code itself is deliberately NOT used as a feature. See the note printed at
the end: as a label encoder it cannot generalise to an unseen country, and in-sample it
memorises reporting capacity, which is the confound the report already identifies.
"""
from __future__ import annotations

import json
import pathlib
import sys

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.model_selection import LeaveOneOut
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import ml_core as C  # noqa: E402

PROC, REP = ROOT / "data" / "processed", ROOT / "reports"


def build() -> tuple[pd.DataFrame, list[str]]:
    panel = pd.read_csv(PROC / "country_year_panel.csv")
    panel = panel[(panel.equine_country == 1) & panel.year.between(2005, 2023)]

    from importlib import util as _u
    spec = _u.spec_from_file_location("train_evaluate", ROOT / "src" / "03_train_evaluate.py")
    TE = _u.module_from_spec(spec)
    spec.loader.exec_module(TE)
    l1 = TE.load_level1()

    sel = json.loads((REP / "selected_features.json").read_text())
    feats = [f for f in sel["numeric"] if f in l1.columns]

    num = l1.groupby("iso3")[feats].mean(numeric_only=True)
    target = l1.groupby("iso3")["y_occ_next"].max().rename("ever_positive")
    df = num.join(target).reset_index()
    df = df.dropna(subset=["ever_positive"])
    df["ever_positive"] = df["ever_positive"].astype(int)
    return df, feats


def main() -> None:
    df, feats = build()
    X = df[feats].to_numpy(dtype=float)
    y = df.ever_positive.to_numpy()

    print(f"country-level rows: {len(df)} | positives: {int(y.sum())} "
          f"({y.mean()*100:.1f}%) | features: {len(feats)}")

    models = {
        "Logistic regression": Pipeline([
            ("imp", SimpleImputer(strategy="median")),
            ("sc", StandardScaler()),
            ("m", LogisticRegression(max_iter=4000, class_weight="balanced")),
        ]),
        "Random forest": Pipeline([
            ("imp", SimpleImputer(strategy="median")),
            ("m", RandomForestClassifier(n_estimators=400, min_samples_leaf=2,
                                         class_weight="balanced",
                                         random_state=C.RANDOM_STATE, n_jobs=-1)),
        ]),
    }

    out = {}
    loo = LeaveOneOut()
    for name, pipe in models.items():
        proba = np.zeros(len(y))
        for tr, te in loo.split(X):
            from sklearn.base import clone
            proba[te] = clone(pipe).fit(X[tr], y[tr]).predict_proba(X[te])[:, 1]
        auc = roc_auc_score(y, proba)
        ap = average_precision_score(y, proba)
        out[name] = {"roc_auc": float(auc), "pr_auc": float(ap)}
        print(f"  {name:22s} leave-one-out ROC-AUC {auc:.3f} | PR-AUC {ap:.3f}")

    RESULTS = {
        "n_countries": int(len(df)),
        "positives": int(y.sum()),
        "prevalence": float(y.mean()),
        "features": feats,
        "n_features": len(feats),
        "models": out,
    }
    (REP / "country_level.json").write_text(json.dumps(RESULTS, indent=2))

    df[["iso3", "ever_positive"] + feats].to_csv(PROC / "country_level_matrix.csv", index=False)
    print(f"wrote {(REP / 'country_level.json').relative_to(ROOT)}")
    print(f"wrote {(PROC / 'country_level_matrix.csv').relative_to(ROOT)}")
    print("\nNote: iso3 was not used as a feature. As an identifier it cannot transfer to an "
          "unseen country, and in-sample it just encodes reporting capacity.")


if __name__ == "__main__":
    main()
