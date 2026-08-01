#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""Rank unlabelled drug-disease pairs by how much curating them would change the evaluation.

Roadmap step 5 (Phase 0.5). The label set has 50 of 15,140 pairs. Curating the
other 15,090 by hand is not a plan, and most of them would not matter: a pair
that ranks 700th of 757 changes no metric whichever way it is labelled.

What DOES matter is a pair that the ranker puts near the top of a disease while
the gold set is silent about it. Every one of those is currently counted as a
false positive, and each is either (a) a genuine miss the system should be
credited with catching, or (b) a genuine false positive. Today we cannot tell,
which is the whole reason no precision claim is defensible.

So this script emits a worklist ordered by IMPACT, defined as the reciprocal of
the pair's rank within its disease. Curating the top of this list buys more
evaluation validity per hour of a human's time than anything else available.

Salt forms are collapsed: "Dacomitinib" and "Dacomitinib Anhydrous" are one
curation task, not two, and the graph currently treats them as separate drugs
occupying separate ranks with identical scores.

Run:
    python -m validation.build_label_worklist
    python -m validation.build_label_worklist --top-n 15 --out reports/label_worklist.csv
"""
from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from validation.repurposing_benchmark import (
    DB_PATH,
    DEFAULT_EXCLUDE_PROVENANCE,
    drug_disease_pairs,
    load_full_typed_view,
    make_strategies,
    score_pair,
)
from validation.nonobvious import normalize_drug_name

LABELS = "data/labels/evaluation_labels_v1.csv"


def load_labelled_pairs(path: str) -> set[tuple[str, str]]:
    """Pairs already carrying ANY status, keyed on the normalized INN."""
    out = set()
    try:
        with open(path, encoding="utf-8-sig") as fh:
            for row in csv.DictReader(fh):
                out.add((normalize_drug_name(row["drug"]), row["disease"]))
                if row.get("drug_inn"):
                    out.add((normalize_drug_name(row["drug_inn"]), row["disease"]))
    except FileNotFoundError:
        print(f"[worklist] no label file at {path}; treating everything as unlabelled")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--db", default=DB_PATH)
    ap.add_argument("--labels", default=LABELS)
    ap.add_argument("--top-n", type=int, default=20,
                    help="How many ranks per disease count as 'near the top'.")
    ap.add_argument("--out", default="reports/label_worklist.csv")
    args = ap.parse_args()

    category, _ = load_full_typed_view(
        args.db, remove_direct_labels=True, cohort="all",
        exclude_provenance=DEFAULT_EXCLUDE_PROVENANCE,
    )
    labelled_view, _ = load_full_typed_view(
        args.db, cohort="all", exclude_provenance=DEFAULT_EXCLUDE_PROVENANCE)
    _, _, graph_positives = drug_disease_pairs(labelled_view)

    drugs = sorted(o.name for o in category.objects() if o.type_name == "Drug")
    diseases = sorted(o.name for o in category.objects() if o.type_name == "Disease")
    strategies = make_strategies(category)
    known = load_labelled_pairs(args.labels)

    rows = []
    coverage = []
    for disease in diseases:
        print(f"[worklist] scoring {disease} ...", flush=True)
        scored = []
        for drug in drugs:
            score, votes = score_pair(strategies, drug, disease)
            if votes:
                scored.append((score, drug))
        scored.sort(reverse=True)

        # collapse salt forms, keeping the best-ranked spelling
        seen_inn, collapsed = set(), []
        for score, drug in scored:
            inn = normalize_drug_name(drug)
            if inn in seen_inn:
                continue
            seen_inn.add(inn)
            collapsed.append((score, drug, inn))

        top = collapsed[: args.top_n]
        n_unlab = 0
        for rank, (score, drug, inn) in enumerate(top, 1):
            in_graph = (drug, disease) in graph_positives
            in_labels = (inn, disease) in known
            if in_graph or in_labels:
                continue
            n_unlab += 1
            rows.append({
                "impact": round(1.0 / rank, 4),
                "rank_in_disease": rank,
                "disease": disease,
                "drug": drug,
                "drug_inn": inn,
                "score": round(score, 4),
                "status_to_determine": "",
                "biomarker_restriction": "",
                "line_of_therapy": "",
                "approval_year": "",
                "source_url": "",
                "curator_note": "",
            })
        coverage.append((disease, n_unlab, len(top)))

    rows.sort(key=lambda r: (-r["impact"], r["disease"]))

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]) if rows else ["impact"])
        w.writeheader()
        w.writerows(rows)

    print("\n" + "=" * 72)
    print(f"  Label curation worklist - top {args.top_n} per disease")
    print("=" * 72)
    print(f"{'disease':<24} {'unlabelled in top':>18}")
    print("-" * 72)
    for disease, n_unlab, n_top in sorted(coverage, key=lambda c: -c[1]):
        bar = "#" * n_unlab
        print(f"{disease:<24} {n_unlab:>3}/{n_top:<3}  {bar}")
    total_unlab = sum(c[1] for c in coverage)
    total_top = sum(c[2] for c in coverage)
    print("-" * 72)
    print(f"{'TOTAL':<24} {total_unlab:>3}/{total_top}")
    print()
    print(f"  {total_unlab} of the {total_top} highest-ranked pairs across all")
    print(f"  {len(diseases)} diseases have NO label of any kind. Every one is")
    print("  currently scored as a false positive by default.")
    print()
    print("  This is the number that makes a precision claim indefensible today.")
    print("  It is not evidence the ranker is good - a pair being unlabelled says")
    print("  nothing about whether it is right. It says the question is open.")
    print()
    print(f"  wrote {len(rows)} curation tasks to {out}")
    print("  Fill `status_to_determine` (APPROVED/IN_TRIAL/PRECLINICAL/UNKNOWN)")
    print("  with a source_url, then merge into data/labels/.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
