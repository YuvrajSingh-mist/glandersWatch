"""Write the model matrix as a formatted Excel workbook for inspection.

Run:  .venv/bin/python src/12_export_matrix_xlsx.py

Produces data/processed/model_matrix.xlsx next to the CSV. Same rows and columns;
this is only a reading aid, so nothing downstream depends on it. The workbook has
a frozen header, a filter on every column, sensible number formats and a second
sheet summarising the matrix.
"""
from __future__ import annotations

import pathlib

import pandas as pd
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "processed" / "model_matrix.csv"
OUT = ROOT / "data" / "processed" / "model_matrix.xlsx"

IDENTIFIERS = ["iso3", "year"]
TARGET = "y_occ_next"
CATEGORICAL = ["region", "income"]

# Columns whose values are counts, kept as whole numbers.
INTEGER_HINTS = {
    "horses", "asses", "mules", "cattle", "goats", "sheep", "camels",
    "occ_count_lag1", "occ_count_5y", "year",
}


def summary(df: pd.DataFrame) -> pd.DataFrame:
    rows = [
        ("Rows", len(df)),
        ("Feature columns", df.shape[1] - len(IDENTIFIERS) - 1),
        ("  numeric", df.shape[1] - len(IDENTIFIERS) - 1 - len(CATEGORICAL)),
        ("  categorical", len(CATEGORICAL)),
        ("Target column", TARGET),
        ("Positives", int(df[TARGET].sum())),
        ("Negatives", int((df[TARGET] == 0).sum())),
        ("Prevalence %", round(df[TARGET].mean() * 100, 2)),
        ("Countries", int(df.iso3.nunique())),
        ("Year range", f"{df.year.min()} to {df.year.max()}"),
        ("Missing cells", int(df.isna().sum().sum())),
        ("Source", "data/processed/model_matrix.csv"),
    ]
    return pd.DataFrame(rows, columns=["Property", "Value"])


def main() -> None:
    df = pd.read_csv(SRC)

    with pd.ExcelWriter(OUT, engine="openpyxl") as xw:
        df.to_excel(xw, sheet_name="model_matrix", index=False)
        summary(df).to_excel(xw, sheet_name="summary", index=False)

        wb = xw.book
        ws = wb["model_matrix"]

        header_fill = PatternFill("solid", fgColor="1F3864")
        header_font = Font(bold=True, color="FFFFFF", size=10)
        for cell in ws[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(vertical="center", wrap_text=False)

        # number formats per column
        for idx, name in enumerate(df.columns, start=1):
            letter = get_column_letter(idx)
            for row in range(2, len(df) + 2):
                cell = ws.cell(row=row, column=idx)
                if name in INTEGER_HINTS:
                    cell.number_format = "0"
                elif name in CATEGORICAL or name == "iso3":
                    pass
                elif name == TARGET:
                    cell.number_format = "0"
                else:
                    cell.number_format = "0.0000"

        # readable widths, capped for the long free-text columns
        for idx, name in enumerate(df.columns, start=1):
            letter = get_column_letter(idx)
            longest = max(len(str(name)), *(len(str(v)) for v in df[name].head(200)))
            ws.column_dimensions[letter].width = min(max(10, longest + 2), 26)

        ws.freeze_panes = "C2"

        table = Table(displayName="ModelMatrix",
                      ref=f"A1:{get_column_letter(df.shape[1])}{len(df) + 1}")
        table.tableStyleInfo = TableStyleInfo(
            name="TableStyleLight9", showRowStripes=True, showColumnStripes=False)
        ws.add_table(table)

        ws2 = wb["summary"]
        ws2.column_dimensions["A"].width = 22
        ws2.column_dimensions["B"].width = 40
        for cell in ws2[1]:
            cell.fill = header_fill
            cell.font = header_font

    print(f"wrote {OUT.relative_to(ROOT)}")
    print(f"  rows {len(df):,} | cols {df.shape[1]} | positives {int(df[TARGET].sum())}")


if __name__ == "__main__":
    main()
