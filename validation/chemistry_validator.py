# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""
Chemistry Results Validator

Validates results from Physical-Chemical Bridge (Phases 1-5):
- Energy function outputs
- Optimizer results
- Rotamer selections
- Statistical potentials

Prevents overclaiming and ensures physical validity using semantic embeddings.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
import numpy as np
import sys
from pathlib import Path

# Import semantic validator for claim checking
from validation.semantic_validator import ProteinInterpretationValidator, SemanticIssue


@dataclass
class ChemistryValidationResult:
    """Result of chemistry validation"""
    passed: bool
    issues: List[SemanticIssue]
    recommendations: List[str]
    confidence_score: float


class ChemistryResultsValidator:
    """
    Validates chemistry module results before making claims.

    This validator prevents the kind of errors that happened in climate analysis:
    - Overclaiming from limited testing
    - Confusing mathematical results with biological reality
    - Missing disclaimers about defaults/approximations
    - Generalizing from insufficient evidence

    Uses sentence embeddings to detect semantic issues in interpretations.
    """

    def __init__(self):
        self.semantic_validator = ProteinInterpretationValidator()

        # Reference energy ranges (from Rosetta, empirical)
        self.expected_energy_per_residue = {
            'min': -15.0,  # Very favorable
            'typical_native': (-10.0, -5.0),  # Tuple range
            'typical_decoy': (-5.0, -2.0),    # Tuple range
            'max': 10.0  # Highly unfavorable
        }

    def validate_energy_function_result(
        self,
        energy_breakdown: Dict,
        structure_data: Dict
    ) -> ChemistryValidationResult:
        """
        Validate energy function results.

        Checks:
        - All energy terms have reasonable magnitudes
        - Signs are correct (favorable interactions = negative)
        - No NaN or Inf values
        - Comparison to Rosetta-style energies
        - Individual components make physical sense

        Args:
            energy_breakdown: Dict with 'total' and component energies
            structure_data: Dict with 'coords', 'sequence', etc.

        Returns:
            ChemistryValidationResult
        """
        issues = []

        # Extract values
        total_energy = energy_breakdown.get('total', 0.0)
        N = len(structure_data.get('sequence', ''))

        if N == 0:
            issues.append(SemanticIssue(
                severity='CRITICAL',
                category='invalid_input',
                message='No sequence provided for energy validation',
                details={}
            ))
            return self._create_result(issues, 0)

        # Check 1: Numerical validity
        if np.isnan(total_energy) or np.isinf(total_energy):
            issues.append(SemanticIssue(
                severity='CRITICAL',
                category='numerical_error',
                message='Energy calculation produced NaN or Inf',
                details={
                    'total_energy': str(total_energy),
                    'recommendation': 'Check for division by zero, invalid coordinates, or numerical overflow'
                }
            ))

        # Check 2: Energy magnitude
        energy_per_residue = total_energy / N

        if energy_per_residue > 100:
            issues.append(SemanticIssue(
                severity='WARNING',
                category='suspicious_energy',
                message=f'Unusually high energy per residue: {energy_per_residue:.1f} kcal/mol',
                details={
                    'expected_range': '-15 to +10 kcal/mol/residue for physical structures',
                    'actual': float(energy_per_residue),
                    'recommendation': 'Check for severe clashes, missing atoms, or incorrect force field parameters'
                }
            ))
        elif energy_per_residue < -50:
            issues.append(SemanticIssue(
                severity='WARNING',
                category='suspicious_energy',
                message=f'Unusually low energy per residue: {energy_per_residue:.1f} kcal/mol',
                details={
                    'expected_range': '-15 to +10 kcal/mol/residue',
                    'actual': float(energy_per_residue),
                    'recommendation': 'May indicate overfitting or unrealistic interactions'
                }
            ))

        # Check 3: Component signs
        if 'hbond' in energy_breakdown and energy_breakdown['hbond'] > 0:
            issues.append(SemanticIssue(
                severity='WARNING',
                category='suspicious_energy',
                message='H-bond energy is positive (should be favorable/negative)',
                details={
                    'hbond_energy': float(energy_breakdown['hbond']),
                    'recommendation': 'H-bonds are attractive interactions and should contribute negative energy'
                }
            ))

        # Check 4: VDW reasonable
        if 'vdw' in energy_breakdown:
            vdw = energy_breakdown['vdw']
            if abs(vdw) > abs(total_energy) * 2:
                issues.append(SemanticIssue(
                    severity='INFO',
                    category='energy_component',
                    message='VDW energy dominates total energy',
                    details={
                        'vdw_energy': float(vdw),
                        'total_energy': float(total_energy),
                        'note': 'Common in clashing structures or during optimization'
                    }
                ))

        # Check 5: Solvation term (should favor burial of hydrophobic residues)
        if 'solvation' in energy_breakdown:
            solv = energy_breakdown['solvation']
            # Solvation typically negative (burial of hydrophobic residues favorable)
            if solv > 5.0 * N:
                issues.append(SemanticIssue(
                    severity='INFO',
                    category='energy_component',
                    message='Solvation energy unusually positive',
                    details={
                        'solvation': float(solv),
                        'note': 'May indicate hydrophobic residues exposed to solvent'
                    }
                ))

        confidence = self._compute_confidence(issues, num_tests=1)

        return ChemistryValidationResult(
            passed=len([i for i in issues if i.severity == 'CRITICAL']) == 0,
            issues=issues,
            recommendations=self._generate_recommendations(issues),
            confidence_score=confidence
        )

    def validate_optimizer_result(
        self,
        result: Dict,
        initial_structure: Dict,
        final_structure: Dict,
        num_structures_tested: int = 1
    ) -> ChemistryValidationResult:
        """
        Validate optimizer results before claiming "works" or "fixes clashes".

        Checks:
        - Energy actually decreased
        - Final structure physically valid
        - Sufficient testing (N > 1 for generalization)
        - Convergence was genuine (not trivial)
        - Clashes actually reduced

        Args:
            result: OptimizationResult dict with initial_energy, final_energy, etc.
            initial_structure: Initial coords and sequence
            final_structure: Final coords and sequence
            num_structures_tested: How many diverse structures tested

        Returns:
            ChemistryValidationResult
        """
        issues = []

        initial_energy = result.get('initial_energy', 0.0)
        final_energy = result.get('final_energy', 0.0)
        converged = result.get('converged', False)

        # Check 1: Energy actually decreased
        if final_energy >= initial_energy:
            issues.append(SemanticIssue(
                severity='CRITICAL',
                category='optimization_failed',
                message='Optimizer did not reduce energy',
                details={
                    'initial': float(initial_energy),
                    'final': float(final_energy),
                    'recommendation': 'Check gradient computation, step size, or energy function'
                }
            ))

        # Check 2: Convergence
        if not converged:
            issues.append(SemanticIssue(
                severity='WARNING',
                category='incomplete_optimization',
                message='Optimizer did not converge',
                details={
                    'recommendation': 'Increase max_iterations or adjust convergence threshold'
                }
            ))

        # Check 3: Sufficient testing for generalization claims
        if num_structures_tested < 10:
            issues.append(SemanticIssue(
                severity='WARNING',
                category='insufficient_testing',
                message=f'Only tested on {num_structures_tested} structure(s)',
                details={
                    'num_tests': num_structures_tested,
                    'recommendation': 'Test on 50+ diverse structures (various sizes, folds) before claiming "optimizer works" generally',
                    'current_claim': 'Can only claim "optimizer works on tested case(s)"'
                }
            ))

        # Check 4: Trivial convergence (starting from absurd energy)
        if initial_energy > 10000:
            issues.append(SemanticIssue(
                severity='INFO',
                category='trivial_case',
                message='Initial energy extremely high (likely artificial test case)',
                details={
                    'initial_energy': float(initial_energy),
                    'note': 'Convergence from absurd initial state does not prove optimizer quality on real structures',
                    'recommendation': 'Test on realistic starting structures (e.g., AlphaFold predictions, decoys)'
                }
            ))

        # Check 5: Percentage improvement can be misleading
        improvement_pct = result.get('improvement_percent', 0.0) if callable(getattr(result, 'improvement_percent', None)) else 0.0

        if improvement_pct > 99 and initial_energy > 1000:
            issues.append(SemanticIssue(
                severity='INFO',
                category='misleading_metric',
                message=f'Improvement percentage ({improvement_pct:.1f}%) misleading due to absurd starting energy',
                details={
                    'note': 'Percentage improvement from unrealistic starting point is not meaningful',
                    'recommendation': 'Report absolute energy change (kcal/mol) instead'
                }
            ))

        # Check 6: Validate final structure for remaining clashes
        if 'coords' in final_structure:
            try:
                # Check for clashes in final structure
                final_coords = final_structure['coords']
                clash_count = self._count_clashes(final_coords)

                total_residues = len(final_coords)
                clash_rate = clash_count / total_residues if total_residues > 0 else 0

                if clash_rate > 0.05:  # >5% residues have clashes
                    issues.append(SemanticIssue(
                        severity='WARNING',
                        category='remaining_clashes',
                        message=f'Final structure still has {clash_count} clashes ({clash_rate:.1%} of residues)',
                        details={
                            'clash_count': clash_count,
                            'clash_rate': float(clash_rate),
                            'recommendation': 'Do not claim "fixes clashes" with >5% clash rate. Consider stronger repulsive term or more iterations.'
                        }
                    ))
                elif clash_count > 0:
                    issues.append(SemanticIssue(
                        severity='INFO',
                        category='minor_clashes',
                        message=f'Final structure has {clash_count} minor clashes ({clash_rate:.1%})',
                        details={
                            'note': '<5% clash rate is acceptable for rough models'
                        }
                    ))

            except Exception as e:
                issues.append(SemanticIssue(
                    severity='INFO',
                    category='validation_incomplete',
                    message=f'Could not validate final structure clashes: {str(e)}',
                    details={}
                ))

        confidence = self._compute_confidence(issues, num_structures_tested)

        return ChemistryValidationResult(
            passed=len([i for i in issues if i.severity == 'CRITICAL']) == 0,
            issues=issues,
            recommendations=self._generate_recommendations(issues),
            confidence_score=confidence
        )

    def validate_interpretation_with_chemistry(
        self,
        interpretation: str,
        chemistry_results: Dict,
        evidence: Dict
    ) -> ChemistryValidationResult:
        """
        Validate textual interpretation of chemistry results.

        Uses sentence embeddings to catch:
        - Overclaiming ("production ready" without benchmarking)
        - Math-biology confusion ("low energy = biologically stable")
        - Missing disclaimers (using defaults not acknowledged)
        - Insufficient evidence (generalizing from 1 test)

        This is the key method that prevents the kind of errors seen in
        climate analysis where technically correct calculations led to
        invalid biological conclusions.

        Args:
            interpretation: Text interpretation to validate
            chemistry_results: Dict with energy, optimizer results, etc.
            evidence: Dict with:
                - num_tests: How many structures tested
                - benchmarked: Compared to baselines?
                - using_defaults: Using simplified data?
                - experimental_validation: Ground truth available?

        Returns:
            ChemistryValidationResult
        """
        # Use semantic validator's chemistry claim checking
        semantic_issues = self.semantic_validator.check_chemistry_claims(
            interpretation, evidence
        )

        # Additional checks specific to chemistry system
        additional_issues = []

        # Check: Don't confuse energy minimum with native state
        if self.semantic_validator.use_embeddings:
            confusion_examples = [
                "Energy minimum proves this is the native state",
                "Low energy means biologically stable",
                "Convergence confirms biological correctness",
                "The mathematics shows this is the functional structure"
            ]

            for example in confusion_examples:
                similarity = self.semantic_validator._compute_similarity(
                    interpretation, example
                )
                if similarity > 0.65:
                    additional_issues.append(SemanticIssue(
                        severity='CRITICAL',
                        category='math_biology_confusion',
                        message='Computational result interpreted as biological truth',
                        details={
                            'problem': 'Energy minimum (computational) ≠ native state (biological)',
                            'similarity_to_error': float(similarity),
                            'recommendation': 'Clarify: "Low computed energy suggests stability; requires experimental validation to confirm native state"',
                            'example': 'Change "This IS the native state" → "This MAY represent a stable conformation"'
                        }
                    ))
                    break

        # Check: Using defaults acknowledged
        if evidence.get('using_defaults', False):
            if 'default' not in interpretation.lower() and 'simplified' not in interpretation.lower() and 'approximation' not in interpretation.lower():
                additional_issues.append(SemanticIssue(
                    severity='WARNING',
                    category='missing_disclaimer',
                    message='Using default/simplified parameters not acknowledged',
                    details={
                        'problem': 'Rotamer library and PDB statistics use simplified defaults',
                        'impact': 'Accuracy may be lower than with real data',
                        'recommendation': 'Add disclaimer: "Using simplified parameters for research prototype; production deployment requires real Dunbrack rotamer library and PDB-derived statistical potentials"'
                    }
                ))

        all_issues = semantic_issues + additional_issues
        confidence = self._compute_confidence(all_issues, evidence.get('num_tests', 0))

        return ChemistryValidationResult(
            passed=len([i for i in all_issues if i.severity == 'CRITICAL']) == 0,
            issues=all_issues,
            recommendations=self._generate_recommendations(all_issues),
            confidence_score=confidence
        )

    # Helper methods

    def _count_clashes(self, coords: np.ndarray, threshold: float = 2.0) -> int:
        """
        Count steric clashes in structure.

        Args:
            coords: Nx3 array of CA coordinates
            threshold: Distance threshold for clash (Å)

        Returns:
            Number of clashing residue pairs
        """
        if coords is None or len(coords) == 0:
            return 0

        clash_count = 0
        N = len(coords)

        for i in range(N):
            for j in range(i + 4, N):  # Skip nearby residues (i, i+1, i+2, i+3)
                dist = np.linalg.norm(coords[i] - coords[j])
                if dist < threshold:
                    clash_count += 1

        return clash_count

    def _generate_recommendations(self, issues: List[SemanticIssue]) -> List[str]:
        """Generate actionable recommendations from issues"""
        recs = []
        for issue in issues:
            if issue.details and 'recommendation' in issue.details:
                recs.append(issue.details['recommendation'])
        return list(set(recs))  # Deduplicate

    def _compute_confidence(self, issues: List[SemanticIssue], num_tests: int) -> float:
        """
        Compute confidence score (0-1).

        Factors:
        - Critical issues: confidence = 0
        - Warnings: -10% each
        - Insufficient testing: -25% if < 10 tests, -50% if < 5 tests

        Args:
            issues: List of validation issues
            num_tests: Number of structures tested

        Returns:
            Confidence score 0-1
        """
        # Critical issues = 0 confidence
        critical_count = len([i for i in issues if i.severity == 'CRITICAL'])
        if critical_count > 0:
            return 0.0

        # Start with full confidence
        confidence = 1.0

        # Penalize for warnings
        warning_count = len([i for i in issues if i.severity == 'WARNING'])
        confidence -= warning_count * 0.1

        # Penalize for insufficient testing
        if num_tests < 5:
            confidence *= 0.5  # 50% confidence if very limited testing
        elif num_tests < 10:
            confidence *= 0.75  # 75% confidence if limited testing
        elif num_tests < 50:
            confidence *= 0.9  # 90% confidence if moderate testing
        # else: 100% testing factor if >=50 tests

        return max(0.0, min(1.0, confidence))

    def _create_result(
        self,
        issues: List[SemanticIssue],
        num_tests: int
    ) -> ChemistryValidationResult:
        """Create validation result from issues"""
        return ChemistryValidationResult(
            passed=len([i for i in issues if i.severity == 'CRITICAL']) == 0,
            issues=issues,
            recommendations=self._generate_recommendations(issues),
            confidence_score=self._compute_confidence(issues, num_tests)
        )

    def generate_report(self, result: ChemistryValidationResult) -> str:
        """Generate human-readable validation report"""
        lines = []
        lines.append("=" * 70)
        lines.append("CHEMISTRY RESULTS VALIDATION REPORT")
        lines.append("=" * 70)
        lines.append("")

        if result.passed:
            lines.append(f"[OK] VALIDATION PASSED")
            lines.append(f"  Confidence Score: {result.confidence_score:.2%}")
        else:
            lines.append(f"[X] VALIDATION FAILED")
            lines.append(f"  Confidence Score: {result.confidence_score:.2%}")

        lines.append("")

        if result.issues:
            # Group by severity
            for severity in ['CRITICAL', 'WARNING', 'INFO']:
                severity_issues = [i for i in result.issues if i.severity == severity]
                if severity_issues:
                    lines.append(f"{severity} Issues ({len(severity_issues)}):")
                    for issue in severity_issues:
                        lines.append(f"  [{issue.category}] {issue.message}")
                        if issue.details:
                            for key, value in issue.details.items():
                                if key == 'recommendation':
                                    lines.append(f"    -> {value}")
                                elif key not in ['problem', 'note', 'example']:
                                    lines.append(f"    {key}: {value}")
                    lines.append("")

        if result.recommendations:
            lines.append("RECOMMENDATIONS:")
            for i, rec in enumerate(result.recommendations, 1):
                lines.append(f"  {i}. {rec}")
            lines.append("")

        lines.append("=" * 70)
        return "\n".join(lines)


# Testing
if __name__ == "__main__":
    print("=" * 70)
    print("Chemistry Results Validator - Test")
    print("=" * 70)
    print()

    validator = ChemistryResultsValidator()

    # Test 1: Energy validation
    print("Test 1: Energy Function Validation")
    print("-" * 70)

    energy_breakdown = {
        'total': 45.2,
        'vdw': 30.0,
        'electrostatic': 5.0,
        'hbond': -10.0,  # Correct sign
        'solvation': 15.2,
        'rama': 5.0
    }

    structure_data = {
        'sequence': 'ALKFDEGHIKLMNPQRSTVWY',  # 21 residues
        'coords': np.random.randn(21, 3)
    }

    result = validator.validate_energy_function_result(energy_breakdown, structure_data)
    print(validator.generate_report(result))
    print()

    # Test 2: Optimizer validation with insufficient testing
    print("Test 2: Optimizer Validation (insufficient testing)")
    print("-" * 70)

    opt_result = {
        'initial_energy': 351989.0,  # Absurdly high
        'final_energy': -6.76,
        'converged': True,
        'improvement_percent': 100.0
    }

    result = validator.validate_optimizer_result(
        opt_result,
        initial_structure={'coords': np.random.randn(21, 3)},
        final_structure={'coords': np.random.randn(21, 3)},
        num_structures_tested=1  # Only 1 test!
    )
    print(validator.generate_report(result))
    print()

    # Test 3: Interpretation validation with overclaiming
    print("Test 3: Interpretation Validation (overclaiming)")
    print("-" * 70)

    interpretation = """
    The optimizer WORKS and FIXES all clashes! This is production ready.
    The energy minimum proves this is the native state. This mathematics
    definitively shows the biological structure is correct.
    """

    chemistry_results = {'energy': -6.76}
    evidence = {
        'num_tests': 1,
        'benchmarked': False,
        'using_defaults': True,
        'experimental_validation': False
    }

    result = validator.validate_interpretation_with_chemistry(
        interpretation, chemistry_results, evidence
    )
    print(validator.generate_report(result))
    print()

    print("=" * 70)
    print("Chemistry validator ready for integration!")
    print("=" * 70)
