#!/usr/bin/env python3
"""Validate PubMed identifiers attached to terminal candidate edges.

Existence and relevance are deliberately separate.  NCBI ESummary can prove
that a PMID resolves; it cannot prove that the paper supports the graph claim.
The generated CSV therefore leaves ``relevance_assessment`` for a reviewer.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sqlite3
import urllib.parse
import urllib.request
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DEFAULT_SHEET = REPO / "reports/candidate_review_2026-08-01/CANDIDATE_REVIEW_60.csv"
DEFAULT_DB = REPO / "data/drugs/tier1.db"
ESUMMARY = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
PMID_RE = re.compile(r"PMID:(\d+)")


def terminal_edges(sheet: Path, db: Path) -> tuple[list[dict[str, str]], dict[str, list[str]]]:
    rows = list(csv.DictReader(sheet.open(encoding="utf-8-sig")))
    uses: dict[str, list[str]] = defaultdict(list)
    with sqlite3.connect(db) as con:
        con.row_factory = sqlite3.Row
        for row in rows:
            edges = con.execute(
                """SELECT evidence_tier, provenance FROM morphisms
                   WHERE source_name=? AND name=? AND target_name=?""",
                (row["mechanism_target"], row["terminal_relation"], row["disease"]),
            ).fetchall()
            for edge in edges:
                for pmid in PMID_RE.findall(edge["provenance"]):
                    uses[pmid].append(row["review_id"])
    return rows, uses


def fetch_summaries(pmids: list[str]) -> dict[str, dict]:
    if not pmids:
        return {}
    query = urllib.parse.urlencode({
        "db": "pubmed", "id": ",".join(pmids), "retmode": "json",
    })
    request = urllib.request.Request(
        f"{ESUMMARY}?{query}", headers={"User-Agent": "KOMPOSOS-IV-PHARM/1.0"}
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = json.loads(response.read().decode("utf-8"))
    result = payload.get("result", {})
    return {pmid: result.get(pmid, {}) for pmid in pmids}


def summary_resolves(summary: dict) -> bool:
    """Require a real bibliographic record, not merely an error keyed by PMID."""
    return bool(
        summary.get("uid") and summary.get("title") and not summary.get("error")
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sheet", type=Path, default=DEFAULT_SHEET)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    _rows, uses = terminal_edges(args.sheet, args.db)
    summaries = fetch_summaries(sorted(uses, key=int))
    output = []
    for pmid in sorted(uses, key=int):
        summary = summaries.get(pmid) or {}
        title = summary.get('title', '')
        resolves = summary_resolves(summary)
        output.append({
            "pmid": pmid,
            "resolves": "YES" if resolves else "NO",
            "ncbi_error": summary.get("error", ""),
            "title": title,
            "pubdate": summary.get("pubdate", ""),
            "review_rows": ";".join(uses[pmid]),
            "relevance_assessment": "",
            "review_note": "",
        })

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=list(output[0]), lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(output)
    missing = sum(row["resolves"] == "NO" for row in output)
    print(f"wrote {len(output)} unique PMIDs to {args.out} ({missing} unresolved)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
