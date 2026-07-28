#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""External drug-disease validation against local Hetionet files.

This script is intentionally executable and versioned. It derives external
positive pairs from local Hetionet CtD edges, maps them by exact node name to
current KOMPOSOS drug/disease names, excludes pairs already present as internal
Drug->Disease labels, then scores the remaining external positives against
open-world unlabeled pairs.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from validation.holdout_utils import evaluate_holdout, print_metrics
from validation.repurposing_benchmark import (
    DB_PATH,
    drug_disease_pairs,
    load_full_typed_view,
)


VERSION = "2026-05-27"
DEFAULT_NODES = "data/external/hetionet_nodes.tsv"
DEFAULT_EDGES = "data/external/hetionet_edges.sif.gz"


def _normalize_name(name: str) -> str:
    return name.strip().lower().replace("_", " ")


def load_hetionet_ctd_pairs(
    nodes_path: str,
    edges_path: str,
    db_drugs: list[str],
    db_diseases: list[str],
) -> set[tuple[str, str]]:
    """Map local Hetionet Compound-treats-Disease edges to DB names."""
    nodes: dict[str, dict[str, str]] = {}
    with open(nodes_path, encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            nodes[row["id"]] = row

    drug_by_norm = {_normalize_name(name): name for name in db_drugs}
    disease_by_norm = {_normalize_name(name): name for name in db_diseases}

    pairs: set[tuple[str, str]] = set()
    with gzip.open(edges_path, "rt", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            if row["metaedge"] != "CtD":
                continue
            source = nodes.get(row["source"])
            target = nodes.get(row["target"])
            if not source or not target:
                continue
            drug = drug_by_norm.get(_normalize_name(source["name"]))
            disease = disease_by_norm.get(_normalize_name(target["name"]))
            if drug and disease:
                pairs.add((drug, disease))
    return pairs


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run external validation using local Hetionet CtD edges."
    )
    parser.add_argument("--db", default=DB_PATH, help="Path to tier1 SQLite database.")
    parser.add_argument("--nodes", default=DEFAULT_NODES, help="Hetionet nodes TSV.")
    parser.add_argument("--edges", default=DEFAULT_EDGES, help="Hetionet edges SIF.GZ.")
    parser.add_argument(
        "--hide-training-labels",
        action="store_true",
        help="Remove all internal direct Drug->Disease labels while scoring.",
    )
    args = parser.parse_args()

    category, _ = load_full_typed_view(
        args.db,
        remove_direct_labels=args.hide_training_labels,
    )
    base_category, _ = load_full_typed_view(args.db)
    drugs, diseases, internal_positives = drug_disease_pairs(base_category)

    hetionet_pairs = load_hetionet_ctd_pairs(
        args.nodes,
        args.edges,
        drugs,
        diseases,
    )
    external_positives = hetionet_pairs - internal_positives
    if not external_positives:
        raise SystemExit(
            "No external Hetionet positives mapped outside internal labels. "
            "Check --nodes/--edges inputs."
        )

    candidate_pairs = [(drug, disease) for drug in drugs for disease in diseases]
    metrics = evaluate_holdout(
        category,
        external_positives,
        candidate_pairs,
        name=f"hetionet_ctd_external_v{VERSION}",
        exclude_pairs=internal_positives,
    )

    print(f"Version:    {VERSION}")
    print(f"Input:      {args.nodes}; {args.edges}")
    print(f"Mapped CtD: {len(hetionet_pairs)} total, {len(external_positives)} external positives")
    print_metrics(metrics)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
