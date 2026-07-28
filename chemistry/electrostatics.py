# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""
Electrostatic Interactions Module
===================================

Electrostatic interactions: salt bridges and disulfide bonds.

Physical Constraints:
- Salt bridges: 2.5-4.5 Å between opposite charges (sidechain-sidechain)
- Salt bridge CA-CA distance: ~3.0-6.0 Å
- Disulfide bonds: 1.8-2.5 Å between cysteine sulfurs (S-S)
- Disulfide CA-CA distance: ~3.5-6.5 Å
- Charge-charge repulsion: Same charges should be > 5 Å apart

Charged Residues:
- Positive: Lysine (K), Arginine (R), Histidine (H, pKa ~6)
- Negative: Aspartate (D), Glutamate (E)
- Cysteines (C): Can form disulfide bonds

Salt bridges stabilize protein structures, especially:
- Surface charge networks
- Domain interfaces
- Active sites

Disulfide bonds:
- Covalent cross-links (very strong)
- Stabilize extracellular proteins
- Rare in cytoplasm (reducing environment)

References:
- Protein chemistry textbooks
- PDB structural analysis
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
from enum import Enum
import numpy as np


class InteractionType(Enum):
    """Types of electrostatic interactions."""
    SALT_BRIDGE = "salt_bridge"
    DISULFIDE_BOND = "disulfide_bond"
    CHARGE_REPULSION = "charge_repulsion"


@dataclass
class ElectrostaticInteraction:
    """Represents an electrostatic interaction."""
    residue_i: int
    residue_j: int
    interaction_type: InteractionType
    distance: float  # CA-CA distance
    energy: float    # Simplified electrostatic energy
    strength: float  # 0-1 strength score
    aa_i: str
    aa_j: str


class ElectrostaticConstraints:
    """
    Electrostatic interactions: salt bridges, disulfide bonds.

    Physical constraints on charged residue interactions and
    covalent cross-links.
    """

    def __init__(self):
        """Initialize electrostatic constraints."""

        # Charged residues
        self.charged_positive = {'K', 'R', 'H'}  # Lysine, Arginine, Histidine
        self.charged_negative = {'D', 'E'}       # Aspartate, Glutamate
        self.cysteine = 'C'

        # Distance constraints (CA-CA distances as proxy)
        self.salt_bridge_range = (3.0, 6.0)      # CA-CA for salt bridge
        self.disulfide_range = (3.5, 6.5)        # CA-CA for disulfide
        self.repulsion_min = 5.0                  # Minimum for same charges

        # Optimal distances
        self.salt_bridge_optimal = 4.5
        self.disulfide_optimal = 5.5

    def predict_salt_bridges(self, coords: np.ndarray, sequence: str) -> List[ElectrostaticInteraction]:
        """
        Predict salt bridges between opposite charges.

        Args:
            coords: Nx3 CA coordinates
            sequence: Amino acid sequence

        Returns:
            List of ElectrostaticInteraction objects (salt bridges)
        """
        salt_bridges = []
        N = len(sequence)

        # Find positively and negatively charged residues
        positive_indices = [i for i, aa in enumerate(sequence) if aa in self.charged_positive]
        negative_indices = [i for i, aa in enumerate(sequence) if aa in self.charged_negative]

        for i in positive_indices:
            for j in negative_indices:
                if abs(i - j) <= 2:  # Skip adjacent residues
                    continue

                distance = np.linalg.norm(coords[i] - coords[j])

                min_d, max_d = self.salt_bridge_range
                if min_d < distance < max_d:
                    # Simplified Coulomb energy: E = -k/r (attractive)
                    # Normalized to ~0-1 range
                    energy = -1.0 / distance

                    # Strength based on distance from optimal
                    strength = self._compute_strength(
                        distance,
                        self.salt_bridge_optimal,
                        tolerance=1.0
                    )

                    salt_bridges.append(ElectrostaticInteraction(
                        residue_i=i,
                        residue_j=j,
                        interaction_type=InteractionType.SALT_BRIDGE,
                        distance=distance,
                        energy=energy,
                        strength=strength,
                        aa_i=sequence[i],
                        aa_j=sequence[j]
                    ))

        return salt_bridges

    def predict_disulfide_bonds(self, coords: np.ndarray, sequence: str) -> List[ElectrostaticInteraction]:
        """
        Predict disulfide bonds between cysteines.

        Args:
            coords: Nx3 CA coordinates
            sequence: Amino acid sequence

        Returns:
            List of ElectrostaticInteraction objects (disulfide bonds)
        """
        disulfides = []
        N = len(sequence)

        # Find all cysteines
        cys_indices = [i for i, aa in enumerate(sequence) if aa == self.cysteine]

        if len(cys_indices) < 2:
            return disulfides  # Need at least 2 cysteines

        for i in range(len(cys_indices)):
            for j in range(i+1, len(cys_indices)):
                idx_i, idx_j = cys_indices[i], cys_indices[j]

                if abs(idx_i - idx_j) <= 2:  # Skip adjacent
                    continue

                distance = np.linalg.norm(coords[idx_i] - coords[idx_j])

                min_d, max_d = self.disulfide_range
                if min_d < distance < max_d:
                    # Disulfide bond energy (very strong, covalent)
                    energy = -5.0  # Arbitrary strong value

                    # Confidence based on distance
                    confidence = self._disulfide_confidence(distance)

                    disulfides.append(ElectrostaticInteraction(
                        residue_i=idx_i,
                        residue_j=idx_j,
                        interaction_type=InteractionType.DISULFIDE_BOND,
                        distance=distance,
                        energy=energy,
                        strength=confidence,
                        aa_i=sequence[idx_i],
                        aa_j=sequence[idx_j]
                    ))

        return disulfides

    def check_charge_repulsion(self, coords: np.ndarray, sequence: str) -> List[ElectrostaticInteraction]:
        """
        Check for unfavorable charge-charge repulsion (same charges too close).

        Args:
            coords: Nx3 CA coordinates
            sequence: Amino acid sequence

        Returns:
            List of unfavorable interactions (repulsions)
        """
        repulsions = []
        N = len(sequence)

        # Check positive-positive repulsion
        positive_indices = [i for i, aa in enumerate(sequence) if aa in self.charged_positive]
        for i in range(len(positive_indices)):
            for j in range(i+1, len(positive_indices)):
                idx_i, idx_j = positive_indices[i], positive_indices[j]

                if abs(idx_i - idx_j) <= 2:
                    continue

                distance = np.linalg.norm(coords[idx_i] - coords[idx_j])

                if distance < self.repulsion_min:
                    # Repulsive energy: E = +k/r
                    energy = +1.0 / distance
                    strength = 1.0 - (distance / self.repulsion_min)

                    repulsions.append(ElectrostaticInteraction(
                        residue_i=idx_i,
                        residue_j=idx_j,
                        interaction_type=InteractionType.CHARGE_REPULSION,
                        distance=distance,
                        energy=energy,
                        strength=strength,
                        aa_i=sequence[idx_i],
                        aa_j=sequence[idx_j]
                    ))

        # Check negative-negative repulsion
        negative_indices = [i for i, aa in enumerate(sequence) if aa in self.charged_negative]
        for i in range(len(negative_indices)):
            for j in range(i+1, len(negative_indices)):
                idx_i, idx_j = negative_indices[i], negative_indices[j]

                if abs(idx_i - idx_j) <= 2:
                    continue

                distance = np.linalg.norm(coords[idx_i] - coords[idx_j])

                if distance < self.repulsion_min:
                    energy = +1.0 / distance
                    strength = 1.0 - (distance / self.repulsion_min)

                    repulsions.append(ElectrostaticInteraction(
                        residue_i=idx_i,
                        residue_j=idx_j,
                        interaction_type=InteractionType.CHARGE_REPULSION,
                        distance=distance,
                        energy=energy,
                        strength=strength,
                        aa_i=sequence[idx_i],
                        aa_j=sequence[idx_j]
                    ))

        return repulsions

    def analyze_electrostatics(self, coords: np.ndarray, sequence: str) -> Dict:
        """
        Comprehensive electrostatic analysis.

        Args:
            coords: Nx3 CA coordinates
            sequence: Amino acid sequence

        Returns:
            Dictionary with electrostatic analysis
        """
        # Predict all interactions
        salt_bridges = self.predict_salt_bridges(coords, sequence)
        disulfides = self.predict_disulfide_bonds(coords, sequence)
        repulsions = self.check_charge_repulsion(coords, sequence)

        # Compute total energy
        total_energy = (
            sum(sb.energy for sb in salt_bridges) +
            sum(ds.energy for ds in disulfides) +
            sum(rep.energy for rep in repulsions)
        )

        # Count charged residues
        num_positive = sum(1 for aa in sequence if aa in self.charged_positive)
        num_negative = sum(1 for aa in sequence if aa in self.charged_negative)
        num_cysteines = sum(1 for aa in sequence if aa == self.cysteine)

        # Assessment
        has_repulsions = len(repulsions) > 0
        has_salt_bridges = len(salt_bridges) > 0
        has_disulfides = len(disulfides) > 0

        if has_repulsions and not has_salt_bridges:
            quality = "POOR - Unfavorable charge repulsion"
        elif has_salt_bridges and not has_repulsions:
            quality = "EXCELLENT - Favorable salt bridge network"
        elif has_disulfides:
            quality = "GOOD - Disulfide cross-links present"
        else:
            quality = "NEUTRAL - Minimal electrostatic interactions"

        return {
            'quality': quality,
            'total_energy': float(total_energy),
            'num_salt_bridges': len(salt_bridges),
            'num_disulfides': len(disulfides),
            'num_repulsions': len(repulsions),
            'num_positive_residues': num_positive,
            'num_negative_residues': num_negative,
            'num_cysteines': num_cysteines,
            'salt_bridges': [
                {
                    'residue_i': sb.residue_i,
                    'residue_j': sb.residue_j,
                    'aa_i': sb.aa_i,
                    'aa_j': sb.aa_j,
                    'distance': float(sb.distance),
                    'energy': float(sb.energy),
                    'strength': float(sb.strength)
                }
                for sb in salt_bridges
            ],
            'disulfides': [
                {
                    'residue_i': ds.residue_i,
                    'residue_j': ds.residue_j,
                    'distance': float(ds.distance),
                    'strength': float(ds.strength)
                }
                for ds in disulfides
            ],
            'repulsions': [
                {
                    'residue_i': rep.residue_i,
                    'residue_j': rep.residue_j,
                    'aa_i': rep.aa_i,
                    'aa_j': rep.aa_j,
                    'distance': float(rep.distance),
                    'strength': float(rep.strength)
                }
                for rep in repulsions
            ]
        }

    def _compute_strength(self, distance: float, optimal: float, tolerance: float = 1.0) -> float:
        """Compute interaction strength based on distance."""
        deviation = abs(distance - optimal)
        if deviation < tolerance:
            return 1.0 - (deviation / tolerance) * 0.3
        else:
            return max(0.0, 0.7 - (deviation - tolerance) * 0.2)

    def _disulfide_confidence(self, distance: float) -> float:
        """Confidence of disulfide bond based on CA-CA distance."""
        # Optimal CA-CA distance for disulfide: ~5.5 Å
        if 5.0 <= distance <= 6.0:
            return 0.9
        elif 4.5 <= distance < 5.0 or 6.0 < distance <= 6.5:
            return 0.7
        elif 3.8 <= distance < 4.5:
            return 0.5
        else:
            return 0.3


# Convenience functions
def predict_salt_bridges(coords: np.ndarray, sequence: str) -> List[ElectrostaticInteraction]:
    """Convenience function to predict salt bridges."""
    elec = ElectrostaticConstraints()
    return elec.predict_salt_bridges(coords, sequence)


def predict_disulfide_bonds(coords: np.ndarray, sequence: str) -> List[ElectrostaticInteraction]:
    """Convenience function to predict disulfide bonds."""
    elec = ElectrostaticConstraints()
    return elec.predict_disulfide_bonds(coords, sequence)


# Testing
if __name__ == "__main__":
    print("=" * 70)
    print("Electrostatic Constraints - Test")
    print("=" * 70)
    print()

    # Test structure with charged residues
    sequence = "KDEKREKDRKEK"  # Mix of K (pos), D (neg), E (neg), R (pos)
    N = len(sequence)

    # Create helical coordinates
    coords = np.zeros((N, 3))
    for i in range(N):
        angle = i * 100 * np.pi / 180
        coords[i] = [2.3 * np.cos(angle), 2.3 * np.sin(angle), i * 1.5]

    elec = ElectrostaticConstraints()
    analysis = elec.analyze_electrostatics(coords, sequence)

    print(f"Sequence: {sequence}")
    print(f"Quality: {analysis['quality']}")
    print(f"Total energy: {analysis['total_energy']:.2f}")
    print(f"Salt bridges: {analysis['num_salt_bridges']}")
    print(f"Disulfides: {analysis['num_disulfides']}")
    print(f"Repulsions: {analysis['num_repulsions']}")
    print()

    if analysis['salt_bridges']:
        print("Salt bridges:")
        for sb in analysis['salt_bridges'][:5]:
            print(f"  {sb['aa_i']}{sb['residue_i']} ↔ {sb['aa_j']}{sb['residue_j']}: "
                  f"{sb['distance']:.2f} Å, strength={sb['strength']:.2f}")
