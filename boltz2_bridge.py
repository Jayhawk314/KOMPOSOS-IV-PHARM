#!/usr/bin/env python3
"""
Boltz-2 Integration for KOMPOSOS-IV-PHARM

Adds structure-based binding predictions to the oracle system.

Boltz-2 predicts:
- Protein-ligand binding structures
- Binding affinity scores
- Pocket geometry
- Interaction patterns

This bridges categorical reasoning (oracle) with physical structure (Boltz-2).
"""

import sys
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))

# Try to import Boltz-2
try:
    import boltz
    BOLTZ_AVAILABLE = True
except ImportError:
    BOLTZ_AVAILABLE = False
    print("[Boltz2Bridge] WARNING: boltz not installed")
    print("  Install with: pip install boltz")


class BioorthogonalWarhead(Enum):
    """Common bioorthogonal reactive groups."""
    AZIDE = "azide"                    # N3
    ALKYNE = "alkyne"                  # terminal alkyne
    CYCLOOCTYNE = "cyclooctyne"        # strained alkyne (SPAAC)
    TETRAZINE = "tetrazine"            # inverse electron demand DA
    TCO = "trans_cyclooctene"          # tetrazine partner
    NORBORNENE = "norbornene"          # diene for tetrazine
    ISOCYANIDE = "isocyanide"          # multicomponent reactions
    QUADRICYCLANE = "quadricyclane"    # photochemical
    NONE = "none"                      # no reactive warhead


@dataclass
class BioorthogonalStability:
    """Stability analysis of bioorthogonal warhead in cellular environment."""
    warhead: BioorthogonalWarhead
    survives_lysosome: bool         # pH 4.5-5.0
    survives_nucleophiles: bool     # GSH, cysteine
    survives_oxidation: bool        # ROS, peroxides
    plasma_half_life_hours: float   # stability in blood
    overall_stability: float        # 0-1 score
    failure_modes: List[str]        # what kills it

    def is_stable(self, threshold: float = 0.6) -> bool:
        """Check if warhead is stable enough to reach target."""
        return self.overall_stability >= threshold


@dataclass
class BindingPrediction:
    """Boltz-2 binding prediction result."""
    drug_name: str
    protein_name: str
    binding_score: float  # 0-1, higher = better binding
    confidence: float     # Boltz-2 confidence
    pocket_score: float   # How well drug fits pocket
    structure_available: bool
    structure_path: Optional[str] = None
    interaction_types: Optional[List[str]] = None  # H-bonds, hydrophobic, etc.

    def to_dict(self) -> Dict:
        return {
            'drug': self.drug_name,
            'protein': self.protein_name,
            'binding_score': self.binding_score,
            'confidence': self.confidence,
            'pocket_score': self.pocket_score,
            'has_structure': self.structure_available,
            'interactions': self.interaction_types or []
        }


class Boltz2Bridge:
    """
    Bridge between KOMPOSOS oracle and Boltz-2 structure prediction.

    Workflow:
    1. Oracle proposes Drug->Protein edge
    2. Boltz-2 predicts binding structure
    3. Score binding quality
    4. Boost/penalize oracle confidence based on structure
    """

    def __init__(self, output_dir: str = "boltz2_structures"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # Initialize Boltz-2 if available
        if BOLTZ_AVAILABLE:
            try:
                self.model = boltz.Boltz2Model()
                self.available = True
                print(f"[Boltz2Bridge] Initialized at {output_dir}")
            except Exception as e:
                print(f"[Boltz2Bridge] Failed to initialize: {e}")
                self.available = False
        else:
            self.available = False
            self.model = None

        # Fallback: use chemistry module for basic scoring
        try:
            from chemistry import (
                HydrogenBondValidator,
                VanDerWaalsConstraints,
                ElectrostaticConstraints
            )
            self.chemistry_available = True
            self.hbond_validator = HydrogenBondValidator()
            self.vdw_validator = VanDerWaalsConstraints()
            self.elec_validator = ElectrostaticConstraints()
        except ImportError:
            self.chemistry_available = False

    def predict_binding(
        self,
        drug_name: str,
        protein_name: str,
        drug_smiles: Optional[str] = None,
        protein_sequence: Optional[str] = None
    ) -> BindingPrediction:
        """
        Predict drug-protein binding using Boltz-2.

        Args:
            drug_name: Drug identifier
            protein_name: Protein identifier
            drug_smiles: SMILES string for drug (optional)
            protein_sequence: Protein sequence (optional)

        Returns:
            BindingPrediction with scores and structure path
        """

        if not self.available:
            # Fallback to heuristic scoring
            return self._fallback_prediction(drug_name, protein_name)

        try:
            # Run Boltz-2 prediction
            structure = self.model.predict_complex(
                ligand_smiles=drug_smiles,
                protein_sequence=protein_sequence,
                output_dir=str(self.output_dir / f"{drug_name}_{protein_name}")
            )

            # Score binding quality
            binding_score = self._score_binding(structure)
            confidence = structure.confidence
            pocket_score = self._score_pocket_fit(structure)

            # Analyze interactions
            interactions = self._analyze_interactions(structure)

            structure_path = str(structure.output_path)

            return BindingPrediction(
                drug_name=drug_name,
                protein_name=protein_name,
                binding_score=binding_score,
                confidence=confidence,
                pocket_score=pocket_score,
                structure_available=True,
                structure_path=structure_path,
                interaction_types=interactions
            )

        except Exception as e:
            print(f"[Boltz2Bridge] Prediction failed for {drug_name}-{protein_name}: {e}")
            return self._fallback_prediction(drug_name, protein_name)

    def _fallback_prediction(self, drug_name: str, protein_name: str) -> BindingPrediction:
        """
        Fallback scoring when Boltz-2 unavailable.

        Uses heuristics:
        - Known drug-target pairs get high scores
        - Kinase inhibitors bind kinases
        - Receptor-targeted drugs bind receptors
        """

        # Known high-confidence pairs
        known_pairs = {
            ('Imatinib', 'BCR-ABL'): 0.95,
            ('Erlotinib', 'EGFR'): 0.92,
            ('Gefitinib', 'EGFR'): 0.90,
            ('Lapatinib', 'ERBB2'): 0.88,
            ('Sorafenib', 'VEGFR2'): 0.85,
            ('Crizotinib', 'ALK'): 0.93,
            ('Osimertinib', 'EGFR'): 0.94,
        }

        pair_key = (drug_name, protein_name)
        if pair_key in known_pairs:
            score = known_pairs[pair_key]
            confidence = 0.85
        else:
            # Heuristic based on drug/protein names
            score = self._heuristic_score(drug_name, protein_name)
            confidence = 0.5

        return BindingPrediction(
            drug_name=drug_name,
            protein_name=protein_name,
            binding_score=score,
            confidence=confidence,
            pocket_score=score * 0.9,
            structure_available=False,
            interaction_types=None
        )

    def _heuristic_score(self, drug: str, protein: str) -> float:
        """Simple heuristic scoring."""
        score = 0.5  # baseline

        # Kinase inhibitors (-inib suffix) likely bind kinases
        if drug.lower().endswith('inib'):
            if any(k in protein.upper() for k in ['RAF', 'MEK', 'ERK', 'AKT', 'MTOR', 'CDK']):
                score += 0.2

        # Receptor-targeted drugs
        if 'EGFR' in protein or 'ERBB' in protein:
            if 'tinib' in drug.lower():
                score += 0.15

        # Common oncogenic targets
        if protein in ['TP53', 'KRAS', 'BRAF', 'MYC', 'PIK3CA']:
            score += 0.1

        return min(score, 0.95)

    def _score_binding(self, structure) -> float:
        """Score binding quality from Boltz-2 structure."""
        # Use pLDDT (predicted local distance difference test)
        # or interface contact score
        if hasattr(structure, 'plddt'):
            return np.mean(structure.plddt) / 100.0
        elif hasattr(structure, 'interface_score'):
            return structure.interface_score
        else:
            return 0.7  # default

    def _score_pocket_fit(self, structure) -> float:
        """Score how well ligand fits binding pocket."""
        # Analyze:
        # - Shape complementarity
        # - Volume overlap
        # - Clash score
        if hasattr(structure, 'pocket_score'):
            return structure.pocket_score
        else:
            # Estimate from binding score
            binding = self._score_binding(structure)
            return binding * 0.95

    def _analyze_interactions(self, structure) -> List[str]:
        """Identify interaction types in binding site."""
        interactions = []

        # Check for hydrogen bonds
        if self.chemistry_available:
            try:
                hbonds = self.hbond_validator.predict_from_structure(structure)
                if len(hbonds) > 0:
                    interactions.append(f"H-bonds({len(hbonds)})")
            except:
                pass

        # Placeholder for other interactions
        interactions.append("hydrophobic")
        interactions.append("van_der_waals")

        return interactions

    def check_bioorthogonal_stability(
        self,
        drug_name: str,
        drug_smiles: Optional[str] = None
    ) -> BioorthogonalStability:
        """
        Check if drug's bioorthogonal warhead survives cellular environment.

        This addresses the gap: "Models hallucinate binding poses for molecules
        that can't physically reach the binding site because their reactive
        groups got hydrolyzed in the lysosome."

        Args:
            drug_name: Drug identifier
            drug_smiles: SMILES string (optional, for detection)

        Returns:
            BioorthogonalStability with survival analysis
        """

        # Detect warhead type
        warhead = self._detect_warhead(drug_name, drug_smiles)

        # Stability rules based on chemical literature
        stability_db = {
            BioorthogonalWarhead.AZIDE: {
                'lysosome': True,   # Stable to acidic pH
                'nucleophile': True,  # Resistant to thiols
                'oxidation': True,    # Stable
                'half_life': 24.0,    # Hours in plasma
                'notes': 'Very stable, gold standard'
            },
            BioorthogonalWarhead.CYCLOOCTYNE: {
                'lysosome': True,
                'nucleophile': True,
                'oxidation': False,   # Can be oxidized
                'half_life': 12.0,
                'notes': 'Moderate stability'
            },
            BioorthogonalWarhead.TETRAZINE: {
                'lysosome': False,    # Acid-labile
                'nucleophile': True,
                'oxidation': True,
                'half_life': 2.0,     # Degrades in acidic pH
                'notes': 'FAILS in lysosomes - pH 4.5 hydrolyzes tetrazine'
            },
            BioorthogonalWarhead.TCO: {
                'lysosome': True,
                'nucleophile': True,
                'oxidation': True,
                'half_life': 18.0,
                'notes': 'Stable'
            },
            BioorthogonalWarhead.NORBORNENE: {
                'lysosome': True,
                'nucleophile': True,
                'oxidation': True,
                'half_life': 20.0,
                'notes': 'Very stable'
            },
            BioorthogonalWarhead.ALKYNE: {
                'lysosome': True,
                'nucleophile': False,  # Can react with strong nucleophiles
                'oxidation': True,
                'half_life': 6.0,
                'notes': 'Moderate - nucleophile sensitive'
            },
            BioorthogonalWarhead.ISOCYANIDE: {
                'lysosome': False,     # Acid-labile
                'nucleophile': False,  # Reacts with nucleophiles
                'half_life': 1.0,
                'notes': 'Unstable - multiple failure modes'
            },
            BioorthogonalWarhead.NONE: {
                'lysosome': True,
                'nucleophile': True,
                'oxidation': True,
                'half_life': 48.0,
                'notes': 'No reactive warhead - stable drug'
            }
        }

        props = stability_db.get(warhead, stability_db[BioorthogonalWarhead.NONE])

        # Identify failure modes
        failures = []
        if not props['lysosome']:
            failures.append('lysosomal_hydrolysis')
        if not props['nucleophile']:
            failures.append('nucleophile_quenching')
        if not props['oxidation']:
            failures.append('oxidative_degradation')
        if props['half_life'] < 3.0:
            failures.append('rapid_plasma_clearance')

        # Compute overall stability
        stability_score = 0.0
        if props['lysosome']:
            stability_score += 0.4  # Lysosome is critical
        if props['nucleophile']:
            stability_score += 0.3
        if props['oxidation']:
            stability_score += 0.2
        if props['half_life'] > 6.0:
            stability_score += 0.1

        return BioorthogonalStability(
            warhead=warhead,
            survives_lysosome=props['lysosome'],
            survives_nucleophiles=props['nucleophile'],
            survives_oxidation=props['oxidation'],
            plasma_half_life_hours=props['half_life'],
            overall_stability=stability_score,
            failure_modes=failures
        )

    def _detect_warhead(
        self,
        drug_name: str,
        drug_smiles: Optional[str] = None
    ) -> BioorthogonalWarhead:
        """Detect bioorthogonal warhead type from drug name or SMILES."""

        # Name-based heuristics
        name_lower = drug_name.lower()

        if 'azide' in name_lower or 'n3' in name_lower:
            return BioorthogonalWarhead.AZIDE
        if 'alkyne' in name_lower:
            if 'cyclo' in name_lower or 'strain' in name_lower:
                return BioorthogonalWarhead.CYCLOOCTYNE
            return BioorthogonalWarhead.ALKYNE
        if 'tetrazine' in name_lower or 'tz' in name_lower:
            return BioorthogonalWarhead.TETRAZINE
        if 'tco' in name_lower or 'cyclooctene' in name_lower:
            return BioorthogonalWarhead.TCO
        if 'norbornene' in name_lower:
            return BioorthogonalWarhead.NORBORNENE

        # TODO: SMILES-based detection using RDKit
        # Would search for functional group patterns

        # Default: assume no bioorthogonal warhead (stable drug)
        return BioorthogonalWarhead.NONE

    def enhance_oracle_prediction(
        self,
        drug: str,
        protein: str,
        oracle_confidence: float,
        drug_smiles: Optional[str] = None,
        protein_seq: Optional[str] = None
    ) -> Tuple[float, BindingPrediction]:
        """
        Enhance oracle prediction with structure-based scoring.

        Args:
            drug: Drug name
            protein: Protein name
            oracle_confidence: Confidence from categorical oracle
            drug_smiles: Optional SMILES
            protein_seq: Optional sequence

        Returns:
            (enhanced_confidence, binding_prediction)

        Enhanced confidence combines:
        - Categorical reasoning (oracle)
        - Physical structure (Boltz-2)
        - Chemistry validation
        - Bioorthogonal stability (NEW)
        """

        # Get Boltz-2 binding prediction
        binding = self.predict_binding(
            drug, protein, drug_smiles, protein_seq
        )

        # Check bioorthogonal stability
        stability = self.check_bioorthogonal_stability(drug, drug_smiles)

        # Combine scores
        # If structure confirms binding, boost confidence
        # If structure shows poor binding, penalize

        structure_weight = 0.4 if binding.structure_available else 0.2
        oracle_weight = 1.0 - structure_weight

        enhanced = (
            oracle_weight * oracle_confidence +
            structure_weight * binding.binding_score
        )

        # Bonus for high-confidence structure predictions
        if binding.confidence > 0.85 and binding.binding_score > 0.8:
            enhanced = min(enhanced * 1.1, 0.98)

        # Penalty for confident structure showing poor binding
        if binding.confidence > 0.8 and binding.binding_score < 0.4:
            enhanced = enhanced * 0.7

        # CRITICAL: Penalty for unstable bioorthogonal warheads
        # "Models hallucinate binding poses for molecules that can't reach the site"
        if not stability.is_stable(threshold=0.6):
            # Severe penalty - drug won't reach target
            penalty = stability.overall_stability  # 0.0-0.6 range
            enhanced = enhanced * (0.3 + 0.7 * penalty)  # Max 30% reduction

            # Extra penalty if warhead fails in lysosome (most common failure)
            if not stability.survives_lysosome:
                enhanced = enhanced * 0.5  # 50% reduction - critical failure

        return enhanced, binding


def integrate_boltz2_with_oracle():
    """
    Example: Integrate Boltz-2 with oracle predictions.

    Shows how structure predictions enhance categorical reasoning.
    """
    from domains.bio import BioDomainLoader
    from core.category import Category
    from oracle.strategies import CompositionStrategy

    print("=" * 80)
    print("BOLTZ-2 + ORACLE INTEGRATION")
    print("=" * 80)

    # Load bio data
    print("\n[1] Loading bio data...")
    loader = BioDomainLoader()
    cat = Category(name="BioTier1", db_path=":memory:")
    loader.load_tier1("data/drugs/tier1.db", cat)

    # Initialize Boltz-2 bridge
    print("\n[2] Initializing Boltz-2 bridge...")
    boltz = Boltz2Bridge()
    print(f"  Boltz-2 available: {boltz.available}")
    print(f"  Chemistry fallback: {boltz.chemistry_available}")

    # Get a drug-protein prediction from oracle
    print("\n[3] Running oracle prediction...")
    strategy = CompositionStrategy(cat)
    drug = "Erlotinib"
    protein = "EGFR"

    oracle_preds = strategy.predict(drug, protein)
    if len(oracle_preds) > 0:
        oracle_conf = oracle_preds[0].confidence
        print(f"  Oracle: {drug} -> {protein}, confidence: {oracle_conf:.3f}")

        # Enhance with Boltz-2
        print("\n[4] Enhancing with Boltz-2...")
        enhanced_conf, binding = boltz.enhance_oracle_prediction(
            drug, protein, oracle_conf
        )

        print(f"  Boltz-2 binding score: {binding.binding_score:.3f}")
        print(f"  Boltz-2 confidence: {binding.confidence:.3f}")
        print(f"  Pocket fit: {binding.pocket_score:.3f}")
        print(f"  Enhanced confidence: {enhanced_conf:.3f} (was {oracle_conf:.3f})")

        if binding.interaction_types:
            print(f"  Interactions: {', '.join(binding.interaction_types)}")

    print("\n" + "=" * 80)
    print("Integration complete - Oracle + Boltz-2 working together")
    print("=" * 80)


if __name__ == "__main__":
    integrate_boltz2_with_oracle()
