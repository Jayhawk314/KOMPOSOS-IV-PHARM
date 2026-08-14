#!/usr/bin/env python3
"""Reconnaissance: how many tracked trials have recoverable results?

Read-only. Reads NCT identifiers from the evidence database, queries the
ClinicalTrials.gov v2 API, and writes RECON_REPORT.json beside this file.
It does NOT modify evidence.db.

    python reports/trial_recovery_recon_2026-08-12/recon.py
"""
from __future__ import annotations

import json
import sqlite3
import time
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
EVIDENCE_DB = REPO / "data" / "evidence" / "evidence.db"
API = "https://clinicaltrials.gov/api/v2/studies"


def tracked_nct_ids(db_path: Path) -> list[str]:
    connection = sqlite3.connect(db_path)
    try:
        rows = connection.execute(
            "SELECT DISTINCT external_id FROM receipts "
            "WHERE source_type='CLINICALTRIALS' AND external_id LIKE 'NCT%' "
            "ORDER BY external_id"
        )
        return [row[0] for row in rows]
    finally:
        connection.close()


def fetch(chunk: list[str]) -> dict:
    query = urllib.parse.urlencode(
        {"filter.ids": "|".join(chunk), "pageSize": len(chunk)}
    )
    with urllib.request.urlopen(f"{API}?{query}", timeout=60) as response:
        return json.loads(response.read())


def classify(record: dict) -> str:
    """Retrieval-only classification. Never infers an outcome."""
    publications = record["result_pmids"] + record["derived_pmids"]
    if record["has_results"] and publications:
        return "RESULTS_POSTED_AND_PUBLISHED"
    if record["has_results"]:
        return "RESULTS_POSTED_NOT_PUBLISHED"
    if publications:
        return "PUBLISHED_ONLY"
    return "NO_RESULTS_NO_PUBLICATION"


def main() -> int:
    ids = tracked_nct_ids(EVIDENCE_DB)
    print(f"tracked NCT identifiers: {len(ids)}")

    records: dict[str, dict] = {}
    for start in range(0, len(ids), 20):
        chunk = ids[start : start + 20]
        for study in fetch(chunk).get("studies", []):
            protocol = study.get("protocolSection", {})
            status = protocol.get("statusModule", {})
            references = protocol.get("referencesModule", {}).get("references", [])
            by_type: dict[str, list[str]] = {}
            for reference in references:
                by_type.setdefault(reference.get("type", "UNKNOWN"), []).append(
                    reference.get("pmid")
                )
            nct = protocol.get("identificationModule", {}).get("nctId")
            records[nct] = {
                "status": status.get("overallStatus"),
                "why_stopped": status.get("whyStopped"),
                "has_results": bool(study.get("hasResults")),
                "result_pmids": [p for p in by_type.get("RESULT", []) if p],
                "derived_pmids": [p for p in by_type.get("DERIVED", []) if p],
                "background_pmids": [p for p in by_type.get("BACKGROUND", []) if p],
            }
        print(f"  fetched {len(records)}/{len(ids)}", flush=True)
        time.sleep(1)

    classes: dict[str, list[str]] = {}
    for nct, record in records.items():
        classes.setdefault(classify(record), []).append(nct)

    report = {
        "trials_queried": len(ids),
        "trials_returned": len(records),
        "not_found_on_ctg": [n for n in ids if n not in records],
        "class_counts": {k: len(v) for k, v in sorted(classes.items())},
        "classes": classes,
        "records": records,
    }
    (HERE / "RECON_REPORT.json").write_text(json.dumps(report, indent=1))

    print()
    print(f"queried {len(ids)}, returned {len(records)}")
    for name, members in sorted(classes.items(), key=lambda kv: -len(kv[1])):
        print(f"  {len(members):3d}  {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
