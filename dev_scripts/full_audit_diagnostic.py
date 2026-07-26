"""
Full end-to-end diagnostic for AUROC verification audit.
Captures every intermediate value for external reproducibility.
"""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from domains.bio import BioDomainLoader
from oracle.strategies import KanExtensionStrategy, TypeHeuristicStrategy, StructuralHoleStrategy, CompositionStrategy, YonedaPatternStrategy, FibrationLiftStrategy
from oracle.topos_strategy import ToposLogicStrategy
from oracle.calibration import StrategyCalibrator, weighted_average

print("=" * 90)
print("KOMPOSOS-IV-PHARM: FULL AUROC VERIFICATION DIAGNOSTIC")
print("=" * 90)

# --- SECTION 1: DATA LOADING ---
print("\n[SECTION 1] DATA LOADING")
print("-" * 90)

loader = BioDomainLoader()
category = loader.load_tier1("data/drugs/tier1.db")

all_objects = list(category.objects())
all_morphisms = list(category.morphisms())
drugs = [obj for obj in all_objects if obj.type_name == "Drug"]
diseases = [obj for obj in all_objects if obj.type_name == "Disease"]

print(f"  Total objects:    {len(all_objects)}")
print(f"  Total morphisms:  {len(all_morphisms)}")
print(f"  Drugs:            {len(drugs)}")
print(f"  Diseases:         {len(diseases)}")
print(f"  Drug names:       {sorted([d.name for d in drugs])}")
print(f"  Disease names:    {sorted([d.name for d in diseases])}")

# Ground truth edges
dd_edges = set()
for mor in all_morphisms:
    src = category.get(mor.source)
    tgt = category.get(mor.target)
    if src and tgt and src.type_name == "Drug" and tgt.type_name == "Disease":
        dd_edges.add((mor.source, mor.target))
        print(f"  Ground truth edge: {mor.source} -> {mor.target} (confidence={mor.confidence:.3f}, name='{mor.name}')")

print(f"  Ground truth count: {len(dd_edges)}")
print(f"  Total possible Drug x Disease pairs: {len(drugs)} x {len(diseases)} = {len(drugs) * len(diseases)}")
print(f"  Negative pairs: {len(drugs) * len(diseases) - len(dd_edges)}")

# --- SECTION 2: STRATEGY LOADING ---
print("\n[SECTION 2] STRATEGY LOADING")
print("-" * 90)

strategies = [
    KanExtensionStrategy(category),
    TypeHeuristicStrategy(category),
    StructuralHoleStrategy(category),
    CompositionStrategy(category),
    YonedaPatternStrategy(category),
    FibrationLiftStrategy(category),
    ToposLogicStrategy(category),
]

for s in strategies:
    print(f"  Loaded: {s.name} ({s.__class__.__name__})")

# --- SECTION 3: RAW PREDICTION COLLECTION ---
print("\n[SECTION 3] RAW PREDICTION COLLECTION")
print("-" * 90)

all_pair_data = []
strategy_stats = {s.name: {"total": 0, "correct": 0, "confidences": []} for s in strategies}

for drug in drugs:
    for disease in diseases:
        pair = (drug.name, disease.name)
        is_true = pair in dd_edges

        votes = []
        strategy_details = {}
        for strategy in strategies:
            try:
                preds = strategy.predict(drug.name, disease.name)
                if preds:
                    best = max(preds, key=lambda p: p.confidence)
                    votes.append((strategy.name, best.confidence))
                    strategy_details[strategy.name] = {
                        "confidence": best.confidence,
                        "relation": best.predicted_relation,
                        "truth_type": best.evidence.get("truth_type", "unknown") if best.evidence else "unknown"
                    }
                    strategy_stats[strategy.name]["total"] += 1
                    strategy_stats[strategy.name]["confidences"].append(best.confidence)
                    if is_true:
                        strategy_stats[strategy.name]["correct"] += 1
            except Exception as e:
                pass

        if votes:
            simple_avg = sum(c for _, c in votes) / len(votes)
            all_pair_data.append({
                "drug": drug.name,
                "disease": disease.name,
                "label": 1 if is_true else 0,
                "simple_avg_score": simple_avg,
                "n_votes": len(votes),
                "votes": votes,
                "strategy_details": strategy_details,
            })

# Pairs with no predictions
no_pred_pairs = []
for drug in drugs:
    for disease in diseases:
        if not any(p["drug"] == drug.name and p["disease"] == disease.name for p in all_pair_data):
            no_pred_pairs.append((drug.name, disease.name))

print(f"  Pairs WITH at least 1 prediction: {len(all_pair_data)}")
print(f"  Pairs WITHOUT any prediction:     {len(no_pred_pairs)}")
print(f"  True pairs with predictions:      {sum(1 for p in all_pair_data if p['label'] == 1)}")
print(f"  True pairs without predictions:   {sum(1 for d, dis in no_pred_pairs if (d, dis) in dd_edges)}")

print(f"\n  Per-strategy statistics:")
for name, stats in sorted(strategy_stats.items(), key=lambda x: -x[1]["correct"]):
    total = stats["total"]
    correct = stats["correct"]
    precision = correct / total if total > 0 else 0.0
    avg_conf = sum(stats["confidences"]) / len(stats["confidences"]) if stats["confidences"] else 0.0
    print(f"    {name:25s}: {total:4d} predictions, {correct:3d} correct, precision={precision:.4f}, avg_conf={avg_conf:.3f}")

# --- SECTION 4: SIMPLE AVERAGE AUROC ---
print("\n[SECTION 4] SIMPLE AVERAGE AUROC (BASELINE)")
print("-" * 90)

labels = [p["label"] for p in all_pair_data]
simple_scores = [p["simple_avg_score"] for p in all_pair_data]

# Manual AUROC via pairwise comparison (Wilcoxon-Mann-Whitney statistic)
true_scores_list = [(p["drug"], p["disease"], p["simple_avg_score"]) for p in all_pair_data if p["label"] == 1]
false_scores_list = [(p["drug"], p["disease"], p["simple_avg_score"]) for p in all_pair_data if p["label"] == 0]

concordant = 0
discordant = 0
tied = 0
for _, _, ts in true_scores_list:
    for _, _, fs in false_scores_list:
        if ts > fs:
            concordant += 1
        elif ts < fs:
            discordant += 1
        else:
            tied += 1

total_comparisons = concordant + discordant + tied
auroc_simple = (concordant + 0.5 * tied) / total_comparisons if total_comparisons > 0 else 0.5

print(f"  True pair count:  {len(true_scores_list)}")
print(f"  False pair count: {len(false_scores_list)}")
print(f"  Total pairwise comparisons: {total_comparisons}")
print(f"  Concordant (true > false):  {concordant}")
print(f"  Discordant (true < false):  {discordant}")
print(f"  Tied (true == false):       {tied}")
print(f"  AUROC = (concordant + 0.5*tied) / total = ({concordant} + 0.5*{tied}) / {total_comparisons}")
print(f"  AUROC (simple average) = {auroc_simple:.6f}")

# --- SECTION 5: CALIBRATED AUROC ---
print("\n[SECTION 5] CALIBRATED AUROC")
print("-" * 90)

calibrator = StrategyCalibrator()
for pair_data in all_pair_data:
    is_correct = (pair_data["label"] == 1)
    for strategy_name, confidence in pair_data["votes"]:
        calibrator.record_prediction(strategy_name, confidence, is_correct, pair_data)

calibrator.calibrate()

print(f"\n  Calibration weight formula:")
print(f"    precision = n_correct / n_predictions")
print(f"    if precision > 0.5: weight = 1.0 + 2*(precision - 0.5)")
print(f"    else:               weight = 2 * precision")
print()

# Recompute calibrated scores
calibrated_scores_list = []
for pair_data in all_pair_data:
    score = weighted_average(pair_data["votes"], calibrator)
    calibrated_scores_list.append((pair_data["drug"], pair_data["disease"], score, pair_data["label"]))

true_cal = [(d, dis, s) for d, dis, s, l in calibrated_scores_list if l == 1]
false_cal = [(d, dis, s) for d, dis, s, l in calibrated_scores_list if l == 0]

concordant2 = 0
discordant2 = 0
tied2 = 0
for _, _, ts in true_cal:
    for _, _, fs in false_cal:
        if ts > fs:
            concordant2 += 1
        elif ts < fs:
            discordant2 += 1
        else:
            tied2 += 1

total2 = concordant2 + discordant2 + tied2
auroc_cal = (concordant2 + 0.5 * tied2) / total2 if total2 > 0 else 0.5

print(f"  Concordant (true > false):  {concordant2}")
print(f"  Discordant (true < false):  {discordant2}")
print(f"  Tied (true == false):       {tied2}")
print(f"  AUROC (calibrated) = {auroc_cal:.6f}")

# --- SECTION 6: DETAILED SCORE TABLE ---
print("\n[SECTION 6] FULL SCORE TABLE (sorted by calibrated score)")
print("-" * 90)

# Build full table
full_table = []
for pair_data in all_pair_data:
    cal_score = weighted_average(pair_data["votes"], calibrator)
    full_table.append({
        "drug": pair_data["drug"],
        "disease": pair_data["disease"],
        "label": pair_data["label"],
        "simple_score": pair_data["simple_avg_score"],
        "calibrated_score": cal_score,
        "n_votes": pair_data["n_votes"],
        "strategy_details": pair_data["strategy_details"],
    })

full_table.sort(key=lambda x: -x["calibrated_score"])

print(f"  {'Rank':>4} {'Drug':<20} {'Disease':<20} {'Label':>5} {'SimpleAvg':>10} {'Calibrated':>10} {'Votes':>6} {'Strategies'}")
for i, row in enumerate(full_table, 1):
    strats = ", ".join(f"{k}({v['confidence']:.2f})" for k, v in row["strategy_details"].items())
    label_str = "TRUE" if row["label"] == 1 else ""
    print(f"  {i:4d} {row['drug']:<20} {row['disease']:<20} {label_str:>5} {row['simple_score']:>10.4f} {row['calibrated_score']:>10.4f} {row['n_votes']:>6} {strats}")
    if i == 20:
        print(f"  ... ({len(full_table) - 20} more rows)")
        break

# --- SECTION 7: SEPARATION ANALYSIS ---
print(f"\n[SECTION 7] SEPARATION ANALYSIS")
print("-" * 90)

true_cal_scores = sorted([r["calibrated_score"] for r in full_table if r["label"] == 1])
false_cal_scores = sorted([r["calibrated_score"] for r in full_table if r["label"] == 0], reverse=True)

print(f"  TRUE pair calibrated scores (ascending):  {['%.4f' % s for s in true_cal_scores]}")
print(f"  FALSE pair top-10 calibrated scores:       {['%.4f' % s for s in false_cal_scores[:10]]}")
print()
print(f"  Min TRUE score:     {min(true_cal_scores):.6f}")
print(f"  Max FALSE score:    {max(false_cal_scores) if false_cal_scores else 'N/A':.6f}")
print(f"  Separation gap:     {min(true_cal_scores) - max(false_cal_scores):.6f}")
print(f"  Perfect separation: {'YES' if min(true_cal_scores) > max(false_cal_scores) else 'NO'}")

# --- SECTION 8: SUMMARY ---
print(f"\n[SECTION 8] SUMMARY")
print("=" * 90)
print(f"  Database:                  data/drugs/tier1.db")
print(f"  Objects:                   {len(all_objects)} ({len(drugs)} drugs, {len(diseases)} diseases)")
print(f"  Morphisms:                 {len(all_morphisms)}")
print(f"  Ground truth edges:        {len(dd_edges)} Drug->Disease")
print(f"  Evaluation pairs:          {len(all_pair_data)} (with predictions)")
print(f"  Skipped pairs:             {len(no_pred_pairs)} (no predictions)")
print(f"  Active strategies:         {len(strategies)}")
print(f"  AUROC (simple average):    {auroc_simple:.6f}")
print(f"  AUROC (calibrated):        {auroc_cal:.6f}")
print(f"  Separation gap:            {min(true_cal_scores) - max(false_cal_scores):.6f}")
print("=" * 90)

# Save full results to JSON for audit
audit_data = {
    "metadata": {
        "database": "data/drugs/tier1.db",
        "n_objects": len(all_objects),
        "n_morphisms": len(all_morphisms),
        "n_drugs": len(drugs),
        "n_diseases": len(diseases),
        "n_ground_truth": len(dd_edges),
        "n_evaluated_pairs": len(all_pair_data),
        "n_skipped_pairs": len(no_pred_pairs),
    },
    "ground_truth_edges": [{"drug": d, "disease": dis} for d, dis in sorted(dd_edges)],
    "strategies_used": [s.name for s in strategies],
    "strategy_stats": {name: {"total": stats["total"], "correct": stats["correct"], "precision": stats["correct"]/max(stats["total"],1)} for name, stats in strategy_stats.items()},
    "auroc_simple_average": auroc_simple,
    "auroc_calibrated": auroc_cal,
    "pairwise_comparisons": {
        "simple": {"concordant": concordant, "discordant": discordant, "tied": tied, "total": total_comparisons},
        "calibrated": {"concordant": concordant2, "discordant": discordant2, "tied": tied2, "total": total2},
    },
    "separation": {
        "min_true_score": min(true_cal_scores),
        "max_false_score": max(false_cal_scores) if false_cal_scores else None,
        "gap": min(true_cal_scores) - (max(false_cal_scores) if false_cal_scores else 0),
        "perfect_separation": min(true_cal_scores) > (max(false_cal_scores) if false_cal_scores else 0),
    },
    "full_rankings": [
        {"rank": i+1, "drug": r["drug"], "disease": r["disease"], "label": r["label"],
         "simple_score": round(r["simple_score"], 6), "calibrated_score": round(r["calibrated_score"], 6),
         "n_votes": r["n_votes"]}
        for i, r in enumerate(full_table)
    ],
}

Path("data/auroc_audit_results.json").write_text(json.dumps(audit_data, indent=2))
print(f"\nFull audit data saved to: data/auroc_audit_results.json")
