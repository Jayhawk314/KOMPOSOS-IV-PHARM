# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""
Layer 4: Experimental Validation

Validates against experimental ground truth when available:
- Structure comparison (RMSD, TM-score vs PDB)
- Folding kinetics (predicted vs measured rates)
- Stability (predicted vs measured ΔG, Tm)
- Mutation effects (ΔΔG predictions vs deep mutational scans)
"""

import re
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class ExperimentalValidation:
    """Single experimental validation result"""
    metric: str
    predicted: float
    experimental: float
    passed: bool
    details: Optional[Dict] = None


class ExperimentalValidator:
    """
    Validates predictions against experimental measurements.

    This validator checks if computational predictions match
    experimental reality when ground truth data is available.
    """

    def __init__(self):
        # Validation thresholds
        self.rmsd_threshold = 5.0  # Angstroms
        self.tm_score_threshold = 0.5  # 0-1 scale
        self.folding_rate_tolerance = 2.0  # Log units
        self.stability_tolerance = 2.0  # kcal/mol
        self.mutation_correlation_threshold = 0.6  # Pearson r

    def validate_against_experiments(
        self,
        predicted_coords: np.ndarray,
        sequence: str,
        experimental_data: Dict
    ) -> Dict[str, ExperimentalValidation]:
        """
        Validate predictions against experimental data.

        Args:
            predicted_coords: Nx3 predicted structure
            sequence: Amino acid sequence
            experimental_data: Dict with experimental measurements

        Returns:
            Dict of validation results by metric type
        """
        validations = {}

        # 1. Structure validation
        if 'pdb_structure' in experimental_data:
            validations['structure'] = self._validate_structure(
                predicted_coords,
                experimental_data['pdb_structure']
            )

        # 2. Folding kinetics validation
        if 'folding_rate' in experimental_data:
            validations['kinetics'] = self._validate_folding_kinetics(
                predicted_coords,
                sequence,
                experimental_data['folding_rate']
            )

        # 3. Stability validation
        if 'melting_temp' in experimental_data or 'delta_g' in experimental_data:
            validations['stability'] = self._validate_stability(
                predicted_coords,
                sequence,
                experimental_data
            )

        # 4. Mutation effects validation
        if 'mutation_scan' in experimental_data:
            validations['mutations'] = self._validate_mutation_effects(
                predicted_coords,
                sequence,
                experimental_data['mutation_scan']
            )

        return validations

    def _validate_structure(
        self,
        predicted: np.ndarray,
        experimental: np.ndarray
    ) -> ExperimentalValidation:
        """
        Compare predicted structure to experimental structure.

        Args:
            predicted: Nx3 predicted coordinates
            experimental: Nx3 experimental coordinates

        Returns:
            Structure validation result
        """
        # Align structures (Kabsch algorithm)
        aligned_pred, aligned_exp = self._align_structures(predicted, experimental)

        # Compute RMSD
        rmsd = np.sqrt(np.mean(np.sum((aligned_pred - aligned_exp) ** 2, axis=1)))

        # Compute TM-score (approximate)
        tm_score = self._compute_tm_score(aligned_pred, aligned_exp)

        passed = rmsd < self.rmsd_threshold and tm_score > self.tm_score_threshold

        return ExperimentalValidation(
            metric='structure',
            predicted=float(rmsd),
            experimental=float(tm_score),
            passed=passed,
            details={
                'rmsd': float(rmsd),
                'tm_score': float(tm_score),
                'rmsd_threshold': self.rmsd_threshold,
                'tm_threshold': self.tm_score_threshold,
                'interpretation': self._interpret_structure_quality(rmsd, tm_score)
            }
        )

    def _validate_folding_kinetics(
        self,
        coords: np.ndarray,
        sequence: str,
        experimental_rate: float
    ) -> ExperimentalValidation:
        """
        Validate predicted folding rate against experimental measurement.

        Args:
            coords: Structure coordinates
            sequence: Amino acid sequence
            experimental_rate: Measured folding rate (s^-1)

        Returns:
            Kinetics validation result
        """
        # Predict folding rate (simplified model)
        predicted_rate = self._predict_folding_rate(coords, sequence)

        # Compare in log space (folding rates span many orders of magnitude)
        log_pred = np.log10(predicted_rate) if predicted_rate > 0 else -10
        log_exp = np.log10(experimental_rate) if experimental_rate > 0 else -10

        difference = abs(log_pred - log_exp)
        passed = difference < self.folding_rate_tolerance

        return ExperimentalValidation(
            metric='folding_kinetics',
            predicted=float(predicted_rate),
            experimental=float(experimental_rate),
            passed=passed,
            details={
                'predicted_rate_log': float(log_pred),
                'experimental_rate_log': float(log_exp),
                'log_difference': float(difference),
                'tolerance': self.folding_rate_tolerance,
                'interpretation': self._interpret_folding_rate(difference)
            }
        )

    def _validate_stability(
        self,
        coords: np.ndarray,
        sequence: str,
        experimental_data: Dict
    ) -> ExperimentalValidation:
        """
        Validate predicted stability against experimental measurements.

        Args:
            coords: Structure coordinates
            sequence: Amino acid sequence
            experimental_data: Dict with Tm and/or ΔG

        Returns:
            Stability validation result
        """
        # Predict melting temperature
        predicted_tm = self._predict_melting_temp(coords, sequence)

        if 'melting_temp' in experimental_data:
            experimental_tm = experimental_data['melting_temp']
            difference = abs(predicted_tm - experimental_tm)
            passed = difference < 10.0  # Within 10°C

            return ExperimentalValidation(
                metric='stability',
                predicted=float(predicted_tm),
                experimental=float(experimental_tm),
                passed=passed,
                details={
                    'predicted_tm': float(predicted_tm),
                    'experimental_tm': float(experimental_tm),
                    'difference_celsius': float(difference),
                    'interpretation': self._interpret_stability(difference)
                }
            )

        # If no Tm, use ΔG
        if 'delta_g' in experimental_data:
            predicted_dg = self._predict_delta_g(coords, sequence)
            experimental_dg = experimental_data['delta_g']
            difference = abs(predicted_dg - experimental_dg)
            passed = difference < self.stability_tolerance

            return ExperimentalValidation(
                metric='stability',
                predicted=float(predicted_dg),
                experimental=float(experimental_dg),
                passed=passed,
                details={
                    'predicted_delta_g': float(predicted_dg),
                    'experimental_delta_g': float(experimental_dg),
                    'difference_kcal': float(difference),
                    'tolerance': self.stability_tolerance
                }
            )

        # No data available
        return ExperimentalValidation(
            metric='stability',
            predicted=float(predicted_tm),
            experimental=0.0,
            passed=False,
            details={'error': 'No experimental stability data provided'}
        )

    def _validate_mutation_effects(
        self,
        coords: np.ndarray,
        sequence: str,
        mutation_scan: Dict[str, float]
    ) -> ExperimentalValidation:
        """
        Validate predicted mutation effects against deep mutational scan.

        Args:
            coords: Structure coordinates
            sequence: Amino acid sequence
            mutation_scan: Dict mapping mutations to experimental ΔΔG

        Returns:
            Mutation validation result
        """
        # Predict ΔΔG for each mutation
        predicted_ddg = {}
        experimental_ddg = {}

        for mutation, exp_value in mutation_scan.items():
            pred_value = self._predict_mutation_effect(coords, sequence, mutation)
            predicted_ddg[mutation] = pred_value
            experimental_ddg[mutation] = exp_value

        # Compute correlation
        pred_values = np.array(list(predicted_ddg.values()))
        exp_values = np.array(list(experimental_ddg.values()))

        correlation = np.corrcoef(pred_values, exp_values)[0, 1]
        passed = correlation > self.mutation_correlation_threshold

        return ExperimentalValidation(
            metric='mutation_effects',
            predicted=float(correlation),
            experimental=1.0,  # Target is perfect correlation
            passed=passed,
            details={
                'correlation': float(correlation),
                'threshold': self.mutation_correlation_threshold,
                'num_mutations': len(mutation_scan),
                'interpretation': self._interpret_mutation_correlation(correlation)
            }
        )

    # Helper methods (simplified implementations)

    def _align_structures(self, coords1: np.ndarray, coords2: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Align two structures using Kabsch algorithm (simplified)"""
        # Center structures
        center1 = np.mean(coords1, axis=0)
        center2 = np.mean(coords2, axis=0)

        centered1 = coords1 - center1
        centered2 = coords2 - center2

        # For simplicity, just return centered structures
        # Real implementation would compute optimal rotation
        return centered1, centered2

    def _compute_tm_score(self, coords1: np.ndarray, coords2: np.ndarray) -> float:
        """Compute TM-score (simplified approximation)"""
        N = len(coords1)
        d0 = 1.24 * (N - 15) ** (1/3) - 1.8  # Length-dependent scale

        distances = np.linalg.norm(coords1 - coords2, axis=1)
        tm_score = np.mean(1.0 / (1.0 + (distances / d0) ** 2))

        return float(tm_score)

    def _predict_folding_rate(self, coords: np.ndarray, sequence: str) -> float:
        """Predict folding rate (placeholder - real implementation needed)"""
        # Simplified: use contact order as proxy
        N = len(coords)
        total_co = 0
        contact_count = 0

        for i in range(N):
            for j in range(i + 1, N):
                distance = np.linalg.norm(coords[i] - coords[j])
                if distance < 8.0:
                    total_co += abs(j - i)
                    contact_count += 1

        if contact_count == 0:
            return 1e-6

        relative_co = (total_co / contact_count) / N
        # Empirical relation: log(k) ~ -15 * relative_CO
        log_rate = -15 * relative_co + 5
        return 10 ** log_rate

    def _predict_melting_temp(self, coords: np.ndarray, sequence: str) -> float:
        """Predict melting temperature (placeholder)"""
        # Simplified: based on compactness
        center = np.mean(coords, axis=0)
        Rg = np.sqrt(np.mean(np.linalg.norm(coords - center, axis=1) ** 2))
        N = len(sequence)
        Rg_expected = 2.2 * (N ** 0.38)
        compactness = Rg / Rg_expected

        # More compact = more stable = higher Tm
        # Typical protein Tm ~ 60°C, compact ones up to 90°C
        tm = 60 + 30 * (1.5 - compactness)
        return float(np.clip(tm, 20, 120))

    def _predict_delta_g(self, coords: np.ndarray, sequence: str) -> float:
        """Predict folding free energy (placeholder)"""
        # Simplified: based on contact density
        N = len(coords)
        contact_count = 0

        for i in range(N):
            for j in range(i + 3, N):
                if np.linalg.norm(coords[i] - coords[j]) < 8.0:
                    contact_count += 1

        contact_density = contact_count / N
        # More contacts = more stable = more negative ΔG
        delta_g = -5.0 - 3.0 * contact_density
        return float(delta_g)

    def _predict_mutation_effect(self, coords: np.ndarray, sequence: str, mutation: str) -> float:
        """Predict mutation effect on stability (placeholder)"""
        # Parse mutation (e.g., "A10V")
        match = re.match(r'([A-Z])(\d+)([A-Z])', mutation)
        if not match:
            return 0.0

        wt_aa, position, mut_aa = match.groups()
        position = int(position) - 1

        # Simplified: hydrophobic to polar is destabilizing
        hydrophobic = set('AILMFVPW')

        if wt_aa in hydrophobic and mut_aa not in hydrophobic:
            return 2.0  # Destabilizing
        elif wt_aa not in hydrophobic and mut_aa in hydrophobic:
            return -1.0  # Stabilizing
        else:
            return 0.5  # Neutral

    # Interpretation methods

    def _interpret_structure_quality(self, rmsd: float, tm_score: float) -> str:
        """Interpret structure comparison quality"""
        if tm_score > 0.9:
            return "Excellent agreement with experimental structure"
        elif tm_score > 0.7:
            return "Good agreement with experimental structure"
        elif tm_score > 0.5:
            return "Moderate agreement with experimental structure"
        else:
            return "Poor agreement with experimental structure"

    def _interpret_folding_rate(self, log_difference: float) -> str:
        """Interpret folding rate prediction quality"""
        if log_difference < 1.0:
            return "Excellent folding rate prediction (within 1 order of magnitude)"
        elif log_difference < 2.0:
            return "Good folding rate prediction (within 2 orders of magnitude)"
        elif log_difference < 3.0:
            return "Moderate folding rate prediction"
        else:
            return "Poor folding rate prediction"

    def _interpret_stability(self, difference: float) -> str:
        """Interpret stability prediction quality"""
        if difference < 5.0:
            return "Excellent stability prediction"
        elif difference < 10.0:
            return "Good stability prediction"
        elif difference < 15.0:
            return "Moderate stability prediction"
        else:
            return "Poor stability prediction"

    def _interpret_mutation_correlation(self, correlation: float) -> str:
        """Interpret mutation effect prediction quality"""
        if correlation > 0.8:
            return "Excellent mutation effect predictions"
        elif correlation > 0.6:
            return "Good mutation effect predictions"
        elif correlation > 0.4:
            return "Moderate mutation effect predictions"
        else:
            return "Poor mutation effect predictions"

    def generate_report(self, validations: Dict[str, ExperimentalValidation]) -> str:
        """Generate human-readable report"""
        lines = []
        lines.append("=" * 70)
        lines.append("EXPERIMENTAL VALIDATION REPORT")
        lines.append("=" * 70)
        lines.append("")

        if not validations:
            lines.append("[i]  No experimental data available for validation")
            lines.append("")
        else:
            passed_count = sum(1 for v in validations.values() if v.passed)
            total_count = len(validations)

            lines.append(f"Validation Summary: {passed_count}/{total_count} metrics passed")
            lines.append("")

            for metric_name, validation in validations.items():
                status = "[OK] PASS" if validation.passed else "[X] FAIL"
                lines.append(f"{status} - {metric_name.upper()}")
                lines.append(f"  Predicted: {validation.predicted:.3f}")
                if metric_name != 'mutation_effects':
                    lines.append(f"  Experimental: {validation.experimental:.3f}")

                if validation.details:
                    if 'interpretation' in validation.details:
                        lines.append(f"  {validation.details['interpretation']}")
                    for key, value in validation.details.items():
                        if key not in ['interpretation', 'error']:
                            lines.append(f"  {key}: {value}")
                    if 'error' in validation.details:
                        lines.append(f"  Error: {validation.details['error']}")

                lines.append("")

        lines.append("=" * 70)
        return "\n".join(lines)
