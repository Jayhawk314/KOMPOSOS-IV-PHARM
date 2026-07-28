#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""
Query OpenTargets and PubMed for ALL protein-disease pairs.
Goal: Get 7000+ edges with PMID provenance.
"""

import json
import sqlite3
import requests
import time
from pathlib import Path
from typing import Dict, Set, List, Tuple
from collections import defaultdict

OPENTARGETS_API = "https://api.platform.opentargets.org/api/v4/graphql"
PUBMED_API = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

DISEASE_MAP = {
    'AML': ['acute myeloid leukemia', 'acute myeloid leukaemia'],
    'Breast_Cancer': ['breast cancer', 'breast carcinoma', 'breast neoplasm'],
    'CLL': ['chronic lymphocytic leukemia', 'chronic lymphocytic leukaemia'],
    'CML': ['chronic myeloid leukemia', 'chronic myelogenous leukemia'],
    'Colorectal_Cancer': ['colorectal cancer', 'colon cancer', 'rectal cancer'],
    'Ewing_Sarcoma': ['ewing sarcoma', 'ewing\'s sarcoma'],
    'GIST': ['gastrointestinal stromal tumor', 'gist'],
    'Glioblastoma': ['glioblastoma', 'gbm'],
    'HCC': ['hepatocellular carcinoma', 'liver cancer', 'hcc'],
    'Li_Fraumeni_Syndrome': ['li-fraumeni syndrome'],
    'Melanoma': ['melanoma', 'skin cancer'],
    'Multiple_Myeloma': ['multiple myeloma', 'plasma cell myeloma'],
    'Myelofibrosis': ['myelofibrosis', 'primary myelofibrosis'],
    'NSCLC': ['non-small cell lung cancer', 'nsclc', 'lung cancer'],
    'Ovarian_Cancer': ['ovarian cancer', 'ovarian carcinoma'],
    'Pancreatic_Cancer': ['pancreatic cancer', 'pancreatic carcinoma'],
    'Prostate_Cancer': ['prostate cancer', 'prostate carcinoma'],
    'RCC': ['renal cell carcinoma', 'kidney cancer', 'rcc'],
    'Soft_Tissue_Sarcoma': ['soft tissue sarcoma', 'sarcoma'],
    'Type2_Diabetes': ['type 2 diabetes', 'diabetes mellitus type 2'],
}


def query_pubmed(protein: str, disease_terms: List[str]) -> List[str]:
    """Search PubMed for protein-disease associations, return PMIDs"""
    pmids = []

    for term in disease_terms:
        query = f"{protein}[Title/Abstract] AND {term}[Title/Abstract]"
        url = f"{PUBMED_API}/esearch.fcgi"
        params = {
            'db': 'pubmed',
            'term': query,
            'retmax': 5,
            'retmode': 'json'
        }

        try:
            resp = requests.get(url, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            ids = data.get('esearchresult', {}).get('idlist', [])
            pmids.extend(ids)
            time.sleep(0.4)  # Rate limit

            if ids:
                break  # Found PMIDs, stop searching other terms
        except Exception as e:
            print(f"  PubMed error for {protein}/{term}: {e}")
            continue

    return list(set(pmids))[:3]  # Return up to 3 unique PMIDs


def query_opentargets(protein: str, disease: str) -> Tuple[float, str]:
    """
    Query OpenTargets for protein-disease association.
    Returns: (score, evidence_type)
    """
    # Simplified - would need gene symbol to Ensembl mapping
    # For now, return placeholder
    return 0.0, ""


def load_existing_edges(manifest_path: str) -> Set[Tuple[str, str]]:
    """Get existing protein->disease edges from manifest"""
    with open(manifest_path) as f:
        manifest = json.load(f)

    edges = set()
    for m in manifest['morphisms']:
        if m['edge_type'] in ['associated_with', 'driver_of']:
            edges.add((m['source'], m['target']))

    return edges


def main():
    print("=" * 80)
    print("QUERYING EXTERNAL APIS FOR ALL PROTEIN-DISEASE PAIRS")
    print("=" * 80)

    # Load proteins and diseases from tier1.db
    conn = sqlite3.connect('data/drugs/tier1.db')
    c = conn.cursor()

    c.execute("SELECT name FROM objects WHERE type_name='Disease'")
    diseases = [r[0] for r in c.fetchall()]

    c.execute("SELECT name FROM objects WHERE type_name NOT IN ('Drug','Disease','ExternalCompound')")
    proteins = [r[0] for r in c.fetchall()]

    conn.close()

    print(f"\nProteins: {len(proteins)}")
    print(f"Diseases: {len(diseases)}")
    print(f"Total pairs: {len(proteins) * len(diseases)}")

    # Load existing edges
    existing = load_existing_edges('data/drugs/tier1_manifest.json')
    print(f"Existing edges: {len(existing)}")
    print(f"Missing pairs: {len(proteins) * len(diseases) - len(existing)}")

    # Query PubMed for all missing pairs
    print("\nQuerying PubMed for missing pairs...")
    print("(This will take ~60 minutes for 7000+ queries)")

    new_edges = []
    count = 0
    errors = 0

    for i, protein in enumerate(proteins):
        if i % 50 == 0:
            print(f"\nProgress: {i}/{len(proteins)} proteins ({len(new_edges)} edges found)")

        for disease in diseases:
            if (protein, disease) in existing:
                continue

            count += 1
            disease_terms = DISEASE_MAP.get(disease, [disease.lower().replace('_', ' ')])

            try:
                pmids = query_pubmed(protein, disease_terms)

                if pmids:
                    # Found literature evidence
                    confidence = 0.60  # Literature evidence
                    provenance = ', '.join(f'PMID:{p}' for p in pmids)

                    edge = {
                        'source': protein,
                        'target': disease,
                        'edge_type': 'associated_with',
                        'confidence': confidence,
                        'provenance': provenance
                    }
                    new_edges.append(edge)

                    if len(new_edges) % 100 == 0:
                        print(f"  Found {len(new_edges)} edges (queried {count} pairs, {errors} errors)")

            except Exception as e:
                errors += 1
                if errors % 100 == 0:
                    print(f"  Errors: {errors}")
                continue

    print(f"\n{'=' * 80}")
    print(f"SUMMARY:")
    print(f"  Queried: {count} protein-disease pairs")
    print(f"  Found: {len(new_edges)} new edges with PMIDs")
    print(f"  Errors: {errors}")
    print(f"  Total edges (existing + new): {len(existing) + len(new_edges)}")
    print(f"{'=' * 80}")

    # Append to manifest
    print("\nAppending to tier1_manifest.json...")
    with open('data/drugs/tier1_manifest.json') as f:
        manifest = json.load(f)

    manifest['morphisms'].extend(new_edges)
    manifest['morphism_count'] = len(manifest['morphisms'])

    with open('data/drugs/tier1_manifest.json', 'w') as f:
        json.dump(manifest, f, indent=2)

    print(f"Updated manifest: {manifest['morphism_count']} total morphisms")
    print("\nNext steps:")
    print("  1. python data/drugs/build_tier1.py --force")
    print("  2. python validation/repurposing_benchmark.py --view full_typed --protocol loocv")


if __name__ == '__main__':
    main()
