#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Shared helpers for executable holdout validation scripts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from validation.repurposing_benchmark import (
    compute_auprc,
    compute_hits_at_k,
    compute_mrr,
    drug_disease_pairs,
    make_strategies,
    pairwise_auroc,
    score_pair,
)


@dataclass(frozen=True)
class HoldoutMetrics:
    name: str
    n_positives: int
    n_negatives: int
    auroc: float
    auprc: float
    hits_at_5: float
    hits_at_10: float
    hits_at_20: float
    mrr: float
    scored_pairs: int
    positive_scores: list[tuple[str, str, float]]
    top_ranked: list[tuple[str, str, float, int]]


def score_pairs(category, pairs: Iterable[tuple[str, str]]) -> dict[tuple[str, str], float]:
    """Score pairs with the corrected research-grade scorer."""
    strategies = make_strategies(category)
    scores: dict[tuple[str, str], float] = {}
    for drug, disease in sorted(set(pairs)):
        score, _ = score_pair(strategies, drug, disease, fail_on_error=True)
        scores[(drug, disease)] = score
    return scores


def evaluate_holdout(
    category,
    positive_pairs: set[tuple[str, str]],
    candidate_pairs: Iterable[tuple[str, str]] | None = None,
    *,
    name: str = "holdout",
    exclude_pairs: set[tuple[str, str]] | None = None,
) -> HoldoutMetrics:
    """Evaluate arbitrary positive pairs against open-world unlabeled negatives."""
    drugs, diseases, _ = drug_disease_pairs(category)
    if candidate_pairs is None:
        candidate_pairs = [(drug, disease) for drug in drugs for disease in diseases]

    exclude_pairs = exclude_pairs or set()
    pairs = sorted(
        set(candidate_pairs)
        - (exclude_pairs - positive_pairs)
    )
    labels = [1 if pair in positive_pairs else 0 for pair in pairs]
    scores_by_pair = score_pairs(category, pairs)
    scores = [scores_by_pair[pair] for pair in pairs]

    auroc, _, _, _ = pairwise_auroc(scores, labels)
    auprc = compute_auprc(scores, labels)
    hits5 = compute_hits_at_k(scores, labels, 5)
    hits10 = compute_hits_at_k(scores, labels, 10)
    hits20 = compute_hits_at_k(scores, labels, 20)
    mrr = compute_mrr(scores, labels)

    ranked = sorted(
        [(drug, disease, scores_by_pair[(drug, disease)], labels[i])
         for i, (drug, disease) in enumerate(pairs)],
        key=lambda row: -row[2],
    )
    top_ranked = ranked[:20]
    positive_scores = sorted(
        [(drug, disease, scores_by_pair[(drug, disease)])
         for drug, disease in positive_pairs],
        key=lambda row: row[2],
    )

    return HoldoutMetrics(
        name=name,
        n_positives=sum(labels),
        n_negatives=len(labels) - sum(labels),
        auroc=auroc,
        auprc=auprc,
        hits_at_5=hits5,
        hits_at_10=hits10,
        hits_at_20=hits20,
        mrr=mrr,
        scored_pairs=len(scores),
        positive_scores=positive_scores,
        top_ranked=top_ranked,
    )


def print_metrics(metrics: HoldoutMetrics) -> None:
    """Print a stable text report for validation scripts."""
    print(f"Scenario:   {metrics.name}")
    print(f"Labels:     {metrics.n_positives} positives, {metrics.n_negatives} negatives")
    print(f"Scored:     {metrics.scored_pairs} pairs")
    print(f"AUROC:      {metrics.auroc:.6f}")
    print(f"AUPRC:      {metrics.auprc:.6f}")
    print(f"Hits@5:     {metrics.hits_at_5:.4f}")
    print(f"Hits@10:    {metrics.hits_at_10:.4f}")
    print(f"Hits@20:    {metrics.hits_at_20:.4f}")
    print(f"MRR:        {metrics.mrr:.6f}")
    print("Positive scores:")
    for drug, disease, score in metrics.positive_scores:
        print(f"  {drug:24s} {disease:24s} {score:.6f}")
    print("Top ranked:")
    for drug, disease, score, label in metrics.top_ranked:
        flag = "POS" if label else "NEG"
        print(f"  {score:.6f}  {flag:3s}  {drug:24s} {disease}")
