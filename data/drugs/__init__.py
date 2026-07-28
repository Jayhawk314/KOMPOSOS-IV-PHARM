# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""Drug repurposing data module for KOMPOSOS-III."""

from .drug_network import get_drug_network, get_holdout_edges, get_stats
from .loader import create_drug_store
