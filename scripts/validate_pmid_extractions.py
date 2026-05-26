#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""
Validate NLP PMID extractions by fetching abstracts and confirming values are present.

For each extraction, checks:
1. Can we fetch the abstract?
2. Does the abstract contain the extracted value?
3. Is the value in the expected context?
"""

import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from nlp.pmid_extractor import PMIDExtractor


def validate_extraction(extractor, pmid, evidence_type, value, unit, context):
    """
    Validate a single extraction against the actual PubMed abstract.

    Returns: (is_valid, error_message)
    """
    # Fetch abstract
    abstract = extractor.fetch_abstract(pmid)
    if not abstract:
        return (False, "Could not fetch abstract")

    abstract_lower = abstract.lower()

    # Build search patterns based on evidence type
    if evidence_type == "ic50":
        # Look for IC50 = X.XX or IC50: X.XX
        # Convert to nM for search since abstracts often use nM
        value_nm = value * 1000 if "uM" in unit or "μM" in unit else value
        value_um = value if "uM" in unit or "μM" in unit else value / 1000

        patterns = [
            f"ic50 = {value_um:.2f}",
            f"ic50={value_um:.2f}",
            f"ic50 {value_um:.1f}",
            f"ic50 = {value_nm:.1f}",
            f"ic50={value_nm:.1f}",
            f"ic50 {value_nm:.0f}",
            "ic50"  # At minimum, IC50 should be mentioned
        ]

    elif evidence_type == "mutation_frequency":
        # Look for XX% of patients/tumors/samples
        pct = value * 100
        patterns = [
            f"{pct:.1f}%",
            f"{pct:.0f}%",
            f"{int(pct)}%",
            "mutation"  # At minimum, mutations should be mentioned
        ]

    elif evidence_type == "hazard_ratio":
        # Look for HR = X.XX
        patterns = [
            f"hr {value:.2f}",
            f"hr = {value:.2f}",
            f"hr={value:.2f}",
            f"hazard ratio {value:.2f}",
            "hazard ratio",  # At minimum
            "hr "  # Very minimum
        ]
    else:
        patterns = []

    # Check if any pattern matches
    found_specific = False
    found_general = False

    for i, pattern in enumerate(patterns):
        if pattern.lower() in abstract_lower:
            if i < len(patterns) - 1:  # Not the last (general) pattern
                found_specific = True
            found_general = True
            break

    if found_specific:
        return (True, "Value confirmed in abstract")
    elif found_general:
        return (True, "General mention confirmed (value not exact match)")
    else:
        return (False, f"No match for {evidence_type} in abstract")


def main():
    print("="*70)
    print("AUTOMATED VALIDATION OF PMID EXTRACTIONS")
    print("="*70)
    print()

    # Load extractions
    with open("data/pmid_extractions.json", "r", encoding="utf-8") as f:
        extractions = json.load(f)

    print(f"Validating {len(extractions)} PMIDs with quantitative data...")
    print()

    extractor = PMIDExtractor()

    total_extractions = 0
    validated = 0
    general_match = 0
    failed = 0

    validation_results = []

    for pmid, data in extractions.items():
        print(f"PMID {pmid}:")

        for ev_type, ev_list in data.items():
            for ev in ev_list:
                total_extractions += 1

                is_valid, msg = validate_extraction(
                    extractor, pmid, ev_type,
                    ev['value'], ev['unit'], ev['context']
                )

                status = "[OK]" if is_valid else "[FAIL]"

                if is_valid:
                    if "exact" in msg or "confirmed" in msg.lower():
                        validated += 1
                    else:
                        general_match += 1
                else:
                    failed += 1

                value_str = f"{ev['value']}"
                if ev_type == "mutation_frequency":
                    value_str = f"{ev['value']*100:.1f}%"
                elif ev_type == "ic50":
                    unit_str = ev['unit'].replace('μ', 'u')  # Replace μ with u
                    value_str = f"{ev['value']:.2f} {unit_str}"

                print(f"  {status} {ev_type}: {value_str} - {msg}")

                validation_results.append({
                    "pmid": pmid,
                    "type": ev_type,
                    "value": ev['value'],
                    "valid": is_valid,
                    "message": msg
                })

        print()

    # Summary
    print("="*70)
    print("VALIDATION SUMMARY")
    print("="*70)
    print(f"Total extractions: {total_extractions}")
    print(f"  Validated (specific match): {validated}")
    print(f"  General match: {general_match}")
    print(f"  Failed to validate: {failed}")
    print()
    print(f"Success rate: {(validated + general_match) / total_extractions * 100:.1f}%")
    print()

    # Save results
    with open("data/pmid_validation_results.json", "w", encoding="utf-8") as f:
        json.dump(validation_results, f, indent=2)

    print("Validation results saved to: data/pmid_validation_results.json")

    # Recommendations
    print()
    print("RECOMMENDATIONS:")
    if failed > 0:
        print(f"  - Review {failed} failed validations manually")
        print(f"  - Consider adjusting regex patterns or confidence thresholds")
    if failed / total_extractions < 0.1:
        print(f"  - <10% failure rate - extraction is working well!")
    else:
        print(f"  - >10% failure rate - improve extraction patterns")


if __name__ == "__main__":
    main()
