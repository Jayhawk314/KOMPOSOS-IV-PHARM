# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""
Load large-scale STRING cancer protein dataset into KomposOSStore.
"""

import sys
from pathlib import Path
import json

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from data import KomposOSStore, StoredObject, StoredMorphism

def load_string_dataset(json_file: str = "string_cancer_large.json",
                       db_path: str = "string_cancer.db") -> KomposOSStore:
    """
    Load STRING dataset into KomposOSStore.

    Args:
        json_file: Path to STRING JSON dataset
        db_path: Output database path

    Returns:
        Populated KomposOSStore
    """
    print("=" * 80)
    print("STRING Cancer Dataset Loader")
    print("=" * 80)
    print()

    # Load JSON
    print(f"[1/4] Loading dataset from {json_file}...")
    with open(json_file, 'r') as f:
        dataset = json.load(f)

    proteins = dataset['proteins']
    interactions = dataset['interactions']

    print(f"  Proteins: {len(proteins)}")
    print(f"  Interactions: {len(interactions)}")
    print()

    # Create store
    print(f"[2/4] Creating KomposOSStore at {db_path}...")
    store = KomposOSStore(db_path)
    print("  [OK] Store created")
    print()

    # Add proteins as objects
    print(f"[3/4] Adding {len(proteins)} proteins...")
    added_count = 0
    failed = []

    for name, data in proteins.items():
        obj = StoredObject(
            name=name,
            type_name=data.get('type', 'Protein'),
            metadata={
                'pathways': data.get('pathways', ['unknown']),
                'source': data.get('source', 'STRING'),
                'description': f"{name} protein from STRING database"
            }
        )

        try:
            success = store.add_object(obj)
            if success:
                added_count += 1
            else:
                failed.append(name)

            if added_count % 50 == 0:
                print(f"  Progress: {added_count}/{len(proteins)}")

        except Exception as e:
            failed.append(f"{name}: {str(e)[:50]}")

    print(f"  [OK] Added {added_count} proteins")
    if failed:
        print(f"  [Warning] Failed: {len(failed)} proteins")
        if len(failed) <= 5:
            for f in failed:
                print(f"    - {f}")
    print()

    # Add interactions as morphisms
    print(f"[4/4] Adding {len(interactions)} interactions...")
    added_interactions = 0
    skipped = 0

    for interaction in interactions:
        source = interaction['source']
        target = interaction['target']
        confidence = interaction['confidence']

        # Infer relation type from protein types
        source_obj = store.get_object(source)
        target_obj = store.get_object(target)

        if not source_obj or not target_obj:
            skipped += 1
            continue

        # Default relation
        relation = "interacts_with"

        # Type-specific relations
        source_type = source_obj.type_name
        target_type = target_obj.type_name

        if source_type == "Oncogene" and target_type == "Oncogene":
            relation = "activates"
        elif source_type == "TumorSuppressor":
            relation = "inhibits"
        elif "Kinase" in source_type or "kinase" in source.lower():
            relation = "phosphorylates"
        elif "Receptor" in source_type:
            relation = "activates"

        morphism = StoredMorphism(
            name=relation,
            source_name=source,
            target_name=target,
            confidence=confidence,
            metadata={
                'source_db': 'STRING',
                'evidence_type': 'functional',
                'original_score': confidence
            }
        )

        try:
            success = store.add_morphism(morphism)
            if success:
                added_interactions += 1

            if added_interactions % 500 == 0:
                print(f"  Progress: {added_interactions}/{len(interactions)}")

        except Exception as e:
            if "UNIQUE constraint" not in str(e):
                # Only print non-duplicate errors
                pass
            skipped += 1

    print(f"  [OK] Added {added_interactions} interactions")
    if skipped > 0:
        print(f"  [Info] Skipped {skipped} duplicates/invalid")
    print()

    # Summary
    print("=" * 80)
    print("Dataset Loading Complete")
    print("=" * 80)
    print()

    final_objects = store.list_objects(limit=10000)
    final_morphisms = store.list_morphisms(limit=20000)

    print(f"Final counts:")
    print(f"  Objects: {len(final_objects)}")
    print(f"  Morphisms: {len(final_morphisms)}")
    print()

    # Show sample
    print("Sample proteins:")
    for obj in final_objects[:5]:
        pathways = obj.metadata.get('pathways', ['unknown'])[:2]
        print(f"  {obj.name:10s} ({obj.type_name:15s}) - {', '.join(pathways)}")
    print()

    print("Sample interactions:")
    for morph in final_morphisms[:5]:
        print(f"  {morph.source_name:10s} --[{morph.name}]--> {morph.target_name:10s} (conf={morph.confidence:.3f})")
    print()

    print("=" * 80)
    return store


if __name__ == "__main__":
    store = load_string_dataset()
    print("Store ready for conjecture generation!")
