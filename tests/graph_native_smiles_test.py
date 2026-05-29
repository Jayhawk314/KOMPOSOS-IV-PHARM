"""Tests for graph-native RDKit SMILES construction from assembled fragments.

Builds minimal assemblies directly from the fragment library (no PDB needed) and
checks that the assembled atom/bond graph becomes a valid RDKit molecule with
real descriptors. Includes a regression guard for the 5-membered-ring (pyrrole-
type NH) kekulization bug that previously made most aromatic candidates invalid.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = PROJECT_ROOT / "scripts"
for path in (PROJECT_ROOT, SCRIPT_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

pytest.importorskip("rdkit")

from design_drug import (  # noqa: E402
    CrossFragmentBond,
    MolecularAssembly,
    PlacedFragment,
    build_fragment_library,
    graph_native_smiles,
)

LIBRARY = build_fragment_library(use_rdkit_conformers=False)


def _placed(name: str, placed_id: int = 0) -> PlacedFragment:
    return PlacedFragment(
        placed_id=placed_id,
        fragment=LIBRARY[name],
        rotation=np.eye(3),
        translation=np.zeros(3),
    )


def _assembly(placed, cross_bonds=None) -> MolecularAssembly:
    return MolecularAssembly(
        placed_fragments=list(placed),
        cross_bonds=list(cross_bonds or []),
        open_connections=[],
        trace=[],
    )


def test_benzene_seed_is_valid_aromatic():
    smiles, valid, props = graph_native_smiles(_assembly([_placed("benzene")]))
    assert valid
    assert smiles == "c1ccccc1"
    assert props["rings"] == 1
    assert props["heavy_atoms"] == 6
    assert 77.0 <= props["molecular_weight"] <= 79.0


def test_pyrazole_nh_kekulizes():
    # Regression guard: 5-membered aromatic ring with a pyrrole-type NH used to
    # fail kekulization, dropping graph-native validity to ~10%.
    smiles, valid, props = graph_native_smiles(_assembly([_placed("pyrazole")]))
    assert valid, "pyrazole NH ring must kekulize"
    assert "n" in smiles and "[nH]" in smiles  # stays aromatic, one NH
    assert props["rings"] == 1


def test_two_fragment_cross_bond():
    benzene = _placed("benzene", placed_id=0)
    methyl = _placed("methyl", placed_id=1)
    cross = CrossFragmentBond(
        source_fragment_id=0,
        source_atom_index=0,
        target_fragment_id=1,
        target_atom_index=0,
        order=1.0,
    )
    smiles, valid, props = graph_native_smiles(_assembly([benzene, methyl], [cross]))
    assert valid
    assert props["heavy_atoms"] == 7  # toluene
    assert smiles == "Cc1ccccc1"


def test_empty_assembly_is_graceful():
    smiles, valid, props = graph_native_smiles(_assembly([]))
    assert smiles == ""
    assert valid is False
    assert props == {}
