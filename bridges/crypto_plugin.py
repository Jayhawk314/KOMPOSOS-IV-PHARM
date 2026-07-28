# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""
Crypto Plugin for Orion

Exposes categorical cryptography as an Orion capability for COG's
security verification tier.

This activates previously dead code: categorical/crypto_category.py
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Try to import Orion (may not be available in all contexts)
try:
    import sys
    import os
    sys.path.insert(0, os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'orion-main', 'src'
    ))
    from orion_core import Plugin
    from orion_core.plugin import on, hook
    HAS_ORION = True
except ImportError:
    HAS_ORION = False
    class Plugin:
        def __init__(self, core, **kwargs):
            self.core = core
            self.name = kwargs.get('name', 'unknown')
    def on(event):
        def decorator(fn):
            return fn
        return decorator
    def hook(event, priority=10):
        def decorator(fn):
            return fn
        return decorator


class CryptoPlugin(Plugin):
    """
    Bridge categorical cryptography to Orion as a capability.

    Capabilities provided:
    - crypto_analysis: Yoneda-based vulnerability detection
    - key_similarity: Structural similarity of cryptographic keys

    Events published:
    - crypto.vulnerability_detected: Key vulnerability found
    """

    def __init__(self, core, category=None, db_path=":memory:"):
        super().__init__(
            core,
            name="crypto",
            version="0.1.0",
            description="Categorical cryptographic vulnerability detection",
            provides={"crypto_analysis", "key_similarity"},
            events_published={"crypto.vulnerability_detected"},
        )

        if category is None:
            from core.category import Category
            self.category = Category(db_path=db_path)
        else:
            self.category = category

        self._analyzer = None

    async def on_start(self):
        logger.info("CryptoPlugin started")

    def analyze_keys(self, keys: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze cryptographic keys for structural vulnerabilities.

        Uses Yoneda lemma on the collection of keys to detect
        subcategory vulnerabilities.

        Args:
            keys: List of key descriptions with modulus, exponent, key_size.

        Returns:
            Analysis with vulnerability scores.
        """
        try:
            from categorical.crypto_category import (
                CryptoCategoryBuilder, YonedaCryptoAnalyzer
            )

            builder = CryptoCategoryBuilder()
            for key_data in keys:
                from categorical.crypto_category import CryptoKey
                key = CryptoKey(
                    modulus=key_data.get("modulus", 0),
                    exponent=key_data.get("exponent", 0),
                    key_size=key_data.get("key_size", 0),
                    source=key_data.get("source", "unknown"),
                )
                builder.add_key(key)

            category = builder.build_morphisms()
            analyzer = YonedaCryptoAnalyzer()
            return analyzer.analyze_key_collection(category)

        except ImportError:
            return {"error": "crypto_category module not available"}

    def find_vulnerable_keys(self, keys: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Find keys that are structurally vulnerable.

        Returns:
            List of vulnerable key descriptions with reasons.
        """
        analysis = self.analyze_keys(keys)
        if "vulnerabilities" in analysis:
            return analysis["vulnerabilities"]
        return []
