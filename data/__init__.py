# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""
KOMPOSOS-IV Data Layer

Provides embeddings for categorical structures using Sentence Transformers.
"""

from .embeddings import (
    EmbeddingResult,
    EmbeddingsEngine,
    CategoryEmbedder,
    create_engine,
    load_engine,
    DEFAULT_MODEL,
)

__all__ = [
    "EmbeddingResult",
    "EmbeddingsEngine",
    "CategoryEmbedder",
    "create_engine",
    "load_engine",
    "DEFAULT_MODEL",
]
