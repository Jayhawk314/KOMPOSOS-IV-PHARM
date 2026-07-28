# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""
Van der Waals Constraints Module
==================================

Van der Waals distance constraints and optimal packing analysis.

Physical Constraints:
- Minimum distances (no overlap/clashes)
- Optimal packing distances for protein cores
- Atom-type specific radii

Van der Waals Radii (Å):
- Carbon (C): 1.70
- Nitrogen (N): 1.55
- Oxygen (O): 1.52
- Sulfur (S): 1.80
- Hydrogen (H): 1.20

CA-CA Optimal Distances by Contact Type:
- Helix sequential: 5.4-6.0 Å
- Helix turn (i,i+3): 5.5-6.5 Å
- Helix H-bond (i,i+4): 5.8-6.8 Å
- Sheet parallel: 4.5-5.5 Å
- Sheet antiparallel: 4.8-5.8 Å
- General contacts: 6-8 Å (optimal packing)
- Minimum separation: 3.0 Å (non-adjacent residues)

References:
- Standard vdW radii from physical chemistry literature
- Protein structure analysis from PDB statistics
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
from enum import Enum
import numpy as np


class ClashSeverity(Enum):
    """Severity levels for steric clashes."""
    NONE = "none"
    WARNING = "warning"      # 2.0-2.5 Å (mild overlap)
    CRITICAL = "critical"     # < 2.0 Å (severe overlap)


@dataclass
class StericClash:
    """Represents a steric clash between two residues."""
    residue_i: int
    residue_j: int
    distance: float
    severity: ClashSeverity
    expected_min: float = 3.0  # Minimum expected distance

    def overlap_distance(self) -> float:
        """How much the residues overlap beyond minimum."""
        return max(0, self.expected_min - self.distance)


class VanDerWaalsConstraints:
    """
    Van der Waals distance constraints for proteins.

    Checks:
    - Steric clashes (atoms too close)
    - Optimal packing (appropriate contact distances)
    - Overall packing density
    """

    def __init__(self):
        """Initialize vdW constraints with physical parameters."""

        # Van der Waals radii (Å)
        self.vdw_radii = {
            'C': 1.70,
            'N': 1.55,
            'O': 1.52,
            'S': 1.80,
            'H': 1.20
        }

        # CA-CA optimal distances by contact type (Å)
        self.ca_distances = {
            'helix_sequential': (5.4, 6.0),
            'helix_turn': (5.5, 6.5),       # i, i+3
            'helix_hbond': (5.8, 6.8),      # i, i+4
            'sheet_parallel': (4.5, 5.5),
            'sheet_antiparallel': (4.8, 5.8),
            'contact_optimal': (6.0, 8.0),  # General contacts
            'loop': (3.8, 10.0)             # Variable
        }

        # Minimum allowed distances
        self.min_distance_adjacent = 3.5  # Adjacent residues (i, i+1)
        self.min_distance_nonadjacent = 3.0  # Non-adjacent
        self.critical_clash_threshold = 2.0  # Severe clashes

    def check_clashes(self, coords: np.ndarray, threshold: Optional[float] = None) -> List[StericClash]:
        """
        Check for steric clashes (atoms too close).

        Args:
            coords: Nx3 CA coordinates
            threshold: Minimum allowed CA-CA distance (Å). If None, uses default 3.0Å

        Returns:
            List of StericClash objects
        """
        if threshold is None:
            threshold = self.min_distance_nonadjacent

        clashes = []
        N = len(coords)

        for i in range(N):
            for j in range(i+3, N):  # Skip adjacent and near-adjacent residues
                distance = np.linalg.norm(coords[i] - coords[j])

                if distance < threshold:
                    # Determine severity
                    if distance < self.critical_clash_threshold:
                        severity = ClashSeverity.CRITICAL
                    elif distance < 2.5:
                        severity = ClashSeverity.WARNING
                    else:
                        severity = ClashSeverity.WARNING

                    clashes.append(StericClash(
                        residue_i=i,
                        residue_j=j,
                        distance=distance,
                        severity=severity,
                        expected_min=threshold
                    ))

        return clashes

    def optimal_packing_score(self, coords: np.ndarray, contacts: List[Tuple[int, int]]) -> float:
        """
        Score how well structure satisfies vdW packing.

        Optimal CA-CA distance for contacts: 6-8 Å
        Acceptable range: 5-9 Å
        Poor: < 5 Å (too tight) or > 9 Å (too loose)

        Args:
            coords: Nx3 CA coordinates
            contacts: List of (i, j) residue pairs that are in contact

        Returns:
            Score 0-1 (1 = optimal packing)
        """
        if not contacts:
            return 0.0

        scores = []

        for i, j in contacts:
            distance = np.linalg.norm(coords[i] - coords[j])

            # Score based on distance from optimal range
            if 6.0 <= distance <= 8.0:
                # Optimal range
                scores.append(1.0)
            elif 5.0 <= distance < 6.0 or 8.0 < distance <= 9.0:
                # Acceptable range
                # Linear decay from 1.0 to 0.7
                if distance < 6.0:
                    score = 0.7 + 0.3 * (distance - 5.0)
                else:
                    score = 1.0 - 0.3 * (distance - 8.0)
                scores.append(score)
            elif 4.5 <= distance < 5.0 or 9.0 < distance <= 10.0:
                # Marginal range
                scores.append(0.5)
            else:
                # Poor packing
                scores.append(0.3)

        return np.mean(scores)

    def analyze_packing_quality(self, coords: np.ndarray, contacts: List[Tuple[int, int]]) -> Dict:
        """
        Comprehensive packing quality analysis.

        Args:
            coords: Nx3 CA coordinates
            contacts: List of (i, j) contact pairs

        Returns:
            Dictionary with packing metrics
        """
        N = len(coords)

        # Check clashes
        clashes = self.check_clashes(coords)
        critical_clashes = [c for c in clashes if c.severity == ClashSeverity.CRITICAL]
        warning_clashes = [c for c in clashes if c.severity == ClashSeverity.WARNING]

        # Check packing score
        packing_score = self.optimal_packing_score(coords, contacts)

        # Analyze contact distances
        contact_distances = []
        for i, j in contacts:
            dist = np.linalg.norm(coords[i] - coords[j])
            contact_distances.append(dist)

        contact_distances = np.array(contact_distances) if contact_distances else np.array([])

        # Overall assessment
        has_critical = len(critical_clashes) > 0
        has_warnings = len(warning_clashes) > 0
        good_packing = packing_score > 0.7

        if has_critical:
            quality = "POOR - Critical clashes present"
        elif packing_score < 0.5:
            quality = "POOR - Suboptimal packing"
        elif has_warnings and packing_score < 0.7:
            quality = "FAIR - Some issues present"
        elif good_packing and not has_warnings:
            quality = "EXCELLENT - Well-packed structure"
        else:
            quality = "GOOD - Acceptable packing"

        return {
            'quality': quality,
            'packing_score': float(packing_score),
            'num_contacts': len(contacts),
            'num_clashes': len(clashes),
            'num_critical_clashes': len(critical_clashes),
            'num_warning_clashes': len(warning_clashes),
            'mean_contact_distance': float(np.mean(contact_distances)) if len(contact_distances) > 0 else 0.0,
            'contact_distance_std': float(np.std(contact_distances)) if len(contact_distances) > 0 else 0.0,
            'clashes': [
                {
                    'residue_i': c.residue_i,
                    'residue_j': c.residue_j,
                    'distance': float(c.distance),
                    'severity': c.severity.value,
                    'overlap': float(c.overlap_distance())
                }
                for c in clashes
            ]
        }

    def validate_structure(self, coords: np.ndarray, contacts: List[Tuple[int, int]]) -> Tuple[bool, Dict]:
        """
        Validate structure against vdW constraints.

        Args:
            coords: Nx3 CA coordinates
            contacts: List of (i, j) contact pairs

        Returns:
            (is_valid, analysis_dict)
        """
        analysis = self.analyze_packing_quality(coords, contacts)

        # Structure is valid if:
        # 1. No critical clashes
        # 2. Packing score > 0.5
        is_valid = (analysis['num_critical_clashes'] == 0 and
                   analysis['packing_score'] > 0.5)

        return is_valid, analysis


# Convenience functions
def check_clashes(coords: np.ndarray, threshold: float = 3.0) -> List[StericClash]:
    """Convenience function to check for clashes."""
    vdw = VanDerWaalsConstraints()
    return vdw.check_clashes(coords, threshold)


def optimal_packing_score(coords: np.ndarray, contacts: List[Tuple[int, int]]) -> float:
    """Convenience function to compute packing score."""
    vdw = VanDerWaalsConstraints()
    return vdw.optimal_packing_score(coords, contacts)


# Testing
if __name__ == "__main__":
    print("=" * 70)
    print("Van der Waals Constraints - Test")
    print("=" * 70)
    print()

    # Test 1: Well-packed structure (helical)
    print("Test 1: Helical structure (well-packed)")
    N = 12
    coords = np.zeros((N, 3))
    for i in range(N):
        angle = i * 100 * np.pi / 180
        coords[i] = [2.3 * np.cos(angle), 2.3 * np.sin(angle), i * 1.5]

    # Contacts: i to i+4 (helix H-bonds)
    contacts = [(i, i+4) for i in range(N-4)]

    vdw = VanDerWaalsConstraints()
    analysis = vdw.analyze_packing_quality(coords, contacts)

    print(f"  Quality: {analysis['quality']}")
    print(f"  Packing score: {analysis['packing_score']:.2f}")
    print(f"  Clashes: {analysis['num_clashes']}")
    print(f"  Mean contact distance: {analysis['mean_contact_distance']:.2f} Å")
    print()

    # Test 2: Structure with clashes
    print("Test 2: Structure with clashes")
    # Create coords with some clashes (residues too close)
    coords_clash = coords.copy()
    coords_clash[5] = coords_clash[8]  # Put residues 5 and 8 at same position

    clashes = vdw.check_clashes(coords_clash)
    print(f"  Number of clashes: {len(clashes)}")
    if clashes:
        print("  Clashes detected:")
        for clash in clashes[:5]:  # Show first 5
            print(f"    Residues {clash.residue_i}-{clash.residue_j}: "
                  f"{clash.distance:.2f} Å ({clash.severity.value})")
    print()

    # Test 3: Validation
    print("Test 3: Validation")
    is_valid_good, _ = vdw.validate_structure(coords, contacts)
    is_valid_bad, _ = vdw.validate_structure(coords_clash, contacts)

    print(f"  Well-packed structure valid: {is_valid_good}")
    print(f"  Clashing structure valid: {is_valid_bad}")
