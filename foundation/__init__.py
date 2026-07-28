# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""
Foundation Module for KOMPOSOS-IV-PHARM

Foundational mathematical structures:
- Verdict bilattice (AGREE/HOLLOW/ORPHAN/REJECT)
- Z2-graded composition
- Complex amplitude semantics
"""

from .verdict_bilattice import (
    Verdict,
    BilatticeElement,
    fold_parallel_paths,
    fold_sequential_chain,
    kan_defect,
    chain_kan_defect
)

__all__ = [
    'Verdict',
    'BilatticeElement',
    'fold_parallel_paths',
    'fold_sequential_chain',
    'kan_defect',
    'chain_kan_defect'
]
