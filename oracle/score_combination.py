# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""
QUARANTINED 2026-07-31 — NON-PRODUCT, EXCLUDED FROM VALIDATION.

Not used by `validation.repurposing_benchmark`, which computes its ranking score
in `score_pair()`. No published metric depends on this module. Retained for
dependency and historical review only; do not delete without that review.

NOTHING HERE IS CALIBRATED. Every constant is hand-set, and the docstrings
suggesting otherwise ("learned from data", "after training") describe an
intention, not a state:

  - `self.coef` — the logistic intercept and all six coefficients are author-set
    "reasonable defaults". No fit was performed. `set_coefficients()` exists but
    is never called with fitted values anywhere in the repository.
  - The blend in `combine()` — 0.3/0.7 when path features exist, 0.7/0.3 when
    they do not — is also hand-set, and is the choice that actually determines
    the output.
  - `_compute_agreement()` maps variance to agreement via `1 - 4*variance`, an
    arbitrary linear rescaling of a [0, 0.25] range.

The output of `combine()` is therefore an unvalidated heuristic score in [0, 1].
It is NOT a probability, and the sigmoid in `_logistic_combine()` must not be
read as one. Calibration would require a held-out fit against the evaluation
label set, which does not yet exist (roadmap Phase 0.5).

--- original docstring follows ---

Improved score combination using logistic model + path features.

Replaces simple averaging with feature-based combination.
"""
from typing import List, Dict, Any
from dataclasses import dataclass
import numpy as np


@dataclass
class PathFeatures:
    """Features extracted from a prediction path."""
    chain_length: int = 0              # How many hops in the path
    min_confidence: float = 0.0        # Weakest link in the chain
    avg_confidence: float = 0.0        # Average confidence along path
    num_strategies: int = 0            # How many strategies voted
    strategy_agreement: float = 0.0    # Fraction of strategies that agree
    has_direct_evidence: bool = False  # Is there a direct morphism?


class ImprovedScoreCombiner:
    """
    Combines multiple strategy predictions using:
    1. Per-strategy weights (from calibration)
    2. Path features (chain length, min confidence)
    3. Logistic combination instead of simple average
    """

    def __init__(self, strategy_weights: Dict[str, float] = None):
        """
        Initialize combiner.

        Args:
            strategy_weights: Dict mapping strategy name -> weight
                             (use 1.0 for unknown strategies)
        """
        self.strategy_weights = strategy_weights or {}

        # Logistic regression coefficients (learned from data)
        # These would be trained on validation data
        # For now, using reasonable defaults
        self.coef = {
            'intercept': -2.0,           # Base log-odds (bias toward negative)
            'avg_confidence': 4.0,        # Higher average → more likely
            'min_confidence': 2.0,        # Strong weakest link → more likely
            'num_strategies': 0.5,        # More strategies → more likely
            'strategy_agreement': 1.0,    # More agreement → more likely
            'has_direct': 2.0,            # Direct evidence → much more likely
            'inverse_chain_length': 1.0,  # Shorter path → more likely
        }

    def combine(self, strategy_votes: List[Dict[str, Any]],
                path_features: PathFeatures = None) -> float:
        """
        Combine multiple strategy predictions into a single confidence score.

        Args:
            strategy_votes: List of dicts with keys:
                           - 'strategy': strategy name
                           - 'confidence': predicted confidence
                           - 'reasoning': explanation (optional)
            path_features: Features extracted from the prediction path

        Returns:
            Combined confidence score [0, 1]
        """
        if not strategy_votes:
            return 0.0

        # Extract features
        features = self._extract_features(strategy_votes, path_features)

        # Compute weighted average (baseline)
        weighted_avg = self._weighted_average(strategy_votes)

        # Compute logistic score
        logistic_score = self._logistic_combine(features)

        # Blend weighted average and logistic score
        # Use logistic when we have good path features, otherwise weighted avg
        if path_features and path_features.chain_length > 0:
            # We have path info: trust logistic more
            return 0.3 * weighted_avg + 0.7 * logistic_score
        else:
            # No path info: trust weighted average more
            return 0.7 * weighted_avg + 0.3 * logistic_score

    def _extract_features(self, votes: List[Dict], path_features: PathFeatures = None) -> Dict[str, float]:
        """Extract numeric features for logistic model."""
        confidences = [v['confidence'] for v in votes]
        weights = [self.strategy_weights.get(v['strategy'], 1.0) for v in votes]

        # Compute weighted statistics
        total_weight = sum(weights)
        weighted_avg = sum(w * c for w, c in zip(weights, confidences)) / total_weight if total_weight > 0 else 0.0

        features = {
            'avg_confidence': weighted_avg,
            'min_confidence': min(confidences) if confidences else 0.0,
            'num_strategies': len(votes),
            'strategy_agreement': self._compute_agreement(confidences),
            'has_direct': 0.0,
            'inverse_chain_length': 1.0,  # Default: assume direct edge
        }

        # Add path features if available
        if path_features:
            features['min_confidence'] = path_features.min_confidence
            features['has_direct'] = 1.0 if path_features.has_direct_evidence else 0.0
            if path_features.chain_length > 0:
                features['inverse_chain_length'] = 1.0 / path_features.chain_length

        return features

    def _compute_agreement(self, confidences: List[float]) -> float:
        """Compute how much strategies agree (low variance = high agreement)."""
        if len(confidences) <= 1:
            return 1.0

        mean = sum(confidences) / len(confidences)
        variance = sum((c - mean) ** 2 for c in confidences) / len(confidences)

        # Map variance [0, 0.25] to agreement [1.0, 0.0]
        # Low variance → high agreement
        return max(0.0, 1.0 - 4 * variance)

    def _weighted_average(self, votes: List[Dict]) -> float:
        """Compute weighted average using strategy weights."""
        if not votes:
            return 0.0

        total_weight = 0.0
        weighted_sum = 0.0

        for vote in votes:
            weight = self.strategy_weights.get(vote['strategy'], 1.0)
            weighted_sum += weight * vote['confidence']
            total_weight += weight

        return weighted_sum / total_weight if total_weight > 0 else 0.0

    def _logistic_combine(self, features: Dict[str, float]) -> float:
        """
        Compute probability using logistic regression.

        P(edge exists) = 1 / (1 + exp(-z))
        where z = intercept + sum(coef_i * feature_i)
        """
        z = self.coef['intercept']

        for feature_name, feature_value in features.items():
            if feature_name in self.coef:
                z += self.coef[feature_name] * feature_value

        # Sigmoid
        return 1.0 / (1.0 + np.exp(-z))

    def set_coefficients(self, coef: Dict[str, float]):
        """Update logistic regression coefficients (after training)."""
        self.coef.update(coef)


def extract_path_features_from_category(category, source: str, target: str) -> PathFeatures:
    """
    Extract path features from the category.

    Args:
        category: KOMPOSOS-IV Category
        source: Source object name
        target: Target object name

    Returns:
        PathFeatures with statistics about paths between source and target
    """
    # Check if direct edge exists
    has_direct = False
    direct_confidence = 0.0

    for mor in category.morphisms():
        if mor.source == source and mor.target == target:
            has_direct = True
            direct_confidence = mor.confidence
            break

    # Find shortest path
    paths = category.find_paths(source, target, max_length=5)

    if not paths:
        return PathFeatures(
            chain_length=0,
            min_confidence=0.0,
            avg_confidence=0.0,
            has_direct_evidence=has_direct
        )

    # Get shortest path (paths is a list of Path objects with .length property)
    shortest = min(paths, key=lambda p: p.length)

    # Compute statistics from morphisms in the path
    confidences = []
    for mor_id in shortest.morphism_ids:
        # Find morphism by ID
        for mor in category.morphisms():
            if mor.name == mor_id:  # morphism_ids are morphism names
                confidences.append(mor.confidence)
                break

    return PathFeatures(
        chain_length=shortest.length,  # Number of morphisms in path
        min_confidence=min(confidences) if confidences else 0.0,
        avg_confidence=sum(confidences) / len(confidences) if confidences else 0.0,
        has_direct_evidence=has_direct
    )
