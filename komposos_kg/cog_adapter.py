# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""Wires a repo's REAL COG (dual ZFC/CAT engine) and OPTIMUS into KGMemory.

Graceful: if the host repo has no COG/OPTIMUS importable, build_memory falls
back to the stub verifier so the package still works (just without the math gate).

COG semantics used here (honest):
  The dual engine's delta_type is AGREE / ORPHAN / HOLLOW / REJECT. We do NOT
  force every new fact to be COG-derivable — that would reject valid new
  observations. Instead:
    • EVIDENCED facts (have source/evidence) are accepted as observations; COG
      only annotates them.
    • UNEVIDENCED facts (inferences with no source) are GATED by COG:
        AGREE/ORPHAN -> store (graph or logic supports it)
        HOLLOW       -> quarantine (structural pattern, not logically proven)
        REJECT       -> refuse (nothing supports an unevidenced claim)
"""
from __future__ import annotations

from typing import List, Optional, Tuple

from .memory import KGMemory, Edge


class CogVerifier:
    """Callable verifier backed by the real dual ZFC/CAT engine over a Category.
    Accepted facts are also written into the Category so later queries (and
    OPTIMUS) build on them."""

    def __init__(self, category=None, domain: str = "memory",
                 content_verifier=None):
        from core.category import Category
        from zfc.store_adapter import StoreAdapter
        from zfc.bridge import DualEngineBridge
        self.category = category or Category(db_path=":memory:")
        self.bridge = DualEngineBridge(StoreAdapter(self.category),
                                       category=self.category)
        self.domain = domain
        # Optional callable (edge, existing) -> (verdict, reason) that INSPECTS
        # the evidence content. Without it, an evidenced fact is accepted as an
        # observation WITHOUT reading the evidence (and the reason says so).
        self.content_verifier = content_verifier

    def __call__(self, edge: Edge, existing: List[Edge]) -> Tuple[str, str]:
        self.category.add(edge.subject)
        self.category.add(edge.object)
        res = self.bridge.query(edge.subject, edge.object, edge.relation,
                                domain=self.domain, record=False)
        dt = res.delta_type.name
        if edge.source or edge.evidence:
            # FIX: an evidenced fact used to be auto-AGREE regardless of whether
            # the evidence supports the relation (COG's verdict was discarded).
            # If a content verifier is supplied, actually read the evidence.
            if self.content_verifier is not None and edge.evidence:
                verdict, creason = self.content_verifier(edge, existing)
                reason = f"{creason}; COG={dt}"
            else:
                verdict = "AGREE"
                reason = f"evidenced observation, content NOT inspected (COG={dt})"
        elif dt in ("AGREE", "ORPHAN"):
            verdict, reason = "AGREE", f"inferred & COG-supported ({dt})"
        elif dt == "HOLLOW":
            verdict, reason = "HOLLOW", "inferred; structural-only, not logically proven (HOLLOW)"
        else:
            verdict, reason = "REJECT", f"inferred & unsupported by COG ({dt})"
        # Only commit relation-supported edges into the working Category, so the
        # graph OPTIMUS/COG reason over isn't polluted by quarantined co-occurrence.
        if verdict == "AGREE":
            try:
                self.category.connect(edge.subject, edge.object, edge.relation,
                                      confidence=res.cat_confidence or 0.5)
            except Exception:
                pass
        return verdict, reason


def build_memory(category=None, *, use_cog: bool = True, use_optimus: bool = True,
                 domain: str = "memory") -> KGMemory:
    """Construct a KGMemory wired to real COG + OPTIMUS where available."""
    verifier = None
    if use_cog:
        try:
            verifier = CogVerifier(category=category, domain=domain)
            category = verifier.category          # share graph with OPTIMUS
        except Exception as exc:
            print(f"[komposos_kg] COG unavailable ({type(exc).__name__}: {exc}); "
                  f"using stub verifier")

    optimus = None
    if use_optimus and category is not None:
        try:
            from core.optimus import OptimusEngine
            optimus = OptimusEngine(category)
        except Exception as exc:
            print(f"[komposos_kg] OPTIMUS unavailable ({type(exc).__name__}: {exc})")

    return KGMemory(verifier=verifier, optimus=optimus)


# ── demo: the full loop with the REAL engines ────────────────────────────────
if __name__ == "__main__":
    mem = build_memory(use_cog=True, use_optimus=True)
    print("backend:", "REAL COG" if mem._verify.__class__.__name__ == "CogVerifier"
          else "stub", "| OPTIMUS:", mem._optimus is not None)

    print("\nWRITE GATE (real dual ZFC/CAT engine):")
    for s, r, o, src, ev in [
        ("aspirin", "treats", "headache", "PMID:123", "RCT: aspirin relieved headache"),
        ("aspirin", "treats", "inflammation", "PMID:456", "aspirin reduced inflammation"),
        ("aspirin", "treats", "cancer", "", ""),          # unevidenced inference
    ]:
        res = mem.remember(s, r, o, source=src, evidence=ev)
        print(f"  {s}->{o:<13} {res.verdict:<7} stored={res.stored}  ({res.reason})")

    print("\nRECALL (verified only, logged):")
    hits = mem.recall(subject="aspirin", agent="A")
    print(f"  {[e.id for e in hits]}")

    print("\nHONESTY GATE:")
    ok = mem.explain_action("recommend aspirin for headache",
                            ["aspirin|treats|headache"], agent="A")
    bad = mem.explain_action("recommend aspirin for cancer",
                             ["aspirin|treats|cancer"], agent="A")
    print(f"  cited a recalled fact       -> sincere={ok.sincere}")
    print(f"  cited a non-recalled fact   -> sincere={bad.sincere} "
          f"{[o['kind'] for o in bad.obstructions]}")

    print("\nOPTIMUS gap-filling (intermediates aspirin->cancer):")
    print(f"  {mem.suggest_path('aspirin', 'cancer')}")
