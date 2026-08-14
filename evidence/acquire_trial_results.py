#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""Recover trial results that exist but are not indexed by the literature.

Why this exists
---------------
Of the trials tracked by the candidate review, 75% never posted results, and
every recorded stop reason is operational or financial - low accrual, lost
funding, sponsor bankruptcy, drug supply - never efficacy or safety. So the
novelty axis in `validation/nonobvious.py` cannot tell "nobody tried this" apart
from "somebody tried it and ran out of money".

The 2026-08-12 reconnaissance found 15 trials whose results are posted on
ClinicalTrials.gov with no publication at all. A literature search will never
surface them. This module fetches and caches them.

The hard boundary
-----------------
**Fill by retrieval. Never by inference.**

This module records that results EXIST, WHERE they are, and structured registry
facts (enrolment, outcome-measure count, participant flow). It does NOT decide
whether a trial succeeded. Every outcome it writes carries
`result_signal = 'RESULTS_AVAILABLE_NOT_ASSESSED'` and `human_reviewed = 0`.
Reading a results section and judging efficacy is human work.

Nothing here may enter the scored graph path. See
`docs/PLAN_TRIAL_RESULTS_RECOVERY_2026-08-12.md` section 4a.

Usage:
    python -m evidence.acquire_trial_results
    python -m evidence.acquire_trial_results --refresh
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, timezone, datetime
from pathlib import Path

from .store import REPO

TRIAL_INVENTORY = REPO / "reports/candidate_review_2026-08-01/TRIAL_EVIDENCE_60.json"

#: Distilled records live under reports/ and are COMMITTED, not cached under
#: data/external/. The build reads them, so a gitignored cache would make the
#: database non-reproducible: two people running `python -m evidence.build`
#: would get different row counts depending on whether they had fetched.
CACHE_DIR = REPO / "reports/trial_recovery_2026-08-12"
RECORDS_NAME = "RECOVERED_RESULTS.json"
API = "https://clinicaltrials.gov/api/v2/studies"
CHUNK = 20
PAUSE_SECONDS = 1.0

#: Retrieval-only dispositions. None of these asserts what a trial showed.
DISPOSITION_RESULTS_CTG = "RESULTS_RECOVERED_CTG"
DISPOSITION_RESULTS_PUBLICATION = "RESULTS_RECOVERED_PUBLICATION"
DISPOSITION_ONGOING = "ONGOING_NO_RESULTS_YET"
DISPOSITION_NO_DATA = "NO_DATA_EVER_GENERATED"
DISPOSITION_UNRESOLVED = "UNRESOLVED_NO_SOURCE_FOUND"

#: Human-readable labels for display surfaces. Kept beside the dispositions so a
#: new disposition cannot silently render as "not checked" in the UI.
DISPOSITION_LABELS = {
    DISPOSITION_RESULTS_CTG: "registry results posted",
    DISPOSITION_RESULTS_PUBLICATION: "result publication linked",
    DISPOSITION_ONGOING: "ongoing - no results yet",
    DISPOSITION_NO_DATA: "no data ever generated",
    DISPOSITION_UNRESOLVED: "no results located yet",
    "NOT_ASSESSED": "not checked",
}

ONGOING_STATUSES = {
    "RECRUITING",
    "ACTIVE_NOT_RECRUITING",
    "NOT_YET_RECRUITING",
    "ENROLLING_BY_INVITATION",
}


def tracked_nct_ids(inventory_path: Path = TRIAL_INVENTORY) -> list[str]:
    """Read trial identifiers from the review inventory, not from the database.

    The database is rebuilt from these files, so depending on it here would make
    acquisition circular.
    """
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    found: set[str] = set()
    for pair in inventory.values():
        for trial in pair.get("trials", []):
            nct = (trial.get("nct") or "").strip().upper()
            if nct.startswith("NCT"):
                found.add(nct)
    return sorted(found)


def summarize_study(study: dict) -> dict:
    """Extract registry facts. Never an efficacy judgement."""
    protocol = study.get("protocolSection", {})
    status = protocol.get("statusModule", {})
    design = protocol.get("designModule", {})
    enrollment = design.get("enrollmentInfo", {}) or {}

    by_type: dict[str, list[str]] = {}
    for reference in protocol.get("referencesModule", {}).get("references", []):
        pmid = reference.get("pmid")
        if pmid:
            by_type.setdefault(reference.get("type", "UNKNOWN"), []).append(pmid)

    results = study.get("resultsSection", {}) or {}
    outcome_measures = (
        results.get("outcomeMeasuresModule", {}).get("outcomeMeasures", []) or []
    )
    flow = results.get("participantFlowModule", {}) or {}

    return {
        "nct_id": protocol.get("identificationModule", {}).get("nctId", ""),
        "title": protocol.get("identificationModule", {}).get("briefTitle", ""),
        "status": status.get("overallStatus", "UNKNOWN"),
        "why_stopped": status.get("whyStopped", "") or "",
        "completion_date": (status.get("completionDateStruct", {}) or {}).get("date", ""),
        "has_results": bool(study.get("hasResults")),
        "enrollment_count": enrollment.get("count"),
        "enrollment_type": enrollment.get("type", ""),
        "result_pmids": by_type.get("RESULT", []),
        "derived_pmids": by_type.get("DERIVED", []),
        # Background citations are prior literature, not reports of THIS trial,
        # so they must never count as a recovered result.
        "background_pmids": by_type.get("BACKGROUND", []),
        "outcome_measure_count": len(outcome_measures),
        "outcome_measure_titles": [
            m.get("title", "") for m in outcome_measures[:12] if m.get("title")
        ],
        "has_participant_flow": bool(flow),
    }


def disposition_for(record: dict) -> str:
    """Classify recoverability from registry facts alone."""
    if record["has_results"]:
        return DISPOSITION_RESULTS_CTG
    if record["result_pmids"] or record["derived_pmids"]:
        return DISPOSITION_RESULTS_PUBLICATION
    if record["status"] in ONGOING_STATUSES:
        return DISPOSITION_ONGOING
    # A withdrawn trial with a confirmed actual enrolment of zero generated no
    # data. "Nothing to recover" is a complete answer, not a failed search.
    if (
        record["status"] == "WITHDRAWN"
        and record["enrollment_type"] == "ACTUAL"
        and record["enrollment_count"] == 0
    ):
        return DISPOSITION_NO_DATA
    return DISPOSITION_UNRESOLVED


def results_url(nct_id: str) -> str:
    return f"https://clinicaltrials.gov/study/{nct_id}?tab=results"


def _fetch_chunk(chunk: list[str]) -> dict:
    query = urllib.parse.urlencode(
        {"filter.ids": "|".join(chunk), "pageSize": len(chunk)}
    )
    url = f"{API}?{query}"
    with urllib.request.urlopen(url, timeout=60) as response:
        payload = response.read()
    return {"url": url, "payload": payload}


def acquire(
    *, cache_dir: Path = CACHE_DIR, refresh: bool = False, verbose: bool = True
) -> dict:
    """Fetch and cache registry records. Resumable; re-run is cheap."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    records_path = cache_dir / RECORDS_NAME
    provenance_path = cache_dir / "PROVENANCE.json"

    if records_path.exists() and not refresh:
        if verbose:
            print(f"cache hit: {records_path} (use --refresh to re-fetch)")
        return json.loads(records_path.read_text(encoding="utf-8"))

    ids = tracked_nct_ids()
    records: dict[str, dict] = {}
    provenance: list[dict] = []

    for start in range(0, len(ids), CHUNK):
        chunk = ids[start : start + CHUNK]
        fetched = _fetch_chunk(chunk)
        provenance.append(
            {
                "url": fetched["url"],
                "requested": chunk,
                "sha256": hashlib.sha256(fetched["payload"]).hexdigest(),
                "retrieved_at": datetime.now(timezone.utc).isoformat(),
                "bytes": len(fetched["payload"]),
            }
        )
        for study in json.loads(fetched["payload"]).get("studies", []):
            summary = summarize_study(study)
            summary["disposition"] = disposition_for(summary)
            summary["results_url"] = (
                results_url(summary["nct_id"]) if summary["has_results"] else ""
            )
            records[summary["nct_id"]] = summary
        if verbose:
            print(f"  fetched {len(records)}/{len(ids)}", flush=True)
        time.sleep(PAUSE_SECONDS)

    report = {
        "generated_at": date.today().isoformat(),
        "source": "ClinicalTrials.gov API v2",
        "requested": len(ids),
        "returned": len(records),
        "not_found": [n for n in ids if n not in records],
        "records": records,
    }
    records_path.write_text(json.dumps(report, indent=1))
    provenance_path.write_text(json.dumps(provenance, indent=1))
    return report


def load_cached(cache_dir: Path = CACHE_DIR) -> dict:
    """Return cached records, or an empty result when acquisition has not run.

    The build must not require network access, so a missing cache is a normal
    state rather than an error.
    """
    records_path = cache_dir / RECORDS_NAME
    if not records_path.exists():
        return {"records": {}, "returned": 0, "requested": 0}
    return json.loads(records_path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Recover unindexed trial results")
    parser.add_argument("--refresh", action="store_true", help="re-fetch, ignore cache")
    parser.add_argument("--cache-dir", type=Path, default=CACHE_DIR)
    args = parser.parse_args()

    try:
        report = acquire(cache_dir=args.cache_dir, refresh=args.refresh)
    except urllib.error.URLError as error:
        print(f"acquisition failed (network): {error}")
        return 1

    counts: dict[str, int] = {}
    for record in report["records"].values():
        counts[record["disposition"]] = counts.get(record["disposition"], 0) + 1

    print()
    print(f"trials: {report['returned']}/{report['requested']}")
    for name, count in sorted(counts.items(), key=lambda kv: -kv[1]):
        print(f"  {count:3d}  {name}")

    unpublished = [
        r for r in report["records"].values()
        if r["disposition"] == DISPOSITION_RESULTS_CTG
        and not (r["result_pmids"] or r["derived_pmids"])
    ]
    print()
    print(f"results posted with no publication: {len(unpublished)}")
    for record in unpublished:
        print(f"  {record['nct_id']}  {record['status']:22s} {record['results_url']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
