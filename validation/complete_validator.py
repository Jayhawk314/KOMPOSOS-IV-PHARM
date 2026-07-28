# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""
Complete Protein Validation Framework

Integrates all 4 validation layers:
1. Structural validation (geometry, clashes, Ramachandran)
2. Chemical validation (H-bonds, hydrophobic core, electrostatics)
3. Semantic validation (interpretation checking with embeddings)
4. Experimental validation (ground truth comparison)

Provides comprehensive validation reports and confidence scores.
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
import json

from .protein_structure_validator import ProteinStructureValidator, ValidationIssue
from .chemical_constraint_validator import ChemicalConstraintValidator, ChemicalIssue
from .semantic_validator import ProteinInterpretationValidator, SemanticIssue
from .experimental_validator import ExperimentalValidator, ExperimentalValidation
from .chemistry_validator import ChemistryResultsValidator, ChemistryValidationResult
from .pfam_validator import PfamDomainValidator, PfamIssue


@dataclass
class ValidationReport:
    """Complete validation report"""
    timestamp: str
    sequence_length: int
    validation_layers: Dict
    overall: Dict
    recommendation: str


class CompleteProteinValidator:
    """
    Complete multi-layer validation system.

    Validates protein structures and interpretations through:
    - Layer 1: Structural geometry
    - Layer 2: Chemical constraints
    - Layer 3: Semantic interpretation
    - Layer 4: Experimental ground truth (if available)
    """

    def __init__(self, pfam_mapper=None):
        self.structural_validator = ProteinStructureValidator()
        self.chemical_validator = ChemicalConstraintValidator()
        self.pfam_validator = PfamDomainValidator(pfam_mapper)
        self.semantic_validator = ProteinInterpretationValidator()
        self.experimental_validator = ExperimentalValidator()
        self.chemistry_results_validator = ChemistryResultsValidator()  # Physical-Chemical Bridge validator
        self._has_pfam = pfam_mapper is not None

    def validate_full_pipeline(
        self,
        sequence: str,
        predicted_coords: np.ndarray,
        interpretation: str,
        confidence: Optional[np.ndarray] = None,
        experimental_data: Optional[Dict] = None,
        frameworks_results: Optional[Dict] = None
    ) -> ValidationReport:
        """
        Run complete validation pipeline.

        Args:
            sequence: Amino acid sequence
            predicted_coords: Nx3 predicted structure
            interpretation: Text interpretation to validate
            confidence: Optional pLDDT scores
            experimental_data: Optional experimental measurements
            frameworks_results: Optional KOMPOSOS-III framework results

        Returns:
            Complete validation report
        """
        report = ValidationReport(
            timestamp=datetime.now().isoformat(),
            sequence_length=len(sequence),
            validation_layers={},
            overall={},
            recommendation=""
        )

        # Prepare structure data for semantic validator
        structure_data = {
            'coords': predicted_coords,
            'sequence': sequence,
            'structure': {
                'mean_plddt': float(np.mean(confidence)) if confidence is not None else 100.0,
                'num_residues': len(sequence)
            }
        }
        if frameworks_results:
            structure_data['frameworks'] = frameworks_results

        print("=" * 70)
        print("KOMPOSOS-III VALIDATION FRAMEWORK")
        print("=" * 70)
        print()
        print(f"Sequence length: {len(sequence)}")
        print(f"Structure confidence: {structure_data['structure']['mean_plddt']:.1f} pLDDT")
        print()

        # Layer 1: Structural validation
        print("[1/4] Running structural validation...")
        struct_valid, struct_issues = self.structural_validator.validate_structure(
            predicted_coords, sequence
        )
        report.validation_layers['structural'] = {
            'passed': struct_valid,
            'issues': [self._issue_to_dict(i) for i in struct_issues]
        }

        if not struct_valid:
            print(f"  [X] FAILED: {len([i for i in struct_issues if i.severity == 'CRITICAL'])} critical issues")
            report.recommendation = 'STOP: Fix structural issues before proceeding with interpretation'
            report.overall = {
                'passed': False,
                'critical_issues': len([i for i in struct_issues if i.severity == 'CRITICAL']),
                'confidence_score': 0.0
            }
            return report
        else:
            warning_count = len([i for i in struct_issues if i.severity == 'WARNING'])
            if warning_count > 0:
                print(f"  [!]  PASSED with {warning_count} warnings")
            else:
                print("  [OK] PASSED")

        # Layer 2: Chemical validation
        print("[2/4] Running chemical validation...")
        chem_issues = self.chemical_validator.validate_chemistry(
            predicted_coords, sequence, confidence
        )
        report.validation_layers['chemical'] = {
            'issues': [self._issue_to_dict(i) for i in chem_issues]
        }

        critical_chem = len([i for i in chem_issues if i.severity == 'CRITICAL'])
        warning_chem = len([i for i in chem_issues if i.severity == 'WARNING'])
        if critical_chem > 0:
            print(f"  [X] FAILED: {critical_chem} critical chemical issues")
        elif warning_chem > 0:
            print(f"  [!]  {warning_chem} warnings")
        else:
            print("  [OK] PASSED")

        # Layer 2.5: Pfam domain validation (if mapper configured)
        pfam_issues = []
        if self._has_pfam and confidence is not None:
            print("[2.5/4] Running Pfam domain validation...")
            # Build a binary contact map from confidence scores
            contact_map = (confidence > 0.0).astype(int) if confidence.ndim == 2 else np.zeros((len(sequence), len(sequence)), dtype=int)
            conf_map = confidence if confidence.ndim == 2 else np.zeros((len(sequence), len(sequence)))
            pfam_issues = self.pfam_validator.validate_domain_contact_agreement(
                sequence, contact_map, conf_map
            )
            report.validation_layers['pfam'] = {
                'issues': [self._issue_to_dict(i) for i in pfam_issues]
            }
            pfam_warnings = len([i for i in pfam_issues if i.severity == 'WARNING'])
            pfam_info = len([i for i in pfam_issues if i.severity == 'INFO'])
            if pfam_warnings > 0:
                print(f"  [!]  {pfam_warnings} warnings, {pfam_info} info")
            else:
                print(f"  [OK] {pfam_info} domain annotations verified")
        elif self._has_pfam:
            print("[2.5/4] Pfam domain validation skipped (no contact data)")
            report.validation_layers['pfam'] = {'issues': [], 'status': 'no_contact_data'}

        # Layer 3: Semantic validation
        print("[3/4] Running semantic validation...")
        semantic_issues = self.semantic_validator.validate_interpretation(
            structure_data, interpretation
        )
        report.validation_layers['semantic'] = {
            'issues': [self._issue_to_dict(i) for i in semantic_issues]
        }

        critical_semantic = len([i for i in semantic_issues if i.severity == 'CRITICAL'])
        warning_semantic = len([i for i in semantic_issues if i.severity == 'WARNING'])
        if critical_semantic > 0:
            print(f"  [X] FAILED: {critical_semantic} critical interpretation errors")
        elif warning_semantic > 0:
            print(f"  [!]  {warning_semantic} warnings")
        else:
            print("  [OK] PASSED")

        # Layer 4: Experimental validation (if data available)
        if experimental_data:
            print("[4/4] Running experimental validation...")
            exp_validations = self.experimental_validator.validate_against_experiments(
                predicted_coords, sequence, experimental_data
            )
            report.validation_layers['experimental'] = {
                metric: self._validation_to_dict(val)
                for metric, val in exp_validations.items()
            }

            passed_exp = sum(1 for v in exp_validations.values() if v.passed)
            total_exp = len(exp_validations)
            print(f"  {passed_exp}/{total_exp} experimental metrics passed")
        else:
            print("[4/4] Experimental validation skipped (no data provided)")
            report.validation_layers['experimental'] = {'status': 'no_data'}

        # Overall assessment
        print()
        print("=" * 70)
        print("OVERALL ASSESSMENT")
        print("=" * 70)
        print()

        all_issues = struct_issues + chem_issues + pfam_issues + semantic_issues
        critical_count = sum(1 for i in all_issues if i.severity == 'CRITICAL')
        warning_count = sum(1 for i in all_issues if i.severity == 'WARNING')

        confidence_score = self._compute_confidence_score(report)

        report.overall = {
            'passed': critical_count == 0,
            'critical_issues': critical_count,
            'warning_count': warning_count,
            'confidence_score': confidence_score
        }

        # Generate recommendation
        if critical_count > 0:
            report.recommendation = self._generate_critical_recommendation(
                struct_issues, chem_issues, semantic_issues
            )
            print(f"[X] VALIDATION FAILED")
            print(f"  Critical issues: {critical_count}")
            print(f"  Recommendation: {report.recommendation}")
        elif warning_count > 5:
            report.recommendation = "PROCEED WITH CAUTION: Multiple warnings require attention"
            print(f"[!]  VALIDATION PASSED WITH WARNINGS")
            print(f"  Warnings: {warning_count}")
            print(f"  Confidence: {confidence_score:.2%}")
        else:
            report.recommendation = "PROCEED: Validation passed"
            print(f"[OK] VALIDATION PASSED")
            print(f"  Confidence: {confidence_score:.2%}")

        print()
        print("=" * 70)

        return report

    def validate_with_chemistry_results(
        self,
        sequence: str,
        predicted_coords: np.ndarray,
        chemistry_results: Dict,
        interpretation: str,
        evidence: Dict,
        confidence: Optional[np.ndarray] = None
    ) -> ValidationReport:
        """
        Validate including chemistry module results (Physical-Chemical Bridge Phases 1-5).

        This extends the standard validation with chemistry-specific checks:
        - Energy function validity
        - Optimizer results
        - Chemistry claims appropriateness

        Args:
            sequence: Amino acid sequence
            predicted_coords: Nx3 predicted structure
            chemistry_results: Results from energy/optimizer, Dict with:
                - 'energy_breakdown': Energy component breakdown
                - 'optimization_result': Optimizer result
                - 'initial_structure': Initial structure (for optimizer)
            interpretation: Text interpretation
            evidence: Dict with testing metadata:
                - num_tests: How many structures tested
                - benchmarked: Compared to baselines?
                - using_defaults: Using simplified data?
                - experimental_validation: Has ground truth?
            confidence: Optional pLDDT scores

        Returns:
            ValidationReport with chemistry layers added
        """
        # Run standard validation first
        report = self.validate_full_pipeline(
            sequence, predicted_coords, interpretation, confidence
        )

        print()
        print("=" * 70)
        print("CHEMISTRY RESULTS VALIDATION (Physical-Chemical Bridge)")
        print("=" * 70)
        print()

        # Validate energy function results (if present)
        if 'energy_breakdown' in chemistry_results:
            print("[Chemistry 1/3] Validating energy function results...")
            energy_validation = self.chemistry_results_validator.validate_energy_function_result(
                chemistry_results['energy_breakdown'],
                {'coords': predicted_coords, 'sequence': sequence}
            )

            report.validation_layers['chemistry_energy'] = {
                'passed': energy_validation.passed,
                'confidence': energy_validation.confidence_score,
                'issues': [self._issue_to_dict(i) for i in energy_validation.issues],
                'recommendations': energy_validation.recommendations
            }

            if not energy_validation.passed:
                print(f"  [X] FAILED: Energy function issues detected")
            elif energy_validation.issues:
                print(f"  [!]  PASSED with {len(energy_validation.issues)} warnings")
            else:
                print("  [OK] PASSED")

        # Validate optimizer results (if present)
        if 'optimization_result' in chemistry_results:
            print("[Chemistry 2/3] Validating optimizer results...")
            opt_validation = self.chemistry_results_validator.validate_optimizer_result(
                chemistry_results['optimization_result'],
                chemistry_results.get('initial_structure', {'coords': predicted_coords}),
                {'coords': predicted_coords, 'sequence': sequence},
                num_structures_tested=evidence.get('num_tests', 1)
            )

            report.validation_layers['chemistry_optimization'] = {
                'passed': opt_validation.passed,
                'confidence': opt_validation.confidence_score,
                'issues': [self._issue_to_dict(i) for i in opt_validation.issues],
                'recommendations': opt_validation.recommendations
            }

            if not opt_validation.passed:
                print(f"  [X] FAILED: Optimizer validation issues")
            elif opt_validation.issues:
                print(f"  [!]  PASSED with {len(opt_validation.issues)} warnings")
            else:
                print("  [OK] PASSED")

        # Validate interpretation with chemistry context
        print("[Chemistry 3/3] Validating chemistry claims in interpretation...")
        interp_validation = self.chemistry_results_validator.validate_interpretation_with_chemistry(
            interpretation, chemistry_results, evidence
        )

        report.validation_layers['chemistry_interpretation'] = {
            'passed': interp_validation.passed,
            'confidence': interp_validation.confidence_score,
            'issues': [self._issue_to_dict(i) for i in interp_validation.issues],
            'recommendations': interp_validation.recommendations
        }

        if not interp_validation.passed:
            print(f"  [X] FAILED: Overclaiming or math-biology confusion detected")
        elif interp_validation.issues:
            print(f"  [!]  PASSED with {len(interp_validation.issues)} warnings")
        else:
            print("  [OK] PASSED")

        # Update overall assessment to include chemistry validation
        all_chemistry_issues = []
        if 'chemistry_energy' in report.validation_layers:
            all_chemistry_issues.extend([
                SemanticIssue(**i) for i in report.validation_layers['chemistry_energy']['issues']
            ])
        if 'chemistry_optimization' in report.validation_layers:
            all_chemistry_issues.extend([
                SemanticIssue(**i) for i in report.validation_layers['chemistry_optimization']['issues']
            ])
        if 'chemistry_interpretation' in report.validation_layers:
            all_chemistry_issues.extend([
                SemanticIssue(**i) for i in report.validation_layers['chemistry_interpretation']['issues']
            ])

        chemistry_critical = len([i for i in all_chemistry_issues if i.severity == 'CRITICAL'])
        chemistry_warnings = len([i for i in all_chemistry_issues if i.severity == 'WARNING'])

        # Update overall counts
        report.overall['critical_issues'] += chemistry_critical
        report.overall['warning_count'] += chemistry_warnings
        report.overall['passed'] = report.overall['passed'] and chemistry_critical == 0

        # Update recommendation if chemistry validation failed
        if chemistry_critical > 0:
            chemistry_recs = []
            for layer in ['chemistry_energy', 'chemistry_optimization', 'chemistry_interpretation']:
                if layer in report.validation_layers:
                    chemistry_recs.extend(report.validation_layers[layer].get('recommendations', []))

            if chemistry_recs:
                report.recommendation = "STOP: " + "; ".join(list(set(chemistry_recs))[:3])
            else:
                report.recommendation = "STOP: Fix chemistry validation issues"

        print()
        print("=" * 70)
        print("OVERALL ASSESSMENT (including chemistry)")
        print("=" * 70)
        print()

        if report.overall['passed']:
            print(f"[OK] VALIDATION PASSED")
            print(f"  Total warnings: {report.overall['warning_count']}")
        else:
            print(f"[X] VALIDATION FAILED")
            print(f"  Critical issues: {report.overall['critical_issues']}")
            print(f"  Recommendation: {report.recommendation}")

        print()
        print("=" * 70)

        return report

    def _compute_confidence_score(self, report: ValidationReport) -> float:
        """
        Compute overall confidence score (0-1).

        Factors:
        - Structural validity (0.3 weight)
        - Chemical validity (0.2 weight)
        - Semantic validity (0.3 weight)
        - Experimental validation (0.2 weight, if available)
        """
        scores = []

        # Structural score
        struct_weight = 0.2 if self._has_pfam else 0.3
        if report.validation_layers['structural']['passed']:
            issues = report.validation_layers['structural']['issues']
            warning_count = len([i for i in issues if i['severity'] == 'WARNING'])
            struct_score = max(0.5, 1.0 - warning_count * 0.1)
            scores.append(('structural', struct_weight, struct_score))
        else:
            scores.append(('structural', struct_weight, 0.0))

        # Chemical score
        chem_issues = report.validation_layers['chemical']['issues']
        critical_chem = len([i for i in chem_issues if i['severity'] == 'CRITICAL'])
        warning_chem = len([i for i in chem_issues if i['severity'] == 'WARNING'])
        if critical_chem > 0:
            chem_score = 0.0
        else:
            chem_score = max(0.5, 1.0 - warning_chem * 0.15)
        scores.append(('chemical', 0.2, chem_score))

        # Pfam domain score (if available)
        pfam_data = report.validation_layers.get('pfam', {})
        if pfam_data and 'issues' in pfam_data and pfam_data['issues']:
            pfam_issues_list = pfam_data['issues']
            pfam_warnings = len([i for i in pfam_issues_list if i['severity'] == 'WARNING'])
            # Pfam is primarily verification — warnings are investigative, not fatal
            pfam_score = max(0.6, 1.0 - pfam_warnings * 0.1)
            scores.append(('pfam', 0.1, pfam_score))

        # Semantic score
        sem_issues = report.validation_layers['semantic']['issues']
        critical_sem = len([i for i in sem_issues if i['severity'] == 'CRITICAL'])
        warning_sem = len([i for i in sem_issues if i['severity'] == 'WARNING'])
        if critical_sem > 0:
            sem_score = 0.0
        else:
            sem_score = max(0.5, 1.0 - warning_sem * 0.15)
        scores.append(('semantic', 0.3, sem_score))

        # Experimental score (if available)
        exp_data = report.validation_layers.get('experimental', {})
        if exp_data.get('status') != 'no_data' and len(exp_data) > 0:
            passed = sum(1 for v in exp_data.values() if isinstance(v, dict) and v.get('passed', False))
            total = len([v for v in exp_data.values() if isinstance(v, dict) and 'passed' in v])
            if total > 0:
                exp_score = passed / total
                scores.append(('experimental', 0.2, exp_score))

        # Compute weighted average
        if len(scores) < 4:
            # No experimental data - renormalize weights
            total_weight = sum(w for _, w, _ in scores)
            confidence = sum(w * s / total_weight for _, w, s in scores)
        else:
            confidence = sum(w * s for _, w, s in scores)

        return float(confidence)

    def _generate_critical_recommendation(
        self,
        struct_issues: List,
        chem_issues: List,
        semantic_issues: List
    ) -> str:
        """Generate specific recommendation based on critical issues"""
        recommendations = []

        struct_critical = [i for i in struct_issues if i.severity == 'CRITICAL']
        chem_critical = [i for i in chem_issues if i.severity == 'CRITICAL']
        semantic_critical = [i for i in semantic_issues if i.severity == 'CRITICAL']

        if struct_critical:
            recommendations.append("Fix structural geometry issues")

        if chem_critical:
            recommendations.append("Address critical chemical constraint violations")

        if semantic_critical:
            categories = set(i.category for i in semantic_critical)
            if 'math_physics_confusion' in categories:
                recommendations.append("Revise interpretation to avoid mathematical-physical confusion")
            if 'terminology' in categories:
                recommendations.append("Correct terminology usage")

        if not recommendations:
            return "Fix critical issues before proceeding"

        return "STOP: " + "; ".join(recommendations)

    def save_report(self, report: ValidationReport, output_path: str):
        """Save validation report to JSON file"""
        with open(output_path, 'w') as f:
            json.dump(asdict(report), f, indent=2)

    def generate_detailed_report(self, report: ValidationReport) -> str:
        """Generate detailed human-readable report"""
        lines = []
        lines.append("=" * 70)
        lines.append("KOMPOSOS-III COMPLETE VALIDATION REPORT")
        lines.append("=" * 70)
        lines.append(f"Timestamp: {report.timestamp}")
        lines.append(f"Sequence length: {report.sequence_length} residues")
        lines.append("")

        # Structural
        lines.append(self.structural_validator.generate_report(
            report.overall['passed'],
            [ValidationIssue(**i) for i in report.validation_layers['structural']['issues']]
        ))
        lines.append("")

        # Chemical
        lines.append(self.chemical_validator.generate_report(
            [ChemicalIssue(**i) for i in report.validation_layers['chemical']['issues']]
        ))
        lines.append("")

        # Pfam (if available)
        pfam_data = report.validation_layers.get('pfam', {})
        if pfam_data and 'issues' in pfam_data:
            lines.append(self.pfam_validator.generate_report(
                [PfamIssue(**i) for i in pfam_data['issues']]
            ))
            lines.append("")

        # Semantic
        lines.append(self.semantic_validator.generate_report(
            [SemanticIssue(**i) for i in report.validation_layers['semantic']['issues']]
        ))
        lines.append("")

        # Experimental (if available)
        if report.validation_layers.get('experimental', {}).get('status') != 'no_data':
            exp_data = report.validation_layers['experimental']
            if exp_data:
                # Convert dict back to ExperimentalValidation objects
                validations = {}
                for metric, data in exp_data.items():
                    if isinstance(data, dict) and 'metric' in data:
                        validations[metric] = ExperimentalValidation(**data)

                if validations:
                    lines.append(self.experimental_validator.generate_report(validations))
                    lines.append("")

        # Overall summary
        lines.append("=" * 70)
        lines.append("OVERALL SUMMARY")
        lines.append("=" * 70)
        lines.append(f"Status: {'PASSED' if report.overall['passed'] else 'FAILED'}")
        lines.append(f"Confidence Score: {report.overall['confidence_score']:.2%}")
        lines.append(f"Critical Issues: {report.overall['critical_issues']}")
        lines.append(f"Warnings: {report.overall['warning_count']}")
        lines.append(f"Recommendation: {report.recommendation}")
        lines.append("=" * 70)

        return "\n".join(lines)

    # Helper methods

    def _issue_to_dict(self, issue) -> Dict:
        """Convert issue dataclass to dict"""
        return {
            'severity': issue.severity,
            'category': issue.category,
            'message': issue.message,
            'details': issue.details
        }

    def _validation_to_dict(self, validation: ExperimentalValidation) -> Dict:
        """Convert validation dataclass to dict"""
        return {
            'metric': validation.metric,
            'predicted': validation.predicted,
            'experimental': validation.experimental,
            'passed': validation.passed,
            'details': validation.details
        }


# Convenience function
def validate_protein_interpretation(
    pdb_path: str,
    interpretation: str,
    experimental_data: Optional[Dict] = None
) -> ValidationReport:
    """
    Convenience function to validate a PDB file and interpretation.

    Args:
        pdb_path: Path to PDB file
        interpretation: Text interpretation to validate
        experimental_data: Optional experimental measurements

    Returns:
        Validation report
    """
    from pathlib import Path

    # Parse PDB (simplified - assumes CA atoms only)
    coords = []
    sequence = []
    confidence = []

    with open(pdb_path, 'r') as f:
        for line in f:
            if line.startswith('ATOM') and ' CA ' in line:
                x = float(line[30:38])
                y = float(line[38:46])
                z = float(line[46:54])
                coords.append([x, y, z])

                # Extract residue name (simplified)
                res = line[17:20].strip()
                aa_map = {
                    'ALA': 'A', 'CYS': 'C', 'ASP': 'D', 'GLU': 'E',
                    'PHE': 'F', 'GLY': 'G', 'HIS': 'H', 'ILE': 'I',
                    'LYS': 'K', 'LEU': 'L', 'MET': 'M', 'ASN': 'N',
                    'PRO': 'P', 'GLN': 'Q', 'ARG': 'R', 'SER': 'S',
                    'THR': 'T', 'VAL': 'V', 'TRP': 'W', 'TYR': 'Y'
                }
                sequence.append(aa_map.get(res, 'X'))

                # Extract B-factor as confidence (if available)
                try:
                    bfactor = float(line[60:66])
                    confidence.append(bfactor)
                except:
                    confidence.append(50.0)

    coords = np.array(coords)
    sequence = ''.join(sequence)
    confidence = np.array(confidence)

    validator = CompleteProteinValidator()
    return validator.validate_full_pipeline(
        sequence, coords, interpretation, confidence, experimental_data
    )
