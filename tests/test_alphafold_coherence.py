import json
from pathlib import Path

import numpy as np
import pytest

from geometry.alphafold_coherence import (
    AuditConfig,
    Domain,
    RigidTransform,
    Standing,
    StructuralCoherenceAuditor,
    StructureModel,
    audit_manifest,
    fit_rigid_transform,
    global_sequence_mapping,
    load_pae,
)


def test_geometry_package_survives_broken_optional_dependencies():
    """A broken optional ML dependency must not take the package down.

    The optional blocks in geometry/__init__.py once caught ImportError only.
    transformers' lazy loader raises RuntimeError when it disagrees with numpy
    about versions, which escaped the guard and made `import geometry` fail -
    taking this module, which needs only numpy, with it.

    Only the legacy geometry tree has that __init__; a clean checkout ships
    alphafold_coherence.py alone and imports it as a namespace package, where
    there is no guard to test.
    """
    import geometry

    if not hasattr(geometry, "unavailable_optional_modules"):
        pytest.skip("namespace package: legacy geometry tree not present")

    assert isinstance(geometry.STRUCTURE_PREDICTION_AVAILABLE, bool)
    for subsystem, reason in geometry.unavailable_optional_modules().items():
        assert reason, f"{subsystem} degraded without recording why"


def test_structural_auditor_needs_no_machine_learning_stack():
    """The auditor is numpy geometry; it must not require transformers/torch."""
    import sys

    assert fit_rigid_transform is not None
    module = sys.modules["geometry.alphafold_coherence"]
    source = Path(module.__file__).read_text(encoding="utf-8")
    for heavy in ("import torch", "from torch", "import transformers", "from transformers"):
        assert heavy not in source, f"structural auditor must not {heavy}"


def _base_coordinates():
    first = np.array([
        [0.0, 0.0, 0.0],
        [1.1, 0.3, 0.2],
        [1.7, 1.2, -0.1],
        [1.0, 2.1, 0.5],
        [-0.1, 1.8, 1.0],
        [-0.6, 0.7, 0.4],
    ])
    second = np.array([
        [7.0, 0.0, 0.0],
        [8.0, 0.4, 0.1],
        [8.5, 1.4, -0.3],
        [7.8, 2.3, 0.4],
        [6.7, 1.9, 1.1],
        [6.2, 0.8, 0.5],
    ])
    return np.vstack((first, second))


def _rotation_z(degrees):
    angle = np.deg2rad(degrees)
    return np.array([
        [np.cos(angle), -np.sin(angle), 0.0],
        [np.sin(angle), np.cos(angle), 0.0],
        [0.0, 0.0, 1.0],
    ])


def _model(model_id, coordinates, pae=True, kind="prediction"):
    size = len(coordinates)
    return StructureModel(
        model_id=model_id,
        sequence="ACDEFGHIKLMN"[:size],
        coordinates=np.asarray(coordinates),
        plddt=np.full(size, 92.0),
        pae=np.full((size, size), 2.0) if pae else None,
        kind=kind,
    )


def _config(**overrides):
    values = {
        "minimum_residues": 4,
        "minimum_domain_coverage": 0.8,
        "arrangement_rmsd_threshold": 2.0,
        "arrangement_rotation_threshold_deg": 15.0,
        "composition_rmsd_threshold": 0.5,
        "composition_rotation_threshold_deg": 3.0,
    }
    values.update(overrides)
    return AuditConfig(**values)


DOMAINS = (Domain("D1", 1, 6), Domain("D2", 7, 12))


def test_kabsch_and_transform_composition_recover_known_pose():
    coordinates = _base_coordinates()
    first = RigidTransform(_rotation_z(31), np.array([2.0, -3.0, 1.5]))
    second = RigidTransform(_rotation_z(-12), np.array([-1.0, 4.0, 0.2]))
    target = first.then(second).apply(coordinates)
    fitted, rmsd = fit_rigid_transform(coordinates, target)
    assert rmsd < 1e-10
    assert np.allclose(fitted.apply(coordinates), target)
    assert np.allclose(first.then(second).apply(coordinates), second.apply(first.apply(coordinates)))
    assert np.allclose(first.inverse().apply(first.apply(coordinates)), coordinates)


def test_globally_rigid_family_is_compositionally_consistent():
    base = _base_coordinates()
    transform_b = RigidTransform(_rotation_z(23), np.array([4.0, -2.0, 1.0]))
    transform_c = RigidTransform(_rotation_z(-37), np.array([-3.0, 5.0, -2.0]))
    models = (
        _model("A", base),
        _model("B", transform_b.apply(base)),
        _model("C", transform_c.apply(base)),
    )
    report = StructuralCoherenceAuditor(_config()).audit("rigid", models, DOMAINS)
    assert report.standing == Standing.CONSISTENT
    assert report.domain_arrangements
    assert report.composition_checks
    assert all(check.standing == Standing.CONSISTENT for check in report.domain_arrangements)
    assert all(check.standing == Standing.CONSISTENT for check in report.composition_checks)
    assert max(check.filler_rmsd for check in report.composition_checks) < 1e-10


def test_confident_relative_domain_rotation_is_flagged():
    base = _base_coordinates()
    changed = base.copy()
    hinge = np.array([6.5, 0.5, 0.0])
    changed[6:] = (changed[6:] - hinge) @ _rotation_z(60).T + hinge
    report = StructuralCoherenceAuditor(_config()).audit(
        "hinge-change", (_model("A", base), _model("B", changed)), DOMAINS
    )
    assert report.standing == Standing.INCONSISTENT
    check = report.domain_arrangements[0]
    assert check.standing == Standing.INCONSISTENT
    assert check.rotation_disagreement_deg > 50
    assert check.mobile_internal_rmsd < 1e-10
    assert "review threshold" in check.reasons[0]


def test_missing_pae_quarantines_an_otherwise_clean_prediction():
    base = _base_coordinates()
    moved = RigidTransform(_rotation_z(10), np.array([1.0, 2.0, 3.0])).apply(base)
    report = StructuralCoherenceAuditor(_config()).audit(
        "missing-pae", (_model("A", base), _model("B", moved, pae=False)), DOMAINS
    )
    assert report.standing == Standing.QUARANTINE
    assert report.domain_arrangements[0].standing == Standing.QUARANTINE
    assert any("has no PAE matrix" in reason for reason in report.domain_arrangements[0].reasons)


def test_experimental_structure_does_not_require_pae():
    base = _base_coordinates()
    moved = RigidTransform(_rotation_z(10), np.array([1.0, 2.0, 3.0])).apply(base)
    report = StructuralCoherenceAuditor(_config()).audit(
        "experiment",
        (_model("prediction", base), _model("experiment", moved, pae=False, kind="experimental")),
        DOMAINS,
    )
    assert report.standing == Standing.CONSISTENT


def test_high_cross_domain_pae_quarantines_domain_arrangement():
    base = _base_coordinates()
    uncertain = _model("B", base.copy())
    uncertain.pae[:6, 6:] = 25.0
    uncertain.pae[6:, :6] = 25.0
    report = StructuralCoherenceAuditor(_config()).audit(
        "uncertain", (_model("A", base), uncertain), DOMAINS
    )
    check = report.domain_arrangements[0]
    assert check.standing == Standing.QUARANTINE
    assert check.target_cross_domain_pae == 25.0


def test_sequence_mapping_handles_an_insertion():
    mapping = global_sequence_mapping("ACDEFG", "ACXDEFG")
    assert mapping == {0: 0, 1: 1, 2: 3, 3: 4, 4: 5, 5: 6}


def test_sequence_mapping_anchors_same_protein_construct_across_long_deletions():
    reference = "ACDEFGHIK" + "L" * 80 + "MNPQRSTVWY" + "A" * 70 + "CDEFGHIKLM"
    query = reference[:9] + reference[89:99] + reference[169:]
    mapping = global_sequence_mapping(reference, query)
    assert all(mapping[index] == index for index in range(9))
    assert all(mapping[index] == index - 80 for index in range(89, 99))
    assert all(mapping[index] == index - 150 for index in range(169, len(reference)))
    assert not any(index in mapping for index in range(9, 89))


def test_pae_loader_supports_current_and_legacy_shapes(tmp_path):
    matrix = [[0.0, 2.0], [3.0, 0.0]]
    current = tmp_path / "current.json"
    current.write_text(json.dumps({"predicted_aligned_error": matrix}), encoding="utf-8")
    wrapped = tmp_path / "wrapped.json"
    wrapped.write_text(json.dumps([{"predicted_aligned_error": matrix}]), encoding="utf-8")
    legacy = tmp_path / "legacy.json"
    legacy.write_text(
        json.dumps({"residue1": [1, 1, 2, 2], "residue2": [1, 2, 1, 2], "distance": [0, 2, 3, 0]}),
        encoding="utf-8",
    )
    assert np.array_equal(load_pae(current), matrix)
    assert np.array_equal(load_pae(wrapped), matrix)
    assert np.array_equal(load_pae(legacy), matrix)


def _write_pdb(path: Path, coordinates: np.ndarray):
    residue_names = ["ALA", "CYS", "ASP", "GLU", "PHE", "GLY", "HIS", "ILE", "LYS", "LEU", "MET", "ASN"]
    lines = []
    for serial, (residue, xyz) in enumerate(zip(residue_names, coordinates), start=1):
        lines.append(
            f"ATOM  {serial:5d}  CA  {residue:>3s} A{serial:4d}    "
            f"{xyz[0]:8.3f}{xyz[1]:8.3f}{xyz[2]:8.3f}  1.00 92.00           C"
        )
    path.write_text("\n".join(lines) + "\nEND\n", encoding="utf-8")


def test_manifest_runs_real_pdb_and_writes_json_serializable_report(tmp_path):
    base = _base_coordinates()
    moved = RigidTransform(_rotation_z(17), np.array([2.0, 1.0, -1.0])).apply(base)
    _write_pdb(tmp_path / "a.pdb", base)
    _write_pdb(tmp_path / "b.pdb", moved)
    pae = {"predicted_aligned_error": np.full((12, 12), 2.0).tolist()}
    (tmp_path / "a_pae.json").write_text(json.dumps(pae), encoding="utf-8")
    (tmp_path / "b_pae.json").write_text(json.dumps(pae), encoding="utf-8")
    manifest = {
        "schema_version": 1,
        "family_id": "example",
        "reference_model": "A",
        "models": [
            {"model_id": "A", "path": "a.pdb", "chain": "A", "pae_path": "a_pae.json"},
            {"model_id": "B", "path": "b.pdb", "chain": "A", "pae_path": "b_pae.json"},
        ],
        "domains": [
            {"domain_id": "D1", "start": 1, "end": 6},
            {"domain_id": "D2", "start": 7, "end": 12},
        ],
        "config": {
            "minimum_residues": 4,
            "minimum_domain_coverage": 0.8,
        },
    }
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    report = audit_manifest(manifest_path)
    rendered = report.to_dict()
    assert rendered["standing"] == "CONSISTENT"
    assert rendered["models"][0]["pae_available"] is True
    json.dumps(rendered)
