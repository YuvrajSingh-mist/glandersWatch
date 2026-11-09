"""Export the exact matrix that is fed to the models.

Run:  .venv/bin/python src/11_export_model_matrix.py

Writes data/processed/model_matrix.csv: one row per country-year, the 44 feature
columns in the order the pipeline receives them, and the binary next-year label.

The rows and columns come from the same loader and the same feature-group
constants that the training script uses, so this file cannot drift from what the
models actually saw. Floating point values are written to 6 decimal places: this
file is an export for inspection, not an input to training (the training script
reads the panel and derives the matrix itself), so rounding here cannot change
any reported number, and it keeps each row readable.
"""
from __future__ import annotations

import importlib.util
import json
import pathlib
import sys

import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import ml_core as C  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "train_evaluate", ROOT / "src" / "03_train_evaluate.py")
TE = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(TE)

OUT = ROOT / "data" / "processed" / "model_matrix.csv"

IDENTIFIERS = ["iso3", "year"]
TARGET = "y_occ_next"

_spec = ROOT / "reports" / "selected_features.json"


def feature_list() -> list[str]:
    """The features the reported models use: the SHAP-selected set, not all candidates."""
    if _spec.exists():
        sel = json.loads(_spec.read_text())
        return sel["numeric"] + sel["categorical"]
    return C.FULL + C.CATEGORICAL


def main() -> None:
    df = TE.load_level1()
    FEATURES = feature_list()

    missing = [c for c in FEATURES if c not in df.columns]
    if missing:
        raise SystemExit(f"features missing from panel: {missing}")

    out = df[IDENTIFIERS + FEATURES + [TARGET]].copy()

    # Round the numeric features so each row stays readable in an editor. Integer
    # stock counts are left exact. This file is an export, not a training input.
    num_cols = [c for c in FEATURES if c in out.columns
                and out[c].dtype.kind == "f"]
    out[num_cols] = out[num_cols].round(6)

    out.to_csv(OUT, index=False)

    print(f"wrote {OUT.relative_to(ROOT)}")
    print(f"  rows      : {len(out):,}")
    n_num = sum(1 for f in FEATURES if f in C.FULL)
    print(f"  features  : {len(FEATURES)} ({n_num} numeric + {len(FEATURES) - n_num} categorical)")
    print(f"  positives : {int(out[TARGET].sum())}")
    print(f"  prevalence: {out[TARGET].mean() * 100:.2f}%")
    print(f"  countries : {out.iso3.nunique()}")
    print(f"  years     : {out.year.min()} to {out.year.max()}")
    print(f"  size      : {OUT.stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    main()
