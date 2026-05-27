#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Disease-level holdout validation.

For each disease with at least --min-positives approved labels, all labels for
that disease are removed from the training graph and drugs are ranked for that
disease only.
"""

from __future__ import annotations

import argparse
import statistics
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from validation.holdout_utils import evaluate_holdout, print_metrics
from validation.repurposing_benchmark import DB_PATH, drug_disease_pairs, load_full_typed_view


VERSION = "2026-05-27"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run disease-level holdout validation.")
    parser.add_argument("--db", default=DB_PATH, help="Path to tier1 SQLite database.")
    parser.add_argument("--min-positives", type=int, default=2, help="Minimum labels per disease fold.")
    args = parser.parse_args()

    base_category, _ = load_full_typed_view(args.db)
    drugs, _, positives = drug_disease_pairs(base_category)

    by_disease: dict[str, set[tuple[str, str]]] = defaultdict(set)
    for pair in positives:
        by_disease[pair[1]].add(pair)

    fold_metrics = []
    for disease, heldout in sorted(by_disease.items()):
        if len(heldout) < args.min_positives:
            continue
        train_category, _ = load_full_typed_view(args.db, skip_pairs=heldout)
        candidate_pairs = [(drug, disease) for drug in drugs]
        metrics = evaluate_holdout(
            train_category,
            heldout,
            candidate_pairs,
            name=f"disease_holdout_{disease}_v{VERSION}",
        )
        fold_metrics.append(metrics)
        print_metrics(metrics)
        print("")

    if not fold_metrics:
        raise SystemExit("No disease folds met --min-positives")

    aurocs = [m.auroc for m in fold_metrics]
    auprcs = [m.auprc for m in fold_metrics]
    print("Summary")
    print(f"Version:       {VERSION}")
    print(f"Folds:         {len(fold_metrics)}")
    print(f"Mean AUROC:    {statistics.mean(aurocs):.6f}")
    print(f"Median AUROC:  {statistics.median(aurocs):.6f}")
    print(f"Mean AUPRC:    {statistics.mean(auprcs):.6f}")
    print(f"Median AUPRC:  {statistics.median(auprcs):.6f}")
    print(f"Range AUROC:   {min(aurocs):.6f} - {max(aurocs):.6f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
