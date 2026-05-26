#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""
NLP extraction of quantitative data from PubMed abstracts.

Extracts:
- IC50/Ki/Kd values (binding affinity)
- Response rates (clinical trials)
- Hazard ratios (survival analysis)
- Sample sizes
- P-values
"""

import re
import requests
import time
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class QuantitativeEvidence:
    """Structured quantitative data extracted from a paper."""
    pmid: str
    evidence_type: str  # "ic50", "response_rate", "hazard_ratio", etc.
    value: float
    unit: str
    confidence: float  # 0-1, how confident are we in this extraction?
    context: str  # Surrounding text for validation


class PMIDExtractor:
    """Extract quantitative data from PubMed abstracts."""

    # Regex patterns for different evidence types
    IC50_PATTERN = r'IC50[:\s=]+([0-9.]+)\s*(nM|μM|uM|mM|nm|um|mm)'
    KI_PATTERN = r'Ki[:\s=]+([0-9.]+)\s*(nM|μM|uM|mM)'
    KD_PATTERN = r'Kd[:\s=]+([0-9.]+)\s*(nM|μM|uM|mM)'
    RESPONSE_RATE_PATTERN = r'(?:response rate|ORR)[:\s=]+([0-9.]+)\s*%'
    HAZARD_RATIO_PATTERN = r'(?:HR|hazard ratio)[:\s=]+([0-9.]+)'
    SAMPLE_SIZE_PATTERN = r'(?:n\s*=|N\s*=)\s*([0-9,]+)'
    P_VALUE_PATTERN = r'(?:p|P)\s*[<=<>\s]+\s*([0-9.]+(?:e-?[0-9]+)?)'
    MUTATION_FREQ_PATTERN = r'([0-9.]+)\s*%\s*(?:of|in)\s+(?:patients|tumors|samples)'

    def __init__(self):
        self.cache = {}  # PMID -> abstract cache

    def fetch_abstract(self, pmid: str) -> Optional[str]:
        """
        Fetch abstract text from PubMed.

        Args:
            pmid: PubMed ID (e.g., "12345678")

        Returns:
            Abstract text or None if not found
        """
        if pmid in self.cache:
            return self.cache[pmid]

        try:
            # Use NCBI EUtils API with requests library for better compatibility
            url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
            params = {
                'db': 'pubmed',
                'id': pmid,
                'rettype': 'abstract',
                'retmode': 'text',
                'tool': 'KOMPOSOS-IV-PHARM',
                'email': 'komposos@example.com'
            }

            headers = {
                'User-Agent': 'KOMPOSOS-IV-PHARM/1.0 (https://github.com/Jayhawk314/KOMPOSOS-IV-PHARM)'
            }

            response = requests.get(url, params=params, headers=headers, timeout=15)

            if response.status_code == 200 and len(response.text) > 50:
                abstract = response.text
                self.cache[pmid] = abstract
                return abstract
            else:
                print(f"  [WARN] PMID {pmid}: No abstract or status {response.status_code}")
                return None

        except requests.exceptions.RequestException as e:
            print(f"  [ERROR] Failed to fetch PMID {pmid}: {e}")
            return None

    def extract_ic50(self, text: str, pmid: str) -> List[QuantitativeEvidence]:
        """Extract IC50 values from text."""
        evidence = []

        for match in re.finditer(self.IC50_PATTERN, text, re.IGNORECASE):
            value_str = match.group(1)
            unit = match.group(2).lower()

            # Convert to μM
            value = float(value_str)
            if unit in ['nm', 'nm']:
                value_um = value / 1000.0
            elif unit in ['um', 'μm', 'um']:
                value_um = value
            elif unit in ['mm', 'mm']:
                value_um = value * 1000.0
            else:
                value_um = value

            # Get surrounding context (±50 chars)
            start = max(0, match.start() - 50)
            end = min(len(text), match.end() + 50)
            context = text[start:end]

            # Confidence: higher for common units, lower for unusual values
            confidence = 0.8
            if value_um < 0.001 or value_um > 1000:  # Unusual range
                confidence = 0.5

            evidence.append(QuantitativeEvidence(
                pmid=pmid,
                evidence_type="ic50",
                value=value_um,
                unit="μM",
                confidence=confidence,
                context=context
            ))

        return evidence

    def extract_response_rate(self, text: str, pmid: str) -> List[QuantitativeEvidence]:
        """Extract clinical response rates."""
        evidence = []

        for match in re.finditer(self.RESPONSE_RATE_PATTERN, text, re.IGNORECASE):
            value = float(match.group(1)) / 100.0  # Convert % to 0-1

            start = max(0, match.start() - 50)
            end = min(len(text), match.end() + 50)
            context = text[start:end]

            confidence = 0.9 if 0.0 <= value <= 1.0 else 0.3

            evidence.append(QuantitativeEvidence(
                pmid=pmid,
                evidence_type="response_rate",
                value=value,
                unit="proportion",
                confidence=confidence,
                context=context
            ))

        return evidence

    def extract_hazard_ratio(self, text: str, pmid: str) -> List[QuantitativeEvidence]:
        """Extract hazard ratios from survival analysis."""
        evidence = []

        for match in re.finditer(self.HAZARD_RATIO_PATTERN, text, re.IGNORECASE):
            value = float(match.group(1))

            start = max(0, match.start() - 50)
            end = min(len(text), match.end() + 50)
            context = text[start:end]

            # HR should be positive, usually < 5
            confidence = 0.85 if 0.1 <= value <= 5.0 else 0.4

            evidence.append(QuantitativeEvidence(
                pmid=pmid,
                evidence_type="hazard_ratio",
                value=value,
                unit="HR",
                confidence=confidence,
                context=context
            ))

        return evidence

    def extract_mutation_frequency(self, text: str, pmid: str) -> List[QuantitativeEvidence]:
        """Extract mutation/alteration frequencies."""
        evidence = []

        for match in re.finditer(self.MUTATION_FREQ_PATTERN, text, re.IGNORECASE):
            value = float(match.group(1)) / 100.0  # Convert % to proportion

            start = max(0, match.start() - 80)
            end = min(len(text), match.end() + 80)
            context = text[start:end]

            confidence = 0.7 if 0.0 <= value <= 1.0 else 0.3

            evidence.append(QuantitativeEvidence(
                pmid=pmid,
                evidence_type="mutation_frequency",
                value=value,
                unit="proportion",
                confidence=confidence,
                context=context
            ))

        return evidence

    def extract_all(self, pmid: str) -> Dict[str, List[QuantitativeEvidence]]:
        """
        Extract all types of quantitative evidence from a PMID.

        Returns:
            Dict mapping evidence type to list of extractions
        """
        abstract = self.fetch_abstract(pmid)
        if not abstract:
            return {}

        all_evidence = {
            "ic50": self.extract_ic50(abstract, pmid),
            "response_rate": self.extract_response_rate(abstract, pmid),
            "hazard_ratio": self.extract_hazard_ratio(abstract, pmid),
            "mutation_frequency": self.extract_mutation_frequency(abstract, pmid),
        }

        # Filter out empty lists
        return {k: v for k, v in all_evidence.items() if len(v) > 0}


def extract_from_pmid_list(pmids: List[str], output_file: str = "pmid_extractions.json"):
    """
    Extract quantitative data from a list of PMIDs.

    Args:
        pmids: List of PubMed IDs
        output_file: JSON file to save results
    """
    import json

    extractor = PMIDExtractor()
    results = {}

    print(f"Extracting from {len(pmids)} PMIDs...")

    for i, pmid in enumerate(pmids):
        if i % 10 == 0:
            print(f"  Progress: {i}/{len(pmids)}")

        evidence = extractor.extract_all(pmid)

        if evidence:
            # Convert to serializable format
            results[pmid] = {}
            for ev_type, ev_list in evidence.items():
                results[pmid][ev_type] = [
                    {
                        "value": e.value,
                        "unit": e.unit,
                        "confidence": e.confidence,
                        "context": e.context
                    }
                    for e in ev_list
                ]

        # Rate limiting
        time.sleep(0.4)  # NCBI allows 3 requests/second

    # Save results
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\nExtraction complete! Saved to {output_file}")

    # Summary stats
    total_extractions = sum(len(ev) for pmid_data in results.values() for ev in pmid_data.values())
    pmids_with_data = len(results)

    print(f"  PMIDs with quantitative data: {pmids_with_data}/{len(pmids)}")
    print(f"  Total extractions: {total_extractions}")

    # Breakdown by type
    type_counts = {}
    for pmid_data in results.values():
        for ev_type in pmid_data.keys():
            type_counts[ev_type] = type_counts.get(ev_type, 0) + len(pmid_data[ev_type])

    print("\n  By evidence type:")
    for ev_type, count in sorted(type_counts.items()):
        print(f"    {ev_type}: {count}")

    return results


if __name__ == "__main__":
    # Test with a few PMIDs
    test_pmids = [
        "17215533",  # Sorafenib RCC trial (should have response rate, survival)
        "12068308",  # Imatinib CML trial (should have response rate)
        # Add more test PMIDs
    ]

    extract_from_pmid_list(test_pmids, "test_extractions.json")
