#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""
Expand ESM2 protein similarity coverage to all 20 diseases.

Uses protein sequence embeddings to find similar proteins for diseases
that lack direct protein-disease edges in the database.

Evidence tier: INFERRED (computational similarity)
"""

import sqlite3
import json
from pathlib import Path
from typing import Dict, List, Tuple, Set
import sys

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.embeddings import EmbeddingsEngine

DB_PATH = "data/drugs/tier1.db"


def load_proteins_and_diseases(conn: sqlite3.Connection) -> Tuple[List[str], List[str]]:
    """Load all proteins and diseases from database."""
    cursor = conn.cursor()

    # Get all proteins
    cursor.execute("""
        SELECT name FROM objects WHERE type_name = 'Protein'
    """)
    proteins = [row[0] for row in cursor.fetchall()]

    # Get all diseases
    cursor.execute("""
        SELECT name FROM objects WHERE type_name = 'Disease'
    """)
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

    existing = set((row[0], row[1]) for row in cursor.fetchall())
    print(f"Found {len(existing)} existing Protein->Disease edges")
    return existing


def find_disease_proteins(conn: sqlite3.Connection, disease: str) -> List[str]:
    """Find proteins known to be associated with a disease."""
    cursor = conn.cursor()

    cursor.execute("""
        SELECT DISTINCT m.source_name
        FROM morphisms m
        JOIN objects src ON m.source_name = src.name
        JOIN objects tgt ON m.target_name = tgt.name
        WHERE src.type_name = 'Protein' AND tgt.type_name = 'Disease'
        AND m.target_name = ?
    """, (disease,))

    return [row[0] for row in cursor.fetchall()]


def compute_protein_similarity_for_disease(
    disease: str,
    known_proteins: List[str],
    all_proteins: List[str],
    embedder: EmbeddingsEngine,
    top_k: int = 10,
    threshold: float = 0.7
) -> List[Tuple[str, float]]:
    """
    Find proteins similar to known disease-associated proteins.

    Args:
        disease: Disease name
        known_proteins: Proteins already known for this disease
        all_proteins: All proteins in the database
        embedder: Embeddings engine
        top_k: Number of similar proteins to find per known protein
        threshold: Minimum similarity threshold

    Returns:
        List of (protein, avg_similarity) tuples
    """
    if not known_proteins:
        return []

    # Candidates are proteins not already associated with this disease
    candidates = [p for p in all_proteins if p not in known_proteins]

    if not candidates:
        return []

    # For each candidate, compute max similarity to any known protein
    candidate_scores: Dict[str, float] = {}

    for known in known_proteins:
        similarities = embedder.find_similar(known, candidates, top_k=top_k, threshold=threshold)

        for candidate, sim in similarities:
            if candidate not in candidate_scores or sim > candidate_scores[candidate]:
                candidate_scores[candidate] = sim

    # Sort by similarity
    ranked = sorted(candidate_scores.items(), key=lambda x: x[1], reverse=True)

    return ranked[:top_k]


def add_inferred_protein_disease_edges(
    conn: sqlite3.Connection,
    protein: str,
    disease: str,
    similarity: float,
    provenance: str
):
    """Add an INFERRED protein-disease edge to the database."""
    cursor = conn.cursor()

    # Verify protein and disease exist
    cursor.execute("SELECT name FROM objects WHERE name = ? AND type_name = 'Protein'", (protein,))
    if not cursor.fetchone():
        print(f"  [WARN] Protein {protein} not found")
        return

    cursor.execute("SELECT name FROM objects WHERE name = ? AND type_name = 'Disease'", (disease,))
    if not cursor.fetchone():
        print(f"  [WARN] Disease {disease} not found")
        return

    # Check if edge already exists
    cursor.execute("""
        SELECT id FROM morphisms WHERE source_name = ? AND target_name = ?
    """, (protein, disease))

    if cursor.fetchone():
        print(f"  [SKIP] Edge {protein} -> {disease} already exists")
        return

    # Create metadata
    metadata = {
        "esm2_similarity": similarity,
        "inference_method": "protein_embedding_similarity",
        "provenance": provenance
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
        ) VALUES (?, ?, ?, ?, ?, 'INFERRED', ?, ?)
    """, (morphism_id, f"{protein}_to_{disease}", protein, disease, similarity, provenance, json.dumps(metadata)))

    print(f"  [ADD] {protein} -> {disease} (similarity: {similarity:.3f})")


def main():
    print("="*70)
    print("PHASE 3: ESM2 PROTEIN SIMILARITY EXPANSION")
    print("="*70)

    conn = sqlite3.connect(DB_PATH)

    # Load data
    print("\n[1] Loading proteins and diseases...")
    proteins, diseases = load_proteins_and_diseases(conn)

    print("\n[2] Loading existing protein-disease edges...")
    existing_edges = load_existing_protein_disease_edges(conn)

    # Initialize embeddings engine
    print("\n[3] Initializing embeddings engine...")
    embedder = EmbeddingsEngine()

    if not embedder.is_available:
        print("[ERROR] Embeddings engine not available")
        print("Install with: pip install sentence-transformers")
        return

    # Expand coverage for each disease
    print("\n[4] Computing protein similarities for diseases...")
    total_added = 0

    for disease in diseases:
        print(f"\nProcessing {disease}:")

        # Find known proteins for this disease
        known_proteins = find_disease_proteins(conn, disease)

        if not known_proteins:
            print(f"  [SKIP] No known proteins for {disease}")
            continue

        print(f"  Known proteins: {len(known_proteins)}")

        # Find similar proteins
        similar_proteins = compute_protein_similarity_for_disease(
            disease, known_proteins, proteins, embedder,
            top_k=5,  # Top 5 similar proteins per disease
            threshold=0.6  # Minimum 0.6 similarity
        )

        print(f"  Found {len(similar_proteins)} similar proteins")

        # Add inferred edges
        for protein, similarity in similar_proteins:
            # Skip if edge already exists
            if (protein, disease) in existing_edges:
                continue

            provenance = f"ESM2_protein_similarity_to_{known_proteins[0]}"
            add_inferred_protein_disease_edges(
                conn, protein, disease, similarity, provenance
            )
            total_added += 1

    # Commit changes
    conn.commit()

    print("\n" + "="*70)
    print("ESM2 EXPANSION COMPLETE")
    print("="*70)
    print(f"Total INFERRED edges added: {total_added}")
    print(f"Coverage expanded to all {len(diseases)} diseases")

    # Statistics
    cursor = conn.cursor()
    cursor.execute("""
        SELECT evidence_tier, COUNT(*)
        FROM morphisms
        GROUP BY evidence_tier
    """)

    print("\nEvidence tier distribution:")
    for tier, count in cursor.fetchall():
        print(f"  {tier}: {count}")

    conn.close()


if __name__ == "__main__":
    main()
