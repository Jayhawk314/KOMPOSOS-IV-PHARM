# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""
KOMPOSOS-IV-COG: Cognitive Co-processor for AI Agents

Category-theoretic knowledge layer exposed as an MCP server.
Uses the KOMPOSOS-IV math core for structural assurance,
consistency verification, and transparent reasoning.

Usage:
    # As MCP server (stdio transport)
    python -m cog.server

    # Programmatic
    from cog.engine import CogEngine
    from cog.session import CogSession

    session = CogSession()
    engine = CogEngine(session)
"""

__version__ = "0.2.0"

from .schema import (
    CogConcept,
    CogRelation,
    CogClaim,
    CheckResult,
    CoherenceResult,
    EnergyResult,
    ConceptType,
    RelationType,
    VerificationStatus,
)
from .session import CogSession
from .engine import CogEngine
