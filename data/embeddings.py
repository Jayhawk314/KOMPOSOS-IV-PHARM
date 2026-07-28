# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""
KOMPOSOS-IV Embeddings Module
===============================

Semantic embeddings for categorical structures using Sentence Transformers.

This module provides high-quality vector representations for concepts,
enabling semantic similarity computation, nearest-neighbor search,
and gap detection in the categorical structure.

Model: all-mpnet-base-v2 (768 dimensions)
- Best quality sentence embeddings available
- Excellent for semantic similarity and cross-domain bridge detection
- Trained on 1B+ sentence pairs from diverse sources

Key Features:
- Sentence Transformers for phrase/sentence understanding
- SQLite caching for fast repeated lookups
- Batch embedding for efficiency
- Integration with the Category runtime

The embeddings enable:
1. Semantic similarity between concepts
2. Finding related concepts (nearest neighbors)
3. Detecting semantic gaps (low-similarity regions)
4. Cross-domain analogy detection
"""

from __future__ import annotations
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
import numpy as np
from dataclasses import dataclass


# Default model and cache directory
DEFAULT_MODEL = 'all-mpnet-base-v2'
CACHE_DIR = Path.home() / ".komposos4" / "embeddings_cache"


@dataclass
class EmbeddingResult:
    """Result of embedding a text."""
    text: str
    vector: np.ndarray
    model: str
    cached: bool = False

    @property
    def dimension(self) -> int:
        return len(self.vector)

    def similarity(self, other: 'EmbeddingResult') -> float:
        """Compute cosine similarity with another embedding."""
        norm1 = np.linalg.norm(self.vector)
        norm2 = np.linalg.norm(other.vector)
        if norm1 > 0 and norm2 > 0:
            return float(np.dot(self.vector, other.vector) / (norm1 * norm2))
        return 0.0


class EmbeddingsEngine:
    """
    High-quality embeddings engine for KOMPOSOS-IV.

    Uses Sentence Transformers (all-mpnet-base-v2 by default) for
    semantic embeddings of concepts, relationships, and paths.

    Features:
    - SQLite caching for fast repeated lookups
    - In-memory cache for even faster access
    - Batch embedding for efficiency
    - Similarity computation
    - Nearest neighbor search

    Usage:
        engine = EmbeddingsEngine()

        # Embed a concept
        vec = engine.embed("quantum mechanics")

        # Compare concepts
        sim = engine.similarity("wave function", "probability amplitude")

        # Find similar concepts
        neighbors = engine.find_similar("entanglement", candidates)
    """

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL,
        cache_path: Optional[Path] = None,
        device: str = None
    ):
        """
        Initialize the embeddings engine.

        Args:
            model_name: Sentence Transformer model name
            cache_path: Path to SQLite cache file
            device: Device to run model on ('cpu', 'cuda', etc.)
        """
        self.model_name = model_name
        self.cache_path = cache_path or (CACHE_DIR / "cache.db")
        self.device = device

        self._model = None
        self._dimension = None
        self._memory_cache: Dict[str, np.ndarray] = {}
        self._db_initialized = False

        # Initialize model
        self._init_model()
        self._init_cache_db()

    def _init_model(self):
        """Initialize the Sentence Transformer model."""
        try:
            from sentence_transformers import SentenceTransformer

            kwargs = {}
            if self.device:
                kwargs['device'] = self.device

            self._model = SentenceTransformer(self.model_name, **kwargs)
            self._dimension = self._model.get_sentence_embedding_dimension()

            print(f"[EmbeddingsEngine] Loaded: {self.model_name} ({self._dimension}d)")

        except ImportError:
            print("[EmbeddingsEngine] WARNING: sentence-transformers not installed")
            print("  Install with: pip install sentence-transformers")
            self._model = None
            self._dimension = 768  # Default dimension

        except Exception as e:
            print(f"[EmbeddingsEngine] ERROR loading model: {e}")
            self._model = None
            self._dimension = 768

    def _init_cache_db(self):
        """Initialize SQLite cache database."""
        if self._db_initialized:
            return

        try:
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)

            conn = sqlite3.connect(str(self.cache_path))
            conn.execute("""
                CREATE TABLE IF NOT EXISTS embeddings (
                    text TEXT NOT NULL,
                    model TEXT NOT NULL,
                    vector BLOB NOT NULL,
                    dimension INTEGER NOT NULL,
                    PRIMARY KEY (text, model)
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_embeddings_text
                ON embeddings(text)
            """)
            conn.commit()
            conn.close()

            self._db_initialized = True

        except Exception as e:
            print(f"[EmbeddingsEngine] Cache DB init failed: {e}")

    @property
    def dimension(self) -> int:
        """Get the embedding dimension."""
        return self._dimension

    @property
    def is_available(self) -> bool:
        """Check if the model is available."""
        return self._model is not None

    # =========================================================================
    # Core Embedding Operations
    # =========================================================================

    def embed(self, text: str, use_cache: bool = True) -> np.ndarray:
        """
        Embed a single text.

        Args:
            text: Text to embed (word, phrase, sentence, or paragraph)
            use_cache: Whether to use caching

        Returns:
            Embedding vector (numpy array)
        """
        text_normalized = text.lower().strip()

        # Check memory cache
        if use_cache and text_normalized in self._memory_cache:
            return self._memory_cache[text_normalized]

        # Check SQLite cache
        if use_cache:
            cached = self._get_cached(text_normalized)
            if cached is not None:
                self._memory_cache[text_normalized] = cached
                return cached

        # Compute embedding
        if self._model is None:
            # Fallback: return random vector (for testing without model)
            vec = np.random.randn(self._dimension).astype(np.float32)
            vec = vec / np.linalg.norm(vec)
        else:
            vec = self._model.encode(text, convert_to_numpy=True)
            vec = vec.astype(np.float32)

        # Cache the result
        if use_cache:
            self._memory_cache[text_normalized] = vec
            self._set_cached(text_normalized, vec)

        return vec

    def embed_batch(
        self,
        texts: List[str],
        use_cache: bool = True,
        show_progress: bool = False
    ) -> List[np.ndarray]:
        """
        Embed multiple texts efficiently.

        Args:
            texts: List of texts to embed
            use_cache: Whether to use caching
            show_progress: Show progress bar

        Returns:
            List of embedding vectors
        """
        texts_normalized = [t.lower().strip() for t in texts]
        results = [None] * len(texts)
        to_embed = []
        to_embed_indices = []

        # Check caches first
        for i, text in enumerate(texts_normalized):
            if use_cache:
                # Memory cache
                if text in self._memory_cache:
                    results[i] = self._memory_cache[text]
                    continue

                # SQLite cache
                cached = self._get_cached(text)
                if cached is not None:
                    self._memory_cache[text] = cached
                    results[i] = cached
                    continue

            to_embed.append(text)
            to_embed_indices.append(i)

        # Batch embed remaining texts
        if to_embed and self._model is not None:
            kwargs = {'convert_to_numpy': True}
            if show_progress:
                kwargs['show_progress_bar'] = True

            embeddings = self._model.encode(to_embed, **kwargs)

            for j, idx in enumerate(to_embed_indices):
                vec = embeddings[j].astype(np.float32)
                results[idx] = vec

                if use_cache:
                    text = texts_normalized[idx]
                    self._memory_cache[text] = vec
                    self._set_cached(text, vec)

        elif to_embed:
            # Fallback for missing model
            for idx in to_embed_indices:
                vec = np.random.randn(self._dimension).astype(np.float32)
                vec = vec / np.linalg.norm(vec)
                results[idx] = vec

        return results

    def embed_with_result(self, text: str) -> EmbeddingResult:
        """
        Embed text and return detailed result.

        Args:
            text: Text to embed

        Returns:
            EmbeddingResult with vector and metadata
        """
        text_normalized = text.lower().strip()
        cached = text_normalized in self._memory_cache

        if not cached:
            cached_db = self._get_cached(text_normalized)
            if cached_db is not None:
                cached = True

        vec = self.embed(text)

        return EmbeddingResult(
            text=text,
            vector=vec,
            model=self.model_name,
            cached=cached
        )

    # =========================================================================
    # Similarity Operations
    # =========================================================================

    def similarity(self, text1: str, text2: str) -> float:
        """
        Compute cosine similarity between two texts.

        Args:
            text1: First text
            text2: Second text

        Returns:
            Cosine similarity in range [-1, 1]
        """
        v1 = self.embed(text1)
        v2 = self.embed(text2)
        return self._cosine_similarity(v1, v2)

    def similarity_matrix(self, texts: List[str]) -> np.ndarray:
        """
        Compute pairwise similarity matrix for a list of texts.

        Args:
            texts: List of texts

        Returns:
            NxN similarity matrix
        """
        embeddings = self.embed_batch(texts)
        n = len(texts)
        matrix = np.zeros((n, n))

        for i in range(n):
            for j in range(i, n):
                sim = self._cosine_similarity(embeddings[i], embeddings[j])
                matrix[i, j] = sim
                matrix[j, i] = sim

        return matrix

    def find_similar(
        self,
        query: str,
        candidates: List[str],
        top_k: int = 10,
        threshold: float = 0.0
    ) -> List[Tuple[str, float]]:
        """
        Find most similar texts from candidates.

        Args:
            query: Query text
            candidates: List of candidate texts
            top_k: Number of results to return
            threshold: Minimum similarity threshold

        Returns:
            List of (text, similarity) tuples, sorted by similarity
        """
        query_vec = self.embed(query)
        candidate_vecs = self.embed_batch(candidates)

        scores = []
        for i, (text, vec) in enumerate(zip(candidates, candidate_vecs)):
            sim = self._cosine_similarity(query_vec, vec)
            if sim >= threshold:
                scores.append((text, sim))

        # Sort by similarity descending
        scores.sort(key=lambda x: x[1], reverse=True)

        return scores[:top_k]

    def find_analogies(
        self,
        a: str,
        b: str,
        c: str,
        candidates: List[str],
        top_k: int = 5
    ) -> List[Tuple[str, float]]:
        """
        Find analogical completions: a is to b as c is to ?

        Uses vector arithmetic: vec(?) ~ vec(b) - vec(a) + vec(c)

        Args:
            a, b, c: Analogy terms
            candidates: Candidate completions
            top_k: Number of results

        Returns:
            List of (text, score) tuples
        """
        vec_a = self.embed(a)
        vec_b = self.embed(b)
        vec_c = self.embed(c)

        # Analogy vector: b - a + c
        target = vec_b - vec_a + vec_c
        target = target / np.linalg.norm(target)

        candidate_vecs = self.embed_batch(candidates)

        scores = []
        for text, vec in zip(candidates, candidate_vecs):
            sim = self._cosine_similarity(target, vec)
            scores.append((text, sim))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]

    @staticmethod
    def _cosine_similarity(v1: np.ndarray, v2: np.ndarray) -> float:
        """Compute cosine similarity between two vectors."""
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        if norm1 > 0 and norm2 > 0:
            return float(np.dot(v1, v2) / (norm1 * norm2))
        return 0.0

    # =========================================================================
    # Gap Detection
    # =========================================================================

    def find_semantic_gaps(
        self,
        concepts: List[str],
        threshold: float = 0.3
    ) -> List[Tuple[str, str, float]]:
        """
        Find semantic gaps: pairs of concepts with low similarity.

        Gaps indicate potential missing connections in the categorical
        structure that could be filled via Kan extensions or discovered.

        Args:
            concepts: List of concept names
            threshold: Similarity below which we consider a gap

        Returns:
            List of (concept1, concept2, similarity) tuples for gaps
        """
        matrix = self.similarity_matrix(concepts)
        gaps = []

        n = len(concepts)
        for i in range(n):
            for j in range(i + 1, n):
                sim = matrix[i, j]
                if sim < threshold:
                    gaps.append((concepts[i], concepts[j], sim))

        # Sort by similarity (lowest first = biggest gaps)
        gaps.sort(key=lambda x: x[2])
        return gaps

    def find_clusters(
        self,
        concepts: List[str],
        threshold: float = 0.7
    ) -> List[List[str]]:
        """
        Find clusters of semantically similar concepts.

        Uses simple threshold-based clustering.

        Args:
            concepts: List of concept names
            threshold: Similarity above which concepts are clustered

        Returns:
            List of clusters (each cluster is a list of concepts)
        """
        matrix = self.similarity_matrix(concepts)
        n = len(concepts)

        # Simple union-find clustering
        parent = list(range(n))

        def find(x):
            if parent[x] != x:
                parent[x] = find(parent[x])
            return parent[x]

        def union(x, y):
            px, py = find(x), find(y)
            if px != py:
                parent[px] = py

        # Cluster based on similarity threshold
        for i in range(n):
            for j in range(i + 1, n):
                if matrix[i, j] >= threshold:
                    union(i, j)

        # Group by cluster
        clusters_dict: Dict[int, List[str]] = {}
        for i, concept in enumerate(concepts):
            root = find(i)
            if root not in clusters_dict:
                clusters_dict[root] = []
            clusters_dict[root].append(concept)

        return list(clusters_dict.values())

    # =========================================================================
    # Cache Management
    # =========================================================================

    def _get_cached(self, text: str) -> Optional[np.ndarray]:
        """Get embedding from SQLite cache."""
        if not self._db_initialized:
            return None

        try:
            conn = sqlite3.connect(str(self.cache_path))
            cursor = conn.execute(
                "SELECT vector, dimension FROM embeddings WHERE text = ? AND model = ?",
                (text, self.model_name)
            )
            row = cursor.fetchone()
            conn.close()

            if row:
                vec = np.frombuffer(row[0], dtype=np.float32)
                return vec

        except Exception:
            pass

        return None

    def _set_cached(self, text: str, vector: np.ndarray):
        """Store embedding in SQLite cache."""
        if not self._db_initialized:
            return

        try:
            conn = sqlite3.connect(str(self.cache_path))
            conn.execute(
                """
                INSERT OR REPLACE INTO embeddings (text, model, vector, dimension)
                VALUES (?, ?, ?, ?)
                """,
                (text, self.model_name, vector.tobytes(), len(vector))
            )
            conn.commit()
            conn.close()

        except Exception:
            pass

    def clear_memory_cache(self):
        """Clear the in-memory cache."""
        self._memory_cache.clear()

    def clear_all_cache(self):
        """Clear both memory and SQLite cache."""
        self._memory_cache.clear()
        try:
            if self.cache_path.exists():
                self.cache_path.unlink()
            self._db_initialized = False
            self._init_cache_db()
        except Exception as e:
            print(f"[EmbeddingsEngine] Cache clear failed: {e}")

    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        stats = {"memory_cache": len(self._memory_cache)}

        if self._db_initialized:
            try:
                conn = sqlite3.connect(str(self.cache_path))
                count = conn.execute(
                    "SELECT COUNT(*) FROM embeddings WHERE model = ?",
                    (self.model_name,)
                ).fetchone()[0]
                conn.close()
                stats["sqlite_cache"] = count
            except Exception:
                stats["sqlite_cache"] = 0

        return stats


# =============================================================================
# Integration with Category
# =============================================================================

class CategoryEmbedder:
    """
    Integrates embeddings with the KOMPOSOS-IV Category runtime.

    Provides methods to:
    - Embed all objects in the category
    - Find similar objects
    - Detect semantic gaps in the graph
    """

    def __init__(
        self,
        category: 'Category',
        engine: Optional[EmbeddingsEngine] = None
    ):
        """
        Initialize the category embedder.

        Args:
            category: KOMPOSOS-IV Category instance
            engine: Embeddings engine (creates default if None)
        """
        self.category = category
        self.engine = engine or EmbeddingsEngine()

    def embed_all_objects(self, show_progress: bool = True) -> int:
        """
        Compute embeddings for all objects in the category.

        Args:
            show_progress: Show progress bar

        Returns:
            Number of objects embedded
        """
        objects = self.category.objects()

        if not objects:
            return 0

        # Create texts for embedding (combine name + type + metadata)
        texts = []
        for obj in objects:
            text_parts = [obj.name, obj.type_name]
            if obj.metadata:
                for k, v in obj.metadata.items():
                    text_parts.append(f"{k}: {v}")
            texts.append(" ".join(text_parts))

        # Batch embed
        embeddings = self.engine.embed_batch(texts, show_progress=show_progress)

        # Update objects with embeddings
        count = 0
        for obj, vec in zip(objects, embeddings):
            obj.embedding = vec
            self.category.add_object(obj)
            count += 1

        return count

    def find_similar_objects(
        self,
        query: str,
        top_k: int = 10,
        type_filter: Optional[str] = None
    ) -> List[Tuple['Object', float]]:
        """
        Find objects similar to a query.

        Args:
            query: Query text
            top_k: Number of results
            type_filter: Optional type filter

        Returns:
            List of (object, similarity) tuples
        """
        if type_filter:
            objects = [o for o in self.category.objects() if o.type_name == type_filter]
        else:
            objects = self.category.objects()

        if not objects:
            return []

        # Get embeddings
        query_vec = self.engine.embed(query)

        results = []
        for obj in objects:
            if obj.embedding is not None:
                sim = self.engine._cosine_similarity(query_vec, obj.embedding)
                results.append((obj, sim))

        # Sort by similarity
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

    def find_gaps(
        self,
        threshold: float = 0.3
    ) -> List[Tuple['Object', 'Object', float]]:
        """
        Find semantic gaps between objects that have no direct morphism.

        A gap is a pair of objects with:
        1. Low semantic similarity (below threshold)
        2. No direct morphism connecting them

        These are candidates for Kan extension or new relationship discovery.

        Args:
            threshold: Similarity below which we consider a gap

        Returns:
            List of (obj1, obj2, similarity) tuples
        """
        objects = self.category.objects()

        if len(objects) < 2:
            return []

        # Get all existing morphism pairs
        existing_pairs = set()
        for mor in self.category.morphisms():
            existing_pairs.add((mor.source, mor.target))
            existing_pairs.add((mor.target, mor.source))

        # Find gaps
        gaps = []
        for i, obj1 in enumerate(objects):
            for obj2 in objects[i+1:]:
                # Skip if direct morphism exists
                if (obj1.name, obj2.name) in existing_pairs:
                    continue

                # Check similarity
                if obj1.embedding is not None and obj2.embedding is not None:
                    sim = self.engine._cosine_similarity(obj1.embedding, obj2.embedding)
                    if sim < threshold:
                        gaps.append((obj1, obj2, sim))

        # Sort by similarity (lowest first)
        gaps.sort(key=lambda x: x[2])
        return gaps


# =============================================================================
# Factory Functions
# =============================================================================

def create_engine(
    model_name: str = DEFAULT_MODEL,
    device: str = None
) -> EmbeddingsEngine:
    """
    Create an embeddings engine.

    Args:
        model_name: Sentence Transformer model name
        device: Device to run on ('cpu', 'cuda', etc.)

    Returns:
        EmbeddingsEngine instance
    """
    return EmbeddingsEngine(model_name=model_name, device=device)


def load_engine() -> EmbeddingsEngine:
    """Load the default embeddings engine with caching."""
    return EmbeddingsEngine()


# =============================================================================
# Demo
# =============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("KOMPOSOS-IV Embeddings Engine Demo")
    print("=" * 70)

    # Create engine
    print("\n[1] Initializing embeddings engine...")
    engine = EmbeddingsEngine()
    print(f"    Model: {engine.model_name}")
    print(f"    Dimension: {engine.dimension}")
    print(f"    Available: {engine.is_available}")

    # Test embedding
    print("\n[2] Testing single embeddings...")
    concepts = [
        "quantum mechanics",
        "wave function",
        "matrix mechanics",
        "classical physics",
        "general relativity"
    ]
    for concept in concepts:
        result = engine.embed_with_result(concept)
        print(f"    '{concept}': {result.dimension}d, cached={result.cached}")

    # Test similarity
    print("\n[3] Testing similarity...")
    pairs = [
        ("quantum mechanics", "wave function"),
        ("quantum mechanics", "classical physics"),
        ("matrix mechanics", "wave function"),
        ("general relativity", "quantum mechanics")
    ]
    for t1, t2 in pairs:
        sim = engine.similarity(t1, t2)
        print(f"    '{t1}' <-> '{t2}': {sim:.4f}")

    # Test analogy
    print("\n[4] Testing analogy: Newton is to classical as ??? is to quantum")
    candidates = ["Einstein", "Schrodinger", "Bohr", "Maxwell", "Faraday"]
    results = engine.find_analogies(
        "Newton", "classical physics", "quantum mechanics",
        candidates, top_k=3
    )
    for name, score in results:
        print(f"    {name}: {score:.4f}")

    # Test gap detection
    print("\n[5] Testing gap detection...")
    all_concepts = concepts + ["thermodynamics", "statistical mechanics", "entropy"]
    gaps = engine.find_semantic_gaps(all_concepts, threshold=0.4)
    print(f"    Found {len(gaps)} gaps:")
    for c1, c2, sim in gaps[:5]:
        print(f"    - '{c1}' <-> '{c2}': {sim:.4f}")

    # Test clustering
    print("\n[6] Testing clustering...")
    clusters = engine.find_clusters(all_concepts, threshold=0.5)
    print(f"    Found {len(clusters)} clusters:")
    for i, cluster in enumerate(clusters):
        print(f"    Cluster {i+1}: {cluster}")

    # Cache stats
    print("\n[7] Cache statistics:")
    stats = engine.get_cache_stats()
    for k, v in stats.items():
        print(f"    {k}: {v}")

    print("\n" + "=" * 70)
    print("Demo complete!")
