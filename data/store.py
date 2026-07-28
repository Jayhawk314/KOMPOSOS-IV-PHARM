# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""
KOMPOSOS-III Data Store
========================

SQLite-based storage for categorical structures with temporal evolution tracking.

This store is designed for KOMPOSOS-III's core use case:
"Phylogenetics of concepts" - tracing how ideas evolve over time
and when different evolutionary paths are structurally equivalent.

Key Features:
- Objects with metadata and timestamps
- Morphisms with provenance and confidence
- Paths (sequences of morphisms) representing evolution
- Equivalence classes (groups of equivalent objects via HoTT)
- Higher morphisms (2-cells: paths between paths)
- Full temporal indexing for evolution tracking

Schema Design:
- Every entity has created_at and updated_at timestamps
- Morphisms track their source (which corpus, paper, etc.)
- Paths are stored as ordered sequences with provenance
- Equivalence classes support HoTT's univalence principle
"""

from __future__ import annotations
import sqlite3
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field, asdict
from contextlib import contextmanager
import numpy as np


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class StoredObject:
    """
    An object in the categorical store.

    Objects represent concepts, entities, theories, designs, etc.
    They have:
    - name: unique identifier
    - type_name: categorization (e.g., "Theory", "Concept", "Design")
    - metadata: arbitrary key-value data
    - embedding: optional vector representation
    - timestamps: for evolution tracking
    - provenance: where this object came from
    """
    name: str
    type_name: str = "Object"
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[np.ndarray] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    provenance: str = "unknown"

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = self.created_at


@dataclass
class StoredMorphism:
    """
    A morphism in the categorical store.

    Morphisms represent relationships, transformations, influences, etc.
    They have:
    - name: identifier for the morphism type
    - source_name: source object name
    - target_name: target object name
    - metadata: arbitrary data (year, weight, evidence, etc.)
    - confidence: how certain we are (0.0 to 1.0)
    - timestamps: for evolution tracking
    - provenance: source of this relationship
    """
    name: str
    source_name: str
    target_name: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    provenance: str = "unknown"

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = self.created_at

    @property
    def id(self) -> str:
        """Unique identifier for this morphism instance."""
        return f"{self.name}:{self.source_name}->{self.target_name}"


@dataclass
class StoredPath:
    """
    A path (sequence of morphisms) representing evolution.

    Paths are the core concept for KOMPOSOS-III's "phylogenetics of concepts":
    - They trace how A became B through intermediate steps
    - They can be compared for structural equivalence
    - They have temporal ordering

    Example:
        Newton -> Hamilton -> Schrödinger
        [reformulation, wave_mechanics]
    """
    name: str
    morphism_ids: List[str]  # Ordered sequence of morphism IDs
    source_name: str  # Starting object
    target_name: str  # Ending object
    metadata: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    created_at: Optional[datetime] = None
    provenance: str = "computed"

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

    @property
    def id(self) -> str:
        """Unique identifier for this path."""
        return f"path:{self.source_name}->...{len(self.morphism_ids)}...{self.target_name}"

    @property
    def length(self) -> int:
        """Number of morphisms in the path."""
        return len(self.morphism_ids)


@dataclass
class EquivalenceClass:
    """
    An equivalence class grouping structurally equivalent objects.

    Via HoTT's univalence: equivalent things ARE equal.
    This class tracks which objects/paths are equivalent.

    Example:
        wave_mechanics ≃ matrix_mechanics (von Neumann proof, 1932)
    """
    name: str
    member_names: List[str]  # Object or path names in this class
    equivalence_type: str = "structural"  # structural, functional, definitional
    witness: str = "unknown"  # The proof/evidence of equivalence
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    provenance: str = "computed"

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class HigherMorphism:
    """
    A 2-cell: a morphism between morphisms (or path between paths).

    This captures "how two paths are equivalent" - not just THAT they
    are equivalent, but the specific transformation between them.

    Example:
        The path (Newton->Hamilton->Schrödinger) is equivalent to
        (Newton->Hamilton->Heisenberg) via the transformation
        (wave_matrix_equivalence, von Neumann).
    """
    name: str
    source_path_id: str
    target_path_id: str
    transformation_type: str  # e.g., "equivalence", "homotopy", "refinement"
    witness: str = "unknown"
    metadata: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    created_at: Optional[datetime] = None
    provenance: str = "computed"

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


# =============================================================================
# Store Class
# =============================================================================

class KomposOSStore:
    """
    SQLite-based categorical store for KOMPOSOS-III.

    Stores objects, morphisms, paths, equivalence classes, and higher morphisms
    with full temporal tracking for evolution analysis.

    Usage:
        store = KomposOSStore("my_corpus.db")

        # Add objects
        store.add_object(StoredObject("Newton", "Physicist", {"era": "classical"}))
        store.add_object(StoredObject("Hamilton", "Physicist", {"era": "classical"}))

        # Add morphisms
        store.add_morphism(StoredMorphism("influenced", "Newton", "Hamilton", {"year": 1833}))

        # Find paths
        paths = store.find_paths("Newton", "Schrödinger")

        # Track equivalences
        store.add_equivalence(EquivalenceClass("QM_formulations",
            ["wave_mechanics", "matrix_mechanics"], witness="von_neumann"))
    """

    def __init__(self, db_path: Union[str, Path] = ":memory:"):
        """
        Initialize the store.

        Args:
            db_path: Path to SQLite database file, or ":memory:" for in-memory
        """
        self.db_path = Path(db_path) if db_path != ":memory:" else db_path
        self._persistent_conn = None

        # For in-memory databases, we need a persistent connection
        if db_path == ":memory:":
            self._persistent_conn = sqlite3.connect(
                ":memory:",
                detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
            )
            self._persistent_conn.row_factory = sqlite3.Row

        self._init_schema()

    @contextmanager
    def _connection(self):
        """Context manager for database connections."""
        # For in-memory databases, reuse the persistent connection
        if self._persistent_conn is not None:
            yield self._persistent_conn
            self._persistent_conn.commit()
            return

        # For file-based databases, create a new connection each time
        conn = sqlite3.connect(
            str(self.db_path),
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
        )
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_schema(self):
        """Initialize database schema."""
        with self._connection() as conn:
            # Objects table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS objects (
                    name TEXT PRIMARY KEY,
                    type_name TEXT NOT NULL DEFAULT 'Object',
                    metadata TEXT NOT NULL DEFAULT '{}',
                    embedding BLOB,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    provenance TEXT NOT NULL DEFAULT 'unknown'
                )
            """)

            # Morphisms table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS morphisms (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    source_name TEXT NOT NULL,
                    target_name TEXT NOT NULL,
                    metadata TEXT NOT NULL DEFAULT '{}',
                    confidence REAL NOT NULL DEFAULT 1.0,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    provenance TEXT NOT NULL DEFAULT 'unknown',
                    FOREIGN KEY (source_name) REFERENCES objects(name),
                    FOREIGN KEY (target_name) REFERENCES objects(name)
                )
            """)

            # Paths table (stores sequences of morphisms)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS paths (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    morphism_ids TEXT NOT NULL,
                    source_name TEXT NOT NULL,
                    target_name TEXT NOT NULL,
                    length INTEGER NOT NULL,
                    metadata TEXT NOT NULL DEFAULT '{}',
                    confidence REAL NOT NULL DEFAULT 1.0,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    provenance TEXT NOT NULL DEFAULT 'computed',
                    FOREIGN KEY (source_name) REFERENCES objects(name),
                    FOREIGN KEY (target_name) REFERENCES objects(name)
                )
            """)

            # Equivalence classes table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS equivalence_classes (
                    name TEXT PRIMARY KEY,
                    member_names TEXT NOT NULL,
                    equivalence_type TEXT NOT NULL DEFAULT 'structural',
                    witness TEXT NOT NULL DEFAULT 'unknown',
                    confidence REAL NOT NULL DEFAULT 1.0,
                    metadata TEXT NOT NULL DEFAULT '{}',
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    provenance TEXT NOT NULL DEFAULT 'computed'
                )
            """)

            # Higher morphisms table (2-cells: paths between paths)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS higher_morphisms (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    source_path_id TEXT NOT NULL,
                    target_path_id TEXT NOT NULL,
                    transformation_type TEXT NOT NULL,
                    witness TEXT NOT NULL DEFAULT 'unknown',
                    metadata TEXT NOT NULL DEFAULT '{}',
                    confidence REAL NOT NULL DEFAULT 1.0,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    provenance TEXT NOT NULL DEFAULT 'computed',
                    FOREIGN KEY (source_path_id) REFERENCES paths(id),
                    FOREIGN KEY (target_path_id) REFERENCES paths(id)
                )
            """)

            # Indexes for efficient queries
            conn.execute("CREATE INDEX IF NOT EXISTS idx_morphisms_source ON morphisms(source_name)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_morphisms_target ON morphisms(target_name)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_morphisms_name ON morphisms(name)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_objects_type ON objects(type_name)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_objects_created ON objects(created_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_morphisms_created ON morphisms(created_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_paths_source ON paths(source_name)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_paths_target ON paths(target_name)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_paths_length ON paths(length)")

    # =========================================================================
    # Objects
    # =========================================================================

    def add_object(self, obj: StoredObject) -> bool:
        """
        Add or update an object in the store.

        Args:
            obj: The object to store

        Returns:
            True if inserted, False if updated
        """
        with self._connection() as conn:
            # Serialize embedding if present
            embedding_blob = None
            if obj.embedding is not None:
                embedding_blob = obj.embedding.tobytes()

            cursor = conn.execute(
                """
                INSERT INTO objects (name, type_name, metadata, embedding, created_at, updated_at, provenance)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET
                    type_name = excluded.type_name,
                    metadata = excluded.metadata,
                    embedding = excluded.embedding,
                    updated_at = excluded.updated_at,
                    provenance = excluded.provenance
                """,
                (
                    obj.name,
                    obj.type_name,
                    json.dumps(obj.metadata),
                    embedding_blob,
                    obj.created_at,
                    obj.updated_at,
                    obj.provenance
                )
            )
            return cursor.rowcount == 1

    def get_object(self, name: str) -> Optional[StoredObject]:
        """Get an object by name."""
        with self._connection() as conn:
            row = conn.execute(
                "SELECT * FROM objects WHERE name = ?",
                (name,)
            ).fetchone()

            if row is None:
                return None

            embedding = None
            if row['embedding'] is not None:
                embedding = np.frombuffer(row['embedding'], dtype=np.float32)

            return StoredObject(
                name=row['name'],
                type_name=row['type_name'],
                metadata=json.loads(row['metadata']),
                embedding=embedding,
                created_at=row['created_at'],
                updated_at=row['updated_at'],
                provenance=row['provenance']
            )

    def get_objects_by_type(self, type_name: str) -> List[StoredObject]:
        """Get all objects of a given type."""
        with self._connection() as conn:
            rows = conn.execute(
                "SELECT * FROM objects WHERE type_name = ? ORDER BY created_at",
                (type_name,)
            ).fetchall()

            return [self._row_to_object(row) for row in rows]

    def get_objects_in_timerange(
        self,
        start: datetime,
        end: datetime,
        type_name: Optional[str] = None
    ) -> List[StoredObject]:
        """Get objects created within a time range."""
        with self._connection() as conn:
            if type_name:
                rows = conn.execute(
                    """
                    SELECT * FROM objects
                    WHERE created_at BETWEEN ? AND ? AND type_name = ?
                    ORDER BY created_at
                    """,
                    (start, end, type_name)
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT * FROM objects
                    WHERE created_at BETWEEN ? AND ?
                    ORDER BY created_at
                    """,
                    (start, end)
                ).fetchall()

            return [self._row_to_object(row) for row in rows]

    def _row_to_object(self, row: sqlite3.Row) -> StoredObject:
        """Convert a database row to a StoredObject."""
        embedding = None
        if row['embedding'] is not None:
            embedding = np.frombuffer(row['embedding'], dtype=np.float32)

        return StoredObject(
            name=row['name'],
            type_name=row['type_name'],
            metadata=json.loads(row['metadata']),
            embedding=embedding,
            created_at=row['created_at'],
            updated_at=row['updated_at'],
            provenance=row['provenance']
        )

    def list_objects(self, limit: int = 100, offset: int = 0) -> List[StoredObject]:
        """List all objects with pagination."""
        with self._connection() as conn:
            rows = conn.execute(
                "SELECT * FROM objects ORDER BY created_at LIMIT ? OFFSET ?",
                (limit, offset)
            ).fetchall()

            return [self._row_to_object(row) for row in rows]

    def count_objects(self) -> int:
        """Count total number of objects."""
        with self._connection() as conn:
            return conn.execute("SELECT COUNT(*) FROM objects").fetchone()[0]

    def delete_object(self, name: str) -> bool:
        """Delete an object (and its morphisms) by name."""
        with self._connection() as conn:
            # Delete related morphisms first
            conn.execute(
                "DELETE FROM morphisms WHERE source_name = ? OR target_name = ?",
                (name, name)
            )
            cursor = conn.execute("DELETE FROM objects WHERE name = ?", (name,))
            return cursor.rowcount > 0

    # =========================================================================
    # Morphisms
    # =========================================================================

    def add_morphism(self, mor: StoredMorphism) -> bool:
        """
        Add or update a morphism in the store.

        Args:
            mor: The morphism to store

        Returns:
            True if inserted, False if updated
        """
        mor_id = mor.id

        with self._connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO morphisms (id, name, source_name, target_name, metadata,
                                       confidence, created_at, updated_at, provenance)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    metadata = excluded.metadata,
                    confidence = excluded.confidence,
                    updated_at = excluded.updated_at,
                    provenance = excluded.provenance
                """,
                (
                    mor_id,
                    mor.name,
                    mor.source_name,
                    mor.target_name,
                    json.dumps(mor.metadata),
                    mor.confidence,
                    mor.created_at,
                    mor.updated_at,
                    mor.provenance
                )
            )
            return cursor.rowcount == 1

    def get_morphism(self, mor_id: str) -> Optional[StoredMorphism]:
        """Get a morphism by ID."""
        with self._connection() as conn:
            row = conn.execute(
                "SELECT * FROM morphisms WHERE id = ?",
                (mor_id,)
            ).fetchone()

            if row is None:
                return None

            return self._row_to_morphism(row)

    def get_morphisms_from(self, source_name: str) -> List[StoredMorphism]:
        """Get all morphisms from a source object."""
        with self._connection() as conn:
            rows = conn.execute(
                "SELECT * FROM morphisms WHERE source_name = ? ORDER BY created_at",
                (source_name,)
            ).fetchall()

            return [self._row_to_morphism(row) for row in rows]

    def get_morphisms_to(self, target_name: str) -> List[StoredMorphism]:
        """Get all morphisms to a target object."""
        with self._connection() as conn:
            rows = conn.execute(
                "SELECT * FROM morphisms WHERE target_name = ? ORDER BY created_at",
                (target_name,)
            ).fetchall()

            return [self._row_to_morphism(row) for row in rows]

    def get_morphisms_by_name(self, name: str) -> List[StoredMorphism]:
        """Get all morphisms of a given type/name."""
        with self._connection() as conn:
            rows = conn.execute(
                "SELECT * FROM morphisms WHERE name = ? ORDER BY created_at",
                (name,)
            ).fetchall()

            return [self._row_to_morphism(row) for row in rows]

    def _row_to_morphism(self, row: sqlite3.Row) -> StoredMorphism:
        """Convert a database row to a StoredMorphism."""
        return StoredMorphism(
            name=row['name'],
            source_name=row['source_name'],
            target_name=row['target_name'],
            metadata=json.loads(row['metadata']),
            confidence=row['confidence'],
            created_at=row['created_at'],
            updated_at=row['updated_at'],
            provenance=row['provenance']
        )

    def list_morphisms(self, limit: int = 100, offset: int = 0) -> List[StoredMorphism]:
        """List all morphisms with pagination."""
        with self._connection() as conn:
            rows = conn.execute(
                "SELECT * FROM morphisms ORDER BY created_at LIMIT ? OFFSET ?",
                (limit, offset)
            ).fetchall()

            return [self._row_to_morphism(row) for row in rows]

    def count_morphisms(self) -> int:
        """Count total number of morphisms."""
        with self._connection() as conn:
            return conn.execute("SELECT COUNT(*) FROM morphisms").fetchone()[0]

    # =========================================================================
    # Paths (Evolution Tracking)
    # =========================================================================

    def add_path(self, path: StoredPath) -> bool:
        """
        Add a path (sequence of morphisms) to the store.

        Paths represent evolution: how A became B through intermediate steps.
        """
        path_id = path.id

        with self._connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO paths (id, name, morphism_ids, source_name, target_name,
                                   length, metadata, confidence, created_at, provenance)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    metadata = excluded.metadata,
                    confidence = excluded.confidence,
                    provenance = excluded.provenance
                """,
                (
                    path_id,
                    path.name,
                    json.dumps(path.morphism_ids),
                    path.source_name,
                    path.target_name,
                    path.length,
                    json.dumps(path.metadata),
                    path.confidence,
                    path.created_at,
                    path.provenance
                )
            )
            return cursor.rowcount == 1

    def get_path(self, path_id: str) -> Optional[StoredPath]:
        """Get a path by ID."""
        with self._connection() as conn:
            row = conn.execute(
                "SELECT * FROM paths WHERE id = ?",
                (path_id,)
            ).fetchone()

            if row is None:
                return None

            return self._row_to_path(row)

    def find_paths(
        self,
        source_name: str,
        target_name: str,
        max_length: int = 5
    ) -> List[StoredPath]:
        """
        Find all paths from source to target.

        This is the core "evolution tracking" operation:
        "How did A become B?"

        Uses BFS to find all paths up to max_length.
        """
        paths = []

        # BFS to find all paths
        queue = [(source_name, [])]  # (current_node, path_so_far)
        visited_paths = set()

        while queue:
            current, path_so_far = queue.pop(0)

            if current == target_name and path_so_far:
                # Found a path
                path_key = "->".join(path_so_far)
                if path_key not in visited_paths:
                    visited_paths.add(path_key)

                    stored_path = StoredPath(
                        name=f"{source_name}_to_{target_name}",
                        morphism_ids=path_so_far,
                        source_name=source_name,
                        target_name=target_name,
                        confidence=1.0,
                        provenance="computed"
                    )
                    paths.append(stored_path)
                continue

            if len(path_so_far) >= max_length:
                continue

            # Get outgoing morphisms
            morphisms = self.get_morphisms_from(current)
            for mor in morphisms:
                new_path = path_so_far + [mor.id]
                queue.append((mor.target_name, new_path))

        return paths

    def get_paths_from(self, source_name: str) -> List[StoredPath]:
        """Get all stored paths from a source object."""
        with self._connection() as conn:
            rows = conn.execute(
                "SELECT * FROM paths WHERE source_name = ? ORDER BY length",
                (source_name,)
            ).fetchall()

            return [self._row_to_path(row) for row in rows]

    def get_paths_to(self, target_name: str) -> List[StoredPath]:
        """Get all stored paths to a target object."""
        with self._connection() as conn:
            rows = conn.execute(
                "SELECT * FROM paths WHERE target_name = ? ORDER BY length",
                (target_name,)
            ).fetchall()

            return [self._row_to_path(row) for row in rows]

    def _row_to_path(self, row: sqlite3.Row) -> StoredPath:
        """Convert a database row to a StoredPath."""
        return StoredPath(
            name=row['name'],
            morphism_ids=json.loads(row['morphism_ids']),
            source_name=row['source_name'],
            target_name=row['target_name'],
            metadata=json.loads(row['metadata']),
            confidence=row['confidence'],
            created_at=row['created_at'],
            provenance=row['provenance']
        )

    # =========================================================================
    # Equivalence Classes (HoTT Univalence)
    # =========================================================================

    def add_equivalence(self, equiv: EquivalenceClass) -> bool:
        """
        Add an equivalence class to the store.

        Via HoTT's univalence: equivalent things ARE equal.
        """
        with self._connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO equivalence_classes
                    (name, member_names, equivalence_type, witness, confidence, metadata, created_at, provenance)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET
                    member_names = excluded.member_names,
                    witness = excluded.witness,
                    confidence = excluded.confidence,
                    metadata = excluded.metadata,
                    provenance = excluded.provenance
                """,
                (
                    equiv.name,
                    json.dumps(equiv.member_names),
                    equiv.equivalence_type,
                    equiv.witness,
                    equiv.confidence,
                    json.dumps(equiv.metadata),
                    equiv.created_at,
                    equiv.provenance
                )
            )
            return cursor.rowcount == 1

    def get_equivalence(self, name: str) -> Optional[EquivalenceClass]:
        """Get an equivalence class by name."""
        with self._connection() as conn:
            row = conn.execute(
                "SELECT * FROM equivalence_classes WHERE name = ?",
                (name,)
            ).fetchone()

            if row is None:
                return None

            return self._row_to_equivalence(row)

    def find_equivalences_containing(self, member_name: str) -> List[EquivalenceClass]:
        """Find all equivalence classes containing a given member."""
        with self._connection() as conn:
            rows = conn.execute(
                "SELECT * FROM equivalence_classes WHERE member_names LIKE ?",
                (f'%"{member_name}"%',)
            ).fetchall()

            return [self._row_to_equivalence(row) for row in rows]

    def are_equivalent(self, name1: str, name2: str) -> Optional[EquivalenceClass]:
        """
        Check if two objects/paths are equivalent.

        Returns the equivalence class if they are, None otherwise.
        """
        classes1 = self.find_equivalences_containing(name1)
        for equiv in classes1:
            if name2 in equiv.member_names:
                return equiv
        return None

    def _row_to_equivalence(self, row: sqlite3.Row) -> EquivalenceClass:
        """Convert a database row to an EquivalenceClass."""
        return EquivalenceClass(
            name=row['name'],
            member_names=json.loads(row['member_names']),
            equivalence_type=row['equivalence_type'],
            witness=row['witness'],
            confidence=row['confidence'],
            metadata=json.loads(row['metadata']),
            created_at=row['created_at'],
            provenance=row['provenance']
        )

    def list_equivalences(self) -> List[EquivalenceClass]:
        """List all equivalence classes."""
        with self._connection() as conn:
            rows = conn.execute(
                "SELECT * FROM equivalence_classes ORDER BY created_at"
            ).fetchall()

            return [self._row_to_equivalence(row) for row in rows]

    # =========================================================================
    # Higher Morphisms (2-cells)
    # =========================================================================

    def add_higher_morphism(self, hmor: HigherMorphism) -> bool:
        """
        Add a higher morphism (path between paths) to the store.

        This captures HOW two paths are equivalent.
        """
        hmor_id = f"2cell:{hmor.source_path_id}=>{hmor.target_path_id}"

        with self._connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO higher_morphisms
                    (id, name, source_path_id, target_path_id, transformation_type,
                     witness, metadata, confidence, created_at, provenance)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    witness = excluded.witness,
                    metadata = excluded.metadata,
                    confidence = excluded.confidence,
                    provenance = excluded.provenance
                """,
                (
                    hmor_id,
                    hmor.name,
                    hmor.source_path_id,
                    hmor.target_path_id,
                    hmor.transformation_type,
                    hmor.witness,
                    json.dumps(hmor.metadata),
                    hmor.confidence,
                    hmor.created_at,
                    hmor.provenance
                )
            )
            return cursor.rowcount == 1

    def get_higher_morphisms_between(
        self,
        path1_id: str,
        path2_id: str
    ) -> List[HigherMorphism]:
        """Get all 2-cells between two paths."""
        with self._connection() as conn:
            rows = conn.execute(
                """
                SELECT * FROM higher_morphisms
                WHERE (source_path_id = ? AND target_path_id = ?)
                   OR (source_path_id = ? AND target_path_id = ?)
                """,
                (path1_id, path2_id, path2_id, path1_id)
            ).fetchall()

            return [self._row_to_higher_morphism(row) for row in rows]

    def _row_to_higher_morphism(self, row: sqlite3.Row) -> HigherMorphism:
        """Convert a database row to a HigherMorphism."""
        return HigherMorphism(
            name=row['name'],
            source_path_id=row['source_path_id'],
            target_path_id=row['target_path_id'],
            transformation_type=row['transformation_type'],
            witness=row['witness'],
            metadata=json.loads(row['metadata']),
            confidence=row['confidence'],
            created_at=row['created_at'],
            provenance=row['provenance']
        )

    # =========================================================================
    # Bulk Operations
    # =========================================================================

    def bulk_add_objects(self, objects: List[StoredObject]) -> int:
        """Add multiple objects in a single transaction.

        Uses executemany with batching for efficient bulk insertion.
        """
        sql = """
            INSERT OR REPLACE INTO objects
                (name, type_name, metadata, embedding, created_at, updated_at, provenance)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        count = 0
        batch_size = 50_000
        with self._connection() as conn:
            for i in range(0, len(objects), batch_size):
                batch = objects[i:i + batch_size]
                params = [
                    (
                        obj.name, obj.type_name, json.dumps(obj.metadata),
                        obj.embedding.tobytes() if obj.embedding is not None else None,
                        obj.created_at, obj.updated_at, obj.provenance
                    )
                    for obj in batch
                ]
                conn.executemany(sql, params)
                count += len(batch)
        return count

    def bulk_add_morphisms(self, morphisms: List[StoredMorphism]) -> int:
        """Add multiple morphisms in a single transaction.

        Uses executemany with batching for efficient bulk insertion.
        """
        sql = """
            INSERT OR REPLACE INTO morphisms
                (id, name, source_name, target_name, metadata,
                 confidence, created_at, updated_at, provenance)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        count = 0
        batch_size = 50_000
        with self._connection() as conn:
            for i in range(0, len(morphisms), batch_size):
                batch = morphisms[i:i + batch_size]
                params = [
                    (
                        mor.id, mor.name, mor.source_name, mor.target_name,
                        json.dumps(mor.metadata), mor.confidence,
                        mor.created_at, mor.updated_at, mor.provenance
                    )
                    for mor in batch
                ]
                conn.executemany(sql, params)
                count += len(batch)
        return count

    # =========================================================================
    # Statistics and Analysis
    # =========================================================================

    def get_statistics(self) -> Dict[str, Any]:
        """Get store statistics."""
        with self._connection() as conn:
            stats = {
                "objects": conn.execute("SELECT COUNT(*) FROM objects").fetchone()[0],
                "morphisms": conn.execute("SELECT COUNT(*) FROM morphisms").fetchone()[0],
                "paths": conn.execute("SELECT COUNT(*) FROM paths").fetchone()[0],
                "equivalences": conn.execute("SELECT COUNT(*) FROM equivalence_classes").fetchone()[0],
                "higher_morphisms": conn.execute("SELECT COUNT(*) FROM higher_morphisms").fetchone()[0],
            }

            # Object types distribution
            type_rows = conn.execute(
                "SELECT type_name, COUNT(*) as count FROM objects GROUP BY type_name"
            ).fetchall()
            stats["object_types"] = {row['type_name']: row['count'] for row in type_rows}

            # Morphism types distribution
            mor_rows = conn.execute(
                "SELECT name, COUNT(*) as count FROM morphisms GROUP BY name"
            ).fetchall()
            stats["morphism_types"] = {row['name']: row['count'] for row in mor_rows}

            return stats

    def export_to_networkx(self):
        """
        Export the store to a NetworkX graph for analysis.

        Returns:
            networkx.DiGraph with objects as nodes and morphisms as edges
        """
        try:
            import networkx as nx
        except ImportError:
            raise ImportError("networkx required: pip install networkx")

        G = nx.DiGraph()

        # Add nodes (objects)
        for obj in self.list_objects(limit=100000):
            G.add_node(obj.name, **{
                "type": obj.type_name,
                "created_at": str(obj.created_at),
                **obj.metadata
            })

        # Add edges (morphisms)
        for mor in self.list_morphisms(limit=100000):
            G.add_edge(mor.source_name, mor.target_name, **{
                "name": mor.name,
                "confidence": mor.confidence,
                "created_at": str(mor.created_at),
                **mor.metadata
            })

        return G


# =============================================================================
# Factory Functions
# =============================================================================

def create_store(db_path: Union[str, Path] = None) -> KomposOSStore:
    """
    Create a new KOMPOSOS-III store.

    Args:
        db_path: Path to database file. If None, uses default location.

    Returns:
        KomposOSStore instance
    """
    if db_path is None:
        db_path = Path.home() / ".komposos3" / "store.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)

    return KomposOSStore(db_path)


def create_memory_store() -> KomposOSStore:
    """Create an in-memory store (for testing or ephemeral use)."""
    return KomposOSStore(":memory:")


# =============================================================================
# Demo
# =============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("KOMPOSOS-III Data Store Demo")
    print("=" * 70)

    # Create in-memory store
    store = create_memory_store()

    # Add some objects (physicists/theories)
    print("\n[1] Adding objects...")
    objects = [
        StoredObject("Newton", "Physicist", {"era": "classical", "birth": 1643}),
        StoredObject("Hamilton", "Physicist", {"era": "classical", "birth": 1805}),
        StoredObject("Schrödinger", "Physicist", {"era": "quantum", "birth": 1887}),
        StoredObject("Heisenberg", "Physicist", {"era": "quantum", "birth": 1901}),
        StoredObject("Dirac", "Physicist", {"era": "quantum", "birth": 1902}),
    ]
    store.bulk_add_objects(objects)
    print(f"  Added {len(objects)} objects")

    # Add morphisms (influences/transformations)
    print("\n[2] Adding morphisms...")
    morphisms = [
        StoredMorphism("influenced", "Newton", "Hamilton", {"year": 1833}, confidence=0.95),
        StoredMorphism("wave_mechanics", "Hamilton", "Schrödinger", {"year": 1926}),
        StoredMorphism("matrix_mechanics", "Hamilton", "Heisenberg", {"year": 1925}),
        StoredMorphism("unified", "Schrödinger", "Dirac", {"year": 1928}),
        StoredMorphism("unified", "Heisenberg", "Dirac", {"year": 1928}),
    ]
    store.bulk_add_morphisms(morphisms)
    print(f"  Added {len(morphisms)} morphisms")

    # Find paths
    print("\n[3] Finding paths from Newton to Dirac...")
    paths = store.find_paths("Newton", "Dirac")
    for i, path in enumerate(paths):
        print(f"  Path {i+1}: {path.source_name} -> ... ({path.length} steps) -> {path.target_name}")
        print(f"           Morphisms: {path.morphism_ids}")

    # Add equivalence
    print("\n[4] Adding equivalence class...")
    equiv = EquivalenceClass(
        "QM_formulations",
        ["wave_mechanics", "matrix_mechanics"],
        equivalence_type="mathematical",
        witness="von_neumann_1932",
        metadata={"proof_year": 1932}
    )
    store.add_equivalence(equiv)

    # Check equivalence
    result = store.are_equivalent("wave_mechanics", "matrix_mechanics")
    print(f"  wave_mechanics ≃ matrix_mechanics: {result is not None}")
    if result:
        print(f"  Witness: {result.witness}")

    # Statistics
    print("\n[5] Store statistics:")
    stats = store.get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    print("\n" + "=" * 70)
    print("Demo complete!")
