# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""
Hydrophobic Effect Module
==========================

Hydrophobic effect: hydrophobic residues prefer protein core burial.

The hydrophobic effect is the primary driving force for protein folding.
Hydrophobic residues (nonpolar sidechains) are buried in the protein core
to minimize unfavorable water contacts, while polar/charged residues prefer
the surface where they can interact with solvent.

Physical Principles:
- Hydrophobic residues: AILMFVPW (nonpolar sidechains)
- Polar residues: STNQCY (uncharged polar)
- Charged residues: KRHDE (ionic)
- Burial propensity: Hydrophobic > Polar > Charged
- Core formation: Hydrophobic collapse drives folding

Hydrophobicity Scale (Kyte-Doolittle):
- Positive values: Hydrophobic (prefer burial)
- Negative values: Hydrophilic (prefer surface)
- Range: -4.5 (R, most hydrophilic) to +4.5 (I, most hydrophobic)

Burial Metrics:
- Distance from geometric center
- Solvent accessibility (requires full atoms, not implemented yet)
- Contact number (more contacts = more buried)

References:
- Kyte & Doolittle (1982): "A simple method for displaying the hydropathic
  character of a protein", J. Mol. Biol. 157:105-132
- Protein folding textbooks (Anfinsen, Levinthal, Dill)
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
import numpy as np


@dataclass
class BurialAnalysis:
    """Analysis of residue burial in protein structure."""
    residue_idx: int
    amino_acid: str
    burial_score: float  # 0 = surface, 1 = buried
    distance_from_center: float
    hydrophobicity: float
    is_buried: bool  # burial_score > 0.5
    is_hydrophobic: bool
    proper_burial: bool  # Hydrophobic buried or hydrophilic exposed


class HydrophobicConstraints:
    """
    Hydrophobic effect: hydrophobic residues prefer protein core.

    Validates that:
    - Hydrophobic residues are buried (distance from center < median)
    - Polar/charged residues are exposed (distance from center > median)
    - Overall burial pattern matches expected folding
    """

    def __init__(self):
        """Initialize hydrophobic constraints with Kyte-Doolittle scale."""

        # Kyte-Doolittle hydrophobicity scale
        # Positive = hydrophobic, Negative = hydrophilic
        self.hydrophobicity = {
            'I': 4.5,  'V': 4.2,  'L': 3.8,  'F': 2.8,  'C': 2.5,
            'M': 1.9,  'A': 1.8,  'W': -0.9, 'G': -0.4, 'T': -0.7,
            'S': -0.8, 'Y': -1.3, 'P': -1.6, 'H': -3.2, 'N': -3.5,
            'D': -3.5, 'Q': -3.5, 'E': -3.5, 'K': -3.9, 'R': -4.5
        }

        # Classify residues
        self.hydrophobic = set([aa for aa, h in self.hydrophobicity.items() if h > 1.0])
        self.polar = set('STNQCY')
        self.charged = set('KRHDE')

        # Burial thresholds
        self.buried_threshold = 0.5  # burial_score > 0.5 = buried

    def compute_burial_scores(self, coords: np.ndarray, sequence: str) -> List[BurialAnalysis]:
        """
        Compute burial score for each residue.

        Burial score based on distance from geometric center:
        - Closer to center = higher burial score
        - Farther from center = lower burial score

        Args:
            coords: Nx3 CA coordinates
            sequence: Amino acid sequence

        Returns:
            List of BurialAnalysis objects
        """
        N = len(sequence)

        # Compute geometric center
        center = np.mean(coords, axis=0)

        # Distance from center for each residue
        distances = np.linalg.norm(coords - center, axis=1)

        # Normalize burial scores
        # burial_score = 1 - (distance / max_distance)
        max_dist = np.max(distances)
        burial_scores = 1.0 - (distances / max_dist) if max_dist > 0 else np.ones(N)

        # Create analysis for each residue
        analyses = []
        for i, aa in enumerate(sequence):
            burial_score = burial_scores[i]
            hydrophobicity = self.hydrophobicity.get(aa, 0.0)
            is_buried = burial_score > self.buried_threshold
            is_hydrophobic = aa in self.hydrophobic

            # Proper burial: hydrophobic buried OR hydrophilic exposed
            if is_hydrophobic:
                proper_burial = is_buried  # Hydrophobic should be buried
            else:
                proper_burial = not is_buried  # Hydrophilic should be exposed

            analyses.append(BurialAnalysis(
                residue_idx=i,
                amino_acid=aa,
                burial_score=float(burial_score),
                distance_from_center=float(distances[i]),
                hydrophobicity=hydrophobicity,
                is_buried=is_buried,
                is_hydrophobic=is_hydrophobic,
                proper_burial=proper_burial
            ))

        return analyses

    def validate_hydrophobic_core(self, coords: np.ndarray, sequence: str) -> Tuple[float, List[Dict]]:
        """
        Validate that hydrophobic residues are properly buried.

        Args:
            coords: Nx3 CA coordinates
            sequence: Amino acid sequence

        Returns:
            (overall_score, list of issues)
        """
        analyses = self.compute_burial_scores(coords, sequence)

        issues = []
        hydrophobic_buried_count = 0
        hydrophobic_total = 0
        polar_exposed_count = 0
        polar_total = 0

        for analysis in analyses:
            aa = analysis.amino_acid
            burial = analysis.burial_score
            is_buried = analysis.is_buried

            if aa in self.hydrophobic:
                hydrophobic_total += 1
                if is_buried:
                    hydrophobic_buried_count += 1
                else:
                    # Hydrophobic residue exposed - issue
                    issues.append({
                        'severity': 'WARNING',
                        'residue': analysis.residue_idx,
                        'type': aa,
                        'burial': burial,
                        'message': f'Hydrophobic {aa}{analysis.residue_idx} exposed (burial={burial:.2f})'
                    })

            elif aa in self.polar or aa in self.charged:
                polar_total += 1
                if not is_buried:
                    polar_exposed_count += 1
                # Note: Buried polar/charged is sometimes OK (active sites, salt bridges)

        # Compute scores
        if hydrophobic_total > 0:
            hydrophobic_burial_ratio = hydrophobic_buried_count / hydrophobic_total
        else:
            hydrophobic_burial_ratio = 1.0

        if polar_total > 0:
            polar_exposure_ratio = polar_exposed_count / polar_total
        else:
            polar_exposure_ratio = 1.0

        # Overall score: weighted average
        # Hydrophobic burial more important (70%) than polar exposure (30%)
        score = 0.7 * hydrophobic_burial_ratio + 0.3 * polar_exposure_ratio

        return score, issues

    def analyze_hydrophobic_core(self, coords: np.ndarray, sequence: str) -> Dict:
        """
        Comprehensive hydrophobic core analysis.

        Args:
            coords: Nx3 CA coordinates
            sequence: Amino acid sequence

        Returns:
            Dictionary with analysis metrics
        """
        score, issues = self.validate_hydrophobic_core(coords, sequence)
        analyses = self.compute_burial_scores(coords, sequence)

        # Count residue types and burial
        total = len(sequence)
        hydrophobic_count = sum(1 for a in analyses if a.is_hydrophobic)
        polar_charged_count = total - hydrophobic_count

        hydrophobic_buried = sum(1 for a in analyses if a.is_hydrophobic and a.is_buried)
        hydrophobic_exposed = hydrophobic_count - hydrophobic_buried

        polar_buried = sum(1 for a in analyses if not a.is_hydrophobic and a.is_buried)
        polar_exposed = polar_charged_count - polar_buried

        # Proper burial percentage
        proper_burial_count = sum(1 for a in analyses if a.proper_burial)
        proper_burial_percent = 100.0 * proper_burial_count / total if total > 0 else 0.0

        # Mean burial scores
        mean_burial_hydrophobic = np.mean([a.burial_score for a in analyses if a.is_hydrophobic]) if hydrophobic_count > 0 else 0.0
        mean_burial_polar = np.mean([a.burial_score for a in analyses if not a.is_hydrophobic]) if polar_charged_count > 0 else 0.0

        # Quality assessment
        if score > 0.8:
            quality = "EXCELLENT - Well-formed hydrophobic core"
        elif score > 0.6:
            quality = "GOOD - Acceptable hydrophobic patterning"
        elif score > 0.4:
            quality = "FAIR - Some hydrophobic misplacement"
        else:
            quality = "POOR - Hydrophobic core disrupted"

        return {
            'quality': quality,
            'overall_score': float(score),
            'proper_burial_percent': float(proper_burial_percent),
            'hydrophobic_count': hydrophobic_count,
            'hydrophobic_buried': hydrophobic_buried,
            'hydrophobic_exposed': hydrophobic_exposed,
            'polar_charged_count': polar_charged_count,
            'polar_buried': polar_buried,
            'polar_exposed': polar_exposed,
            'mean_burial_hydrophobic': float(mean_burial_hydrophobic),
            'mean_burial_polar': float(mean_burial_polar),
            'num_issues': len(issues),
            'issues': issues[:10],  # Limit to first 10 issues
            'burial_analyses': [
                {
                    'residue': a.residue_idx,
                    'aa': a.amino_acid,
                    'burial_score': float(a.burial_score),
                    'is_hydrophobic': a.is_hydrophobic,
                    'proper_burial': a.proper_burial
                }
                for a in analyses
            ]
        }


# Convenience functions
def compute_burial_scores(coords: np.ndarray, sequence: str) -> List[BurialAnalysis]:
    """Convenience function to compute burial scores."""
    hydro = HydrophobicConstraints()
    return hydro.compute_burial_scores(coords, sequence)


def validate_hydrophobic_core(coords: np.ndarray, sequence: str) -> Tuple[float, List[Dict]]:
    """Convenience function to validate hydrophobic core."""
    hydro = HydrophobicConstraints()
    return hydro.validate_hydrophobic_core(coords, sequence)


# Testing
if __name__ == "__main__":
    print("=" * 70)
    print("Hydrophobic Constraints - Test")
    print("=" * 70)
    print()

    # Test: Protein with hydrophobic core
    # LIVF in center, KRED on surface
    sequence = "KREDLILIVFKRED"  # Charged outside, hydrophobic inside
    N = len(sequence)

    # Create coords with hydrophobic residues toward center
    coords = np.zeros((N, 3))
    center_start = 4  # Where hydrophobic core starts
    center_end = 10

    for i in range(N):
        if center_start <= i < center_end:
            # Hydrophobic core: small radius
            angle = i * 60 * np.pi / 180
            coords[i] = [1.5 * np.cos(angle), 1.5 * np.sin(angle), i * 0.5]
        else:
            # Charged residues: larger radius (surface)
            angle = i * 60 * np.pi / 180
            coords[i] = [4.0 * np.cos(angle), 4.0 * np.sin(angle), i * 0.5]

    hydro = HydrophobicConstraints()
    analysis = hydro.analyze_hydrophobic_core(coords, sequence)

    print(f"Sequence: {sequence}")
    print(f"Quality: {analysis['quality']}")
    print(f"Overall score: {analysis['overall_score']:.2f}")
    print(f"Proper burial: {analysis['proper_burial_percent']:.1f}%")
    print()
    print(f"Hydrophobic residues: {analysis['hydrophobic_count']}")
    print(f"  Buried: {analysis['hydrophobic_buried']}")
    print(f"  Exposed: {analysis['hydrophobic_exposed']}")
    print()
    print(f"Polar/Charged residues: {analysis['polar_charged_count']}")
    print(f"  Buried: {analysis['polar_buried']}")
    print(f"  Exposed: {analysis['polar_exposed']}")
    print()

    if analysis['issues']:
        print("Issues:")
        for issue in analysis['issues'][:5]:
            print(f"  [{issue['severity']}] {issue['message']}")
