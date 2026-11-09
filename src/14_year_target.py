"""Alternative target: predict the YEAR of a country's next glanders report.

Run:  .venv/bin/python src/14_year_target.py

This exists to test the proposal that the calendar year should be the prediction
rather than the binary next-year label. It reports what such a model actually
achieves, and the diagnostics needed to judge whether the number is meaningful.

Three targets are compared, because "predict the year" is ambiguous:

  A. year of the next reported event   (regression, one row per country)
  B. years until the next event        (regression, time-to-event framing)
  C. ever reports glanders             (binary, the country-level question)

The distinction matters: A is trivially predictable from reporting trends, B is
the survival formulation that matches the question a planner asks, and C is the
coarse classification already reported in the main results.
"""
from __future__ import annotations

import json
import pathlib
import sys

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import LeaveOneOut, cross_val_predict
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import ml_core as C  # noqa: E402

PROC, REP = ROOT / "data" / "processed", ROOT / "reports"
WINDOW = (2006, 2023)


def panel() -> pd.DataFrame:
    from importlib import util as _u
    spec = _u.spec_from_file_location("train_evaluate", ROOT / "src" / "03_train_evaluate.py")
    TE = _u.module_from_spec(spec)
    spec.loader.exec_module(TE)
    return TE.load_level1()


def build_targets(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    sel = json.loads((REP / "selected_features.json").read_text())
    feats = [f for f in sel["numeric"] if f in df.columns]

    # per country: first event, last event, and the mean feature vector
    ev = df[df.occ_any == 1].groupby("iso3").year.agg(first_event="min", last_event="max")
    base = df.groupby("iso3")[feats].mean(numeric_only=True)
    out = base.join(ev).reset_index()

    # A: year of the last observed event, used as the "next" event proxy
    out["year_target"] = out["last_event"]
    # B: years from the first observation to the first event; right-censored where none
    out["years_to_event"] = (out["first_event"] - WINDOW[0]).astype(float)

    return out, feats


def fit_report(X: np.ndarray, y: np.ndarray, label: str) -> dict:
    models = {
        "Linear regression": Pipeline([("imp", SimpleImputer(strategy="median")),
                                       ("sc", StandardScaler()),
                                       ("m", LinearRegression())]),
        "Random forest": Pipeline([("imp", SimpleImputer(strategy="median")),
                                   ("m", RandomForestRegressor(
                                       n_estimators=300, min_samples_leaf=2,
                                       random_state=C.RANDOM_STATE, n_jobs=-1))]),
    }
    loo = LeaveOneOut()
    out = {}
    for name, pipe in models.items():
        pred = cross_val_predict(pipe, X, y, cv=loo)
        out[name] = {
            "mae": float(mean_absolute_error(y, pred)),
            "r2": float(r2_score(y, pred)),
        }
        print(f"  {label} / {name:18s} MAE {out[name]['mae']:.2f} yr | R2 {out[name]['r2']:+.3f}")

    # baseline: always predict the training mean
    base_pred = np.full_like(y, y.mean(), dtype=float)
    out["mean_baseline"] = {"mae": float(mean_absolute_error(y, base_pred)), "r2": 0.0}
    print(f"  {label} / {'predict the mean':18s} MAE {out['mean_baseline']['mae']:.2f} yr")
    return out


def main() -> None:
    df = panel()
    out, feats = build_targets(df)
    print(f"countries: {len(out)} | with a recorded event: {int(out.last_event.notna().sum())}")
    print(f"window: {WINDOW[0]}-{WINDOW[1]} | features: {len(feats)}\n")

    # --- A: year of the event, only where an event exists --------------------
    ev = out.dropna(subset=["year_target"]).copy()
    print(f"A. Year of the reported event (n={len(ev)})")
    res_a = fit_report(ev[feats].to_numpy(float), ev["year_target"].to_numpy(float),
                       "year")

    print("\n   Why this number is not useful:")
    print(f"     target range  : {ev.year_target.min():.0f} - {ev.year_target.max():.0f}")
    print(f"     target sd     : {ev.year_target.std():.2f} years")
    print(f"     share in the last 5 years of the window: "
          f"{(ev.year_target >= 2019).mean()*100:.0f}%")
    corr = np.corrcoef(ev["internet_pct"].fillna(ev["internet_pct"].median()),
                       ev.year_target)[0, 1]
    print(f"     corr(internet_pct, year) = {corr:+.2f}  "
          "(a proxy for reporting growth, not biology)")

    # --- B: years to first event -------------------------------------------
    b = out.dropna(subset=["years_to_event"]).copy()
    print(f"\nB. Years from {WINDOW[0]} to the first recorded event (n={len(b)})")
    res_b = fit_report(b[feats].to_numpy(float), b["years_to_event"].to_numpy(float),
                       "years_to_event")

    # --- C: binary, for reference ------------------------------------------
    print("\nC. Ever reports glanders (binary, already in the main results)")

    payload = {
        "window": list(WINDOW),
        "features": feats,
        "n_countries": int(len(out)),
        "n_with_event": int(out.last_event.notna().sum()),
        "target_a_year": res_a,
        "target_b_years_to_event": res_b,
        "target_a_target_range": [float(ev.year_target.min()), float(ev.year_target.max())],
        "target_a_target_sd": float(ev.year_target.std()),
        "internet_year_corr": float(corr),
    }
    (REP / "year_target.json").write_text(json.dumps(payload, indent=2))
    print(f"\nwrote {(REP / 'year_target.json').relative_to(ROOT)}")


if __name__ == "__main__":
    main()
