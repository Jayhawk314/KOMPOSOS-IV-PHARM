# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""
Layer 2: Chemical Constraint Validation

Validates physical chemistry properties:
- Hydrogen bonding networks
- Hydrophobic core burial
- Electrostatic interactions (salt bridges)
- Disulfide bonds
- Secondary structure propensities
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class ChemicalIssue:
    """Chemical validation issue"""
    severity: str
    category: str
    message: str
    details: Optional[Dict] = None


class ChemicalConstraintValidator:
    """
    Validates chemical and physical properties of protein structures.
    """

    def __init__(self):
        # Amino acid properties
        self.hydrophobic = set('AILMFVPWG')
        self.polar = set('STNQCY')
        self.charged_positive = set('KRH')
        self.charged_negative = set('DE')
        self.aromatic = set('FYW')

        # Secondary structure propensities
        self.helix_breakers = set('PG')  # Proline and Glycine
        self.helix_formers = set('AELM')
        self.sheet_formers = set('VIF')

        # H-bond geometries
        self.hbond_distance_range = (2.5, 3.5)  # Angstroms
        self.salt_bridge_distance_range = (2.5, 4.5)  # Angstroms
        self.disulfide_distance_range = (1.8, 2.5)  # Angstroms

    def validate_chemistry(self, coords: np.ndarray, sequence: str,
                          confidence: Optional[np.ndarray] = None) -> List[ChemicalIssue]:
        """
        Validate chemical properties of structure.

        Args:
            coords: Nx3 array of CA coordinates
            sequence: Amino acid sequence
            confidence: Optional pLDDT scores

        Returns:
            List of chemical issues
        """
        issues = []

        # Check 1: Hydrophobic core
        issues.extend(self._check_hydrophobic_core(coords, sequence))

        # Check 2: Hydrogen bonding (approximate)
        issues.extend(self._check_hydrogen_bonding(coords, sequence))

        # Check 3: Electrostatic interactions
        issues.extend(self._check_electrostatics(coords, sequence))

        # Check 4: Disulfide bonds
        issues.extend(self._check_disulfide_bonds(coords, sequence))

        # Check 5: Secondary structure propensities
        issues.extend(self._check_secondary_structure(coords, sequence))

        # Check 6: Confidence-based warnings
        if confidence is not None:
            issues.extend(self._check_confidence(confidence, sequence))

        return issues

    def _check_hydrophobic_core(self, coords: np.ndarray, sequence: str) -> List[ChemicalIssue]:
        """Check if hydrophobic residues are buried in core"""
        issues = []

        if len(coords) < 10:
            return issues

        # Compute center of mass
        center = np.mean(coords, axis=0)

        # Compute distance of each residue from center
        distances = np.linalg.norm(coords - center, axis=1)

        # Identify hydrophobic residues
        hydrophobic_indices = [i for i, aa in enumerate(sequence) if aa in self.hydrophobic]

        if len(hydrophobic_indices) == 0:
            return issues

        # Check how many hydrophobic residues are buried (inner 50% of structure)
        median_distance = np.median(distances)
        buried_hydrophobic = sum(1 for i in hydrophobic_indices if distances[i] < median_distance)

        burial_ratio = buried_hydrophobic / len(hydrophobic_indices)

        if burial_ratio < 0.4:  # <40% buried is unusual
            issues.append(ChemicalIssue(
                severity='WARNING',
                category='hydrophobic',
                message=f'Only {burial_ratio*100:.1f}% of hydrophobic residues are buried',
                details={
                    'buried_count': buried_hydrophobic,
                    'total_hydrophobic': len(hydrophobic_indices),
                    'burial_ratio': burial_ratio,
                    'recommendation': 'Hydrophobic residues should cluster in protein core'
                }
            ))

        return issues

    def _check_hydrogen_bonding(self, coords: np.ndarray, sequence: str) -> List[ChemicalIssue]:
        """
        Check for hydrogen bonding patterns (simplified).

        Note: This is approximate using CA positions only.
        Real H-bond detection requires backbone N, H, O atoms.
        """
        issues = []

        if len(coords) < 5:
            return issues

        # Count potential H-bonds based on CA-CA distances
        # Residues 3-5 positions apart can form H-bonds
        hbond_count = 0

        for i in range(len(coords)):
            for j in range(i + 3, min(i + 6, len(coords))):
                distance = np.linalg.norm(coords[i] - coords[j])
                # Approximate: CA-CA distance ~6Å for H-bonded residues
                if 5.0 < distance < 7.0:
                    hbond_count += 1

        # Expected: ~1 H-bond per 3 residues in structured regions
        expected_hbonds = len(sequence) / 3
        hbond_ratio = hbond_count / expected_hbonds if expected_hbonds > 0 else 0

        if hbond_ratio < 0.5:  # <50% of expected
            issues.append(ChemicalIssue(
                severity='WARNING',
                category='hydrogen_bonding',
                message=f'Low hydrogen bonding: {hbond_count} detected vs {expected_hbonds:.0f} expected',
                details={
                    'detected': hbond_count,
                    'expected': int(expected_hbonds),
                    'ratio': hbond_ratio,
                    'note': 'Simplified check using CA atoms only'
                }
            ))

        return issues

    def _check_electrostatics(self, coords: np.ndarray, sequence: str) -> List[ChemicalIssue]:
        """Check for salt bridges and charge distributions"""
        issues = []

        # Find charged residues
        positive_indices = [i for i, aa in enumerate(sequence) if aa in self.charged_positive]
        negative_indices = [i for i, aa in enumerate(sequence) if aa in self.charged_negative]

        if len(positive_indices) == 0 or len(negative_indices) == 0:
            return issues

        # Look for salt bridges (opposite charges close together)
        salt_bridges = 0

        for i in positive_indices:
            for j in negative_indices:
                if abs(i - j) > 3:  # Non-adjacent residues
                    distance = np.linalg.norm(coords[i] - coords[j])
                    if self.salt_bridge_distance_range[0] < distance < self.salt_bridge_distance_range[1]:
                        salt_bridges += 1

        total_charged = len(positive_indices) + len(negative_indices)

        if total_charged > 10 and salt_bridges == 0:
            issues.append(ChemicalIssue(
                severity='INFO',
                category='electrostatics',
                message=f'{total_charged} charged residues but no salt bridges detected',
                details={
                    'positive': len(positive_indices),
                    'negative': len(negative_indices),
                    'salt_bridges': salt_bridges,
                    'note': 'May indicate unstructured or surface-exposed charges'
                }
            ))

        return issues

    def _check_disulfide_bonds(self, coords: np.ndarray, sequence: str) -> List[ChemicalIssue]:
        """Check for disulfide bonds between cysteines"""
        issues = []

        # Find cysteine residues
        cys_indices = [i for i, aa in enumerate(sequence) if aa == 'C']

        if len(cys_indices) < 2:
            return issues

        # Look for disulfide bonds (Cys-Cys close together)
        disulfides = 0

        for i in range(len(cys_indices)):
            for j in range(i + 1, len(cys_indices)):
                idx_i, idx_j = cys_indices[i], cys_indices[j]
                if abs(idx_i - idx_j) > 3:  # Non-adjacent
                    distance = np.linalg.norm(coords[idx_i] - coords[idx_j])
                    # CA-CA distance for disulfide is ~3.5-6Å
                    if 3.5 < distance < 6.5:
                        disulfides += 1

        if len(cys_indices) >= 4 and disulfides == 0:
            issues.append(ChemicalIssue(
                severity='INFO',
                category='disulfide',
                message=f'{len(cys_indices)} cysteines present but no disulfide bonds detected',
                details={
                    'cysteine_count': len(cys_indices),
                    'disulfide_count': disulfides,
                    'note': 'May be reduced state or separated in structure'
                }
            ))

        return issues

    def _check_secondary_structure(self, coords: np.ndarray, sequence: str) -> List[ChemicalIssue]:
        """Check secondary structure propensities"""
        issues = []

        if len(coords) < 10:
            return issues

        # Detect helical regions (consecutive residues with regular spacing)
        helix_regions = []
        current_helix = []

        for i in range(len(coords) - 3):
            # Check if next 4 residues form helix-like spacing
            v1 = coords[i+1] - coords[i]
            v2 = coords[i+2] - coords[i+1]
            v3 = coords[i+3] - coords[i+2]

            d1 = np.linalg.norm(v1)
            d2 = np.linalg.norm(v2)
            d3 = np.linalg.norm(v3)

            # Helix has regular CA-CA spacing ~3.8Å
            if 3.6 < d1 < 4.0 and 3.6 < d2 < 4.0 and 3.6 < d3 < 4.0:
                if len(current_helix) == 0 or i == current_helix[-1] + 1:
                    current_helix.append(i)
                else:
                    if len(current_helix) >= 4:
                        helix_regions.append(current_helix)
                    current_helix = [i]

        if len(current_helix) >= 4:
            helix_regions.append(current_helix)

        # Check if helix-breakers (P, G) are in helical regions
        helix_breaker_violations = 0

        for helix in helix_regions:
            for i in helix:
                if i < len(sequence) and sequence[i] in self.helix_breakers:
                    helix_breaker_violations += 1

        if helix_breaker_violations > 0:
            issues.append(ChemicalIssue(
                severity='INFO',
                category='secondary_structure',
                message=f'{helix_breaker_violations} helix-breaking residues (P/G) found in helical regions',
                details={
                    'violations': helix_breaker_violations,
                    'helix_regions': len(helix_regions),
                    'note': 'Proline and Glycine typically disrupt helices'
                }
            ))

        return issues

    def _check_confidence(self, confidence: np.ndarray, sequence: str) -> List[ChemicalIssue]:
        """Check pLDDT confidence scores"""
        issues = []

        mean_confidence = np.mean(confidence)
        low_confidence_count = np.sum(confidence < 50)
        low_confidence_percentage = 100 * low_confidence_count / len(confidence)

        if mean_confidence < 70:
            issues.append(ChemicalIssue(
                severity='WARNING',
                category='confidence',
                message=f'Low overall confidence: mean pLDDT = {mean_confidence:.1f}',
                details={
                    'mean_plddt': mean_confidence,
                    'recommendation': 'Interpret structural features cautiously'
                }
            ))

        if low_confidence_percentage > 20:
            issues.append(ChemicalIssue(
                severity='WARNING',
                category='confidence',
                message=f'{low_confidence_percentage:.1f}% of residues have pLDDT < 50',
                details={
                    'low_confidence_count': int(low_confidence_count),
                    'total_residues': len(confidence),
                    'percentage': low_confidence_percentage,
                    'recommendation': 'These regions likely disordered or low accuracy'
                }
            ))

        return issues

    def generate_report(self, issues: List[ChemicalIssue]) -> str:
        """Generate human-readable report"""
        lines = []
        lines.append("=" * 70)
        lines.append("CHEMICAL CONSTRAINT VALIDATION REPORT")
        lines.append("=" * 70)
        lines.append("")

        if not issues:
            lines.append("[OK] ALL CHEMICAL CHECKS PASSED")
            lines.append("")
        else:
            # Group by severity
            for severity in ['CRITICAL', 'WARNING', 'INFO']:
                severity_issues = [i for i in issues if i.severity == severity]
                if severity_issues:
                    lines.append(f"{severity} ({len(severity_issues)}):")
                    for issue in severity_issues:
                        lines.append(f"  • [{issue.category}] {issue.message}")
                        if issue.details:
                            for key, value in issue.details.items():
                                if key != 'recommendation' and key != 'note':
                                    lines.append(f"    - {key}: {value}")
                            if 'recommendation' in issue.details:
                                lines.append(f"    -> {issue.details['recommendation']}")
                            if 'note' in issue.details:
                                lines.append(f"    [i] {issue.details['note']}")
                    lines.append("")

        lines.append("=" * 70)
        return "\n".join(lines)
