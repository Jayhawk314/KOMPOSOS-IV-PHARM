#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Read-only audit that splits evidence tier from source/status classification."""

from __future__ import annotations

import argparse
import csv
import sqlite3
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.evidence_classification import classify_evidence
from validation.repurposing_benchmark import DB_PATH


VERSION = "2026-05-27"


def main() -> int:
    parser = argparse.ArgumentParser(description="Split evidence tier into source type and validation status.")
    parser.add_argument("--db", default=DB_PATH, help="Path to tier1 SQLite database.")
    parser.add_argument("--out", default=None, help="Optional CSV output path.")
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, source_name, target_name, name, provenance, evidence_tier,
               quantitative_value, metadata
        FROM morphisms
        ORDER BY id
    """)

    rows = []
    for row in cursor.fetchall():
        cls = classify_evidence(
            row["provenance"],
            row["metadata"],
            row["evidence_tier"],
            row["quantitative_value"],
        )
        rows.append({
            "morphism_id": row["id"],
            "source": row["source_name"],
            "relation": row["name"],
            "target": row["target_name"],
            "evidence_tier": row["evidence_tier"] or "",
            **cls.to_dict(),
        })
    conn.close()

    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()) if rows else [])
            writer.writeheader()
            writer.writerows(rows)

    by_tier = Counter(row["evidence_tier"] for row in rows)
    by_source = Counter(row["source_type"] for row in rows)
    by_status = Counter(row["validation_status"] for row in rows)
    mismatches = [
        row for row in rows
        if row["evidence_tier"] == "MEASURED"
        and row["validation_status"].endswith("tier_mismatch")
    ]

    print(f"Version:   {VERSION}")
    print(f"Rows:      {len(rows)}")
    if args.out:
        print(f"CSV:       {args.out}")
    print("Evidence tiers:")
    for key, value in by_tier.most_common():
        print(f"  {key:20s} {value}")
    print("Source types:")
    for key, value in by_source.most_common():
        print(f"  {key:40s} {value}")
    print("Validation statuses:")
    for key, value in by_status.most_common():
        print(f"  {key:40s} {value}")
    print(f"MEASURED tier mismatches: {len(mismatches)}")
    for row in mismatches[:20]:
        print(
            f"  {row['source']} -{row['relation']}-> {row['target']} "
            f"source_type={row['source_type']} status={row['validation_status']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
