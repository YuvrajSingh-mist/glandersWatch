"""Fetch the novel data sources used by the GlandersWatch chained-ML study.

Sources (none of these had been used for glanders risk modelling before this study):
  1. Europe PMC  -> literature-derived glanders occurrence panel (animal history)
  2. FAOSTAT     -> equine / livestock stocks by country-year (animal population)  [extracted separately]
  3. World Bank  -> country metadata (centroid, region, income) + socio-agricultural covariates
  4. NASA POWER  -> annual agro-climatology per country centroid

Run:  python src/01_fetch_data.py
"""
from __future__ import annotations

import json
import pathlib
import time
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)

UA = {"User-Agent": "glanderswatch-research/1.0 (academic use)"}


def get(url: str, tries: int = 4, timeout: int = 60) -> bytes:
    last = None
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception as exc:  # noqa: BLE001 - transient HTTP issues
            last = exc
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"failed: {url}") from last


# --------------------------------------------------------------------------- #
# 1. Europe PMC: every glanders record with abstract (literature occurrence panel)
# --------------------------------------------------------------------------- #
def fetch_europepmc() -> None:
    out = RAW / "europepmc_glanders.jsonl"
    if out.exists() and out.stat().st_size > 1_000_000:
        print(f"[europepmc] cached {out.stat().st_size/1e6:.1f} MB")
        return
    cursor = "*"
    seen = 0
    with out.open("w", encoding="utf-8") as fh:
        while True:
            q = urllib.parse.urlencode(
                {
                    "query": "glanders",
                    "format": "json",
                    "pageSize": 1000,
                    "resultType": "core",
                    "cursorMark": cursor,
                }
            )
            payload = json.loads(get(f"https://www.ebi.ac.uk/europepmc/webservices/rest/search?{q}"))
            hits = payload.get("resultList", {}).get("result", [])
            if not hits:
                break
            for rec in hits:
                keep = {
                    k: rec.get(k)
                    for k in (
                        "id", "pmid", "doi", "title", "abstractText", "pubYear",
                        "journalTitle", "pubType", "country", "authorString",
                        "firstPublicationDate", "isOpenAccess",
                    )
                }
                fh.write(json.dumps(keep, ensure_ascii=False) + "\n")
            seen += len(hits)
            nxt = payload.get("nextCursorMark")
            print(f"[europepmc] {seen} records", flush=True)
            if not nxt or nxt == cursor:
                break
            cursor = nxt
            time.sleep(0.35)
    print(f"[europepmc] saved {seen} records")


# --------------------------------------------------------------------------- #
# 2. World Bank: country metadata + socio-agricultural covariates
# --------------------------------------------------------------------------- #
WB_INDICATORS = {
    "SP.POP.TOTL": "pop_total",
    "SP.RUR.TOTL.ZS": "rural_pct",
    "AG.LND.AGRI.ZS": "agri_land_pct",
    "AG.LND.TOTL.K2": "land_area_km2",
    "NV.AGR.TOTL.ZS": "agri_va_pct_gdp",
    "AG.PRD.LVSK.XD": "livestock_prod_index",
    "NY.GDP.PCAP.CD": "gdp_pc",
    "IT.NET.USER.ZS": "internet_pct",
    "AG.CON.FERT.ZS": "fertilizer_pct",
    "SP.DYN.LE00.IN": "life_expectancy",
}


def fetch_worldbank() -> None:
    meta_out = RAW / "wb_countries.json"
    if not meta_out.exists() or meta_out.stat().st_size < 10_000:
        raw = json.loads(get("https://api.worldbank.org/v2/country?format=json&per_page=400"))
        rows = []
        for c in raw[1]:
            if c["region"]["value"] == "Aggregates":
                continue
            rows.append(
                {
                    "iso3": c["id"],
                    "iso2": c.get("iso2Code"),
                    "country": c["name"],
                    "region": c["region"]["value"],
                    "income": c["incomeLevel"]["value"],
                    "lat": c.get("latitude"),
                    "lon": c.get("longitude"),
                }
            )
        meta_out.write_text(json.dumps(rows, indent=1))
        print(f"[worldbank] {len(rows)} countries")
    else:
        print("[worldbank] country metadata cached")

    for code, name in WB_INDICATORS.items():
        out = RAW / f"wb_{name}.json"
        if out.exists() and out.stat().st_size > 5_000:
            continue
        rows = []
        page = 1
        while True:
            url = (
                f"https://api.worldbank.org/v2/country/all/indicator/{code}"
                f"?format=json&per_page=20000&date=2000:2024&page={page}"
            )
            payload = json.loads(get(url))
            if len(payload) < 2 or not payload[1]:
                break
            for r in payload[1]:
                if r["value"] is None:
                    continue
                rows.append(
                    {
                        "iso3": r["countryiso3code"],
                        "country": r["country"]["value"],
                        "year": int(r["date"]),
                        "value": r["value"],
                    }
                )
            if page >= payload[0]["pages"]:
                break
            page += 1
        out.write_text(json.dumps(rows))
        print(f"[worldbank] {name}: {len(rows)} rows")


# --------------------------------------------------------------------------- #
# 3. NASA POWER: annual agro-climatology at each country centroid 2005-2024
# --------------------------------------------------------------------------- #
POWER_PARAMS = ["T2M", "T2M_MAX", "T2M_MIN", "PRECTOTCORR", "RH2M", "WS2M"]


def fetch_nasa_power() -> None:
    meta = json.loads((RAW / "wb_countries.json").read_text())
    out = RAW / "nasa_power_country_climate.json"
    cache = json.loads(out.read_text()) if out.exists() else {}
    def usable(c: dict) -> bool:
        if c["iso3"] in cache or c["iso3"] in {"ATA"}:
            return False
        try:
            return -60 < float(c["lat"]) < 75
        except (TypeError, ValueError):
            return False

    todo = [c for c in meta if usable(c)]
    print(f"[nasa] {len(todo)} countries to fetch, {len(cache)} cached")
    for i, c in enumerate(todo, 1):
        q = urllib.parse.urlencode(
            {
                "parameters": ",".join(POWER_PARAMS),
                "community": "AG",
                "longitude": round(float(c["lon"]), 2),
                "latitude": round(float(c["lat"]), 2),
                "start": "2005",
                "end": "2024",
                "format": "JSON",
            }
        )
        try:
            payload = json.loads(
                get(f"https://power.larc.nasa.gov/api/temporal/monthly/point?{q}", timeout=90)
            )
            cache[c["iso3"]] = payload["properties"]["parameter"]
        except Exception as exc:  # noqa: BLE001
            print(f"[nasa] {c['iso3']} failed: {exc}")
        if i % 10 == 0 or i == len(todo):
            out.write_text(json.dumps(cache))
            print(f"[nasa] {i}/{len(todo)}", flush=True)
        time.sleep(0.25)


if __name__ == "__main__":
    fetch_europepmc()
    fetch_worldbank()
    fetch_nasa_power()
