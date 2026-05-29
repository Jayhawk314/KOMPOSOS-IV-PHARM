#!/usr/bin/env python3
"""
Category M molecular engine for pocket-aware fragment assembly.

The pipeline treats fragments as objects, attachment transforms as morphisms,
assembled ligands as colimits, and pocket scoring as an evaluation functor.
It is intentionally dependency-light: NumPy is required, RDKit is optional for
SMILES validation/canonicalization when present.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


AA_RESIDUES = {
    "ALA", "ARG", "ASN", "ASP", "CYS", "GLN", "GLU", "GLY", "HIS", "ILE",
    "LEU", "LYS", "MET", "PHE", "PRO", "SER", "THR", "TRP", "TYR", "VAL",
}
WATER_RESIDUES = {"HOH", "WAT", "DOD", "H2O"}
HYDROPHOBIC_RESIDUES = {"ALA", "VAL", "LEU", "ILE", "PHE", "TRP", "TYR", "MET", "PRO"}
POSITIVE_RESIDUES = {"LYS", "ARG", "HIS"}
NEGATIVE_RESIDUES = {"ASP", "GLU"}
VDW_RADII = {
    "H": 1.20,
    "C": 1.70,
    "N": 1.55,
    "O": 1.52,
    "F": 1.47,
    "P": 1.80,
    "S": 1.80,
    "CL": 1.75,
    "BR": 1.85,
    "I": 1.98,
    "ZN": 1.39,
    "MG": 1.73,
    "FE": 1.72,
}
ATOMIC_WEIGHTS = {
    "H": 1.008,
    "C": 12.011,
    "N": 14.007,
    "O": 15.999,
    "F": 18.998,
    "P": 30.974,
    "S": 32.06,
    "CL": 35.45,
    "BR": 79.904,
    "I": 126.90,
}


@dataclass(frozen=True)
class PDBAtom:
    serial: int
    name: str
    residue_name: str
    chain_id: str
    residue_id: str
    record_type: str
    element: str
    coord: np.ndarray
    partial_charge: float = 0.0

    @property
    def residue_label(self) -> str:
        return f"{self.chain_id}:{self.residue_name}{self.residue_id}"


@dataclass(frozen=True)
class InteractionSite:
    kind: str
    position: np.ndarray
    strength: float
    residue_label: str
    source_atom: str
    charge: float = 0.0


@dataclass
class Pocket:
    center: np.ndarray
    radius: float
    atoms: List[PDBAtom]
    residues: List[str]
    sites: List[InteractionSite]
    mode: str

    def to_summary(self) -> Dict:
        return {
            "center": round_vector(self.center),
            "radius": float(self.radius),
            "mode": self.mode,
            "num_atoms": len(self.atoms),
            "num_residues": len(self.residues),
            "residues": self.residues[:80],
            "site_counts": count_by_kind(site.kind for site in self.sites),
        }


@dataclass(frozen=True)
class FragmentAtom:
    element: str
    coord: np.ndarray
    partial_charge: float = 0.0
    donor: bool = False
    acceptor: bool = False
    hydrophobic: bool = False
    aromatic: bool = False


@dataclass(frozen=True)
class Bond:
    atom_i: int
    atom_j: int
    order: float = 1.0


@dataclass(frozen=True)
class ConnectionPoint:
    atom_index: int
    label: str
    direction: np.ndarray
    bond_order: float = 1.0


@dataclass(frozen=True)
class MolecularFragment:
    name: str
    atoms: Tuple[FragmentAtom, ...]
    bonds: Tuple[Bond, ...]
    connection_points: Tuple[ConnectionPoint, ...]
    role: str

    @property
    def coordinates(self) -> np.ndarray:
        return np.array([atom.coord for atom in self.atoms], dtype=float)


@dataclass(frozen=True)
class PlacedFragment:
    placed_id: int
    fragment: MolecularFragment
    rotation: np.ndarray
    translation: np.ndarray

    def atom_coord(self, atom_index: int) -> np.ndarray:
        return self.rotation @ self.fragment.atoms[atom_index].coord + self.translation

    def atom_coords(self) -> np.ndarray:
        return np.array([self.atom_coord(index) for index in range(len(self.fragment.atoms))])


@dataclass(frozen=True)
class OpenConnection:
    placed_id: int
    connection_index: int
    position: np.ndarray
    direction: np.ndarray
    element: str
    label: str


@dataclass(frozen=True)
class CrossFragmentBond:
    source_fragment_id: int
    source_atom_index: int
    target_fragment_id: int
    target_atom_index: int
    order: float = 1.0


@dataclass
class MolecularAssembly:
    placed_fragments: List[PlacedFragment]
    cross_bonds: List[CrossFragmentBond]
    open_connections: List[OpenConnection]
    trace: List[Dict]
    score_terms: Dict[str, float] = field(default_factory=dict)
    score_total: float = 0.0

    def atom_count(self) -> int:
        return sum(len(placed.fragment.atoms) for placed in self.placed_fragments)

    def fragment_names(self) -> List[str]:
        return [placed.fragment.name for placed in self.placed_fragments]

    def all_atoms(self) -> List[Tuple[int, int, FragmentAtom, np.ndarray]]:
        atoms = []
        for placed in self.placed_fragments:
            for atom_index, atom in enumerate(placed.fragment.atoms):
                atoms.append((placed.placed_id, atom_index, atom, placed.atom_coord(atom_index)))
        return atoms


@dataclass
class DesignResult:
    pdb_path: str
    pocket: Pocket
    candidates: List[Dict]
    rejection_counts: Dict[str, int]
    warnings: List[str]

    def to_dict(self) -> Dict:
        return {
            "pdb_path": self.pdb_path,
            "pocket": self.pocket.to_summary(),
            "candidate_count": len(self.candidates),
            "candidates": self.candidates,
            "rejection_counts": self.rejection_counts,
            "warnings": self.warnings,
        }


def round_vector(vector: np.ndarray, digits: int = 3) -> List[float]:
    return [round(float(value), digits) for value in vector.tolist()]


def count_by_kind(values: Iterable[str]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def unit_vector(vector: Sequence[float]) -> np.ndarray:
    arr = np.array(vector, dtype=float)
    norm = float(np.linalg.norm(arr))
    if norm < 1e-12:
        return np.array([1.0, 0.0, 0.0], dtype=float)
    return arr / norm


def rotation_about_axis(axis: Sequence[float], angle: float) -> np.ndarray:
    x, y, z = unit_vector(axis)
    c = math.cos(angle)
    s = math.sin(angle)
    one_c = 1.0 - c
    return np.array(
        [
            [c + x * x * one_c, x * y * one_c - z * s, x * z * one_c + y * s],
            [y * x * one_c + z * s, c + y * y * one_c, y * z * one_c - x * s],
            [z * x * one_c - y * s, z * y * one_c + x * s, c + z * z * one_c],
        ],
        dtype=float,
    )


def align_vectors(source: Sequence[float], target: Sequence[float]) -> np.ndarray:
    source_unit = unit_vector(source)
    target_unit = unit_vector(target)
    cross = np.cross(source_unit, target_unit)
    dot = float(np.clip(np.dot(source_unit, target_unit), -1.0, 1.0))
    cross_norm = float(np.linalg.norm(cross))
    if cross_norm < 1e-10:
        if dot > 0:
            return np.eye(3)
        fallback = np.cross(source_unit, np.array([1.0, 0.0, 0.0]))
        if np.linalg.norm(fallback) < 1e-10:
            fallback = np.cross(source_unit, np.array([0.0, 1.0, 0.0]))
        return rotation_about_axis(fallback, math.pi)
    skew = np.array(
        [
            [0.0, -cross[2], cross[1]],
            [cross[2], 0.0, -cross[0]],
            [-cross[1], cross[0], 0.0],
        ],
        dtype=float,
    )
    return np.eye(3) + skew + skew @ skew * ((1.0 - dot) / (cross_norm ** 2))


def rotation_library() -> List[np.ndarray]:
    rotations = [np.eye(3)]
    for angle in (math.pi / 2, math.pi, 3 * math.pi / 2):
        rotations.append(rotation_about_axis([0.0, 0.0, 1.0], angle))
    rotations.append(rotation_about_axis([0.0, 1.0, 0.0], math.pi))
    rotations.append(rotation_about_axis([1.0, 0.0, 0.0], math.pi))
    return rotations


def infer_element(atom_name: str, explicit: str = "") -> str:
    if explicit:
        return explicit.strip().upper()
    letters = "".join(char for char in atom_name.upper() if char.isalpha())
    if not letters:
        return "C"
    for two_letter in ("CL", "BR", "ZN", "MG", "FE"):
        if letters.startswith(two_letter):
            return two_letter
    return letters[0]


def residue_atom_charge(residue_name: str, atom_name: str, element: str, record_type: str) -> float:
    residue = residue_name.upper()
    atom = atom_name.upper()
    if record_type == "ATOM":
        if residue == "LYS" and atom.startswith("NZ"):
            return 1.0
        if residue == "ARG" and (atom.startswith("NH") or atom.startswith("NE") or atom.startswith("CZ")):
            return 0.7
        if residue == "HIS" and atom.startswith(("ND", "NE")):
            return 0.35
        if residue == "ASP" and atom.startswith("OD"):
            return -0.7
        if residue == "GLU" and atom.startswith("OE"):
            return -0.7
        if element == "O":
            return -0.2
        if element == "N":
            return 0.2
    return 0.0


def parse_pdb_atoms(pdb_path: Path, chain: Optional[str] = None) -> Tuple[List[PDBAtom], List[PDBAtom]]:
    protein_atoms: List[PDBAtom] = []
    ligand_atoms: List[PDBAtom] = []
    chain_filter = chain.strip() if chain else None

    with pdb_path.open("r", encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            record_type = line[0:6].strip()
            if record_type not in {"ATOM", "HETATM"}:
                continue
            altloc = line[16:17].strip()
            if altloc and altloc != "A":
                continue
            chain_id = line[21:22].strip() or "_"
            if chain_filter and chain_id != chain_filter:
                continue
            residue_name = line[17:20].strip().upper()
            if residue_name in WATER_RESIDUES:
                continue
            try:
                x = float(line[30:38])
                y = float(line[38:46])
                z = float(line[46:54])
            except ValueError:
                parts = line.split()
                if len(parts) < 9:
                    continue
                x, y, z = map(float, parts[6:9])
            atom_name = line[12:16].strip()
            residue_id = f"{line[22:26].strip()}{line[26:27].strip()}".strip() or "0"
            explicit_element = line[76:78].strip() if len(line) >= 78 else ""
            element = infer_element(atom_name, explicit_element)
            serial_text = line[6:11].strip()
            serial = int(serial_text) if serial_text.isdigit() else len(protein_atoms) + len(ligand_atoms) + 1
            charge = residue_atom_charge(residue_name, atom_name, element, record_type)
            atom = PDBAtom(
                serial=serial,
                name=atom_name,
                residue_name=residue_name,
                chain_id=chain_id,
                residue_id=residue_id,
                record_type=record_type,
                element=element,
                coord=np.array([x, y, z], dtype=float),
                partial_charge=charge,
            )
            if record_type == "ATOM" or residue_name in AA_RESIDUES:
                protein_atoms.append(atom)
            else:
                ligand_atoms.append(atom)

    if not protein_atoms:
        raise ValueError(f"No protein atoms found in {pdb_path}")
    return protein_atoms, ligand_atoms


def parse_center(center: Optional[str]) -> Optional[np.ndarray]:
    if center is None:
        return None
    parts = [part.strip() for part in center.split(",")]
    if len(parts) != 3:
        raise ValueError("--center must use x,y,z format")
    return np.array([float(part) for part in parts], dtype=float)


def residue_selector_matches(atom: PDBAtom, selector: str) -> bool:
    cleaned = selector.strip()
    if not cleaned:
        return False
    if ":" in cleaned:
        chain_id, residue_id = cleaned.split(":", 1)
        return atom.chain_id == chain_id and atom.residue_id == residue_id
    return atom.residue_id == cleaned


def pocket_center_from_residue(protein_atoms: List[PDBAtom], selector: str) -> Optional[np.ndarray]:
    selected = [atom.coord for atom in protein_atoms if residue_selector_matches(atom, selector)]
    if not selected:
        return None
    return np.mean(np.array(selected), axis=0)


def _fibonacci_directions(count: int = 64) -> np.ndarray:
    """Roughly uniform unit vectors on the sphere via the Fibonacci lattice."""
    indices = np.arange(count, dtype=float) + 0.5
    phi = np.arccos(1.0 - 2.0 * indices / count)
    theta = math.pi * (1.0 + 5.0 ** 0.5) * indices
    return np.stack(
        [np.cos(theta) * np.sin(phi), np.sin(theta) * np.sin(phi), np.cos(phi)],
        axis=1,
    )


def _buriedness(
    point: np.ndarray,
    coords: np.ndarray,
    directions: np.ndarray,
    ray_length: float = 10.0,
    cone_cos: float = 0.9,
) -> float:
    """Fraction of probe directions that hit a protein atom within ray_length.

    A real binding pocket is a concavity: most directions are blocked by protein
    but at least one (the ligand-entry side) is open to solvent. Fully buried
    core points approach 1.0 but contain no void; exposed surface bumps stay low.
    """
    vectors = coords - point
    norms = np.linalg.norm(vectors, axis=1)
    mask = (norms > 1e-6) & (norms <= ray_length)
    if not np.any(mask):
        return 0.0
    units = vectors[mask] / norms[mask, None]
    dots = directions @ units.T  # (num_directions, num_nearby_atoms)
    blocked = np.any(dots > cone_cos, axis=1)
    return float(np.mean(blocked))


def _largest_cavity(points: np.ndarray, link_distance: float = 3.2) -> np.ndarray:
    """Return the points of the largest connected cluster.

    Two points belong to the same cavity if within link_distance of each other
    (grid spacing is 2.5 A, so this links grid-adjacent voids). Connectivity is
    resolved with union-find; the largest component is the main pocket.
    """
    count = len(points)
    parent = list(range(count))

    def find(node: int) -> int:
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node

    distances = np.linalg.norm(points[:, None, :] - points[None, :, :], axis=2)
    for i in range(count):
        for j in np.where(distances[i] <= link_distance)[0]:
            j = int(j)
            if j > i:
                root_i, root_j = find(i), find(j)
                if root_i != root_j:
                    parent[root_i] = root_j

    components: Dict[int, List[int]] = defaultdict(list)
    for node in range(count):
        components[find(node)].append(node)
    largest = max(components.values(), key=len)
    return points[largest]


def detect_grid_pocket_center(
    protein_atoms: List[PDBAtom],
    radius: float,
    grid_spacing: float = 2.5,
    max_points: int = 45000,
) -> Tuple[np.ndarray, Dict[str, float]]:
    """
    Approximate the ligand-binding pocket center as the largest buried cavity.

    Two-stage method:
      1. Sweep a grid and keep void points that sit inside the protein envelope
         (a real clearance from the nearest atom, surrounded by enough atoms).
      2. Keep the concave subset by ray-cast buriedness, group those points into
         connected cavities, and return the centroid of the LARGEST cavity.

    The drug-binding pocket is empirically the largest contiguous concave cavity.
    An earlier version maximised single-point buriedness, which walked into the
    fully-enclosed protein core (buriedness ~1.0) instead of the solvent-
    accessible cleft; selecting the largest cavity by volume fixes that.
    Validated on data/benchmarks/cocrystal_small.json via
    scripts/benchmark_pocket_recovery.py (median pocket-center error ~4 A,
    versus ~12 A for the protein-centroid baseline).
    """
    coords = np.array([atom.coord for atom in protein_atoms], dtype=float)
    min_corner = np.min(coords, axis=0) - 2.0
    max_corner = np.max(coords, axis=0) + 2.0
    axes = [np.arange(min_corner[i], max_corner[i] + grid_spacing, grid_spacing) for i in range(3)]
    grid_shape = [len(axis) for axis in axes]
    total_points = int(grid_shape[0] * grid_shape[1] * grid_shape[2])
    if total_points > max_points:
        scale = (total_points / max_points) ** (1.0 / 3.0)
        grid_spacing *= scale
        axes = [np.arange(min_corner[i], max_corner[i] + grid_spacing, grid_spacing) for i in range(3)]

    hotspot_indices = [
        index for index, atom in enumerate(protein_atoms)
        if abs(atom.partial_charge) > 0.25
        or atom.element in {"N", "O"}
        or (atom.element in {"C", "S"} and atom.residue_name in HYDROPHOBIC_RESIDUES)
    ]
    hotspot_coords = coords[hotspot_indices] if hotspot_indices else coords

    centroid = np.mean(coords, axis=0)
    candidate_points: List[np.ndarray] = []
    candidate_contacts: List[float] = []
    candidate_hotspots: List[float] = []
    evaluated = 0
    chunk: List[List[float]] = []
    chunk_size = 2048

    def collect(points: List[List[float]]) -> None:
        nonlocal evaluated
        if not points:
            return
        point_array = np.array(points, dtype=float)
        evaluated += len(point_array)
        distances = np.linalg.norm(point_array[:, None, :] - coords[None, :, :], axis=2)
        min_distances = np.min(distances, axis=1)
        contact_counts = np.sum(distances <= 9.0, axis=1)
        # Void inside the protein envelope: a real clearance from the nearest
        # atom, embedded in enough neighbours to exclude solvent-floating points.
        valid_mask = (min_distances >= 3.0) & (min_distances <= 5.5) & (contact_counts >= 12)
        if not np.any(valid_mask):
            return
        valid_index = np.where(valid_mask)[0]
        hotspot_distances = np.linalg.norm(
            point_array[valid_index][:, None, :] - hotspot_coords[None, :, :], axis=2
        )
        hotspot_counts = np.sum(hotspot_distances <= 8.0, axis=1)
        for local, global_index in enumerate(valid_index):
            candidate_points.append(point_array[global_index])
            candidate_contacts.append(float(contact_counts[global_index]))
            candidate_hotspots.append(float(hotspot_counts[local]))

    for x_coord in axes[0]:
        for y_coord in axes[1]:
            for z_coord in axes[2]:
                chunk.append([float(x_coord), float(y_coord), float(z_coord)])
                if len(chunk) >= chunk_size:
                    collect(chunk)
                    chunk = []
    collect(chunk)

    if not candidate_points:
        return centroid, {
            "grid_spacing": round(float(grid_spacing), 3),
            "grid_points_evaluated": float(evaluated),
            "valid_cavity_points": 0.0,
            "buried_points": 0,
            "largest_cavity_points": 0,
            "best_grid_score": 0.0,
        }

    candidate_array = np.array(candidate_points, dtype=float)

    # Buriedness is the costly term; cap the evaluated set with a deterministic
    # uniform thinning so large proteins stay fast without spatial bias.
    max_buriedness_evals = 1600
    if len(candidate_array) > max_buriedness_evals:
        stride = max(1, len(candidate_array) // max_buriedness_evals)
        candidate_array = candidate_array[::stride]

    directions = _fibonacci_directions(64)
    buriedness = np.array(
        [_buriedness(point, coords, directions) for point in candidate_array],
        dtype=float,
    )
    # Keep the concave subset (pocket-like). The lower bound was tuned on the
    # co-crystal benchmark; there is no upper cap so deep cavities still qualify.
    buried = candidate_array[buriedness >= 0.78]
    if len(buried) < 3:
        return centroid, {
            "grid_spacing": round(float(grid_spacing), 3),
            "grid_points_evaluated": float(evaluated),
            "valid_cavity_points": float(len(candidate_points)),
            "buried_points": int(len(buried)),
            "largest_cavity_points": 0,
            "best_grid_score": 0.0,
        }

    cluster = _largest_cavity(buried, link_distance=3.2)
    best_point = np.mean(cluster, axis=0)
    return best_point, {
        "grid_spacing": round(float(grid_spacing), 3),
        "grid_points_evaluated": float(evaluated),
        "valid_cavity_points": float(len(candidate_points)),
        "buried_points": int(len(buried)),
        "largest_cavity_points": int(len(cluster)),
        "best_grid_score": round(float(len(cluster)), 1),
    }


def define_pocket(
    protein_atoms: List[PDBAtom],
    ligand_atoms: List[PDBAtom],
    radius: float,
    center: Optional[np.ndarray] = None,
    residue: Optional[str] = None,
    pocket_mode: str = "auto",
) -> Pocket:
    mode = "explicit_center"
    if center is None and residue and pocket_mode in {"auto", "residue"}:
        center = pocket_center_from_residue(protein_atoms, residue)
        mode = f"residue:{residue}"
    if center is None and ligand_atoms and pocket_mode in {"auto", "ligand"}:
        center = np.mean(np.array([atom.coord for atom in ligand_atoms]), axis=0)
        mode = "bound_ligand"
    if center is None and pocket_mode in {"auto", "grid"}:
        center, grid_meta = detect_grid_pocket_center(protein_atoms, radius)
        mode = (
            f"grid_cavity:spacing={grid_meta['grid_spacing']}:"
            f"valid={int(grid_meta['valid_cavity_points'])}:"
            f"score={grid_meta['best_grid_score']}"
        )
    if center is None:
        center = np.mean(np.array([atom.coord for atom in protein_atoms]), axis=0)
        mode = "protein_centroid"

    distances = [(float(np.linalg.norm(atom.coord - center)), atom) for atom in protein_atoms]
    pocket_atoms = [atom for distance, atom in distances if distance <= radius + 2.0]
    if len(pocket_atoms) < 12:
        pocket_atoms = [atom for _, atom in sorted(distances, key=lambda item: item[0])[: min(160, len(distances))]]
        mode = f"{mode}:nearest_atoms"

    residues = sorted({atom.residue_label for atom in pocket_atoms})
    sites = build_interaction_sites(pocket_atoms, center)
    if not sites:
        sites = [InteractionSite("center", center, 1.0, "geometric_center", "CENTER", 0.0)]
    return Pocket(center=center, radius=radius, atoms=pocket_atoms, residues=residues, sites=sites, mode=mode)


def build_interaction_sites(pocket_atoms: List[PDBAtom], center: np.ndarray) -> List[InteractionSite]:
    sites: List[InteractionSite] = []
    for atom in pocket_atoms:
        residue = atom.residue_name
        element = atom.element
        distance_to_center = float(np.linalg.norm(atom.coord - center))
        distance_weight = 1.0 / (1.0 + 0.05 * distance_to_center)
        if atom.partial_charge > 0.25:
            sites.append(InteractionSite("positive", atom.coord, 1.2 * distance_weight, atom.residue_label, atom.name, atom.partial_charge))
        if atom.partial_charge < -0.25:
            sites.append(InteractionSite("negative", atom.coord, 1.2 * distance_weight, atom.residue_label, atom.name, atom.partial_charge))
        if element == "N":
            sites.append(InteractionSite("donor", atom.coord, 0.9 * distance_weight, atom.residue_label, atom.name, atom.partial_charge))
        if element == "O":
            sites.append(InteractionSite("acceptor", atom.coord, 0.9 * distance_weight, atom.residue_label, atom.name, atom.partial_charge))
        if element in {"C", "S"} and residue in HYDROPHOBIC_RESIDUES:
            sites.append(InteractionSite("hydrophobic", atom.coord, 0.7 * distance_weight, atom.residue_label, atom.name, atom.partial_charge))
    sites.sort(key=lambda site: site.strength, reverse=True)
    return sites[:96]


def atom(element: str, coord: Sequence[float], **kwargs) -> FragmentAtom:
    return FragmentAtom(element=element.upper(), coord=np.array(coord, dtype=float), **kwargs)


def cp(atom_index: int, label: str, direction: Sequence[float], bond_order: float = 1.0) -> ConnectionPoint:
    return ConnectionPoint(atom_index=atom_index, label=label, direction=unit_vector(direction), bond_order=bond_order)


def ring_coords(size: int, radius: float) -> List[np.ndarray]:
    return [
        np.array([radius * math.cos(2 * math.pi * index / size), radius * math.sin(2 * math.pi * index / size), 0.0])
        for index in range(size)
    ]


def build_fragment_library(use_rdkit_conformers: bool = True) -> Dict[str, MolecularFragment]:
    benzene_coords = ring_coords(6, 1.39)
    pyridine_coords = ring_coords(6, 1.36)
    pyrimidine_coords = ring_coords(6, 1.36)
    pyrazine_coords = ring_coords(6, 1.36)
    imidazole_coords = ring_coords(5, 1.25)
    pyrazole_coords = ring_coords(5, 1.25)
    fragments = {
        "benzene": MolecularFragment(
            name="benzene",
            atoms=tuple(atom("C", coord, hydrophobic=True, aromatic=True) for coord in benzene_coords),
            bonds=tuple(Bond(index, (index + 1) % 6, 1.5) for index in range(6)),
            connection_points=(cp(0, "ring_C1", benzene_coords[0]), cp(3, "ring_C4", benzene_coords[3])),
            role="seed",
        ),
        "pyridine": MolecularFragment(
            name="pyridine",
            atoms=(
                atom("N", pyridine_coords[0], partial_charge=-0.35, acceptor=True, aromatic=True),
                atom("C", pyridine_coords[1], hydrophobic=True, aromatic=True),
                atom("C", pyridine_coords[2], hydrophobic=True, aromatic=True),
                atom("C", pyridine_coords[3], hydrophobic=True, aromatic=True),
                atom("C", pyridine_coords[4], hydrophobic=True, aromatic=True),
                atom("C", pyridine_coords[5], hydrophobic=True, aromatic=True),
            ),
            bonds=tuple(Bond(index, (index + 1) % 6, 1.5) for index in range(6)),
            connection_points=(cp(3, "ring_C4", pyridine_coords[3]),),
            role="seed",
        ),
        "imidazole": MolecularFragment(
            name="imidazole",
            atoms=(
                atom("N", imidazole_coords[0], partial_charge=-0.25, acceptor=True, aromatic=True),
                atom("C", imidazole_coords[1], hydrophobic=True, aromatic=True),
                atom("N", imidazole_coords[2], partial_charge=0.18, donor=True, aromatic=True),
                atom("C", imidazole_coords[3], hydrophobic=True, aromatic=True),
                atom("C", imidazole_coords[4], hydrophobic=True, aromatic=True),
            ),
            bonds=tuple(Bond(index, (index + 1) % 5, 1.5) for index in range(5)),
            connection_points=(cp(3, "ring_C4", imidazole_coords[3]),),
            role="seed",
        ),
        "pyrimidine": MolecularFragment(
            name="pyrimidine",
            atoms=(
                atom("N", pyrimidine_coords[0], partial_charge=-0.35, acceptor=True, aromatic=True),
                atom("C", pyrimidine_coords[1], hydrophobic=True, aromatic=True),
                atom("N", pyrimidine_coords[2], partial_charge=-0.35, acceptor=True, aromatic=True),
                atom("C", pyrimidine_coords[3], hydrophobic=True, aromatic=True),
                atom("C", pyrimidine_coords[4], hydrophobic=True, aromatic=True),
                atom("C", pyrimidine_coords[5], hydrophobic=True, aromatic=True),
            ),
            bonds=tuple(Bond(index, (index + 1) % 6, 1.5) for index in range(6)),
            connection_points=(cp(4, "hinge_C5", pyrimidine_coords[4]),),
            role="seed",
        ),
        "aminopyrimidine": MolecularFragment(
            name="aminopyrimidine",
            atoms=(
                atom("N", pyrimidine_coords[0], partial_charge=-0.35, acceptor=True, aromatic=True),
                atom("C", pyrimidine_coords[1], hydrophobic=True, aromatic=True),
                atom("N", pyrimidine_coords[2], partial_charge=-0.35, acceptor=True, aromatic=True),
                atom("C", pyrimidine_coords[3], hydrophobic=True, aromatic=True),
                atom("C", pyrimidine_coords[4], hydrophobic=True, aromatic=True),
                atom("C", pyrimidine_coords[5], hydrophobic=True, aromatic=True),
                atom("N", pyrimidine_coords[4] + np.array([0.0, -1.35, 0.0]), partial_charge=0.25, donor=True),
            ),
            bonds=tuple(Bond(index, (index + 1) % 6, 1.5) for index in range(6)) + (Bond(4, 6, 1.0),),
            connection_points=(cp(3, "hinge_C4", pyrimidine_coords[3]),),
            role="seed",
        ),
        "pyrazine": MolecularFragment(
            name="pyrazine",
            atoms=(
                atom("N", pyrazine_coords[0], partial_charge=-0.35, acceptor=True, aromatic=True),
                atom("C", pyrazine_coords[1], hydrophobic=True, aromatic=True),
                atom("C", pyrazine_coords[2], hydrophobic=True, aromatic=True),
                atom("N", pyrazine_coords[3], partial_charge=-0.35, acceptor=True, aromatic=True),
                atom("C", pyrazine_coords[4], hydrophobic=True, aromatic=True),
                atom("C", pyrazine_coords[5], hydrophobic=True, aromatic=True),
            ),
            bonds=tuple(Bond(index, (index + 1) % 6, 1.5) for index in range(6)),
            connection_points=(cp(2, "ring_C3", pyrazine_coords[2]), cp(5, "ring_C6", pyrazine_coords[5])),
            role="seed",
        ),
        "pyrazole": MolecularFragment(
            name="pyrazole",
            atoms=(
                atom("N", pyrazole_coords[0], partial_charge=0.18, donor=True, aromatic=True),
                atom("N", pyrazole_coords[1], partial_charge=-0.30, acceptor=True, aromatic=True),
                atom("C", pyrazole_coords[2], hydrophobic=True, aromatic=True),
                atom("C", pyrazole_coords[3], hydrophobic=True, aromatic=True),
                atom("C", pyrazole_coords[4], hydrophobic=True, aromatic=True),
            ),
            bonds=tuple(Bond(index, (index + 1) % 5, 1.5) for index in range(5)),
            connection_points=(cp(3, "ring_C4", pyrazole_coords[3]),),
            role="seed",
        ),
        "methylene": MolecularFragment(
            name="methylene",
            atoms=(atom("C", [0.0, 0.0, 0.0], hydrophobic=True),),
            bonds=(),
            connection_points=(cp(0, "left", [-1.0, 0.0, 0.0]), cp(0, "right", [1.0, 0.0, 0.0])),
            role="linker",
        ),
        "ethylene": MolecularFragment(
            name="ethylene",
            atoms=(atom("C", [-0.77, 0.0, 0.0], hydrophobic=True), atom("C", [0.77, 0.0, 0.0], hydrophobic=True)),
            bonds=(Bond(0, 1, 1.0),),
            connection_points=(cp(0, "left", [-1.0, 0.0, 0.0]), cp(1, "right", [1.0, 0.0, 0.0])),
            role="linker",
        ),
        "ether": MolecularFragment(
            name="ether",
            atoms=(atom("O", [0.0, 0.0, 0.0], partial_charge=-0.28, acceptor=True),),
            bonds=(),
            connection_points=(cp(0, "left", [-1.0, 0.0, 0.0]), cp(0, "right", [1.0, 0.0, 0.0])),
            role="linker",
        ),
        "carbonyl": MolecularFragment(
            name="carbonyl",
            atoms=(atom("C", [0.0, 0.0, 0.0], partial_charge=0.35), atom("O", [0.0, 1.22, 0.0], partial_charge=-0.45, acceptor=True)),
            bonds=(Bond(0, 1, 2.0),),
            connection_points=(cp(0, "acyl_left", [-1.0, 0.0, 0.0]), cp(0, "acyl_right", [1.0, 0.0, 0.0])),
            role="linker",
        ),
        "amide": MolecularFragment(
            name="amide",
            atoms=(
                atom("C", [0.0, 0.0, 0.0], partial_charge=0.35),
                atom("O", [0.0, 1.22, 0.0], partial_charge=-0.45, acceptor=True),
                atom("N", [1.32, 0.0, 0.0], partial_charge=0.20, donor=True),
            ),
            bonds=(Bond(0, 1, 2.0), Bond(0, 2, 1.0)),
            connection_points=(cp(0, "acyl", [-1.0, 0.0, 0.0]), cp(2, "amide_N", [1.0, 0.0, 0.0])),
            role="linker",
        ),
        "urea": MolecularFragment(
            name="urea",
            atoms=(
                atom("C", [0.0, 0.0, 0.0], partial_charge=0.45),
                atom("O", [0.0, 1.22, 0.0], partial_charge=-0.45, acceptor=True),
                atom("N", [-1.25, 0.0, 0.0], partial_charge=0.22, donor=True),
                atom("N", [1.25, 0.0, 0.0], partial_charge=0.22, donor=True),
            ),
            bonds=(Bond(0, 1, 2.0), Bond(0, 2, 1.0), Bond(0, 3, 1.0)),
            connection_points=(cp(2, "urea_N_left", [-1.0, 0.0, 0.0]), cp(3, "urea_N_right", [1.0, 0.0, 0.0])),
            role="linker",
        ),
        "sulfonamide": MolecularFragment(
            name="sulfonamide",
            atoms=(
                atom("S", [0.0, 0.0, 0.0], partial_charge=0.55),
                atom("O", [0.0, 1.42, 0.0], partial_charge=-0.45, acceptor=True),
                atom("O", [0.0, -1.42, 0.0], partial_charge=-0.45, acceptor=True),
                atom("N", [1.55, 0.0, 0.0], partial_charge=0.20, donor=True),
            ),
            bonds=(Bond(0, 1, 2.0), Bond(0, 2, 2.0), Bond(0, 3, 1.0)),
            connection_points=(cp(0, "sulfonyl_S", [-1.0, 0.0, 0.0]), cp(3, "sulfonamide_N", [1.0, 0.0, 0.0])),
            role="linker",
        ),
        "amine": MolecularFragment(
            name="amine",
            atoms=(atom("N", [0.0, 0.0, 0.0], partial_charge=0.35, donor=True),),
            bonds=(),
            connection_points=(cp(0, "amine_N", [1.0, 0.0, 0.0]),),
            role="cap",
        ),
        "hydroxyl": MolecularFragment(
            name="hydroxyl",
            atoms=(atom("O", [0.0, 0.0, 0.0], partial_charge=-0.30, donor=True, acceptor=True),),
            bonds=(),
            connection_points=(cp(0, "hydroxyl_O", [1.0, 0.0, 0.0]),),
            role="cap",
        ),
        "carboxylate": MolecularFragment(
            name="carboxylate",
            atoms=(
                atom("C", [0.0, 0.0, 0.0], partial_charge=0.55),
                atom("O", [0.0, 1.24, 0.0], partial_charge=-0.65, acceptor=True),
                atom("O", [0.0, -1.24, 0.0], partial_charge=-0.65, acceptor=True),
            ),
            bonds=(Bond(0, 1, 1.5), Bond(0, 2, 1.5)),
            connection_points=(cp(0, "carboxyl_C", [1.0, 0.0, 0.0]),),
            role="cap",
        ),
        "methyl": MolecularFragment(
            name="methyl",
            atoms=(atom("C", [0.0, 0.0, 0.0], hydrophobic=True),),
            bonds=(),
            connection_points=(cp(0, "methyl_C", [1.0, 0.0, 0.0]),),
            role="cap",
        ),
        "nitrile": MolecularFragment(
            name="nitrile",
            atoms=(atom("C", [0.0, 0.0, 0.0]), atom("N", [1.16, 0.0, 0.0], partial_charge=-0.30, acceptor=True)),
            bonds=(Bond(0, 1, 3.0),),
            connection_points=(cp(0, "nitrile_C", [-1.0, 0.0, 0.0]),),
            role="cap",
        ),
        "fluoro": MolecularFragment(
            name="fluoro",
            atoms=(atom("F", [0.0, 0.0, 0.0], partial_charge=-0.18),),
            bonds=(),
            connection_points=(cp(0, "fluoro_F", [1.0, 0.0, 0.0]),),
            role="cap",
        ),
    }
    if use_rdkit_conformers:
        fragments = apply_rdkit_conformers(fragments)
    return fragments


def vdw_radius(element: str) -> float:
    return VDW_RADII.get(element.upper(), 1.70)


def bond_length(element_a: str, element_b: str, order: float = 1.0) -> float:
    pair = tuple(sorted((element_a.upper(), element_b.upper())))
    if order >= 1.5:
        return {
            ("C", "C"): 1.39,
            ("C", "N"): 1.34,
            ("C", "O"): 1.23,
            ("N", "O"): 1.25,
        }.get(pair, 1.30)
    return {
        ("C", "C"): 1.53,
        ("C", "N"): 1.47,
        ("C", "O"): 1.43,
        ("C", "S"): 1.82,
        ("N", "O"): 1.40,
        ("N", "S"): 1.70,
        ("O", "S"): 1.58,
    }.get(pair, 1.50)


def ideal_site_distance(kind: str) -> float:
    return {
        "positive": 3.2,
        "negative": 3.2,
        "donor": 2.9,
        "acceptor": 2.9,
        "hydrophobic": 4.0,
        "center": 0.0,
    }.get(kind, 3.4)


def build_open_connections(placed: PlacedFragment) -> List[OpenConnection]:
    connections = []
    for index, connection in enumerate(placed.fragment.connection_points):
        atom_index = connection.atom_index
        fragment_atom = placed.fragment.atoms[atom_index]
        connections.append(
            OpenConnection(
                placed_id=placed.placed_id,
                connection_index=index,
                position=placed.atom_coord(atom_index),
                direction=unit_vector(placed.rotation @ connection.direction),
                element=fragment_atom.element,
                label=f"{placed.fragment.name}.{connection.label}",
            )
        )
    return connections


def complementary_anchor_indices(fragment: MolecularFragment, site: InteractionSite) -> List[int]:
    matches = []
    for index, fragment_atom in enumerate(fragment.atoms):
        if site.kind == "positive" and fragment_atom.partial_charge < -0.15:
            matches.append(index)
        elif site.kind == "negative" and fragment_atom.partial_charge > 0.15:
            matches.append(index)
        elif site.kind == "donor" and fragment_atom.acceptor:
            matches.append(index)
        elif site.kind == "acceptor" and fragment_atom.donor:
            matches.append(index)
        elif site.kind == "hydrophobic" and fragment_atom.hydrophobic:
            matches.append(index)
    if matches:
        return matches[:3]
    if site.kind == "center":
        return [0]
    hydrophobic = [index for index, fragment_atom in enumerate(fragment.atoms) if fragment_atom.hydrophobic]
    return hydrophobic[:2] or [0]


def connection_atom(fragment: MolecularFragment, connection_index: int) -> FragmentAtom:
    return fragment.atoms[fragment.connection_points[connection_index].atom_index]


def incompatible_bond(element_a: str, element_b: str) -> bool:
    first = element_a.upper()
    second = element_b.upper()
    pair = {first, second}
    if "F" in pair and pair != {"C", "F"}:
        return True
    return pair in [{"O"}, {"N"}, {"O", "O"}]


class MolecularDesignEngine:
    def __init__(
        self,
        beam_width: int = 32,
        max_fragments: int = 4,
        max_candidates: int = 25,
        max_atoms: int = 40,
        clash_scale: float = 0.62,
        use_rdkit_conformers: bool = True,
        use_rdkit_relaxation: bool = True,
        use_graph_native_smiles: bool = True,
        pocket_mode: str = "auto",
    ):
        self.beam_width = beam_width
        self.max_fragments = max_fragments
        self.max_candidates = max_candidates
        self.max_atoms = max_atoms
        self.clash_scale = clash_scale
        self.use_rdkit_relaxation = use_rdkit_relaxation
        self.use_graph_native_smiles = use_graph_native_smiles
        self.pocket_mode = pocket_mode
        self.fragment_library = build_fragment_library(use_rdkit_conformers=use_rdkit_conformers)
        self.rotations = rotation_library()
        self.rejection_counts: Dict[str, int] = {
            "protein_clash": 0,
            "self_clash": 0,
            "pocket_escape": 0,
            "max_atoms": 0,
            "incompatible_bond": 0,
            "duplicate": 0,
        }

    def design(
        self,
        pdb_path: Path,
        chain: Optional[str] = None,
        center: Optional[np.ndarray] = None,
        radius: float = 8.0,
        residue: Optional[str] = None,
    ) -> DesignResult:
        self.rejection_counts = {key: 0 for key in self.rejection_counts}
        warnings: List[str] = []
        protein_atoms, ligand_atoms = parse_pdb_atoms(pdb_path, chain=chain)
        pocket = define_pocket(
            protein_atoms,
            ligand_atoms,
            radius=radius,
            center=center,
            residue=residue,
            pocket_mode=self.pocket_mode,
        )

        seeds = self.create_seed_assemblies(pocket)
        if not seeds:
            warnings.append("No seed placement survived steric and containment filters.")
            return DesignResult(str(pdb_path), pocket, [], dict(self.rejection_counts), warnings)

        beam = self.rank_assemblies(seeds, pocket)[: self.beam_width]
        completed = list(beam)
        for _ in range(1, self.max_fragments):
            expanded: List[MolecularAssembly] = []
            for assembly in beam:
                expanded.extend(self.expand_assembly(assembly, pocket))
            if not expanded:
                break
            beam = self.rank_assemblies(expanded, pocket)[: self.beam_width]
            completed.extend(beam)

        ranked = self.rank_assemblies(completed, pocket)
        unique = self.unique_assemblies(ranked)
        candidates = [self.candidate_dict(index + 1, assembly, pocket) for index, assembly in enumerate(unique[: self.max_candidates])]
        if not candidates:
            warnings.append("Assembly search completed but no unique candidates remained.")
        return DesignResult(str(pdb_path), pocket, candidates, dict(self.rejection_counts), warnings)

    def create_seed_assemblies(self, pocket: Pocket) -> List[MolecularAssembly]:
        assemblies: List[MolecularAssembly] = []
        seed_fragments = [fragment for fragment in self.fragment_library.values() if fragment.role == "seed"]
        sites = pocket.sites[:48]
        if all(site.kind != "center" for site in sites):
            sites.append(InteractionSite("center", pocket.center, 0.7, "geometric_center", "CENTER", 0.0))

        for fragment in seed_fragments:
            for site in sites:
                inward = unit_vector(pocket.center - site.position)
                target = pocket.center if site.kind == "center" else site.position + inward * ideal_site_distance(site.kind)
                for anchor_index in complementary_anchor_indices(fragment, site):
                    for rotation in self.rotations:
                        translation = target - rotation @ fragment.atoms[anchor_index].coord
                        placed = PlacedFragment(0, fragment, rotation, translation)
                        assembly = MolecularAssembly(
                            placed_fragments=[placed],
                            cross_bonds=[],
                            open_connections=build_open_connections(placed),
                            trace=[
                                {
                                    "object": fragment.name,
                                    "morphism": "seed_placement",
                                    "site_kind": site.kind,
                                    "site_residue": site.residue_label,
                                }
                            ],
                        )
                        valid, reason = self.validate_assembly(assembly, pocket)
                        if valid:
                            assemblies.append(assembly)
                        else:
                            self.rejection_counts[reason] += 1
        return assemblies

    def expand_assembly(self, assembly: MolecularAssembly, pocket: Pocket) -> List[MolecularAssembly]:
        expanded: List[MolecularAssembly] = []
        attachable = [fragment for fragment in self.fragment_library.values() if fragment.role in {"linker", "cap"}]
        next_id = max(placed.placed_id for placed in assembly.placed_fragments) + 1
        for open_index, source_connection in enumerate(assembly.open_connections):
            for fragment in attachable:
                if assembly.atom_count() + len(fragment.atoms) > self.max_atoms:
                    self.rejection_counts["max_atoms"] += 1
                    continue
                for target_connection_index, target_connection in enumerate(fragment.connection_points):
                    target_atom = connection_atom(fragment, target_connection_index)
                    if incompatible_bond(source_connection.element, target_atom.element):
                        self.rejection_counts["incompatible_bond"] += 1
                        continue
                    placed = self.place_attachment(next_id, source_connection, fragment, target_connection_index)
                    open_connections = [
                        connection for index, connection in enumerate(assembly.open_connections) if index != open_index
                    ]
                    for new_open in build_open_connections(placed):
                        if new_open.connection_index != target_connection_index:
                            open_connections.append(new_open)
                    cross_bond = CrossFragmentBond(
                        source_fragment_id=source_connection.placed_id,
                        source_atom_index=self.source_atom_index(assembly, source_connection),
                        target_fragment_id=placed.placed_id,
                        target_atom_index=target_connection.atom_index,
                        order=target_connection.bond_order,
                    )
                    new_assembly = MolecularAssembly(
                        placed_fragments=assembly.placed_fragments + [placed],
                        cross_bonds=assembly.cross_bonds + [cross_bond],
                        open_connections=open_connections,
                        trace=assembly.trace
                        + [
                            {
                                "object": fragment.name,
                                "morphism": "fragment_attachment",
                                "source": source_connection.label,
                                "target": f"{fragment.name}.{target_connection.label}",
                            }
                        ],
                    )
                    valid, reason = self.validate_assembly(new_assembly, pocket)
                    if valid:
                        expanded.append(new_assembly)
                    else:
                        self.rejection_counts[reason] += 1
        return expanded

    def place_attachment(
        self,
        placed_id: int,
        source_connection: OpenConnection,
        fragment: MolecularFragment,
        target_connection_index: int,
    ) -> PlacedFragment:
        target_connection = fragment.connection_points[target_connection_index]
        target_atom = fragment.atoms[target_connection.atom_index]
        length = bond_length(source_connection.element, target_atom.element, target_connection.bond_order)
        rotation = align_vectors(target_connection.direction, -source_connection.direction)
        target_anchor = source_connection.position + source_connection.direction * length
        translation = target_anchor - rotation @ target_atom.coord
        return PlacedFragment(placed_id=placed_id, fragment=fragment, rotation=rotation, translation=translation)

    def source_atom_index(self, assembly: MolecularAssembly, source_connection: OpenConnection) -> int:
        placed = next(placed for placed in assembly.placed_fragments if placed.placed_id == source_connection.placed_id)
        return placed.fragment.connection_points[source_connection.connection_index].atom_index

    def validate_assembly(self, assembly: MolecularAssembly, pocket: Pocket) -> Tuple[bool, str]:
        for _, _, _, coord in assembly.all_atoms():
            if float(np.linalg.norm(coord - pocket.center)) > pocket.radius + 2.5:
                return False, "pocket_escape"

        for _, _, ligand_atom, ligand_coord in assembly.all_atoms():
            ligand_radius = vdw_radius(ligand_atom.element)
            for protein_atom in pocket.atoms:
                protein_radius = vdw_radius(protein_atom.element)
                distance = float(np.linalg.norm(ligand_coord - protein_atom.coord))
                if distance < self.clash_scale * (ligand_radius + protein_radius):
                    return False, "protein_clash"

        ligand_atoms = assembly.all_atoms()
        bonded = self.bonded_pairs(assembly)
        for left_index in range(len(ligand_atoms)):
            left_key = (ligand_atoms[left_index][0], ligand_atoms[left_index][1])
            left_atom = ligand_atoms[left_index][2]
            left_coord = ligand_atoms[left_index][3]
            for right_index in range(left_index + 1, len(ligand_atoms)):
                right_key = (ligand_atoms[right_index][0], ligand_atoms[right_index][1])
                if left_key[0] == right_key[0] or frozenset((left_key, right_key)) in bonded:
                    continue
                right_atom = ligand_atoms[right_index][2]
                right_coord = ligand_atoms[right_index][3]
                distance = float(np.linalg.norm(left_coord - right_coord))
                threshold = 0.58 * (vdw_radius(left_atom.element) + vdw_radius(right_atom.element))
                if distance < threshold:
                    return False, "self_clash"
        return True, ""

    def bonded_pairs(self, assembly: MolecularAssembly) -> set:
        bonded = set()
        for placed in assembly.placed_fragments:
            for bond in placed.fragment.bonds:
                bonded.add(frozenset(((placed.placed_id, bond.atom_i), (placed.placed_id, bond.atom_j))))
        for bond in assembly.cross_bonds:
            bonded.add(
                frozenset(
                    (
                        (bond.source_fragment_id, bond.source_atom_index),
                        (bond.target_fragment_id, bond.target_atom_index),
                    )
                )
            )
        return bonded

    def rank_assemblies(self, assemblies: List[MolecularAssembly], pocket: Pocket) -> List[MolecularAssembly]:
        for assembly in assemblies:
            assembly.score_terms = self.score_assembly(assembly, pocket)
            assembly.score_total = float(sum(assembly.score_terms.values()))
        return sorted(assemblies, key=lambda assembly: assembly.score_total, reverse=True)

    def score_assembly(self, assembly: MolecularAssembly, pocket: Pocket) -> Dict[str, float]:
        ligand_atoms = assembly.all_atoms()
        electrostatic = self.score_electrostatics(ligand_atoms, pocket)
        hbond = self.score_hbonds(ligand_atoms, pocket)
        hydrophobic = self.score_hydrophobic(ligand_atoms, pocket)
        shape = self.score_shape(ligand_atoms, pocket)
        steric = self.score_steric_margin(ligand_atoms, pocket)
        synthetic = self.score_synthetic_sanity(assembly)
        relaxation = self.score_rdkit_relaxation(assembly) if self.use_rdkit_relaxation else 0.0
        categorical = 0.35 * len(assembly.cross_bonds) + 0.10 * len({placed.fragment.role for placed in assembly.placed_fragments})
        return {
            "steric_fit": round(steric, 4),
            "electrostatics": round(electrostatic, 4),
            "hydrogen_bonds": round(hbond, 4),
            "hydrophobic": round(hydrophobic, 4),
            "shape_fit": round(shape, 4),
            "synthetic_sanity": round(synthetic, 4),
            "rdkit_relaxation": round(relaxation, 4),
            "categorical_colimit": round(categorical, 4),
        }

    def score_electrostatics(self, ligand_atoms: List[Tuple[int, int, FragmentAtom, np.ndarray]], pocket: Pocket) -> float:
        score = 0.0
        charged_sites = [site for site in pocket.sites if site.kind in {"positive", "negative"}]
        for _, _, ligand_atom, ligand_coord in ligand_atoms:
            if abs(ligand_atom.partial_charge) < 0.15:
                continue
            for site in charged_sites:
                distance = float(np.linalg.norm(ligand_coord - site.position))
                if distance > 5.5:
                    continue
                product = ligand_atom.partial_charge * site.charge
                if product < 0:
                    score += site.strength * min(1.5, 4.0 / max(distance, 1.0))
                else:
                    score -= 0.7 * site.strength * min(1.2, 4.0 / max(distance, 1.0))
        return score

    def score_hbonds(self, ligand_atoms: List[Tuple[int, int, FragmentAtom, np.ndarray]], pocket: Pocket) -> float:
        score = 0.0
        donor_sites = [site for site in pocket.sites if site.kind == "donor"]
        acceptor_sites = [site for site in pocket.sites if site.kind == "acceptor"]
        for _, _, ligand_atom, ligand_coord in ligand_atoms:
            if ligand_atom.acceptor:
                score += self.hbond_site_score(ligand_coord, donor_sites)
            if ligand_atom.donor:
                score += self.hbond_site_score(ligand_coord, acceptor_sites)
        return score

    def hbond_site_score(self, coord: np.ndarray, sites: List[InteractionSite]) -> float:
        score = 0.0
        for site in sites:
            distance = float(np.linalg.norm(coord - site.position))
            if 2.4 <= distance <= 3.8:
                score += site.strength * (1.0 - abs(distance - 2.9) / 1.4)
        return score

    def score_hydrophobic(self, ligand_atoms: List[Tuple[int, int, FragmentAtom, np.ndarray]], pocket: Pocket) -> float:
        score = 0.0
        sites = [site for site in pocket.sites if site.kind == "hydrophobic"]
        for _, _, ligand_atom, ligand_coord in ligand_atoms:
            if not ligand_atom.hydrophobic:
                continue
            for site in sites:
                distance = float(np.linalg.norm(ligand_coord - site.position))
                if 3.2 <= distance <= 5.2:
                    score += 0.25 * site.strength * (1.0 - abs(distance - 4.1) / 2.0)
        return score

    def score_shape(self, ligand_atoms: List[Tuple[int, int, FragmentAtom, np.ndarray]], pocket: Pocket) -> float:
        distances = np.array([np.linalg.norm(coord - pocket.center) for _, _, _, coord in ligand_atoms], dtype=float)
        if len(distances) == 0:
            return 0.0
        target_mean = 0.45 * pocket.radius
        mean_distance = float(np.mean(distances))
        spread = float(np.std(distances))
        fill_score = max(0.0, 1.8 - abs(mean_distance - target_mean) / max(pocket.radius, 1.0) * 3.0)
        spread_score = max(0.0, 0.8 - abs(spread - 1.8) / max(pocket.radius, 1.0))
        return fill_score + spread_score

    def score_steric_margin(self, ligand_atoms: List[Tuple[int, int, FragmentAtom, np.ndarray]], pocket: Pocket) -> float:
        margins = []
        for _, _, ligand_atom, ligand_coord in ligand_atoms:
            for protein_atom in pocket.atoms:
                distance = float(np.linalg.norm(ligand_coord - protein_atom.coord))
                expected = 0.78 * (vdw_radius(ligand_atom.element) + vdw_radius(protein_atom.element))
                margins.append(distance - expected)
        if not margins:
            return 0.0
        min_margin = min(margins)
        return max(-2.0, min(1.5, min_margin / 2.0))

    def score_synthetic_sanity(self, assembly: MolecularAssembly) -> float:
        atoms = [atom for _, _, atom, _ in assembly.all_atoms()]
        atom_count = len(atoms)
        hetero_count = sum(1 for atom in atoms if atom.element in {"N", "O", "S", "P", "F", "CL", "BR", "I"})
        hetero_ratio = hetero_count / max(atom_count, 1)
        size_score = max(0.0, 1.0 - abs(atom_count - 18) / 30.0)
        hetero_score = max(0.0, 1.0 - abs(hetero_ratio - 0.25) * 2.0)
        cap_bonus = 0.2 if any(placed.fragment.role == "cap" for placed in assembly.placed_fragments) else 0.0
        return size_score + hetero_score + cap_bonus

    def score_rdkit_relaxation(self, assembly: MolecularAssembly) -> float:
        smiles, _ = fallback_smiles(assembly)
        if not smiles:
            return 0.0
        try:
            from rdkit import Chem
            from rdkit.Chem import AllChem

            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                return 0.0
            mol = Chem.AddHs(mol)
            params = AllChem.ETKDGv3()
            params.randomSeed = 314159
            if AllChem.EmbedMolecule(mol, params) != 0:
                return 0.0
            AllChem.UFFOptimizeMolecule(mol, maxIters=120)
            forcefield = AllChem.UFFGetMoleculeForceField(mol)
            if forcefield is None:
                return 0.0
            energy = max(0.0, float(forcefield.CalcEnergy()))
            heavy_atoms = max(1, sum(1 for atom_obj in mol.GetAtoms() if atom_obj.GetAtomicNum() > 1))
            energy_per_heavy_atom = energy / heavy_atoms
            return 1.0 / (1.0 + energy_per_heavy_atom / 15.0)
        except Exception:
            return 0.0

    def unique_assemblies(self, assemblies: List[MolecularAssembly]) -> List[MolecularAssembly]:
        unique: List[MolecularAssembly] = []
        seen = set()
        for assembly in assemblies:
            smiles, _ = fallback_smiles(assembly)
            key = (smiles, tuple(assembly.fragment_names()))
            if key in seen:
                self.rejection_counts["duplicate"] += 1
                continue
            seen.add(key)
            unique.append(assembly)
        return unique

    def candidate_dict(self, index: int, assembly: MolecularAssembly, pocket: Pocket) -> Dict:
        smiles_method = "fallback"
        rdkit_properties: Dict[str, float] = {}
        if self.use_graph_native_smiles:
            graph_smiles, graph_valid, rdkit_properties = graph_native_smiles(assembly)
        else:
            graph_smiles, graph_valid = "", False
        if graph_valid:
            smiles, validated, smiles_method = graph_smiles, True, "graph_native"
        else:
            smiles, validated = fallback_smiles(assembly)
            canonical_smiles, smiles_validated = canonicalize_smiles(smiles)
            if smiles_validated:
                smiles = canonical_smiles
                validated = True
        atoms = assembly.all_atoms()
        return {
            "candidate_id": f"MOL-{index:04d}",
            "score_total": round(float(assembly.score_total), 4),
            "score_terms": assembly.score_terms,
            "smiles": smiles,
            "smiles_validated": validated,
            "smiles_method": smiles_method,
            "rdkit_properties": rdkit_properties,
            "fragment_trace": assembly.trace,
            "fragments": assembly.fragment_names(),
            "morphism_count": len(assembly.cross_bonds),
            "atom_count": len(atoms),
            "formula": molecular_formula([atom for _, _, atom, _ in atoms]),
            "molecular_weight": round(molecular_weight([atom for _, _, atom, _ in atoms]), 3),
            "pocket_residues": pocket.residues[:80],
            "coordinates": [
                {
                    "fragment_id": placed_id,
                    "atom_index": atom_index,
                    "element": atom.element,
                    "x": round(float(coord[0]), 3),
                    "y": round(float(coord[1]), 3),
                    "z": round(float(coord[2]), 3),
                }
                for placed_id, atom_index, atom, coord in atoms
            ],
        }


FRAGMENT_SMILES = {
    "benzene": "c1ccccc1",
    "pyridine": "n1ccccc1",
    "imidazole": "c1ncc[nH]1",
    "pyrimidine": "n1cnccc1",
    "aminopyrimidine": "Nc1nccnc1",
    "pyrazine": "n1ccncc1",
    "pyrazole": "c1cn[nH]c1",
    "methylene": "C",
    "ethylene": "CC",
    "ether": "O",
    "carbonyl": "C(=O)",
    "amide": "C(=O)N",
    "urea": "NC(=O)N",
    "sulfonamide": "S(=O)(=O)N",
    "amine": "N",
    "hydroxyl": "O",
    "carboxylate": "C(=O)O",
    "methyl": "C",
    "nitrile": "C#N",
    "fluoro": "F",
}


def apply_rdkit_conformers(fragments: Dict[str, MolecularFragment]) -> Dict[str, MolecularFragment]:
    """Replace toy fragment coordinates with deterministic RDKit ETKDG conformers when possible."""
    try:
        from rdkit import Chem
        from rdkit.Chem import AllChem
    except Exception:
        return fragments

    updated = dict(fragments)
    for name, fragment in fragments.items():
        smiles = FRAGMENT_SMILES.get(name)
        if not smiles:
            continue
        try:
            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                continue
            mol = Chem.AddHs(mol)
            params = AllChem.ETKDGv3()
            params.randomSeed = 271828
            params.useSmallRingTorsions = True
            if AllChem.EmbedMolecule(mol, params) != 0:
                continue
            AllChem.UFFOptimizeMolecule(mol, maxIters=120)
            heavy_mol = Chem.RemoveHs(mol)
            if heavy_mol.GetNumAtoms() != len(fragment.atoms):
                continue
            conformer = heavy_mol.GetConformer()
            coords = np.array(
                [
                    [
                        conformer.GetAtomPosition(index).x,
                        conformer.GetAtomPosition(index).y,
                        conformer.GetAtomPosition(index).z,
                    ]
                    for index in range(heavy_mol.GetNumAtoms())
                ],
                dtype=float,
            )
            coords = coords - np.mean(coords, axis=0)
            new_atoms = []
            for index, old_atom in enumerate(fragment.atoms):
                rdkit_atom = heavy_mol.GetAtomWithIdx(index)
                new_atoms.append(
                    FragmentAtom(
                        element=rdkit_atom.GetSymbol().upper(),
                        coord=coords[index],
                        partial_charge=old_atom.partial_charge,
                        donor=old_atom.donor,
                        acceptor=old_atom.acceptor,
                        hydrophobic=old_atom.hydrophobic,
                        aromatic=old_atom.aromatic or rdkit_atom.GetIsAromatic(),
                    )
                )
            new_connections = []
            centroid = np.mean(coords, axis=0)
            for connection in fragment.connection_points:
                direction = connection.direction
                if connection.atom_index < len(coords):
                    radial = coords[connection.atom_index] - centroid
                    if np.linalg.norm(radial) > 0.1:
                        direction = unit_vector(radial)
                new_connections.append(
                    ConnectionPoint(
                        atom_index=connection.atom_index,
                        label=connection.label,
                        direction=direction,
                        bond_order=connection.bond_order,
                    )
                )
            updated[name] = MolecularFragment(
                name=fragment.name,
                atoms=tuple(new_atoms),
                bonds=fragment.bonds,
                connection_points=tuple(new_connections),
                role=fragment.role,
            )
        except Exception:
            continue
    return updated


def fallback_smiles(assembly: MolecularAssembly) -> Tuple[str, bool]:
    names = assembly.fragment_names()
    if not names:
        return "", False
    seed = names[0]
    tail = "".join(FRAGMENT_SMILES.get(name, "C") for name in names[1:])
    if seed == "benzene":
        return (f"c1ccc({tail})cc1", False) if tail else ("c1ccccc1", False)
    if seed == "pyridine":
        return (f"n1ccc({tail})cc1", False) if tail else ("n1ccccc1", False)
    if seed == "imidazole":
        return (f"c1nc({tail})c[nH]1", False) if tail else ("c1ncc[nH]1", False)
    if seed == "pyrimidine":
        return (f"n1cnc({tail})cc1", False) if tail else ("n1cnccc1", False)
    if seed == "aminopyrimidine":
        return (f"Nc1nc({tail})cnc1", False) if tail else ("Nc1nccnc1", False)
    if seed == "pyrazine":
        return (f"n1cc({tail})ncc1", False) if tail else ("n1ccncc1", False)
    if seed == "pyrazole":
        return (f"c1c({tail})n[nH]c1", False) if tail else ("c1cn[nH]c1", False)
    return FRAGMENT_SMILES.get(seed, seed) + tail, False


def _rdkit_bond_type(order: float):
    from rdkit.Chem import BondType

    if abs(order - 1.5) < 0.25:
        return BondType.AROMATIC
    if abs(order - 2.0) < 0.25:
        return BondType.DOUBLE
    if abs(order - 3.0) < 0.25:
        return BondType.TRIPLE
    return BondType.SINGLE


def graph_native_smiles(assembly: MolecularAssembly) -> Tuple[str, bool, Dict[str, float]]:
    """Build an RDKit molecule from the assembled atom/bond graph.

    Unlike fallback_smiles (which concatenates per-fragment SMILES strings by
    name), this uses the real assembled graph: every fragment atom, its
    intra-fragment bonds, and the cross-fragment bonds formed during assembly.
    Returns (canonical_smiles, valid, properties). valid is False when the
    heuristic assembly produced a chemically invalid graph (e.g. over-valent
    atoms); callers should then fall back. Honestly reporting that fraction is
    itself a signal about assembly chemistry quality.
    """
    try:
        from rdkit import Chem, RDLogger
        from rdkit.Chem import Crippen, Descriptors, Lipinski, rdMolDescriptors
    except Exception:
        return "", False, {}

    RDLogger.DisableLog("rdApp.*")  # heuristic graphs fail often; don't spam stderr

    atoms = assembly.all_atoms()
    if not atoms:
        return "", False, {}

    editable = Chem.RWMol()
    index_map: Dict[Tuple[int, int], int] = {}
    for placed_id, atom_index, fragment_atom, _coord in atoms:
        rd_atom = Chem.Atom(str(fragment_atom.element).capitalize())
        if getattr(fragment_atom, "aromatic", False):
            rd_atom.SetIsAromatic(True)
            # Pyrrole-type aromatic N (the H-bond donor in imidazole/pyrazole)
            # needs an explicit H for RDKit to kekulize the 5-membered ring.
            if rd_atom.GetSymbol() == "N" and getattr(fragment_atom, "donor", False):
                rd_atom.SetNumExplicitHs(1)
                rd_atom.SetNoImplicit(True)
        index_map[(placed_id, atom_index)] = editable.AddAtom(rd_atom)

    added: set = set()

    def link(global_i: int, global_j: int, order: float) -> None:
        key = (min(global_i, global_j), max(global_i, global_j))
        if global_i == global_j or key in added:
            return
        added.add(key)
        bond_type = _rdkit_bond_type(order)
        editable.AddBond(global_i, global_j, bond_type)
        if bond_type.name == "AROMATIC":
            editable.GetAtomWithIdx(global_i).SetIsAromatic(True)
            editable.GetAtomWithIdx(global_j).SetIsAromatic(True)

    for placed in assembly.placed_fragments:
        for bond in placed.fragment.bonds:
            i = index_map.get((placed.placed_id, bond.atom_i))
            j = index_map.get((placed.placed_id, bond.atom_j))
            if i is not None and j is not None:
                link(i, j, bond.order)

    for cross in assembly.cross_bonds:
        i = index_map.get((cross.source_fragment_id, cross.source_atom_index))
        j = index_map.get((cross.target_fragment_id, cross.target_atom_index))
        if i is not None and j is not None:
            link(i, j, cross.order)

    mol = editable.GetMol()
    try:
        Chem.SanitizeMol(mol)
        smiles = Chem.MolToSmiles(mol)
    except Exception:
        return "", False, {}
    if not smiles:
        return "", False, {}

    properties = {
        "molecular_weight": round(float(Descriptors.MolWt(mol)), 3),
        "logp": round(float(Crippen.MolLogP(mol)), 3),
        "h_bond_donors": int(Lipinski.NumHDonors(mol)),
        "h_bond_acceptors": int(Lipinski.NumHAcceptors(mol)),
        "tpsa": round(float(rdMolDescriptors.CalcTPSA(mol)), 3),
        "rings": int(rdMolDescriptors.CalcNumRings(mol)),
        "rotatable_bonds": int(rdMolDescriptors.CalcNumRotatableBonds(mol)),
        "heavy_atoms": int(mol.GetNumHeavyAtoms()),
    }
    return smiles, True, properties


def canonicalize_smiles(smiles: str) -> Tuple[str, bool]:
    try:
        from rdkit import Chem
    except Exception:
        return smiles, False
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return smiles, False
        return Chem.MolToSmiles(mol), True
    except Exception:
        return smiles, False


def molecular_formula(atoms: List[FragmentAtom]) -> str:
    counts: Dict[str, int] = {}
    for fragment_atom in atoms:
        counts[fragment_atom.element] = counts.get(fragment_atom.element, 0) + 1
    ordered = []
    for element in ("C", "H", "N", "O", "S", "P", "F", "CL", "BR", "I"):
        count = counts.pop(element, 0)
        if count:
            ordered.append(f"{element}{count if count > 1 else ''}")
    for element in sorted(counts):
        count = counts[element]
        ordered.append(f"{element}{count if count > 1 else ''}")
    return "".join(ordered)


def molecular_weight(atoms: List[FragmentAtom]) -> float:
    return sum(ATOMIC_WEIGHTS.get(atom.element, 12.0) for atom in atoms)


def write_json(result: DesignResult, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(result.to_dict(), handle, indent=2)


def write_csv(result: DesignResult, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "candidate_id",
        "score_total",
        "smiles",
        "smiles_validated",
        "fragments",
        "morphism_count",
        "atom_count",
        "formula",
        "molecular_weight",
    ]
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for candidate in result.candidates:
            writer.writerow(
                {
                    "candidate_id": candidate["candidate_id"],
                    "score_total": candidate["score_total"],
                    "smiles": candidate["smiles"],
                    "smiles_validated": candidate["smiles_validated"],
                    "fragments": "|".join(candidate["fragments"]),
                    "morphism_count": candidate["morphism_count"],
                    "atom_count": candidate["atom_count"],
                    "formula": candidate["formula"],
                    "molecular_weight": candidate["molecular_weight"],
                }
            )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Category M de novo molecular design from a protein PDB pocket"
    )
    parser.add_argument("--pdb", required=True, type=Path, help="Input protein PDB path")
    parser.add_argument("--chain", default=None, help="Optional chain ID filter")
    parser.add_argument("--center", default=None, help="Pocket center as x,y,z")
    parser.add_argument("--residue", default=None, help="Pocket residue selector such as A:123 or 123")
    parser.add_argument(
        "--pocket-mode",
        choices=["auto", "grid", "ligand", "residue", "centroid"],
        default="auto",
        help="Pocket definition strategy when --center is not supplied",
    )
    parser.add_argument("--radius", type=float, default=8.0, help="Pocket radius in Angstroms")
    parser.add_argument("--max-candidates", type=int, default=25, help="Number of ranked candidates to output")
    parser.add_argument("--beam-width", type=int, default=32, help="Beam width for categorical assembly")
    parser.add_argument("--max-fragments", type=int, default=4, help="Maximum fragments per candidate")
    parser.add_argument("--max-atoms", type=int, default=40, help="Maximum heavy atoms per candidate")
    parser.add_argument("--no-rdkit-fragments", action="store_true", help="Use built-in toy fragment coordinates")
    parser.add_argument("--no-rdkit-relax", action="store_true", help="Disable RDKit ETKDG/UFF relaxation score")
    parser.add_argument("--no-graph-smiles", action="store_true", help="Disable graph-native RDKit SMILES (use name-based fallback only)")
    parser.add_argument("--out", type=Path, default=Path("reports/design_drug_results.json"), help="JSON output path")
    parser.add_argument("--csv", dest="csv_path", type=Path, default=None, help="CSV summary output path")
    parser.add_argument("--no-csv", action="store_true", help="Disable CSV summary")
    parser.add_argument("--quiet", action="store_true", help="Suppress console summary")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        center = parse_center(args.center)
        engine = MolecularDesignEngine(
            beam_width=args.beam_width,
            max_fragments=args.max_fragments,
            max_candidates=args.max_candidates,
            max_atoms=args.max_atoms,
            use_rdkit_conformers=not args.no_rdkit_fragments,
            use_rdkit_relaxation=not args.no_rdkit_relax,
            use_graph_native_smiles=not args.no_graph_smiles,
            pocket_mode=args.pocket_mode,
        )
        result = engine.design(
            pdb_path=args.pdb,
            chain=args.chain,
            center=center,
            radius=args.radius,
            residue=args.residue,
        )
        write_json(result, args.out)
        csv_path = args.csv_path
        if csv_path is None and not args.no_csv:
            csv_path = args.out.with_suffix(".csv")
        if csv_path is not None and not args.no_csv:
            write_csv(result, csv_path)
        if not args.quiet:
            print("--- Molecular Engine Result ---")
            print(f"pdb: {args.pdb}")
            print(f"pocket_mode: {result.pocket.mode}")
            print(f"pocket_atoms: {len(result.pocket.atoms)}")
            print(f"candidates: {len(result.candidates)}")
            if result.candidates:
                top = result.candidates[0]
                print(f"top_candidate: {top['candidate_id']} score={top['score_total']} smiles={top['smiles']}")
            print(f"json: {args.out}")
            if csv_path is not None and not args.no_csv:
                print(f"csv: {csv_path}")
            if result.warnings:
                print(f"warnings: {'; '.join(result.warnings)}")
        return 0
    except Exception as exc:
        print(f"[FAIL] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
