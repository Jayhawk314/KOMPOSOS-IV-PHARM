"""
komposos_kg — a portable verified-KG-memory package for agents.

Drop this whole folder into any repo. It auto-wires to that repo's COG
(dual ZFC/CAT engine) and OPTIMUS if they're importable, and falls back to a
stub verifier if they're not — so it works everywhere, better where COG exists.

    from komposos_kg import build_memory
    mem = build_memory()          # auto-wires real COG + OPTIMUS if present
    mem.remember("aspirin", "treats", "headache", source="PMID:123",
                 evidence="aspirin relieved headache in RCT")
    facts = mem.recall(subject="aspirin", agent="A")
    ok = mem.explain_action("recommend aspirin", [f.id for f in facts], agent="A")

Pieces:
  honesty.py     — the honesty core (sincerity = stated reasoning == actual)
  memory.py      — KGMemory: verify-on-write, verified-only recall, honest-on-read
  cog_adapter.py — wires real COG (verifier) + OPTIMUS (gap-filling) + build_memory
"""
from .memory import KGMemory, Edge, RememberResult          # noqa: F401
from .honesty import check_sincerity, SincerityResult        # noqa: F401
from .cog_adapter import build_memory, CogVerifier           # noqa: F401
