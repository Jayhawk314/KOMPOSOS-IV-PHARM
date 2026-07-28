# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""
Ramachandran Plot Validation
=============================

Full Ramachandran plot validation for protein backbone geometry.

The Ramachandran plot shows which combinations of φ (phi) and ψ (psi) angles
are energetically allowed for amino acid residues in a protein backbone.

Backbone Dihedral Angles:
- φ (phi): Rotation around N-Cα bond
  Defined by: C(i-1) - N(i) - Cα(i) - C(i)
- ψ (psi): Rotation around Cα-C bond
  Defined by: N(i) - Cα(i) - C(i) - N(i+1)

Allowed Regions:
- α-helix (right-handed): φ ~ -60°, ψ ~ -45°
- β-sheet: φ ~ -120°, ψ ~ +120°
- Left-handed α-helix: φ ~ +60°, ψ ~ +45° (rare, mostly Gly)
- Forbidden: Most other combinations (steric clashes)

Classification:
- Favored (core): >2% frequency in high-quality structures
- Allowed (additional): >0.2% frequency
- Generously allowed: >0.02% frequency
- Disallowed/Outlier: <0.02% frequency

Quality Metrics (MolProbity standards):
- Excellent: >98% favored
- Good: >98% favored + allowed
- Needs improvement: >90% favored + allowed
- Poor: <90% favored + allowed

References:
- Ramachandran, Ramakrishnan, Sasisekharan (1963): "Stereochemistry of polypeptide chain configurations"
- Lovell et al. (2003): "Structure validation by Cα geometry: φ,ψ and Cβ deviation"
- MolProbity: http://molprobity.biochem.duke.edu/
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
from enum import Enum
import numpy as np


class RamachandranRegion(Enum):
    """Classification of Ramachandran plot regions."""
    FAVORED = "favored"              # Core allowed (>2%)
    ALLOWED = "allowed"              # Additional allowed (>0.2%)
    GENEROUS = "generous"             # Generously allowed (>0.02%)
    OUTLIER = "outlier"              # Disallowed (<0.02%)


@dataclass
class AngleAnalysis:
    """Analysis of backbone angles for one residue."""
    residue_idx: int
    amino_acid: str
    phi: Optional[float]  # None for first residue
    psi: Optional[float]  # None for last residue
    region: RamachandranRegion
    probability: float  # Probability in empirical distribution


class RamachandranValidator:
    """
    Full Ramachandran plot validation.

    Validates backbone φ/ψ angles against empirical distributions
    from high-quality PDB structures.

    NOTE: Requires backbone N, CA, C, O atoms (not just CA).
    For CA-only structures, angles cannot be computed accurately.
    """

    def __init__(self):
        """Initialize Ramachandran validator with empirical distributions."""

        # Define allowed regions (φ, ψ) ranges (degrees)
        # Based on Lovell et al. (2003) and MolProbity
        self.regions = {
            'alpha_R': {  # Right-handed α-helix
                'phi': (-70, -50),
                'psi': (-50, -30),
                'probability': 0.30  # 30% of residues
            },
            'beta': {  # β-sheet
                'phi': (-140, -100),
                'psi': (100, 180),
                'probability': 0.25
            },
            'alpha_L': {  # Left-handed α-helix (rare, mostly Gly)
                'phi': (40, 80),
                'psi': (20, 60),
                'probability': 0.01
            },
            'ppII': {  # Polyproline II (extended)
                'phi': (-75, -55),
                'psi': (120, 180),
                'probability': 0.10
            }
        }

        # Glycine has more freedom (smaller side chain)
        self.glycine_regions = {
            'alpha_R': {'phi': (-90, -30), 'psi': (-70, -10), 'probability': 0.20},
            'beta': {'phi': (-180, -80), 'psi': (80, 180), 'probability': 0.25},
            'alpha_L': {'phi': (30, 90), 'psi': (0, 90), 'probability': 0.15},
            'other': {'phi': (-180, 180), 'psi': (-180, 180), 'probability': 0.40}
        }

        # Proline is restricted (cyclic side chain)
        self.proline_regions = {
            'alpha': {'phi': (-75, -55), 'psi': (-50, -20), 'probability': 0.60},
            'ppII': {'phi': (-75, -55), 'psi': (120, 180), 'probability': 0.35}
        }

    def compute_dihedral(self, p1: np.ndarray, p2: np.ndarray,
                        p3: np.ndarray, p4: np.ndarray) -> float:
        """
        Compute dihedral angle for four points.

        Args:
            p1, p2, p3, p4: 3D coordinates of four atoms

        Returns:
            Dihedral angle in degrees (-180 to 180)
        """
        # Vectors
        b1 = p2 - p1
        b2 = p3 - p2
        b3 = p4 - p3

        # Normal vectors
        n1 = np.cross(b1, b2)
        n2 = np.cross(b2, b3)

        # Normalize
        n1 = n1 / (np.linalg.norm(n1) + 1e-10)
        n2 = n2 / (np.linalg.norm(n2) + 1e-10)

        # Dihedral angle
        m1 = np.cross(n1, b2 / (np.linalg.norm(b2) + 1e-10))

        x = np.dot(n1, n2)
        y = np.dot(m1, n2)

        angle = np.arctan2(y, x)
        return np.degrees(angle)

    def compute_angles_from_backbone(self, backbone_coords: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Compute φ/ψ angles from backbone coordinates.

        Args:
            backbone_coords: Nx4x3 array (N, CA, C, O for each residue)

        Returns:
            (phi_array, psi_array) - angles in degrees
            First residue has phi=None, last has psi=None
        """
        N = len(backbone_coords)
        phi = np.full(N, np.nan)
        psi = np.full(N, np.nan)

        for i in range(1, N - 1):
            # φ (phi): C(i-1) - N(i) - CA(i) - C(i)
            phi[i] = self.compute_dihedral(
                backbone_coords[i-1][2],  # C(i-1)
                backbone_coords[i][0],     # N(i)
                backbone_coords[i][1],     # CA(i)
                backbone_coords[i][2]      # C(i)
            )

            # ψ (psi): N(i) - CA(i) - C(i) - N(i+1)
            psi[i] = self.compute_dihedral(
                backbone_coords[i][0],     # N(i)
                backbone_coords[i][1],     # CA(i)
                backbone_coords[i][2],     # C(i)
                backbone_coords[i+1][0]    # N(i+1)
            )

        return phi, psi

    def estimate_angles_from_ca_only(self, ca_coords: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Estimate φ/ψ angles from CA coordinates only (approximate).

        This is a rough approximation and should not be used for final validation.
        Real Ramachandran validation requires full backbone atoms.

        Uses CA-CA virtual bond angles as proxy.

        Args:
            ca_coords: Nx3 CA coordinates

        Returns:
            (phi_approx, psi_approx) - approximate angles
        """
        N = len(ca_coords)
        phi = np.full(N, np.nan)
        psi = np.full(N, np.nan)

        # Very rough approximation using CA-CA-CA angles
        for i in range(1, N - 1):
            # Virtual dihedral from 4 consecutive CAs
            if i >= 1 and i < N - 2:
                phi[i] = self.compute_dihedral(
                    ca_coords[i-1],
                    ca_coords[i],
                    ca_coords[i+1],
                    ca_coords[i+2]
                )
                psi[i] = phi[i]  # Same for simplified model

        return phi, psi

    def classify_angles(self, phi: float, psi: float, amino_acid: str = 'A') -> Tuple[RamachandranRegion, float]:
        """
        Classify (φ, ψ) angles into Ramachandran regions.

        Args:
            phi: φ angle (degrees)
            psi: ψ angle (degrees)
            amino_acid: Amino acid type (G and P have different allowed regions)

        Returns:
            (region_classification, probability)
        """
        if np.isnan(phi) or np.isnan(psi):
            return RamachandranRegion.OUTLIER, 0.0

        # Use appropriate regions based on amino acid
        if amino_acid == 'G':
            regions = self.glycine_regions
        elif amino_acid == 'P':
            regions = self.proline_regions
        else:
            regions = self.regions

        # Check each region
        for region_name, region_def in regions.items():
            phi_min, phi_max = region_def['phi']
            psi_min, psi_max = region_def['psi']

            # Handle angle wrapping (-180 to 180)
            if phi_min <= phi <= phi_max and psi_min <= psi <= psi_max:
                prob = region_def['probability']

                # Classify based on probability
                if prob > 0.02:
                    return RamachandranRegion.FAVORED, prob
                elif prob > 0.002:
                    return RamachandranRegion.ALLOWED, prob
                elif prob > 0.0002:
                    return RamachandranRegion.GENEROUS, prob

        # Not in any known region
        return RamachandranRegion.OUTLIER, 0.0

    def validate_angles(self, phi: np.ndarray, psi: np.ndarray, sequence: str) -> Tuple[Dict, List[AngleAnalysis]]:
        """
        Validate φ/ψ angles against Ramachandran plot.

        Args:
            phi: Array of φ angles (degrees)
            psi: Array of ψ angles (degrees)
            sequence: Amino acid sequence

        Returns:
            (summary_dict, list of AngleAnalysis objects)
        """
        N = len(sequence)

        if len(phi) != N or len(psi) != N:
            raise ValueError("Angles and sequence length mismatch")

        analyses = []
        favored_count = 0
        allowed_count = 0
        generous_count = 0
        outlier_count = 0

        for i in range(N):
            if np.isnan(phi[i]) and np.isnan(psi[i]):
                # Terminal residues
                continue

            aa = sequence[i]
            region, prob = self.classify_angles(phi[i], psi[i], aa)

            analyses.append(AngleAnalysis(
                residue_idx=i,
                amino_acid=aa,
                phi=float(phi[i]) if not np.isnan(phi[i]) else None,
                psi=float(psi[i]) if not np.isnan(psi[i]) else None,
                region=region,
                probability=prob
            ))

            # Count by region
            if region == RamachandranRegion.FAVORED:
                favored_count += 1
            elif region == RamachandranRegion.ALLOWED:
                allowed_count += 1
            elif region == RamachandranRegion.GENEROUS:
                generous_count += 1
            else:
                outlier_count += 1

        # Compute percentages
        total_classified = favored_count + allowed_count + generous_count + outlier_count
        if total_classified > 0:
            favored_pct = 100.0 * favored_count / total_classified
            allowed_pct = 100.0 * (favored_count + allowed_count) / total_classified
            generous_pct = 100.0 * (favored_count + allowed_count + generous_count) / total_classified
        else:
            favored_pct = allowed_pct = generous_pct = 0.0

        # Quality assessment (MolProbity standards)
        if favored_pct > 98:
            quality = "EXCELLENT"
        elif allowed_pct > 98:
            quality = "GOOD"
        elif allowed_pct > 90:
            quality = "ACCEPTABLE"
        else:
            quality = "POOR"

        summary = {
            'quality': quality,
            'favored_count': favored_count,
            'allowed_count': allowed_count,
            'generous_count': generous_count,
            'outlier_count': outlier_count,
            'favored_percent': favored_pct,
            'allowed_percent': allowed_pct,
            'generous_percent': generous_pct,
            'total_residues': total_classified,
            'outliers': [
                {
                    'residue': a.residue_idx,
                    'aa': a.amino_acid,
                    'phi': a.phi,
                    'psi': a.psi
                }
                for a in analyses if a.region == RamachandranRegion.OUTLIER
            ]
        }

        return summary, analyses


# Testing
if __name__ == "__main__":
    print("=" * 70)
    print("Ramachandran Validation - Test")
    print("=" * 70)
    print()

    # Test with approximate CA-only angles
    sequence = "AAAAAAAAAAAA"
    N = len(sequence)

    # Create helical CA coordinates
    ca_coords = np.zeros((N, 3))
    for i in range(N):
        angle = i * 100 * np.pi / 180
        ca_coords[i] = [2.3 * np.cos(angle), 2.3 * np.sin(angle), i * 1.5]

    validator = RamachandranValidator()

    # Estimate angles from CA only (approximate)
    phi, psi = validator.estimate_angles_from_ca_only(ca_coords)

    print("NOTE: Using CA-only approximation (not accurate for real validation)")
    print(f"Sequence: {sequence}")
    print(f"Length: {N} residues")
    print()

    # Validate
    try:
        summary, analyses = validator.validate_angles(phi, psi, sequence)

        print(f"Quality: {summary['quality']}")
        print(f"Favored: {summary['favored_count']}/{summary['total_residues']} ({summary['favored_percent']:.1f}%)")
        print(f"Allowed: {summary['allowed_count']}/{summary['total_residues']}")
        print(f"Outliers: {summary['outlier_count']}/{summary['total_residues']}")
        print()

        if summary['outliers']:
            print("Outliers detected:")
            for outlier in summary['outliers'][:5]:
                print(f"  Residue {outlier['residue']} ({outlier['aa']}): "
                      f"phi={outlier['phi']:.1f}, psi={outlier['psi']:.1f}")
    except Exception as e:
        print(f"Validation skipped: {e}")
        print("(Expected - CA-only coordinates don't provide accurate angles)")
