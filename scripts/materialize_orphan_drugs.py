#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""
Materialize ChEMBL drug endpoints that exist only in `morphisms` as real `objects` rows.

Background
----------
855 ChEMBL-sourced edges (inhibits/activates/targets/binds/modulates) name a drug
on the source side that has no row in `objects`. Every loader selects its drug
universe with `type_name='Drug'` from `objects`, so those 679 drugs were silently
dropped at load: the search space was 78 drugs when the graph actually carries
target pharmacology for 757.

Materialized drugs are tagged `provenance='ChEMBL:materialized_orphan'` so they can
be included or excluded explicitly. The legacy 78 keep `provenance='unknown'`, which
is what `--cohort core` filters on downstream.

This script only INSERTS objects. It never edits or deletes a morphism.

Usage:
    python scripts/materialize_orphan_drugs.py --dry-run
    python scripts/materialize_orphan_drugs.py --apply
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from collections import Counter
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "drugs" / "tier1.db"

# Relations whose SOURCE is a drug acting on a protein target.
DRUG_ACTION_RELATIONS = {"inhibits", "activates", "targets", "binds", "modulates"}

PROVENANCE_TAG = "ChEMBL:materialized_orphan"


def find_orphans(conn: sqlite3.Connection) -> tuple[dict[str, dict], list[str]]:
    """Return (orphan_name -> info, refusals). Refusals are endpoints we won't type."""
    objects = {r[0] for r in conn.execute("SELECT name FROM objects")}

    as_source: dict[str, Counter] = {}
    as_target: set[str] = set()
    chembl: dict[str, str] = {}

    for src, rel, tgt, prov in conn.execute(
        "SELECT source_name, name, target_name, provenance FROM morphisms"
    ):
        if src not in objects:
            as_source.setdefault(src, Counter())[rel] += 1
            if prov and prov.startswith("ChEMBL:") and src not in chembl:
                chembl[src] = prov.split(";")[0].strip()
        if tgt not in objects:
            as_target.add(tgt)

    orphans: dict[str, dict] = {}
    refusals: list[str] = []
    for name, rels in as_source.items():
        # Only materialize endpoints that act EXCLUSIVELY as a drug on targets.
        # Anything also appearing on the target side is likely a protein, not a drug.
        if name in as_target:
            refusals.append(f"{name}: appears as a morphism TARGET too - ambiguous type")
            continue
        if not set(rels).issubset(DRUG_ACTION_RELATIONS):
            refusals.append(f"{name}: non-drug relations {sorted(set(rels) - DRUG_ACTION_RELATIONS)}")
            continue
        if name not in chembl:
            refusals.append(f"{name}: no ChEMBL provenance")
            continue
        orphans[name] = {"chembl": chembl[name], "n_targets": sum(rels.values())}

    # Any orphan that only ever appears as a target is a data problem, not a drug.
    for name in sorted(as_target - set(as_source) - objects):
        refusals.append(f"{name}: orphan appears ONLY as a target - not materialized")

    return orphans, refusals


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--db", default=str(DB_PATH))
    ap.add_argument("--apply", action="store_true", help="Write to the database.")
    ap.add_argument("--dry-run", action="store_true", help="Report only (default).")
    args = ap.parse_args()

    if not args.apply:
        args.dry_run = True

    conn = sqlite3.connect(args.db)
    before = conn.execute("SELECT COUNT(*) FROM objects WHERE type_name='Drug'").fetchone()[0]
    orphans, refusals = find_orphans(conn)

    print(f"database:              {args.db}")
    print(f"Drug objects before:   {before}")
    print(f"orphans to materialize:{len(orphans)}")
    print(f"refused (not typed):   {len(refusals)}")
    if refusals:
        print("\n  refusal reasons (first 10):")
        for r in refusals[:10]:
            print(f"    - {r}")

    if args.dry_run:
        print("\nDRY RUN - nothing written. Re-run with --apply to commit.")
        return 0

    rows = [
        (
            name,
            "Drug",
            json.dumps({"source": "ChEMBL", "chembl_id": info["chembl"].split(":", 1)[1],
                        "n_target_edges": info["n_targets"], "materialized": True}),
            PROVENANCE_TAG,
        )
        for name, info in sorted(orphans.items())
    ]
    conn.executemany(
        "INSERT OR IGNORE INTO objects (name, type_name, metadata, provenance) VALUES (?,?,?,?)",
        rows,
    )
    conn.commit()

    after = conn.execute("SELECT COUNT(*) FROM objects WHERE type_name='Drug'").fetchone()[0]
    dangling = conn.execute(
        "SELECT COUNT(*) FROM morphisms WHERE source_name NOT IN (SELECT name FROM objects)"
        "   OR target_name NOT IN (SELECT name FROM objects)"
    ).fetchone()[0]
    total = conn.execute("SELECT COUNT(*) FROM morphisms").fetchone()[0]
    print(f"\nDrug objects after:    {after}  (+{after - before})")
    print(f"dangling edges now:    {dangling}/{total} ({100*dangling/total:.1f}%)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
