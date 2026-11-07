"""Novelty audit: how much prior work joins glanders with these data sources / ML?

Every count is reproducible from the public Europe PMC API.
Run:  .venv/bin/python src/00_novelty_audit.py
"""
from __future__ import annotations

import json
import pathlib
import time
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
REP = ROOT / "reports"
REP.mkdir(exist_ok=True)

QUERIES = {
    "A. glanders (baseline corpus)": 'glanders OR "Burkholderia mallei" OR farcy',
    "B. glanders + machine learning": (
        '(glanders OR "Burkholderia mallei") AND '
        '("machine learning" OR "deep learning" OR "neural network")'
    ),
    "C. glanders + tree ensembles": (
        '(glanders OR "Burkholderia mallei") AND '
        '("random forest" OR xgboost OR lightgbm OR "gradient boosting" OR "decision tree")'
    ),
    "D. glanders + forecasting": (
        '(glanders OR "Burkholderia mallei") AND '
        '(forecast OR forecasting OR "early warning" OR "risk map" OR "risk model")'
    ),
    "E. glanders + FAOSTAT": '(glanders OR "Burkholderia mallei") AND FAOSTAT',
    "F. glanders + NASA POWER": '(glanders OR "Burkholderia mallei") AND "NASA POWER"',
    "G. glanders + World Bank indicators": (
        '(glanders OR "Burkholderia mallei") AND "World Bank"'
    ),
    "H. glanders + equine population denominator": (
        '(glanders OR "Burkholderia mallei") AND '
        '("equine population" OR "horse population" OR "equid population")'
    ),
    "I. glanders + Europe PMC text mining": (
        '(glanders OR "Burkholderia mallei") AND '
        '("text mining" OR "literature mining" OR "corpus")'
    ),
    "J. glanders + chained/stacked models": (
        '(glanders OR "Burkholderia mallei") AND '
        '("stacking" OR "stacked model" OR "model chain" OR "chained model" OR "hurdle model")'
    ),
    "K. glanders + random forest (risk context)": (
        '(glanders OR "Burkholderia mallei") AND "random forest" AND '
        '(outbreak OR risk OR predict OR forecast)'
    ),
    "L. glanders + niche / distribution model": (
        '(glanders OR "Burkholderia mallei") AND '
        '("species distribution model" OR "ecological niche" OR maxent OR "habitat suitability")'
    ),
    "M. glanders + remote sensing / reanalysis": (
        '(glanders OR "Burkholderia mallei") AND '
        '("remote sensing" OR NDVI OR "land surface temperature" OR ERA5)'
    ),
    "N. glanders + spatio-temporal clustering": (
        '(glanders OR "Burkholderia mallei") AND (spatial OR spatio-temporal OR cluster) '
        'AND (risk OR predict OR forecast)'
    ),
    "O. glanders + gradient boosting": (
        '(glanders OR "Burkholderia mallei") AND '
        '(xgboost OR lightgbm OR catboost OR "gradient boosting")'
    ),
}


def count(query: str) -> tuple[int, list[str]]:
    q = urllib.parse.urlencode(
        {"query": query, "format": "json", "pageSize": 5, "resultType": "lite"}
    )
    req = urllib.request.Request(
        f"https://www.ebi.ac.uk/europepmc/webservices/rest/search?{q}",
        headers={"User-Agent": "glanderswatch-research/1.0"},
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        payload = json.load(r)
    hits = payload.get("hitCount", 0)
    titles = [
        (h.get("title") or "")[:150]
        for h in payload.get("resultList", {}).get("result", [])
    ]
    return int(hits), titles


if __name__ == "__main__":
    out = {}
    for label, query in QUERIES.items():
        try:
            n, titles = count(query)
        except Exception as exc:  # noqa: BLE001
            print(f"{label}: FAILED {exc}")
            continue
        out[label] = {"query": query, "hits": n, "example_titles": titles}
        print(f"{label:46s} {n:5d} hits")
        for t in titles[:3]:
            print(f"      - {t}")
        time.sleep(0.3)
    (REP / "novelty_audit.json").write_text(json.dumps(out, indent=2))
    print("\nsaved reports/novelty_audit.json")
