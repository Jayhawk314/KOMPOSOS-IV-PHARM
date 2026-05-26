#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""
Import OpenTargets gene-disease associations.

OpenTargets: https://www.targetvalidation.org/
GraphQL API: https://api.platform.opentargets.org/api/v4/graphql

Imports high-confidence associations (overall score >= 0.5) for
diseases and genes/proteins in our database.

Evidence tier: Varies by evidence type
- Clinical: MEASURED (clinical trials, FDA labels)
- Genetic: ESTABLISHED (GWAS, rare disease genetics)
- Literature: HYPOTHESIS (text-mined associations)
- Animal models, pathways: INFERRED
"""

import sqlite3
import json
import requests
import time
from pathlib import Path
from typing import List, Dict, Set, Tuple
import sys

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

DB_PATH = "data/drugs/tier1.db"
OPENTARGETS_API = "https://api.platform.opentargets.org/api/v4/graphql"


# Disease name to EFO/MONDO ID mapping (manual for now)
DISEASE_TO_EFO = {
    "AML": "EFO_0000222",  # Acute myeloid leukemia
    "CML": "EFO_0000339",  # Chronic myelogenous leukemia
    "Melanoma": "EFO_0000756",
    "RCC": "EFO_0000681",  # Renal cell carcinoma
    "NSCLC": "EFO_0003060",  # Non-small cell lung carcinoma
    "GIST": "EFO_0002916",  # Gastrointestinal stromal tumor
    "Breast_Cancer": "EFO_0000305",
    "Prostate_Cancer": "EFO_0001663",
    "Colorectal_Cancer": "EFO_0005842",
    "Ovarian_Cancer": "EFO_0001075",
    "Pancreatic_Cancer": "EFO_0002618",
    "Gastric_Cancer": "EFO_0000503",
    "Hepatocellular_Carcinoma": "EFO_0000182",
    "Thyroid_Cancer": "EFO_0002892",
    "Bladder_Cancer": "EFO_0000292",
    "Multiple_Myeloma": "EFO_0001378",
    "Lymphoma": "EFO_0000574",
    "Sarcoma": "EFO_0000626",
    "Brain_Tumor": "EFO_0005543",  # Glioma
}


def load_proteins_and_diseases(conn: sqlite3.Connection) -> Tuple[List[str], List[str]]:
    """Load all proteins and diseases from database."""
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM objects WHERE type_name = 'Protein'")
    proteins = [row[0] for row in cursor.fetchall()]

    cursor.execute("SELECT name FROM objects WHERE type_name = 'Disease'")
    diseases = [row[0] for row in cursor.fetchall()]

    print(f"Loaded {len(proteins)} proteins, {len(diseases)} diseases")
    return proteins, diseases


def load_existing_protein_disease_edges(conn: sqlite3.Connection) -> Set[Tuple[str, str]]:
    """Load existing protein-disease edges."""
    cursor = conn.cursor()

    cursor.execute("""
        SELECT DISTINCT m.source_name, m.target_name
        FROM morphisms m
        JOIN objects src ON m.source_name = src.name
        JOIN objects tgt ON m.target_name = tgt.name
        WHERE src.type_name = 'Protein' AND tgt.type_name = 'Disease'
    """)

    return set((row[0], row[1]) for row in cursor.fetchall())


def query_opentargets_disease(disease_efo: str) -> List[Dict]:
    """
    Query OpenTargets for gene-disease associations.

    Args:
        disease_efo: EFO/MONDO disease ID

    Returns:
        List of association dictionaries
    """
    query = """
    query TargetsAssociatedWithDisease($efoId: String!) {
      disease(efoId: $efoId) {
        id
        name
        associatedTargets(page: {size: 100}) {
          rows {
            target {
              id
              approvedSymbol
              approvedName
            }
            score
            datatypeScores {
              id
              score
            }
          }
        }
      }
    }
    """

    variables = {"efoId": disease_efo}

    try:
        response = requests.post(
            OPENTARGETS_API,
            json={"query": query, "variables": variables},
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()

            if "data" in data and "disease" in data["data"] and data["data"]["disease"]:
                return data["data"]["disease"]["associatedTargets"]["rows"]

    except requests.exceptions.RequestException as e:
        print(f"  [ERROR] Failed to query OpenTargets: {e}")

    return []


def classify_evidence_tier(datatype_scores: List[Dict]) -> str:
    """
    Classify evidence tier based on OpenTargets datatype scores.

    Evidence types in OpenTargets:
    - affected_pathway: INFERRED
    - animal_model: INFERRED
    - genetic_association: ESTABLISHED
    - known_drug: MEASURED
    - literature: HYPOTHESIS
    - rna_expression: INFERRED
    - somatic_mutation: ESTABLISHED

    Args:
        datatype_scores: List of {id: datatype, score: float}

    Returns:
        Evidence tier string
    """
    # Priority order: known_drug > somatic_mutation > genetic_association > literature > others
    tier_priority = {
        "known_drug": "MEASURED",
        "somatic_mutation": "ESTABLISHED",
        "genetic_association": "ESTABLISHED",
        "literature": "HYPOTHESIS",
        "affected_pathway": "INFERRED",
        "animal_model": "INFERRED",
        "rna_expression": "INFERRED",
    }

    # Find highest-priority tier with score > 0
    for datatype, tier in tier_priority.items():
        for score_entry in datatype_scores:
            if score_entry["id"] == datatype and score_entry["score"] > 0.0:
                return tier

    return "HYPOTHESIS"  # Default


def add_protein_disease_association(
    conn: sqlite3.Connection,
    protein: str,
    disease: str,
    overall_score: float,
    evidence_tier: str,
    datatype_scores: List[Dict]
):
    """Add protein-disease association from OpenTargets."""
    cursor = conn.cursor()

    # Verify protein and disease exist
    cursor.execute("SELECT name FROM objects WHERE name = ? AND type_name = 'Protein'", (protein,))
    if not cursor.fetchone():
        return

    cursor.execute("SELECT name FROM objects WHERE name = ? AND type_name = 'Disease'", (disease,))
    if not cursor.fetchone():
        return

    # Check if edge exists
    cursor.execute("""
        SELECT id FROM morphisms WHERE source_name = ? AND target_name = ?
    """, (protein, disease))

    if cursor.fetchone():
        return  # Already exists

    # Create metadata
    evidence_breakdown = {
        score_entry["id"]: score_entry["score"]
        for score_entry in datatype_scores
        if score_entry["score"] > 0
    }

    metadata = {
        "opentargets_overall_score": overall_score,
        "evidence_breakdown": evidence_breakdown,
        "source": "OpenTargets_v24.03"
    }

    # Generate unique ID
    import uuid
    morphism_id = str(uuid.uuid4())

    # Insert morphism
    cursor.execute("""
        INSERT INTO morphisms (
            id, name, source_name, target_name,
            confidence, evidence_tier, provenance,
            metadata
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        morphism_id, f"{protein}_to_{disease}",
        protein, disease,
        overall_score, evidence_tier,
        f"OpenTargets_score_{overall_score:.3f}",
        json.dumps(metadata)
    ))

    print(f"  [ADD] {protein} -> {disease} ({evidence_tier}, score: {overall_score:.3f})")


def main():
    print("="*70)
    print("PHASE 3: OPENTARGETS GENE-DISEASE ASSOCIATION IMPORT")
    print("="*70)

    conn = sqlite3.connect(DB_PATH)

    # Load data
    print("\n[1] Loading proteins and diseases...")
    proteins, diseases = load_proteins_and_diseases(conn)
    protein_set = set(proteins)

    print("\n[2] Loading existing protein-disease edges...")
    existing_edges = load_existing_protein_disease_edges(conn)

    # Query OpenTargets for each disease
    print("\n[3] Querying OpenTargets for gene-disease associations...")
    total_added = 0

    for disease in diseases:
        if disease not in DISEASE_TO_EFO:
            print(f"\n[SKIP] {disease}: No EFO ID mapping")
            continue

        disease_efo = DISEASE_TO_EFO[disease]
        print(f"\nQuerying {disease} ({disease_efo})...")

        associations = query_opentargets_disease(disease_efo)
        print(f"  Retrieved {len(associations)} associations")

        # Filter and add associations
        added_for_disease = 0

        for assoc in associations:
            target_symbol = assoc["target"]["approvedSymbol"]
            overall_score = assoc["score"]
            datatype_scores = assoc["datatypeScores"]

            # Skip if score too low
            if overall_score < 0.5:
                continue

            # Skip if protein not in our database
            if target_symbol not in protein_set:
                continue

            # Skip if edge already exists
            if (target_symbol, disease) in existing_edges:
                continue

            # Classify evidence tier
            evidence_tier = classify_evidence_tier(datatype_scores)

            # Add to database
            add_protein_disease_association(
                conn, target_symbol, disease,
                overall_score, evidence_tier, datatype_scores
            )

            added_for_disease += 1

        print(f"  Added {added_for_disease} associations for {disease}")
        total_added += added_for_disease

        # Rate limiting
        time.sleep(1.0)

    # Commit
    conn.commit()

    print("\n" + "="*70)
    print("OPENTARGETS IMPORT COMPLETE")
    print("="*70)
    print(f"Total associations added: {total_added}")

    # Statistics by tier
    cursor = conn.cursor()
    cursor.execute("""
        SELECT evidence_tier, COUNT(*)
        FROM morphisms
        WHERE provenance LIKE 'OpenTargets%'
        GROUP BY evidence_tier
    """)

    print("\nOpenTargets associations by evidence tier:")
    for tier, count in cursor.fetchall():
        print(f"  {tier}: {count}")

    conn.close()


if __name__ == "__main__":
    main()
