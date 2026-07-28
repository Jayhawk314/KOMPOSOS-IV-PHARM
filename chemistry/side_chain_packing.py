# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""
Side Chain Packing Module
==========================

Pack side chains onto protein backbone using rotamer library.

Takes a backbone (N, CA, C, O coordinates) and generates full atom
coordinates by selecting optimal rotamers for each side chain.

Process:
1. For each residue, get backbone angles (φ, ψ)
2. Look up rotamers from Dunbrack library
3. Select best rotamer based on:
   - Rotamer probability
   - vdW clashes with neighboring residues
   - Statistical potential energy
4. Generate full atom coordinates from rotamer χ angles

Standard Protein Geometry:
- Bond lengths: CA-CB ~1.54Å, CB-CG ~1.5Å, etc.
- Bond angles: CA-CB-CG ~110°, etc.
- Torsion angles: From rotamer library (χ1, χ2, χ3, χ4)

Applications:
- Homology modeling
- Structure refinement
- Protein design
- Side chain optimization

References:
- Dunbrack rotamer library
- SCWRL (Side Chain With a Rotamer Library)
- Rosetta side chain packing
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
import numpy as np
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from chemistry.rotamers import DunbrackRotamerLibrary, Rotamer
from chemistry.van_der_waals import VanDerWaalsConstraints


@dataclass
class FullAtomResidue:
    """
    Full atom coordinates for a single residue.

    Attributes:
        residue_idx: Residue index in sequence
        amino_acid: One-letter amino acid code
        backbone: Dict of backbone atom coordinates (N, CA, C, O)
        sidechain: Dict of side chain atom coordinates (CB, CG, etc.)
        rotamer: Selected rotamer used
    """
    residue_idx: int
    amino_acid: str
    backbone: Dict[str, np.ndarray]
    sidechain: Dict[str, np.ndarray]
    rotamer: Optional[Rotamer] = None


class SideChainPacker:
    """
    Pack side chains onto backbone using rotamer library.

    Uses Dunbrack library and vdW constraints to select optimal rotamers.
    """

    def __init__(self, rotamer_library: Optional[DunbrackRotamerLibrary] = None):
        """
        Initialize side chain packer.

        Args:
            rotamer_library: Dunbrack rotamer library (creates default if None)
        """
        self.rotamer_library = rotamer_library or DunbrackRotamerLibrary()
        self.vdw = VanDerWaalsConstraints()

        # Standard bond lengths (Å)
        self.bond_lengths = {
            'CA-CB': 1.54,
            'CB-CG': 1.52,
            'CG-CD': 1.52,
            'CD-CE': 1.52,
            'CE-NZ': 1.46,  # Lysine
            'CG-OD': 1.25,  # Asp
            'CG-ND': 1.33,  # Asn
            'CD-OE': 1.25,  # Glu
            'CD-NE': 1.33,  # Gln
            'CD-NE-CZ': 1.33,  # Arg
            'CB-OG': 1.43,  # Ser
            'CB-SG': 1.81,  # Cys
        }

        # Standard bond angles (degrees)
        self.bond_angles = {
            'N-CA-CB': 110.5,
            'CA-CB-CG': 113.0,
            'CB-CG-CD': 112.0,
            'CG-CD-CE': 112.0,
        }

    def pack_structure(self, backbone_coords: np.ndarray, sequence: str,
                      phi: np.ndarray, psi: np.ndarray) -> List[FullAtomResidue]:
        """
        Pack side chains for entire structure.

        Args:
            backbone_coords: Nx4x3 array (N, CA, C, O for each residue)
            sequence: Amino acid sequence
            phi: φ angles for each residue
            psi: ψ angles for each residue

        Returns:
            List of FullAtomResidue objects with packed side chains
        """
        N = len(sequence)
        packed_residues = []

        print(f"Packing {N} residues...")

        for i in range(N):
            aa = sequence[i]

            # Extract backbone
            backbone = {
                'N': backbone_coords[i, 0],
                'CA': backbone_coords[i, 1],
                'C': backbone_coords[i, 2],
                'O': backbone_coords[i, 3]
            }

            # Pack side chain
            if aa in ['G', 'A']:
                # Glycine has no side chain, Alanine only has CB
                sidechain = self._pack_simple_sidechain(aa, backbone)
                rotamer = None
            else:
                # Use rotamer library
                current_phi = phi[i] if not np.isnan(phi[i]) else -60
                current_psi = psi[i] if not np.isnan(psi[i]) else -40

                sidechain, rotamer = self._pack_rotamer_sidechain(
                    aa, backbone, current_phi, current_psi, packed_residues
                )

            packed_residues.append(FullAtomResidue(
                residue_idx=i,
                amino_acid=aa,
                backbone=backbone,
                sidechain=sidechain,
                rotamer=rotamer
            ))

        print(f"Packing complete: {len(packed_residues)} residues")
        return packed_residues

    def _pack_simple_sidechain(self, aa: str, backbone: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
        """Pack simple side chains (Gly, Ala)."""
        sidechain = {}

        if aa == 'A':
            # Alanine: just add CB
            N = backbone['N']
            CA = backbone['CA']
            C = backbone['C']

            # CB is ~tetrahedral from CA
            # Place at standard geometry
            v_n = N - CA
            v_c = C - CA
            v_n = v_n / (np.linalg.norm(v_n) + 1e-10)
            v_c = v_c / (np.linalg.norm(v_c) + 1e-10)

            # CB direction: perpendicular to N-CA-C plane
            v_cb = np.cross(v_n, v_c)
            v_cb = v_cb / (np.linalg.norm(v_cb) + 1e-10)

            # Place CB at standard distance
            CB = CA + v_cb * self.bond_lengths['CA-CB']
            sidechain['CB'] = CB

        # Glycine has no side chain
        return sidechain

    def _pack_rotamer_sidechain(self, aa: str, backbone: Dict[str, np.ndarray],
                                phi: float, psi: float,
                                packed_residues: List[FullAtomResidue]) -> Tuple[Dict[str, np.ndarray], Rotamer]:
        """
        Pack side chain using rotamer library.

        Args:
            aa: Amino acid type
            backbone: Backbone atom coordinates
            phi: φ angle
            psi: ψ angle
            packed_residues: Previously packed residues (for clash checking)

        Returns:
            (sidechain_coords, selected_rotamer)
        """
        # Get possible rotamers
        rotamers = self.rotamer_library.get_rotamers(aa, phi, psi)

        if not rotamers:
            # No rotamers available, return minimal side chain
            return self._pack_simple_sidechain(aa, backbone), None

        # Try rotamers in order of probability
        for rotamer in rotamers:
            # Generate coordinates for this rotamer
            sidechain = self._build_sidechain_from_rotamer(aa, backbone, rotamer)

            # Check for clashes with neighboring residues
            if self._check_no_clashes(sidechain, packed_residues):
                return sidechain, rotamer

        # If all rotamers clash, use most probable anyway
        best_rotamer = rotamers[0]
        sidechain = self._build_sidechain_from_rotamer(aa, backbone, best_rotamer)
        return sidechain, best_rotamer

    def _build_sidechain_from_rotamer(self, aa: str, backbone: Dict[str, np.ndarray],
                                     rotamer: Rotamer) -> Dict[str, np.ndarray]:
        """
        Build full side chain coordinates from rotamer χ angles.

        Uses standard bond lengths/angles and rotamer χ torsions.

        Args:
            aa: Amino acid type
            backbone: Backbone coordinates
            rotamer: Rotamer with χ angles

        Returns:
            Dict of side chain atom coordinates
        """
        sidechain = {}

        # Start with CB
        CA = backbone['CA']
        N = backbone['N']
        C = backbone['C']

        # Build CB using standard geometry
        CB = self._place_atom_tetrahedral(N, CA, C, self.bond_lengths['CA-CB'])
        sidechain['CB'] = CB

        # Build rest of side chain based on amino acid type and χ angles
        chi_angles = rotamer.chi_angles

        # This is a simplified implementation
        # Full implementation would handle all 20 amino acids with proper geometry

        if aa in ['C', 'S', 'T', 'V']:
            # One chi angle, terminal atom
            if not np.isnan(chi_angles[0]):
                # For Cys: CB-SG, for Ser/Thr: CB-OG, for Val: CB-CG1
                atom_name = 'SG' if aa == 'C' else ('OG' if aa in 'ST' else 'CG1')
                bond_length = self.bond_lengths.get('CB-SG' if aa == 'C' else 'CB-OG', 1.5)

                terminal = self._place_atom_with_chi(CA, CB, N, bond_length, chi_angles[0])
                sidechain[atom_name] = terminal

        elif aa in ['D', 'N', 'F', 'Y', 'W', 'H', 'I', 'L', 'P']:
            # Two chi angles
            if not np.isnan(chi_angles[0]):
                CG = self._place_atom_with_chi(CA, CB, N, self.bond_lengths['CB-CG'], chi_angles[0])
                sidechain['CG'] = CG

                if not np.isnan(chi_angles[1]) and aa in ['D', 'N']:
                    # Terminal OD/ND
                    atom_name = 'OD1' if aa == 'D' else 'ND2'
                    bond_length = self.bond_lengths.get('CG-OD' if aa == 'D' else 'CG-ND', 1.3)
                    terminal = self._place_atom_with_chi(CB, CG, CA, bond_length, chi_angles[1])
                    sidechain[atom_name] = terminal

        elif aa in ['E', 'Q', 'M']:
            # Three chi angles
            if not np.isnan(chi_angles[0]):
                CG = self._place_atom_with_chi(CA, CB, N, self.bond_lengths['CB-CG'], chi_angles[0])
                sidechain['CG'] = CG

                if not np.isnan(chi_angles[1]):
                    CD = self._place_atom_with_chi(CB, CG, CA, self.bond_lengths['CG-CD'], chi_angles[1])
                    sidechain['CD'] = CD

        elif aa in ['K', 'R']:
            # Four chi angles
            if not np.isnan(chi_angles[0]):
                CG = self._place_atom_with_chi(CA, CB, N, self.bond_lengths['CB-CG'], chi_angles[0])
                sidechain['CG'] = CG

                if not np.isnan(chi_angles[1]):
                    CD = self._place_atom_with_chi(CB, CG, CA, self.bond_lengths['CG-CD'], chi_angles[1])
                    sidechain['CD'] = CD

                    if not np.isnan(chi_angles[2]):
                        CE = self._place_atom_with_chi(CG, CD, CB, self.bond_lengths['CD-CE'], chi_angles[2])
                        sidechain['CE'] = CE

        return sidechain

    def _place_atom_tetrahedral(self, atom1: np.ndarray, atom2: np.ndarray,
                                atom3: np.ndarray, bond_length: float) -> np.ndarray:
        """
        Place atom in tetrahedral geometry.

        Atom4 is placed relative to atom2, tetrahedral from atom1-atom2-atom3.
        """
        v1 = atom1 - atom2
        v3 = atom3 - atom2

        v1 = v1 / (np.linalg.norm(v1) + 1e-10)
        v3 = v3 / (np.linalg.norm(v3) + 1e-10)

        # Tetrahedral direction
        v4 = -np.cross(v1, v3)
        v4 = v4 / (np.linalg.norm(v4) + 1e-10)

        return atom2 + v4 * bond_length

    def _place_atom_with_chi(self, atom1: np.ndarray, atom2: np.ndarray,
                            atom3: np.ndarray, bond_length: float,
                            chi: float) -> np.ndarray:
        """
        Place atom using dihedral angle χ.

        Places new atom relative to atom2, along atom2-atom3 bond,
        with torsion angle χ around atom1-atom2-atom3.
        """
        # Convert chi to radians
        chi_rad = np.radians(chi)

        # Vectors
        v1 = atom1 - atom2
        v2 = atom3 - atom2

        v1 = v1 / (np.linalg.norm(v1) + 1e-10)
        v2 = v2 / (np.linalg.norm(v2) + 1e-10)

        # Perpendicular vector
        v_perp = np.cross(v1, v2)
        v_perp = v_perp / (np.linalg.norm(v_perp) + 1e-10)

        # Rotate v2 by chi around axis v1
        # Use Rodrigues' rotation formula
        v_rot = (v2 * np.cos(chi_rad) +
                np.cross(v_perp, v2) * np.sin(chi_rad) +
                v_perp * np.dot(v_perp, v2) * (1 - np.cos(chi_rad)))

        return atom2 + v_rot * bond_length

    def _check_no_clashes(self, sidechain: Dict[str, np.ndarray],
                         packed_residues: List[FullAtomResidue],
                         clash_threshold: float = 2.0) -> bool:
        """
        Check if side chain clashes with previously packed residues.

        Args:
            sidechain: Current side chain coordinates
            packed_residues: Previously packed residues
            clash_threshold: Minimum allowed distance (Å)

        Returns:
            True if no clashes, False if clashes detected
        """
        # Check only against nearby residues (within 10 residues)
        for prev_res in packed_residues[-10:]:
            for atom1_coords in sidechain.values():
                for atom2_coords in prev_res.sidechain.values():
                    dist = np.linalg.norm(atom1_coords - atom2_coords)
                    if dist < clash_threshold:
                        return False

        return True


# Testing
if __name__ == "__main__":
    print("=" * 70)
    print("Side Chain Packing - Test")
    print("=" * 70)
    print()

    # Create test backbone (simple helix)
    sequence = "ALKFDE"
    N = len(sequence)

    # Generate helical backbone coordinates
    backbone_coords = np.zeros((N, 4, 3))

    for i in range(N):
        angle = i * 100 * np.pi / 180
        # CA position
        ca = np.array([2.3 * np.cos(angle), 2.3 * np.sin(angle), i * 1.5])

        # N (before CA)
        n = ca + np.array([-0.5, 0, -0.5])
        # C (after CA)
        c = ca + np.array([0.5, 0, 0.5])
        # O (carbonyl)
        o = c + np.array([0, 0.5, 0])

        backbone_coords[i] = np.array([n, ca, c, o])

    # Phi/psi angles (helical)
    phi = np.full(N, -60.0)
    psi = np.full(N, -45.0)

    # Pack side chains
    packer = SideChainPacker()
    packed = packer.pack_structure(backbone_coords, sequence, phi, psi)

    print(f"Sequence: {sequence}")
    print(f"Packed {len(packed)} residues\n")

    # Show results
    for res in packed:
        print(f"Residue {res.residue_idx} ({res.amino_acid}):")
        print(f"  Backbone atoms: {list(res.backbone.keys())}")
        print(f"  Side chain atoms: {list(res.sidechain.keys())}")
        if res.rotamer:
            print(f"  Rotamer: {res.rotamer.name}")
            print(f"  Probability: {res.rotamer.probability:.2f}")
        print()

    print("=" * 70)
    print("Side chain packing complete!")
