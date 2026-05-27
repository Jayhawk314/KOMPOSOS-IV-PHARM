#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""
Yoneda Distance Strategy for drug repurposing.

Scores Drug-Disease pairs by structural similarity: if Drug_X has a similar
Yoneda presheaf to a drug known to treat Disease_Y, then Drug_X is a
structural substitute.

Operates on a clean subgraph (MEASURED + ESTABLISHED evidence tiers only)
to avoid noise contamination. Uses confidence-weighted Jaccard distance
rather than binary set comparison.
"""

from __future__ import annotations

import sqlite3
from collections import defaultdict
from typing import Dict, List, Set, Tuple

from oracle.prediction import Prediction, PredictionType
from oracle.strategies import InferenceStrategy
from core.category import Category

DB_PATH = "data/drugs/tier1.db"
NON_PROTEIN_TYPES = {"Drug", "Disease", "ExternalCompound"}

# Module-level cache: the clean subgraph, fingerprints, and known treatments
# are DB-derived and do not change between LOOCV folds. Caching avoids
# rebuilding 44 times during cross-validation.
_cache: Dict[str, dict] = {}


def _get_cached(db_path: str) -> dict:
    """Return or build the shared clean subgraph, fingerprints, and treatments."""
    if db_path not in _cache:
        clean_cat = YonedaDistanceStrategy._load_clean_subgraph(db_path)
        fingerprints: Dict[str, Dict[Tuple[str, str], float]] = {}
        for obj in clean_cat.objects():
            fp: Dict[Tuple[str, str], float] = {}
            for m in clean_cat.morphisms_to(obj.name):
                key = (m.source, m.name)
                fp[key] = max(fp.get(key, 0.0), m.confidence)
            for m in clean_cat.morphisms_from(obj.name):
                key = (m.target, m.name)
                fp[key] = max(fp.get(key, 0.0), m.confidence)
            fingerprints[obj.name] = fp

        known_treatments: Dict[str, Set[str]] = defaultdict(set)
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT m.source_name, m.target_name "
            "FROM morphisms m "
            "JOIN objects src ON m.source_name = src.name "
            "JOIN objects tgt ON m.target_name = tgt.name "
            "WHERE src.type_name = 'Drug' AND tgt.type_name = 'Disease'"
        )
        for row in cursor.fetchall():
            known_treatments[row["target_name"]].add(row["source_name"])
        conn.close()

        _cache[db_path] = {
            "clean_cat": clean_cat,
            "fingerprints": fingerprints,
            "known_treatments": known_treatments,
        }
    return _cache[db_path]


class YonedaDistanceStrategy(InferenceStrategy):
    """Score Drug-Disease pairs via Yoneda distance on clean evidence."""

    name = "yoneda_distance"

    def __init__(self, category: Category, db_path: str = DB_PATH):
        super().__init__(category)
        self._db_path = db_path
        cached = _get_cached(db_path)
        self.clean_cat = cached["clean_cat"]
        self._fingerprints: Dict[str, Dict[Tuple[str, str], float]] = cached["fingerprints"]
        self._known_treatments: Dict[str, Set[str]] = cached["known_treatments"]

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    @staticmethod
    def _load_clean_subgraph(db_path: str) -> Category:
        """Load Category with only MEASURED + ESTABLISHED edges."""
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        type_map: Dict[str, str] = {}
        cursor.execute("SELECT name, type_name FROM objects")
        for row in cursor.fetchall():
            type_map[row["name"]] = row["type_name"]

        cursor.execute(
            "SELECT source_name, target_name, name, confidence "
            "FROM morphisms WHERE evidence_tier IN ('MEASURED', 'ESTABLISHED')"
        )
        edges = cursor.fetchall()
        conn.close()

        cat = Category("yoneda_clean", db_path=":memory:")
        seen: Set[str] = set()
        for edge in edges:
            for obj_name in (edge["source_name"], edge["target_name"]):
                if obj_name not in seen:
                    seen.add(obj_name)
                    cat.add(obj_name, type_name=type_map.get(obj_name, "Object"))
            cat.connect(
                edge["source_name"],
                edge["target_name"],
                name=edge["name"],
                confidence=edge["confidence"] or 1.0,
            )
        return cat

    # ------------------------------------------------------------------
    # Fingerprint & distance
    # ------------------------------------------------------------------

    def _weighted_fingerprint(
        self, obj_name: str
    ) -> Dict[Tuple[str, str], float]:
        """Yoneda presheaf as confidence-weighted (neighbor, relation) map.

        Each key is a (neighbor, morphism_name) pair. The value is the max
        confidence across all morphisms with that key, so repeated edges
        contribute only their strongest evidence.
        """
        fp: Dict[Tuple[str, str], float] = {}
        for m in self.clean_cat.morphisms_to(obj_name):
            key = (m.source, m.name)
            fp[key] = max(fp.get(key, 0.0), m.confidence)
        for m in self.clean_cat.morphisms_from(obj_name):
            key = (m.target, m.name)
            fp[key] = max(fp.get(key, 0.0), m.confidence)
        return fp

    def _weighted_jaccard(
        self,
        fp1: Dict[Tuple[str, str], float],
        fp2: Dict[Tuple[str, str], float],
    ) -> float:
        """Weighted Jaccard distance between two fingerprints.

        Uses min/max aggregation: intersection weight = sum of min per key,
        union weight = sum of max per key. Returns 0.0 for identical
        fingerprints, 1.0 for disjoint.
        """
        all_keys = set(fp1) | set(fp2)
        if not all_keys:
            return 1.0
        intersection = sum(min(fp1.get(k, 0.0), fp2.get(k, 0.0)) for k in all_keys)
        union = sum(max(fp1.get(k, 0.0), fp2.get(k, 0.0)) for k in all_keys)
        if union <= 0:
            return 1.0
        return 1.0 - intersection / union

    # ------------------------------------------------------------------
    # Strategy interface
    # ------------------------------------------------------------------

    def predict(self, source: str, target: str) -> List[Prediction]:
        """Score a Drug->Disease pair by Yoneda similarity to known treatments.

        For each drug that is known to treat the target disease, compute
        the weighted Jaccard distance on the clean subgraph. Return the
        best similarity as the prediction confidence.
        """
        src_obj = self.category.get(source)
        tgt_obj = self.category.get(target)
        if not src_obj or not tgt_obj:
            return []
        if src_obj.type_name != "Drug" or tgt_obj.type_name != "Disease":
            return []

        treating_drugs = self._known_treatments.get(target, set())
        if not treating_drugs:
            return []

        fp_source = self._fingerprints.get(source)
        if not fp_source:
            return []

        best_similarity = 0.0
        best_drug = None
        for known_drug in treating_drugs:
            if known_drug == source:
                continue
            fp_known = self._fingerprints.get(known_drug)
            if not fp_known:
                continue
            dist = self._weighted_jaccard(fp_source, fp_known)
            similarity = 1.0 - dist
            if similarity > best_similarity:
                best_similarity = similarity
                best_drug = known_drug

        if best_similarity <= 0.0 or best_drug is None:
            return []

        return [
            Prediction(
                source=source,
                target=target,
                predicted_relation="yoneda_similar",
                prediction_type=PredictionType.YONEDA_DISTANCE,
                strategy_name=self.name,
                confidence=best_similarity,
                reasoning=(
                    f"Yoneda distance {1.0 - best_similarity:.3f} from "
                    f"{best_drug} (known treatment for {target}) on "
                    f"MEASURED+ESTABLISHED subgraph"
                ),
                evidence={
                    "nearest_drug": best_drug,
                    "distance": round(1.0 - best_similarity, 4),
                    "similarity": round(best_similarity, 4),
                    "subgraph": "MEASURED+ESTABLISHED",
                },
            )
        ]
