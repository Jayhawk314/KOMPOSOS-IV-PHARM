# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""
Statistical Potentials Module
==============================

Knowledge-based statistical potentials derived from PDB structures.

Statistical potentials capture the frequencies with which different amino acid
pairs occur at various distances in known protein structures. They provide an
empirical energy function based on the Boltzmann hypothesis:

    E(d, i, j) = -kT ln[P(d|i,j) / P(d)]

Where:
- E(d, i, j): Statistical potential energy
- d: Distance between residues
- i, j: Amino acid types
- P(d|i,j): Observed frequency of distance d for pair (i,j)
- P(d): Background frequency (reference state)
- kT: Thermal energy (usually set to 1)

Data Source:
- PDB Top8000: High-quality structures (resolution < 2.5Å, R-factor < 0.25)
- ~8000 non-redundant structures
- Precomputed and cached for efficiency

Applications:
- Structure quality assessment
- Contact prediction scoring
- Energy-based structure refinement
- Homology modeling validation

References:
- Sippl (1990): "Calculation of conformational ensembles from potentials of mean force"
- Sippl (1993): "Recognition of errors in three-dimensional structures of proteins"
- Lu & Skolnick (2001): "A distance-dependent atomic knowledge-based potential"
- Zhou & Zhou (2002): "Distance-scaled, finite ideal-gas reference state improves structure-derived potentials"

Website: https://pmc.ncbi.nlm.nih.gov/articles/PMC2242414/
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
from pathlib import Path
import numpy as np
import json


@dataclass
class PotentialStatistics:
    """Statistics about computed potentials."""
    num_structures: int
    num_pairs: int
    distance_range: Tuple[float, float]
    bin_size: float
    total_observations: int


class StatisticalPotentials:
    """
    Statistical potentials derived from PDB structures.

    Implements distance-dependent pair potentials based on observed
    frequencies in high-quality protein structures.
    """

    def __init__(self, potentials_file: Optional[Path] = None):
        """
        Initialize statistical potentials.

        Args:
            potentials_file: Path to precomputed potentials file (JSON format)
                            If None, uses built-in default potentials
        """
        self.amino_acids = list('ACDEFGHIKLMNPQRSTVWY')  # 20 standard amino acids
        self.num_aa = len(self.amino_acids)
        self.aa_to_idx = {aa: i for i, aa in enumerate(self.amino_acids)}

        # Distance binning
        self.distance_min = 0.0
        self.distance_max = 20.0
        self.bin_size = 0.5
        self.distance_bins = np.arange(self.distance_min, self.distance_max + self.bin_size, self.bin_size)
        self.num_bins = len(self.distance_bins) - 1

        # Storage for pair potentials
        # Shape: (num_aa, num_aa, num_bins)
        self.pair_potentials = np.zeros((self.num_aa, self.num_aa, self.num_bins))
        self.pair_counts = np.zeros((self.num_aa, self.num_aa, self.num_bins))
        self.background_counts = np.zeros(self.num_bins)

        # Statistics
        self.statistics = PotentialStatistics(
            num_structures=0,
            num_pairs=0,
            distance_range=(self.distance_min, self.distance_max),
            bin_size=self.bin_size,
            total_observations=0
        )

        # Load potentials
        if potentials_file and potentials_file.exists():
            self._load_potentials(potentials_file)
        else:
            self._initialize_default_potentials()

    def _initialize_default_potentials(self):
        """
        Initialize with simplified default potentials.

        These are rough approximations based on general protein statistics.
        For production use, should be replaced with real PDB-derived potentials.
        """
        # Simplified model: favorable for similar hydrophobicity
        from chemistry.hydrophobic import HydrophobicConstraints
        hydro = HydrophobicConstraints()

        # For each pair, create distance-dependent potential
        for i, aa_i in enumerate(self.amino_acids):
            h_i = hydro.hydrophobicity.get(aa_i, 0.0)

            for j, aa_j in enumerate(self.amino_acids):
                h_j = hydro.hydrophobicity.get(aa_j, 0.0)

                # Similar hydrophobicity = more favorable contact
                hydro_similarity = 1.0 - abs(h_i - h_j) / 9.0  # Normalize by max difference

                # Distance-dependent profile
                for k, dist_center in enumerate(self.distance_bins[:-1]):
                    dist = dist_center + self.bin_size / 2

                    # Optimal contact distance: 6-8 Å
                    if 6.0 <= dist <= 8.0:
                        # Favorable at optimal distance
                        self.pair_potentials[i, j, k] = -hydro_similarity * 0.5
                    elif 4.0 <= dist < 6.0 or 8.0 < dist <= 10.0:
                        # Less favorable
                        self.pair_potentials[i, j, k] = -hydro_similarity * 0.2
                    elif dist < 4.0:
                        # Too close (repulsive)
                        self.pair_potentials[i, j, k] = 1.0 / max(dist, 0.1)
                    else:
                        # Too far (no interaction)
                        self.pair_potentials[i, j, k] = 0.0

        self.statistics = PotentialStatistics(
            num_structures=0,
            num_pairs=0,
            distance_range=(self.distance_min, self.distance_max),
            bin_size=self.bin_size,
            total_observations=0
        )

    def extract_from_pdb(self, pdb_files: List[Path], output_file: Path):
        """
        Extract statistical potentials from PDB structures.

        This would analyze a collection of high-quality PDB files and compute
        observed frequencies. For production use with PDB Top8000.

        Args:
            pdb_files: List of PDB file paths
            output_file: Where to save computed potentials
        """
        # Reset counts
        self.pair_counts = np.zeros((self.num_aa, self.num_aa, self.num_bins))
        self.background_counts = np.zeros(self.num_bins)

        total_pairs = 0

        # Process each PDB file
        for pdb_file in pdb_files:
            pairs = self._extract_pairs_from_pdb(pdb_file)
            total_pairs += len(pairs)

            for aa_i, aa_j, distance in pairs:
                if aa_i not in self.aa_to_idx or aa_j not in self.aa_to_idx:
                    continue

                # Get indices
                idx_i = self.aa_to_idx[aa_i]
                idx_j = self.aa_to_idx[aa_j]

                # Find distance bin
                bin_idx = int((distance - self.distance_min) / self.bin_size)
                if 0 <= bin_idx < self.num_bins:
                    self.pair_counts[idx_i, idx_j, bin_idx] += 1
                    self.pair_counts[idx_j, idx_i, bin_idx] += 1  # Symmetric
                    self.background_counts[bin_idx] += 2

        # Compute potentials from counts
        self._compute_potentials_from_counts()

        # Save to file
        self._save_potentials(output_file)

        # Update statistics
        self.statistics = PotentialStatistics(
            num_structures=len(pdb_files),
            num_pairs=total_pairs,
            distance_range=(self.distance_min, self.distance_max),
            bin_size=self.bin_size,
            total_observations=int(np.sum(self.pair_counts))
        )

    def _extract_pairs_from_pdb(self, pdb_file: Path) -> List[Tuple[str, str, float]]:
        """
        Extract amino acid pairs and distances from a PDB file.

        Args:
            pdb_file: Path to PDB file

        Returns:
            List of (aa_i, aa_j, distance) tuples
        """
        # TODO: Implement PDB parsing
        # Would use BioPython or similar to:
        # 1. Parse PDB structure
        # 2. Extract CA coordinates
        # 3. Get amino acid types
        # 4. Compute all pairwise distances
        # 5. Return pairs within distance range

        pairs = []
        # Placeholder implementation
        return pairs

    def _compute_potentials_from_counts(self):
        """
        Compute statistical potentials from observed counts.

        Uses Sippl's formula:
            E(d, i, j) = -ln[N(d, i, j) / N(d)]

        Where:
        - N(d, i, j): Count of pair (i,j) at distance d
        - N(d): Total count at distance d (background)
        """
        # Avoid division by zero
        epsilon = 1e-10

        for i in range(self.num_aa):
            for j in range(self.num_aa):
                for k in range(self.num_bins):
                    observed = self.pair_counts[i, j, k]
                    background = self.background_counts[k]

                    if observed > 0 and background > 0:
                        # Normalize by total counts
                        p_observed = observed / np.sum(self.pair_counts[i, j, :] + epsilon)
                        p_background = background / np.sum(self.background_counts + epsilon)

                        # Statistical potential: -ln(observed/expected)
                        if p_background > 0:
                            self.pair_potentials[i, j, k] = -np.log(p_observed / p_background)
                        else:
                            self.pair_potentials[i, j, k] = 0.0
                    else:
                        # No observations: neutral energy
                        self.pair_potentials[i, j, k] = 0.0

    def score_contact(self, aa1: str, aa2: str, distance: float) -> float:
        """
        Score a contact based on statistical potential.

        Args:
            aa1: First amino acid (one-letter code)
            aa2: Second amino acid (one-letter code)
            distance: CA-CA distance (Å)

        Returns:
            Energy score (negative = favorable, positive = unfavorable)
        """
        aa1 = aa1.upper()
        aa2 = aa2.upper()

        if aa1 not in self.aa_to_idx or aa2 not in self.aa_to_idx:
            return 0.0  # Unknown amino acid

        # Get indices
        idx1 = self.aa_to_idx[aa1]
        idx2 = self.aa_to_idx[aa2]

        # Find distance bin
        bin_idx = int((distance - self.distance_min) / self.bin_size)

        if 0 <= bin_idx < self.num_bins:
            return float(self.pair_potentials[idx1, idx2, bin_idx])
        else:
            return 0.0  # Out of range

    def score_structure(self, coords: np.ndarray, sequence: str, contacts: List[Tuple[int, int]]) -> Dict:
        """
        Score entire structure using statistical potentials.

        Args:
            coords: Nx3 CA coordinates
            sequence: Amino acid sequence
            contacts: List of (i, j) contact pairs

        Returns:
            Dictionary with scoring results
        """
        if len(sequence) != len(coords):
            raise ValueError("Sequence and coordinates length mismatch")

        scores = []
        favorable_count = 0
        unfavorable_count = 0

        for i, j in contacts:
            if i >= len(sequence) or j >= len(sequence):
                continue

            aa_i = sequence[i]
            aa_j = sequence[j]
            distance = np.linalg.norm(coords[i] - coords[j])

            score = self.score_contact(aa_i, aa_j, distance)
            scores.append(score)

            if score < -0.1:
                favorable_count += 1
            elif score > 0.1:
                unfavorable_count += 1

        total_energy = sum(scores)
        mean_energy = np.mean(scores) if scores else 0.0

        # Quality assessment
        if mean_energy < -0.2:
            quality = "EXCELLENT - Highly favorable contacts"
        elif mean_energy < 0:
            quality = "GOOD - Favorable contacts overall"
        elif mean_energy < 0.2:
            quality = "FAIR - Mixed quality contacts"
        else:
            quality = "POOR - Unfavorable contact pattern"

        return {
            'quality': quality,
            'total_energy': float(total_energy),
            'mean_energy': float(mean_energy),
            'num_contacts': len(contacts),
            'favorable_contacts': favorable_count,
            'unfavorable_contacts': unfavorable_count,
            'neutral_contacts': len(contacts) - favorable_count - unfavorable_count,
            'contact_scores': [
                {
                    'residue_i': i,
                    'residue_j': j,
                    'aa_i': sequence[i],
                    'aa_j': sequence[j],
                    'distance': float(np.linalg.norm(coords[i] - coords[j])),
                    'score': float(self.score_contact(sequence[i], sequence[j],
                                   np.linalg.norm(coords[i] - coords[j])))
                }
                for i, j in contacts[:20]  # Limit to first 20
            ]
        }

    def _save_potentials(self, output_file: Path):
        """Save computed potentials to JSON file."""
        data = {
            'amino_acids': self.amino_acids,
            'distance_bins': self.distance_bins.tolist(),
            'pair_potentials': self.pair_potentials.tolist(),
            'statistics': {
                'num_structures': self.statistics.num_structures,
                'num_pairs': self.statistics.num_pairs,
                'total_observations': self.statistics.total_observations
            }
        }

        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)

    def _load_potentials(self, potentials_file: Path):
        """Load precomputed potentials from JSON file."""
        with open(potentials_file, 'r') as f:
            data = json.load(f)

        self.amino_acids = data['amino_acids']
        self.distance_bins = np.array(data['distance_bins'])
        self.pair_potentials = np.array(data['pair_potentials'])

        if 'statistics' in data:
            stats = data['statistics']
            self.statistics = PotentialStatistics(
                num_structures=stats.get('num_structures', 0),
                num_pairs=stats.get('num_pairs', 0),
                distance_range=(self.distance_min, self.distance_max),
                bin_size=self.bin_size,
                total_observations=stats.get('total_observations', 0)
            )


# Convenience function
def score_structure_with_potentials(coords: np.ndarray, sequence: str,
                                   contacts: List[Tuple[int, int]]) -> Dict:
    """Convenience function to score structure with statistical potentials."""
    potentials = StatisticalPotentials()
    return potentials.score_structure(coords, sequence, contacts)


# Testing
if __name__ == "__main__":
    print("=" * 70)
    print("Statistical Potentials - Test")
    print("=" * 70)
    print()

    # Create test structure
    sequence = "LVILMFAILVILMFAI"  # Hydrophobic residues
    N = len(sequence)

    # Helical coordinates
    coords = np.zeros((N, 3))
    for i in range(N):
        angle = i * 100 * np.pi / 180
        coords[i] = [2.3 * np.cos(angle), 2.3 * np.sin(angle), i * 1.5]

    # Define contacts (helix i, i+4)
    contacts = [(i, i+4) for i in range(N-4)]

    # Score with statistical potentials
    potentials = StatisticalPotentials()
    result = potentials.score_structure(coords, sequence, contacts)

    print(f"Sequence: {sequence}")
    print(f"Quality: {result['quality']}")
    print(f"Total energy: {result['total_energy']:.2f}")
    print(f"Mean energy per contact: {result['mean_energy']:.3f}")
    print(f"Favorable contacts: {result['favorable_contacts']}/{result['num_contacts']}")
    print(f"Unfavorable contacts: {result['unfavorable_contacts']}/{result['num_contacts']}")
    print()

    # Show some individual scores
    print("Sample contact scores:")
    for cs in result['contact_scores'][:5]:
        print(f"  {cs['aa_i']}{cs['residue_i']} - {cs['aa_j']}{cs['residue_j']}: "
              f"{cs['distance']:.2f}A, score={cs['score']:.3f}")
