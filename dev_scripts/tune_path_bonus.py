"""
Tune the path bonus and composition parameters.

The LOOCV calibration showed:
- Simple average = best weight scheme (0.9451 AUROC)
- Composition has 97.7% recall but -0.047 separation
- The path bonus (+0.03 per path, max +0.10) is the key differentiator

This script grid-searches for optimal path bonus parameters
and composition confidence scaling.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from validation.repurposing_benchmark import (
    load_full_typed_view, make_strategies, drug_disease_pairs, DB_PATH
)
from oracle.prediction import Prediction
import json


def score_pair_tuned(strategies, source, target, per_path_bonus, max_bonus, composition_weight=1.0):
    """Score with tunable path bonus parameters."""
    votes = []
    composition_count = 0

    for strategy in strategies:
        try:
            preds = strategy.predict(source, target)
        except Exception:
            preds = []
        if preds:
            best = max(preds, key=lambda p: p.confidence)
            if strategy.name == "composition":
                # Apply composition weight to its confidence
                votes.append((strategy.name, best.confidence * composition_weight))
                composition_count = len(preds)
            else:
                votes.append((strategy.name, best.confidence))

    if not votes:
        return 0.0

    base = sum(c for _, c in votes) / len(votes)
    path_bonus = min(max_bonus, per_path_bonus * composition_count)
    return min(1.0, base + path_bonus)


def run_loocv_tuned(per_path_bonus, max_bonus, composition_weight=1.0, db_path=DB_PATH):
    """Run LOOCV with tuned parameters."""
    base_category, _ = load_full_typed_view(db_path)
    drugs, diseases, positives = drug_disease_pairs(base_category)
    negatives = [(d, dis) for d in drugs for dis in diseases if (d, dis) not in positives]

    concordant = 0
    discordant = 0
    tied = 0

    for held_pair in sorted(positives):
        fold_category, _ = load_full_typed_view(db_path, skip_pair=held_pair)
        strategies = make_strategies(fold_category)

        held_score = score_pair_tuned(strategies, *held_pair, per_path_bonus, max_bonus, composition_weight)

        for neg in negatives:
            neg_score = score_pair_tuned(strategies, *neg, per_path_bonus, max_bonus, composition_weight)
            if held_score > neg_score:
                concordant += 1
            elif held_score < neg_score:
                discordant += 1
            else:
                tied += 1

    total = concordant + discordant + tied
    return (concordant + 0.5 * tied) / total if total else 0.5


def main():
    print("=" * 70)
    print("PATH BONUS & COMPOSITION TUNING")
    print("=" * 70)

    # Current parameters
    print("\nCurrent: per_path=0.03, max_bonus=0.10, composition_weight=1.0")
    print("Current AUROC: 0.945")

    # Grid search
    configs = [
        # (per_path_bonus, max_bonus, composition_weight, name)
        (0.03, 0.10, 1.0, "BASELINE (current)"),
        (0.05, 0.15, 1.0, "boost path bonus"),
        (0.07, 0.20, 1.0, "strong path bonus"),
        (0.03, 0.10, 0.8, "reduce composition conf"),
        (0.05, 0.15, 0.8, "boost path + reduce comp"),
        (0.10, 0.25, 1.0, "aggressive path bonus"),
        (0.03, 0.05, 1.0, "cap path bonus low"),
        (0.02, 0.08, 1.0, "subtle path bonus"),
        (0.05, 0.10, 1.2, "boost both"),
    ]

    results = []
    for per_path, max_b, comp_w, name in configs:
        print(f"\n  Testing: {name} (per_path={per_path}, max={max_b}, comp_w={comp_w})...")
        auroc = run_loocv_tuned(per_path, max_b, comp_w)
        results.append((name, auroc, per_path, max_b, comp_w))
        delta = auroc - 0.945
        print(f"    AUROC: {auroc:.4f} ({delta:+.4f})")

    # Summary
    results.sort(key=lambda x: x[1], reverse=True)
    print(f"\n{'='*70}")
    print(f"RESULTS (sorted by AUROC)")
    print(f"{'='*70}")

    for name, auroc, pp, mb, cw in results:
        delta = auroc - 0.945
        marker = " <-- BEST" if auroc == results[0][1] else ""
        print(f"  {name:35s} {auroc:.4f} ({delta:+.4f}) pp={pp} max={mb} cw={cw}{marker}")

    best = results[0]
    print(f"\n  Best config: {best[0]}")
    print(f"  Best AUROC:  {best[1]:.4f}")
    print(f"  vs Baseline: {best[1] - 0.945:+.4f}")

    if best[1] > 0.945:
        print(f"\n  IMPROVEMENT FOUND!")
        print(f"  Update validation/repurposing_benchmark.py line 195:")
        print(f"    path_bonus = min({best[3]}, {best[2]} * composition_count)")
    else:
        print(f"\n  Current parameters are already optimal.")
        print(f"  The simple average + path bonus is well-tuned.")

    # Save results
    output = {
        "tuning_results": [
            {"name": n, "auroc": a, "per_path": pp, "max_bonus": mb, "comp_weight": cw}
            for n, a, pp, mb, cw in results
        ],
        "best_config": {
            "name": best[0],
            "auroc": best[1],
            "per_path_bonus": best[2],
            "max_bonus": best[3],
            "composition_weight": best[4],
        }
    }

    Path("data/tuning_results.json").write_text(json.dumps(output, indent=2))
    print(f"\n  Saved to data/tuning_results.json")


if __name__ == "__main__":
    main()
