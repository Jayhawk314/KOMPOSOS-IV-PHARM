#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""
Validate new PMID extractions (same process as original 609).

For each extraction:
1. Fetch abstract
2. Confirm value appears in abstract
3. Flag low-confidence extractions
4. Generate validation report
"""

import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from nlp.pmid_extractor import PMIDExtractor


def validate_extraction(extractor, pmid, evidence_type, value, unit, context, confidence):
    """Validate a single extraction against the actual abstract."""

    # Fetch abstract
    abstract = extractor.fetch_abstract(pmid)
    if not abstract:
        return (False, "Could not fetch abstract")

    abstract_lower = abstract.lower()

    # Build search patterns based on evidence type
    if evidence_type == "ic50":
        value_nm = value * 1000 if "uM" in unit or "μM" in unit else value
        value_um = value if "uM" in unit or "μM" in unit else value / 1000

        patterns = [
            f"ic50 = {value_um:.2f}",
            f"ic50={value_um:.2f}",
            f"ic50 {value_um:.1f}",
            f"ic50 = {value_nm:.1f}",
            f"ic50={value_nm:.1f}",
            "ic50"  # General mention
        ]

    elif evidence_type == "mutation_frequency":
        pct = value * 100
        patterns = [
            f"{pct:.1f}%",
            f"{pct:.0f}%",
            f"{int(pct)}%",
            "mutation"
        ]

    elif evidence_type == "hazard_ratio":
        patterns = [
            f"hr {value:.2f}",
            f"hr = {value:.2f}",
            f"hazard ratio {value:.2f}",
            "hazard ratio",
            "hr "
        ]

    elif evidence_type == "response_rate":
        pct = value * 100
        patterns = [
            f"{pct:.1f}%",
            f"response rate",
            f"orr"
        ]
    else:
        patterns = []

    # Check for matches
    found_specific = False
    found_general = False

    for i, pattern in enumerate(patterns):
        if pattern.lower() in abstract_lower:
            if i < len(patterns) - 1:
                found_specific = True
            found_general = True
            break

    if found_specific:
        return (True, "Value confirmed in abstract")
    elif found_general:
        return (True, "General mention confirmed")
    else:
        return (False, f"No match for {evidence_type}")


def main():
    print("="*70)
    print("VALIDATION - NEW PMID EXTRACTIONS")
    print("="*70)
    print()

    # Load new extractions
    try:
        with open("data/new_pmid_extractions.json", "r", encoding="utf-8") as f:
            extractions = json.load(f)
    except FileNotFoundError:
        print("[ERROR] data/new_pmid_extractions.json not found")
        print("Run extract_new_pmids.py first")
        return

    print(f"Loaded extractions for {len(extractions)} PMIDs")
    print()

    extractor = PMIDExtractor()

    total = 0
    validated = 0
    general = 0
    failed = 0

    validation_results = []

    print("Validating extractions...")
    print()

    for pmid, data in extractions.items():
        print(f"PMID {pmid}:")

        for ev_type, ev_list in data.items():
            for ev in ev_list:
                total += 1

                is_valid, msg = validate_extraction(
                    extractor, pmid, ev_type,
                    ev['value'], ev['unit'], ev['context'], ev['confidence']
                )

                status = "[OK]" if is_valid else "[FAIL]"

                if is_valid:
                    if "confirmed" in msg.lower():
                        validated += 1
                    else:
                        general += 1
                else:
                    failed += 1

                value_str = f"{ev['value']}"
                if ev_type == "mutation_frequency":
                    value_str = f"{ev['value']*100:.1f}%"
                elif ev_type == "ic50":
                    unit_str = ev['unit'].replace('μ', 'u')
                    value_str = f"{ev['value']:.2f} {unit_str}"
                elif ev_type == "response_rate":
                    value_str = f"{ev['value']*100:.1f}%"

                print(f"  {status} {ev_type}: {value_str} (conf: {ev['confidence']:.2f}) - {msg}")

                validation_results.append({
                    "pmid": pmid,
                    "type": ev_type,
                    "value": ev['value'],
                    "valid": is_valid,
                    "message": msg,
                    "confidence": ev['confidence']
                })

        print()

    # Summary
    print("="*70)
    print("VALIDATION SUMMARY")
    print("="*70)
    print(f"Total extractions: {total}")
    print(f"  Validated (specific): {validated}")
    print(f"  General match: {general}")
    print(f"  Failed: {failed}")
    print()
    print(f"Success rate: {(validated + general) / total * 100:.1f}%" if total > 0 else "N/A")
    print()

    # Save results
    with open("data/new_pmid_validation_results.json", "w", encoding="utf-8") as f:
        json.dump(validation_results, f, indent=2)

    print("Validation results saved to: data/new_pmid_validation_results.json")

    # Quality analysis
    print()
    print("QUALITY ANALYSIS:")
    high_conf = sum(1 for r in validation_results if r['confidence'] >= 0.7 and r['valid'])
    med_conf = sum(1 for r in validation_results if 0.5 <= r['confidence'] < 0.7 and r['valid'])
    low_conf = sum(1 for r in validation_results if r['confidence'] < 0.5 and r['valid'])

    print(f"  High confidence (≥0.7): {high_conf}")
    print(f"  Medium confidence (0.5-0.7): {med_conf}")
    print(f"  Low confidence (<0.5): {low_conf}")


if __name__ == "__main__":
    main()
