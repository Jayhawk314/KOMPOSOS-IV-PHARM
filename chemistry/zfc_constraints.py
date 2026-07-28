# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""
Chemistry -> ZFC Constraint Bridge

Converts physical-chemical validation results into ZFC logical constraints.
This lets the SeparationChecker detect when:
- A predicted drug-protein interaction violates physics (energy > threshold)
- H-bond patterns contradict the predicted binding mode
- Clash counts exceed physical limits

These constraints join the normal prediction constraints in the separation
checker, creating a unified logical view of both structural AND physical
evidence.

Stdlib-only in the ZFC direction (no numpy in ZFC formulas).
Chemistry-side uses numpy as always.
"""

from __future__ import annotations

from typing import List

# Graceful ZFC import
try:
    from zfc.logic import Formula, atom, neg, conj, implies, const
    from zfc.separation import Constraint
    ZFC_LOGIC_AVAILABLE = True
except ImportError:
    ZFC_LOGIC_AVAILABLE = False


class ChemZFCBridge:
    """
    Converts chemistry validation results to ZFC constraints.

    Usage:
        bridge = ChemZFCBridge()
        constraints = bridge.energy_constraints(
            drug="Celecoxib",
            protein="COX2",
            delta_energy=3.5,
            delta_hbonds=-4,
            clash_count=12,
        )
        # constraints is List[Constraint] ready for SeparationChecker
    """

    def __init__(self,
                 energy_threshold: float = 5.0,
                 clash_threshold: int = 20,
                 hbond_loss_threshold: int = 5):
        """
        Args:
            energy_threshold: delta_energy above which binding is "destabilized"
            clash_threshold: clash count above which structure is "unphysical"
            hbond_loss_threshold: H-bond loss above which binding is "disrupted"
        """
        self.energy_threshold = energy_threshold
        self.clash_threshold = clash_threshold
        self.hbond_loss_threshold = hbond_loss_threshold

    @property
    def is_available(self) -> bool:
        """Whether ZFC logic imports succeeded."""
        return ZFC_LOGIC_AVAILABLE

    def energy_constraints(
        self,
        drug: str,
        protein: str,
        delta_energy: float,
        delta_hbonds: int = 0,
        clash_count: int = 0,
    ) -> List:
        """
        Convert energy validation to logical constraints.

        If delta_energy > threshold:
            produces neg(atom("stable_binding", drug, protein))
        If delta_hbonds < -threshold:
            produces neg(atom("conserved_binding", drug, protein))
        If clash_count > threshold:
            produces neg(atom("physically_valid", drug, protein))

        Returns empty list if ZFC unavailable.
        """
        if not ZFC_LOGIC_AVAILABLE:
            return []

        constraints = []
        d = const(drug)
        p = const(protein)

        # Energy destabilization constraint
        if delta_energy > self.energy_threshold:
            formula = neg(atom("stable_binding", d, p))
            constraints.append(Constraint(
                formula=formula,
                source_prediction={"source": drug, "target": protein,
                        "relation": "stable_binding",
                        "confidence": 0.0, "strategy": "chemistry_energy"},
                confidence=min(1.0, delta_energy / (self.energy_threshold * 2)),
                strategy="chemistry_energy",
            ))
        elif delta_energy < -self.energy_threshold:
            # Stabilizing -- positive constraint
            formula = atom("stabilized_binding", d, p)
            constraints.append(Constraint(
                formula=formula,
                source_prediction={"source": drug, "target": protein,
                        "relation": "stabilized_binding",
                        "confidence": 1.0, "strategy": "chemistry_energy"},
                confidence=min(1.0, abs(delta_energy) / (self.energy_threshold * 2)),
                strategy="chemistry_energy",
            ))

        # H-bond disruption constraint
        if delta_hbonds < -self.hbond_loss_threshold:
            formula = neg(atom("conserved_binding", d, p))
            constraints.append(Constraint(
                formula=formula,
                source_prediction={"source": drug, "target": protein,
                        "relation": "conserved_binding",
                        "confidence": 0.0, "strategy": "chemistry_hbond"},
                confidence=min(1.0, abs(delta_hbonds) / (self.hbond_loss_threshold * 2)),
                strategy="chemistry_hbond",
            ))

        # Clash constraint
        if clash_count > self.clash_threshold:
            formula = neg(atom("physically_valid", d, p))
            constraints.append(Constraint(
                formula=formula,
                source_prediction={"source": drug, "target": protein,
                        "relation": "physically_valid",
                        "confidence": 0.0, "strategy": "chemistry_clash"},
                confidence=min(1.0, clash_count / (self.clash_threshold * 2)),
                strategy="chemistry_clash",
            ))

        return constraints

    def mutation_impact_constraints(
        self,
        protein: str,
        mutation: str,
        delta_energy: float,
        lost_contacts: int,
        gained_contacts: int,
        stability: str,
    ) -> List:
        """
        Convert mutation impact analysis to ZFC constraints.

        Encodes:
        - stability assessment (STABILIZING/DESTABILIZING/NEUTRAL)
        - contact disruption severity
        - gain-of-function signals
        """
        if not ZFC_LOGIC_AVAILABLE:
            return []

        constraints = []
        p = const(protein)
        m = const(mutation)

        # Stability constraint
        if "DESTABILIZING" in stability.upper():
            formula = atom("destabilizing", p, m)
            constraints.append(Constraint(
                formula=formula,
                source_prediction={"source": protein, "target": mutation,
                        "relation": "destabilizing",
                        "confidence": 0.9, "strategy": "chemistry_stability"},
                confidence=min(1.0, abs(delta_energy) / 10.0),
                strategy="chemistry_stability",
            ))
        elif "STABILIZING" in stability.upper():
            formula = atom("stabilizing", p, m)
            constraints.append(Constraint(
                formula=formula,
                source_prediction={"source": protein, "target": mutation,
                        "relation": "stabilizing",
                        "confidence": 0.9, "strategy": "chemistry_stability"},
                confidence=min(1.0, abs(delta_energy) / 10.0),
                strategy="chemistry_stability",
            ))

        # Contact disruption
        if lost_contacts > 5:
            formula = atom("contact_disruption", p, m)
            constraints.append(Constraint(
                formula=formula,
                source_prediction={"source": protein, "target": mutation,
                        "relation": "contact_disruption",
                        "confidence": 0.8, "strategy": "chemistry_contacts"},
                confidence=min(1.0, lost_contacts / 20.0),
                strategy="chemistry_contacts",
            ))

        # Gain-of-function signal
        if gained_contacts > 3:
            formula = atom("gain_of_function", p, m)
            constraints.append(Constraint(
                formula=formula,
                source_prediction={"source": protein, "target": mutation,
                        "relation": "gain_of_function",
                        "confidence": 0.7, "strategy": "chemistry_contacts"},
                confidence=min(1.0, gained_contacts / 10.0),
                strategy="chemistry_contacts",
            ))

        return constraints

    def hbond_network_constraints(
        self,
        protein: str,
        wt_hbonds: int,
        mut_hbonds: int,
        disrupted_fraction: float,
    ) -> List:
        """
        Convert H-bond network changes to constraints.

        Args:
            protein: protein name
            wt_hbonds: wild-type H-bond count
            mut_hbonds: mutant H-bond count
            disrupted_fraction: fraction of WT H-bonds lost (0-1)
        """
        if not ZFC_LOGIC_AVAILABLE:
            return []

        constraints = []
        p = const(protein)

        # Major H-bond network disruption
        if disrupted_fraction > 0.3:
            formula = atom("hbond_network_disrupted", p, const("mutation"))
            constraints.append(Constraint(
                formula=formula,
                source_prediction={"source": protein, "target": "mutation",
                        "relation": "hbond_network_disrupted",
                        "confidence": disrupted_fraction,
                        "strategy": "chemistry_hbond_network"},
                confidence=disrupted_fraction,
                strategy="chemistry_hbond_network",
            ))

        # H-bond network preserved
        if disrupted_fraction < 0.1 and wt_hbonds > 0:
            formula = atom("hbond_network_conserved", p, const("mutation"))
            constraints.append(Constraint(
                formula=formula,
                source_prediction={"source": protein, "target": "mutation",
                        "relation": "hbond_network_conserved",
                        "confidence": 1.0 - disrupted_fraction,
                        "strategy": "chemistry_hbond_network"},
                confidence=1.0 - disrupted_fraction,
                strategy="chemistry_hbond_network",
            ))

        return constraints
