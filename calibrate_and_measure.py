# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""
Calibrate strategy weights and measure AUROC improvement.

This script:
1. Loads tier1.db
2. Runs oracle on all Drug->Disease pairs
3. Learns per-strategy weights
4. Re-scores using improved combination
5. Compares AUROC: baseline vs calibrated
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from domains.bio import BioDomainLoader
from oracle import CategoricalOracle
from oracle.strategies import create_all_strategies
from oracle.calibration import StrategyCalibrator, weighted_average
from oracle.score_combination import ImprovedScoreCombiner, extract_path_features_from_category
from data import EmbeddingsEngine
import numpy as np


def compute_auroc(scores, labels):
    """Compute AUROC manually."""
    pairs = sorted(zip(scores, labels), key=lambda x: x[0], reverse=True)
    n_pos = sum(labels)
    n_neg = len(labels) - n_pos

    if n_pos == 0 or n_neg == 0:
        return 0.5

    tp = fp = 0
    prev_fpr = prev_tpr = 0.0
    auroc = 0.0

    for score, label in pairs:
        if label == 1:
            tp += 1
        else:
            fp += 1

        tpr = tp / n_pos
        fpr = fp / n_neg
        auroc += (fpr - prev_fpr) * (tpr + prev_tpr) / 2.0
        prev_fpr = fpr
        prev_tpr = tpr

    auroc += (1.0 - prev_fpr) * (1.0 + prev_tpr) / 2.0
    return auroc


def main():
    print("=" * 70)
    print("STRATEGY CALIBRATION & AUROC MEASUREMENT")
    print("=" * 70)

    # Load data
    print("\n[1/6] Loading tier1.db...")
    loader = BioDomainLoader()
    category = loader.load_tier1("data/drugs/tier1.db")

    drugs = [obj for obj in category.objects() if obj.type_name == "Drug"]
    diseases = [obj for obj in category.objects() if obj.type_name == "Disease"]
    print(f"  {len(drugs)} drugs × {len(diseases)} diseases = {len(drugs) * len(diseases)} pairs")

    # Find ground truth
    dd_edges = set()
    for mor in category.morphisms():
        src = category.get(mor.source)
        tgt = category.get(mor.target)
        if src and tgt and src.type_name == "Drug" and tgt.type_name == "Disease":
            dd_edges.add((mor.source, mor.target))

    print(f"  Ground truth: {len(dd_edges)} Drug->Disease edges")

    # Create oracle (without requiring embeddings for all strategies)
    print("\n[2/6] Creating Oracle...")
    try:
        engine = EmbeddingsEngine()
        strategies = create_all_strategies(category, engine)
    except:
        print("  WARNING: Some strategies failed to load (embeddings not available)")
        # Fallback: create basic strategies that don't need embeddings
        from oracle.strategies import (
            CompositionStrategy, TypeHeuristicStrategy,
            YonedaPatternStrategy, StructuralHoleStrategy,
            KanExtensionStrategy, FibrationLiftStrategy
        )
        engine = None
        strategies = [
            CompositionStrategy(category),
            TypeHeuristicStrategy(category),
            YonedaPatternStrategy(category),
            StructuralHoleStrategy(category),
            KanExtensionStrategy(category),
            FibrationLiftStrategy(category),
        ]

    print(f"  Loaded {len(strategies)} strategies:")
    for s in strategies:
        print(f"    - {s.name}")

    # Score all pairs and collect per-strategy votes
    print(f"\n[3/6] Scoring all {len(drugs) * len(diseases)} pairs...")
    all_pairs = []
    strategy_votes_per_pair = {}  # (drug, disease) -> [(strategy, confidence), ...]

    for drug in drugs:
        for disease in diseases:
            pair = (drug.name, disease.name)
            label = 1 if pair in dd_edges else 0

            # Collect votes from each strategy
            votes = []
            for strategy in strategies:
                try:
                    preds = strategy.predict(drug.name, disease.name)
                    if preds:
                        # Take highest confidence prediction
                        best_pred = max(preds, key=lambda p: p.confidence)
                        votes.append((strategy.name, best_pred.confidence))
                except Exception as e:
                    pass  # Strategy failed, skip

            if votes:
                # Simple average (baseline)
                baseline_score = sum(conf for _, conf in votes) / len(votes)
                all_pairs.append({
                    'pair': pair,
                    'label': label,
                    'baseline_score': baseline_score,
                    'votes': votes
                })
                strategy_votes_per_pair[pair] = votes

    print(f"  Got predictions for {len(all_pairs)} pairs")

    # Baseline AUROC
    baseline_scores = [p['baseline_score'] for p in all_pairs]
    labels = [p['label'] for p in all_pairs]
    baseline_auroc = compute_auroc(baseline_scores, labels)

    print(f"\n  BASELINE AUROC (simple average): {baseline_auroc:.4f}")

    # Calibrate strategies
    print("\n[4/6] Calibrating per-strategy weights...")
    calibrator = StrategyCalibrator()

    for pair_data in all_pairs:
        pair = pair_data['pair']
        is_correct = (pair_data['label'] == 1)

        for strategy_name, confidence in pair_data['votes']:
            calibrator.record_prediction(strategy_name, confidence, is_correct, pair)

    calibrator.calibrate()
    calibrator.save("data/strategy_weights.json")

    # Re-score using calibrated weights
    print("\n[5/6] Re-scoring with calibrated weights...")
    calibrated_scores = []

    for pair_data in all_pairs:
        votes = pair_data['votes']
        calibrated_score = weighted_average(votes, calibrator)
        calibrated_scores.append(calibrated_score)

    calibrated_auroc = compute_auroc(calibrated_scores, labels)
    print(f"  CALIBRATED AUROC (weighted average): {calibrated_auroc:.4f}")
    print(f"  Improvement: +{(calibrated_auroc - baseline_auroc):.4f}")

    # Re-score using improved combiner (logistic + path features)
    print("\n[6/6] Re-scoring with logistic combination + path features...")
    weights_dict = {name: cal.weight for name, cal in calibrator.calibrations.items()}
    combiner = ImprovedScoreCombiner(strategy_weights=weights_dict)

    improved_scores = []
    for pair_data in all_pairs:
        pair = pair_data['pair']
        votes_list = [{'strategy': s, 'confidence': c} for s, c in pair_data['votes']]

        # Extract path features
        path_features = extract_path_features_from_category(category, pair[0], pair[1])

        # Combine using improved method
        improved_score = combiner.combine(votes_list, path_features)
        improved_scores.append(improved_score)

    improved_auroc = compute_auroc(improved_scores, labels)
    print(f"  IMPROVED AUROC (logistic + path features): {improved_auroc:.4f}")
    print(f"  Improvement over baseline: +{(improved_auroc - baseline_auroc):.4f}")
    print(f"  Improvement over calibrated: +{(improved_auroc - calibrated_auroc):.4f}")

    # Final summary
    print("\n" + "=" * 70)
    print("FINAL RESULTS")
    print("=" * 70)
    print(f"Baseline (simple average):           {baseline_auroc:.4f}")
    print(f"Calibrated (weighted average):       {calibrated_auroc:.4f}  (+{(calibrated_auroc - baseline_auroc):.4f})")
    print(f"Improved (logistic + path features): {improved_auroc:.4f}  (+{(improved_auroc - baseline_auroc):.4f})")
    print("=" * 70)

    if improved_auroc >= 0.75:
        print("\n✓ Target AUROC (0.75+) ACHIEVED!")
    else:
        print(f"\n  Target: 0.75  (need +{(0.75 - improved_auroc):.4f} more)")


if __name__ == "__main__":
    main()
