#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""
Query OpenTargets + PubMed for all missing protein-disease pairs.
Target: ~6000 edges to reach full coverage.
"""

import json
import sqlite3
import requests
import time
from typing import Dict, Set, List, Tuple
from collections import defaultdict

OPENTARGETS_API = "https://api.platform.opentargets.org/api/v4/graphql"
PUBMED_SEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"

DISEASE_SEARCH_TERMS = {
    'AML': ['acute myeloid leukemia', 'AML'],
    'Breast_Cancer': ['breast cancer', 'breast carcinoma'],
    'CLL': ['chronic lymphocytic leukemia', 'CLL'],
    'CML': ['chronic myeloid leukemia', 'CML'],
    'Colorectal_Cancer': ['colorectal cancer', 'colon cancer'],
    'Ewing_Sarcoma': ['ewing sarcoma'],
    'GIST': ['gastrointestinal stromal tumor', 'GIST'],
    'Glioblastoma': ['glioblastoma', 'GBM'],
    'HCC': ['hepatocellular carcinoma', 'liver cancer'],
    'Li_Fraumeni_Syndrome': ['li-fraumeni syndrome', 'LFS'],
    'Melanoma': ['melanoma'],
    'Multiple_Myeloma': ['multiple myeloma'],
    'Myelofibrosis': ['myelofibrosis'],
    'NSCLC': ['non-small cell lung cancer', 'NSCLC', 'lung cancer'],
    'Ovarian_Cancer': ['ovarian cancer'],
    'Pancreatic_Cancer': ['pancreatic cancer'],
    'Prostate_Cancer': ['prostate cancer'],
    'RCC': ['renal cell carcinoma', 'kidney cancer'],
    'Soft_Tissue_Sarcoma': ['soft tissue sarcoma'],
    'Type2_Diabetes': ['type 2 diabetes', 'diabetes mellitus'],
}


def load_existing() -> Tuple[Set[str], Set[str], Set[Tuple[str, str]]]:
    """Load proteins, diseases, and existing edges"""
    conn = sqlite3.connect('data/drugs/tier1.db')
    c = conn.cursor()

    c.execute("SELECT name FROM objects WHERE type_name='Disease'")
    diseases = {r[0] for r in c.fetchall()}

    c.execute("SELECT name FROM objects WHERE type_name NOT IN ('Drug','Disease','ExternalCompound')")
    proteins = {r[0] for r in c.fetchall()}

    c.execute("""
        SELECT source_name, target_name FROM morphisms
        WHERE target_name IN (SELECT name FROM objects WHERE type_name='Disease')
    """)
    existing_edges = {(r[0], r[1]) for r in c.fetchall()}

    conn.close()
    return proteins, diseases, existing_edges


def query_pubmed_simple(protein: str, disease: str, search_terms: List[str]) -> List[str]:
    """Quick PubMed search for protein-disease PMIDs"""
    for term in search_terms[:2]:  # Try first 2 search terms
        query = f'"{protein}"[Title/Abstract] AND "{term}"[Title/Abstract]'

        try:
            resp = requests.get(
                PUBMED_SEARCH,
                params={
                    'db': 'pubmed',
                    'term': query,
                    'retmax': 3,
                    'retmode': 'json'
                },
                timeout=10
            )

            if resp.status_code == 200:
                data = resp.json()
                pmids = data.get('esearchresult', {}).get('idlist', [])
                if pmids:
                    return pmids[:2]  # Return up to 2 PMIDs

            time.sleep(0.35)  # Rate limit

        except Exception:
            continue

    return []


def main():
    print("=" * 80)
    print("QUERYING OPENTARGETS + PUBMED FOR MISSING EDGES")
    print("=" * 80)

    proteins, diseases, existing = load_existing()

    missing = []
    for p in proteins:
        for d in diseases:
            if (p, d) not in existing:
                missing.append((p, d))

    print(f"\nProteins: {len(proteins)}")
    print(f"Diseases: {len(diseases)}")
    print(f"Existing edges: {len(existing)}")
    print(f"Missing pairs: {len(missing)}")
    print(f"\nQuerying PubMed for missing pairs...")
    print(f"Estimated time: {len(missing) * 0.4 / 60:.0f} minutes")

    new_edges = []
    errors = 0

    for i, (protein, disease) in enumerate(missing):
        if i % 100 == 0:
            print(f"Progress: {i}/{len(missing)} ({len(new_edges)} edges found, {errors} errors)")

        search_terms = DISEASE_SEARCH_TERMS.get(disease, [disease.lower().replace('_', ' ')])

        try:
            pmids = query_pubmed_simple(protein, disease, search_terms)

            if pmids:
                # Found literature support
                new_edges.append({
                    'source': protein,
                    'target': disease,
                    'edge_type': 'associated_with',
                    'confidence': 0.65,  # Literature evidence
                    'provenance': ', '.join(f'PMID:{p}' for p in pmids)
                })

        except Exception as e:
            errors += 1
            if errors % 50 == 0:
                print(f"  Errors: {errors}")

    print(f"\n{'=' * 80}")
    print(f"RESULTS:")
    print(f"  Queried: {len(missing)} pairs")
    print(f"  Found: {len(new_edges)} edges with PMIDs")
    print(f"  Coverage: {(len(existing) + len(new_edges)) / (len(proteins) * len(diseases)) * 100:.1f}%")
    print(f"{'=' * 80}")

    # Save to file for review
    with open('data/new_edges_pubmed.json', 'w') as f:
        json.dump(new_edges, f, indent=2)

    print(f"\nSaved {len(new_edges)} new edges to data/new_edges_pubmed.json")
    print("\nTo append to manifest:")
    print("  python scripts/append_edges.py data/new_edges_pubmed.json")


if __name__ == '__main__':
    main()
