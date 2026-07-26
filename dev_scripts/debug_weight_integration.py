"""
Debug why integrated weights give 0.81 instead of 0.84
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from oracle.prediction import Prediction, PredictionType

# Test that merge_with() is loading weights correctly
print("=" * 70)
print("DEBUGGING WEIGHT INTEGRATION")
print("=" * 70)

# Check if weights file exists
weights_file = Path("data/strategy_weights.json")
if weights_file.exists():
    import json
    data = json.loads(weights_file.read_text())
    print("\nWeights from file:")
    for name, cal in data['calibrations'].items():
        print(f"  {name:30s} weight={cal['weight']:.3f}")
else:
    print("\nERROR: data/strategy_weights.json not found!")
    sys.exit(1)

# Test merge_with() with two predictions
print("\n" + "=" * 70)
print("TESTING merge_with() METHOD")
print("=" * 70)

pred1 = Prediction(
    source="Imatinib",
    target="CML",
    predicted_relation="treats",
    prediction_type=PredictionType.KAN_EXTENSION,
    strategy_name="kan_extension",
    confidence=0.8,
    reasoning="Test"
)

pred2 = Prediction(
    source="Imatinib",
    target="CML",
    predicted_relation="treats",
    prediction_type=PredictionType.TYPE_CONSTRAINED,
    strategy_name="composition",
    confidence=0.6,
    reasoning="Test"
)

print("\nPrediction 1:")
print(f"  Strategy: {pred1.strategy_name}, Confidence: {pred1.confidence}")

print("\nPrediction 2:")
print(f"  Strategy: {pred2.strategy_name}, Confidence: {pred2.confidence}")

# Merge them
merged = pred1.merge_with(pred2)

print("\nMerged prediction:")
print(f"  Strategy: {merged.strategy_name}")
print(f"  Confidence: {merged.confidence:.4f}")

# Calculate what it SHOULD be with calibrated weights
# kan_extension weight: 0.113
# composition weight: 0.000
expected = (0.113 * 0.8 + 0.000 * 0.6) / (0.113 + 0.000) if (0.113 + 0.000) > 0 else (0.8 + 0.6) / 2
print(f"\nExpected confidence (calibrated): {expected:.4f}")

# Calculate simple average
simple_avg = (0.8 + 0.6) / 2
print(f"Simple average (old method):      {simple_avg:.4f}")

print("\n" + "=" * 70)
if abs(merged.confidence - expected) < 0.01:
    print("✓ merge_with() is using calibrated weights correctly!")
else:
    print("✗ merge_with() is NOT using calibrated weights!")
    print(f"  Expected: {expected:.4f}")
    print(f"  Got:      {merged.confidence:.4f}")
print("=" * 70)
