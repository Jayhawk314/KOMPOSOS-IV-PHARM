# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""
Bio Domain for KOMPOSOS-IV-PHARM

Provides integration with KOMPOSOS-III biological data:
- Drug-Protein-Disease networks
- Protein-Protein Interactions
- Spatial biology data
"""

from .loader import BioDomainLoader, load_bio_domain

__all__ = ['BioDomainLoader', 'load_bio_domain']
