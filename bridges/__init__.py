# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""
Orion-KOMPOSOS-COG-OPTIMUS Bridge Plugins

Integrates the four-layer architecture:
- Orion (application framework)
- KOMPOSOS-IV (mathematical runtime)
- COG (cognitive co-processor)
- OPTIMUS (categorical gradient descent / self-refinement)
"""

__version__ = "0.3.0"

from .cog_reasoning import CogReasoningPlugin
from .knowledge_manager import KnowledgeManagerPlugin
from .session_manager import SessionManagerPlugin
from .optimus_plugin import OptimusPlugin
from .telemetry_plugin import TelemetryPlugin
from .infinity_cosmos_plugin import InfinityCosmosPlugin

__all__ = [
    "CogReasoningPlugin",
    "KnowledgeManagerPlugin",
    "SessionManagerPlugin",
    "OptimusPlugin",
    "TelemetryPlugin",
    "InfinityCosmosPlugin",
]
