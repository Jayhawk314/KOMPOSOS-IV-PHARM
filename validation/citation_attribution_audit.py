#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""Read-only citation and quantitative-attribution audit for graph edges."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sqlite3
import sys
from collections import Counter
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.evidence_classification import classify_evidence, extract_pmids
from validation.repurposing_benchmark import DB_PATH


VERSION = "2026-05-27"


RELATION_TERMS = {
    "treats": ("treat", "therapy", "therapeutic", "response", "survival", "approved"),
    "inhibits": ("inhibit", "inhibitor", "ic50", "block", "suppress"),
    "activates": ("activat", "agonist", "increase"),
    "associated_with": ("associated", "association", "correlat", "risk"),
    "driver_of": ("driver", "mutation", "oncogenic", "causal"),
    "mutated_in": ("mutat", "variant", "alteration"),
    "expressed_in": ("express", "overexpress"),
    "phosphorylates": ("phosphorylat",),
    "regulates": ("regulat",),
}


def _safe_json(text: str | None) -> Any:
    if not text:
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {}


def _contains_name(text: str, name: str) -> bool:
    norm_text = text.lower().replace("_", " ")
    norm_name = name.lower().replace("_", " ")
    return norm_name in norm_text


def _contexts(metadata: Any) -> list[str]:
    contexts: list[str] = []
    if isinstance(metadata, dict):
        for item in metadata.get("nlp_extractions", []) or []:
            if isinstance(item, dict):
                for key in ("context", "abstract", "snippet"):
                    if item.get(key):
                        contexts.append(str(item[key]))
    return contexts


def audit_row(row: sqlite3.Row) -> dict[str, Any]:
    metadata = _safe_json(row["metadata"])
    metadata_text = json.dumps(metadata, sort_keys=True) if metadata else (row["metadata"] or "")
    provenance = row["provenance"] or ""
    classification = classify_evidence(
        provenance,
        metadata,
        row["evidence_tier"],
        row["quantitative_value"],
    )
    pmids = extract_pmids(provenance, metadata_text)
    contexts = _contexts(metadata)
    context_text = " ".join(contexts)
    all_text = f"{provenance} {metadata_text} {context_text}"

    source_mentioned = _contains_name(all_text, row["source_name"])
    target_mentioned = _contains_name(all_text, row["target_name"])
    endpoint_context_match = bool(context_text) and (
        _contains_name(context_text, row["source_name"])
        or _contains_name(context_text, row["target_name"])
    )

    terms = RELATION_TERMS.get(row["name"], (row["name"].replace("_", " "),))
    relation_support = any(term in all_text.lower() for term in terms)
    relation_context_support = bool(context_text) and any(
        term in context_text.lower() for term in terms
    )

    nlp_extractions = metadata.get("nlp_extractions", []) if isinstance(metadata, dict) else []
    quantitative_contexts = [
        item for item in nlp_extractions
        if isinstance(item, dict) and item.get("value") is not None
    ]
    quantitative_value_support = "none"
    if row["quantitative_value"] is not None:
        quantitative_value_support = "structured_column"
    elif quantitative_contexts:
        if endpoint_context_match and relation_context_support:
            quantitative_value_support = "nlp_context_matches_endpoint_and_relation"
        elif endpoint_context_match:
            quantitative_value_support = "nlp_context_matches_endpoint_only"
        else:
            quantitative_value_support = "nlp_context_not_edge_specific"

    risk_flags = []
    if row["evidence_tier"] == "MEASURED" and classification.validation_status.endswith("tier_mismatch"):
        risk_flags.append("measured_tier_mismatch")
    if quantitative_contexts and not endpoint_context_match:
        risk_flags.append("quantitative_not_endpoint_specific")
    if pmids and not contexts and classification.source_type == "literature_citation":
        risk_flags.append("pmid_without_context")
    if not pmids and classification.citation_status == "no_source":
        risk_flags.append("missing_source")

    return {
        "morphism_id": row["id"],
        "source": row["source_name"],
        "relation": row["name"],
        "target": row["target_name"],
        "evidence_tier": row["evidence_tier"] or "",
        **classification.to_dict(),
        "pmid_count": len(pmids),
        "pmids": ";".join(sorted(pmids)),
        "has_context": bool(contexts),
        "has_full_text": False,
        "source_mentioned": source_mentioned,
        "target_mentioned": target_mentioned,
        "endpoint_context_match": endpoint_context_match,
        "relation_support_heuristic": relation_support,
        "relation_context_support": relation_context_support,
        "quantitative_value_support": quantitative_value_support,
        "risk_flags": ";".join(risk_flags),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a read-only citation attribution audit.")
    parser.add_argument("--db", default=DB_PATH, help="Path to tier1 SQLite database.")
    parser.add_argument("--out", default=None, help="Optional CSV output path.")
    parser.add_argument("--limit", type=int, default=0, help="Limit rows for quick checks.")
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    query = """
        SELECT id, source_name, target_name, name, provenance, evidence_tier,
               quantitative_value, value_unit, metadata
        FROM morphisms
        ORDER BY id
    """
    if args.limit:
        query += f" LIMIT {int(args.limit)}"
    cursor.execute(query)
    rows = [audit_row(row) for row in cursor.fetchall()]
    conn.close()

    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()) if rows else [])
            writer.writeheader()
            writer.writerows(rows)

    source_counts = Counter(row["source_type"] for row in rows)
    status_counts = Counter(row["validation_status"] for row in rows)
    risk_counts = Counter(
        flag
        for row in rows
        for flag in row["risk_flags"].split(";")
        if flag
    )

    print(f"Version:   {VERSION}")
    print(f"Rows:      {len(rows)}")
    if args.out:
        print(f"CSV:       {args.out}")
    print("Source types:")
    for key, value in source_counts.most_common():
        print(f"  {key:40s} {value}")
    print("Validation statuses:")
    for key, value in status_counts.most_common():
        print(f"  {key:40s} {value}")
    print("Risk flags:")
    for key, value in risk_counts.most_common():
        print(f"  {key:40s} {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
