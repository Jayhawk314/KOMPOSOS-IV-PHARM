#!/usr/bin/env python3
"""
ACTUAL WORKING TEST - 22 Strategies on Bio Data

This runs PHARM's full oracle on tier1.db and produces real predictions.
"""

import sys
import asyncio
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from domains.bio import BioDomainLoader
from core.category import Category
from oracle.engine import OracleEngine

async def main():
    print("=" * 80)
    print("RUNNING 22 STRATEGIES ON BIO DATA")
    print("=" * 80)

    # Step 1: Load tier1.db into Category
    print("\n[Step 1] Loading tier1.db...")
    loader = BioDomainLoader()
    cat = Category(name="BioTier1", db_path="bio_tier1.db")
    loader.load_tier1("data/drugs/tier1.db", cat)
    stats = loader.get_stats()
    print(f"  Loaded: {stats['objects_loaded']} objects, {stats['morphisms_loaded']} morphisms")

    # Step 2: Initialize Oracle with 22 strategies
    print("\n[Step 2] Initializing Oracle with 22 strategies...")
    oracle = OracleEngine(cat)
    strategies = oracle.list_strategies()
    print(f"  Available strategies: {len(strategies)}")
    for i, s in enumerate(strategies[:22], 1):
        print(f"    {i:2d}. {s}")

    # Step 3: Generate Drug->Disease predictions
    print("\n[Step 3] Generating Drug->Disease predictions...")

    # Get all Drug and Disease objects
    drugs = [obj for obj in cat.objects() if obj.type_name == "Drug"]
    diseases = [obj for obj in cat.objects() if obj.type_name == "Disease"]

    print(f"  Found {len(drugs)} drugs, {len(diseases)} diseases")

    if len(drugs) == 0 or len(diseases) == 0:
        print("  No Drug or Disease objects found. Trying any object types...")
        all_types = {}
        for obj in cat.objects():
            all_types[obj.type_name] = all_types.get(obj.type_name, 0) + 1
        print(f"  Available types: {all_types}")

        # Use most common types as source/target
        sorted_types = sorted(all_types.items(), key=lambda x: -x[1])
        source_type = sorted_types[0][0] if len(sorted_types) > 0 else "Object"
        target_type = sorted_types[1][0] if len(sorted_types) > 1 else source_type

        sources = [obj for obj in cat.objects() if obj.type_name == source_type][:10]
        targets = [obj for obj in cat.objects() if obj.type_name == target_type][:10]

        print(f"  Using {source_type} -> {target_type}")
    else:
        sources = drugs[:5]
        targets = diseases[:5]

    predictions = []
    for source in sources:
        for target in targets:
            # Check if edge already exists
            if cat.hom(source.name, target.name) is not None:
                continue

            # Run all strategies
            score = await oracle.score_edge(source.name, target.name)
            if score > 0.5:
                predictions.append({
                    'source': source.name,
                    'target': target.name,
                    'score': score,
                    'strategies': oracle.last_strategy_votes
                })

    print(f"\n  Generated {len(predictions)} predictions (score > 0.5)")

    # Show top 10
    predictions.sort(key=lambda x: -x['score'])
    print("\n[Step 4] Top 10 Predictions:")
    for i, pred in enumerate(predictions[:10], 1):
        src = pred['source']
        tgt = pred['target']
        score = pred['score']
        n_strat = len(pred.get('strategies', []))
        print(f"  {i:2d}. {src:20s} -> {tgt:20s} (score: {score:.3f}, {n_strat} strategies)")

    # Step 5: Compute paths for top prediction
    if len(predictions) > 0:
        print("\n[Step 5] Finding compositional paths for top prediction...")
        top = predictions[0]
        paths = cat.find_paths(top['source'], top['target'], max_length=3)
        print(f"  Found {len(paths)} paths from {top['source']} to {top['target']}")
        for i, path in enumerate(paths[:3], 1):
            print(f"    Path {i}: {' -> '.join([top['source']] + [cat.get_morphism(mid).target for mid in path.morphism_ids])}")
            print(f"            Weight: {path.weight:.3f}")

    print("\n" + "=" * 80)
    print("COMPLETE - 22 strategies running on Bio data")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())
