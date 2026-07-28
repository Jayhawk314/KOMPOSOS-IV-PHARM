# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""
Adapter to make Category work with old validation scripts that expect KomposOSStore API.
"""
from core.category import Category
from core.types import Object, Morphism


class MorphismAdapter:
    """Wraps IV Morphism to add old API attributes."""
    def __init__(self, morphism: Morphism):
        self._morphism = morphism
        # Add old attribute names
        self.source_name = morphism.source
        self.target_name = morphism.target
        self.name = morphism.name
        self.confidence = morphism.confidence
        self.metadata = getattr(morphism, 'metadata', {})

    def __getattr__(self, name):
        return getattr(self._morphism, name)


class ObjectAdapter:
    """Wraps IV Object to add old API attributes."""
    def __init__(self, obj: Object):
        self._obj = obj
        self.name = obj.name
        self.type_name = obj.type_name
        self.metadata = getattr(obj, 'metadata', {})
        self.embedding = getattr(obj, 'embedding', None)

    def __getattr__(self, name):
        return getattr(self._obj, name)


class StoreAdapter:
    """Wraps Category to provide KomposOSStore-like API for legacy validation scripts."""

    def __init__(self, category: Category):
        self.category = category

    def count_objects(self):
        """Count total objects."""
        return len(self.category.objects())

    def count_morphisms(self):
        """Count total morphisms."""
        return len(self.category.morphisms())

    def list_objects(self, limit=None):
        """List all objects (returns Object instances with old API)."""
        objs = list(self.category.objects())
        if limit:
            objs = objs[:limit]
        return [ObjectAdapter(obj) for obj in objs]

    def list_morphisms(self, limit=None):
        """List all morphisms (returns Morphism instances with old API)."""
        mors = list(self.category.morphisms())
        if limit:
            mors = mors[:limit]
        return [MorphismAdapter(mor) for mor in mors]

    def get_objects_by_type(self, type_name: str):
        """Get all objects of a given type."""
        return [ObjectAdapter(obj) for obj in self.category.objects() if obj.type_name == type_name]

    def get_morphisms_by_name(self, name: str):
        """Get all morphisms with a given name."""
        return [MorphismAdapter(mor) for mor in self.category.morphisms() if mor.name == name]

    def find_paths(self, source: str, target: str, max_length: int = 5):
        """Find paths between objects."""
        return self.category.find_paths(source, target, max_length=max_length)

    def optimal_path(self, source: str, target: str):
        """Find optimal path between objects."""
        return self.category.optimal_path(source, target)

    def get(self, name: str):
        """Get object by name."""
        return self.category.get(name)

    def morphisms_from(self, source: str):
        """Get morphisms from source."""
        return self.category.morphisms_from(source)

    def morphisms_to(self, target: str):
        """Get morphisms to target."""
        return self.category.morphisms_to(target)

    def objects(self):
        """Get all objects."""
        return self.category.objects()

    def morphisms(self):
        """Get all morphisms."""
        return self.category.morphisms()
