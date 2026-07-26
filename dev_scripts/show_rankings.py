"""Show top predictions to verify ranking."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from domains.bio import BioDomainLoader
from oracle.strategies import KanExtensionStrategy, TypeHeuristicStrategy, StructuralHoleStrategy
from oracle.topos_strategy import ToposLogicStrategy

# Load data
loader = BioDomainLoader()
category = loader.load_tier1("data/drugs/tier1.db")

drugs = [obj for obj in category.objects() if obj.type_name == "Drug"]
diseases = [obj for obj in category.objects() if obj.type_name == "Disease"]

# Ground truth
dd_edges = set()
for mor in category.morphisms():
    src = category.get(mor.source)
    tgt = category.get(mor.target)
    if src and tgt and src.type_name == "Drug" and tgt.type_name == "Disease":
        dd_edges.add((mor.source, mor.target))

# Load strategies
strategies = [
    KanExtensionStrategy(category),
    TypeHeuristicStrategy(category),
    StructuralHoleStrategy(category),
    ToposLogicStrategy(category),
]

# Score all pairs
all_scores = []
for drug in drugs:
    for disease in diseases:
        pair = (drug.name, disease.name)
        is_true = pair in dd_edges

        votes = []
        for strategy in strategies:
            try:
                preds = strategy.predict(drug.name, disease.name)
                if preds:
                    best = max(preds, key=lambda p: p.confidence)
                    votes.append((strategy.name, best.confidence))
            except:
                pass

        if votes:
            score = sum(c for _, c in votes) / len(votes)
            all_scores.append((score, drug.name, disease.name, is_true, len(votes)))

# Sort by score
all_scores.sort(reverse=True)

print("TOP 20 PREDICTIONS (by score):")
print("=" * 80)
for i, (score, drug, disease, is_true, n_votes) in enumerate(all_scores[:20], 1):
    mark = "[TRUE]" if is_true else ""
    print(f"{i:2d}. {score:.3f}  {drug:20s} -> {disease:20s} {mark:8s} ({n_votes} votes)")

print("\nBOTTOM 10 TRUE PAIRS (lowest scoring true pairs):")
print("=" * 80)
true_pairs = [(s, d, dis, t, v) for s, d, dis, t, v in all_scores if t]
true_pairs.sort()
for i, (score, drug, disease, is_true, n_votes) in enumerate(true_pairs[:10], 1):
    print(f"{i:2d}. {score:.3f}  {drug:20s} -> {disease:20s} [TRUE]    ({n_votes} votes)")

print("\nTOP 10 FALSE PAIRS (highest scoring false pairs):")
print("=" * 80)
false_pairs = [(s, d, dis, t, v) for s, d, dis, t, v in all_scores if not t]
false_pairs.sort(reverse=True)
for i, (score, drug, disease, is_true, n_votes) in enumerate(false_pairs[:10], 1):
    print(f"{i:2d}. {score:.3f}  {drug:20s} -> {disease:20s}            ({n_votes} votes)")

print(f"\nSummary:")
print(f"  Lowest true score:  {true_pairs[0][0]:.3f}")
print(f"  Highest false score: {false_pairs[0][0]:.3f}")
print(f"  Gap: {true_pairs[0][0] - false_pairs[0][0]:.3f}")
