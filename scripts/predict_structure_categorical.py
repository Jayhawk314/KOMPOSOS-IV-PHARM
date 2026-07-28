# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""
Categorical Fragment Assembly -- CLI Entry Point

Predict 3D protein structure via category-theoretic fragment assembly:
  Sequence -> Pfam domains -> Motif matching -> Fragment category
  -> Kan extension gap filling -> Assembly -> ZFC verification -> Energy refinement

Usage:
  python predict_structure_categorical.py --sequence NLYIQWLKDGGPSSGRPPPS --name trp_cage
  python predict_structure_categorical.py --sequence NLYIQWLKDGGPSSGRPPPS --name trp_cage --native pdb_native/1l2y.pdb
"""

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import numpy as np

from geometry.fragment_category import FragmentAssembler, FragmentAssemblyResult


def main():
    parser = argparse.ArgumentParser(
        description="Categorical Fragment Assembly for 3D Structure Prediction"
    )
    parser.add_argument("--sequence", required=True, help="Amino acid sequence")
    parser.add_argument("--name", default="protein", help="Protein name")
    parser.add_argument("--output", default=None, help="Output PDB path")
    parser.add_argument("--native", default=None, help="Native PDB for TM-score comparison")
    parser.add_argument("--no-energy", action="store_true", help="Skip energy refinement")
    parser.add_argument("--no-zfc", action="store_true", help="Skip ZFC verification")
    parser.add_argument("--no-esm2", action="store_true", help="Skip ESM-2 contact-guided folding")
    args = parser.parse_args()

    sequence = args.sequence.upper().strip()
    protein_name = args.name

    print("=" * 70)
    print("KOMPOSOS-III CATEGORICAL FRAGMENT ASSEMBLY")
    print("=" * 70)
    print(f"Protein: {protein_name}")
    print(f"Sequence: {sequence[:50]}{'...' if len(sequence) > 50 else ''}")
    print(f"Length: {len(sequence)} residues")
    print()

    t0 = time.time()

    assembler = FragmentAssembler(
        use_energy=not args.no_energy,
        use_zfc=not args.no_zfc,
        use_esm2_contacts=not args.no_esm2,
    )

    result = assembler.predict_structure(sequence, protein_name)

    elapsed = time.time() - t0

    # Print assembly log
    print()
    print("Assembly Log:")
    for line in result.assembly_log:
        print(f"  {line}")
    print()

    # Print summary
    print("=" * 70)
    print("RESULTS")
    print("=" * 70)
    print(f"Fragments used: {result.fragments_used}")
    print(f"Gaps filled (Kan extension): {result.gaps_filled}")
    print(f"Coverage: {result.coverage:.1%}")
    if result.energy is not None:
        print(f"Energy: {result.energy:.2f}")
    if result.zfc_result is not None:
        valid_str = "VALID" if result.zfc_result.is_valid else "INVALID"
        print(f"ZFC verification: {valid_str} ({result.zfc_result.num_violations} violations)")
    print(f"Time: {elapsed:.1f}s")

    # Save PDB
    output_path = args.output
    if output_path is None:
        output_path = f"predicted_{protein_name}_categorical.pdb"
    output_path = Path(output_path)
    result.to_pdb(output_path)
    print(f"PDB saved: {output_path}")

    # Compare to native if provided
    if args.native:
        _compare_to_native(result.coordinates, sequence, args.native, protein_name)

    print()
    print("Category-theoretic interpretation:")
    cat = result.fragment_category
    print(f"  Objects (fragments): {len(cat.fragments)}")
    print(f"  Morphisms (spatial transforms): {len(cat.morphisms)}")
    print(f"  Kan-extended loops: {result.gaps_filled}")
    print("=" * 70)


def _compare_to_native(pred_coords, sequence, native_pdb_path, protein_name):
    """Compare predicted coordinates to native PDB structure via TM-score."""
    native_path = Path(native_pdb_path)
    if not native_path.exists():
        print(f"\n[WARN] Native PDB not found: {native_path}")
        return

    # Parse native CA coordinates
    native_coords = _read_pdb_ca(native_path)
    if native_coords is None:
        print(f"\n[WARN] Could not parse native PDB: {native_path}")
        return

    # Align lengths
    n_pred = len(pred_coords)
    n_native = len(native_coords)
    n_common = min(n_pred, n_native)

    if n_common < 5:
        print(f"\n[WARN] Too few residues for comparison: {n_common}")
        return

    pred = pred_coords[:n_common]
    native = native_coords[:n_common]

    # Try tmtools for TM-score
    try:
        import tmtools
        res = tmtools.tm_align(pred, native, sequence[:n_common], sequence[:n_common])
        print(f"\nComparison to native ({native_path.name}):")
        print(f"  TM-score: {res.tm_norm_chain2:.3f}")
        print(f"  RMSD: {res.rmsd:.2f} A")
        return
    except ImportError:
        pass

    # Fallback: compute RMSD only
    # Center both
    pred_c = pred - pred.mean(axis=0)
    native_c = native - native.mean(axis=0)
    rmsd = np.sqrt(np.mean(np.sum((pred_c - native_c) ** 2, axis=1)))
    print(f"\nComparison to native ({native_path.name}):")
    print(f"  RMSD (no alignment): {rmsd:.2f} A")
    print("  (Install tmtools for TM-score: pip install tmtools)")


def _read_pdb_ca(pdb_path):
    """Read CA coordinates from a PDB file."""
    coords = []
    with open(pdb_path) as f:
        for line in f:
            if line.startswith("ENDMDL"):
                break
            if line.startswith("ATOM") and " CA " in line:
                try:
                    x = float(line[30:38])
                    y = float(line[38:46])
                    z = float(line[46:54])
                    coords.append([x, y, z])
                except (ValueError, IndexError):
                    continue
    if not coords:
        return None
    return np.array(coords)


if __name__ == "__main__":
    main()
