# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""
Spatial biology integration module for KOMPOSOS-III.

Provides adapters for spatial transcriptomics platforms:
- CosMx (NanoString)
- Visium (10x Genomics)
- MERFISH (Vizgen)
"""

from .cosmx_adapter import CosMxAdapter
from .ligand_receptor_db import build_ligand_receptor_database

__all__ = ['CosMxAdapter', 'build_ligand_receptor_database']
