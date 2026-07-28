# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""
Hydrogen Bonding Module
=======================

Validates and predicts hydrogen bonding patterns in protein structures.

Physical Constraints (from research):
- Donor-acceptor distance: 2.5-3.5 Å (tight), 3.0-3.9 Å (relaxed)
- H-acceptor distance: < 2.5 Å optimal
- Angle constraints: D-H...A angle > 120°, optimal ~155-160°
- Per residue: 0-5 H-bonds expected
- Secondary structure patterns:
  * α-helix: i→i+4 backbone H-bonds, CA-CA ~6Å
  * β-sheet: inter-strand H-bonds, CA-CA ~5-6Å (antiparallel), ~4.5-5.5Å (parallel)

Integration with Category Theory:
- H-bonds become morphisms in the categorical store
- Strength (based on geometry) becomes morphism confidence
- Composition: H-bond networks form paths through the category

References:
- RSC Physical Chemistry (2025): "Determinants of hydrogen bond distances in proteins"
  https://pubs.rsc.org/en/content/articlelanding/2025/cp/d5cp00511f
- Hubbard & Haider (2010): "Hydrogen Bonds in Proteins: Role and Strength"
- Proteopedia: https://proteopedia.org/wiki/index.php/Hydrogen_bonds
"""

from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple, Optional
from enum import Enum
import numpy as np
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from data.store import StoredMorphism
    STORE_AVAILABLE = True
except ImportError:
    STORE_AVAILABLE = False
    StoredMorphism = None


class HBondType(Enum):
    """Types of hydrogen bonds in proteins."""
    HELIX_BACKBONE = "helix_backbone"          # α-helix i→i+4
    SHEET_BACKBONE = "sheet_backbone"          # β-sheet inter-strand
    SIDECHAIN = "sidechain"                     # Side chain H-bonds
    BACKBONE_SIDECHAIN = "backbone_sidechain"  # Mixed BB-SC
    LONG_RANGE = "long_range"                   # Non-local contacts


@dataclass
class HydrogenBond:
    """
    Represents a hydrogen bond in a protein structure.

    Attributes:
        donor: Residue index of donor
        acceptor: Residue index of acceptor
        bond_type: Type of H-bond (helix, sheet, sidechain, etc.)
        distance: CA-CA distance (Å) - proxy for actual H-bond distance
        confidence: Confidence score 0-1 based on geometry
        donor_aa: Amino acid type at donor position
        acceptor_aa: Amino acid type at acceptor position
    """
    donor: int
    acceptor: int
    bond_type: HBondType
    distance: float
    confidence: float
    donor_aa: Optional[str] = None
    acceptor_aa: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary for storage."""
        return {
            'donor': self.donor,
            'acceptor': self.acceptor,
            'type': self.bond_type.value,
            'distance': float(self.distance),
            'confidence': float(self.confidence),
            'donor_aa': self.donor_aa,
            'acceptor_aa': self.acceptor_aa
        }


class HydrogenBondValidator:
    """
    Validates and predicts hydrogen bonding patterns.

    This class implements physical chemistry constraints for H-bonds and
    integrates with KOMPOSOS-III's category theory framework by representing
    H-bonds as morphisms with strength-based confidence scores.
    """

    def __init__(self):
        """Initialize H-bond validator with chemical knowledge."""

        # H-bond donors by residue type (can donate H via sidechain)
        # Based on proteopedia and biochemistry textbooks
        # NOTE: ALL residues also donate via backbone N-H (not listed here)
        self.donors = {
            'K': ['NZ-HZ'],  # Lysine (charged)
            'R': ['NE-HE', 'NH1-HH1', 'NH2-HH2'],  # Arginine (charged)
            'W': ['NE1-HE1'],  # Tryptophan (indole)
            'H': ['ND1-HD1', 'NE2-HE2'],  # Histidine (imidazole, can be charged)
            'S': ['OG-HG'],  # Serine (hydroxyl)
            'T': ['OG1-HG1'],  # Threonine (hydroxyl)
            'Y': ['OH-HH'],  # Tyrosine (phenolic OH)
            'C': ['SG-HG'],  # Cysteine (thiol, weak donor)
            'N': ['N-H', 'ND2-HD2'],  # Asparagine (backbone amide + sidechain amide)
            'Q': ['NE2-HE2']  # Glutamine (amide)
        }

        # H-bond acceptors by residue type (can accept H via sidechain)
        # NOTE: ALL residues also accept via backbone C=O (not listed here)
        self.acceptors = {
            'D': ['OD1', 'OD2'],  # Aspartate (charged)
            'E': ['OE1', 'OE2'],  # Glutamate (charged)
            'N': ['OD1'],  # Asparagine (amide oxygen)
            'Q': ['OE1'],  # Glutamine (amide oxygen)
            'S': ['OG'],  # Serine (hydroxyl)
            'T': ['OG1'],  # Threonine (hydroxyl)
            'Y': ['OH'],  # Tyrosine (phenolic OH)
            'H': ['ND1', 'NE2'],  # Histidine (imidazole nitrogens)
            'M': ['SD']  # Methionine (sulfur, weak acceptor)
        }

        # Distance constraints (Å)
        self.distance_constraints = {
            'helix_backbone': (5.5, 6.5),      # α-helix i, i+4 CA-CA
            'helix_turn': (5.0, 6.0),          # α-helix i, i+3 CA-CA
            'sheet_parallel': (4.5, 5.5),      # β-sheet parallel CA-CA
            'sheet_antiparallel': (4.8, 5.8),  # β-sheet antiparallel CA-CA
            'sidechain': (3.0, 8.0),           # Side chain H-bonds (CA-CA proxy)
            'backbone_sidechain': (3.0, 7.0),  # BB-SC H-bonds
        }

        # Ideal distances for confidence scoring
        self.ideal_distances = {
            'helix_backbone': 6.0,
            'sheet_parallel': 5.0,
            'sheet_antiparallel': 5.3,
            'sidechain': 5.5,
        }

    def can_form_hbond(self, aa1: str, aa2: str) -> Tuple[bool, str]:
        """
        Check if two amino acids can form a hydrogen bond.

        Args:
            aa1: First amino acid (one-letter code)
            aa2: Second amino acid (one-letter code)

        Returns:
            (can_bond, bond_description)
        """
        aa1 = aa1.upper()
        aa2 = aa2.upper()

        # Check backbone H-bonds (always possible)
        backbone = "backbone H-bond (N-H...O=C)"

        # Check if aa1 can donate to aa2
        if aa1 in self.donors and aa2 in self.acceptors:
            return True, f"{aa1} donor → {aa2} acceptor (sidechain)"

        # Check if aa2 can donate to aa1
        if aa2 in self.donors and aa1 in self.acceptors:
            return True, f"{aa2} donor → {aa1} acceptor (sidechain)"

        # Backbone H-bonds always possible
        return True, backbone

    def predict_hbonds(self, coords: np.ndarray, sequence: str) -> List[HydrogenBond]:
        """
        Predict hydrogen bonds given CA coordinates.

        Args:
            coords: Nx3 numpy array of CA coordinates
            sequence: Amino acid sequence (one-letter codes)

        Returns:
            List of HydrogenBond objects
        """
        hbonds = []
        N = len(sequence)

        if len(coords) != N:
            raise ValueError(f"Coordinates ({len(coords)}) and sequence ({N}) length mismatch")

        # 1. α-helix H-bonds: i → i+4
        for i in range(N - 4):
            distance = np.linalg.norm(coords[i] - coords[i+4])
            min_d, max_d = self.distance_constraints['helix_backbone']

            if min_d < distance < max_d:
                confidence = self._compute_confidence(
                    distance,
                    self.ideal_distances['helix_backbone'],
                    tolerance=0.5
                )

                hbonds.append(HydrogenBond(
                    donor=i,
                    acceptor=i+4,
                    bond_type=HBondType.HELIX_BACKBONE,
                    distance=distance,
                    confidence=confidence,
                    donor_aa=sequence[i],
                    acceptor_aa=sequence[i+4]
                ))

        # 2. β-sheet H-bonds: inter-strand (look for non-local contacts)
        for i in range(N):
            for j in range(i+5, N):  # Skip local contacts
                distance = np.linalg.norm(coords[i] - coords[j])

                # Check for sheet-like geometry
                if 4.5 < distance < 6.5:
                    # Determine if parallel or antiparallel (simplified heuristic)
                    # Antiparallel more common for CA-CA distance ~5.3Å
                    if abs(distance - 5.3) < 0.5:
                        bond_type = HBondType.SHEET_BACKBONE
                        ideal_dist = self.ideal_distances['sheet_antiparallel']
                        confidence = self._compute_confidence(distance, ideal_dist, tolerance=0.5)
                    else:
                        # Could be parallel sheet or other
                        bond_type = HBondType.SHEET_BACKBONE
                        ideal_dist = 5.3
                        confidence = self._compute_confidence(distance, ideal_dist, tolerance=0.8) * 0.7

                    hbonds.append(HydrogenBond(
                        donor=i,
                        acceptor=j,
                        bond_type=bond_type,
                        distance=distance,
                        confidence=confidence,
                        donor_aa=sequence[i],
                        acceptor_aa=sequence[j]
                    ))

        # 3. Side chain H-bonds
        for i in range(N):
            for j in range(i+1, N):
                if abs(i - j) < 3:  # Skip very local contacts
                    continue

                aa_i = sequence[i]
                aa_j = sequence[j]

                # Check if compatible donor-acceptor pair
                can_bond, _ = self.can_form_hbond(aa_i, aa_j)

                if can_bond and (aa_i in self.donors or aa_i in self.acceptors):
                    distance = np.linalg.norm(coords[i] - coords[j])
                    min_d, max_d = self.distance_constraints['sidechain']

                    if min_d < distance < max_d:
                        # Lower confidence for sidechain (we don't have full atoms)
                        confidence = self._compute_confidence(
                            distance,
                            self.ideal_distances.get('sidechain', 5.5),
                            tolerance=1.0
                        ) * 0.6  # Penalty for not having exact atom positions

                        hbonds.append(HydrogenBond(
                            donor=i if aa_i in self.donors else j,
                            acceptor=j if aa_i in self.donors else i,
                            bond_type=HBondType.SIDECHAIN,
                            distance=distance,
                            confidence=confidence,
                            donor_aa=aa_i if aa_i in self.donors else aa_j,
                            acceptor_aa=aa_j if aa_i in self.donors else aa_i
                        ))

        return hbonds

    def _compute_confidence(self, distance: float, ideal: float, tolerance: float = 0.5) -> float:
        """
        Compute confidence score based on distance from ideal geometry.

        Args:
            distance: Observed distance (Å)
            ideal: Ideal distance (Å)
            tolerance: Tolerance window (Å)

        Returns:
            Confidence score 0-1
        """
        deviation = abs(distance - ideal)

        if deviation < tolerance:
            # High confidence: within tolerance
            return 1.0 - (deviation / tolerance) * 0.3  # 0.7 - 1.0
        else:
            # Lower confidence: outside tolerance
            extra_dev = deviation - tolerance
            return max(0.0, 0.7 - extra_dev * 0.2)  # Decay with distance

    def validate_hbond_network(self, hbonds: List[HydrogenBond], sequence: str) -> Tuple[bool, List[Dict]]:
        """
        Validate H-bond network makes physical sense.

        Checks:
        - H-bonds per residue (should be 0-5)
        - Overall H-bond density (should be ~0.5-1.0 per residue)
        - No excessive bonding

        Args:
            hbonds: List of predicted H-bonds
            sequence: Amino acid sequence

        Returns:
            (is_valid, list of issues)
        """
        issues = []
        N = len(sequence)

        # Count H-bonds per residue
        hbond_counts = {i: 0 for i in range(N)}
        for hb in hbonds:
            hbond_counts[hb.donor] += 1
            hbond_counts[hb.acceptor] += 1

        # Check for excessive H-bonding
        for idx, count in hbond_counts.items():
            if count > 5:
                issues.append({
                    'severity': 'WARNING',
                    'residue': idx,
                    'aa': sequence[idx],
                    'count': count,
                    'message': f'Residue {idx} ({sequence[idx]}) has {count} H-bonds (expected 0-5)'
                })

        # Check overall H-bond density
        total_hbonds = len(hbonds)
        expected_hbonds = N * 0.5  # ~1 H-bond per 2 residues (rough average)

        if total_hbonds < expected_hbonds * 0.3:
            issues.append({
                'severity': 'CRITICAL',
                'message': f'Too few H-bonds: {total_hbonds} vs {expected_hbonds:.0f} expected (30% threshold)'
            })
        elif total_hbonds > expected_hbonds * 3.0:
            issues.append({
                'severity': 'WARNING',
                'message': f'Unusually many H-bonds: {total_hbonds} vs {expected_hbonds:.0f} expected'
            })

        # Check confidence distribution
        confidences = [hb.confidence for hb in hbonds]
        if confidences:
            mean_conf = np.mean(confidences)
            if mean_conf < 0.3:
                issues.append({
                    'severity': 'WARNING',
                    'message': f'Low mean H-bond confidence: {mean_conf:.2f} (suggests poor geometry)'
                })

        # Determine if valid (no CRITICAL issues)
        is_valid = len([i for i in issues if i['severity'] == 'CRITICAL']) == 0

        return is_valid, issues


# Integration with Category Theory
class HBondMorphism:
    """
    Hydrogen bond as categorical morphism.

    This class bridges physical chemistry with category theory by representing
    H-bonds as morphisms in the categorical store. The strength of the H-bond
    (based on geometry) becomes the morphism confidence.
    """

    def __init__(self, hbond: HydrogenBond, sequence: str):
        """
        Create morphism from H-bond.

        Args:
            hbond: HydrogenBond object
            sequence: Full protein sequence
        """
        self.hbond = hbond
        self.sequence = sequence

    def to_stored_morphism(self) -> 'StoredMorphism':
        """Convert to StoredMorphism for categorical store."""
        if not STORE_AVAILABLE or StoredMorphism is None:
            raise ImportError("StoredMorphism not available - cannot create categorical morphism")

        donor_name = f"R{self.hbond.donor}_{self.hbond.donor_aa}"
        acceptor_name = f"R{self.hbond.acceptor}_{self.hbond.acceptor_aa}"

        return StoredMorphism(
            name="hydrogen_bond",
            source_name=donor_name,
            target_name=acceptor_name,
            metadata={
                'type': self.hbond.bond_type.value,
                'distance': float(self.hbond.distance),
                'donor_residue': self.hbond.donor,
                'acceptor_residue': self.hbond.acceptor,
                'donor_aa': self.hbond.donor_aa,
                'acceptor_aa': self.hbond.acceptor_aa,
            },
            confidence=float(self.hbond.confidence),
            provenance="physical_chemistry_hbond_prediction"
        )


# Convenience functions
def predict_hbonds_from_coords(coords: np.ndarray, sequence: str) -> List[HydrogenBond]:
    """Convenience function to predict H-bonds from coordinates."""
    validator = HydrogenBondValidator()
    return validator.predict_hbonds(coords, sequence)


def validate_hbond_network(hbonds: List[HydrogenBond], sequence: str) -> Tuple[bool, List[Dict]]:
    """Convenience function to validate H-bond network."""
    validator = HydrogenBondValidator()
    return validator.validate_hbond_network(hbonds, sequence)


# Testing and demonstration
if __name__ == "__main__":
    print("=" * 70)
    print("Hydrogen Bond Validator - Test")
    print("=" * 70)
    print()

    # Create a simple test structure (3-turn helix)
    # Approximate helix geometry: rise = 1.5Å per residue, radius = 2.3Å
    sequence = "AAAAAAAAAAAA"  # 12 alanines
    N = len(sequence)

    # Generate helical coordinates
    coords = np.zeros((N, 3))
    for i in range(N):
        angle = i * 100 * np.pi / 180  # 100° rotation per residue
        coords[i] = [
            2.3 * np.cos(angle),
            2.3 * np.sin(angle),
            i * 1.5  # Rise along z-axis
        ]

    # Predict H-bonds
    validator = HydrogenBondValidator()
    hbonds = validator.predict_hbonds(coords, sequence)

    print(f"Sequence: {sequence}")
    print(f"Length: {N} residues")
    print(f"Predicted H-bonds: {len(hbonds)}")
    print()

    # Show H-bonds
    for hb in hbonds:
        print(f"  {hb.donor:2d} → {hb.acceptor:2d}  "
              f"({hb.bond_type.value:20s})  "
              f"d={hb.distance:.2f}Å  "
              f"conf={hb.confidence:.2f}")
    print()

    # Validate network
    is_valid, issues = validator.validate_hbond_network(hbonds, sequence)

    print(f"Validation: {'PASS' if is_valid else 'FAIL'}")
    if issues:
        print("Issues found:")
        for issue in issues:
            print(f"  [{issue['severity']}] {issue['message']}")
    else:
        print("  No issues found - H-bond network is physically reasonable")
