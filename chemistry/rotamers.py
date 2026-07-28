# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""
Rotamer Library Module
======================

Backbone-dependent rotamer library for side chain conformations.

The Dunbrack rotamer library provides discrete side chain conformations
(rotamers) and their probabilities as a function of backbone dihedral
angles φ (phi) and ψ (psi).

Side Chain Torsion Angles (χ):
- χ1: N-CA-CB-CG (all amino acids with side chain)
- χ2: CA-CB-CG-CD/OD/ND (longer side chains)
- χ3: CB-CG-CD-CE/NE/OE (even longer)
- χ4: CG-CD-CE-NZ (Lys, Arg only)

Rotamer Representation:
- Each rotamer: (χ1, χ2, χ3, χ4) angles
- Probability: P(rotamer | φ, ψ)
- Common rotamers: t (trans ~180°), g+ (gauche+ ~60°), g- (gauche- ~-60°)

Dunbrack Library:
- 2010 version (smoothed with kernel density estimates)
- Backbone-dependent: P(χ | φ, ψ)
- Derived from high-quality PDB structures
- Available at: http://dunbrack.fccc.edu/bbdep2010/

Applications:
- Homology modeling
- Structure prediction
- Side chain refinement
- Protein design

References:
- Dunbrack & Karplus (1993): Backbone-dependent rotamer library
- Dunbrack & Cohen (1997): Bayesian statistical analysis
- Shapovalov & Dunbrack (2011): Smoothed backbone-dependent library
- http://dunbrack.fccc.edu/

Website: https://dunbrack.fccc.edu/bbdep2010/
"""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional
from pathlib import Path
import numpy as np
import json


@dataclass
class Rotamer:
    """
    Represents a single rotamer conformation.

    Attributes:
        chi_angles: List of χ angles in degrees [χ1, χ2, χ3, χ4]
        probability: Probability of this rotamer given backbone angles
        name: Rotamer name (e.g., 'ttg-', 'g+g-')
    """
    chi_angles: List[float]  # χ1, χ2, χ3, χ4 (NaN for missing)
    probability: float
    name: str = ""

    def __post_init__(self):
        """Generate rotamer name from χ angles."""
        if not self.name:
            self.name = self._generate_name()

    def _generate_name(self) -> str:
        """Generate rotamer name from χ angles (e.g., 'tg+g-')."""
        name_parts = []
        for chi in self.chi_angles:
            if np.isnan(chi):
                break
            if chi > 120 or chi < -120:
                name_parts.append('t')   # trans
            elif 0 <= chi <= 120:
                name_parts.append('g+')  # gauche+
            else:
                name_parts.append('g-')  # gauche-
        return ''.join(name_parts) if name_parts else 'none'


@dataclass
class BackboneBin:
    """
    Backbone angle bin for rotamer library.

    Attributes:
        phi_center: Center of φ bin (degrees)
        psi_center: Center of ψ bin (degrees)
        rotamers: List of rotamers for this backbone bin
    """
    phi_center: float
    psi_center: float
    rotamers: List[Rotamer] = field(default_factory=list)


class DunbrackRotamerLibrary:
    """
    Backbone-dependent rotamer library (Dunbrack 2010).

    Provides rotamer probabilities P(χ | φ, ψ) for each amino acid type.
    """

    def __init__(self, library_path: Optional[Path] = None):
        """
        Initialize rotamer library.

        Args:
            library_path: Path to precomputed Dunbrack library (JSON format)
                         If None, uses built-in simplified library
        """
        self.amino_acids = list('ACDEFGHIKLMNPQRSTVWY')

        # Number of χ angles per amino acid
        self.num_chi = {
            'A': 0, 'C': 1, 'D': 2, 'E': 3, 'F': 2, 'G': 0,
            'H': 2, 'I': 2, 'K': 4, 'L': 2, 'M': 3, 'N': 2,
            'P': 2, 'Q': 3, 'R': 4, 'S': 1, 'T': 1, 'V': 1,
            'W': 2, 'Y': 2
        }

        # Backbone angle bins (10° resolution)
        self.phi_bins = np.arange(-180, 180, 10)
        self.psi_bins = np.arange(-180, 180, 10)

        # Storage for rotamer library
        # library[AA][(phi_bin, psi_bin)] = List[Rotamer]
        self.library: Dict[str, Dict[Tuple[int, int], List[Rotamer]]] = {}

        # Load library
        if library_path and library_path.exists():
            self._load_library(library_path)
        else:
            self._initialize_default_library()

    def _initialize_default_library(self):
        """
        Initialize with simplified default rotamer library.

        This is a basic implementation with common rotamers.
        For production, should use real Dunbrack 2010 data.
        """
        print("Initializing simplified rotamer library...")
        print("NOTE: For production, download Dunbrack 2010 library")

        # Common rotamers for each amino acid (simplified)
        # Format: (chi_angles, base_probability, name)
        common_rotamers = {
            'A': [],  # Alanine: no side chain
            'G': [],  # Glycine: no side chain

            # One χ angle
            'C': [([60], 0.5, 'g+'), ([-60], 0.3, 'g-'), ([180], 0.2, 't')],
            'S': [([60], 0.5, 'g+'), ([-60], 0.3, 'g-'), ([180], 0.2, 't')],
            'T': [([60], 0.6, 'g+'), ([-60], 0.2, 'g-'), ([180], 0.2, 't')],
            'V': [([180], 0.6, 't'), ([60], 0.3, 'g+'), ([-60], 0.1, 'g-')],

            # Two χ angles
            'D': [([180, -10], 0.3, 'tt'), ([60, -20], 0.25, 'g+t'),
                  ([-60, -10], 0.25, 'g-t'), ([180, 60], 0.2, 'tg+')],
            'N': [([180, -10], 0.3, 'tt'), ([60, -20], 0.25, 'g+t'),
                  ([-60, -10], 0.25, 'g-t'), ([180, 60], 0.2, 'tg+')],
            'H': [([180, 80], 0.3, 'tg+'), ([60, 80], 0.25, 'g+g+'),
                  ([-60, 80], 0.25, 'g-g+'), ([180, -80], 0.2, 'tg-')],
            'F': [([180, 80], 0.3, 'tg+'), ([60, 80], 0.25, 'g+g+'),
                  ([-60, -80], 0.25, 'g-g-'), ([180, -80], 0.2, 'tg-')],
            'Y': [([180, 80], 0.3, 'tg+'), ([60, 80], 0.25, 'g+g+'),
                  ([-60, -80], 0.25, 'g-g-'), ([180, -80], 0.2, 'tg-')],
            'W': [([180, 90], 0.35, 'tg+'), ([60, -90], 0.3, 'g+g-'),
                  ([-60, 90], 0.2, 'g-g+'), ([180, -90], 0.15, 'tg-')],
            'I': [([180, 60], 0.4, 'tg+'), ([60, 170], 0.3, 'g+t'),
                  ([-60, 170], 0.2, 'g-t'), ([180, -60], 0.1, 'tg-')],
            'L': [([180, 80], 0.3, 'tg+'), ([60, 80], 0.25, 'g+g+'),
                  ([-60, -80], 0.25, 'g-g-'), ([180, -80], 0.2, 'tg-')],
            'P': [([30, -30], 0.6, 'g+g-'), ([30, 30], 0.3, 'g+g+'),
                  ([-30, -30], 0.1, 'g-g-')],  # Proline is constrained

            # Three χ angles
            'E': [([180, 180, -20], 0.25, 'ttt'), ([60, 180, -20], 0.2, 'g+tt'),
                  ([-60, 180, -20], 0.2, 'g-tt'), ([180, 70, 20], 0.2, 'tg+g+'),
                  ([180, -80, 0], 0.15, 'tg-t')],
            'Q': [([180, 180, -20], 0.25, 'ttt'), ([60, 180, -20], 0.2, 'g+tt'),
                  ([-60, 180, -20], 0.2, 'g-tt'), ([180, 70, 20], 0.2, 'tg+g+'),
                  ([180, -80, 0], 0.15, 'tg-t')],
            'M': [([180, 180, 70], 0.25, 'ttg+'), ([180, 65, 75], 0.25, 'tg+g+'),
                  ([60, 180, 70], 0.2, 'g+tg+'), ([-60, 180, 70], 0.15, 'g-tg+'),
                  ([180, -80, -75], 0.15, 'tg-g-')],

            # Four χ angles
            'K': [([180, 180, 180, 180], 0.2, 'tttt'), ([180, 180, 68, 180], 0.15, 'ttg+t'),
                  ([60, 180, 68, 180], 0.15, 'g+tg+t'), ([-60, 180, 180, 180], 0.15, 'g-ttt'),
                  ([180, 65, 180, 65], 0.15, 'tg+tg+'), ([180, 180, 180, 65], 0.1, 'tttg+'),
                  ([62, 180, 65, 180], 0.1, 'g+tg+t')],
            'R': [([180, 180, 180, 180], 0.2, 'tttt'), ([180, 180, 65, 85], 0.15, 'ttg+g+'),
                  ([60, 180, 65, 85], 0.15, 'g+tg+g+'), ([-60, 180, 180, 180], 0.15, 'g-ttt'),
                  ([180, 65, 180, -85], 0.15, 'tg+tg-'), ([180, 180, 180, -85], 0.1, 'tttg-'),
                  ([62, 180, 65, -85], 0.1, 'g+tg+g-')]
        }

        # Populate library (backbone-independent for now)
        for aa, rotamers in common_rotamers.items():
            self.library[aa] = {}

            # Apply to all backbone bins (simplified)
            for phi_idx in range(len(self.phi_bins)):
                for psi_idx in range(len(self.psi_bins)):
                    bin_key = (phi_idx, psi_idx)

                    # Create rotamer objects
                    rotamer_list = []
                    for chi_angles, prob, name in rotamers:
                        # Pad with NaN for missing χ angles
                        chi_full = chi_angles + [np.nan] * (4 - len(chi_angles))
                        rotamer_list.append(Rotamer(
                            chi_angles=chi_full,
                            probability=prob,
                            name=name
                        ))

                    self.library[aa][bin_key] = rotamer_list

    def get_rotamers(self, amino_acid: str, phi: float, psi: float) -> List[Rotamer]:
        """
        Get rotamers for amino acid at given backbone angles.

        Args:
            amino_acid: One-letter amino acid code
            phi: φ backbone angle (degrees)
            psi: ψ backbone angle (degrees)

        Returns:
            List of Rotamer objects sorted by probability
        """
        aa = amino_acid.upper()

        if aa not in self.library:
            return []

        # Find backbone bin
        phi_idx = self._find_bin_index(phi, self.phi_bins)
        psi_idx = self._find_bin_index(psi, self.psi_bins)
        bin_key = (phi_idx, psi_idx)

        # Get rotamers for this bin
        if bin_key in self.library[aa]:
            rotamers = self.library[aa][bin_key]
            # Sort by probability (highest first)
            return sorted(rotamers, key=lambda r: r.probability, reverse=True)
        else:
            return []

    def get_most_probable_rotamer(self, amino_acid: str, phi: float, psi: float) -> Optional[Rotamer]:
        """
        Get the most probable rotamer for given backbone angles.

        Args:
            amino_acid: One-letter amino acid code
            phi: φ backbone angle (degrees)
            psi: ψ backbone angle (degrees)

        Returns:
            Most probable Rotamer, or None if no rotamers available
        """
        rotamers = self.get_rotamers(amino_acid, phi, psi)
        return rotamers[0] if rotamers else None

    def _find_bin_index(self, angle: float, bins: np.ndarray) -> int:
        """Find the bin index for an angle."""
        # Wrap angle to [-180, 180]
        angle = ((angle + 180) % 360) - 180

        # Find closest bin
        idx = np.argmin(np.abs(bins - angle))
        return int(idx)

    def _load_library(self, library_path: Path):
        """Load precomputed Dunbrack library from JSON."""
        with open(library_path, 'r') as f:
            data = json.load(f)

        # Parse library data
        for aa, aa_data in data.items():
            self.library[aa] = {}

            for bin_key_str, rotamers_data in aa_data.items():
                # Parse bin key "(phi_idx, psi_idx)"
                phi_idx, psi_idx = map(int, bin_key_str.strip('()').split(','))
                bin_key = (phi_idx, psi_idx)

                # Parse rotamers
                rotamers = []
                for rot_data in rotamers_data:
                    rotamers.append(Rotamer(
                        chi_angles=rot_data['chi_angles'],
                        probability=rot_data['probability'],
                        name=rot_data['name']
                    ))

                self.library[aa][bin_key] = rotamers

    def save_library(self, output_path: Path):
        """Save library to JSON file."""
        data = {}

        for aa, aa_data in self.library.items():
            data[aa] = {}

            for bin_key, rotamers in aa_data.items():
                bin_key_str = str(bin_key)
                data[aa][bin_key_str] = [
                    {
                        'chi_angles': [float(x) if not np.isnan(x) else None
                                     for x in rot.chi_angles],
                        'probability': float(rot.probability),
                        'name': rot.name
                    }
                    for rot in rotamers
                ]

        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)


# Testing
if __name__ == "__main__":
    print("=" * 70)
    print("Rotamer Library - Test")
    print("=" * 70)
    print()

    # Initialize library
    library = DunbrackRotamerLibrary()

    # Test on several amino acids
    test_cases = [
        ('L', -60, -45, "Alpha helix"),
        ('F', -120, 120, "Beta sheet"),
        ('K', -60, -45, "Alpha helix with long side chain"),
        ('A', -60, -45, "Alanine (no side chain)"),
    ]

    print("Testing rotamer selection:\n")

    for aa, phi, psi, context in test_cases:
        rotamers = library.get_rotamers(aa, phi, psi)
        most_prob = library.get_most_probable_rotamer(aa, phi, psi)

        print(f"{aa} at phi={phi}, psi={psi} ({context}):")
        print(f"  Number of rotamers: {len(rotamers)}")

        if most_prob:
            chi_str = ', '.join(
                f"{chi:.0f}" if not np.isnan(chi) else "N/A"
                for chi in most_prob.chi_angles
            )
            print(f"  Most probable: {most_prob.name}")
            print(f"  Chi angles: [{chi_str}]")
            print(f"  Probability: {most_prob.probability:.2f}")
        else:
            print(f"  No rotamers (expected for {aa})")
        print()

    print("=" * 70)
    print("Rotamer library initialized successfully!")
    print("Ready for side chain packing.")
