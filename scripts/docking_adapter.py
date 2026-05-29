"""AutoDock Vina docking adapter (Milestone 4 — downstream verifier).

The Category M engine proposes a pocket and candidate molecules; this adapter
hands them to AutoDock Vina to estimate binding and a docked pose. It is
deliberately graceful: if the Vina binary or the meeko prep tools are missing,
calls raise DockingUnavailable so callers can skip rather than crash.

Setup (see docs/DOCKING_SETUP.md):
  - Vina binary: download from the AutoDock-Vina releases, put it on PATH, set
    the VINA_BINARY env var, or drop it at tools/vina/vina.exe in the repo.
  - Prep tools: pip install meeko gemmi rdkit  (provides mk_prepare_receptor /
    mk_prepare_ligand console scripts).

Validated end-to-end on 1M17 (EGFR/erlotinib): receptor prep, ligand prep, and
a Vina run boxed on the engine-detected pocket placed the ligand 4.2 A from the
crystal pose at -7.1 kcal/mol.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BOX = 22.5


class DockingError(RuntimeError):
    """A docking step ran but failed (bad input, prep error, vina error)."""


class DockingUnavailable(DockingError):
    """A required external tool (vina binary or meeko script) is missing."""


def find_vina(explicit: Optional[str] = None) -> Optional[str]:
    """Locate the Vina binary: explicit arg, VINA_BINARY env, PATH, then tools/."""
    for candidate in (explicit, os.environ.get("VINA_BINARY")):
        if candidate and Path(candidate).exists():
            return str(candidate)
    for name in ("vina", "vina.exe"):
        found = shutil.which(name)
        if found:
            return found
    local = REPO_ROOT / "tools" / "vina" / ("vina.exe" if os.name == "nt" else "vina")
    return str(local) if local.exists() else None


def _meeko_script(name: str) -> str:
    """Resolve a meeko console script next to the active interpreter, else PATH."""
    scripts_dir = Path(sys.executable).parent / "Scripts"
    for suffix in (".exe", ""):
        candidate = scripts_dir / f"{name}{suffix}"
        if candidate.exists():
            return str(candidate)
    found = shutil.which(name)
    if found:
        return found
    raise DockingUnavailable(f"meeko script '{name}' not found (pip install meeko gemmi)")


def write_protein_only_pdb(pdb_path: Path, out_path: Path) -> Path:
    """Strip everything but ATOM records so only the rigid receptor remains."""
    lines = [
        line for line in Path(pdb_path).read_text(encoding="utf-8", errors="ignore").splitlines()
        if line.startswith("ATOM")
    ]
    if not lines:
        raise DockingError(f"no ATOM records in {pdb_path}")
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out_path


def prepare_receptor(pdb_path: Path, out_basename: Path, default_altloc: str = "A") -> Path:
    """Build a rigid receptor PDBQT from a protein PDB via mk_prepare_receptor."""
    script = _meeko_script("mk_prepare_receptor")
    protein_pdb = out_basename.with_name(out_basename.name + "_protein.pdb")
    write_protein_only_pdb(pdb_path, protein_pdb)
    cmd = [
        script, "--read_pdb", str(protein_pdb), "-o", str(out_basename), "-p",
        "--allow_bad_res", "--default_altloc", default_altloc,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    pdbqt = Path(str(out_basename) + ".pdbqt")
    if not pdbqt.exists():
        raise DockingError(f"receptor prep failed for {pdb_path.name}: {result.stderr[-500:]}")
    return pdbqt


def prepare_ligand(smiles: str, out_pdbqt: Path, seed: int = 42) -> Path:
    """Embed a 3D conformer from SMILES and write a ligand PDBQT via mk_prepare_ligand."""
    try:
        from rdkit import Chem, RDLogger
        from rdkit.Chem import AllChem
    except Exception as exc:  # noqa: BLE001
        raise DockingUnavailable("RDKit is required for ligand prep") from exc
    RDLogger.DisableLog("rdApp.*")
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise DockingError(f"unparseable SMILES: {smiles}")
    mol = Chem.AddHs(mol)
    params = AllChem.ETKDGv3()
    params.randomSeed = seed
    if AllChem.EmbedMolecule(mol, params) != 0:
        raise DockingError(f"3D embedding failed for {smiles}")
    AllChem.UFFOptimizeMolecule(mol, maxIters=200)
    sdf = out_pdbqt.with_suffix(".sdf")
    Chem.MolToMolFile(mol, str(sdf))
    script = _meeko_script("mk_prepare_ligand")
    result = subprocess.run([script, "-i", str(sdf), "-o", str(out_pdbqt)], capture_output=True, text=True)
    if not Path(out_pdbqt).exists():
        raise DockingError(f"ligand prep failed for {smiles}: {result.stderr[-300:]}")
    return out_pdbqt


def parse_vina_affinity(stdout: str) -> Optional[float]:
    """Pull the mode-1 affinity (kcal/mol) from Vina's stdout table."""
    for line in stdout.splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[0] == "1":
            try:
                return float(parts[1])
            except ValueError:
                continue
    return None


def parse_first_pose(out_pdbqt: Path) -> np.ndarray:
    """Heavy-atom coordinates of the top-ranked docked pose (first MODEL)."""
    coords: List[List[float]] = []
    in_model = False
    for line in Path(out_pdbqt).read_text(encoding="utf-8", errors="ignore").splitlines():
        if line.startswith("MODEL"):
            in_model, coords = True, []
        elif line.startswith("ENDMDL"):
            break
        elif in_model and line.startswith(("ATOM", "HETATM")):
            coords.append([float(line[30:38]), float(line[38:46]), float(line[46:54])])
    return np.array(coords, dtype=float)


def run_vina(
    receptor_pdbqt: Path,
    ligand_pdbqt: Path,
    center: Sequence[float],
    size: float = DEFAULT_BOX,
    exhaustiveness: int = 8,
    seed: int = 42,
    out_pdbqt: Optional[Path] = None,
    vina_binary: Optional[str] = None,
) -> Dict:
    """Run a Vina docking and return affinity + top-pose coordinates."""
    vina = find_vina(vina_binary)
    if vina is None:
        raise DockingUnavailable("Vina binary not found (set VINA_BINARY or place tools/vina/vina.exe)")
    out_pdbqt = out_pdbqt or Path(ligand_pdbqt).with_name("dock_out.pdbqt")
    cmd = [
        vina, "--receptor", str(receptor_pdbqt), "--ligand", str(ligand_pdbqt),
        "--center_x", f"{center[0]:.3f}", "--center_y", f"{center[1]:.3f}", "--center_z", f"{center[2]:.3f}",
        "--size_x", str(size), "--size_y", str(size), "--size_z", str(size),
        "--exhaustiveness", str(exhaustiveness), "--seed", str(seed), "--out", str(out_pdbqt),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    affinity = parse_vina_affinity(result.stdout)
    if affinity is None or not Path(out_pdbqt).exists():
        raise DockingError(f"vina run failed: {(result.stderr or result.stdout)[-400:]}")
    pose = parse_first_pose(out_pdbqt)
    return {
        "affinity_kcal_per_mol": round(affinity, 3),
        "pose_centroid": [round(float(v), 3) for v in pose.mean(axis=0)],
        "pose_atoms": int(len(pose)),
        "box_center": [round(float(v), 3) for v in center],
        "box_size": size,
        "out_pdbqt": str(out_pdbqt),
        "_pose_coords": pose,
    }


def dock_smiles_into_pocket(
    pdb_path: Path,
    smiles: str,
    center: Sequence[float],
    workdir: Optional[Path] = None,
    size: float = DEFAULT_BOX,
    exhaustiveness: int = 8,
    seed: int = 42,
    reuse_receptor: Optional[Path] = None,
) -> Dict:
    """Full pipeline: prep receptor + ligand, run Vina in a box at `center`.

    `reuse_receptor` lets a caller prep the receptor once and dock many ligands.
    Raises DockingUnavailable if tools are missing, DockingError on prep/run failure.
    """
    workdir = Path(workdir or (REPO_ROOT / "tools" / "dock_tmp"))
    workdir.mkdir(parents=True, exist_ok=True)
    stem = Path(pdb_path).stem
    receptor = reuse_receptor or prepare_receptor(pdb_path, workdir / f"{stem}_receptor")
    ligand = prepare_ligand(smiles, workdir / f"{stem}_ligand.pdbqt", seed=seed)
    result = run_vina(receptor, ligand, center, size=size, exhaustiveness=exhaustiveness, seed=seed,
                      out_pdbqt=workdir / f"{stem}_dock_out.pdbqt")
    result["receptor_pdbqt"] = str(receptor)
    result["smiles"] = smiles
    return result
