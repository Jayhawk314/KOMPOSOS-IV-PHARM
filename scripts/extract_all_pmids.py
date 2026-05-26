#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""
Extract quantitative data from ALL PMIDs in the database.

This is the Phase 5 master script that:
1. Gets all unique PMIDs from tier1.db
2. Extracts IC50, response rates, hazard ratios, etc. using NLP
3. Updates morphisms with quantitative_value and upgrades to MEASURED tier
4. Generates validation report
"""

import sqlite3
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from nlp.pmid_extractor import PMIDExtractor, extract_from_pmid_list

DB_PATH = "data/drugs/tier1.db"


def get_all_pmids() -> dict:
    """
    Get all PMIDs from database with their associated edges.

    Returns:
        Dict mapping PMID -> list of (source, target, relation) tuples
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get all morphisms with PMIDs in provenance
    cursor.execute("SELECT source_name, target_name, name, provenance FROM morphisms")

    pmid_edges = {}
    for source, target, relation, prov in cursor.fetchall():
        if not prov:
            continue

        # Extract PMID from provenance
        import re
        pmids = re.findall(r'PMID:(\d+)', prov, re.IGNORECASE)

        for pmid in pmids:
            if pmid not in pmid_edges:
                pmid_edges[pmid] = []
            pmid_edges[pmid].append((source, target, relation))

    conn.close()

    print(f"Found {len(pmid_edges)} unique PMIDs in database")
    return pmid_edges


def update_morphism_with_extraction(source: str, target: str, relation: str,
                                    evidence_type: str, value: float, unit: str,
                                    confidence: float, pmid: str):
    """Update a morphism with extracted quantitative data."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get current morphism
    cursor.execute("""
        SELECT id, metadata, evidence_tier FROM morphisms
        WHERE source_name = ? AND target_name = ? AND name = ?
    """, (source, target, relation))

    result = cursor.fetchone()
    if not result:
        conn.close()
        return

    morph_id, metadata_str, current_tier = result

    # Parse metadata
    try:
        metadata = json.loads(metadata_str) if metadata_str else {}
    except:
        metadata = {}

    # Add extraction
    if "nlp_extractions" not in metadata:
        metadata["nlp_extractions"] = []

    metadata["nlp_extractions"].append({
        "evidence_type": evidence_type,
        "value": value,
        "unit": unit,
        "confidence": confidence,
        "pmid": pmid,
    })

    # Determine new evidence tier
    # If high-confidence extraction (>=0.7), upgrade to MEASURED
    new_tier = current_tier
    if confidence >= 0.7 and evidence_type in ["ic50", "response_rate", "hazard_ratio", "mutation_frequency"]:
        new_tier = "MEASURED"

    # Update database
    cursor.execute("""
        UPDATE morphisms
        SET metadata = ?,
            evidence_tier = ?,
            quantitative_value = ?,
            value_unit = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (
        json.dumps(metadata),
        new_tier,
        value,
        evidence_type,
        morph_id
    ))

    conn.commit()
    conn.close()


def main():
    print("="*70)
    print("PHASE 5: NLP EXTRACTION FROM ALL PMIDs")
    print("="*70)

    # Step 1: Get all PMIDs
    pmid_edges = get_all_pmids()
    all_pmids = list(pmid_edges.keys())

    print(f"\nExtracting quantitative data from {len(all_pmids)} PMIDs...")
    print("This will take ~5-10 minutes (rate-limited to 3 requests/second)")

    # Step 2: Extract from all PMIDs
    results = extract_from_pmid_list(all_pmids, "data/pmid_extractions.json")

    # Step 3: Update database with extractions
    print("\nUpdating database with extractions...")

    update_count = 0
    upgrade_count = 0  # Count edges upgraded to MEASURED

    for pmid, extractions in results.items():
        edges = pmid_edges.get(pmid, [])

        for source, target, relation in edges:
            # For each extraction type
            for ev_type, ev_list in extractions.items():
                for extraction in ev_list:
                    # Get current tier before update
                    conn = sqlite3.connect(DB_PATH)
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT evidence_tier FROM morphisms WHERE source_name=? AND target_name=? AND name=?",
                        (source, target, relation)
                    )
                    result = cursor.fetchone()
                    old_tier = result[0] if result else None
                    conn.close()

                    # Update morphism
                    update_morphism_with_extraction(
                        source, target, relation,
                        ev_type,
                        extraction["value"],
                        extraction["unit"],
                        extraction["confidence"],
                        pmid
                    )

                    update_count += 1

                    # Check if tier was upgraded
                    if old_tier != "MEASURED" and extraction["confidence"] >= 0.7:
                        upgrade_count += 1

    print(f"\n{'='*70}")
    print(f"EXTRACTION COMPLETE")
    print(f"{'='*70}")
    print(f"  Total extractions: {update_count}")
    print(f"  Edges upgraded to MEASURED: {upgrade_count}")
    print(f"  PMIDs with quantitative data: {len(results)}/{len(all_pmids)} ({100*len(results)/len(all_pmids):.1f}%)")

    # Generate validation report
    print("\nGenerating validation report...")

    with open("data/pmid_extraction_report.txt", "w", encoding='utf-8') as f:
        f.write("PMID EXTRACTION VALIDATION REPORT\n")
        f.write("="*70 + "\n\n")

        f.write(f"Total PMIDs processed: {len(all_pmids)}\n")
        f.write(f"PMIDs with quantitative data: {len(results)}\n")
        f.write(f"Extraction success rate: {100*len(results)/len(all_pmids):.1f}%\n\n")

        f.write("EXTRACTIONS BY TYPE:\n")
        f.write("-"*70 + "\n")

        type_counts = {}
        for pmid_data in results.values():
            for ev_type in pmid_data.keys():
                type_counts[ev_type] = type_counts.get(ev_type, 0) + len(pmid_data[ev_type])

        for ev_type, count in sorted(type_counts.items()):
            f.write(f"  {ev_type:20s}: {count:4d}\n")

        f.write("\n" + "="*70 + "\n")
        f.write("SAMPLE EXTRACTIONS (first 10 PMIDs with data):\n")
        f.write("="*70 + "\n\n")

        for i, (pmid, extractions) in enumerate(list(results.items())[:10]):
            f.write(f"PMID {pmid}:\n")
            for ev_type, ev_list in extractions.items():
                for ev in ev_list:
                    f.write(f"  {ev_type}: {ev['value']} {ev['unit']} (confidence: {ev['confidence']:.2f})\n")
                    f.write(f"    Context: {ev['context'][:100]}...\n")
            f.write("\n")

    print(f"  Validation report saved to: data/pmid_extraction_report.txt")

    print("\n[OK] Phase 5 complete! Quantitative PMID data extracted and integrated.")


if __name__ == "__main__":
    main()
