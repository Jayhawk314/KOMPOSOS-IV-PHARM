import json

import numpy as np

from geometry.alphafold_coherence import (
    AuditConfig,
    Domain,
    RigidTransform,
    Standing,
    StructureModel,
)
from oracle.structural_coherence import (
    StructuralCheckKind,
    StructuralCoherenceOracle,
)


BASE = np.array([
    [0.0, 0.0, 0.0], [1.1, 0.3, 0.2], [1.7, 1.2, -0.1],
    [1.0, 2.1, 0.5], [-0.1, 1.8, 1.0], [-0.6, 0.7, 0.4],
    [7.0, 0.0, 0.0], [8.0, 0.4, 0.1], [8.5, 1.4, -0.3],
    [7.8, 2.3, 0.4], [6.7, 1.9, 1.1], [6.2, 0.8, 0.5],
])
DOMAINS = (Domain("D1", 1, 6), Domain("D2", 7, 12))


def _rotation_z(degrees):
    angle = np.deg2rad(degrees)
    return np.array([
        [np.cos(angle), -np.sin(angle), 0.0],
        [np.sin(angle), np.cos(angle), 0.0],
        [0.0, 0.0, 1.0],
    ])


def _model(model_id, coordinates, pae=True, source_path=None):
    return StructureModel(
        model_id=model_id,
        sequence="ACDEFGHIKLMN",
        coordinates=coordinates,
        plddt=np.full(12, 92.0),
        pae=np.full((12, 12), 2.0) if pae else None,
        source_path=source_path,
    )


def _oracle():
    return StructuralCoherenceOracle(AuditConfig(
        minimum_residues=4,
        minimum_domain_coverage=0.8,
        arrangement_rmsd_threshold=2.0,
        arrangement_rotation_threshold_deg=15.0,
        composition_rmsd_threshold=0.5,
        composition_rotation_threshold_deg=3.0,
    ))


def test_oracle_ranks_assessable_domain_conflict_with_receipts():
    changed = BASE.copy()
    hinge = np.array([6.5, 0.5, 0.0])
    changed[6:] = (changed[6:] - hinge) @ _rotation_z(60).T + hinge
    result = _oracle().audit_family(
        "hinge-change",
        (_model("A", BASE, source_path="a.cif"), _model("B", changed, source_path="b.cif")),
        DOMAINS,
    )
    assert result.standing == Standing.INCONSISTENT
    assert result.counts == {"CONSISTENT": 0, "INCONSISTENT": 1, "QUARANTINE": 0}
    assert result.receipts == {"A": "a.cif", "B": "b.cif"}
    finding = result.ranked_findings[0]
    assert finding.kind == StructuralCheckKind.DOMAIN_ARRANGEMENT
    assert finding.review_priority > 3.0
    assert "exceeds a configured review threshold" in finding.reasoning
    json.dumps(result.to_dict())


def test_oracle_preserves_quarantine_without_inventing_score():
    result = _oracle().audit_family(
        "missing-pae", (_model("A", BASE), _model("B", BASE, pae=False)), DOMAINS
    )
    assert result.standing == Standing.QUARANTINE
    assert result.counts["QUARANTINE"] == 1
    finding = result.ranked_findings[0]
    assert finding.standing == Standing.QUARANTINE
    assert finding.review_priority is None
    assert "has no PAE matrix" in finding.reasoning


def test_oracle_records_passing_horns_without_calling_them_findings():
    models = (
        _model("A", BASE),
        _model("B", RigidTransform(_rotation_z(20), np.array([2.0, 1.0, 0.0])).apply(BASE)),
        _model("C", RigidTransform(_rotation_z(-15), np.array([-1.0, 3.0, 2.0])).apply(BASE)),
    )
    result = _oracle().audit_family("rigid", models, DOMAINS)
    horn_checks = [
        check for check in result.checks
        if check.kind == StructuralCheckKind.COMPOSITION_HORN
    ]
    assert result.standing == Standing.CONSISTENT
    assert len(horn_checks) == 2
    assert all(check.standing == Standing.CONSISTENT for check in horn_checks)
    assert result.ranked_findings == ()
