"""Extract livestock stocks (equines + ruminants) from the FAOSTAT bulk archive.

The FAOSTAT normalized CSV is ~545 MB uncompressed, so it is streamed from the
zip and filtered instead of being loaded into memory.

Run:  .venv/bin/python src/01c_extract_faostat.py
"""
from __future__ import annotations

import csv
import io
import pathlib
import time
import urllib.request
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)
URL = (
    "https://bulks-faostat.fao.org/production/"
    "Production_Crops_Livestock_E_All_Data_(Normalized).zip"
)
ITEMS = {
    "1096": "Horses",
    "1107": "Asses",
    "1110": "Mules and hinnies",
    "1126": "Camels",
    "866": "Cattle",
    "976": "Sheep",
    "1016": "Goats",
}


def download(dest: pathlib.Path) -> None:
    if dest.exists() and dest.stat().st_size > 1_000_000:
        print(f"cached {dest.name} ({dest.stat().st_size/1e6:.0f} MB)")
        return
    print("downloading FAOSTAT bulk archive ...")
    urllib.request.urlretrieve(URL, dest)
    print(f"saved {dest.name} ({dest.stat().st_size/1e6:.0f} MB)")


def main() -> None:
    zpath = RAW / "faostat_crops_livestock.zip"
    download(zpath)
    out = RAW / "faostat_stocks_raw.csv"
    member = "Production_Crops_Livestock_E_All_Data_(Normalized).csv"
    t0 = time.time()
    zf = zipfile.ZipFile(zpath)
    handle = io.TextIOWrapper(zf.open(member), encoding="utf-8-sig", newline="")
    reader = csv.DictReader(handle)
    n = 0
    with out.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["Area", "Item", "Element", "Year", "Unit", "Value", "Flag"])
        for row in reader:
            if row["Item Code"] in ITEMS and row["Element"] == "Stocks":
                writer.writerow([
                    row["Area"], row["Item"], row["Element"], row["Year"],
                    row["Unit"], row["Value"], row["Flag"],
                ])
                n += 1
    print(f"{n} stock rows -> {out.name} in {time.time()-t0:.1f}s")


if __name__ == "__main__":
    main()
