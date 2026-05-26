#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""
Integrate validated new extractions into database.

Process:
1. Load validated extractions
2. Load search metadata (which drugs/diseases/proteins each PMID relates to)
3. Map extractions to database edges
4. Update morphisms with quantitative values
5. Upgrade to MEASURED tier if confidence ≥ 0.7
"""

import json
import sqlite3
import sys
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))

DB_PATH = "data/drugs/tier1.db"
CONFIDENCE_THRESHOLD = 0.7


def load_search_metadata():
    """Load metadata about which PMID relates to which drug/disease/protein pairs."""
    with open("data/pubmed_quantitative_search.json", "r", encoding="utf-8") as f:
        search_data = json.load(f)

    return search_data["metadata"]


def load_validated_extractions():
    """Load validated extractions."""
    with open("data/new_pmid_extractions.json", "r", encoding="utf-8") as f:
        extractions = json.load(f)

    with open("data/new_pmid_validation_results.json", "r", encoding="utf-8") as f:
        validations = json.load(f)

    # Filter to only valid extractions
    valid_pmids = set()
    for v in validations:
        if v['valid']:
            valid_pmids.add(v['pmid'])

    return {pmid: data for pmid, data in extractions.items() if pmid in valid_pmids}


def find_relevant_edges(conn, pmid, metadata_list, evidence_type):
    """
    Find database edges that this PMID extraction could apply to.

    Args:
        pmid: PubMed ID
        metadata_list: List of search metadata for this PMID
        evidence_type: Type of extraction (ic50, mutation_frequency, etc.)

    Returns:
        List of (morphism_id, source_name, target_name) tuples
    """
    cursor = conn.cursor()
    relevant_edges = []

    for meta in metadata_list:
        search_type = meta["type"]

        if search_type == "drug_disease":
            drug = meta["drug"]
            disease = meta["disease"]

            # Find Drug->Disease edge
            cursor.execute("""
                SELECT id, source_name, target_name
                FROM morphisms
                WHERE source_name = ? AND target_name = ?
            """, (drug, disease))

            rows = cursor.fetchall()
            relevant_edges.extend(rows)

            # Also find Drug->Protein->Disease paths
            cursor.execute("""
                SELECT DISTINCT m1.id, m1.source_name, m1.target_name
                FROM morphisms m1
                JOIN objects src ON m1.source_name = src.name
                JOIN objects tgt ON m1.target_name = tgt.name
                WHERE m1.source_name = ?
                AND src.type_name = 'Drug'
                AND tgt.type_name = 'Protein'
            """, (drug,))

            rows = cursor.fetchall()
            relevant_edges.extend(rows)

        elif search_type == "protein_mutation":
            protein = meta["protein"]
            disease = meta["disease"]

            # Find Protein->Disease edge
            cursor.execute("""
                SELECT id, source_name, target_name
                FROM morphisms
                WHERE source_name = ? AND target_name = ?
            """, (protein, disease))

            rows = cursor.fetchall()
            relevant_edges.extend(rows)

        elif search_type == "drug_target":
            drug = meta.get("drug")
            protein = meta.get("protein")

            if drug and protein:
                # Find Drug->Protein edge
                cursor.execute("""
                    SELECT id, source_name, target_name
                    FROM morphisms
                    WHERE source_name = ? AND target_name = ?
                """, (drug, protein))

                rows = cursor.fetchall()
                relevant_edges.extend(rows)

    return relevant_edges


def update_morphism_with_extraction(conn, morphism_id, pmid, evidence_type, value, unit, confidence, context):
    """Update a morphism with NLP-extracted quantitative data."""
    cursor = conn.cursor()

    # Load existing metadata
    cursor.execute("SELECT metadata, evidence_tier FROM morphisms WHERE id = ?", (morphism_id,))
    row = cursor.fetchone()

    if not row:
        return

    metadata_str, current_tier = row
    metadata = json.loads(metadata_str) if metadata_str else {}

    # Add NLP extraction
    if "nlp_extractions" not in metadata:
        metadata["nlp_extractions"] = []

    metadata["nlp_extractions"].append({
        "pmid": pmid,
        "evidence_type": evidence_type,
        "value": value,
        "unit": unit,
        "confidence": confidence,
        "context": context
    })

    # Upgrade tier if high confidence
    new_tier = current_tier
    if confidence >= CONFIDENCE_THRESHOLD and current_tier != "MEASURED":
        new_tier = "MEASURED"

    # Update morphism
    cursor.execute("""
        UPDATE morphisms
        SET quantitative_value = ?,
            value_unit = ?,
            evidence_tier = ?,
            metadata = ?
        WHERE id = ?
    """, (value, evidence_type, new_tier, json.dumps(metadata), morphism_id))


def main():
    print("="*70)
    print("DATABASE INTEGRATION - NEW EXTRACTIONS")
    print("="*70)
    print()

    conn = sqlite3.connect(DB_PATH)

    print("[1] Loading search metadata...")
    search_metadata = load_search_metadata()
    print(f"  Loaded metadata for {len(search_metadata)} PMIDs")

    print("\n[2] Loading validated extractions...")
    extractions = load_validated_extractions()
    print(f"  Loaded {len(extractions)} PMIDs with validated data")

    print("\n[3] Mapping extractions to database edges...")
    edges_updated = 0
    tier_upgrades = 0
    extractions_added = 0

    for pmid, pmid_data in extractions.items():
        if pmid not in search_metadata:
            print(f"  [WARN] PMID {pmid} has no search metadata, skipping")
            continue

        metadata_list = search_metadata[pmid]

        for ev_type, ev_list in pmid_data.items():
            for ev in ev_list:
                # Find relevant edges
                edges = find_relevant_edges(conn, pmid, metadata_list, ev_type)

                if not edges:
                    continue

                # Update each relevant edge
                for morphism_id, source, target in edges:
                    update_morphism_with_extraction(
                        conn, morphism_id, pmid,
                        ev_type, ev['value'], ev['unit'],
                        ev['confidence'], ev['context']
                    )

                    edges_updated += 1
                    extractions_added += 1

                    if ev['confidence'] >= CONFIDENCE_THRESHOLD:
                        tier_upgrades += 1

                    print(f"  [ADD] {source} -> {target}: {ev_type}={ev['value']} (conf: {ev['confidence']:.2f})")

    # Commit changes
    conn.commit()

    print("\n" + "="*70)
    print("INTEGRATION COMPLETE")
    print("="*70)
    print(f"Edges updated: {edges_updated}")
    print(f"Extractions added: {extractions_added}")
    print(f"Tier upgrades to MEASURED: {tier_upgrades}")

    # Final statistics
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM morphisms WHERE quantitative_value IS NOT NULL")
    total_quantified = cursor.fetchone()[0]

    cursor.execute("SELECT evidence_tier, COUNT(*) FROM morphisms GROUP BY evidence_tier")
    print("\nEvidence tier distribution:")
    for tier, count in cursor.fetchall():
        print(f"  {tier}: {count}")

    print(f"\nTotal edges with quantitative values: {total_quantified}")

    conn.close()

    print("\nNext steps:")
    print("  1. Commit updated database")
    print("  2. Re-run benchmark to see impact")
    print("  3. Update documentation")


if __name__ == "__main__":
    main()
