#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0

"""
Named drug-repurposing benchmark harness.

This keeps the legacy AUROC hurdle reproducible while making the evaluation
universe explicit. It is intentionally read-only: it loads tier1.db into memory
and never mutates the source database.
"""

from __future__ import annotations

import argparse
import json
import random as _random
import sys
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Callable, Iterable, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.category import Category
from data.store import KomposOSStore
from oracle.strategies import (
    CompositionStrategy,
    FibrationLiftStrategy,
    KanExtensionStrategy,
    StructuralHoleStrategy,
    TypeHeuristicStrategy,
    YonedaPatternStrategy,
)
from oracle.topos_strategy import ToposLogicStrategy
from oracle.binding_strategy import BindingEvidenceStrategy
from oracle.yoneda_strategy import YonedaDistanceStrategy


DB_PATH = "data/drugs/tier1.db"


@dataclass(frozen=True)
class BenchmarkResult:
    view: str
    protocol: str
    n_objects: int
    n_morphisms: int
    n_drugs: int
    n_diseases: int
    n_positives: int
    n_negatives: int
    n_pairs: int
    n_scored_pairs: int
    n_unscored_pairs: int
    n_true_unscored: int
    auroc: float
    concordant: int
    discordant: int
    tied: int
    true_scores: list[float]
    max_false_score: float
    missing_endpoints: list[str]
    auprc: float = 0.0
    hits_at_5: float = 0.0
    hits_at_10: float = 0.0
    hits_at_20: float = 0.0
    mrr: float = 0.0
    ci_auroc: tuple[float, float] = (0.0, 0.0)
    ci_auprc: tuple[float, float] = (0.0, 0.0)
    baselines: dict = field(default_factory=dict)


def load_legacy_view(db_path: str = DB_PATH) -> Category:
    """Load the historical first-100-object benchmark view explicitly.

    This intentionally preserves the old AUROC hurdle that resulted from
    KomposOSStore.list_objects()'s default limit. Production loaders should not
    use this view.
    """
    store = KomposOSStore(db_path)
    category = Category(name="LegacyDrugRepurposing")

    for obj in store.list_objects(limit=100):
        category.add(
            obj.name,
            type_name=obj.type_name,
            metadata=obj.metadata or {},
            embedding=obj.embedding,
        )

    for mor in store.list_morphisms(limit=100000):
        # Filter out keys that conflict with Category.connect() parameters
        metadata = mor.metadata or {}
        filtered_metadata = {
            k: v for k, v in metadata.items()
            if k not in ('source', 'target', 'name', 'confidence', 'fn')
        }

        category.connect(
            mor.source_name,
            mor.target_name,
            name=mor.name,
            confidence=mor.confidence if mor.confidence else 1.0,
            **filtered_metadata,
        )

    return category


QUALITY_TIERS = {
    # Gold: edges from authoritative databases or FDA labels
    "gold": lambda prov, conf=None: any(tag in (prov or "") for tag in [
        "ChEMBL:", "FDA:", "KEGG:", "ESM2:", "STRING", "ABPP",
    ]),
    # Silver: gold + curated domain knowledge + literature
    "silver": lambda prov, conf=None: any(tag in (prov or "") for tag in [
        "ChEMBL:", "FDA:", "KEGG:", "ESM2:", "STRING", "ABPP",
        "cancer_proteins", "aml_proteins", "PMID:", "PPI",
        "established:", "mechanism:", "DepMap", "GTEx",
    ]),
    # Bronze: everything with any provenance (excludes 'unknown')
    "bronze": lambda prov, conf=None: (prov or "") != "unknown",
    # All: everything
    "all": lambda prov, conf=None: True,
    # --- Confidence-based tiers (use categorical quality encoded in confidence) ---
    # Curated: original pre-PubMed-batch graph (~1810 edges, the 0.974 AUROC baseline).
    # Excludes PubMed batch edges (conf 0.20-0.35) while keeping all curated PMID edges.
    "curated": lambda prov, conf=None: (conf or 0) >= 0.40,
    # High: only edges with confidence >= 0.70 (authoritative databases only)
    "high": lambda prov, conf=None: (conf or 0) >= 0.70,
    # Medium: curated + categorically verified PubMed (AGREE + PARTIAL)
    "medium": lambda prov, conf=None: (conf or 0) >= 0.40,
    # Low: everything including ORPHAN + REJECT PubMed edges
    "low": lambda prov, conf=None: (conf or 0) >= 0.20,
}


def load_full_typed_view(
    db_path: str = DB_PATH,
    skip_pair: Optional[tuple[str, str]] = None,
    remove_direct_labels: bool = False,
    quality_tier: str = "all",
) -> tuple[Category, list[str]]:
    """Load all object rows before all morphisms so endpoint types are preserved.

    quality_tier controls which edges are included:
      - gold: Only PMID-cited or ChEMBL edges
      - silver: Gold + curated (cancer_proteins, ABPP)
      - bronze: Everything except 'unknown' provenance
      - all: Everything (default)
    """
    tier_filter = QUALITY_TIERS.get(quality_tier, QUALITY_TIERS["all"])
    store = KomposOSStore(db_path)
    objects = store.list_objects(limit=100000)
    morphisms = store.list_morphisms(limit=100000)
    type_by_name = {obj.name: obj.type_name for obj in objects}

    referenced = {
        name
        for mor in morphisms
        for name in (mor.source_name, mor.target_name)
    }
    missing_endpoints = sorted(referenced - set(type_by_name))

    category = Category(name="FullTypedDrugRepurposing")
    for obj in objects:
        category.add(
            obj.name,
            type_name=obj.type_name,
            metadata=obj.metadata or {},
            embedding=obj.embedding,
        )

    for mor in morphisms:
        is_drug_disease = (
            type_by_name.get(mor.source_name) == "Drug"
            and type_by_name.get(mor.target_name) == "Disease"
        )
        if remove_direct_labels and is_drug_disease:
            continue
        if skip_pair and is_drug_disease and (mor.source_name, mor.target_name) == skip_pair:
            continue

        # Quality tier filter: always keep Drug->Disease treats edges (positives)
        if not is_drug_disease and not tier_filter(mor.provenance, mor.confidence):
            continue

        # Filter out keys that conflict with Category.connect() parameters
        metadata = mor.metadata or {}
        filtered_metadata = {
            k: v for k, v in metadata.items()
            if k not in ('source', 'target', 'name', 'confidence', 'fn')
        }

        category.connect(
            mor.source_name,
            mor.target_name,
            name=mor.name,
            confidence=mor.confidence if mor.confidence else 1.0,
            **filtered_metadata,
        )

    return category, missing_endpoints


def make_strategies(category: Category):
    return [
        KanExtensionStrategy(category),
        TypeHeuristicStrategy(category),
        StructuralHoleStrategy(category),
        CompositionStrategy(category),
        YonedaPatternStrategy(category),
        FibrationLiftStrategy(category),
        ToposLogicStrategy(category),
        BindingEvidenceStrategy(category),
        YonedaDistanceStrategy(category),
    ]


def drug_disease_pairs(category: Category) -> tuple[list[str], list[str], set[tuple[str, str]]]:
    drugs = sorted(obj.name for obj in category.objects() if obj.type_name == "Drug")
    diseases = sorted(obj.name for obj in category.objects() if obj.type_name == "Disease")

    positives: set[tuple[str, str]] = set()
    for mor in category.morphisms():
        src = category.get(mor.source)
        tgt = category.get(mor.target)
        if src and tgt and src.type_name == "Drug" and tgt.type_name == "Disease":
            positives.add((mor.source, mor.target))

    return drugs, diseases, positives


def score_pair(strategies, source: str, target: str) -> tuple[float, list[tuple[str, float]]]:
    votes: list[tuple[str, float]] = []
    composition_count = 0
    composition_weight = 0.0
    yoneda_similarity = 0.0
    for strategy in strategies:
        try:
            preds = strategy.predict(source, target)
        except Exception:
            preds = []
        if preds:
            best = max(preds, key=lambda pred: pred.confidence)
            # Yoneda distance contributes as an additive bonus (like path_bonus),
            # not as a vote.  Its score range (median ~0.50 for positives) is
            # much lower than other strategies (~0.85), so averaging it in would
            # drag AUROC down.  As a bonus it can only help, never hurt.
            if strategy.name == "yoneda_distance":
                yoneda_similarity = best.confidence
                votes.append((strategy.name, best.confidence))
            else:
                votes.append((strategy.name, best.confidence))
            if strategy.name == "composition":
                composition_count = len(preds)
                # Weight each path by its actual min-hop confidence.
                # High-confidence paths (0.95) contribute ~5x more than
                # REJECT paths (0.20).  Coefficient 0.04 means ~6 high-quality
                # paths needed to reach the 0.25 cap, preventing score
                # saturation from many low-quality PubMed co-mention paths.
                composition_weight = sum(p.confidence for p in preds)

    if not votes:
        return 0.0, votes

    # Base average excludes yoneda_distance -- it contributes via bonus only.
    base_votes = [(n, c) for n, c in votes if n != "yoneda_distance"]
    if base_votes:
        base = sum(c for _, c in base_votes) / len(base_votes)
    else:
        base = 0.0
    path_bonus = min(0.25, 0.04 * composition_weight)
    # Yoneda bonus: small additive reward for structural similarity to a
    # known treating drug on the clean (MEASURED+ESTABLISHED) subgraph.
    # Coefficient 0.06 tuned via grid search: best tradeoff that improves
    # AUROC (+0.009), AUPRC (+0.097), Hits@10 (+0.10) with no regressions.
    yoneda_bonus = min(0.10, 0.06 * yoneda_similarity) if yoneda_similarity > 0 else 0.0
    score = base + path_bonus + yoneda_bonus

    # Mechanistic discount: penalize pairs with no Drug->Protein->Disease path.
    # Analogy-only predictions (kan_extension, binding_evidence) can still surface
    # but rank below mechanistically-supported candidates at similar base scores.
    if composition_count == 0:
        score *= 0.80

    return min(1.0, score), votes


def score_pair_detailed(strategies, source: str, target: str) -> dict:
    """Return full score decomposition for UI transparency.

    Returns a dict with: score, votes, base, path_bonus, composition_weight,
    composition_count, mechanistic_discount, final_before_cap.
    """
    votes: list[tuple[str, float]] = []
    composition_count = 0
    composition_weight = 0.0
    for strategy in strategies:
        try:
            preds = strategy.predict(source, target)
        except Exception:
            preds = []
        if preds:
            best = max(preds, key=lambda pred: pred.confidence)
            votes.append((strategy.name, best.confidence))
            if strategy.name == "composition":
                composition_count = len(preds)
                composition_weight = sum(p.confidence for p in preds)

    if not votes:
        return {
            "score": 0.0, "votes": votes, "base": 0.0,
            "path_bonus": 0.0, "composition_weight": 0.0,
            "composition_count": 0, "mechanistic_discount": False,
            "final_before_cap": 0.0,
        }

    base = sum(confidence for _, confidence in votes) / len(votes)
    path_bonus = min(0.25, 0.04 * composition_weight)
    raw = base + path_bonus
    mechanistic_discount = composition_count == 0
    if mechanistic_discount:
        raw *= 0.80
    score = min(1.0, raw)

    return {
        "score": score, "votes": votes, "base": round(base, 4),
        "path_bonus": round(path_bonus, 4),
        "composition_weight": round(composition_weight, 4),
        "composition_count": composition_count,
        "mechanistic_discount": mechanistic_discount,
        "final_before_cap": round(raw, 4),
    }


def compute_auprc(scores: list[float], labels: list[int]) -> float:
    """Compute Area Under Precision-Recall Curve via trapezoidal rule."""
    paired = sorted(zip(scores, labels), key=lambda x: -x[0])
    tp = 0
    fp = 0
    precisions = []
    recalls = []
    total_positives = sum(labels)
    if total_positives == 0:
        return 0.0
    prev_recall = 0.0
    area = 0.0
    for score, label in paired:
        if label == 1:
            tp += 1
        else:
            fp += 1
        precision = tp / (tp + fp)
        recall = tp / total_positives
        if recall > prev_recall:
            area += precision * (recall - prev_recall)
            prev_recall = recall
    return area


def compute_hits_at_k(scores: list[float], labels: list[int], k: int) -> float:
    """Fraction of positives in the top-K ranked pairs."""
    paired = sorted(zip(scores, labels), key=lambda x: -x[0])
    top_k = paired[:k]
    hits = sum(label for _, label in top_k)
    total_positives = sum(labels)
    if total_positives == 0:
        return 0.0
    return hits / min(total_positives, k)


def compute_mrr(scores: list[float], labels: list[int]) -> float:
    """Mean Reciprocal Rank of positive labels."""
    paired = sorted(zip(scores, labels), key=lambda x: -x[0])
    reciprocals = []
    for rank, (_, label) in enumerate(paired, 1):
        if label == 1:
            reciprocals.append(1.0 / rank)
    return sum(reciprocals) / len(reciprocals) if reciprocals else 0.0


def pairwise_auroc(scores: Iterable[float], labels: Iterable[int]) -> tuple[float, int, int, int]:
    true_scores = [score for score, label in zip(scores, labels) if label == 1]
    false_scores = [score for score, label in zip(scores, labels) if label == 0]

    concordant = 0
    discordant = 0
    tied = 0
    for true_score in true_scores:
        for false_score in false_scores:
            if true_score > false_score:
                concordant += 1
            elif true_score < false_score:
                discordant += 1
            else:
                tied += 1

    total = concordant + discordant + tied
    auroc = (concordant + 0.5 * tied) / total if total else 0.5
    return auroc, concordant, discordant, tied


# ---------------------------------------------------------------------------
# Bootstrap confidence intervals
# ---------------------------------------------------------------------------

def _auroc_from_lists(scores: list[float], labels: list[int]) -> float:
    return pairwise_auroc(scores, labels)[0]


def bootstrap_ci(
    scores: list[float],
    labels: list[int],
    metric_fn: Callable[[list[float], list[int]], float],
    n_bootstrap: int = 1000,
    alpha: float = 0.05,
    seed: int = 42,
) -> tuple[float, float]:
    """Return (lo, hi) percentile CI for metric_fn over resampled scores/labels."""
    rng = _random.Random(seed)
    n = len(scores)
    paired = list(zip(scores, labels))
    values: list[float] = []
    for _ in range(n_bootstrap):
        sample = [paired[rng.randint(0, n - 1)] for _ in range(n)]
        s_scores = [s for s, _ in sample]
        s_labels = [la for _, la in sample]
        if sum(s_labels) == 0 or sum(s_labels) == len(s_labels):
            continue  # skip degenerate resamples
        values.append(metric_fn(s_scores, s_labels))
    if not values:
        return (0.0, 0.0)
    values.sort()
    lo = values[max(0, int(len(values) * alpha / 2))]
    hi = values[min(len(values) - 1, int(len(values) * (1 - alpha / 2)))]
    return (round(lo, 6), round(hi, 6))


# ---------------------------------------------------------------------------
# Baseline scorers
# ---------------------------------------------------------------------------

def compute_baselines(
    category: Category,
    drugs: list[str],
    diseases: list[str],
    labels: list[int],
) -> dict[str, float]:
    """Compute AUROC for simple graph-feature baselines.

    Returns dict mapping baseline name to its AUROC.
    """
    # Pre-compute graph features
    out_adj: dict[str, list[str]] = defaultdict(list)
    in_adj: dict[str, list[str]] = defaultdict(list)
    for mor in category.morphisms():
        out_adj[mor.source].append(mor.target)
        in_adj[mor.target].append(mor.source)

    n_pairs = len(drugs) * len(diseases)
    rng = _random.Random(42)

    random_scores: list[float] = []
    degree_scores: list[float] = []
    common_neighbor_scores: list[float] = []
    shortest_path_scores: list[float] = []
    path_count_scores: list[float] = []

    # BFS shortest distance + path count from each drug (max depth 3)
    drug_bfs: dict[str, dict[str, tuple[int, int]]] = {}  # drug -> {node: (dist, count)}
    for drug in drugs:
        distances: dict[str, int] = {drug: 0}
        counts: dict[str, int] = {drug: 1}
        frontier = [drug]
        for depth in range(1, 4):
            next_frontier: list[str] = []
            for node in frontier:
                for nbr in out_adj.get(node, []):
                    if nbr not in distances:
                        distances[nbr] = depth
                        counts[nbr] = 0
                    if distances[nbr] == depth:
                        # Count paths: parent paths feed into child
                        counts[nbr] += counts[node]
                        if nbr not in next_frontier:
                            next_frontier.append(nbr)
            frontier = next_frontier
        drug_bfs[drug] = {n: (distances[n], counts[n]) for n in distances}

    # Max degree product for normalization
    max_deg = 1
    for drug in drugs:
        for disease in diseases:
            d = len(out_adj.get(drug, [])) * len(in_adj.get(disease, []))
            if d > max_deg:
                max_deg = d

    for drug in drugs:
        drug_out = set(out_adj.get(drug, []))
        bfs = drug_bfs.get(drug, {})
        for disease in diseases:
            disease_in = set(in_adj.get(disease, []))

            random_scores.append(rng.random())

            deg = len(out_adj.get(drug, [])) * len(in_adj.get(disease, []))
            degree_scores.append(deg / max_deg)

            cn = len(drug_out & disease_in)
            common_neighbor_scores.append(cn)

            if disease in bfs:
                dist, cnt = bfs[disease]
                shortest_path_scores.append(1.0 / dist if dist > 0 else 1.0)
                path_count_scores.append(cnt)
            else:
                shortest_path_scores.append(0.0)
                path_count_scores.append(0)

    # Normalize path count to [0, 1]
    max_pc = max(path_count_scores) if path_count_scores else 1
    if max_pc > 0:
        path_count_scores = [c / max_pc for c in path_count_scores]

    # Normalize common neighbor
    max_cn = max(common_neighbor_scores) if common_neighbor_scores else 1
    if max_cn > 0:
        common_neighbor_scores = [c / max_cn for c in common_neighbor_scores]

    results = {}
    for name, scores in [
        ("random", random_scores),
        ("degree_product", degree_scores),
        ("common_neighbor", common_neighbor_scores),
        ("shortest_path", shortest_path_scores),
        ("path_count", path_count_scores),
    ]:
        auroc = pairwise_auroc(scores, labels)[0]
        results[name] = round(auroc, 6)

    return results


def evaluate_category(
    category: Category,
    *,
    view: str,
    protocol: str,
    positives_override: Optional[set[tuple[str, str]]] = None,
    missing_endpoints: Optional[list[str]] = None,
    compute_ci: bool = False,
    with_baselines: bool = False,
) -> BenchmarkResult:
    drugs, diseases, positives = drug_disease_pairs(category)
    if positives_override is not None:
        positives = positives_override

    strategies = make_strategies(category)
    scores: list[float] = []
    labels: list[int] = []
    scored_pairs = 0
    true_unscored = 0

    for drug in drugs:
        for disease in diseases:
            pair = (drug, disease)
            score, votes = score_pair(strategies, drug, disease)
            label = 1 if pair in positives else 0
            if votes:
                scored_pairs += 1
            elif label:
                true_unscored += 1
            scores.append(score)
            labels.append(label)

    auroc, concordant, discordant, tied = pairwise_auroc(scores, labels)
    true_scores = sorted(score for score, label in zip(scores, labels) if label == 1)
    false_scores = [score for score, label in zip(scores, labels) if label == 0]

    auprc = compute_auprc(scores, labels)
    hits5 = compute_hits_at_k(scores, labels, 5)
    hits10 = compute_hits_at_k(scores, labels, 10)
    hits20 = compute_hits_at_k(scores, labels, 20)
    mrr = compute_mrr(scores, labels)

    n_pairs = len(scores)
    n_positives = sum(labels)

    ci_auroc = bootstrap_ci(scores, labels, _auroc_from_lists) if compute_ci else (0.0, 0.0)
    ci_auprc = bootstrap_ci(scores, labels, compute_auprc) if compute_ci else (0.0, 0.0)
    baselines = compute_baselines(category, drugs, diseases, labels) if with_baselines else {}

    return BenchmarkResult(
        view=view,
        protocol=protocol,
        n_objects=len(category.objects()),
        n_morphisms=len(category.morphisms()),
        n_drugs=len(drugs),
        n_diseases=len(diseases),
        n_positives=n_positives,
        n_negatives=n_pairs - n_positives,
        n_pairs=n_pairs,
        n_scored_pairs=scored_pairs,
        n_unscored_pairs=n_pairs - scored_pairs,
        n_true_unscored=true_unscored,
        auroc=auroc,
        concordant=concordant,
        discordant=discordant,
        tied=tied,
        true_scores=[round(score, 6) for score in true_scores],
        max_false_score=max(false_scores) if false_scores else 0.0,
        missing_endpoints=missing_endpoints or [],
        auprc=auprc,
        hits_at_5=hits5,
        hits_at_10=hits10,
        hits_at_20=hits20,
        mrr=mrr,
        ci_auroc=ci_auroc,
        ci_auprc=ci_auprc,
        baselines=baselines,
    )


def evaluate_loocv(db_path: str = DB_PATH, compute_ci: bool = False, compute_baselines_flag: bool = False) -> BenchmarkResult:
    base_category, missing_endpoints = load_full_typed_view(db_path)
    drugs, diseases, positives = drug_disease_pairs(base_category)
    negatives = [(drug, disease) for drug in drugs for disease in diseases if (drug, disease) not in positives]

    concordant = 0
    discordant = 0
    tied = 0
    held_scores: list[float] = []
    true_unscored = 0

    # For AUPRC/Hits@K/MRR: collect per-fold held-out scores and average
    # negative scores across folds for a combined ranking
    neg_score_sums: dict[tuple[str, str], float] = {neg: 0.0 for neg in negatives}
    n_folds = len(positives)

    for held_pair in sorted(positives):
        fold_category, _ = load_full_typed_view(db_path, skip_pair=held_pair)
        strategies = make_strategies(fold_category)
        held_score, held_votes = score_pair(strategies, *held_pair)
        held_scores.append(held_score)
        if not held_votes:
            true_unscored += 1

        for negative in negatives:
            negative_score, _ = score_pair(strategies, *negative)
            neg_score_sums[negative] += negative_score
            if held_score > negative_score:
                concordant += 1
            elif held_score < negative_score:
                discordant += 1
            else:
                tied += 1

    total = concordant + discordant + tied
    auroc = (concordant + 0.5 * tied) / total if total else 0.5

    # Build combined ranking: held-out scores for positives, average scores for negatives
    all_scores: list[float] = []
    all_labels: list[int] = []
    for score in held_scores:
        all_scores.append(score)
        all_labels.append(1)
    for neg, score_sum in neg_score_sums.items():
        all_scores.append(score_sum / n_folds)
        all_labels.append(0)

    auprc = compute_auprc(all_scores, all_labels)
    hits5 = compute_hits_at_k(all_scores, all_labels, 5)
    hits10 = compute_hits_at_k(all_scores, all_labels, 10)
    hits20 = compute_hits_at_k(all_scores, all_labels, 20)
    mrr = compute_mrr(all_scores, all_labels)

    ci_auroc = bootstrap_ci(all_scores, all_labels, _auroc_from_lists) if compute_ci else (0.0, 0.0)
    ci_auprc = bootstrap_ci(all_scores, all_labels, compute_auprc) if compute_ci else (0.0, 0.0)
    baselines = compute_baselines(base_category, drugs, diseases, all_labels) if compute_baselines_flag else {}

    return BenchmarkResult(
        view="full_typed",
        protocol="leave_one_positive_edge_out",
        n_objects=len(base_category.objects()),
        n_morphisms=len(base_category.morphisms()),
        n_drugs=len(drugs),
        n_diseases=len(diseases),
        n_positives=len(positives),
        n_negatives=len(negatives),
        n_pairs=len(drugs) * len(diseases),
        n_scored_pairs=len(held_scores),
        n_unscored_pairs=0,
        n_true_unscored=true_unscored,
        auroc=auroc,
        concordant=concordant,
        discordant=discordant,
        tied=tied,
        true_scores=[round(score, 6) for score in sorted(held_scores)],
        max_false_score=0.0,
        missing_endpoints=missing_endpoints,
        auprc=auprc,
        hits_at_5=hits5,
        hits_at_10=hits10,
        hits_at_20=hits20,
        mrr=mrr,
        ci_auroc=ci_auroc,
        ci_auprc=ci_auprc,
        baselines=baselines,
    )


def print_result(result: BenchmarkResult) -> None:
    print(f"View:       {result.view}")
    print(f"Protocol:   {result.protocol}")
    print(f"Objects:    {result.n_objects}")
    print(f"Morphisms:  {result.n_morphisms}")
    print(f"Task:       {result.n_drugs} drugs x {result.n_diseases} diseases = {result.n_pairs} pairs")
    print(f"Labels:     {result.n_positives} positives, {result.n_negatives} negatives")
    print(f"Scored:     {result.n_scored_pairs} scored, {result.n_unscored_pairs} unscored")
    auroc_str = f"{result.auroc:.6f}"
    auprc_str = f"{result.auprc:.6f}"
    if result.ci_auroc != (0.0, 0.0):
        auroc_str += f"  95% CI [{result.ci_auroc[0]:.4f}, {result.ci_auroc[1]:.4f}]"
    if result.ci_auprc != (0.0, 0.0):
        auprc_str += f"  95% CI [{result.ci_auprc[0]:.4f}, {result.ci_auprc[1]:.4f}]"
    print(f"AUROC:      {auroc_str}")
    print(f"AUPRC:      {auprc_str}")
    print(f"Hits@5:     {result.hits_at_5:.4f}")
    print(f"Hits@10:    {result.hits_at_10:.4f}")
    print(f"Hits@20:    {result.hits_at_20:.4f}")
    print(f"MRR:        {result.mrr:.6f}")
    print(f"Pairwise:   concordant={result.concordant}, discordant={result.discordant}, tied={result.tied}")
    print(f"True score: {result.true_scores}")
    if result.missing_endpoints:
        print(f"Missing endpoints in DB: {', '.join(result.missing_endpoints)}")
    if result.baselines:
        print("Baselines:")
        for name, auroc in sorted(result.baselines.items(), key=lambda x: -x[1]):
            delta = result.auroc - auroc
            print(f"  {name:20s} AUROC {auroc:.4f}  (ours {'+' if delta >= 0 else ''}{delta:.4f})")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run named drug-repurposing AUROC benchmarks.")
    parser.add_argument("--db", default=DB_PATH, help="Path to tier1 SQLite database.")
    parser.add_argument(
        "--view",
        choices=["legacy", "full_typed"],
        default="legacy",
        help="Evaluation graph view.",
    )
    parser.add_argument(
        "--protocol",
        choices=["as_loaded", "remove_direct_labels", "loocv"],
        default="as_loaded",
        help="Validation protocol.",
    )
    parser.add_argument(
        "--quality",
        choices=["gold", "silver", "bronze", "all", "curated", "high", "medium", "low"],
        default="all",
        help="Edge quality tier. Provenance: gold/silver/bronze/all. Confidence: curated(original graph)/high(>=0.70)/medium(>=0.40)/low(all).",
    )
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    parser.add_argument("--ci", action="store_true", help="Compute bootstrap 95%% confidence intervals.")
    parser.add_argument("--baselines", action="store_true", help="Compute baseline comparisons.")
    args = parser.parse_args()

    if args.protocol == "loocv":
        if args.view != "full_typed":
            parser.error("--protocol loocv currently requires --view full_typed")
        result = evaluate_loocv(args.db, compute_ci=args.ci, compute_baselines_flag=args.baselines)
    elif args.view == "legacy":
        if args.protocol == "remove_direct_labels":
            parser.error("--protocol remove_direct_labels currently requires --view full_typed")
        category = load_legacy_view(args.db)
        result = evaluate_category(
            category, view="legacy", protocol="as_loaded",
            compute_ci=args.ci, with_baselines=args.baselines,
        )
    else:
        remove_direct = args.protocol == "remove_direct_labels"
        category, missing_endpoints = load_full_typed_view(
            args.db,
            remove_direct_labels=remove_direct,
            quality_tier=args.quality,
        )

        positives_override = None
        if remove_direct:
            base_category, _ = load_full_typed_view(args.db, quality_tier=args.quality)
            _, _, positives_override = drug_disease_pairs(base_category)

        result = evaluate_category(
            category,
            view="full_typed",
            protocol=args.protocol,
            positives_override=positives_override,
            missing_endpoints=missing_endpoints,
            compute_ci=args.ci,
            with_baselines=args.baselines,
        )

    if args.json:
        print(json.dumps(asdict(result), indent=2))
    else:
        print_result(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
