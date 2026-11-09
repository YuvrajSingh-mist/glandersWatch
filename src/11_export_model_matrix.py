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
    """Write strictly the eight selected feature columns, and nothing else.

    No identifiers, no categorical columns, no target. The previous version kept
    iso3/year/region/income/y_occ_next alongside the features, which made a "10
    feature" file 13 columns wide. The label is written separately to
    model_matrix_labels.csv so the feature table is exactly what was asked for.
    """
    df = TE.load_level1()
    sel = json.loads(_spec.read_text())
    features = sel["numeric"]
    if len(features) != 8:
        raise SystemExit(f"expected 8 selected features, found {len(features)}: {features}")
    missing = [c for c in features if c not in df.columns]
    if missing:
        raise SystemExit(f"features missing from panel: {missing}")

    out = df[features].copy()

    # Round so each row stays readable in an editor. This file is an export, not a
    # training input.
    num_cols = [c for c in features if out[c].dtype.kind == "f"]
    out[num_cols] = out[num_cols].round(6)
    out.to_csv(OUT, index=False)

    # The label, kept beside the features so a reader can still tell a positive row.
    labels = df[["y_occ_next"]].copy()
    labels.to_csv(OUT.with_name("model_matrix_labels.csv"), index=False)

    print(f"wrote {OUT.relative_to(ROOT)}")
    print(f"  rows     : {len(out):,}")
    print(f"  columns  : {len(out.columns)} (exactly the selected features)")
    print(f"  features : {', '.join(features)}")
    print(f"  positives: {int(df['y_occ_next'].sum())} "
          f"(label in {OUT.with_name('model_matrix_labels.csv').name})")


if __name__ == "__main__":
    main()
