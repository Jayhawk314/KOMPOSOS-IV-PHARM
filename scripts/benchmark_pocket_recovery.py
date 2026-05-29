#!/usr/bin/env python3
"""
Retrospective pocket / contact recovery benchmark (Validation Ladder Level 2-3).

For each co-crystal in the manifest this measures whether the engine's pocket
detector finds the real ligand-binding pocket, by comparing three pocket modes
against the bound cognate ligand as ground truth:

  - grid     : grid-cavity + hotspot detection (the method under test)
  - centroid : protein-centroid fallback (weak baseline / floor)
  - ligand   : sphere centered on the true ligand centroid (oracle / ceiling)

Metrics per structure and mode:
  - centroid_error_A : distance from predicted pocket center to the matched
                       cognate-ligand instance centroid
  - within_4A / within_6A : whether centroid_error is under those thresholds
  - contact precision / recall / f1 : predicted pocket residues vs protein
                       residues actually within contact_distance of the ligand

The headline result is whether grid beats centroid on centroid error and recall.
This proves geometry recovery; it does NOT prove binding or affinity.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = Path(__file__).resolve().parent
for path in (PROJECT_ROOT, SCRIPT_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from design_drug import PDBAtom, define_pocket, parse_pdb_atoms  # noqa: E402

DEFAULT_MANIFEST = PROJECT_ROOT / "data" / "benchmarks" / "cocrystal_small.json"
DEFAULT_TEMPLATE_DIR = PROJECT_ROOT / "data" / "cache" / "pdb_templates"
DEFAULT_OUT = PROJECT_ROOT / "reports" / "pocket_recovery_benchmark.json"

LigandGroup = Tuple[str, str, str]  # (chain_id, residue_name, residue_id)


def group_ligand_atoms(ligand_atoms: List[PDBAtom]) -> Dict[LigandGroup, List[PDBAtom]]:
    groups: Dict[LigandGroup, List[PDBAtom]] = defaultdict(list)
    for atom in ligand_atoms:
        groups[(atom.chain_id, atom.residue_name, atom.residue_id)].append(atom)
    return groups


def select_cognate_ligand(
    ligand_atoms: List[PDBAtom],
    blocklist: set,
    min_atoms: int,
) -> Tuple[Optional[str], List[List[PDBAtom]]]:
    """Return (cognate_resname, instances) where instances share that resname.

    The cognate ligand is the largest non-additive HETATM residue group; ties
    broken by resname for determinism. All instances of that resname (e.g. both
    copies in a homodimer) are returned so symmetric pockets are credited.
    """
    groups = group_ligand_atoms(ligand_atoms)
    candidates = [
        (group_key, atoms)
        for group_key, atoms in groups.items()
        if group_key[1] not in blocklist and len(atoms) >= min_atoms
    ]
    if not candidates:
        return None, []
    candidates.sort(key=lambda item: (len(item[1]), item[0][1]), reverse=True)
    cognate_resname = candidates[0][0][1]
    instances = [atoms for (key, atoms) in candidates if key[1] == cognate_resname]
    return cognate_resname, instances


def centroid(atoms: List[PDBAtom]) -> np.ndarray:
    return np.mean(np.array([atom.coord for atom in atoms], dtype=float), axis=0)


def contact_residues(
    protein_atoms: List[PDBAtom],
    ligand_instance: List[PDBAtom],
    contact_distance: float,
) -> set:
    ligand_coords = np.array([atom.coord for atom in ligand_instance], dtype=float)
    contacts = set()
    for atom in protein_atoms:
        if float(np.min(np.linalg.norm(ligand_coords - atom.coord, axis=1))) <= contact_distance:
            contacts.add(atom.residue_label)
    return contacts


def score_mode(
    protein_atoms: List[PDBAtom],
    ligand_atoms: List[PDBAtom],
    instances: List[List[PDBAtom]],
    instance_centroids: List[np.ndarray],
    radius: float,
    contact_distance: float,
    mode: str,
) -> Dict:
    if mode == "grid":
        pocket = define_pocket(protein_atoms, ligand_atoms, radius=radius, pocket_mode="grid")
    elif mode == "centroid":
        pocket = define_pocket(protein_atoms, [], radius=radius, pocket_mode="centroid")
    elif mode == "ligand":
        # Oracle: sphere centered on the largest (canonical) ligand instance.
        pocket = define_pocket(protein_atoms, [], radius=radius, center=instance_centroids[0])
    else:
        raise ValueError(f"unknown mode {mode}")

    predicted_center = np.asarray(pocket.center, dtype=float)
    predicted_residues = set(pocket.residues)

    # Match to the nearest cognate-ligand instance: credits finding either copy
    # of a symmetric pocket, while still reporting true distance.
    distances = [float(np.linalg.norm(predicted_center - c)) for c in instance_centroids]
    matched_index = int(np.argmin(distances))
    centroid_error = distances[matched_index]
    true_contacts = contact_residues(protein_atoms, instances[matched_index], contact_distance)

    overlap = predicted_residues & true_contacts
    precision = len(overlap) / len(predicted_residues) if predicted_residues else 0.0
    recall = len(overlap) / len(true_contacts) if true_contacts else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0

    return {
        "mode": mode,
        "pocket_mode_label": pocket.mode,
        "predicted_center": [round(float(v), 3) for v in predicted_center.tolist()],
        "centroid_error_A": round(centroid_error, 3),
        "within_4A": centroid_error <= 4.0,
        "within_6A": centroid_error <= 6.0,
        "matched_instance_index": matched_index,
        "num_predicted_pocket_residues": len(predicted_residues),
        "num_true_contact_residues": len(true_contacts),
        "num_overlap_residues": len(overlap),
        "contact_precision": round(precision, 3),
        "contact_recall": round(recall, 3),
        "contact_f1": round(f1, 3),
    }


def benchmark_structure(entry: Dict, manifest: Dict, template_dir: Path, radius: float) -> Dict:
    pdb_id = str(entry["pdb_id"]).upper()
    pdb_path = template_dir / f"{pdb_id}.pdb"
    base = {
        "pdb_id": pdb_id,
        "target_id": entry.get("target_id"),
        "known_drug": entry.get("known_drug"),
        "family": entry.get("family"),
    }
    if not pdb_path.exists():
        return {**base, "status": "missing_file", "path": str(pdb_path)}

    protein_atoms, ligand_atoms = parse_pdb_atoms(pdb_path, chain=None)
    blocklist = set(manifest.get("ligand_additive_blocklist", []))
    min_atoms = int(manifest.get("min_ligand_atoms", 12))
    contact_distance = float(manifest.get("contact_distance_A", 4.0))

    override = entry.get("ligand_resname")
    if override:
        instances = [atoms for key, atoms in group_ligand_atoms(ligand_atoms).items() if key[1] == override.upper()]
        cognate_resname = override.upper() if instances else None
    else:
        cognate_resname, instances = select_cognate_ligand(ligand_atoms, blocklist, min_atoms)

    if not instances:
        return {**base, "status": "no_cognate_ligand",
                "ligand_atoms_total": len(ligand_atoms),
                "note": "No non-additive HETATM group passed the size filter."}

    instance_centroids = [centroid(atoms) for atoms in instances]
    modes = {
        mode: score_mode(protein_atoms, ligand_atoms, instances, instance_centroids,
                         radius, contact_distance, mode)
        for mode in ("grid", "centroid", "ligand")
    }
    return {
        **base,
        "status": "ok",
        "protein_atoms": len(protein_atoms),
        "cognate_ligand_resname": cognate_resname,
        "cognate_ligand_instances": len(instances),
        "cognate_ligand_atoms_largest": len(instances[0]),
        "modes": modes,
    }


def _median(values: List[float]) -> Optional[float]:
    return round(statistics.median(values), 3) if values else None


def _mean(values: List[float]) -> Optional[float]:
    return round(statistics.fmean(values), 3) if values else None


def aggregate(rows: List[Dict]) -> Dict:
    ok = [row for row in rows if row.get("status") == "ok"]
    summary: Dict[str, Dict] = {}
    for mode in ("grid", "centroid", "ligand"):
        errors = [row["modes"][mode]["centroid_error_A"] for row in ok]
        recalls = [row["modes"][mode]["contact_recall"] for row in ok]
        precisions = [row["modes"][mode]["contact_precision"] for row in ok]
        f1s = [row["modes"][mode]["contact_f1"] for row in ok]
        summary[mode] = {
            "median_centroid_error_A": _median(errors),
            "frac_within_4A": round(sum(1 for e in errors if e <= 4.0) / len(errors), 3) if errors else None,
            "frac_within_6A": round(sum(1 for e in errors if e <= 6.0) / len(errors), 3) if errors else None,
            "mean_contact_recall": _mean(recalls),
            "mean_contact_precision": _mean(precisions),
            "mean_contact_f1": _mean(f1s),
        }
    lift = {}
    if summary["grid"]["median_centroid_error_A"] is not None and summary["centroid"]["median_centroid_error_A"] is not None:
        lift["median_error_reduction_A_vs_centroid"] = round(
            summary["centroid"]["median_centroid_error_A"] - summary["grid"]["median_centroid_error_A"], 3
        )
    if summary["grid"]["mean_contact_recall"] is not None and summary["centroid"]["mean_contact_recall"] is not None:
        lift["recall_lift_vs_centroid"] = round(
            summary["grid"]["mean_contact_recall"] - summary["centroid"]["mean_contact_recall"], 3
        )
    return {
        "structures_total": len(rows),
        "structures_scored": len(ok),
        "structures_skipped": [
            {"pdb_id": row["pdb_id"], "status": row["status"]}
            for row in rows if row.get("status") != "ok"
        ],
        "per_mode": summary,
        "grid_vs_centroid": lift,
        "interpretation": [
            "centroid_error compares the predicted pocket center to the nearest real cognate-ligand centroid.",
            "grid should beat centroid on error and recall for the engine to be a useful pocket finder.",
            "ligand mode is an oracle ceiling (perfectly centered), not a prediction.",
            "This is geometry recovery only. It does not measure binding, affinity, or ranking of actives vs decoys.",
        ],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Co-crystal pocket/contact recovery benchmark")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--template-dir", type=Path, default=DEFAULT_TEMPLATE_DIR)
    parser.add_argument("--radius", type=float, default=10.0, help="Pocket radius in Angstroms")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--quiet", action="store_true")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.manifest.exists():
        print(f"[FAIL] manifest not found: {args.manifest}", file=sys.stderr)
        return 1
    with args.manifest.open("r", encoding="utf-8") as handle:
        manifest = json.load(handle)

    rows: List[Dict] = []
    structures = manifest.get("structures", [])
    for index, entry in enumerate(structures, start=1):
        if not args.quiet:
            print(f"[{index}/{len(structures)}] {entry.get('pdb_id')} ({entry.get('target_id')})")
        try:
            rows.append(benchmark_structure(entry, manifest, args.template_dir, args.radius))
        except Exception as exc:  # noqa: BLE001
            rows.append({"pdb_id": entry.get("pdb_id"), "status": "error", "error": str(exc)})

    report = {
        "schema": "komposos.category_m.pocket_recovery.v1",
        "settings": {"radius": args.radius, "manifest": str(args.manifest)},
        "aggregate": aggregate(rows),
        "structures": rows,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)

    if not args.quiet:
        print("--- Pocket Recovery Summary ---")
        print(json.dumps(report["aggregate"]["per_mode"], indent=2))
        print(json.dumps(report["aggregate"]["grid_vs_centroid"], indent=2))
        print(f"report: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
