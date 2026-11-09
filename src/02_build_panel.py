"""Build the novel country-year glanders panel from the four unused sources.

Level 0 of the pipeline: dataset assembly + audit.

Outputs
-------
data/processed/literature_events.csv   text-mined occurrence events (animal history)
data/processed/country_year_panel.csv  modelling panel (features at t, targets at t+1)
data/processed/audit.json              dataset-level audit numbers
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from text_extract import (  # noqa: E402
    OCCURRENCE_TERMS,
    REVIEW_TERMS,
    extract_countries,
    extract_years,
)

ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW, PROC = ROOT / "data" / "raw", ROOT / "data" / "processed"
PROC.mkdir(parents=True, exist_ok=True)

START_YEAR, END_YEAR = 2005, 2024
SENT_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9])")

# --------------------------------------------------------------------------- #
# ISO3 helper
# --------------------------------------------------------------------------- #
import pycountry  # noqa: E402

_OVERRIDES = {
    "Bolivia (Plurinational State of)": "BOL",
    "Venezuela (Bolivarian Republic of)": "VEN",
    "Iran (Islamic Republic of)": "IRN",
    "Syrian Arab Republic": "SYR",
    "Republic of Moldova": "MDA",
    "United Republic of Tanzania": "TZA",
    "Democratic People's Republic of Korea": "PRK",
    "Republic of Korea": "KOR",
    "China, mainland": "CHN",
    "China, Hong Kong SAR": "HKG",
    "China, Taiwan Province of": "TWN",
    "Netherlands (Kingdom of the)": "NLD",
    "Türkiye": "TUR",
    "Czechia": "CZE",
    "Eswatini": "SWZ",
    "Cabo Verde": "CPV",
    "Côte d'Ivoire": "CIV",
    "Lao People's Democratic Republic": "LAO",
    "Viet Nam": "VNM",
    "Russian Federation": "RUS",
    "United States of America": "USA",
    "United Kingdom of Great Britain and Northern Ireland": "GBR",
    "Micronesia (Federated States of)": "FSM",
    "Brunei Darussalam": "BRN",
    "Timor-Leste": "TLS",
    "Palestine": "PSE",
    "Tanzania": "TZA",
    "Gambia": "GMB",
    "Bahamas": "BHS",
    "Egypt": "EGY",
    "Yemen": "YEM",
    "Sao Tome and Principe": "STP",
}


# FAOSTAT and Europe PMC both carry regional aggregates alongside countries. A fuzzy
# match must never turn one into a country: "Africa" is a substring of "Central
# African Republic", which silently gave the whole continent CAF's row.
_NON_COUNTRY = {
    "world", "africa", "asia", "europe", "americas", "oceania", "antarctica",
    "north america", "south america", "central america", "caribbean",
    "eastern africa", "western africa", "middle africa", "northern africa",
    "southern africa", "sub-saharan africa", "central asia", "eastern asia",
    "southern asia", "south-eastern asia", "western asia", "eastern europe",
    "western europe", "northern europe", "southern europe",
    "asia and the pacific", "least developed countries", "landlocked countries",
    "developing countries", "developed countries", "small island states",
    "european union", "world total", "total", "areas, total",
}


def _is_word_in(needle: str, hay: str) -> bool:
    """True when needle appears in hay on word boundaries."""
    import re
    return re.search(rf"\b{re.escape(needle)}\b", hay, flags=re.IGNORECASE) is not None


def to_iso3(name: str) -> str | None:
    if not isinstance(name, str) or not name.strip():
        return None
    key = name.strip()
    if key in _OVERRIDES:
        return _OVERRIDES[key]
    if key.lower() in _NON_COUNTRY:
        return None
    try:
        return pycountry.countries.lookup(key).alpha_3
    except LookupError:
        pass
    # Only accept a fuzzy hit on a word boundary, so an aggregate cannot smuggle
    # itself in as a country.
    if len(key) > 4:
        for c in pycountry.countries:
            if _is_word_in(key, c.name):
                return c.alpha_3
    return None


# --------------------------------------------------------------------------- #
# 1. Literature -> occurrence events  (animal history)
# --------------------------------------------------------------------------- #
def build_literature_events() -> pd.DataFrame:
    path = RAW / "europepmc_glanders_expanded.jsonl"
    recs = [json.loads(line) for line in path.open(encoding="utf-8")]
    rows: list[dict] = []
    for rec in recs:
        try:
            pub_year = int(rec.get("pubYear") or 0)
        except (TypeError, ValueError):
            continue
        if not (int(2000) <= pub_year <= END_YEAR):
            continue
        text = f"{rec.get('title') or ''}. {rec.get('abstractText') or ''}".strip()
        if len(text) < 40:
            continue
        title = rec.get("title") or ""
        is_review = bool(REVIEW_TERMS.search(text))
        for sent in SENT_SPLIT.split(text):
            countries = extract_countries(sent)
            if not countries or not OCCURRENCE_TERMS.search(sent):
                continue
            years = [y for y in extract_years(sent) if 1900 <= y <= pub_year]
            year = max(years) if years else pub_year
            for iso in countries:
                rows.append(
                    {
                        "iso3": iso,
                        "year": year,
                        "pub_year": pub_year,
                        "record_id": rec.get("id"),
                        "source": rec.get("source"),
                        "doi": rec.get("doi"),
                        "title": title[:180],
                        "sentence": sent[:300],
                        "is_review": is_review,
                        "in_abstract": bool(rec.get("abstractText")),
                    }
                )
    ev = pd.DataFrame(rows).drop_duplicates(subset=["iso3", "year", "record_id"])
    ev = ev[(ev.year >= 1995) & (ev.year <= END_YEAR)]
    ev.to_csv(PROC / "literature_events.csv", index=False)
    return ev


# --------------------------------------------------------------------------- #
# 2. FAOSTAT -> animal population features
# --------------------------------------------------------------------------- #
EQUINE = {"Horses": "horses", "Asses": "asses", "Mules and hinnies": "mules"}
OTHER = {"Camels": "camels", "Cattle": "cattle", "Goats": "goats", "Sheep": "sheep"}


def build_fao_panel() -> pd.DataFrame:
    df = pd.read_csv(RAW / "faostat_stocks_raw.csv")
    df = df[df.Year.between(1990, END_YEAR)].copy()
    df["iso3"] = df.Area.map(to_iso3)
    df = df[df.iso3.astype(str).str.len() == 3]
    df["var"] = df.Item.map({**EQUINE, **OTHER})
    df = df.dropna(subset=["var"])
    wide = df.pivot_table(index=["iso3", "Year"], columns="var", values="Value", aggfunc="max")
    wide = wide.reset_index().rename(columns={"Year": "year"})
    for c in ["horses", "asses", "mules", "camels", "cattle", "goats", "sheep"]:
        if c not in wide:
            wide[c] = np.nan
    return wide


# --------------------------------------------------------------------------- #
# 3. World Bank -> socio-agricultural features
# --------------------------------------------------------------------------- #
WB_FILES = {
    "wb_pop_total.json": "pop_total",
    "wb_rural_pct.json": "rural_pct",
    "wb_agri_land_pct.json": "agri_land_pct",
    "wb_land_area_km2.json": "land_area_km2",
    "wb_agri_va_pct_gdp.json": "agri_va_pct_gdp",
    "wb_livestock_prod_index.json": "livestock_prod_index",
    "wb_gdp_pc.json": "gdp_pc",
    "wb_internet_pct.json": "internet_pct",
    "wb_fertilizer_pct.json": "fertilizer_pct",
    "wb_life_expectancy.json": "life_expectancy",
}


def build_wb_panel() -> pd.DataFrame:
    frames = []
    for fname, col in WB_FILES.items():
        p = RAW / fname
        if not p.exists():
            continue
        d = pd.DataFrame(json.loads(p.read_text()))
        d = d[d.iso3.astype(str).str.len() == 3]          # drop WB aggregates ("", "1A", ...)
        d = d[(d.year >= 1990) & (d.year <= END_YEAR)]
        d = d.groupby(["iso3", "year"])["value"].mean().reset_index().rename(columns={"value": col})
        frames.append(d)
    out = frames[0]
    for f in frames[1:]:
        out = out.merge(f, on=["iso3", "year"], how="outer")
    return out


# --------------------------------------------------------------------------- #
# 4. NASA POWER -> agro-climate features
# --------------------------------------------------------------------------- #
def build_climate_panel() -> pd.DataFrame:
    p = RAW / "nasa_power_country_climate.json"
    if not p.exists():
        return pd.DataFrame(columns=["iso3", "year"])
    data = json.loads(p.read_text())
    rows = []
    for iso3, params in data.items():
        by_year: dict[int, dict[str, list[float]]] = {}
        for param, series in params.items():
            for key, val in series.items():
                if val in (-999.0, None, -999):
                    continue
                try:
                    y, m = int(str(key)[:4]), int(str(key)[4:6])
                except ValueError:
                    continue
                if m > 12:
                    continue
                by_year.setdefault(y, {}).setdefault(param, []).append(float(val))
        for y, params_y in by_year.items():
            row = {"iso3": iso3, "year": y}
            if "T2M" in params_y:
                row["temp_mean"] = float(np.mean(params_y["T2M"]))
            if "T2M_MAX" in params_y:
                row["temp_max"] = float(np.mean(params_y["T2M_MAX"]))
            if "T2M_MIN" in params_y:
                row["temp_min"] = float(np.mean(params_y["T2M_MIN"]))
            if "PRECTOTCORR" in params_y:
                prec = params_y["PRECTOTCORR"]
                row["precip_sum"] = float(np.sum(prec))
                row["precip_cv"] = float(np.std(prec) / (np.mean(prec) + 1e-6))
            if "RH2M" in params_y:
                row["humidity"] = float(np.mean(params_y["RH2M"]))
            if "WS2M" in params_y:
                row["wind"] = float(np.mean(params_y["WS2M"]))
            rows.append(row)
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- #
# 5. Assemble + feature engineering
# --------------------------------------------------------------------------- #
def assemble() -> tuple[pd.DataFrame, dict]:
    ev = build_literature_events()
    fao = build_fao_panel()
    wb = build_wb_panel()
    clim = build_climate_panel()

    years = range(2000, END_YEAR + 1)
    countries = sorted(set(fao.iso3) | set(wb.iso3) | set(clim.iso3))
    grid = pd.MultiIndex.from_product([countries, years], names=["iso3", "year"]).to_frame(index=False)
    panel = grid.merge(fao, on=["iso3", "year"], how="left")
    panel = panel.merge(wb, on=["iso3", "year"], how="left")
    panel = panel.merge(clim, on=["iso3", "year"], how="left")

    # --- occurrence counts per country-year (animal history signal)
    counts = ev.groupby(["iso3", "year"]).size().rename("occ_count").reset_index()
    panel = panel.merge(counts, on=["iso3", "year"], how="left")
    panel["occ_count"] = panel.occ_count.fillna(0)
    panel["occ_any"] = (panel.occ_count > 0).astype(int)

    # --- country metadata
    meta = pd.DataFrame(json.loads((RAW / "wb_countries.json").read_text()))
    meta = meta[["iso3", "country", "region", "income", "lat", "lon"]]
    meta["lat"] = pd.to_numeric(meta.lat, errors="coerce")
    meta["lon"] = pd.to_numeric(meta.lon, errors="coerce")
    meta["region"] = meta.region.str.strip()
    meta["income"] = meta.income.str.strip()
    panel = panel.merge(meta, on="iso3", how="left")

    panel = panel.sort_values(["iso3", "year"]).reset_index(drop=True)

    # --- equine aggregates
    for c in ["horses", "asses", "mules", "camels", "cattle", "goats", "sheep"]:
        panel[c] = panel[c].fillna(0.0)
    panel["equids"] = panel.horses + panel.asses + panel.mules
    panel["livestock_units"] = (
        panel.equids + 0.8 * panel.cattle + 0.1 * panel.goats + 0.1 * panel.sheep + 0.8 * panel.camels
    )

    g = panel.groupby("iso3")
    panel["equids_lag1"] = g["equids"].shift(1)
    panel["equids_lag2"] = g["equids"].shift(2)
    panel["equids_lag3"] = g["equids"].shift(3)
    panel["equid_growth_1y"] = (panel.equids - panel.equids_lag1) / (panel.equids_lag1 + 1)
    panel["equid_growth_3y"] = (panel.equids - panel.equids_lag3) / (panel.equids_lag3 + 1)
    panel["log_equids"] = np.log1p(panel.equids)
    panel["log_livestock"] = np.log1p(panel.livestock_units)
    panel["equid_share"] = panel.equids / (panel.livestock_units + 1)
    panel["equid_density"] = panel.equids / (panel.land_area_km2 * 0.01 + 1)
    panel["pop_density"] = panel.pop_total / (panel.land_area_km2 + 1)

    # --- disease-history lags (only past information)
    panel["occ_lag1"] = g["occ_any"].shift(1)
    panel["occ_lag2"] = g["occ_any"].shift(2)
    panel["occ_count_lag1"] = g["occ_count"].shift(1)
    panel["occ_count_5y"] = (
        g["occ_count"].shift(1).rolling(5, min_periods=1).sum().reset_index(level=0, drop=True)
    )
    last_seen = []
    seen_year: dict[str, int | None] = {}
    for iso3, year in zip(panel.iso3, panel.year):
        prev = seen_year.get(iso3)
        last_seen.append(np.nan if prev is None else year - prev)
        if panel.loc[len(last_seen) - 1, "occ_any"] == 1:
            seen_year[iso3] = year
    panel["years_since_last"] = last_seen
    panel["years_since_last"] = panel.years_since_last.fillna(99)

    # --- spatial / global context (same-year, so still "available at t")
    panel["global_occ_share"] = panel.groupby("year").occ_any.transform("mean")
    region_share = panel.groupby(["region", "year"]).occ_any.transform("mean")
    panel["region_occ_share"] = region_share

    # --- climate anomalies (country-level baseline, expanding mean up to t)
    for col in ["temp_mean", "precip_sum", "humidity"]:
        base = panel.groupby("iso3")[col].transform(
            lambda s: s.expanding().mean().shift(1)
        )
        panel[f"{col}_anom"] = panel[col] - base
    panel["abs_lat"] = panel.lat.abs()

    # --- targets: next year
    panel["y_occ_next"] = g["occ_any"].shift(-1)
    panel["y_count_next"] = g["occ_count"].shift(-1)
    panel["y_log_equids_next"] = g["log_equids"].shift(-1)

    # --- eligibility: countries with a real equine sector
    max_equids = panel.groupby("iso3").equids.transform("max")
    panel["equine_country"] = (max_equids >= 1000).astype(int)

    audit = {
        "literature_records": int(sum(1 for _ in (RAW / "europepmc_glanders_expanded.jsonl").open())),
        "literature_events": int(len(ev)),
        "countries_in_panel": int(panel.iso3.nunique()),
        "years": [int(panel.year.min()), int(panel.year.max())],
        "equine_countries": int(panel[panel.equine_country == 1].iso3.nunique()),
        "panel_rows": int(len(panel)),
        "positive_cells_all": int(panel.occ_any.sum()),
        "positive_cells_equine": int(panel[panel.equine_country == 1].occ_any.sum()),
        "positive_countries": int(panel[panel.occ_any == 1].iso3.nunique()),
        "occurrence_prevalence": float(panel.occ_any.mean()),
        "missing_pct": {c: float(panel[c].isna().mean() * 100) for c in panel.columns},
    }
    return panel, audit


if __name__ == "__main__":
    panel, audit = assemble()
    keep = panel[panel.year.between(START_YEAR, END_YEAR - 1)].copy()
    keep.to_csv(PROC / "country_year_panel.csv", index=False)
    (PROC / "audit.json").write_text(json.dumps(audit, indent=2))
    print(json.dumps({k: v for k, v in audit.items() if k != "missing_pct"}, indent=2))
    print("\nrows:", len(keep), " pos:", int(keep.y_occ_next.sum()),
          f"({keep.y_occ_next.mean()*100:.1f}%)")
    print(keep[keep.equine_country == 1].y_occ_next.value_counts(dropna=False).to_dict())
