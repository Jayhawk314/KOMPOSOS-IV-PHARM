#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""
Phase 5: Validate and integrate NLP-extracted quantitative data.

Validates extraction quality, integrates into database,
and generates comprehensive audit report.

Steps:
1. Load extractions from pmid_extractions.json
2. Validate each extraction (range checks, confidence thresholds)
3. Map extractions to database edges
4. Upgrade evidence tiers for high-quality extractions
5. Update quantitative_value and metadata fields
6. Generate validation report with quality metrics
"""

import sqlite3
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import sys
from collections import defaultdict

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

DB_PATH = "data/drugs/tier1.db"
EXTRACTIONS_FILE = "data/pmid_extractions.json"
REPORT_FILE = "data/pmid_extraction_report.txt"


# Validation ranges for each evidence type
VALIDATION_RANGES = {
    "ic50": (0.001, 1000.0),  # μM
    "response_rate": (0.0, 1.0),  # proportion
    "hazard_ratio": (0.1, 5.0),
    "mutation_frequency": (0.0, 1.0),  # proportion
}

# Minimum confidence for MEASURED tier upgrade
CONFIDENCE_THRESHOLD = 0.7


def load_extractions(filepath: str) -> Dict:
    """Load NLP extractions from JSON file."""
    if not Path(filepath).exists():
        print(f"[ERROR] Extractions file not found: {filepath}")
        return {}

    with open(filepath, 'r') as f:
        extractions = json.load(f)

    print(f"Loaded extractions for {len(extractions)} PMIDs")
    return extractions


def validate_extraction(
    evidence_type: str,
    value: float,
    confidence: float
) -> Tuple[bool, Optional[str]]:
    """
    Validate an extraction against range and confidence thresholds.

    Args:
        evidence_type: Type of evidence (ic50, response_rate, etc.)
        value: Extracted value
        confidence: Extraction confidence

    Returns:
        (is_valid, error_message)
    """
    # Check confidence
    if confidence < 0.3:
        return (False, f"Confidence too low: {confidence:.2f}")

    # Check range
    if evidence_type in VALIDATION_RANGES:
        min_val, max_val = VALIDATION_RANGES[evidence_type]

        if not (min_val <= value <= max_val):
            return (False, f"Value {value} outside valid range [{min_val}, {max_val}]")

    return (True, None)


def find_edges_for_pmid(conn: sqlite3.Connection, pmid: str) -> List[Tuple[int, str, str, str]]:
    """
    Find all edges (morphisms) that cite this PMID.

    Args:
        conn: Database connection
        pmid: PubMed ID

    Returns:
        List of (morphism_id, source_name, target_name, provenance)
    """
    cursor = conn.cursor()

    cursor.execute("""
        SELECT m.id, src.name, tgt.name, m.provenance
        FROM morphisms m
        JOIN objects src ON m.source_id = src.id
        JOIN objects tgt ON m.target_id = tgt.id
        WHERE m.provenance LIKE ?
    """, (f"%{pmid}%",))

    return cursor.fetchall()


def update_morphism_with_extraction(
    conn: sqlite3.Connection,
    morphism_id: int,
    evidence_type: str,
    value: float,
    unit: str,
    confidence: float,
    context: str
):
    """
    Update morphism with NLP-extracted quantitative data.

    Args:
        conn: Database connection
        morphism_id: Morphism ID to update
        evidence_type: Type of evidence
        value: Extracted value
        unit: Value unit
        confidence: Extraction confidence
        context: Context text
    """
    cursor = conn.cursor()

    # Load existing metadata
    cursor.execute("SELECT metadata, evidence_tier FROM morphisms WHERE id = ?", (morphism_id,))
    row = cursor.fetchone()

    if not row:
        return

    metadata_str, current_tier = row
    metadata = json.loads(metadata_str) if metadata_str else {}

    # Add NLP extraction to metadata
    if "nlp_extractions" not in metadata:
        metadata["nlp_extractions"] = []

    metadata["nlp_extractions"].append({
        "evidence_type": evidence_type,
        "value": value,
        "unit": unit,
        "confidence": confidence,
        "context": context
    })

    # Upgrade to MEASURED tier if high confidence
    new_tier = current_tier
    if confidence >= CONFIDENCE_THRESHOLD:
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


def generate_validation_report(
    extractions: Dict,
    validation_results: Dict,
    integration_results: Dict
) -> str:
    """
    Generate comprehensive validation report.

    Args:
        extractions: All extractions
        validation_results: Validation statistics
        integration_results: Integration statistics

    Returns:
        Report text
    """
    report_lines = []

    report_lines.append("="*70)
    report_lines.append("NLP PMID EXTRACTION VALIDATION REPORT")
    report_lines.append("="*70)
    report_lines.append("")

    # Overall statistics
    report_lines.append("EXTRACTION STATISTICS:")
    report_lines.append(f"  Total PMIDs processed: {validation_results['total_pmids']}")
    report_lines.append(f"  PMIDs with extractions: {validation_results['pmids_with_data']}")
    report_lines.append(f"  Total extractions: {validation_results['total_extractions']}")
    report_lines.append(f"  Valid extractions: {validation_results['valid_extractions']}")
    report_lines.append(f"  Invalid extractions: {validation_results['invalid_extractions']}")
    report_lines.append("")

    # By evidence type
    report_lines.append("EXTRACTIONS BY TYPE:")
    for ev_type, count in sorted(validation_results['by_type'].items()):
        report_lines.append(f"  {ev_type}: {count}")
    report_lines.append("")

    # Quality distribution
    report_lines.append("CONFIDENCE DISTRIBUTION:")
    report_lines.append(f"  High confidence (≥0.7): {validation_results['high_confidence']}")
    report_lines.append(f"  Medium confidence (0.5-0.7): {validation_results['medium_confidence']}")
    report_lines.append(f"  Low confidence (<0.5): {validation_results['low_confidence']}")
    report_lines.append("")

    # Integration results
    report_lines.append("DATABASE INTEGRATION:")
    report_lines.append(f"  Edges updated: {integration_results['edges_updated']}")
    report_lines.append(f"  Edges upgraded to MEASURED: {integration_results['tier_upgrades']}")
    report_lines.append(f"  Edges with quantitative values: {integration_results['quantified_edges']}")
    report_lines.append("")

    # Top extractions by type
    report_lines.append("SAMPLE EXTRACTIONS (Top 10 by confidence):")
    for ev_type in ["ic50", "response_rate", "hazard_ratio", "mutation_frequency"]:
        if ev_type not in validation_results['samples']:
            continue

        report_lines.append(f"\n  {ev_type.upper()}:")
        for sample in validation_results['samples'][ev_type][:10]:
            report_lines.append(f"    PMID {sample['pmid']}: {sample['value']} {sample['unit']} "
                              f"(conf: {sample['confidence']:.2f})")
            report_lines.append(f"      Context: ...{sample['context'][:80]}...")

    report_lines.append("")
    report_lines.append("="*70)
    report_lines.append("END OF REPORT")
    report_lines.append("="*70)

    return "\n".join(report_lines)


def main():
    print("="*70)
    print("PHASE 5: VALIDATE AND INTEGRATE NLP EXTRACTIONS")
    print("="*70)

    # Load extractions
    print("\n[1] Loading NLP extractions...")
    extractions = load_extractions(EXTRACTIONS_FILE)

    if not extractions:
        print("[ERROR] No extractions to process")
        return

    # Validation statistics
    validation_stats = {
        "total_pmids": len(extractions),
        "pmids_with_data": 0,
        "total_extractions": 0,
        "valid_extractions": 0,
        "invalid_extractions": 0,
        "by_type": defaultdict(int),
        "high_confidence": 0,
        "medium_confidence": 0,
        "low_confidence": 0,
        "samples": defaultdict(list)
    }

    # Integration statistics
    integration_stats = {
        "edges_updated": 0,
        "tier_upgrades": 0,
        "quantified_edges": 0
    }

    # Connect to database
    conn = sqlite3.connect(DB_PATH)

    # Process each PMID
    print("\n[2] Validating extractions...")

    for pmid, pmid_data in extractions.items():
        if pmid_data:
            validation_stats["pmids_with_data"] += 1

        for evidence_type, extractions_list in pmid_data.items():
            for extraction in extractions_list:
                validation_stats["total_extractions"] += 1
                validation_stats["by_type"][evidence_type] += 1

                # Validate
                value = extraction["value"]
                confidence = extraction["confidence"]
                unit = extraction["unit"]
                context = extraction["context"]

                is_valid, error_msg = validate_extraction(evidence_type, value, confidence)

                if is_valid:
                    validation_stats["valid_extractions"] += 1

                    # Confidence distribution
                    if confidence >= 0.7:
                        validation_stats["high_confidence"] += 1
                    elif confidence >= 0.5:
                        validation_stats["medium_confidence"] += 1
                    else:
                        validation_stats["low_confidence"] += 1

                    # Collect samples
                    validation_stats["samples"][evidence_type].append({
                        "pmid": pmid,
                        "value": value,
                        "unit": unit,
                        "confidence": confidence,
                        "context": context
                    })

                else:
                    validation_stats["invalid_extractions"] += 1
                    print(f"  [INVALID] PMID {pmid}, {evidence_type}: {error_msg}")

    # Sort samples by confidence
    for ev_type in validation_stats["samples"]:
        validation_stats["samples"][ev_type].sort(key=lambda x: x["confidence"], reverse=True)

    # Integration
    print("\n[3] Integrating validated extractions into database...")

    for pmid, pmid_data in extractions.items():
        # Find edges for this PMID
        edges = find_edges_for_pmid(conn, pmid)

        if not edges:
            # PMID not in database edges
            continue

        for morphism_id, source, target, provenance in edges:
            # Check if we have relevant extractions for this edge
            for evidence_type, extractions_list in pmid_data.items():
                for extraction in extractions_list:
                    value = extraction["value"]
                    confidence = extraction["confidence"]
                    unit = extraction["unit"]
                    context = extraction["context"]

                    # Validate
                    is_valid, _ = validate_extraction(evidence_type, value, confidence)

                    if is_valid:
                        # Update morphism
                        update_morphism_with_extraction(
                            conn, morphism_id, evidence_type,
                            value, unit, confidence, context
                        )

                        integration_stats["edges_updated"] += 1

                        if confidence >= CONFIDENCE_THRESHOLD:
                            integration_stats["tier_upgrades"] += 1

    # Count quantified edges
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM morphisms WHERE quantitative_value IS NOT NULL")
    integration_stats["quantified_edges"] = cursor.fetchone()[0]

    # Commit changes
    conn.commit()
    conn.close()

    # Generate report
    print("\n[4] Generating validation report...")
    report = generate_validation_report(extractions, validation_stats, integration_stats)

    # Save report
    with open(REPORT_FILE, 'w') as f:
        f.write(report)

    print(f"\nReport saved to: {REPORT_FILE}")

    # Print summary
    print("\n" + "="*70)
    print("VALIDATION AND INTEGRATION COMPLETE")
    print("="*70)
    print(f"Valid extractions: {validation_stats['valid_extractions']}/{validation_stats['total_extractions']}")
    print(f"Edges updated: {integration_stats['edges_updated']}")
    print(f"Tier upgrades: {integration_stats['tier_upgrades']}")
    print(f"Quantified edges: {integration_stats['quantified_edges']}")


if __name__ == "__main__":
    main()
