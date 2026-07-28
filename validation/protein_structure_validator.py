# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""
Layer 1: Structural Validation

Validates basic geometric and structural properties:
- Bond lengths and angles
- Atomic clashes
- Ramachandran angles
- Compactness (radius of gyration)
- Coordinate completeness
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class ValidationIssue:
    """Single validation issue"""
    severity: str  # 'CRITICAL', 'WARNING', 'INFO'
    category: str  # 'geometry', 'clashes', 'ramachandran', etc.
    message: str
    details: Optional[Dict] = None


class ProteinStructureValidator:
    """
    Validates basic structural properties of protein coordinates.
    """

    def __init__(self):
        # Standard bond length ranges (Angstroms)
        self.bond_lengths = {
            'CA-CA': (3.6, 4.0),  # α-carbon spacing
            'CA-C': (1.4, 1.6),
            'C-N': (1.2, 1.4),
            'N-CA': (1.3, 1.5)
        }

        # Ramachandran allowed regions (phi, psi angles in degrees)
        # Approximate allowed regions for different secondary structures
        self.ramachandran_regions = {
            'alpha_helix': {'phi': (-70, -50), 'psi': (-50, -30)},
            'beta_sheet': {'phi': (-140, -100), 'psi': (100, 140)},
            'left_helix': {'phi': (40, 80), 'psi': (20, 60)}
        }

        # Van der Waals radii (Angstroms)
        self.vdw_radii = {
            'C': 1.70,
            'N': 1.55,
            'O': 1.52,
            'S': 1.80,
            'H': 1.20
        }

    def validate_structure(self, coords: np.ndarray, sequence: str) -> Tuple[bool, List[ValidationIssue]]:
        """
        Validate protein structure.

        Args:
            coords: Nx3 array of CA coordinates
            sequence: Amino acid sequence

        Returns:
            (is_valid, issues)
        """
        issues = []

        # Check 1: Coordinate completeness
        issues.extend(self._check_completeness(coords, sequence))

        # Check 2: Geometry (bond lengths)
        issues.extend(self._check_geometry(coords))

        # Check 3: Atomic clashes
        issues.extend(self._check_clashes(coords))

        # Check 4: Compactness (radius of gyration)
        issues.extend(self._check_compactness(coords, sequence))

        # Check 5: Ramachandran angles
        issues.extend(self._check_ramachandran(coords, sequence))

        # Check if any critical issues
        critical_count = sum(1 for issue in issues if issue.severity == 'CRITICAL')
        is_valid = critical_count == 0

        return is_valid, issues

    def _check_completeness(self, coords: np.ndarray, sequence: str) -> List[ValidationIssue]:
        """Check if coordinates are complete"""
        issues = []

        if coords is None or len(coords) == 0:
            issues.append(ValidationIssue(
                severity='CRITICAL',
                category='completeness',
                message='No coordinates provided'
            ))
            return issues

        expected_length = len(sequence)
        actual_length = len(coords)

        if actual_length != expected_length:
            issues.append(ValidationIssue(
                severity='CRITICAL',
                category='completeness',
                message=f'Coordinate length mismatch: {actual_length} coords vs {expected_length} residues',
                details={'expected': expected_length, 'actual': actual_length}
            ))

        # Check for NaN or infinite values
        if np.any(np.isnan(coords)) or np.any(np.isinf(coords)):
            issues.append(ValidationIssue(
                severity='CRITICAL',
                category='completeness',
                message='Coordinates contain NaN or infinite values'
            ))

        return issues

    def _check_geometry(self, coords: np.ndarray) -> List[ValidationIssue]:
        """Check bond lengths and angles"""
        issues = []

        if len(coords) < 2:
            return issues

        # Check CA-CA distances (consecutive residues)
        ca_distances = np.linalg.norm(coords[1:] - coords[:-1], axis=1)

        min_expected, max_expected = self.bond_lengths['CA-CA']
        outliers = np.where((ca_distances < min_expected) | (ca_distances > max_expected))[0]

        if len(outliers) > 0:
            outlier_percentage = 100 * len(outliers) / len(ca_distances)

            if outlier_percentage > 10:
                issues.append(ValidationIssue(
                    severity='CRITICAL',
                    category='geometry',
                    message=f'{outlier_percentage:.1f}% of CA-CA bonds outside normal range',
                    details={
                        'outlier_count': len(outliers),
                        'total_bonds': len(ca_distances),
                        'expected_range': (min_expected, max_expected),
                        'min_distance': float(ca_distances.min()),
                        'max_distance': float(ca_distances.max())
                    }
                ))
            elif outlier_percentage > 5:
                issues.append(ValidationIssue(
                    severity='WARNING',
                    category='geometry',
                    message=f'{outlier_percentage:.1f}% of CA-CA bonds outside normal range',
                    details={
                        'outlier_count': len(outliers),
                        'total_bonds': len(ca_distances)
                    }
                ))

        return issues

    def _check_clashes(self, coords: np.ndarray, threshold: float = 2.0) -> List[ValidationIssue]:
        """
        Check for atomic clashes (atoms too close together).

        Args:
            coords: Nx3 array of coordinates
            threshold: Minimum allowed distance (Angstroms)
        """
        issues = []

        if len(coords) < 2:
            return issues

        # Compute pairwise distances
        # Only check non-adjacent residues (skip i, i+1, i+2)
        clash_count = 0
        clash_pairs = []

        for i in range(len(coords)):
            for j in range(i + 3, len(coords)):  # Skip adjacent residues
                distance = np.linalg.norm(coords[i] - coords[j])
                if distance < threshold:
                    clash_count += 1
                    if len(clash_pairs) < 10:  # Store first 10 for reporting
                        clash_pairs.append((i, j, distance))

        if clash_count > 0:
            clash_percentage = 100 * clash_count / (len(coords) * (len(coords) - 3) / 2)

            if clash_count > len(coords) * 0.05:  # >5% of residues involved
                issues.append(ValidationIssue(
                    severity='CRITICAL',
                    category='clashes',
                    message=f'{clash_count} atomic clashes detected (<{threshold}Å)',
                    details={
                        'clash_count': clash_count,
                        'clash_percentage': clash_percentage,
                        'examples': [(int(i), int(j), float(d)) for i, j, d in clash_pairs[:5]]
                    }
                ))
            else:
                issues.append(ValidationIssue(
                    severity='WARNING',
                    category='clashes',
                    message=f'{clash_count} minor clashes detected',
                    details={'clash_count': clash_count}
                ))

        return issues

    def _check_compactness(self, coords: np.ndarray, sequence: str) -> List[ValidationIssue]:
        """Check radius of gyration"""
        issues = []

        # Compute radius of gyration
        center = np.mean(coords, axis=0)
        distances = np.linalg.norm(coords - center, axis=1)
        Rg = np.sqrt(np.mean(distances ** 2))

        # Expected Rg from empirical relation: Rg = 2.2 * N^0.38
        N = len(sequence)
        Rg_expected = 2.2 * (N ** 0.38)
        Rg_ratio = Rg / Rg_expected

        if Rg_ratio < 0.5:
            issues.append(ValidationIssue(
                severity='WARNING',
                category='compactness',
                message=f'Structure unusually compact (Rg ratio = {Rg_ratio:.2f})',
                details={
                    'Rg': float(Rg),
                    'Rg_expected': float(Rg_expected),
                    'Rg_ratio': float(Rg_ratio)
                }
            ))
        elif Rg_ratio > 2.0:
            issues.append(ValidationIssue(
                severity='WARNING',
                category='compactness',
                message=f'Structure unusually extended (Rg ratio = {Rg_ratio:.2f})',
                details={
                    'Rg': float(Rg),
                    'Rg_expected': float(Rg_expected),
                    'Rg_ratio': float(Rg_ratio)
                }
            ))

        return issues

    def _check_ramachandran(self, coords: np.ndarray, sequence: str) -> List[ValidationIssue]:
        """
        Check backbone dihedral angles (Ramachandran plot).

        Note: This is simplified - only checks CA positions.
        Full validation would need backbone N, CA, C, O atoms.
        """
        issues = []

        if len(coords) < 4:
            return issues

        # Approximate phi/psi from CA positions
        # This is a simplified check - real Ramachandran needs full backbone
        outliers = 0

        for i in range(1, len(coords) - 2):
            # Vector from CA(i-1) to CA(i)
            v1 = coords[i] - coords[i-1]
            # Vector from CA(i) to CA(i+1)
            v2 = coords[i+1] - coords[i]
            # Vector from CA(i+1) to CA(i+2)
            v3 = coords[i+2] - coords[i+1]

            # Approximate dihedral angle
            # This is simplified - real calculation needs 4 atoms
            angle1 = np.arccos(np.clip(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)), -1, 1))
            angle2 = np.arccos(np.clip(np.dot(v2, v3) / (np.linalg.norm(v2) * np.linalg.norm(v3)), -1, 1))

            # Check if angles are in extreme ranges (simplified)
            angle1_deg = np.degrees(angle1)
            angle2_deg = np.degrees(angle2)

            # Very crude check - angles should be neither too small nor too large
            if angle1_deg < 60 or angle1_deg > 150 or angle2_deg < 60 or angle2_deg > 150:
                outliers += 1

        outlier_percentage = 100 * outliers / max(len(coords) - 3, 1)

        if outlier_percentage > 15:  # >15% outliers is unusual
            issues.append(ValidationIssue(
                severity='WARNING',
                category='ramachandran',
                message=f'{outlier_percentage:.1f}% of residues have unusual backbone angles',
                details={
                    'outlier_count': outliers,
                    'total_residues': len(coords) - 3,
                    'note': 'Simplified check using CA atoms only'
                }
            ))

        return issues

    def generate_report(self, is_valid: bool, issues: List[ValidationIssue]) -> str:
        """Generate human-readable validation report"""
        lines = []
        lines.append("=" * 70)
        lines.append("STRUCTURAL VALIDATION REPORT")
        lines.append("=" * 70)
        lines.append("")

        if is_valid:
            lines.append("[OK] STRUCTURE PASSED ALL CRITICAL CHECKS")
        else:
            critical = [i for i in issues if i.severity == 'CRITICAL']
            lines.append(f"[X] STRUCTURE FAILED: {len(critical)} critical issue(s)")

        lines.append("")

        # Group by severity
        for severity in ['CRITICAL', 'WARNING', 'INFO']:
            severity_issues = [i for i in issues if i.severity == severity]
            if severity_issues:
                lines.append(f"{severity} ({len(severity_issues)}):")
                for issue in severity_issues:
                    lines.append(f"  • [{issue.category}] {issue.message}")
                    if issue.details:
                        for key, value in issue.details.items():
                            if key != 'examples':
                                lines.append(f"    - {key}: {value}")
                lines.append("")

        if not issues:
            lines.append("No issues detected.")
            lines.append("")

        lines.append("=" * 70)

        return "\n".join(lines)


def validate_structure_file(pdb_path: str) -> Tuple[bool, List[ValidationIssue]]:
    """
    Convenience function to validate a PDB file.

    Args:
        pdb_path: Path to PDB file

    Returns:
        (is_valid, issues)
    """
    from pathlib import Path

    # Parse PDB (simplified - assumes CA atoms only)
    coords = []
    sequence = []

    with open(pdb_path, 'r') as f:
        for line in f:
            if line.startswith('ATOM') and ' CA ' in line:
                x = float(line[30:38])
                y = float(line[38:46])
                z = float(line[46:54])
                coords.append([x, y, z])

                # Extract residue name (simplified)
                res = line[17:20].strip()
                # Map 3-letter to 1-letter (simplified)
                aa_map = {
                    'ALA': 'A', 'CYS': 'C', 'ASP': 'D', 'GLU': 'E',
                    'PHE': 'F', 'GLY': 'G', 'HIS': 'H', 'ILE': 'I',
                    'LYS': 'K', 'LEU': 'L', 'MET': 'M', 'ASN': 'N',
                    'PRO': 'P', 'GLN': 'Q', 'ARG': 'R', 'SER': 'S',
                    'THR': 'T', 'VAL': 'V', 'TRP': 'W', 'TYR': 'Y'
                }
                sequence.append(aa_map.get(res, 'X'))

    coords = np.array(coords)
    sequence = ''.join(sequence)

    validator = ProteinStructureValidator()
    return validator.validate_structure(coords, sequence)
