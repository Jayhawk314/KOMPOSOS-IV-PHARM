"""Tests for the Vina docking adapter.

The parsing/IO helpers are tested without any external tools. The full docking
pipeline is exercised only when the Vina binary, meeko, and a cached co-crystal
PDB are all present; otherwise that test skips, so CI stays green on machines
without docking installed.
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

import docking_adapter as da  # noqa: E402


def test_parse_vina_affinity_picks_mode_one():
    stdout = (
        "mode |   affinity | dist from best mode\n"
        "     | (kcal/mol) | rmsd l.b.| rmsd u.b.\n"
        "-----+------------+----------+----------\n"
        "   1       -7.065          0          0\n"
        "   2       -6.500      1.234      3.456\n"
    )
    assert da.parse_vina_affinity(stdout) == pytest.approx(-7.065)


def test_parse_vina_affinity_returns_none_without_table():
    assert da.parse_vina_affinity("no table here\njust text\n") is None


def _atom_line(serial: int, x: float, y: float, z: float) -> str:
    # Columns must place coords at [30:38], [38:46], [46:54].
    prefix = f"ATOM  {serial:>5}  C   LIG A{1:>4}    "
    assert len(prefix) == 30, len(prefix)
    return f"{prefix}{x:8.3f}{y:8.3f}{z:8.3f}  1.00  0.00"


def test_parse_first_pose_reads_first_model_only(tmp_path):
    pdbqt = tmp_path / "pose.pdbqt"
    pdbqt.write_text(
        "MODEL 1\n"
        + _atom_line(1, 0.0, 0.0, 0.0) + "\n"
        + _atom_line(2, 2.0, 0.0, 0.0) + "\n"
        + "ENDMDL\n"
        + "MODEL 2\n"
        + _atom_line(1, 100.0, 100.0, 100.0) + "\n"
        + "ENDMDL\n",
        encoding="utf-8",
    )
    pose = da.parse_first_pose(pdbqt)
    assert pose.shape == (2, 3)
    assert np.allclose(pose.mean(axis=0), [1.0, 0.0, 0.0])


def test_write_protein_only_pdb_filters(tmp_path):
    src = tmp_path / "src.pdb"
    src.write_text(
        "ATOM      1  N   ALA A   1      0.000   0.000   0.000\n"
        "HETATM    2  O   HOH A   2      5.000   5.000   5.000\n"
        "ATOM      3  C   ALA A   1      1.000   1.000   1.000\n",
        encoding="utf-8",
    )
    out = da.write_protein_only_pdb(src, tmp_path / "prot.pdb")
    lines = out.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2 and all(line.startswith("ATOM") for line in lines)


def test_find_vina_signature():
    # Returns a path string or None; must not raise.
    result = da.find_vina()
    assert result is None or isinstance(result, str)


def test_run_vina_unavailable_raises(monkeypatch, tmp_path):
    monkeypatch.setattr(da, "find_vina", lambda explicit=None: None)
    with pytest.raises(da.DockingUnavailable):
        da.run_vina(tmp_path / "r.pdbqt", tmp_path / "l.pdbqt", [0, 0, 0])


# --- live integration (skips unless the full toolchain is present) ---

ERLOTINIB = "C#Cc1cccc(Nc2ncnc3cc(OCCOC)c(OCCOC)cc23)c1"
COCRYSTAL = PROJECT_ROOT / "data" / "cache" / "pdb_templates" / "1M17.pdb"


@pytest.mark.skipif(da.find_vina() is None, reason="Vina binary not installed")
@pytest.mark.skipif(not COCRYSTAL.exists(), reason="1M17 co-crystal not cached")
def test_live_redock_1m17_lands_in_pocket():
    pytest.importorskip("meeko")
    from design_drug import define_pocket, parse_pdb_atoms

    protein, ligand = parse_pdb_atoms(COCRYSTAL, chain=None)
    center = define_pocket(protein, [], radius=10.0, pocket_mode="grid").center
    result = da.dock_smiles_into_pocket(COCRYSTAL, ERLOTINIB, center, exhaustiveness=8, seed=42)
    # Real binder must score favorably and land near the box center / true pocket.
    assert result["affinity_kcal_per_mol"] < -4.0
    pose = np.asarray(result["pose_centroid"], dtype=float)
    assert float(np.linalg.norm(pose - np.asarray(center))) < 8.0
