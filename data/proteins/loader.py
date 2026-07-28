# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""
Load cancer protein network into KOMPOSOS-III store
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from data import KomposOSStore, StoredObject, StoredMorphism
from data.proteins.cancer_proteins import get_protein_network

def create_protein_store(db_path: str = "data/proteins/cancer_proteins.db"):
    """
    Create a KomposOSStore with cancer protein network.

    Returns:
        KomposOSStore instance
    """
    print(f"Creating protein store at: {db_path}")

    store = KomposOSStore(db_path)

    proteins, interactions = get_protein_network()

    # Add proteins as objects
    print(f"Adding {len(proteins)} proteins...")
    for name, data in proteins.items():
        obj = StoredObject(
            name=name,
            type_name=data["type"],
            metadata={
                "function": data["function"],
                "pathways": data["pathways"],
                "cancers": data["cancers"],
                "domain": "protein",
            }
        )
        store.add_object(obj)

    # Add interactions as morphisms
    print(f"Adding {len(interactions)} interactions...")
    for source, target, relation, confidence, evidence in interactions:
        mor = StoredMorphism(
            source_name=source,
            target_name=target,
            name=relation,
            confidence=confidence,
            metadata={
                "evidence": evidence,
                "domain": "protein",
            }
        )
        store.add_morphism(mor)

    print(f"[OK] Protein store created successfully")
    print(f"  Objects: {len(store.list_objects(limit=1000))}")
    print(f"  Morphisms: {len(store.list_morphisms(limit=1000))}")

    return store

if __name__ == "__main__":
    store = create_protein_store()

    # Print sample
    print("\nSample proteins:")
    for obj in store.list_objects(limit=5):
        print(f"  - {obj.name} ({obj.type_name}): {obj.metadata.get('function', 'N/A')}")

    print("\nSample interactions:")
    for mor in store.list_morphisms(limit=5):
        print(f"  - {mor.source_name} --[{mor.name}]--> {mor.target_name} (conf={mor.confidence:.2f})")
