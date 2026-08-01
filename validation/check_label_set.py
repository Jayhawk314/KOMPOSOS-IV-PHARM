#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""Validate the Phase 0.5 evaluation label set and report how incomplete it is.

    python -m validation.check_label_set

Checks structure, resolves every drug and disease against the graph, and - the
point of the script - reports the SIZE OF THE GAP rather than pretending the file
is finished. A label set that quietly looks complete is worse than no label set,
because it makes an indefensible precision claim feel defensible.

Exits non-zero only on structural faults (bad status, unresolvable node,
duplicate key). Incompleteness is reported, not failed, because incompleteness is
the current known state.
"""
from __future__ import annotations

import argparse
import csv
import sqlite3
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from validation.repurposing_benchmark import DB_PATH

LABELS = "data/labels/evaluation_labels_v1.csv"

VALID_STATUS = {"APPROVED", "APPROVED_TUMOR_AGNOSTIC", "IN_TRIAL", "PRECLINICAL",
                "SCREENED_NEGATIVE", "UNKNOWN"}
VALID_SOURCE = {"FDA_ONCOLOGY_ANNOUNCEMENT", "FDA_APPROVAL_LETTER",
                "CLINICALTRIALS_GOV", "INHERITED_UNVERIFIED"}
VALID_LINE = {"first_line", "later_line", "post_progression", "any", "unknown"}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--labels", default=LABELS)
    ap.add_argument("--db", default=DB_PATH)
    args = ap.parse_args()

    rows = list(csv.DictReader(open(args.labels, encoding="utf-8-sig")))
    conn = sqlite3.connect(args.db)
    drugs = {n for (n,) in conn.execute("SELECT name FROM objects WHERE type_name='Drug'")}
    diseases = {n for (n,) in conn.execute("SELECT name FROM objects WHERE type_name='Disease'")}
    conn.close()

    errors, warnings = [], []
    seen = set()

    for r in rows:
        rid = r["label_id"]
        key = (r["drug"], r["disease"])
        if key in seen:
            errors.append(f"{rid}: duplicate pair {key}")
        seen.add(key)
        if r["status"] not in VALID_STATUS:
            errors.append(f"{rid}: bad status {r['status']!r}")
        if r["source_type"] not in VALID_SOURCE:
            errors.append(f"{rid}: bad source_type {r['source_type']!r}")
        if r["line_of_therapy"] not in VALID_LINE:
            errors.append(f"{rid}: bad line_of_therapy {r['line_of_therapy']!r}")
        if r["drug"] not in drugs:
            errors.append(f"{rid}: drug {r['drug']!r} is not a node in the graph")
        if r["disease"] not in diseases:
            errors.append(f"{rid}: disease {r['disease']!r} is not a node in the graph")
        if r["source_type"] != "INHERITED_UNVERIFIED" and not r["source_url"]:
            errors.append(f"{rid}: claims a verified source type but has no source_url")
        if r["status"] == "APPROVED" and r["biomarker_restriction"] == "unknown":
            warnings.append(f"{rid}: approved but biomarker restriction unrecorded")
        if not r.get("combination_partner"):
            errors.append(f"{rid}: combination_partner is blank; use 'none' explicitly")

    status = Counter(r["status"] for r in rows)
    source = Counter(r["source_type"] for r in rows)
    verified = sum(1 for r in rows if r["source_type"] != "INHERITED_UNVERIFIED")

    print("=" * 72)
    print("  Evaluation label set - Phase 0.5")
    print("=" * 72)
    print(f"file        {args.labels}")
    print(f"rows        {len(rows)}")
    print(f"status      {dict(status)}")
    print(f"sources     {dict(source)}")
    print()

    print("COMPLETENESS")
    print("-" * 72)
    print(f"  cited to a primary source:  {verified}/{len(rows)}")
    print(f"  inherited without citation: {len(rows) - verified}/{len(rows)}")
    n_pairs = len(drugs) * len(diseases)
    print(f"  graph pair space:           {len(drugs)} drugs x {len(diseases)} diseases "
          f"= {n_pairs:,} pairs")
    print(f"  pairs with ANY label:       {len(seen):,} ({100.0*len(seen)/n_pairs:.2f}%)")
    print(f"  pairs that are UNKNOWN:     {n_pairs - len(seen):,}")
    print()
    print("  Every unlabelled pair is UNKNOWN, never a negative. Treating absence as")
    print("  a negative is the error that produced the contaminated temporal holdout.")
    print()

    agnostic = [r for r in rows if r["status"] == "APPROVED_TUMOR_AGNOSTIC"]
    if agnostic:
        print("TUMOUR-AGNOSTIC APPROVALS  (neither a hit nor a false positive)")
        print("-" * 72)
        for r in agnostic:
            print(f"  {r['drug']} -> {r['disease']}  ({r['biomarker_restriction']})")
        print()
        print("  These drugs are approvable in these diseases ONLY under a rare")
        print("  biomarker the graph cannot see. Scoring them as whole-disease hits")
        print("  would overstate; scoring them as false positives would understate.")
        print("  A metric that uses this file MUST decide explicitly how to treat")
        print("  this status - it is the reason the status exists.")
        print()

    combos = [r for r in rows if r.get("combination_partner", "none") not in ("none", "")]
    if combos:
        print("COMBINATION-ONLY APPROVALS")
        print("-" * 72)
        for r in combos:
            print(f"  {r['drug']} + {r['combination_partner']} -> {r['disease']}"
                  f"  ({r['biomarker_restriction']})")
        print()
        print("  These are NOT monotherapy approvals. Crediting the ranker with")
        print("  predicting them as single-drug indications would be an overstatement")
        print("  in the opposite direction from the one this label set exists to fix.")
        print()
    print("  This file is a SEED. Do not compute AUPRC or precision against it and")
    print("  present the result as a measurement of PHARM's performance.")
    print()

    if warnings:
        print(f"WARNINGS ({len(warnings)})")
        print("-" * 72)
        for w in warnings[:10]:
            print(f"  {w}")
        if len(warnings) > 10:
            print(f"  ... and {len(warnings) - 10} more")
        print()
        print("  A biomarker-restricted approval credited as a whole-disease label is an")
        print("  overstatement in the opposite direction. See data/labels/README.md.")
        print()

    if errors:
        print(f"ERRORS ({len(errors)})")
        print("-" * 72)
        for e in errors:
            print(f"  {e}")
        return 1

    print("structure OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
