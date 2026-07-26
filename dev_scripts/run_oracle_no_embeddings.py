#!/usr/bin/env python3
"""
Run Oracle on Bio Data - NO EMBEDDINGS NEEDED

Uses only the strategies that work without embeddings:
- Kan Extension (categorical)
- Composition (path-based)
- Yoneda Pattern (morphism patterns)
- Fibration Lift (structural)
- Type Heuristic (type-based)
- Structural Hole (triangle closure)
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from domains.bio import BioDomainLoader
from core.category import Category
from oracle.strategies import (
    KanExtensionStrategy,
    CompositionStrategy,
    YonedaPatternStrategy,
    FibrationLiftStrategy,
    TypeHeuristicStrategy,
    StructuralHoleStrategy
)

def main():
    print("=" * 80)
    print("ORACLE ON BIO DATA - 6 Strategies (No Embeddings)")
    print("=" * 80)

    # Load tier1.db
    print("\n[1] Loading tier1.db...")
    loader = BioDomainLoader()
    cat = Category(name="BioTier1", db_path=":memory:")
    loader.load_tier1("data/drugs/tier1.db", cat)
    stats = loader.get_stats()
    print(f"  Loaded: {stats['objects_loaded']} objects, {stats['morphisms_loaded']} morphisms")

    # Initialize strategies
    print("\n[2] Initializing 6 strategies...")
    strategies = [
        KanExtensionStrategy(cat),
        CompositionStrategy(cat),
        YonedaPatternStrategy(cat),
        FibrationLiftStrategy(cat),
        TypeHeuristicStrategy(cat),
        StructuralHoleStrategy(cat),
    ]

    for i, s in enumerate(strategies, 1):
        print(f"  {i}. {s.name}")

    # Find drugs and diseases
    print("\n[3] Finding Drug and Disease objects...")
    drugs = [obj for obj in cat.objects() if obj.type_name == "Drug"]
    diseases = [obj for obj in cat.objects() if obj.type_name == "Disease"]
    proteins = [obj for obj in cat.objects() if obj.type_name not in ["Drug", "Disease", "Object"]]

    print(f"  Drugs: {len(drugs)}")
    print(f"  Diseases: {len(diseases)}")
    print(f"  Proteins: {len(proteins)}")

    # Run predictions
    print("\n[4] Running predictions (Drug -> Disease)...")
    predictions = []

    for drug in drugs[:5]:  # Top 5 drugs
        for disease in diseases[:5]:  # Top 5 diseases
            # Skip if edge exists
            if cat.hom(drug.name, disease.name) is not None:
                continue

            # Run each strategy
            votes = []
            for strategy in strategies:
                try:
                    preds = strategy.predict(drug.name, disease.name)
                    if len(preds) > 0:
                        votes.append((strategy.name, preds[0].confidence))
                except Exception as e:
                    pass

            if len(votes) >= 2:  # At least 2 strategies vote
                avg_conf = sum(v[1] for v in votes) / len(votes)
                predictions.append({
                    'source': drug.name,
                    'target': disease.name,
                    'confidence': avg_conf,
                    'n_strategies': len(votes),
                    'strategies': [v[0] for v in votes]
                })

    predictions.sort(key=lambda x: (-x['n_strategies'], -x['confidence']))

    print(f"\n[5] Top 10 Predictions:")
    for i, pred in enumerate(predictions[:10], 1):
        src = pred['source']
        tgt = pred['target']
        conf = pred['confidence']
        n = pred['n_strategies']
        strats = ', '.join(pred['strategies'][:2])
        print(f"  {i:2d}. {src:15s} -> {tgt:20s}")
        print(f"      Confidence: {conf:.3f}, Strategies: {n} ({strats}...)")

    # Show compositional paths
    if len(predictions) > 0:
        print("\n[6] Finding paths for top prediction...")
        top = predictions[0]
        paths = cat.find_paths(top['source'], top['target'], max_length=3)
        print(f"  Found {len(paths)} paths from {top['source']} to {top['target']}")

        for i, path in enumerate(paths[:3], 1):
            # Reconstruct path names
            path_names = [top['source']]
            for mid in path.morphism_ids:
                mor = cat.get_morphism(mid)
                if mor:
                    path_names.append(mor.target)

            print(f"    Path {i}: {' -> '.join(path_names)}")
            print(f"            Weight: {path.weight:.3f}")

    print("\n" + "=" * 80)
    print(f"COMPLETE - Generated {len(predictions)} Drug->Disease predictions")
    print("=" * 80)

if __name__ == "__main__":
    main()
