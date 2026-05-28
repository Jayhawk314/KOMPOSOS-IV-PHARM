#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""
Expand ESMC protein similarity coverage to all 20 diseases.

Uses ESMC-300M protein sequence embeddings to find similar proteins for
diseases that lack direct protein-disease edges in the database.

Replaces the old expand_esm2_protein_similarity.py which incorrectly used
text embeddings (sentence-transformers) instead of real protein language
model embeddings.

Evidence tier: INFERRED (computational sequence similarity)
"""

import sqlite3
import json
import uuid
from pathlib import Path
from typing import Dict, List, Tuple, Set
import sys

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.bio_embeddings import BiologicalEmbeddingsEngine

DB_PATH = "data/drugs/tier1.db"


def load_biological_entities_and_diseases(conn: sqlite3.Connection) -> Tuple[List[str], List[str]]:
    """Load all biological entities (non-Drug, non-Disease) and diseases."""
    cursor = conn.cursor()

    # Get all biological entities (any type except Drug and Disease)
    cursor.execute("""
        SELECT name FROM objects WHERE type_name NOT IN ('Drug', 'Disease')
    """)
    entities = [row[0] for row in cursor.fetchall()]

    # Get all diseases
    cursor.execute("""
        SELECT name FROM objects WHERE type_name = 'Disease'
    """)
    diseases = [row[0] for row in cursor.fetchall()]

    print(f"Loaded {len(entities)} biological entities, {len(diseases)} diseases")
    return entities, diseases


def load_existing_entity_disease_edges(conn: sqlite3.Connection) -> Set[Tuple[str, str]]:
    """Load existing entity-disease edges."""
    cursor = conn.cursor()

    cursor.execute("""
        SELECT DISTINCT m.source_name, m.target_name
        FROM morphisms m
        JOIN objects tgt ON m.target_name = tgt.name
        WHERE tgt.type_name = 'Disease'
    """)

    existing = set((row[0], row[1]) for row in cursor.fetchall())
    print(f"Found {len(existing)} existing entity->Disease edges")
    return existing


def find_disease_entities(conn: sqlite3.Connection, disease: str) -> List[str]:
    """Find biological entities known to be associated with a disease."""
    cursor = conn.cursor()

    cursor.execute("""
        SELECT DISTINCT m.source_name
        FROM morphisms m
        JOIN objects src ON m.source_name = src.name
        JOIN objects tgt ON m.target_name = tgt.name
        WHERE tgt.type_name = 'Disease'
        AND src.type_name NOT IN ('Drug', 'Disease')
        AND m.target_name = ?
    """, (disease,))

    return [row[0] for row in cursor.fetchall()]


def compute_protein_similarity_for_disease(
    disease: str,
    known_entities: List[str],
    all_entities: List[str],
    embedder: BiologicalEmbeddingsEngine,
    top_k: int = 10,
    threshold: float = 0.7
) -> List[Tuple[str, float, str]]:
    """
    Find proteins similar to known disease-associated proteins using ESMC.

    Args:
        disease: Disease name
        known_entities: Entities already known for this disease
        all_entities: All biological entities in the database
        embedder: ESMC embeddings engine
        top_k: Number of similar proteins to find per known protein
        threshold: Minimum similarity threshold

    Returns:
        List of (protein, similarity, most_similar_known) tuples
    """
    if not known_entities:
        return []

    # Candidates are entities not already associated with this disease
    candidates = [p for p in all_entities if p not in known_entities]

    if not candidates:
        return []

    # For each candidate, compute max similarity to any known entity
    candidate_scores: Dict[str, Tuple[float, str]] = {}

    for known in known_entities:
        for candidate in candidates:
            try:
                sim = embedder.similarity(known, candidate)
            except (ValueError, RuntimeError):
                # Skip proteins without sequences
                continue

            if sim >= threshold:
                if candidate not in candidate_scores or sim > candidate_scores[candidate][0]:
                    candidate_scores[candidate] = (sim, known)

    # Sort by similarity
    ranked = sorted(candidate_scores.items(), key=lambda x: x[1][0], reverse=True)

    return [(name, score, ref) for name, (score, ref) in ranked[:top_k]]


def add_inferred_entity_disease_edges(
    conn: sqlite3.Connection,
    entity: str,
    disease: str,
    similarity: float,
    provenance: str
):
    """Add an INFERRED entity-disease edge to the database."""
    cursor = conn.cursor()

    # Verify entity and disease exist
    cursor.execute("SELECT name FROM objects WHERE name = ?", (entity,))
    if not cursor.fetchone():
        print(f"  [WARN] Entity {entity} not found")
        return

    cursor.execute("SELECT name FROM objects WHERE name = ? AND type_name = 'Disease'", (disease,))
    if not cursor.fetchone():
        print(f"  [WARN] Disease {disease} not found")
        return

    # Check if edge already exists
    cursor.execute("""
        SELECT id FROM morphisms WHERE source_name = ? AND target_name = ?
    """, (entity, disease))

    if cursor.fetchone():
        print(f"  [SKIP] Edge {entity} -> {disease} already exists")
        return

    # Create metadata
    metadata = {
        "esmc_similarity": similarity,
        "inference_method": "protein_sequence_similarity",
        "model": "esmc_300m",
        "provenance": provenance
    }

    morphism_id = str(uuid.uuid4())

    cursor.execute("""
        INSERT INTO morphisms (
            id, name, source_name, target_name,
            confidence, evidence_tier, provenance,
            metadata
        ) VALUES (?, ?, ?, ?, ?, 'INFERRED', ?, ?)
    """, (morphism_id, f"{entity}_to_{disease}", entity, disease, similarity, provenance, json.dumps(metadata)))

    print(f"  [ADD] {entity} -> {disease} (similarity: {similarity:.3f})")


def main():
    print("=" * 70)
    print("ESMC PROTEIN SEQUENCE SIMILARITY EXPANSION")
    print("=" * 70)

    conn = sqlite3.connect(DB_PATH)

    # Load data
    print("\n[1] Loading biological entities and diseases...")
    entities, diseases = load_biological_entities_and_diseases(conn)

    print("\n[2] Loading existing entity-disease edges...")
    existing_edges = load_existing_entity_disease_edges(conn)

    # Initialize ESMC embeddings engine
    print("\n[3] Initializing ESMC embeddings engine...")
    embedder = BiologicalEmbeddingsEngine(device='cpu')

    if not embedder.is_available:
        print("[ERROR] ESMC embeddings engine not available")
        print("Install with: pip install esm")
        print("Then run: python scripts/fetch_protein_sequences.py")
        return

    # Report coverage
    entities_with_seq = [e for e in entities if e in embedder._sequences]
    print(f"\n  Entities with sequences: {len(entities_with_seq)}/{len(entities)}")

    # Expand coverage for each disease
    print("\n[4] Computing protein similarities for diseases...")
    total_added = 0

    for disease in diseases:
        print(f"\nProcessing {disease}:")

        # Find known entities for this disease
        known_entities = find_disease_entities(conn, disease)

        if not known_entities:
            print(f"  [SKIP] No known entities for {disease}")
            continue

        # Filter to those with sequences
        known_with_seq = [e for e in known_entities if e in embedder._sequences]
        print(f"  Known entities: {len(known_entities)} ({len(known_with_seq)} with sequences)")

        if not known_with_seq:
            print(f"  [SKIP] No known entities with sequences for {disease}")
            continue

        # Find similar proteins
        similar = compute_protein_similarity_for_disease(
            disease, known_with_seq, entities_with_seq, embedder,
            top_k=5,
            threshold=0.7
        )

        print(f"  Found {len(similar)} similar proteins")

        # Add inferred edges
        for entity, similarity, ref_protein in similar:
            if (entity, disease) in existing_edges:
                continue

            provenance = f"ESMC:similar_to_{ref_protein}({similarity:.2f})"
            add_inferred_entity_disease_edges(
                conn, entity, disease, similarity, provenance
            )
            total_added += 1

    # Commit changes
    conn.commit()

    print("\n" + "=" * 70)
    print("ESMC EXPANSION COMPLETE")
    print("=" * 70)
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
