# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""
Validate generated conjectures against historical records.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from data import KomposOSStore, EmbeddingsEngine
from oracle import CategoricalOracle
from oracle.conjecture import ConjectureEngine

# Historical validation data
# Format: (source, target) -> (is_correct, evidence)
HISTORICAL_VALIDATION = {
    # Confirmed influences from physics history
    ("Newton", "Lagrange"): (True, "Lagrange's analytical mechanics built directly on Newton's principles"),
    ("Newton", "Hamilton"): (True, "Hamilton reformulated Newtonian mechanics"),
    ("Lagrange", "Hamilton"): (True, "Hamilton extended Lagrange's formulation"),
    ("Galileo", "Euler"): (True, "Euler studied Galilean mechanics and extended it"),
    ("Kepler", "Euler"): (True, "Euler worked on celestial mechanics building on Kepler's laws"),
    ("Faraday", "Einstein"): (True, "Maxwell's equations (based on Faraday) influenced Einstein's relativity"),
    ("Faraday", "Maxwell"): (True, "Maxwell formalized Faraday's field theory"),
    ("Maxwell", "Einstein"): (True, "Maxwell's equations were foundational to special relativity"),
    ("Lorentz", "Einstein"): (True, "Lorentz transformations are central to special relativity"),
    ("Lorentz", "Bohr"): (False, "No direct influence - different research areas"),
    ("Poincare", "Einstein"): (True, "Poincare's work on relativity influenced Einstein"),
    ("Poincare", "Bohr"): (False, "No direct documented influence"),
    ("Heisenberg", "Schwinger"): (True, "Schwinger extended Heisenberg's quantum mechanics to QFT"),
    ("Schrodinger", "Schwinger"): (True, "Schwinger unified wave and matrix mechanics approaches"),
    ("Sommerfeld", "Dirac"): (True, "Sommerfeld was Heisenberg's advisor, influenced quantum theory development"),
    ("deBroglie", "Dirac"): (True, "Wave-particle duality influenced Dirac's quantum theory"),
    ("Born", "Feynman"): (True, "Born's probability interpretation influenced QFT"),
    ("Dirac", "Feynman"): (True, "Feynman built on Dirac's quantum electrodynamics"),
}

def main():
    print("=" * 80)
    print("Conjecture Validation")
    print("=" * 80)
    print()

    # Load store and check existing morphisms
    print("[1/4] Loading existing data...")
    store = KomposOSStore('data/store.db')
    existing_morphisms = store.list_morphisms(limit=10000)
    existing_pairs = {(m.source_name, m.target_name) for m in existing_morphisms}
    print(f"  Existing morphisms: {len(existing_morphisms)}")
    print()

    # Generate conjectures
    print("[2/4] Generating conjectures...")
    embeddings = EmbeddingsEngine()
    oracle = CategoricalOracle(store, embeddings, min_confidence=0.5)
    engine = ConjectureEngine(oracle, semantic_top_k=10)
    result = engine.conjecture(top_k=30, min_confidence=0.5)
    print(f"  Generated: {len(result.conjectures)} conjectures")
    print()

    # Validate
    print("[3/4] Validating against historical records...")
    print("-" * 80)

    validated = []
    for conj in result.conjectures[:20]:
        pair = (conj.source, conj.target)
        is_novel = pair not in existing_pairs

        # Check historical validation
        if pair in HISTORICAL_VALIDATION:
            is_correct, evidence = HISTORICAL_VALIDATION[pair]
            status = "CORRECT" if is_correct else "INCORRECT"
        else:
            is_correct = None
            evidence = "Not in validation set"
            status = "UNKNOWN"

        validated.append({
            'conjecture': conj,
            'is_novel': is_novel,
            'is_correct': is_correct,
            'status': status,
            'evidence': evidence
        })

        novelty = "[NOVEL]" if is_novel else "[EXISTS]"
        print(f"{novelty} {status:10s} | {conj.source:15s} -> {conj.target:15s} | conf={conj.top_confidence:.3f}")
        if evidence != "Not in validation set":
            print(f"              Evidence: {evidence}")
        print()

    # Statistics
    print()
    print("[4/4] Validation Statistics")
    print("-" * 80)

    novel_count = sum(1 for v in validated if v['is_novel'])
    correct_count = sum(1 for v in validated if v['is_correct'] == True)
    incorrect_count = sum(1 for v in validated if v['is_correct'] == False)
    unknown_count = sum(1 for v in validated if v['is_correct'] is None)

    print(f"Total conjectures evaluated: {len(validated)}")
    print(f"Novel (not in training data): {novel_count}")
    print(f"Correct: {correct_count}")
    print(f"Incorrect: {incorrect_count}")
    print(f"Unknown (need manual validation): {unknown_count}")
    print()

    if correct_count + incorrect_count > 0:
        precision = correct_count / (correct_count + incorrect_count)
        print(f"Precision (on validated set): {precision:.1%}")
    print()

    # Highlight best novel conjectures
    print("=" * 80)
    print("TOP NOVEL CONJECTURES FOR DEEPMIND")
    print("=" * 80)
    print()

    novel_correct = [v for v in validated if v['is_novel'] and v['is_correct'] == True]
    if novel_correct:
        print("These were NOT in the training data but are historically verified:")
        print()
        for v in novel_correct[:5]:
            conj = v['conjecture']
            print(f"  {conj.source} -> {conj.target}")
            print(f"  Confidence: {conj.top_confidence:.3f}")
            print(f"  Strategies: {'+'.join(conj.candidate_sources)}")
            print(f"  Evidence: {v['evidence']}")
            print()
    else:
        print("No novel+correct conjectures in this run.")
        print("(The system may need more training data or the dataset is complete)")

    print("=" * 80)

if __name__ == "__main__":
    main()
