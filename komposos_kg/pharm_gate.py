# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""pharm_gate.py — wire the pharm CONTENT verifier into KGMemory's write gate.

`build_pharm_memory()` returns a KGMemory whose `remember()` gate:
  1. reads the proof sentence (PharmCitationVerifier) and judges directed/signed
     relation support -> AGREE (relation-supported) / HOLLOW (co-occurrence,
     quarantined) / REJECT (no usable evidence), and
  2. if the real COG is importable, annotates that verdict with the dual
     ZFC/CAT structural opinion (COG=AGREE/ORPHAN/HOLLOW/REJECT).

This closes the hole demonstrated by `python -m komposos_kg.cog_adapter`, where an
evidenced fact was accepted as AGREE even though COG said REJECT and the evidence
was never read. Now the evidence IS read; co-occurrence cites are quarantined as
HOLLOW and never silently promoted to a verified tier.

Honest scope: AGREE from this gate is LEXICAL relation support (a screen, ~0.82
precision vs in-session adjudication — see validate_gate.py), not entailment.
RELATION-VERIFIED as a published tier still requires adjudication.
"""
from __future__ import annotations

from .memory import KGMemory
from .pharm_verifier import PharmCitationVerifier, VERDICT_TO_TIER


def build_pharm_memory(category=None, *, use_cog: bool = True,
                       use_optimus: bool = True, domain: str = "pharm") -> KGMemory:
    content = PharmCitationVerifier()
    verifier = content                     # content-only fallback
    optimus = None

    if use_cog:
        try:
            from .cog_adapter import CogVerifier
            verifier = CogVerifier(category=category, domain=domain,
                                   content_verifier=content)
            category = verifier.category   # share graph with OPTIMUS
        except Exception as exc:
            print(f"[pharm_gate] COG unavailable ({type(exc).__name__}: {exc}); "
                  f"content-only gate")

    if use_optimus and category is not None:
        try:
            from core.optimus import OptimusEngine
            optimus = OptimusEngine(category)
        except Exception as exc:
            print(f"[pharm_gate] OPTIMUS unavailable ({type(exc).__name__}: {exc})")

    return KGMemory(verifier=verifier, optimus=optimus)


# ── demo: ingest REAL pharm proof sentences through the gate ──────────────────
if __name__ == "__main__":
    import json

    proofs = json.load(open("data/action_verified_provenance.json", encoding="utf-8"))
    truth = {v["edge_id"]: v["verdict"] for v in
             json.load(open("data/relation_extraction_verdicts.json",
                            encoding="utf-8"))["verdicts"]}

    mem = build_pharm_memory(use_cog=True, use_optimus=True)
    backend = "REAL COG" if mem._verify.__class__.__name__ == "CogVerifier" else "content-only"
    print(f"\nbackend: {backend} | OPTIMUS: {mem._optimus is not None}\n")

    # Pick a spread: some the gate should pass, some it should quarantine.
    sample = proofs[:6] + [p for p in proofs if truth.get(p["edge_id"]) == "COOCCUR"][:4]
    print("WRITE GATE over real proof sentences:")
    print(f"  {'edge':<42} {'verdict':<8} {'tier':<20} adj")
    for p in sample:
        res = mem.remember(p["source"], p["relation"], p["target"],
                           source=f"PMID:{p['pmid']}", evidence=p["proof_sentence"])
        tier = VERDICT_TO_TIER.get(res.verdict, "?")
        adj = truth.get(p["edge_id"], "?")
        print(f"  {p['edge_id']:<42} {res.verdict:<8} {tier:<20} {adj}")

    print("\nRECALL (verified only, logged):")
    hits = mem.recall(agent="triage")
    print(f"  {len(hits)} relation-supported edges recallable "
          f"(HOLLOW co-occurrence quarantined)")

    print("\nHONESTY GATE:")
    if hits:
        good = mem.explain_action("recommend based on " + hits[0].id,
                                  [hits[0].id], agent="triage")
        bad = mem.explain_action("recommend based on a fact never recalled",
                                 ["Made_Up|treats|Nothing"], agent="triage")
        print(f"  cite a recalled edge      -> sincere={good.sincere}")
        print(f"  cite a never-recalled edge-> sincere={bad.sincere} "
              f"{[o['kind'] for o in bad.obstructions]}")
