#!/usr/bin/env python3
"""Regenerate graph-evidence columns in a candidate-review sheet.

The review queue is a fixed sample, but its graph metadata must come from the
active database rather than memory or hand entry.  This command fails closed
when a terminal edge cannot be reconstructed.
"""
from __future__ import annotations

import argparse
import csv
import re
import sqlite3
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DEFAULT_SHEET = REPO / "reports/candidate_review_2026-08-01/CANDIDATE_REVIEW_60.csv"
DEFAULT_DB = REPO / "data/drugs/tier1.db"
DEFAULT_PMID_REVIEW = (
    REPO / "reports/candidate_review_2026-08-01/TERMINAL_PMID_REVIEW.csv"
)
DEFAULT_EVIDENCE_REVIEW = (
    REPO / "reports/candidate_review_2026-08-01/CANDIDATE_EVIDENCE_REVIEW.csv"
)
PMID_RE = re.compile(r"PMID:(\d+)")
INSERT_AFTER = "terminal_tier"
GENERATED_FIELDS = ("terminal_provenance", "terminal_receipt_assessment")
LEGACY_REVIEW_FIELDS = (
    "VERDICT", "why", "negative_evidence_found", "what_kind_of_negative_evidence",
)


def load_pmid_reviews(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    return {
        row["pmid"]: row["relevance_assessment"]
        for row in csv.DictReader(path.open(encoding="utf-8-sig"))
    }


def load_evidence_reviews(path: Path) -> tuple[list[str], dict[str, dict[str, str]]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = [field for field in (reader.fieldnames or []) if field != "review_id"]
        reviews = {row["review_id"]: row for row in reader}
    return fields, reviews


def receipt_assessment(provenance: str, reviews: dict[str, str]) -> str:
    pmids = PMID_RE.findall(provenance)
    if not pmids:
        return "NON_PMID_SOURCE"
    return ";".join(f"PMID:{pmid}={reviews.get(pmid, 'NOT_REVIEWED')}" for pmid in pmids)


def enriched_rows(
    sheet: Path, db: Path, pmid_review: Path, evidence_review: Path,
) -> tuple[list[str], list[dict[str, str]]]:
    with sheet.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = list(reader.fieldnames or [])
        rows = list(reader)
    reviews = load_pmid_reviews(pmid_review)
    evidence_fields, evidence_reviews = load_evidence_reviews(evidence_review)

    with sqlite3.connect(db) as con:
        con.row_factory = sqlite3.Row
        for row in rows:
            edges = con.execute(
                """SELECT evidence_tier, provenance FROM morphisms
                   WHERE source_name=? AND name=? AND target_name=?""",
                (row["mechanism_target"], row["terminal_relation"], row["disease"]),
            ).fetchall()
            if len(edges) != 1:
                raise RuntimeError(
                    f"{row['review_id']}: expected one terminal edge, found {len(edges)}"
                )
            edge = edges[0]
            row["terminal_tier"] = edge["evidence_tier"]
            row["terminal_provenance"] = edge["provenance"]
            row["terminal_receipt_assessment"] = receipt_assessment(
                edge["provenance"], reviews
            )
            try:
                evidence = evidence_reviews[row["review_id"]]
            except KeyError as exc:
                raise RuntimeError(f"{row['review_id']}: missing evidence review") from exc
            for field in LEGACY_REVIEW_FIELDS:
                row.pop(field, None)
            for field in evidence_fields:
                row[field] = evidence[field]

    fields = [field for field in fields if field not in LEGACY_REVIEW_FIELDS]
    for field in reversed(GENERATED_FIELDS):
        if field not in fields:
            fields.insert(fields.index(INSERT_AFTER) + 1, field)
    fields.extend(field for field in evidence_fields if field not in fields)
    return fields, rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sheet", type=Path, default=DEFAULT_SHEET)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--pmid-review", type=Path, default=DEFAULT_PMID_REVIEW)
    parser.add_argument("--evidence-review", type=Path, default=DEFAULT_EVIDENCE_REVIEW)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    fields, rows = enriched_rows(
        args.sheet, args.db, args.pmid_review, args.evidence_review
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.out.with_suffix(args.out.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(args.out)
    print(f"wrote {len(rows)} rows to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
