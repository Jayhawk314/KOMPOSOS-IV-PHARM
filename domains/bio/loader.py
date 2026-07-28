# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""
BioDomainLoader - Load KOMPOSOS-III biological data into KOMPOSOS-IV Category

This loader bridges the KomposOSStore (flat SQLite) used in Bio with the
enriched Category system used in PHARM. It loads every object row before
loading morphisms so endpoint types are preserved. For historical AUROC
reproduction, use validation/repurposing_benchmark.py --view legacy.
"""

import sys
from pathlib import Path
from typing import Any, Dict, Optional
import numpy as np

# Import from Bio's data layer
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from data.store import KomposOSStore

# Import from PHARM's core
from core.category import Category


class BioDomainLoader:
    """Load KOMPOSOS-III bio data into KOMPOSOS-IV Category."""

    def __init__(self):
        self.store: Optional[KomposOSStore] = None
        self.category: Optional[Category] = None
        self.loaded_count: Dict[str, int] = {"objects": 0, "morphisms": 0}

    def load_tier1(self, tier1_db_path: str, category: Optional[Category] = None) -> Category:
        """
        Load tier1.db into Category.

        Args:
            tier1_db_path: Path to tier1.db (e.g., "data/drugs/tier1.db")
            category: Existing Category to load into, or None to create new one

        Returns:
            Category with all tier1 object rows and morphisms loaded

        Example:
            >>> loader = BioDomainLoader()
            >>> cat = loader.load_tier1("data/drugs/tier1.db")
            >>> print(f"Loaded {len(cat.objects())} objects")
        """
        self.loaded_count = {"objects": 0, "morphisms": 0}

        # Open store
        self.store = KomposOSStore(tier1_db_path)

        # Create or use existing category
        if category is None:
            category = Category(name="BioTier1")
        self.category = category

        # Load objects first
        self._load_objects()

        # Then load morphisms
        self._load_morphisms()

        print(f"[BioDomainLoader] Loaded {self.loaded_count['objects']} objects, "
              f"{self.loaded_count['morphisms']} morphisms from tier1.db")

        return category

    def _load_objects(self):
        """Load all objects from store into category."""
        object_count = self.store.count_objects()
        objects = self.store.list_objects(limit=object_count)

        for obj in objects:
            # Convert StoredObject to Category object
            # Category.add(name, type_name=None, metadata=None, embedding=None)
            self.category.add(
                obj.name,
                type_name=obj.type_name,
                metadata=obj.metadata if obj.metadata else {},
                embedding=self._deserialize_embedding(obj.embedding)
            )
            self.loaded_count["objects"] += 1

    def _load_morphisms(self):
        """Load all morphisms from store into category."""
        morphism_count = self.store.count_morphisms()
        morphisms = self.store.list_morphisms(limit=morphism_count)

        for mor in morphisms:
            # Convert StoredMorphism to Category morphism
            # Category.connect(source, target, name=None, confidence=1.0, **metadata)
            # Filter out keys that collide with connect() positional/keyword args.
            meta = mor.metadata if mor.metadata else {}
            safe_meta = {k: v for k, v in meta.items()
                         if k not in ("source", "target", "name", "confidence")}
            self.category.connect(
                mor.source_name,
                mor.target_name,
                name=mor.name,
                confidence=mor.confidence if mor.confidence else 1.0,
                **safe_meta
            )
            self.loaded_count["morphisms"] += 1

    def _deserialize_embedding(self, embedding_blob: Optional[bytes]) -> Optional[np.ndarray]:
        """
        Deserialize embedding from SQLite blob.

        KomposOSStore stores embeddings as pickled numpy arrays.
        """
        if embedding_blob is None:
            return None

        try:
            import pickle
            embedding = pickle.loads(embedding_blob)
            if isinstance(embedding, np.ndarray):
                return embedding
            elif isinstance(embedding, list):
                return np.array(embedding)
            else:
                return None
        except Exception as e:
            print(f"[BioDomainLoader] Warning: Failed to deserialize embedding: {e}")
            return None

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about loaded data."""
        if self.category is None:
            return {"status": "not_loaded"}

        # Get type distribution
        type_dist = {}
        for obj in self.category.objects():
            obj_type = obj.type_name if hasattr(obj, 'type_name') else "Unknown"
            type_dist[obj_type] = type_dist.get(obj_type, 0) + 1

        return {
            "status": "loaded",
            "objects_loaded": self.loaded_count["objects"],
            "morphisms_loaded": self.loaded_count["morphisms"],
            "type_distribution": type_dist,
            "category_name": self.category.name if hasattr(self.category, 'name') else "N/A"
        }


# Convenience function
def load_bio_domain(tier1_db_path: str = "data/drugs/tier1.db") -> Category:
    """
    Quick loader for tier1.db.

    Example:
        >>> from domains.bio import load_bio_domain
        >>> cat = load_bio_domain()
        >>> # Now run PHARM's 22 strategies on bio data
    """
    loader = BioDomainLoader()
    return loader.load_tier1(tier1_db_path)
