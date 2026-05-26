#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""
Import STRING protein-protein interactions (PPI) with high confidence scores.

STRING database: https://string-db.org/
API: https://string-db.org/cgi/help?sessionId=bfBHqhNYkJXU&subpage=api

Only imports interactions with:
- Combined score >= 0.7 (high confidence)
- Both proteins in our database

Evidence tier: INFERRED (computational prediction + literature)
"""

import sqlite3
import json
import requests
import time
from pathlib import Path
from typing import List, Set, Tuple
import sys

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

DB_PATH = "data/drugs/tier1.db"
STRING_API = "https://string-db.org/api"
SPECIES_ID = "9606"  # Homo sapiens


def load_proteins(conn: sqlite3.Connection) -> List[str]:
    """Load all proteins from database."""
    cursor = conn.cursor()

    cursor.execute("""
        SELECT name FROM objects WHERE type_name = 'Protein'
    """)

    proteins = [row[0] for row in cursor.fetchall()]
    print(f"Loaded {len(proteins)} proteins from database")
    return proteins


def load_existing_ppi_edges(conn: sqlite3.Connection) -> Set[Tuple[str, str]]:
    """Load existing protein-protein edges."""
    cursor = conn.cursor()

    cursor.execute("""
        SELECT DISTINCT m.source_name, m.target_name
        FROM morphisms m
        JOIN objects src ON m.source_name = src.name
        JOIN objects tgt ON m.target_name = tgt.name
        WHERE src.type_name = 'Protein' AND tgt.type_name = 'Protein'
    """)

    existing = set()
    for source, target in cursor.fetchall():
        # Add both directions (PPI are symmetric)
        existing.add((source, target))
        existing.add((target, source))

    print(f"Found {len(existing)//2} existing Protein-Protein edges")
    return existing


def query_string_interactions(
    proteins: List[str],
    score_threshold: float = 0.7
) -> List[Tuple[str, str, float, str]]:
    """
    Query STRING API for high-confidence interactions.

    Args:
        proteins: List of protein names (gene symbols)
        score_threshold: Minimum combined score (0-1)

    Returns:
        List of (protein1, protein2, score, evidence_string)
    """
    print(f"\nQuerying STRING API for {len(proteins)} proteins...")
    print(f"Score threshold: {score_threshold} (high confidence)")

    # STRING requires gene symbols/UniProt IDs
    # Our proteins are gene symbols, so we can use them directly

    # Query in batches to avoid overwhelming the API
    batch_size = 50
    all_interactions = []

    for i in range(0, len(proteins), batch_size):
        batch = proteins[i:i+batch_size]

        print(f"  Batch {i//batch_size + 1}/{(len(proteins)-1)//batch_size + 1}: {len(batch)} proteins")

        # Use network endpoint to get interactions
        url = f"{STRING_API}/tsv/network"
        params = {
            "identifiers": "%0d".join(batch),  # Newline-separated
            "species": SPECIES_ID,
            "required_score": int(score_threshold * 1000),  # Convert to 0-1000 scale
            "limit": 0,  # No limit
        }

        try:
            response = requests.get(url, params=params, timeout=30)

            if response.status_code == 200:
                lines = response.text.strip().split("\n")

                # Skip header
                for line in lines[1:]:
                    parts = line.split("\t")

                    if len(parts) < 6:
                        continue

                    # Parse STRING output
                    # Format: stringId_A, stringId_B, preferredName_A, preferredName_B, ncbiTaxonId, score, ...
                    protein_a_id = parts[2]  # preferredName_A
                    protein_b_id = parts[3]  # preferredName_B
                    score = float(parts[5])  # score

                    # Evidence channels: nscore, fscore, pscore, ascore, escore, dscore, tscore
                    # Indices: 6=nscore, 7=fscore, 8=pscore, 9=ascore, 10=escore, 11=dscore, 12=tscore
                    evidence_types = []
                    if len(parts) > 12:  # Has evidence channels
                        if len(parts) > 10 and float(parts[10]) > 0:  # escore (experimental)
                            evidence_types.append("experimental")
                        if len(parts) > 11 and float(parts[11]) > 0:  # dscore (database)
                            evidence_types.append("database")
                        if len(parts) > 12 and float(parts[12]) > 0:  # tscore (textmining)
                            evidence_types.append("textmining")
                        if len(parts) > 9 and float(parts[9]) > 0:  # ascore (coexpression)
                            evidence_types.append("coexpression")

                    evidence_str = "+".join(evidence_types) if evidence_types else "combined"

                    all_interactions.append((
                        protein_a_id, protein_b_id, score / 1000.0, evidence_str
                    ))

            else:
                print(f"    [WARN] STRING API returned status {response.status_code}")

        except requests.exceptions.RequestException as e:
            print(f"    [ERROR] Failed to query STRING: {e}")

        # Rate limiting
        time.sleep(0.5)

    print(f"  Retrieved {len(all_interactions)} interactions from STRING")
    return all_interactions


def add_ppi_edge(
    conn: sqlite3.Connection,
    protein_a: str,
    protein_b: str,
    score: float,
    evidence_types: str
):
    """Add a protein-protein interaction edge to the database."""
    cursor = conn.cursor()

    # Verify proteins exist
    cursor.execute("SELECT name FROM objects WHERE name = ? AND type_name = 'Protein'", (protein_a,))
    if not cursor.fetchone():
        return

    cursor.execute("SELECT name FROM objects WHERE name = ? AND type_name = 'Protein'", (protein_b,))
    if not cursor.fetchone():
        return

    # Check if edge already exists (either direction)
    cursor.execute("""
        SELECT id FROM morphisms
        WHERE (source_name = ? AND target_name = ?)
           OR (source_name = ? AND target_name = ?)
    """, (protein_a, protein_b, protein_b, protein_a))

    if cursor.fetchone():
        return  # Already exists

    # Create metadata
    metadata = {
        "string_score": score,
        "evidence_types": evidence_types,
        "source": "STRING_v12.0",
        "species": "Homo sapiens"
    }

    # Insert morphism (bidirectional, so add both directions)
    import uuid
    for source, target in [(protein_a, protein_b), (protein_b, protein_a)]:
        morphism_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO morphisms (
                id, name, source_name, target_name,
                confidence, evidence_tier, provenance,
                metadata
            ) VALUES (?, ?, ?, ?, ?, 'INFERRED', ?, ?)
        """, (morphism_id, f"{source}_interacts_{target}", source, target, score, f"STRING_v12_score_{score:.3f}", json.dumps(metadata)))

    print(f"  [ADD] {protein_a} <-> {protein_b} (score: {score:.3f}, evidence: {evidence_types})")


def main():
    print("="*70)
    print("PHASE 3: STRING PROTEIN-PROTEIN INTERACTION IMPORT")
    print("="*70)

    conn = sqlite3.connect(DB_PATH)

    # Load proteins
    print("\n[1] Loading proteins from database...")
    proteins = load_proteins(conn)

    print("\n[2] Loading existing PPI edges...")
    existing_edges = load_existing_ppi_edges(conn)

    # Query STRING
    print("\n[3] Querying STRING database...")
    interactions = query_string_interactions(proteins, score_threshold=0.7)

    # Filter to proteins in our database
    protein_set = set(proteins)
    filtered_interactions = [
        (p1, p2, score, evidence)
        for p1, p2, score, evidence in interactions
        if p1 in protein_set and p2 in protein_set
    ]

    print(f"\n  Filtered to {len(filtered_interactions)} interactions with both proteins in DB")

    # Add to database
    print("\n[4] Adding high-confidence PPIs to database...")
    total_added = 0

    for protein_a, protein_b, score, evidence_types in filtered_interactions:
        # Skip if already exists
        if (protein_a, protein_b) in existing_edges:
            continue

        add_ppi_edge(conn, protein_a, protein_b, score, evidence_types)
        total_added += 1

    # Commit
    conn.commit()

    print("\n" + "="*70)
    print("STRING PPI IMPORT COMPLETE")
    print("="*70)
    print(f"Total PPI edges added: {total_added * 2} (bidirectional)")
    print(f"Unique protein pairs: {total_added}")

    # Statistics
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*)
        FROM morphisms m
        JOIN objects src ON m.source_name = src.name
        JOIN objects tgt ON m.target_name = tgt.name
        WHERE src.type_name = 'Protein' AND tgt.type_name = 'Protein'
    """)
    total_ppi = cursor.fetchone()[0]

    print(f"\nTotal Protein-Protein edges in database: {total_ppi}")

    conn.close()


if __name__ == "__main__":
    main()
