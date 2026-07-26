"""
Check for data leakage: does topos_logic use the ground truth edges
in its predictions?
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from domains.bio import BioDomainLoader
from oracle.topos_strategy import ToposLogicStrategy

loader = BioDomainLoader()
category = loader.load_tier1("data/drugs/tier1.db")

strategy = ToposLogicStrategy(category)

# Test a TRUE pair (Imatinib -> CML)
print("=== Test 1: TRUE pair (Imatinib -> CML) ===")
preds = strategy.predict("Imatinib", "CML")
for pred in preds:
    print(f"  Relation: {pred.predicted_relation}")
    print(f"  Confidence: {pred.confidence:.3f}")
    print(f"  Truth type: {pred.evidence.get('truth_type', 'unknown')}")
    print(f"  Reasoning: {pred.reasoning}")
    print()

# Test a FALSE pair with pathways (Gefitinib -> NSCLC)
print("=== Test 2: FALSE pair with pathway (Gefitinib -> NSCLC) ===")
preds = strategy.predict("Gefitinib", "NSCLC")
for pred in preds:
    print(f"  Relation: {pred.predicted_relation}")
    print(f"  Confidence: {pred.confidence:.3f}")
    print(f"  Truth type: {pred.evidence.get('truth_type', 'unknown')}")
    print(f"  Reasoning: {pred.reasoning}")
    print()

# Test a FALSE pair with no pathway
print("=== Test 3: FALSE pair, no pathway (Aspirin -> CML) ===")
preds = strategy.predict("Aspirin", "CML")
for pred in preds:
    print(f"  Relation: {pred.predicted_relation}")
    print(f"  Confidence: {pred.confidence:.3f}")
    print(f"  Truth type: {pred.evidence.get('truth_type', 'unknown')}")
    print(f"  Reasoning: {pred.reasoning}")
    print()
if not preds:
    print("  (No predictions)")
    print()

# DATA LEAKAGE CHECK
print("=" * 70)
print("DATA LEAKAGE ANALYSIS")
print("=" * 70)
print()
print("CRITICAL QUESTION: Does topos_logic use the 'treats' edges")
print("(ground truth) during prediction?")
print()
print("ANSWER: YES.")
print()
print("The _has_direct_edge() method at line 164-168 checks:")
print("  for mor in self._get_morphisms():")
print("    if mor.source == source and mor.target == target:")
print("      return mor")
print()
print("This iterates ALL morphisms including the 11 'treats' edges.")
print("For true pairs, it finds the 'treats' morphism and returns")
print("its stored confidence (0.93-0.99).")
print()
print("For false pairs, it finds no direct edge, so it falls through")
print("to pathway prediction (capped at 0.70) or returns nothing.")
print()
print("This means the strategy has INFORMATION LEAKAGE: it can see")
print("the labels during prediction. True pairs always get higher")
print("scores (0.93+) because the ground truth edge is in the database.")
print()
print("A PROPER evaluation requires cross-validation: hold out some")
print("'treats' edges, remove them from the database, then try to")
print("predict them.")
