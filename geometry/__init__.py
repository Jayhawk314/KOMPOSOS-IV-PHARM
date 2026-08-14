# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""
KOMPOSOS-III Geometry Layer

Implements geometric analysis of knowledge graphs using:
- Ollivier-Ricci curvature for local geometry detection
- Discrete Ricci flow for structure revelation
- Thurston-style geometric decomposition

Key insight: Different regions of a knowledge graph have different
natural geometries (hyperbolic for hierarchies, spherical for clusters,
euclidean for chains). This layer reveals that structure.
"""

from .ricci import (
    OllivierRicciCurvature,
    CurvatureResult,
    GeometryType,
    compute_graph_curvature,
)

from .flow import (
    DiscreteRicciFlow,
    DecompositionResult,
    GeometricRegion,
    FlowStep,
    run_ricci_flow,
)

# Optional heavy dependencies degrade; they must never take the package down.
#
# These blocks originally caught ImportError only. That is not enough: a broken
# optional dependency can fail with anything. transformers' lazy module loader
# raises RuntimeError (e.g. "module 'numpy' has no attribute 'dtypes'" when
# numpy and transformers disagree on version), which escaped the guard and made
# `import geometry` fail outright - taking alphafold_coherence, which needs only
# numpy, down with it. Catch broadly and record the reason instead of hiding it.
_UNAVAILABLE: dict[str, str] = {}


def unavailable_optional_modules() -> dict[str, str]:
    """Why each optional geometry subsystem is not loaded, for diagnostics."""
    return dict(_UNAVAILABLE)


# Protein structure prediction (if available)
try:
    from .contact_prediction import (
        CompositionalContactPredictor,
        ContactMap,
        MotifPattern,
        PredictionResult
    )
    from .structure_reconstruction import (
        StructureReconstructor,
        Structure3D,
        DistanceConstraint,
        reconstruct_from_contact_map
    )
    from .protein_structure_pipeline import (
        KOMPOSOSStructurePipeline,
        StructurePredictionResult,
        predict_protein_structure
    )
    STRUCTURE_PREDICTION_AVAILABLE = True
except Exception as error:  # noqa: BLE001 - optional subsystem must degrade
    STRUCTURE_PREDICTION_AVAILABLE = False
    _UNAVAILABLE["structure_prediction"] = f"{type(error).__name__}: {error}"

# Spectral analysis (if available)
try:
    from .spectral import SpectralGraphAnalyzer, analyze_spectrum
    SPECTRAL_AVAILABLE = True
except Exception as error:  # noqa: BLE001 - optional subsystem must degrade
    SPECTRAL_AVAILABLE = False
    _UNAVAILABLE["spectral"] = f"{type(error).__name__}: {error}"

__all__ = [
    # Curvature
    "OllivierRicciCurvature",
    "CurvatureResult",
    "GeometryType",
    "compute_graph_curvature",
    # Ricci Flow
    "DiscreteRicciFlow",
    "DecompositionResult",
    "GeometricRegion",
    "FlowStep",
    "run_ricci_flow",
]

# Add structure prediction if available
if STRUCTURE_PREDICTION_AVAILABLE:
    __all__.extend([
        "CompositionalContactPredictor",
        "ContactMap",
        "MotifPattern",
        "PredictionResult",
        "StructureReconstructor",
        "Structure3D",
        "DistanceConstraint",
        "reconstruct_from_contact_map",
        "KOMPOSOSStructurePipeline",
        "StructurePredictionResult",
        "predict_protein_structure",
    ])

# Add spectral if available
if SPECTRAL_AVAILABLE:
    __all__.extend(["SpectralGraphAnalyzer", "analyze_spectrum"])

# ESMFold + ZFC verification pipeline (if available)
try:
    from .zfc_structure_verifier import StructureZFCBridge, StructureVerificationResult
    from .esmfold_zfc_pipeline import ESMFoldZFCPipeline, ESMFoldZFCResult
    ESMFOLD_ZFC_AVAILABLE = True
    __all__.extend([
        "StructureZFCBridge", "StructureVerificationResult",
        "ESMFoldZFCPipeline", "ESMFoldZFCResult",
    ])
except Exception as error:  # noqa: BLE001 - optional subsystem must degrade
    ESMFOLD_ZFC_AVAILABLE = False
    _UNAVAILABLE["esmfold_zfc"] = f"{type(error).__name__}: {error}"

# Categorical fragment assembly (if available)
try:
    from .fragment_category import (
        FragmentAssembler,
        FragmentCategory,
        FragmentAssemblyResult,
        PositionedFragment,
        SpatialMorphism,
    )
    FRAGMENT_ASSEMBLY_AVAILABLE = True
    __all__.extend([
        "FragmentAssembler", "FragmentCategory", "FragmentAssemblyResult",
        "PositionedFragment", "SpatialMorphism",
    ])
except Exception as error:  # noqa: BLE001 - optional subsystem must degrade
    FRAGMENT_ASSEMBLY_AVAILABLE = False
    _UNAVAILABLE["fragment_assembly"] = f"{type(error).__name__}: {error}"
