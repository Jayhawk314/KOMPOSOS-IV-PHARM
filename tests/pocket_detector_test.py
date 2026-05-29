"""Regression and stress tests for the grid pocket detector.

These run without network or PDB files: they build synthetic proteins with a
known cavity and assert the largest-connected-cavity detector finds it rather
than the dense core (the exact failure mode that the co-crystal benchmark
exposed). They also check determinism and graceful handling of degenerate input.

A separate, skippable test cross-checks the committed benchmark report so the
'grid beats centroid' gate cannot silently regress.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = PROJECT_ROOT / "scripts"
for path in (PROJECT_ROOT, SCRIPT_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from design_drug import PDBAtom, define_pocket, detect_grid_pocket_center  # noqa: E402


def _atom(coord) -> PDBAtom:
    return PDBAtom(
        serial=1,
        name="CA",
        residue_name="ALA",
        chain_id="A",
        residue_id="1",
        record_type="ATOM",
        element="C",
        coord=np.asarray(coord, dtype=float),
        partial_charge=0.0,
    )


def _solid_ball_with_pocket(
    ball_radius: float = 14.0,
    lattice: float = 2.0,
    pocket_center=(9.0, 0.0, 0.0),
    pocket_radius: float = 6.0,
):
    """Dense ball of atoms with a spherical void carved near the surface.

    The geometric center (origin) is solidly packed (no void), so the only
    detectable cavity is the carved pocket. A correct detector must return a
    point near pocket_center, far from the centroid.
    """
    pocket_center = np.asarray(pocket_center, dtype=float)
    axis = np.arange(-ball_radius, ball_radius + lattice, lattice)
    atoms = []
    for x in axis:
        for y in axis:
            for z in axis:
                point = np.array([x, y, z], dtype=float)
                if np.linalg.norm(point) > ball_radius:
                    continue
                if np.linalg.norm(point - pocket_center) <= pocket_radius:
                    continue  # carve the pocket
                atoms.append(_atom(point))
    return atoms, pocket_center


def test_finds_carved_pocket_not_core():
    atoms, pocket_center = _solid_ball_with_pocket()
    center, meta = detect_grid_pocket_center(atoms, radius=10.0)
    err_to_pocket = float(np.linalg.norm(center - pocket_center))
    err_to_origin = float(np.linalg.norm(center - np.zeros(3)))
    assert meta["largest_cavity_points"] > 0, meta
    assert err_to_pocket <= 4.0, f"detector {center} far from pocket {pocket_center}"
    # And it must NOT collapse onto the densely packed geometric center.
    assert err_to_origin > err_to_pocket


def test_detector_is_deterministic():
    atoms, _ = _solid_ball_with_pocket()
    first, _ = detect_grid_pocket_center(atoms, radius=10.0)
    second, _ = detect_grid_pocket_center(atoms, radius=10.0)
    assert np.allclose(first, second)


def test_degenerate_input_returns_finite_centroid():
    # Too few atoms to host any cavity: must fall back, not crash or NaN.
    atoms = [_atom([0, 0, 0]), _atom([3, 0, 0]), _atom([0, 3, 0]), _atom([0, 0, 3])]
    center, meta = detect_grid_pocket_center(atoms, radius=10.0)
    assert center.shape == (3,)
    assert np.all(np.isfinite(center))
    assert meta["largest_cavity_points"] == 0


def test_define_pocket_grid_mode_runs_on_synthetic():
    atoms, pocket_center = _solid_ball_with_pocket()
    pocket = define_pocket(atoms, [], radius=10.0, pocket_mode="grid")
    assert pocket.atoms, "pocket should contain protein atoms"
    assert float(np.linalg.norm(pocket.center - pocket_center)) <= 4.0


def test_committed_benchmark_grid_beats_centroid():
    """Lock the gate: the committed report must show grid beating centroid."""
    for name in ("pocket_recovery_benchmark.json", "pocket_recovery_holdout.json"):
        report_path = PROJECT_ROOT / "reports" / name
        if not report_path.exists():
            pytest.skip(f"{name} not present")
        report = json.loads(report_path.read_text(encoding="utf-8"))
        per_mode = report["aggregate"]["per_mode"]
        grid_err = per_mode["grid"]["median_centroid_error_A"]
        centroid_err = per_mode["centroid"]["median_centroid_error_A"]
        grid_recall = per_mode["grid"]["mean_contact_recall"]
        centroid_recall = per_mode["centroid"]["mean_contact_recall"]
        assert grid_err < centroid_err, f"{name}: grid {grid_err} !< centroid {centroid_err}"
        assert grid_recall > centroid_recall, f"{name}: grid recall not above centroid"
