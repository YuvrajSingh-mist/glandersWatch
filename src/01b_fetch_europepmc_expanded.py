"""Download the expanded glanders corpus (glanders OR Burkholderia mallei OR farcy)."""
from __future__ import annotations

import json
import pathlib
import time
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "raw" / "europepmc_glanders_expanded.jsonl"
QUERY = 'glanders OR "Burkholderia mallei" OR farcy'


def main() -> None:
    if OUT.exists() and OUT.stat().st_size > 500_000:
        n = sum(1 for _ in OUT.open())
        print(f"cached {n} records")
        return
    cursor, seen = "*", 0
    with OUT.open("w", encoding="utf-8") as fh:
        while True:
            q = urllib.parse.urlencode(
                {
                    "query": QUERY,
                    "format": "json",
                    "pageSize": 1000,
                    "resultType": "core",
                    "cursorMark": cursor,
                }
            )
            req = urllib.request.Request(
                f"https://www.ebi.ac.uk/europepmc/webservices/rest/search?{q}",
                headers={"User-Agent": "glanderswatch-research/1.0"},
            )
            with urllib.request.urlopen(req, timeout=90) as r:
                payload = json.load(r)
            hits = payload.get("resultList", {}).get("result", [])
            if not hits:
                break
            for rec in hits:
                fh.write(
                    json.dumps(
                        {
                            k: rec.get(k)
                            for k in (
                                "id", "source", "pmid", "doi", "title", "abstractText",
                                "pubYear", "journalTitle", "pubType", "authorString",
                                "firstPublicationDate", "isOpenAccess",
                            )
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )
            seen += len(hits)
            nxt = payload.get("nextCursorMark")
            print(f"{seen} records", flush=True)
            if not nxt or nxt == cursor:
                break
            cursor = nxt
            time.sleep(0.3)


if __name__ == "__main__":
    main()
