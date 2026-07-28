# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""
Shared helpers for Lung 5 public validation and Noetik-style audit reports.
"""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np

from spatial_biology.cosmx_adapter import CosMxAdapter
from spatial_biology.pathway_scoring import MotifSpec, available_motifs, build_negative_motifs


def load_public_dataset(
    dataset_path: str | Path,
    proximity_threshold: float = 100.0,
    expression_threshold: float = 0.1,
) -> Tuple[CosMxAdapter, List, object, Dict[str, object]]:
    """
    Load cells, build the logic-gated network, and run geometry once.
    """
    adapter = CosMxAdapter(
        proximity_threshold=proximity_threshold,
        expression_threshold=expression_threshold,
    )
    cells = adapter.load_cosmx_csv(str(dataset_path))
    store = adapter.build_network(cells)
    audit_results = adapter.run_geometric_audit(store)

    curvature_cache = dict(audit_results['curvature'].edge_curvatures)
    store.curvature_cache = curvature_cache
    context = {
        'dataset_path': str(dataset_path),
        'cells': cells,
        'store': store,
        'audit_results': audit_results,
        'curvature_cache': curvature_cache,
        'available_genes': set(cells[0].expression.keys()) if cells else set(),
        'proximity_threshold': proximity_threshold,
        'expression_threshold': expression_threshold,
        'coordinates': np.array([[c.x, c.y] for c in cells], dtype=float),
    }
    return adapter, cells, store, context


def build_benchmark_panel(context: Dict[str, object], negative_count: int = 24) -> List[MotifSpec]:
    """Build a mixed positive/negative motif panel for the dataset."""
    available_genes = context['available_genes']
    adapter = context['store']  # type: ignore[assignment]
    _ = adapter
    positives = available_motifs(available_genes)
    lr_db = CosMxAdapter().lr_db
    known_pairs = lr_db.get_known_pair_set()
    negatives = build_negative_motifs(available_genes, known_pairs, target_count=negative_count)
    return positives + negatives


def build_expression_arrays(cells: List) -> Dict[str, np.ndarray]:
    """Convert per-cell expression dicts into arrays keyed by gene."""
    if not cells:
        return {}
    genes = cells[0].expression.keys()
    arrays: Dict[str, np.ndarray] = {}
    for gene in genes:
        arrays[gene] = np.array([c.expression.get(gene, 0.0) for c in cells], dtype=float)
    return arrays


def geometry_weight(kappa: float) -> float:
    """Bound Ricci contribution to avoid exploding weights on extreme bottlenecks."""
    return 0.5 + (1.0 / (1.0 + np.exp(np.clip(kappa, -8.0, 8.0))))


def compute_pair_score(
    motif: MotifSpec,
    context: Dict[str, object],
    expression_arrays: Dict[str, np.ndarray],
) -> Dict[str, float]:
    """Compute baseline and KOMPOSOS scores for one motif."""
    coords: np.ndarray = context['coordinates']  # type: ignore[assignment]
    proximity_threshold: float = context['proximity_threshold']  # type: ignore[assignment]
    expression_threshold: float = context['expression_threshold']  # type: ignore[assignment]
    store = context['store']
    curvature_cache = context['curvature_cache']

    src = expression_arrays.get(motif.source_gene)
    tgt = expression_arrays.get(motif.target_gene)
    if src is None or tgt is None:
        return {
            'random': 0.0,
            'distance_only': 0.0,
            'expression_only': 0.0,
            'logic_gated': 0.0,
            'logic_gated_geometry': 0.0,
        }

    if motif.interaction_type == "intracellular":
        mask = (src >= expression_threshold) & (tgt >= expression_threshold)
        support = np.minimum(src, tgt)[mask]
        expression_only = float(support.mean()) if support.size else 0.0
        distance_only = expression_only
    else:
        src_idx = np.flatnonzero(src >= expression_threshold)
        tgt_idx = np.flatnonzero(tgt >= expression_threshold)
        if src_idx.size and tgt_idx.size:
            dists = np.linalg.norm(
                coords[src_idx][:, None, :] - coords[tgt_idx][None, :, :],
                axis=2,
            )
            support = np.minimum(src[src_idx][:, None], tgt[tgt_idx][None, :])
            valid = dists <= proximity_threshold
            if valid.any():
                expr_support = support[valid]
                distance_support = (1.0 - (dists[valid] / proximity_threshold)) * expr_support
                expression_only = float(expr_support.mean())
                distance_only = float(distance_support.mean())
            else:
                expression_only = 0.0
                distance_only = 0.0
        else:
            expression_only = 0.0
            distance_only = 0.0

    logic_scores: List[float] = []
    geometry_scores: List[float] = []
    for morph in store.list_morphisms(limit=100000):
        src_gene = morph.metadata.get('source_gene') or morph.metadata.get('ligand')
        tgt_gene = morph.metadata.get('target_gene') or morph.metadata.get('receptor')
        if (src_gene, tgt_gene) != (motif.source_gene, motif.target_gene):
            continue
        logic_scores.append(float(morph.confidence))
        kappa = curvature_cache.get((morph.source_name, morph.target_name), 0.0)
        geometry_scores.append(float(morph.confidence) * geometry_weight(float(kappa)))

    logic_gated = float(np.mean(logic_scores)) if logic_scores else 0.0
    logic_gated_geometry = float(np.mean(geometry_scores)) if geometry_scores else 0.0

    # Deterministic pseudo-random baseline for reproducibility.
    random_seed = abs(hash((motif.source_gene, motif.target_gene))) % 10_000
    random = random_seed / 10_000.0

    return {
        'random': float(random),
        'distance_only': distance_only,
        'expression_only': expression_only,
        'logic_gated': logic_gated,
        'logic_gated_geometry': logic_gated_geometry,
    }


def motif_record(motif: MotifSpec, scores: Dict[str, float]) -> Dict[str, object]:
    """Serialize a motif with its scores for reporting."""
    record = asdict(motif)
    record.update(scores)
    return record
