# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""
Chemistry Module for KOMPOSOS-III
==================================

Physical chemistry constraints for protein structure validation and prediction.

This module bridges category theory with real physical chemistry by implementing:
- Hydrogen bonding constraints (geometry, distance, angles)
- Van der Waals forces (packing, clash detection)
- Electrostatic interactions (salt bridges, disulfide bonds)
- Hydrophobic effect (burial preferences, core formation)

These constraints ground the abstract categorical framework in real molecular physics,
ensuring predictions are not just mathematically sound but physically realistic.

Scientific Foundations:
-----------------------
- H-bond geometry: Donor-acceptor distance 2.5-3.5 Å, angles 120-180°
  (Hubbard & Haider 2010, Proteopedia; RSC Physical Chemistry 2025)
- vdW radii: Element-specific (C: 1.70Å, N: 1.55Å, O: 1.52Å, S: 1.80Å)
- Electrostatics: Salt bridge distance 2.5-4.5 Å, disulfide bonds 1.8-2.5 Å
- Hydrophobic effect: Kyte-Doolittle scale, burial propensities

References:
-----------
- Hydrogen bonding: https://pubs.rsc.org/en/content/articlelanding/2025/cp/d5cp00511f
- Statistical potentials: https://pmc.ncbi.nlm.nih.gov/articles/PMC2242414/
- Rotamer libraries: https://dunbrack.fccc.edu/bbdep2010/
"""

from chemistry.hydrogen_bonds import (
    HydrogenBondValidator,
    HBondMorphism,
    predict_hbonds_from_coords,
    validate_hbond_network
)

from chemistry.van_der_waals import (
    VanDerWaalsConstraints,
    check_clashes,
    optimal_packing_score
)

from chemistry.electrostatics import (
    ElectrostaticConstraints,
    predict_salt_bridges,
    predict_disulfide_bonds
)

from chemistry.hydrophobic import (
    HydrophobicConstraints,
    compute_burial_scores,
    validate_hydrophobic_core
)

from chemistry.statistical_potentials import (
    StatisticalPotentials,
    score_structure_with_potentials
)

from chemistry.ramachandran import (
    RamachandranValidator,
    RamachandranRegion
)

from chemistry.rotamers import (
    DunbrackRotamerLibrary,
    Rotamer
)

from chemistry.side_chain_packing import (
    SideChainPacker,
    FullAtomResidue
)

from chemistry.data_integration import (
    RealDataIntegrator,
    MSAInfo,
    PDBStatistics
)

from chemistry.energy_functions import (
    EnergyFunction,
    EnergyWeights,
    EnergyBreakdown
)

from chemistry.optimizer import (
    StructureOptimizer,
    OptimizationResult
)

from chemistry.pfam_domain_mapper import (
    PfamDomainMapper,
    PfamDomain,
    TemplateMatch
)

__all__ = [
    # Hydrogen bonding
    'HydrogenBondValidator',
    'HBondMorphism',
    'predict_hbonds_from_coords',
    'validate_hbond_network',

    # Van der Waals
    'VanDerWaalsConstraints',
    'check_clashes',
    'optimal_packing_score',

    # Electrostatics
    'ElectrostaticConstraints',
    'predict_salt_bridges',
    'predict_disulfide_bonds',

    # Hydrophobic effect
    'HydrophobicConstraints',
    'compute_burial_scores',
    'validate_hydrophobic_core',

    # Statistical potentials (Phase 2)
    'StatisticalPotentials',
    'score_structure_with_potentials',

    # Ramachandran validation (Phase 2)
    'RamachandranValidator',
    'RamachandranRegion',

    # Rotamer libraries (Phase 3)
    'DunbrackRotamerLibrary',
    'Rotamer',

    # Side chain packing (Phase 3)
    'SideChainPacker',
    'FullAtomResidue',

    # Real data integration (Phase 4)
    'RealDataIntegrator',
    'MSAInfo',
    'PDBStatistics',

    # Energy functions (Phase 5)
    'EnergyFunction',
    'EnergyWeights',
    'EnergyBreakdown',

    # Optimization (Phase 5) - FIXES CLASHES
    'StructureOptimizer',
    'OptimizationResult',

    # Pfam domain mapping (verification layer)
    'PfamDomainMapper',
    'PfamDomain',
    'TemplateMatch',
]

__version__ = '5.0.0'  # ALL PHASES COMPLETE ✅
__author__ = 'James Ray Hawkins'
