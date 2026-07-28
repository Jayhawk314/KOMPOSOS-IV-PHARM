#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""Calibrate ranking scores against an explicit benchmark protocol.

This does not change strategy signals or ranking scores.  It creates a separate
artifact mapping score bins to observed benchmark label rates.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from validation.ranking_calibration import (
    CALIBRATION_TARGET,
    CALIBRATION_WARNING,
    DEFAULT_CALIBRATION_PATH,
    VERSION,
    build_quantile_bins,
    calibrate_score,
)
from validation.repurposing_benchmark import (
    DB_PATH,
    drug_disease_pairs,
    load_full_typed_view,
    make_strategies,
    pairwise_auroc,
    score_pair,
)


def score_benchmark_pairs(db_path: str, protocol: str) -> tuple[list[float], list[int], dict]:
    """Return ranking scores and labels for a named calibration protocol."""
    base_category, _ = load_full_typed_view(db_path)
    drugs, diseases, positives = drug_disease_pairs(base_category)

    if protocol == "remove_direct_labels":
        category, missing_endpoints = load_full_typed_view(
            db_path,
            remove_direct_labels=True,
        )
    elif protocol == "in_sample":
        category = base_category
        missing_endpoints = []
    else:
        raise ValueError(f"Unsupported protocol: {protocol}")

    strategies = make_strategies(category)
    scores: list[float] = []
    labels: list[int] = []
    for drug in drugs:
        for disease in diseases:
            score, _ = score_pair(strategies, drug, disease, fail_on_error=True)
            scores.append(score)
            labels.append(1 if (drug, disease) in positives else 0)

    metadata = {
        "view": "full_typed",
        "protocol": protocol,
        "n_drugs": len(drugs),
        "n_diseases": len(diseases),
        "n_pairs": len(scores),
        "n_positives": sum(labels),
        "n_negatives": len(labels) - sum(labels),
        "missing_endpoints": missing_endpoints,
    }
    return scores, labels, metadata


def build_report(scores: list[float], labels: list[int], metadata: dict, n_bins: int) -> dict:
    bins = build_quantile_bins(scores, labels, n_bins=n_bins)
    calibrated = [calibrate_score(score, {"bins": bins}) for score in scores]
    brier = sum((float(pred) - label) ** 2 for pred, label in zip(calibrated, labels)) / len(labels)
    auroc, _, _, _ = pairwise_auroc(scores, labels)

    return {
        "version": VERSION,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "score_name": "ranking_score",
        "calibration_target": CALIBRATION_TARGET,
        "warning": CALIBRATION_WARNING,
        **metadata,
        "positive_prevalence": round(sum(labels) / len(labels), 6),
        "score_min": round(min(scores), 6),
        "score_max": round(max(scores), 6),
        "score_mean": round(sum(scores) / len(scores), 6),
        "auroc": round(auroc, 6),
        "n_bins_requested": n_bins,
        "brier_calibrated_label_rate": round(brier, 6),
        "bins": bins,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create a benchmark-label-rate calibration artifact for ranking scores."
    )
    parser.add_argument("--db", default=DB_PATH, help="Path to tier1 SQLite database.")
    parser.add_argument(
        "--protocol",
        choices=["remove_direct_labels", "in_sample"],
        default="remove_direct_labels",
        help="Benchmark protocol used to derive calibration bins.",
    )
    parser.add_argument("--bins", type=int, default=10, help="Number of score quantile bins.")
    parser.add_argument(
        "--out",
        default=str(DEFAULT_CALIBRATION_PATH),
        help="Output JSON artifact path.",
    )
    args = parser.parse_args()

    scores, labels, metadata = score_benchmark_pairs(args.db, args.protocol)
    report = build_report(scores, labels, metadata, args.bins)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
        handle.write("\n")

    print(f"Version:        {report['version']}")
    print(f"Protocol:       {report['protocol']}")
    print(f"Labels:         {report['n_positives']} positives, {report['n_negatives']} negatives")
    print(f"Score AUROC:    {report['auroc']:.6f}")
    print(f"Prevalence:     {report['positive_prevalence']:.6f}")
    print(f"Calibrated Brier (benchmark label rate): {report['brier_calibrated_label_rate']:.6f}")
    print(f"Warning:        {report['warning']}")
    print(f"Wrote:          {out_path}")
    print("Bins:")
    for row in report["bins"]:
        print(
            f"  {row['bin']:2d}  "
            f"{row['score_min']:.6f}-{row['score_max']:.6f}  "
            f"n={row['n']:4d}  pos={row['positives']:2d}  "
            f"empirical={row['empirical_label_rate']:.4f}  "
            f"monotone={row['monotonic_label_rate']:.4f}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
