"""
Clean AUROC confirmation test.
Uses only the 6 working strategies, properly handles missing predictions.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from domains.bio import BioDomainLoader
from oracle.strategies import (
    CompositionStrategy, TypeHeuristicStrategy,
    YonedaPatternStrategy, StructuralHoleStrategy,
    KanExtensionStrategy, FibrationLiftStrategy
)
from oracle.calibration import StrategyCalibrator, weighted_average
import json


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
    print("AUROC CONFIRMATION TEST")
    print("=" * 70)

    # Load data
    print("\n[1/3] Loading tier1.db...")
    loader = BioDomainLoader()
    category = loader.load_tier1("data/drugs/tier1.db")

    drugs = [obj for obj in category.objects() if obj.type_name == "Drug"]
    diseases = [obj for obj in category.objects() if obj.type_name == "Disease"]

    # Find ground truth
    dd_edges = set()
    for mor in category.morphisms():
        src = category.get(mor.source)
        tgt = category.get(mor.target)
        if src and tgt and src.type_name == "Drug" and tgt.type_name == "Disease":
            dd_edges.add((mor.source, mor.target))

    print(f"  {len(drugs)} drugs, {len(diseases)} diseases")
    print(f"  {len(dd_edges)} true Drug->Disease edges")
    print(f"  {len(drugs) * len(diseases)} total pairs to score")

    # Create strategies (only the 6 that work without embeddings)
    strategies = [
        CompositionStrategy(category),
        TypeHeuristicStrategy(category),
        YonedaPatternStrategy(category),
        StructuralHoleStrategy(category),
        KanExtensionStrategy(category),
        FibrationLiftStrategy(category),
    ]

    print(f"\n[2/3] Using {len(strategies)} strategies")

    # Score all pairs
    all_pairs = []
    for drug in drugs:
        for disease in diseases:
            pair = (drug.name, disease.name)
            label = 1 if pair in dd_edges else 0

            # Collect votes
            votes = []
            for strategy in strategies:
                try:
                    preds = strategy.predict(drug.name, disease.name)
                    if preds:
                        best = max(preds, key=lambda p: p.confidence)
                        votes.append((strategy.name, best.confidence))
                except:
                    pass

            # Only include pairs with at least one prediction
            if votes:
                baseline_score = sum(c for _, c in votes) / len(votes)
                all_pairs.append({
                    'label': label,
                    'baseline_score': baseline_score,
                    'votes': votes
                })

    print(f"  Scored {len(all_pairs)}/{len(drugs) * len(diseases)} pairs")

    # Baseline AUROC
    baseline_scores = [p['baseline_score'] for p in all_pairs]
    labels = [p['label'] for p in all_pairs]
    baseline_auroc = compute_auroc(baseline_scores, labels)

    print(f"\n  BASELINE (simple average): {baseline_auroc:.4f}")

    # Load calibrated weights
    print("\n[3/3] Testing calibrated weights...")

    if Path("data/strategy_weights.json").exists():
        calibrator = StrategyCalibrator("data/strategy_weights.json")

        # Re-score with calibration
        calibrated_scores = []
        for pair_data in all_pairs:
            calibrated_score = weighted_average(pair_data['votes'], calibrator)
            calibrated_scores.append(calibrated_score)

        calibrated_auroc = compute_auroc(calibrated_scores, labels)

        print(f"  CALIBRATED (weighted avg): {calibrated_auroc:.4f}")
        print(f"  Improvement: +{(calibrated_auroc - baseline_auroc):.4f}")
    else:
        print("  No calibration file found - run calibrate_and_measure.py first")

    print("\n" + "=" * 70)
    print("CONFIRMED AUROC:")
    print(f"  Baseline:   {baseline_auroc:.4f}")
    if Path("data/strategy_weights.json").exists():
        print(f"  Calibrated: {calibrated_auroc:.4f}  (+{(calibrated_auroc - baseline_auroc):.4f})")
    print("=" * 70)


if __name__ == "__main__":
    main()
