#!/usr/bin/env python3
"""
Trace a drug-repurposing prediction back to evidence.

Outputs the mechanistic chains and provenance for each edge,
so a wet-lab scientist can verify the reasoning.

Usage:
    python validation/trace_prediction.py Erlotinib Colorectal_Cancer
    python validation/trace_prediction.py --top 10 Melanoma
    python validation/trace_prediction.py --all
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from data.store import KomposOSStore
from core.evidence_classification import classify_evidence
from validation.repurposing_benchmark import (
    DB_PATH,
    drug_disease_pairs,
    load_full_typed_view,
    make_strategies,
    score_pair,
)
from oracle.strategies import REPURPOSING_INTERMEDIATE_TYPES


PROTEIN_TYPES = REPURPOSING_INTERMEDIATE_TYPES


def _build_provenance_index(db_path: str) -> dict[tuple[str, str, str], dict]:
    """Build a lookup from edge key to provenance and derived audit fields."""
    import sqlite3
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    index = {}
    cursor.execute("""
        SELECT source_name, target_name, name, provenance, evidence_tier,
               quantitative_value, value_unit, metadata
        FROM morphisms
    """)
    for source, target, relation, prov, tier, quant_val, quant_unit, metadata in cursor.fetchall():
        classification = classify_evidence(prov, metadata, tier, quant_val)
        index[(source, target, relation)] = {
            "provenance": prov or "unknown",
            "evidence_tier": tier or "HYPOTHESIS",
            "quantitative_value": quant_val,
            "value_unit": quant_unit,
            **classification.to_dict(),
        }

    conn.close()
    return index


def trace_pair(category, drug: str, disease: str, strategies=None,
               provenance_index=None):
    """Return a structured trace for one drug-disease prediction."""
    score = 0.0
    strategy_votes = []
    if strategies:
        score, strategy_votes = score_pair(strategies, drug, disease)

    # Find mechanistic paths (exclude direct Drug->Disease edge)
    paths = category.find_paths(drug, disease, max_length=4)
    chains = []
    for path in paths:
        if not hasattr(path, "morphism_ids") or len(path.morphism_ids) < 2:
            continue

        edges = []
        for mid in path.morphism_ids:
            relation, pair = mid.split(":", 1) if ":" in mid else ("unknown", mid)
            src, tgt = pair.split("->", 1)
            # Look up the actual morphism for confidence/metadata
            confidence = 0.0
            evidence_type = "uncurated"
            for mor in category.morphisms():
                if mor.source == src and mor.target == tgt and mor.name == relation:
                    confidence = mor.confidence
                    meta = mor.metadata if hasattr(mor, "metadata") else {}
                    evidence_type = meta.get("evidence_type", "uncurated")
                    break
            # Get provenance and evidence_tier from SQLite index (bypasses Category loader gap)
            provenance = "unknown"
            evidence_tier = "HYPOTHESIS"
            quant_value = None
            quant_unit = None
            if provenance_index:
                prov_data = provenance_index.get((src, tgt, relation), {})
                provenance = prov_data.get("provenance", "unknown")
                evidence_tier = prov_data.get("evidence_tier", "HYPOTHESIS")
                quant_value = prov_data.get("quantitative_value")
                quant_unit = prov_data.get("value_unit")
                source_type = prov_data.get("source_type", "unknown_or_internal")
                validation_status = prov_data.get("validation_status", "unclassified")
                citation_status = prov_data.get("citation_status", "no_source")
                quantitative_status = prov_data.get("quantitative_status", "no_quantitative_value")
            else:
                source_type = "unknown_or_internal"
                validation_status = "unclassified"
                citation_status = "no_source"
                quantitative_status = "no_quantitative_value"
            tgt_obj = category.get(tgt)
            edges.append({
                "source": src,
                "relation": relation,
                "target": tgt,
                "target_type": tgt_obj.type_name if tgt_obj else "?",
                "confidence": confidence,
                "provenance": provenance,
                "evidence_tier": evidence_tier,
                "source_type": source_type,
                "validation_status": validation_status,
                "citation_status": citation_status,
                "quantitative_status": quantitative_status,
                "evidence_type": evidence_type,
                "quantitative_value": quant_value,
                "value_unit": quant_unit,
            })

        chains.append({
            "path_confidence": path.weight,
            "edges": edges,
        })

    # Sort by path confidence descending
    chains.sort(key=lambda c: -c["path_confidence"])

    return {
        "drug": drug,
        "disease": disease,
        "score": score,
        "strategy_votes": strategy_votes,
        "n_chains": len(chains),
        "chains": chains,
    }


def print_trace(trace):
    """Print a human-readable trace."""
    drug = trace["drug"]
    disease = trace["disease"]

    print(f"{'=' * 70}")
    print(f"  {drug} -> {disease}")
    print(f"  Score: {trace['score']:.4f}    Chains: {trace['n_chains']}")
    if trace["strategy_votes"]:
        votes_str = ", ".join(
            f"{name}={conf:.3f}" for name, conf in trace["strategy_votes"]
        )
        print(f"  Votes: {votes_str}")
    print(f"{'=' * 70}")

    if not trace["chains"]:
        print("  No mechanistic paths found.")
        print()
        return

    for i, chain in enumerate(trace["chains"], 1):
        print(f"\n  Chain {i} (confidence: {chain['path_confidence']:.4f})")
        print(f"  {'-' * 60}")
        for edge in chain["edges"]:
            prov = edge["provenance"]
            if prov == "unknown":
                prov_str = "[NEEDS CITATION]"
            else:
                prov_str = f"[{prov}]"
            print(
                f"    {edge['source']} --[{edge['relation']}]--> "
                f"{edge['target']} ({edge['target_type']})"
            )
            print(
                f"      conf={edge['confidence']:.2f}  "
                f"evidence={edge['evidence_type']}  "
                f"{prov_str}"
            )
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Trace drug-repurposing predictions to mechanistic evidence."
    )
    parser.add_argument("drug", nargs="?", help="Drug name")
    parser.add_argument("disease", nargs="?", help="Disease name")
    parser.add_argument(
        "--top", type=int, default=0,
        help="Show top N novel predictions for a disease (drug arg = disease name)",
    )
    parser.add_argument("--all", action="store_true", help="Trace all 16 known positives")
    parser.add_argument("--db", default=DB_PATH)
    args = parser.parse_args()

    category, _ = load_full_typed_view(args.db)
    drugs, diseases, positives = drug_disease_pairs(category)
    strategies = make_strategies(category)
    prov_index = _build_provenance_index(args.db)

    if args.all:
        for drug, disease in sorted(positives):
            trace = trace_pair(category, drug, disease, strategies, prov_index)
            print_trace(trace)
        return

    if args.top and args.drug:
        # Treat first arg as disease, find top novel predictions
        target_disease = args.drug
        if target_disease not in [d for d in diseases]:
            print(f"Disease '{target_disease}' not found. Available: {diseases}")
            return 1

        scored = []
        for drug in drugs:
            if (drug, target_disease) in positives:
                continue  # Skip known positives
            score, votes = score_pair(strategies, drug, target_disease)
            if score > 0:
                scored.append((drug, score, votes))

        scored.sort(key=lambda x: -x[1])
        print(f"Top {args.top} novel predictions for {target_disease}")
        print(f"(Known positives excluded)\n")

        for drug, score, votes in scored[: args.top]:
            trace = trace_pair(category, drug, target_disease, strategies, prov_index)
            print_trace(trace)
        return

    if not args.drug or not args.disease:
        parser.print_help()
        return 1

    trace = trace_pair(category, args.drug, args.disease, strategies, prov_index)
    print_trace(trace)


if __name__ == "__main__":
    raise SystemExit(main() or 0)
