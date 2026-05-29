#!/usr/bin/env python3
"""Dock a candidate SMILES into a protein pocket with AutoDock Vina.

Ties the Category M pocket detector to docking: by default the docking box is
centered on the engine-detected pocket (the same largest-cavity detector used by
the pocket-recovery benchmark), so "engine proposes the pocket, Vina disposes".
Supply --center or --residue to override. If a bound ligand is present in the
PDB, the report also includes the docked-pose distance to that crystal ligand.

Examples:
  python scripts/dock_candidate.py --pdb data/cache/pdb_templates/1M17.pdb \
      --smiles "C#Cc1cccc(Nc2ncnc3cc(OCCOC)c(OCCOC)cc23)c1"
  python scripts/dock_candidate.py --pdb target.pdb --smiles "..." --residue A:797
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Optional, Sequence

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
for path in (PROJECT_ROOT, PROJECT_ROOT / "scripts"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from design_drug import define_pocket, parse_center, parse_pdb_atoms  # noqa: E402
from docking_adapter import (  # noqa: E402
    DockingUnavailable,
    dock_smiles_into_pocket,
    find_vina,
)


def cognate_ligand_centroid(ligand_atoms) -> Optional[np.ndarray]:
    if not ligand_atoms:
        return None
    groups = defaultdict(list)
    for atom in ligand_atoms:
        groups[(atom.chain_id, atom.residue_name, atom.residue_id)].append(atom)
    largest = max(groups.values(), key=len)
    return np.mean([atom.coord for atom in largest], axis=0)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Dock a SMILES into a protein pocket with Vina")
    parser.add_argument("--pdb", type=Path, required=True)
    parser.add_argument("--smiles", required=True)
    parser.add_argument("--center", default=None, help="Box center x,y,z (overrides pocket detection)")
    parser.add_argument("--residue", default=None, help="Center on a residue, e.g. A:797")
    parser.add_argument("--radius", type=float, default=10.0, help="Pocket detection radius")
    parser.add_argument("--size", type=float, default=22.5, help="Docking box edge (Angstrom)")
    parser.add_argument("--exhaustiveness", type=int, default=8)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--json", action="store_true", help="Emit JSON only")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    if find_vina() is None:
        print("[FAIL] Vina binary not found. See docs/DOCKING_SETUP.md "
              "(set VINA_BINARY or place tools/vina/vina.exe).", file=sys.stderr)
        return 2

    protein_atoms, ligand_atoms = parse_pdb_atoms(args.pdb, chain=None)
    explicit_center = parse_center(args.center)
    pocket = define_pocket(
        protein_atoms, ligand_atoms, radius=args.radius,
        center=explicit_center, residue=args.residue,
        pocket_mode="grid" if (explicit_center is None and args.residue is None) else "auto",
    )
    center = np.asarray(pocket.center, dtype=float)

    try:
        result = dock_smiles_into_pocket(
            args.pdb, args.smiles, center,
            size=args.size, exhaustiveness=args.exhaustiveness, seed=args.seed,
        )
    except DockingUnavailable as exc:
        print(f"[FAIL] docking tools unavailable: {exc}", file=sys.stderr)
        return 2

    pose_centroid = np.asarray(result["pose_centroid"], dtype=float)
    report = {
        "pdb": str(args.pdb),
        "smiles": args.smiles,
        "pocket_mode": pocket.mode,
        "box_center": result["box_center"],
        "affinity_kcal_per_mol": result["affinity_kcal_per_mol"],
        "pose_centroid": result["pose_centroid"],
        "pose_to_box_center_A": round(float(np.linalg.norm(pose_centroid - center)), 3),
    }
    crystal = cognate_ligand_centroid(ligand_atoms)
    if crystal is not None:
        report["bound_ligand_present"] = True
        report["pose_to_crystal_ligand_A"] = round(float(np.linalg.norm(pose_centroid - crystal)), 3)
        report["detected_center_to_crystal_A"] = round(float(np.linalg.norm(center - crystal)), 3)

    result.pop("_pose_coords", None)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"Affinity: {report['affinity_kcal_per_mol']} kcal/mol")
        print(f"Pocket mode: {pocket.mode.split(':')[0]}")
        print(f"Box center: {report['box_center']}")
        print(f"Pose centroid: {report['pose_centroid']} ({report['pose_to_box_center_A']} A from box center)")
        if crystal is not None:
            print(f"Detected center -> crystal ligand: {report['detected_center_to_crystal_A']} A")
            print(f"Docked pose -> crystal ligand: {report['pose_to_crystal_ligand_A']} A")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
