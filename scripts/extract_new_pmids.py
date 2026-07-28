#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""
Extract quantitative data from the 1,054 new PMIDs found via PubMed search.

Same NLP extraction as the original 609 PMIDs:
- IC50, Ki, Kd values
- Response rates (clinical trials)
- Hazard ratios (survival)
- Mutation frequencies
"""

import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from nlp.pmid_extractor import extract_from_pmid_list


def main():
    print("="*70)
    print("NLP EXTRACTION - NEW 1,054 PMIDs")
    print("="*70)
    print()

    # Load the new PMIDs from search results
    with open("data/pubmed_quantitative_search.json", "r", encoding="utf-8") as f:
        search_results = json.load(f)

    new_pmids = search_results["pmids"]
    print(f"Loaded {len(new_pmids)} PMIDs from targeted search")
    print()

    # Run extraction
    print("Running NLP extraction...")
    print("This will take ~10-15 minutes (rate-limited to 3 requests/second)")
    print()

    results = extract_from_pmid_list(
        new_pmids,
        output_file="data/new_pmid_extractions.json"
    )

    print()
    print("="*70)
    print("EXTRACTION COMPLETE")
    print("="*70)
    print()
    print("Results saved to: data/new_pmid_extractions.json")
    print()
    print("Next steps:")
    print("  1. Review: data/new_pmid_extractions.json")
    print("  2. Validate extractions")
    print("  3. Merge with existing extractions")
    print("  4. Update database")


if __name__ == "__main__":
    main()
