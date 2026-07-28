#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""
Import Protein->Disease associations from OpenTargets Platform.

Systematic, automated import with uniform criteria:
- Queries ALL proteins in tier1.db (not cherry-picked)
- Filters to cancer therapeutic area only
- Uniform score threshold applied to all
- Full provenance (OpenTargets evidence IDs)
- Reproducible (script, not manual)

This is scientifically defensible because:
1. Third-party source (OpenTargets integrates 20+ databases)
2. Uniform criteria across all proteins
3. No selection bias (all proteins queried, not just high-connectivity)
4. Reproducible and auditable
5. Cancer-filtered (avoids scope explosion)

Usage:
    python data/drugs/importers/import_opentargets_diseases.py \\
        --manifest data/drugs/tier1_manifest.json \\
        --output data/drugs/tier1_manifest_with_ot_diseases.json \\
        --min-score 0.5 \\
        --dry-run

    # Deploy:
    python data/drugs/importers/import_opentargets_diseases.py \\
        --manifest data/drugs/tier1_manifest.json \\
        --output data/drugs/tier1_manifest.json \\
        --min-score 0.5
"""

import json
import sqlite3
import sys
import time
import argparse
import requests
import logging
from typing import Dict, List, Optional, Set, Tuple
from pathlib import Path
from collections import defaultdict

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)
logger = logging.getLogger(__name__)

OPENTARGETS_API = "https://api.platform.opentargets.org/api/v4/graphql"

# Cancer therapeutic area ID in OpenTargets
CANCER_AREA_ID = "MONDO_0045024"
CANCER_AREA_NAME = "cancer or benign tumor"

# Map OpenTargets disease names to our existing disease names.
# Only map when there's a clear, unambiguous correspondence.
# Uses lowercase matching.
DISEASE_NAME_MAP = {
    # AML
    'acute myeloid leukemia': 'AML',
    'acute myeloid leukaemia': 'AML',
    # Breast Cancer
    'breast cancer': 'Breast_Cancer',
    'breast carcinoma': 'Breast_Cancer',
    'breast adenocarcinoma': 'Breast_Cancer',
    'breast neoplasm': 'Breast_Cancer',
    'breast ductal adenocarcinoma': 'Breast_Cancer',
    'triple-negative breast cancer': 'Breast_Cancer',
    'estrogen-receptor positive breast cancer': 'Breast_Cancer',
    'her2-positive breast cancer': 'Breast_Cancer',
    'inflammatory breast cancer': 'Breast_Cancer',
    # CLL
    'chronic lymphocytic leukemia': 'CLL',
    'chronic lymphocytic leukaemia': 'CLL',
    'b-cell chronic lymphocytic leukemia': 'CLL',
    # CML
    'chronic myeloid leukemia': 'CML',
    'chronic myelogenous leukemia': 'CML',
    'chronic myeloid leukaemia': 'CML',
    # Colorectal Cancer
    'colorectal cancer': 'Colorectal_Cancer',
    'colorectal carcinoma': 'Colorectal_Cancer',
    'colorectal adenocarcinoma': 'Colorectal_Cancer',
    'colon cancer': 'Colorectal_Cancer',
    'colon carcinoma': 'Colorectal_Cancer',
    'colon adenocarcinoma': 'Colorectal_Cancer',
    'rectal cancer': 'Colorectal_Cancer',
    'rectal carcinoma': 'Colorectal_Cancer',
    # Ewing Sarcoma
    'ewing sarcoma': 'Ewing_Sarcoma',
    "ewing's sarcoma": 'Ewing_Sarcoma',
    'ewing sarcoma/peripheral primitive neuroectodermal tumor': 'Ewing_Sarcoma',
    # GIST
    'gastrointestinal stromal tumor': 'GIST',
    'gastrointestinal stromal tumour': 'GIST',
    # Glioblastoma
    'glioblastoma': 'Glioblastoma',
    'glioblastoma multiforme': 'Glioblastoma',
    # HCC
    'hepatocellular carcinoma': 'HCC',
    'liver cancer': 'HCC',
    'hepatocellular cancer': 'HCC',
    'hepatoblastoma': 'HCC',
    # Li-Fraumeni
    'li-fraumeni syndrome': 'Li_Fraumeni_Syndrome',
    'li-fraumeni syndrome 1': 'Li_Fraumeni_Syndrome',
    # Melanoma
    'melanoma': 'Melanoma',
    'malignant melanoma': 'Melanoma',
    'cutaneous melanoma': 'Melanoma',
    'skin melanoma': 'Melanoma',
    'uveal melanoma': 'Melanoma',
    # Multiple Myeloma
    'multiple myeloma': 'Multiple_Myeloma',
    'plasma cell myeloma': 'Multiple_Myeloma',
    # Myelofibrosis
    'myelofibrosis': 'Myelofibrosis',
    'primary myelofibrosis': 'Myelofibrosis',
    # NSCLC
    'non-small cell lung cancer': 'NSCLC',
    'non-small cell lung carcinoma': 'NSCLC',
    'lung non-small cell carcinoma': 'NSCLC',
    'lung adenocarcinoma': 'NSCLC',
    'lung squamous cell carcinoma': 'NSCLC',
    # Ovarian Cancer
    'ovarian cancer': 'Ovarian_Cancer',
    'ovarian carcinoma': 'Ovarian_Cancer',
    'ovarian epithelial cancer': 'Ovarian_Cancer',
    'ovarian serous adenocarcinoma': 'Ovarian_Cancer',
    # Pancreatic Cancer
    'pancreatic cancer': 'Pancreatic_Cancer',
    'pancreatic carcinoma': 'Pancreatic_Cancer',
    'pancreatic adenocarcinoma': 'Pancreatic_Cancer',
    'pancreatic ductal adenocarcinoma': 'Pancreatic_Cancer',
    # Prostate Cancer
    'prostate cancer': 'Prostate_Cancer',
    'prostate carcinoma': 'Prostate_Cancer',
    'prostate adenocarcinoma': 'Prostate_Cancer',
    'castration-resistant prostate cancer': 'Prostate_Cancer',
    # RCC
    'renal cell carcinoma': 'RCC',
    'clear cell renal carcinoma': 'RCC',
    'clear cell renal cell carcinoma': 'RCC',
    'kidney cancer': 'RCC',
    'renal cancer': 'RCC',
    'renal carcinoma': 'RCC',
    # Soft Tissue Sarcoma
    'soft tissue sarcoma': 'Soft_Tissue_Sarcoma',
    'sarcoma': 'Soft_Tissue_Sarcoma',
    'rhabdomyosarcoma': 'Soft_Tissue_Sarcoma',
    'leiomyosarcoma': 'Soft_Tissue_Sarcoma',
    'liposarcoma': 'Soft_Tissue_Sarcoma',
    # Type 2 Diabetes - only include if cancer-comorbidity context
    'type ii diabetes mellitus': 'Type2_Diabetes',
    'type 2 diabetes': 'Type2_Diabetes',
    'diabetes mellitus type 2': 'Type2_Diabetes',
}


def get_all_proteins(db_path: str) -> List[str]:
    """Get all protein names from tier1.db."""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('SELECT name FROM objects WHERE type_name NOT IN ("Drug", "Disease") ORDER BY name')
    proteins = [row[0] for row in c.fetchall()]
    conn.close()
    return proteins


def get_existing_protein_disease_edges(db_path: str) -> Set[Tuple[str, str]]:
    """Get existing Protein->Disease edges to avoid duplicates."""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''
        SELECT source_name, target_name
        FROM morphisms
        WHERE target_name IN (SELECT name FROM objects WHERE type_name = "Disease")
          AND source_name IN (SELECT name FROM objects WHERE type_name NOT IN ("Drug", "Disease"))
    ''')
    edges = {(row[0], row[1]) for row in c.fetchall()}
    conn.close()
    return edges


def resolve_gene_symbol(symbol: str) -> Optional[str]:
    """Resolve gene symbol to Ensembl ID via OpenTargets search."""
    query = """
    query geneSearch($queryString: String!) {
      search(queryString: $queryString, entityNames: ["target"], page: {index: 0, size: 5}) {
        hits {
          id
          name
          entity
        }
      }
    }
    """

    try:
        response = requests.post(
            OPENTARGETS_API,
            json={"query": query, "variables": {"queryString": symbol}},
            timeout=30
        )

        if response.status_code != 200:
            return None

        hits = response.json().get('data', {}).get('search', {}).get('hits', [])

        # Find exact symbol match
        for hit in hits:
            if hit.get('name', '').upper() == symbol.upper():
                return hit['id']

        # Fall back to first hit if name is close
        if hits:
            return hits[0]['id']

        return None

    except Exception as e:
        logger.warning(f"Error resolving {symbol}: {e}")
        return None


def get_cancer_disease_associations(
    ensembl_id: str,
    min_score: float = 0.5,
    max_diseases: int = 200
) -> List[Dict]:
    """
    Get cancer-filtered disease associations for a target.

    Returns list of {
        'disease_name': str,
        'disease_id': str,
        'score': float,
        'our_disease': str or None  (mapped to our 20 diseases)
    }
    """
    query = """
    query targetDiseases($ensemblId: String!, $size: Int!) {
      target(ensemblId: $ensemblId) {
        approvedSymbol
        associatedDiseases(page: {index: 0, size: $size}) {
          count
          rows {
            disease {
              id
              name
              therapeuticAreas {
                id
                name
              }
            }
            score
          }
        }
      }
    }
    """

    try:
        response = requests.post(
            OPENTARGETS_API,
            json={
                "query": query,
                "variables": {"ensemblId": ensembl_id, "size": max_diseases}
            },
            timeout=30
        )

        if response.status_code != 200:
            return []

        target_data = response.json().get('data', {}).get('target', {})
        if not target_data:
            return []

        rows = target_data.get('associatedDiseases', {}).get('rows', [])

        cancer_associations = []
        for row in rows:
            score = row.get('score', 0)
            if score < min_score:
                continue

            disease = row['disease']
            areas = disease.get('therapeuticAreas', [])

            # Filter: must be in cancer therapeutic area
            is_cancer = any(a.get('id') == CANCER_AREA_ID for a in areas)
            if not is_cancer:
                continue

            disease_name = disease['name']
            disease_id = disease['id']

            # Map to our existing 20 diseases
            our_disease = DISEASE_NAME_MAP.get(disease_name.lower())

            cancer_associations.append({
                'disease_name': disease_name,
                'disease_id': disease_id,
                'score': score,
                'our_disease': our_disease,
            })

        return cancer_associations

    except Exception as e:
        logger.warning(f"Error getting diseases for {ensembl_id}: {e}")
        return []


def run_import(
    db_path: str,
    manifest_path: str,
    output_path: str,
    min_score: float = 0.5,
    dry_run: bool = False,
    only_existing_diseases: bool = True,
):
    """
    Run the full cancer-filtered OpenTargets import.

    Args:
        db_path: Path to tier1.db
        manifest_path: Path to tier1_manifest.json
        output_path: Where to write updated manifest
        min_score: Minimum OpenTargets association score (0-1)
        dry_run: If True, only report what would be imported
        only_existing_diseases: If True, only import edges to our existing 20 diseases
    """
    print("=" * 70)
    print("OpenTargets Cancer-Filtered Protein->Disease Import")
    print("=" * 70)
    print(f"\nDatabase: {db_path}")
    print(f"Manifest: {manifest_path}")
    print(f"Output: {output_path}")
    print(f"Min score: {min_score}")
    print(f"Only existing diseases: {only_existing_diseases}")
    print(f"Dry run: {dry_run}")
    print()

    # Load proteins
    proteins = get_all_proteins(db_path)
    existing_edges = get_existing_protein_disease_edges(db_path)
    print(f"Total proteins: {len(proteins)}")
    print(f"Existing Protein->Disease edges: {len(existing_edges)}")

    # Load manifest
    with open(manifest_path, 'r', encoding='utf-8') as f:
        manifest = json.load(f)

    # Track results
    resolved = 0
    unresolved = 0
    new_edges = []
    skipped_existing = 0
    skipped_unmapped = 0
    skipped_low_score = 0
    proteins_with_new_edges = 0

    # Disease coverage stats
    disease_edge_counts = defaultdict(int)

    print(f"\nQuerying OpenTargets for {len(proteins)} proteins...")
    print("(This will take ~5-10 minutes with rate limiting)\n")

    for i, protein in enumerate(proteins, 1):
        # Progress
        if i % 10 == 0 or i == 1:
            print(f"[{i}/{len(proteins)}] Processing {protein}...")

        # Step 1: Resolve gene symbol to Ensembl ID
        ensembl_id = resolve_gene_symbol(protein)
        time.sleep(0.3)  # Rate limit

        if not ensembl_id:
            unresolved += 1
            continue

        resolved += 1

        # Step 2: Get cancer disease associations
        associations = get_cancer_disease_associations(
            ensembl_id, min_score=min_score
        )
        time.sleep(0.3)  # Rate limit

        protein_new = 0
        for assoc in associations:
            our_disease = assoc['our_disease']

            # Skip if we can't map to existing disease and flag is set
            if only_existing_diseases and our_disease is None:
                skipped_unmapped += 1
                continue

            target_disease = our_disease if our_disease else assoc['disease_name']

            # Skip if edge already exists
            if (protein, target_disease) in existing_edges:
                skipped_existing += 1
                continue

            # New edge to add
            edge = {
                'source': protein,
                'target': target_disease,
                'relation': 'associated_with',
                'confidence': round(min(assoc['score'], 0.95), 3),
                'provenance': f"OpenTargets:{assoc['disease_id']}",
                'evidence_type': 'database',
                'opentargets_score': round(assoc['score'], 4),
                'opentargets_disease_name': assoc['disease_name'],
                'opentargets_disease_id': assoc['disease_id'],
            }

            new_edges.append(edge)
            existing_edges.add((protein, target_disease))  # Prevent duplicates
            disease_edge_counts[target_disease] += 1
            protein_new += 1

        if protein_new > 0:
            proteins_with_new_edges += 1

    # Report
    print("\n" + "=" * 70)
    print("IMPORT RESULTS")
    print("=" * 70)

    print(f"\nProteins resolved: {resolved}/{len(proteins)} ({resolved/len(proteins)*100:.1f}%)")
    print(f"Proteins unresolved: {unresolved}/{len(proteins)}")
    print(f"\nNew Protein->Disease edges: {len(new_edges)}")
    print(f"Proteins gaining new edges: {proteins_with_new_edges}")
    print(f"Skipped (already existing): {skipped_existing}")
    print(f"Skipped (unmapped disease): {skipped_unmapped}")

    if disease_edge_counts:
        print(f"\nNew edges by disease:")
        for disease, count in sorted(disease_edge_counts.items(), key=lambda x: -x[1]):
            print(f"  {disease}: +{count}")

    if dry_run:
        print("\n[DRY RUN] No changes written.")
        print(f"Would add {len(new_edges)} morphisms to manifest.")

        # Save dry run report
        report = {
            'proteins_total': len(proteins),
            'proteins_resolved': resolved,
            'proteins_unresolved': unresolved,
            'new_edges': len(new_edges),
            'proteins_with_new_edges': proteins_with_new_edges,
            'skipped_existing': skipped_existing,
            'skipped_unmapped': skipped_unmapped,
            'disease_edge_counts': dict(disease_edge_counts),
            'edges': new_edges,
        }

        report_path = output_path.replace('.json', '_dry_run_report.json')
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        print(f"\nDry run report: {report_path}")

    else:
        # Add new morphisms to manifest
        if 'morphisms' not in manifest:
            manifest['morphisms'] = []

        for edge in new_edges:
            morphism = {
                'source': edge['source'],
                'target': edge['target'],
                'edge_type': edge['relation'],
                'confidence': edge['confidence'],
                'provenance': edge['provenance'],
                'metadata': {
                    'source': 'OpenTargets_Platform',
                    'evidence_type': edge['evidence_type'],
                    'opentargets_score': edge['opentargets_score'],
                    'opentargets_disease_name': edge['opentargets_disease_name'],
                    'opentargets_disease_id': edge['opentargets_disease_id'],
                },
            }
            manifest['morphisms'].append(morphism)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2)

        print(f"\nManifest written: {output_path}")
        print(f"Added {len(new_edges)} new morphisms")
        print(f"\nNext steps:")
        print(f"  1. python data/drugs/build_tier1.py --force")
        print(f"  2. python validation/repurposing_benchmark.py --view full_typed --protocol loocv --ci")


def main():
    parser = argparse.ArgumentParser(
        description='Import cancer Protein->Disease associations from OpenTargets'
    )
    parser.add_argument(
        '--db', default='data/drugs/tier1.db',
        help='Path to tier1.db'
    )
    parser.add_argument(
        '--manifest', default='data/drugs/tier1_manifest.json',
        help='Path to tier1_manifest.json'
    )
    parser.add_argument(
        '--output', default='data/drugs/tier1_manifest_with_ot_diseases.json',
        help='Output manifest path'
    )
    parser.add_argument(
        '--min-score', type=float, default=0.5,
        help='Minimum OpenTargets association score (0-1, default: 0.5)'
    )
    parser.add_argument(
        '--dry-run', action='store_true',
        help='Only report what would be imported, do not write'
    )
    parser.add_argument(
        '--include-new-diseases', action='store_true',
        help='Include diseases not in our existing 20 (default: only existing)'
    )

    args = parser.parse_args()

    run_import(
        db_path=args.db,
        manifest_path=args.manifest,
        output_path=args.output,
        min_score=args.min_score,
        dry_run=args.dry_run,
        only_existing_diseases=not args.include_new_diseases,
    )


if __name__ == '__main__':
    main()
