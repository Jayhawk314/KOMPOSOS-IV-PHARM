# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""
ESMFold Structure Prediction with ZFC Verification

Predicts 3D protein structure from amino acid sequence using ESMFold,
then verifies with ZFC geometric constraints, Pfam domain annotations,
and category theory interpretation (Ricci, TDA, spectral, etc.).

Usage:
    python predict_structure.py --sequence MQIFVKTLTGKTITLE... --name ubiquitin
    python predict_structure.py --sequence MQIFV... --native pdb_native/1ubq.pdb
    python predict_structure.py --sequence MQIFV... --output results/ubiquitin.pdb
    python predict_structure.py --sequence MQIFV... --no-pfam --no-cat
"""

import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from geometry.esmfold_zfc_pipeline import ESMFoldZFCPipeline


def main():
    parser = argparse.ArgumentParser(
        description="ESMFold + ZFC + Pfam structure prediction pipeline"
    )
    parser.add_argument(
        '--sequence', type=str, required=True,
        help='Amino acid sequence (one-letter code)',
    )
    parser.add_argument(
        '--name', type=str, default='protein',
        help='Protein name for labeling (default: protein)',
    )
    parser.add_argument(
        '--native', type=str, default=None,
        help='Path to native PDB for TM-score comparison',
    )
    parser.add_argument(
        '--output', type=str, default=None,
        help='Path to save predicted PDB file',
    )
    parser.add_argument(
        '--no-pfam', action='store_true',
        help='Skip Pfam domain annotation',
    )
    parser.add_argument(
        '--no-cat', action='store_true',
        help='Skip category theory interpretation',
    )
    parser.add_argument(
        '--quiet', action='store_true',
        help='Suppress verbose output',
    )
    args = parser.parse_args()

    # Validate sequence
    valid_aa = set('ACDEFGHIKLMNPQRSTVWY')
    seq_upper = args.sequence.upper().strip()
    invalid = set(seq_upper) - valid_aa
    if invalid:
        print(f"[FAIL] Invalid amino acids in sequence: {invalid}")
        sys.exit(1)

    pipeline = ESMFoldZFCPipeline(
        use_category_theory=not args.no_cat,
        use_pfam=not args.no_pfam,
        verbose=not args.quiet,
    )

    result = pipeline.predict_and_verify(
        sequence=seq_upper,
        protein_name=args.name,
        native_pdb_path=Path(args.native) if args.native else None,
        output_pdb=Path(args.output) if args.output else None,
    )

    # Print machine-readable summary
    print()
    print("--- RESULT ---")
    print(f"protein: {args.name}")
    print(f"length: {len(seq_upper)}")
    print(f"mean_plddt: {result.mean_plddt:.1f}")
    print(f"confidence_class: {result.confidence_class}")
    if result.verification:
        print(f"zfc_valid: {result.verification.is_valid}")
        print(f"zfc_violations: {result.verification.num_violations}")
    if result.tm_score is not None:
        print(f"tm_score: {result.tm_score:.3f}")
    if result.rmsd is not None:
        print(f"rmsd: {result.rmsd:.2f}")
    print(f"stages_completed: {result.stages_completed}")
    print(f"total_time_s: {result.total_time_s:.1f}")


if __name__ == "__main__":
    main()
