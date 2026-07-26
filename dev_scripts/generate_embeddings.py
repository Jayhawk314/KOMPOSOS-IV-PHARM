#!/usr/bin/env python3
"""
Generate embeddings for tier1.db objects using sentence-transformers.
This is required for the oracle to work.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

print("Generating embeddings for tier1.db objects...")

# Import store and embeddings
from data.store import KomposOSStore
from data.embeddings import EmbeddingsEngine

# Load tier1.db
print("\n[1] Loading tier1.db...")
store = KomposOSStore("data/drugs/tier1.db")
objects = store.list_objects()
print(f"  Found {len(objects)} objects")

# Initialize embeddings engine
print("\n[2] Initializing embeddings engine...")
try:
    embeddings = EmbeddingsEngine(model_name="all-mpnet-base-v2")
    print(f"  Engine initialized: {embeddings.model_name}")
except Exception as e:
    print(f"  [FAIL] Could not initialize embeddings: {e}")
    print("  Install: pip install sentence-transformers")
    sys.exit(1)

# Generate embeddings for each object
print("\n[3] Generating embeddings...")
updated = 0
skipped = 0

for i, obj in enumerate(objects, 1):
    if obj.embedding is not None:
        skipped += 1
        continue

    # Create text representation
    text = f"{obj.name}"
    if obj.metadata:
        desc = obj.metadata.get('description', '')
        if desc:
            text = f"{obj.name}: {desc}"

    # Generate embedding
    try:
        emb = embeddings.embed_text(text)
        obj.embedding = emb
        store.update_object_embedding(obj.name, emb)
        updated += 1

        if i % 10 == 0:
            print(f"  Progress: {i}/{len(objects)} objects processed...")
    except Exception as e:
        print(f"  Warning: Failed to embed {obj.name}: {e}")

print(f"\n[4] Complete!")
print(f"  Updated: {updated} objects")
print(f"  Skipped: {skipped} objects (already had embeddings)")
print(f"  Total: {len(objects)} objects")

print("\n[5] Verifying...")
objects_check = store.list_objects()
with_emb = sum(1 for o in objects_check if o.embedding is not None)
print(f"  Objects with embeddings: {with_emb}/{len(objects_check)}")

if with_emb == len(objects_check):
    print("\n✓ SUCCESS - All objects now have embeddings")
    print("  The oracle can now run!")
else:
    print(f"\n⚠ WARNING - {len(objects_check) - with_emb} objects still missing embeddings")
