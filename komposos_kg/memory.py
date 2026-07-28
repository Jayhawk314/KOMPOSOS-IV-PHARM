# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""KGMemory — verified knowledge-graph memory with honesty gates.

The graph is common; the value is the two gates around it:
    remember()        -> a verifier (real COG, or stub) judges a fact BEFORE storing
    recall()          -> returns only verified facts, and LOGS what was retrieved
    explain_action()  -> checks the agent only cited facts it actually recalled
    suggest_path()    -> OPTIMUS proposes bridging concepts when a link is missing
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Tuple

from .honesty import (ReasoningStep, ReasoningTrace, ClaimedStep, Statement,
                      check_sincerity, SincerityResult)


@dataclass
class Edge:
    subject: str
    relation: str
    object: str
    source: str = ""
    evidence: str = ""
    verdict: str = "AGREE"          # AGREE | HOLLOW | REJECT
    reason: str = ""

    @property
    def id(self) -> str:
        return f"{self.subject}|{self.relation}|{self.object}"


@dataclass
class RememberResult:
    stored: bool
    verdict: str
    edge_id: str
    reason: str


Verifier = Callable[[Edge, List[Edge]], Tuple[str, str]]


def _stub_verifier(edge: Edge, existing: List[Edge]) -> Tuple[str, str]:
    """Used only when no real COG is available. Flags unevidenced facts."""
    if not (edge.source or edge.evidence):
        return "HOLLOW", "no source/evidence — unsupported (stub; plug in COG)"
    return "AGREE", "evidenced (stub verifier)"


class KGMemory:
    def __init__(self, verifier: Optional[Verifier] = None, *,
                 optimus=None, quarantine_hollow: bool = True):
        self._edges: Dict[str, Edge] = {}
        self._verify = verifier or _stub_verifier
        self._optimus = optimus
        self._quarantine = quarantine_hollow
        self._recall_log: Dict[str, set] = {}

    # 1 ── write gate ─────────────────────────────────────────────────────────
    def remember(self, subject, relation, object, *, source="", evidence=""):
        edge = Edge(subject, relation, object, source, evidence)
        verdict, reason = self._verify(edge, list(self._edges.values()))
        edge.verdict, edge.reason = verdict, reason
        if verdict == "REJECT":
            return RememberResult(False, verdict, edge.id, reason)
        if verdict == "HOLLOW" and not self._quarantine:
            return RememberResult(False, verdict, edge.id, reason)
        self._edges[edge.id] = edge
        return RememberResult(True, verdict, edge.id, reason)

    # 2 ── logged retrieval (verified only by default) ─────────────────────────
    def recall(self, subject=None, relation=None, object=None, *,
               agent="default", include_unverified=False) -> List[Edge]:
        hits = []
        for e in self._edges.values():
            if subject and e.subject != subject:
                continue
            if relation and e.relation != relation:
                continue
            if object and e.object != object:
                continue
            if e.verdict != "AGREE" and not include_unverified:
                continue
            hits.append(e)
        self._recall_log.setdefault(agent, set()).update(e.id for e in hits)
        return hits

    # 3 ── read-only check ─────────────────────────────────────────────────────
    def verify(self, subject, relation, object, *, source="", evidence="") -> str:
        v, _ = self._verify(Edge(subject, relation, object, source, evidence),
                            list(self._edges.values()))
        return v

    # 4 ── honesty gate ─────────────────────────────────────────────────────────
    def explain_action(self, action: str, cited_edge_ids: List[str], *,
                       agent="default") -> SincerityResult:
        # causal=False on purpose: citing a RELEVANT SUBSET of what you recalled
        # is fine. The only dishonesty we flag is citing a fact you never
        # recalled (a FABRICATED step). We do not demand every recalled fact be cited.
        recalled = self._recall_log.get(agent, set())
        claimed = [ClaimedStep(eid, f"cite:{eid}") for eid in cited_edge_ids]
        actual = [ReasoningStep(eid, f"cite:{eid}", causal=False) for eid in recalled]
        return check_sincerity(ReasoningTrace(actual, conclusion=action),
                               Statement(claimed, claimed_conclusion=action))

    # 5 ── OPTIMUS gap-filling ───────────────────────────────────────────────────
    def suggest_path(self, subject: str, object: str, depth: int = 3) -> List[str]:
        """When a direct link is missing/weak, OPTIMUS proposes intermediate
        concepts B such that subject -> B -> object. [] if OPTIMUS absent."""
        if self._optimus is None:
            return []
        try:
            return self._optimus.discover_intermediates(subject, object, depth=depth)
        except Exception:
            return []

    def why(self, edge_id: str) -> Optional[Dict[str, str]]:
        e = self._edges.get(edge_id)
        if not e:
            return None
        return {"fact": edge_id, "verdict": e.verdict, "reason": e.reason,
                "source": e.source, "evidence": e.evidence}
