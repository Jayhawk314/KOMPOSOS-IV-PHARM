#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""
Ablation study for drug-repurposing benchmark.

Tests individual strategy contributions and path bonus impact via LOOCV.
"""

from __future__ import annotations

import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path

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

DB_PATH = "data/drugs/tier1.db"

ALL_STRATEGY_NAMES = [
    "kan_extension",
    "type_heuristic",
    "structural_hole",
    "composition",
    "yoneda_pattern",
    "fibration_lift",
    "topos_logic",
]

STRATEGY_CLASSES = {
    "kan_extension": KanExtensionStrategy,
    "type_heuristic": TypeHeuristicStrategy,
    "structural_hole": StructuralHoleStrategy,
    "composition": CompositionStrategy,
    "yoneda_pattern": YonedaPatternStrategy,
    "fibration_lift": FibrationLiftStrategy,
    "topos_logic": ToposLogicStrategy,
}


def load_full_typed_view(db_path=DB_PATH, skip_pair=None):
    store = KomposOSStore(db_path)
    objects = store.list_objects(limit=100000)
    morphisms = store.list_morphisms(limit=100000)
    type_by_name = {obj.name: obj.type_name for obj in objects}

    category = Category(name="AblationStudy")
    for obj in objects:
        category.add(obj.name, type_name=obj.type_name, metadata=obj.metadata or {}, embedding=obj.embedding)

    for mor in morphisms:
        is_dd = type_by_name.get(mor.source_name) == "Drug" and type_by_name.get(mor.target_name) == "Disease"
        if skip_pair and is_dd and (mor.source_name, mor.target_name) == skip_pair:
            continue
        category.connect(mor.source_name, mor.target_name, name=mor.name,
                         confidence=mor.confidence if mor.confidence else 1.0, **(mor.metadata or {}))

    return category, type_by_name


def drug_disease_pairs(category):
    drugs = sorted(obj.name for obj in category.objects() if obj.type_name == "Drug")
    diseases = sorted(obj.name for obj in category.objects() if obj.type_name == "Disease")
    positives = set()
    for mor in category.morphisms():
        src = category.get(mor.source)
        tgt = category.get(mor.target)
        if src and tgt and src.type_name == "Drug" and tgt.type_name == "Disease":
            positives.add((mor.source, mor.target))
    return drugs, diseases, positives


def make_strategies(category, strategy_names=None):
    if strategy_names is None:
        strategy_names = ALL_STRATEGY_NAMES
    return [STRATEGY_CLASSES[name](category) for name in strategy_names if name in STRATEGY_CLASSES]


def score_pair(strategies, source, target, path_bonus_enabled=True, path_bonus_per=0.10, path_bonus_cap=0.25):
    votes = []
    composition_count = 0
    for strategy in strategies:
        try:
            preds = strategy.predict(source, target)
        except Exception:
            preds = []
        if preds:
            best = max(preds, key=lambda p: p.confidence)
            votes.append((strategy.name, best.confidence))
            if strategy.name == "composition":
                composition_count = len(preds)

    if not votes:
        return 0.0, votes

    base = sum(c for _, c in votes) / len(votes)
    if path_bonus_enabled:
        path_bonus = min(path_bonus_cap, path_bonus_per * composition_count)
    else:
        path_bonus = 0.0
    return min(1.0, base + path_bonus), votes


def pairwise_auroc(scores, labels):
    true_scores = [s for s, l in zip(scores, labels) if l == 1]
    false_scores = [s for s, l in zip(scores, labels) if l == 0]
    concordant = discordant = tied = 0
    for ts in true_scores:
        for fs in false_scores:
            if ts > fs:
                concordant += 1
            elif ts < fs:
                discordant += 1
            else:
                tied += 1
    total = concordant + discordant + tied
    return (concordant + 0.5 * tied) / total if total else 0.5


def compute_auprc(scores, labels):
    paired = sorted(zip(scores, labels), key=lambda x: -x[0])
    tp = fp = 0
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


def run_loocv(db_path, strategy_names=None, path_bonus_enabled=True,
              path_bonus_per=0.10, path_bonus_cap=0.25):
    """Run LOOCV with specific strategy subset and path bonus settings."""
    base_category, _ = load_full_typed_view(db_path)
    drugs, diseases, positives = drug_disease_pairs(base_category)
    negatives = [(d, dis) for d in drugs for dis in diseases if (d, dis) not in positives]

    concordant = discordant = tied = 0
    held_scores = []

    neg_score_sums = {neg: 0.0 for neg in negatives}

    for held_pair in sorted(positives):
        fold_cat, _ = load_full_typed_view(db_path, skip_pair=held_pair)
        strategies = make_strategies(fold_cat, strategy_names)
        held_score, _ = score_pair(strategies, *held_pair, path_bonus_enabled=path_bonus_enabled,
                                   path_bonus_per=path_bonus_per, path_bonus_cap=path_bonus_cap)
        held_scores.append(held_score)

        for negative in negatives:
            neg_score, _ = score_pair(strategies, *negative, path_bonus_enabled=path_bonus_enabled,
                                     path_bonus_per=path_bonus_per, path_bonus_cap=path_bonus_cap)
            neg_score_sums[negative] += neg_score
            if held_score > neg_score:
                concordant += 1
            elif held_score < neg_score:
                discordant += 1
            else:
                tied += 1

    total = concordant + discordant + tied
    auroc = (concordant + 0.5 * tied) / total if total else 0.5

    n_folds = len(positives)
    all_scores = list(held_scores)
    all_labels = [1] * len(held_scores)
    for neg, ss in neg_score_sums.items():
        all_scores.append(ss / n_folds)
        all_labels.append(0)

    auprc = compute_auprc(all_scores, all_labels)
    return auroc, auprc, len(positives), len(negatives)


def run_single_eval(db_path, strategy_names=None, path_bonus_enabled=True,
                    path_bonus_per=0.10, path_bonus_cap=0.25, protocol="remove_direct_labels"):
    """Run remove_direct_labels evaluation (faster than LOOCV)."""
    base_category, _ = load_full_typed_view(db_path)
    _, _, positives = drug_disease_pairs(base_category)

    eval_cat, _ = load_full_typed_view(db_path)
    # For remove_direct_labels, load without Drug->Disease edges
    if protocol == "remove_direct_labels":
        store = KomposOSStore(db_path)
        objects = store.list_objects(limit=100000)
        morphisms = store.list_morphisms(limit=100000)
        type_by_name = {obj.name: obj.type_name for obj in objects}
        eval_cat = Category(name="AblationEval")
        for obj in objects:
            eval_cat.add(obj.name, type_name=obj.type_name, metadata=obj.metadata or {}, embedding=obj.embedding)
        for mor in morphisms:
            is_dd = type_by_name.get(mor.source_name) == "Drug" and type_by_name.get(mor.target_name) == "Disease"
            if is_dd:
                continue
            eval_cat.connect(mor.source_name, mor.target_name, name=mor.name,
                             confidence=mor.confidence if mor.confidence else 1.0, **(mor.metadata or {}))

    drugs, diseases, _ = drug_disease_pairs(base_category)
    strategies = make_strategies(eval_cat, strategy_names)

    scores = []
    labels = []
    for drug in drugs:
        for disease in diseases:
            score, _ = score_pair(strategies, drug, disease, path_bonus_enabled=path_bonus_enabled,
                                  path_bonus_per=path_bonus_per, path_bonus_cap=path_bonus_cap)
            scores.append(score)
            labels.append(1 if (drug, disease) in positives else 0)

    auroc = pairwise_auroc(scores, labels)
    auprc = compute_auprc(scores, labels)
    return auroc, auprc, sum(labels), len(labels) - sum(labels)


def main():
    print("=" * 70)
    print("ABLATION STUDY: KOMPOSOS-IV-PHARM Drug Repurposing")
    print("=" * 70)
    print()

    results = {}

    # 1. Full system baseline (remove_direct_labels -- faster)
    print("[1/12] Full system (remove_direct_labels) ...")
    t0 = time.time()
    auroc, auprc, pos, neg = run_single_eval(DB_PATH, strategy_names=None, path_bonus_enabled=True)
    results["full_system"] = {"auroc": round(auroc, 6), "auprc": round(auprc, 6), "positives": pos, "negatives": neg}
    print(f"  AUROC={auroc:.4f}  AUPRC={auprc:.4f}  ({time.time()-t0:.1f}s)")

    # 2. Full system without path bonus
    print("[2/12] Full system, NO path bonus ...")
    t0 = time.time()
    auroc, auprc, pos, neg = run_single_eval(DB_PATH, strategy_names=None, path_bonus_enabled=False)
    results["no_path_bonus"] = {"auroc": round(auroc, 6), "auprc": round(auprc, 6), "positives": pos, "negatives": neg}
    print(f"  AUROC={auroc:.4f}  AUPRC={auprc:.4f}  ({time.time()-t0:.1f}s)")

    # 3. Each strategy in isolation
    for i, name in enumerate(ALL_STRATEGY_NAMES):
        print(f"[{3+i}/12] Strategy: {name} only ...")
        t0 = time.time()
        auroc, auprc, pos, neg = run_single_eval(DB_PATH, strategy_names=[name],
                                                  path_bonus_enabled=(name == "composition"))
        results[f"only_{name}"] = {"auroc": round(auroc, 6), "auprc": round(auprc, 6), "positives": pos, "negatives": neg}
        print(f"  AUROC={auroc:.4f}  AUPRC={auprc:.4f}  ({time.time()-t0:.1f}s)")

    # 4. Leave-one-out ablation (remove each strategy one at a time)
    print()
    print("-" * 70)
    print("LEAVE-ONE-OUT ABLATION (remove each strategy, keep rest + path bonus)")
    print("-" * 70)

    for name in ALL_STRATEGY_NAMES:
        remaining = [n for n in ALL_STRATEGY_NAMES if n != name]
        label = f"without_{name}"
        print(f"  Without {name} ...")
        t0 = time.time()
        auroc, auprc, pos, neg = run_single_eval(DB_PATH, strategy_names=remaining, path_bonus_enabled=True)
        results[label] = {"auroc": round(auroc, 6), "auprc": round(auprc, 6), "positives": pos, "negatives": neg}
        print(f"    AUROC={auroc:.4f}  AUPRC={auprc:.4f}  ({time.time()-t0:.1f}s)")

    # 5. Composition-only (the strongest individual should be this)
    print()
    print("-" * 70)
    print("COMPOSITION-ONLY WITH VARYING PATH BONUS")
    print("-" * 70)

    for per, cap in [(0.0, 0.0), (0.05, 0.15), (0.10, 0.25), (0.15, 0.35), (0.20, 0.50)]:
        label = f"composition_pb_{per}_{cap}"
        enabled = per > 0
        print(f"  Composition only, path_bonus per={per} cap={cap} ...")
        t0 = time.time()
        auroc, auprc, pos, neg = run_single_eval(DB_PATH, strategy_names=["composition"],
                                                  path_bonus_enabled=enabled,
                                                  path_bonus_per=per, path_bonus_cap=cap)
        results[label] = {"auroc": round(auroc, 6), "auprc": round(auprc, 6), "positives": pos, "negatives": neg}
        print(f"    AUROC={auroc:.4f}  AUPRC={auprc:.4f}  ({time.time()-t0:.1f}s)")

    # Summary
    print()
    print("=" * 70)
    print("SUMMARY TABLE")
    print("=" * 70)
    print(f"{'Configuration':<45s} {'AUROC':>8s} {'AUPRC':>8s} {'Delta':>8s}")
    print("-" * 70)
    full_auroc = results["full_system"]["auroc"]
    for label, data in results.items():
        delta = data["auroc"] - full_auroc
        delta_str = f"{delta:+.4f}" if label != "full_system" else "  base"
        print(f"{label:<45s} {data['auroc']:>8.4f} {data['auprc']:>8.4f} {delta_str:>8s}")

    # Save results
    out_path = Path(__file__).parent / "ablation_results.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to {out_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
