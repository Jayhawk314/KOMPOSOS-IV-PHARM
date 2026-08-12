# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""Uncertainty-aware compositional audits for AlphaFold structure families.

This module does not predict a fold and does not infer folding dynamics.  It
tests two observable consistency conditions across related structures:

1. Domain arrangement: after one domain is superposed, does another domain
   occupy the corresponding pose in the comparison structure?
2. Alignment composition: does a fitted A -> B -> C rigid transformation agree
   with the directly fitted A -> C transformation?

The second condition is the concrete ``horn filler`` used here.  The two known
faces are composed and compared with the observed third face.  Category theory
supplies the bookkeeping; Kabsch alignment supplies the measured morphisms.

Predicted structures require PAE for an automated verdict.  Missing or
high-uncertainty checks are quarantined rather than treated as supporting
evidence.  Structural inconsistency is a review flag, not proof that AlphaFold
is wrong: genuine alternative conformations can produce the same signal.
"""

from __future__ import annotations

import argparse
import difflib
import json
import math
import shlex
from dataclasses import dataclass, field
from enum import Enum
from itertools import combinations
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional, Sequence

import numpy as np


AA3_TO_1 = {
    "ALA": "A", "ARG": "R", "ASN": "N", "ASP": "D", "CYS": "C",
    "GLN": "Q", "GLU": "E", "GLY": "G", "HIS": "H", "ILE": "I",
    "LEU": "L", "LYS": "K", "MET": "M", "PHE": "F", "PRO": "P",
    "SER": "S", "THR": "T", "TRP": "W", "TYR": "Y", "VAL": "V",
    "MSE": "M", "SEC": "U", "PYL": "O",
}


class Standing(str, Enum):
    """Standing of a structural consistency check."""

    CONSISTENT = "CONSISTENT"
    INCONSISTENT = "INCONSISTENT"
    QUARANTINE = "QUARANTINE"


@dataclass(frozen=True)
class Domain:
    """One-based inclusive residue range on the reference model sequence."""

    domain_id: str
    start: int
    end: int

    def __post_init__(self) -> None:
        if not self.domain_id:
            raise ValueError("domain_id must not be empty")
        if self.start < 1 or self.end < self.start:
            raise ValueError(
                f"invalid domain {self.domain_id!r} range: {self.start}-{self.end}"
            )

    @property
    def length(self) -> int:
        return self.end - self.start + 1

    @property
    def reference_indices(self) -> range:
        return range(self.start - 1, self.end)


@dataclass
class StructureModel:
    """The C-alpha trace and uncertainty information for one structure."""

    model_id: str
    sequence: str
    coordinates: np.ndarray
    plddt: np.ndarray
    pae: Optional[np.ndarray] = None
    kind: str = "prediction"
    source_path: Optional[str] = None

    def __post_init__(self) -> None:
        self.coordinates = np.asarray(self.coordinates, dtype=float)
        self.plddt = np.asarray(self.plddt, dtype=float)
        if self.coordinates.shape != (len(self.sequence), 3):
            raise ValueError(
                f"{self.model_id}: coordinates must have shape "
                f"({len(self.sequence)}, 3), got {self.coordinates.shape}"
            )
        if self.plddt.shape != (len(self.sequence),):
            raise ValueError(
                f"{self.model_id}: pLDDT/B-factor count does not match sequence"
            )
        if not np.isfinite(self.coordinates).all():
            raise ValueError(f"{self.model_id}: coordinates contain non-finite values")
        if self.pae is not None:
            self.pae = np.asarray(self.pae, dtype=float)
            expected = (len(self.sequence), len(self.sequence))
            if self.pae.shape != expected:
                raise ValueError(
                    f"{self.model_id}: PAE must have shape {expected}, got {self.pae.shape}"
                )
        if self.kind not in {"prediction", "experimental"}:
            raise ValueError(
                f"{self.model_id}: kind must be 'prediction' or 'experimental'"
            )


@dataclass(frozen=True)
class RigidTransform:
    """Rigid transform using the convention y = R @ x + t."""

    rotation: np.ndarray
    translation: np.ndarray

    def __post_init__(self) -> None:
        rotation = np.asarray(self.rotation, dtype=float)
        translation = np.asarray(self.translation, dtype=float)
        if rotation.shape != (3, 3) or translation.shape != (3,):
            raise ValueError("rigid transform requires a 3x3 rotation and length-3 translation")
        object.__setattr__(self, "rotation", rotation)
        object.__setattr__(self, "translation", translation)

    @staticmethod
    def identity() -> "RigidTransform":
        return RigidTransform(np.eye(3), np.zeros(3))

    def apply(self, coordinates: np.ndarray) -> np.ndarray:
        coordinates = np.asarray(coordinates, dtype=float)
        return coordinates @ self.rotation.T + self.translation

    def inverse(self) -> "RigidTransform":
        inverse_rotation = self.rotation.T
        inverse_translation = -(inverse_rotation @ self.translation)
        return RigidTransform(inverse_rotation, inverse_translation)

    def then(self, following: "RigidTransform") -> "RigidTransform":
        """Compose this transform followed by ``following``."""

        return RigidTransform(
            following.rotation @ self.rotation,
            following.rotation @ self.translation + following.translation,
        )


@dataclass(frozen=True)
class FittedMorphism:
    source_model: str
    target_model: str
    domain_id: str
    transform: RigidTransform
    fitted_rmsd: float
    residues_used: int
    coverage: float


@dataclass(frozen=True)
class DomainArrangementCheck:
    source_model: str
    target_model: str
    anchor_domain: str
    mobile_domain: str
    standing: Standing
    arrangement_rmsd: Optional[float]
    mobile_internal_rmsd: Optional[float]
    excess_arrangement_rmsd: Optional[float]
    rotation_disagreement_deg: Optional[float]
    centroid_displacement: Optional[float]
    source_cross_domain_pae: Optional[float]
    target_cross_domain_pae: Optional[float]
    residues_used: int
    reasons: tuple[str, ...] = ()


@dataclass(frozen=True)
class CompositionCheck:
    source_model: str
    via_model: str
    target_model: str
    domain_id: str
    standing: Standing
    filler_rmsd: Optional[float]
    rotation_disagreement_deg: Optional[float]
    residues_used: int
    reasons: tuple[str, ...] = ()


@dataclass
class AuditConfig:
    """Thresholds are explicit hypotheses, not learned biological constants."""

    minimum_residues: int = 8
    minimum_domain_coverage: float = 0.60
    minimum_plddt: float = 50.0
    maximum_assessable_pae: float = 15.0
    arrangement_rmsd_threshold: float = 5.0
    arrangement_rotation_threshold_deg: float = 20.0
    composition_rmsd_threshold: float = 2.0
    composition_rotation_threshold_deg: float = 10.0
    require_pae_for_predictions: bool = True
    quarantine_on_any_missing_check: bool = True

    def __post_init__(self) -> None:
        if self.minimum_residues < 3:
            raise ValueError("minimum_residues must be at least 3")
        if not 0 < self.minimum_domain_coverage <= 1:
            raise ValueError("minimum_domain_coverage must be in (0, 1]")
        positive = (
            self.maximum_assessable_pae,
            self.arrangement_rmsd_threshold,
            self.arrangement_rotation_threshold_deg,
            self.composition_rmsd_threshold,
            self.composition_rotation_threshold_deg,
        )
        if any(value <= 0 for value in positive):
            raise ValueError("audit thresholds must be positive")


@dataclass
class AuditReport:
    family_id: str
    reference_model: str
    standing: Standing
    models: tuple[dict[str, Any], ...]
    domains: tuple[Domain, ...]
    domain_arrangements: tuple[DomainArrangementCheck, ...]
    composition_checks: tuple[CompositionCheck, ...]
    reasons: tuple[str, ...]
    config: AuditConfig
    limitations: tuple[str, ...] = (
        "Inconsistency is a review flag, not proof of model error; alternative conformations are possible.",
        "The auditor measures structural coherence and does not infer folding pathways or thermodynamic stability.",
        "Thresholds require external calibration against experimental structures before biological use.",
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "family_id": self.family_id,
            "reference_model": self.reference_model,
            "standing": self.standing.value,
            "models": list(self.models),
            "domains": [
                {"domain_id": d.domain_id, "start": d.start, "end": d.end}
                for d in self.domains
            ],
            "domain_arrangements": [_arrangement_dict(item) for item in self.domain_arrangements],
            "composition_checks": [_composition_dict(item) for item in self.composition_checks],
            "reasons": list(self.reasons),
            "config": {
                key: value for key, value in vars(self.config).items()
            },
            "limitations": list(self.limitations),
        }


def _optional_float(value: Optional[float]) -> Optional[float]:
    return None if value is None else float(value)


def _arrangement_dict(item: DomainArrangementCheck) -> dict[str, Any]:
    return {
        "source_model": item.source_model,
        "target_model": item.target_model,
        "anchor_domain": item.anchor_domain,
        "mobile_domain": item.mobile_domain,
        "standing": item.standing.value,
        "arrangement_rmsd": _optional_float(item.arrangement_rmsd),
        "mobile_internal_rmsd": _optional_float(item.mobile_internal_rmsd),
        "excess_arrangement_rmsd": _optional_float(item.excess_arrangement_rmsd),
        "rotation_disagreement_deg": _optional_float(item.rotation_disagreement_deg),
        "centroid_displacement": _optional_float(item.centroid_displacement),
        "source_cross_domain_pae": _optional_float(item.source_cross_domain_pae),
        "target_cross_domain_pae": _optional_float(item.target_cross_domain_pae),
        "residues_used": item.residues_used,
        "reasons": list(item.reasons),
    }


def _composition_dict(item: CompositionCheck) -> dict[str, Any]:
    return {
        "source_model": item.source_model,
        "via_model": item.via_model,
        "target_model": item.target_model,
        "domain_id": item.domain_id,
        "standing": item.standing.value,
        "filler_rmsd": _optional_float(item.filler_rmsd),
        "rotation_disagreement_deg": _optional_float(item.rotation_disagreement_deg),
        "residues_used": item.residues_used,
        "reasons": list(item.reasons),
    }


def fit_rigid_transform(source: np.ndarray, target: np.ndarray) -> tuple[RigidTransform, float]:
    """Fit the proper Kabsch rotation mapping ``source`` to ``target``."""

    source = np.asarray(source, dtype=float)
    target = np.asarray(target, dtype=float)
    if source.shape != target.shape or source.ndim != 2 or source.shape[1] != 3:
        raise ValueError("source and target must have matching shape (n, 3)")
    if len(source) < 3:
        raise ValueError("at least three coordinate pairs are required")
    source_center = source.mean(axis=0)
    target_center = target.mean(axis=0)
    source_centered = source - source_center
    target_centered = target - target_center
    if np.linalg.matrix_rank(source_centered) < 2:
        raise ValueError("coordinate pairs are collinear; rigid rotation is underdetermined")
    covariance = source_centered.T @ target_centered
    u, _singular_values, vt = np.linalg.svd(covariance)
    rotation = vt.T @ u.T
    if np.linalg.det(rotation) < 0:
        vt[-1, :] *= -1
        rotation = vt.T @ u.T
    translation = target_center - rotation @ source_center
    transform = RigidTransform(rotation, translation)
    residual = transform.apply(source) - target
    rmsd = float(np.sqrt(np.mean(np.sum(residual * residual, axis=1))))
    return transform, rmsd


def rotation_distance_degrees(first: np.ndarray, second: np.ndarray) -> float:
    """Geodesic angular distance between two proper rotations."""

    delta = np.asarray(first) @ np.asarray(second).T
    cosine = float(np.clip((np.trace(delta) - 1.0) / 2.0, -1.0, 1.0))
    return math.degrees(math.acos(cosine))


def global_sequence_mapping(reference: str, query: str) -> dict[int, int]:
    """Map zero-based reference positions to query positions by global alignment."""

    if reference == query:
        return {index: index for index in range(len(reference))}
    # Experimental constructs mapped to the same UniProt entry commonly omit
    # long internal regions. A score-only Needleman-Wunsch traceback can choose
    # a different, equally scoring placement across repeated sequence when the
    # gaps are long. Exact matching blocks anchor those constructs to their
    # unambiguous canonical positions and deliberately omit engineered mutation
    # sites rather than assigning them speculatively.
    matcher = difflib.SequenceMatcher(None, reference, query, autojunk=False)
    exact_mapping = {
        block.a + offset: block.b + offset
        for block in matcher.get_matching_blocks()
        for offset in range(block.size)
    }
    exact_fraction = len(exact_mapping) / max(1, min(len(reference), len(query)))
    if exact_fraction >= 0.50:
        return exact_mapping
    n, m = len(reference), len(query)
    gap = -2
    scores = np.empty((n + 1, m + 1), dtype=np.int32)
    trace = np.empty((n + 1, m + 1), dtype=np.uint8)
    scores[:, 0] = np.arange(n + 1, dtype=np.int32) * gap
    scores[0, :] = np.arange(m + 1, dtype=np.int32) * gap
    trace[1:, 0] = 1
    trace[0, 1:] = 2
    trace[0, 0] = 0
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            diagonal = scores[i - 1, j - 1] + (2 if reference[i - 1] == query[j - 1] else -1)
            up = scores[i - 1, j] + gap
            left = scores[i, j - 1] + gap
            if diagonal >= up and diagonal >= left:
                scores[i, j] = diagonal
                trace[i, j] = 0
            elif up >= left:
                scores[i, j] = up
                trace[i, j] = 1
            else:
                scores[i, j] = left
                trace[i, j] = 2
    mapping: dict[int, int] = {}
    i, j = n, m
    while i or j:
        direction = int(trace[i, j])
        if i and j and direction == 0:
            mapping[i - 1] = j - 1
            i -= 1
            j -= 1
        elif i and (j == 0 or direction == 1):
            i -= 1
        else:
            j -= 1
    return mapping


def load_pae(path: str | Path) -> np.ndarray:
    """Load AFDB or AlphaFold-Server PAE JSON without assuming one release format."""

    with Path(path).open(encoding="utf-8") as handle:
        payload = json.load(handle)
    if isinstance(payload, list) and len(payload) == 1 and isinstance(payload[0], dict):
        payload = payload[0]
    if isinstance(payload, dict):
        matrix = payload.get("predicted_aligned_error", payload.get("pae"))
        if matrix is not None:
            result = np.asarray(matrix, dtype=float)
            if result.ndim != 2 or result.shape[0] != result.shape[1]:
                raise ValueError(f"{path}: PAE matrix must be square")
            return result
        residue1 = payload.get("residue1")
        residue2 = payload.get("residue2")
        distance = payload.get("distance")
        if residue1 is not None and residue2 is not None and distance is not None:
            size = int(max(max(residue1), max(residue2)))
            result = np.full((size, size), np.nan, dtype=float)
            for first, second, value in zip(residue1, residue2, distance):
                result[int(first) - 1, int(second) - 1] = float(value)
            return result
    raise ValueError(f"{path}: unsupported PAE JSON format")


def load_structure(
    path: str | Path,
    model_id: Optional[str] = None,
    kind: str = "prediction",
    chain: Optional[str] = None,
    pae_path: Optional[str | Path] = None,
) -> StructureModel:
    """Load one chain from an AlphaFold PDB/mmCIF or an experimental structure."""

    path = Path(path)
    suffix = path.suffix.lower()
    if suffix in {".cif", ".mmcif"}:
        records = _parse_mmcif_ca(path)
    elif suffix in {".pdb", ".ent"}:
        records = _parse_pdb_ca(path)
    else:
        raise ValueError(f"{path}: expected .pdb, .ent, .cif, or .mmcif")
    chains = sorted({record[0] for record in records})
    if chain is None:
        if len(chains) != 1:
            raise ValueError(f"{path}: contains chains {chains}; specify one in the manifest")
        chain = chains[0]
    selected = [record for record in records if record[0] == chain]
    if not selected:
        raise ValueError(f"{path}: chain {chain!r} contains no C-alpha atoms")
    selected.sort(key=lambda item: (item[1], item[2]))
    sequence = "".join(AA3_TO_1.get(item[3], "X") for item in selected)
    coordinates = np.asarray([item[4] for item in selected], dtype=float)
    b_factors = np.asarray([item[5] for item in selected], dtype=float)
    plddt = b_factors if kind == "prediction" else np.full(len(selected), np.nan)
    pae = load_pae(pae_path) if pae_path else None
    return StructureModel(
        model_id=model_id or path.stem,
        sequence=sequence,
        coordinates=coordinates,
        plddt=plddt,
        pae=pae,
        kind=kind,
        source_path=str(path),
    )


def _parse_pdb_ca(path: Path) -> list[tuple[str, int, str, str, np.ndarray, float]]:
    records: dict[tuple[str, int, str], tuple[str, int, str, str, np.ndarray, float]] = {}
    with path.open(encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if not line.startswith(("ATOM  ", "HETATM")) or line[12:16].strip() != "CA":
                continue
            alternate = line[16:17].strip()
            if alternate not in {"", "A", ".", "?"}:
                continue
            chain = line[21:22].strip() or "_"
            try:
                residue_number = int(line[22:26])
                insertion = line[26:27].strip()
                residue = line[17:20].strip().upper()
                coordinate = np.array(
                    [float(line[30:38]), float(line[38:46]), float(line[46:54])]
                )
                b_factor = float(line[60:66]) if line[60:66].strip() else float("nan")
            except ValueError as error:
                raise ValueError(f"{path}: invalid ATOM record: {line.rstrip()}") from error
            key = (chain, residue_number, insertion)
            records.setdefault(
                key, (chain, residue_number, insertion, residue, coordinate, b_factor)
            )
    if not records:
        raise ValueError(f"{path}: no C-alpha records found")
    return list(records.values())


def _parse_mmcif_ca(path: Path) -> list[tuple[str, int, str, str, np.ndarray, float]]:
    """Parse the atom_site loop used by AlphaFold mmCIF files.

    This intentionally implements only atom-site tabular data; it is not a
    general mmCIF parser.  Quoted fields are supported through ``shlex``.
    """

    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    index = 0
    while index < len(lines):
        if lines[index].strip().lower() != "loop_":
            index += 1
            continue
        index += 1
        columns: list[str] = []
        while index < len(lines) and lines[index].lstrip().startswith("_"):
            columns.append(lines[index].strip())
            index += 1
        if not columns or not columns[0].startswith("_atom_site."):
            continue
        tokens: list[str] = []
        while index < len(lines):
            stripped = lines[index].strip()
            if stripped == "#":
                index += 1
                break
            if stripped.lower() == "loop_" or stripped.startswith("_"):
                break
            if stripped:
                lexer = shlex.shlex(stripped, posix=True)
                lexer.whitespace_split = True
                lexer.commenters = ""
                tokens.extend(list(lexer))
            index += 1
        if len(tokens) % len(columns):
            raise ValueError(f"{path}: malformed atom_site loop")
        field = {name: position for position, name in enumerate(columns)}

        def column(*names: str, required: bool = True) -> Optional[int]:
            for name in names:
                if name in field:
                    return field[name]
            if required:
                raise ValueError(f"{path}: atom_site loop lacks {names[0]}")
            return None

        group_col = column("_atom_site.group_PDB", required=False)
        atom_col = column("_atom_site.label_atom_id", "_atom_site.auth_atom_id")
        alt_col = column("_atom_site.label_alt_id", required=False)
        residue_col = column("_atom_site.label_comp_id", "_atom_site.auth_comp_id")
        chain_col = column("_atom_site.auth_asym_id", "_atom_site.label_asym_id")
        number_col = column("_atom_site.auth_seq_id", "_atom_site.label_seq_id")
        insertion_col = column("_atom_site.pdbx_PDB_ins_code", required=False)
        x_col = column("_atom_site.Cartn_x")
        y_col = column("_atom_site.Cartn_y")
        z_col = column("_atom_site.Cartn_z")
        b_col = column("_atom_site.B_iso_or_equiv", required=False)
        model_col = column("_atom_site.pdbx_PDB_model_num", required=False)
        records: dict[tuple[str, int, str], tuple[str, int, str, str, np.ndarray, float]] = {}
        width = len(columns)
        for offset in range(0, len(tokens), width):
            row = tokens[offset:offset + width]
            if group_col is not None and row[group_col] not in {"ATOM", "HETATM"}:
                continue
            if model_col is not None and row[model_col] not in {"1", ".", "?"}:
                continue
            if row[atom_col].strip("'\"") != "CA":
                continue
            if alt_col is not None and row[alt_col] not in {".", "?", "A"}:
                continue
            try:
                chain = row[chain_col] if row[chain_col] not in {".", "?"} else "_"
                number = int(float(row[number_col]))
                insertion = "" if insertion_col is None or row[insertion_col] in {".", "?"} else row[insertion_col]
                residue = row[residue_col].upper()
                coordinate = np.array(
                    [float(row[x_col]), float(row[y_col]), float(row[z_col])]
                )
                b_factor = (
                    float(row[b_col])
                    if b_col is not None and row[b_col] not in {".", "?"}
                    else float("nan")
                )
            except ValueError as error:
                raise ValueError(f"{path}: invalid atom_site row") from error
            key = (chain, number, insertion)
            records.setdefault(
                key, (chain, number, insertion, residue, coordinate, b_factor)
            )
        if not records:
            raise ValueError(f"{path}: no C-alpha records found in atom_site loop")
        return list(records.values())
    raise ValueError(f"{path}: no atom_site loop found")


class StructuralCoherenceAuditor:
    """Audit a related family of predictions/experimental structures."""

    def __init__(self, config: Optional[AuditConfig] = None):
        self.config = config or AuditConfig()

    def audit(
        self,
        family_id: str,
        models: Sequence[StructureModel],
        domains: Sequence[Domain],
        reference_model: Optional[str] = None,
    ) -> AuditReport:
        if len(models) < 2:
            raise ValueError("a coherence audit requires at least two structures")
        if len(domains) < 1:
            raise ValueError("a coherence audit requires at least one domain")
        by_id = {model.model_id: model for model in models}
        if len(by_id) != len(models):
            raise ValueError("model IDs must be unique")
        reference_model = reference_model or models[0].model_id
        if reference_model not in by_id:
            raise ValueError(f"reference model {reference_model!r} was not supplied")
        reference = by_id[reference_model]
        for domain in domains:
            if domain.end > len(reference.sequence):
                raise ValueError(
                    f"domain {domain.domain_id} ends at {domain.end}, beyond reference length "
                    f"{len(reference.sequence)}"
                )
        maps = {
            model.model_id: global_sequence_mapping(reference.sequence, model.sequence)
            for model in models
        }
        morphisms: dict[tuple[str, str, str], Optional[FittedMorphism]] = {}
        morphism_reasons: dict[tuple[str, str, str], tuple[str, ...]] = {}
        for first, second in combinations(models, 2):
            for domain in domains:
                fitted, reasons = self._fit_domain(first, second, domain, maps)
                morphisms[(first.model_id, second.model_id, domain.domain_id)] = fitted
                morphism_reasons[(first.model_id, second.model_id, domain.domain_id)] = reasons
                if fitted is not None:
                    morphisms[(second.model_id, first.model_id, domain.domain_id)] = FittedMorphism(
                        source_model=second.model_id,
                        target_model=first.model_id,
                        domain_id=domain.domain_id,
                        transform=fitted.transform.inverse(),
                        fitted_rmsd=fitted.fitted_rmsd,
                        residues_used=fitted.residues_used,
                        coverage=fitted.coverage,
                    )
                    morphism_reasons[(second.model_id, first.model_id, domain.domain_id)] = reasons
        arrangements = tuple(
            self._arrangement_check(first, second, anchor, mobile, maps, morphisms, morphism_reasons)
            for first, second in combinations(models, 2)
            for anchor, mobile in combinations(domains, 2)
        )
        compositions = tuple(
            self._composition_check(first, via, target, domain, maps, morphisms, morphism_reasons)
            for first, via, target in combinations(models, 3)
            for domain in domains
        )
        checks: tuple[DomainArrangementCheck | CompositionCheck, ...] = arrangements + compositions
        reasons: list[str] = []
        if len(domains) < 2:
            reasons.append("only one domain was supplied; domain-arrangement checks are unavailable")
        if not checks:
            standing = Standing.QUARANTINE
            reasons.append("no assessable coherence checks were generated")
        elif self.config.quarantine_on_any_missing_check and any(
            check.standing == Standing.QUARANTINE for check in checks
        ):
            standing = Standing.QUARANTINE
            reasons.append("one or more required checks were missing or uncertain")
        else:
            assessed = [check for check in checks if check.standing != Standing.QUARANTINE]
            if not assessed:
                standing = Standing.QUARANTINE
                reasons.append("all generated checks were quarantined")
            elif any(check.standing == Standing.INCONSISTENT for check in assessed):
                standing = Standing.INCONSISTENT
                reasons.append("at least one assessable structural relation failed coherence thresholds")
            else:
                standing = Standing.CONSISTENT
                reasons.append("all assessable structural relations passed current thresholds")
        model_summaries = tuple(
            {
                "model_id": model.model_id,
                "kind": model.kind,
                "residues": len(model.sequence),
                "mean_plddt": (
                    None
                    if model.kind == "experimental" or not np.isfinite(model.plddt).any()
                    else float(np.nanmean(model.plddt))
                ),
                "pae_available": model.pae is not None,
                "source_path": model.source_path,
                "reference_coverage": len(maps[model.model_id]) / len(reference.sequence),
            }
            for model in models
        )
        return AuditReport(
            family_id=family_id,
            reference_model=reference_model,
            standing=standing,
            models=model_summaries,
            domains=tuple(domains),
            domain_arrangements=arrangements,
            composition_checks=compositions,
            reasons=tuple(reasons),
            config=self.config,
        )

    def _fit_domain(
        self,
        source: StructureModel,
        target: StructureModel,
        domain: Domain,
        maps: Mapping[str, Mapping[int, int]],
    ) -> tuple[Optional[FittedMorphism], tuple[str, ...]]:
        pairs = self._paired_indices(source, target, domain, maps)
        coverage = len(pairs) / domain.length
        reasons: list[str] = []
        if len(pairs) < self.config.minimum_residues:
            reasons.append(
                f"only {len(pairs)} usable residues; {self.config.minimum_residues} required"
            )
        if coverage < self.config.minimum_domain_coverage:
            reasons.append(
                f"domain coverage {coverage:.3f} is below {self.config.minimum_domain_coverage:.3f}"
            )
        if reasons:
            return None, tuple(reasons)
        source_coordinates = np.asarray([source.coordinates[i] for i, _ in pairs])
        target_coordinates = np.asarray([target.coordinates[j] for _, j in pairs])
        try:
            transform, rmsd = fit_rigid_transform(source_coordinates, target_coordinates)
        except ValueError as error:
            return None, (str(error),)
        return FittedMorphism(
            source_model=source.model_id,
            target_model=target.model_id,
            domain_id=domain.domain_id,
            transform=transform,
            fitted_rmsd=rmsd,
            residues_used=len(pairs),
            coverage=coverage,
        ), ()

    def _paired_indices(
        self,
        source: StructureModel,
        target: StructureModel,
        domain: Domain,
        maps: Mapping[str, Mapping[int, int]],
    ) -> list[tuple[int, int]]:
        source_map = maps[source.model_id]
        target_map = maps[target.model_id]
        pairs: list[tuple[int, int]] = []
        for reference_index in domain.reference_indices:
            if reference_index not in source_map or reference_index not in target_map:
                continue
            source_index = source_map[reference_index]
            target_index = target_map[reference_index]
            if not self._usable_residue(source, source_index):
                continue
            if not self._usable_residue(target, target_index):
                continue
            pairs.append((source_index, target_index))
        return pairs

    def _usable_residue(self, model: StructureModel, index: int) -> bool:
        if model.kind == "experimental":
            return True
        value = model.plddt[index]
        return bool(np.isfinite(value) and value >= self.config.minimum_plddt)

    def _uncertainty_reasons(
        self,
        models: Iterable[StructureModel],
        domains: Sequence[Domain],
        maps: Mapping[str, Mapping[int, int]],
        cross_domain: bool,
    ) -> tuple[list[str], dict[str, Optional[float]]]:
        reasons: list[str] = []
        pae_values: dict[str, Optional[float]] = {}
        for model in models:
            if model.kind == "experimental":
                pae_values[model.model_id] = None
                continue
            if model.pae is None:
                pae_values[model.model_id] = None
                if self.config.require_pae_for_predictions:
                    reasons.append(f"{model.model_id} has no PAE matrix")
                continue
            mapped = [
                [maps[model.model_id][i] for i in domain.reference_indices if i in maps[model.model_id]]
                for domain in domains
            ]
            if any(not indices for indices in mapped):
                pae_values[model.model_id] = None
                reasons.append(f"{model.model_id} lacks mapped residues for PAE assessment")
                continue
            if cross_domain and len(mapped) == 2:
                block_forward = model.pae[np.ix_(mapped[0], mapped[1])].ravel()
                block_reverse = model.pae[np.ix_(mapped[1], mapped[0])].ravel()
                values = np.concatenate((block_forward, block_reverse))
            else:
                values = np.concatenate(
                    [model.pae[np.ix_(indices, indices)].ravel() for indices in mapped]
                )
            finite = values[np.isfinite(values)]
            if not finite.size:
                pae_values[model.model_id] = None
                reasons.append(f"{model.model_id} has no finite PAE values for this check")
                continue
            median = float(np.median(finite))
            pae_values[model.model_id] = median
            if median > self.config.maximum_assessable_pae:
                reasons.append(
                    f"{model.model_id} median PAE {median:.3f} exceeds "
                    f"{self.config.maximum_assessable_pae:.3f}"
                )
        return reasons, pae_values

    def _arrangement_check(
        self,
        source: StructureModel,
        target: StructureModel,
        anchor: Domain,
        mobile: Domain,
        maps: Mapping[str, Mapping[int, int]],
        morphisms: Mapping[tuple[str, str, str], Optional[FittedMorphism]],
        morphism_reasons: Mapping[tuple[str, str, str], tuple[str, ...]],
    ) -> DomainArrangementCheck:
        anchor_key = (source.model_id, target.model_id, anchor.domain_id)
        mobile_key = (source.model_id, target.model_id, mobile.domain_id)
        anchor_fit = morphisms.get(anchor_key)
        mobile_fit = morphisms.get(mobile_key)
        reasons = list(morphism_reasons.get(anchor_key, ())) + list(
            morphism_reasons.get(mobile_key, ())
        )
        uncertainty, pae_values = self._uncertainty_reasons(
            (source, target), (anchor, mobile), maps, cross_domain=True
        )
        reasons.extend(uncertainty)
        pairs = self._paired_indices(source, target, mobile, maps)
        if anchor_fit is None or mobile_fit is None or not pairs:
            return DomainArrangementCheck(
                source.model_id, target.model_id, anchor.domain_id, mobile.domain_id,
                Standing.QUARANTINE, None, None, None, None, None,
                pae_values.get(source.model_id), pae_values.get(target.model_id),
                len(pairs), tuple(dict.fromkeys(reasons)),
            )
        source_coordinates = np.asarray([source.coordinates[i] for i, _ in pairs])
        target_coordinates = np.asarray([target.coordinates[j] for _, j in pairs])
        anchored = anchor_fit.transform.apply(source_coordinates)
        residual = anchored - target_coordinates
        arrangement_rmsd = float(np.sqrt(np.mean(np.sum(residual * residual, axis=1))))
        excess = float(
            math.sqrt(max(0.0, arrangement_rmsd ** 2 - mobile_fit.fitted_rmsd ** 2))
        )
        rotation = rotation_distance_degrees(
            anchor_fit.transform.rotation, mobile_fit.transform.rotation
        )
        centroid_displacement = float(
            np.linalg.norm(anchored.mean(axis=0) - target_coordinates.mean(axis=0))
        )
        if reasons:
            standing = Standing.QUARANTINE
        elif (
            excess >= self.config.arrangement_rmsd_threshold
            or rotation >= self.config.arrangement_rotation_threshold_deg
        ):
            standing = Standing.INCONSISTENT
            reasons.append("domain pose disagreement exceeds a configured review threshold")
        else:
            standing = Standing.CONSISTENT
        return DomainArrangementCheck(
            source.model_id, target.model_id, anchor.domain_id, mobile.domain_id,
            standing, arrangement_rmsd, mobile_fit.fitted_rmsd, excess, rotation,
            centroid_displacement, pae_values.get(source.model_id),
            pae_values.get(target.model_id), len(pairs), tuple(dict.fromkeys(reasons)),
        )

    def _composition_check(
        self,
        source: StructureModel,
        via: StructureModel,
        target: StructureModel,
        domain: Domain,
        maps: Mapping[str, Mapping[int, int]],
        morphisms: Mapping[tuple[str, str, str], Optional[FittedMorphism]],
        morphism_reasons: Mapping[tuple[str, str, str], tuple[str, ...]],
    ) -> CompositionCheck:
        keys = (
            (source.model_id, via.model_id, domain.domain_id),
            (via.model_id, target.model_id, domain.domain_id),
            (source.model_id, target.model_id, domain.domain_id),
        )
        fits = [morphisms.get(key) for key in keys]
        reasons = [reason for key in keys for reason in morphism_reasons.get(key, ())]
        uncertainty, _pae_values = self._uncertainty_reasons(
            (source, via, target), (domain,), maps, cross_domain=False
        )
        reasons.extend(uncertainty)
        common_reference = [
            index for index in domain.reference_indices
            if all(index in maps[model.model_id] for model in (source, via, target))
            and all(
                self._usable_residue(model, maps[model.model_id][index])
                for model in (source, via, target)
            )
        ]
        if any(fit is None for fit in fits) or len(common_reference) < self.config.minimum_residues:
            if len(common_reference) < self.config.minimum_residues:
                reasons.append(
                    f"only {len(common_reference)} residues are common to all three models"
                )
            return CompositionCheck(
                source.model_id, via.model_id, target.model_id, domain.domain_id,
                Standing.QUARANTINE, None, None, len(common_reference),
                tuple(dict.fromkeys(reasons)),
            )
        first, second, direct = fits
        assert first is not None and second is not None and direct is not None
        filler = first.transform.then(second.transform)
        source_coordinates = np.asarray(
            [source.coordinates[maps[source.model_id][index]] for index in common_reference]
        )
        difference = filler.apply(source_coordinates) - direct.transform.apply(source_coordinates)
        filler_rmsd = float(np.sqrt(np.mean(np.sum(difference * difference, axis=1))))
        rotation = rotation_distance_degrees(filler.rotation, direct.transform.rotation)
        if reasons:
            standing = Standing.QUARANTINE
        elif (
            filler_rmsd >= self.config.composition_rmsd_threshold
            or rotation >= self.config.composition_rotation_threshold_deg
        ):
            standing = Standing.INCONSISTENT
            reasons.append("composed horn filler disagrees with the directly fitted morphism")
        else:
            standing = Standing.CONSISTENT
        return CompositionCheck(
            source.model_id, via.model_id, target.model_id, domain.domain_id,
            standing, filler_rmsd, rotation, len(common_reference),
            tuple(dict.fromkeys(reasons)),
        )


def audit_manifest(path: str | Path) -> AuditReport:
    """Load and run a versioned JSON audit manifest."""

    manifest_path = Path(path)
    with manifest_path.open(encoding="utf-8") as handle:
        manifest = json.load(handle)
    if manifest.get("schema_version", 1) != 1:
        raise ValueError("only manifest schema_version 1 is supported")
    root = manifest_path.resolve().parent

    def resolved(value: Optional[str]) -> Optional[Path]:
        if value is None:
            return None
        candidate = Path(value)
        return candidate if candidate.is_absolute() else root / candidate

    models = [
        load_structure(
            resolved(item["path"]),
            model_id=item["model_id"],
            kind=item.get("kind", "prediction"),
            chain=item.get("chain"),
            pae_path=resolved(item.get("pae_path")),
        )
        for item in manifest["models"]
    ]
    domains = [
        Domain(item["domain_id"], int(item["start"]), int(item["end"]))
        for item in manifest["domains"]
    ]
    config_fields = set(AuditConfig.__dataclass_fields__)
    unknown_config = set(manifest.get("config", {})) - config_fields
    if unknown_config:
        raise ValueError(f"unknown audit config fields: {sorted(unknown_config)}")
    config = AuditConfig(**manifest.get("config", {}))
    return StructuralCoherenceAuditor(config).audit(
        family_id=manifest["family_id"],
        models=models,
        domains=domains,
        reference_model=manifest.get("reference_model"),
    )


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Audit AlphaFold domain arrangements and compositional alignment coherence"
    )
    parser.add_argument("manifest", type=Path, help="schema-version 1 JSON manifest")
    parser.add_argument("--output", type=Path, help="write the JSON report here")
    args = parser.parse_args(argv)
    report = audit_manifest(args.manifest)
    rendered = json.dumps(report.to_dict(), indent=2, sort_keys=False)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
