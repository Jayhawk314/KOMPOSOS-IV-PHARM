# komposos_kg

A portable **verified knowledge-graph memory for agents**. Drop this folder into
any repo. An agent uses it as memory, and it adds two guard rails a plain KG
doesn't have:

- **verify-on-write** — a fact is checked *before* it enters memory.
- **honest-on-read** — when the agent says "I did X because of fact Y", it's
  checked that Y was a fact the agent *actually retrieved*.

The graph itself isn't the point (those are common). The point is the gates.

---

## Status (read this first)

This is a **research component**, not a finished product. What's real vs. not:

- ✅ The graph, retrieval logging, the honesty check, and the gate plumbing
  **work and are tested by the demo below.**
- ✅ It wires to a repo's **real COG** (dual ZFC/CAT engine) and **real OPTIMUS**
  when they're importable — verified: the demo's unevidenced inference was
  rejected by the actual engine.
- ⚠️ If COG isn't importable, it falls back to a **deliberately dumb stub**
  verifier (flags only facts with no evidence). The stub is a placeholder, not
  a safety guarantee.
- ⚠️ The honesty check is *provable* here only because **retrieval is logged**.
  It verifies "you cited a fact you actually recalled" — **not** "the fact is
  true in the world." Truth of stored facts is the verifier's job.
- ❌ No benchmark numbers are claimed. Measure it on your own data before
  trusting it for anything that matters.

---

## Install / drop-in

Copy the whole `komposos_kg/` folder into your repo. No third-party
dependencies inside the package itself. To get the **real** COG/OPTIMUS gate,
the host repo must have importable `core/`, `zfc/` (for COG) and `core/optimus.py`
(for OPTIMUS) — i.e. a KOMPOSOS-style repo. Without them it still runs on the stub.

```python
from komposos_kg import build_memory
mem = build_memory()        # auto-wires real COG + OPTIMUS if present, else stub
```

---

## Quick start

```python
from komposos_kg import build_memory

mem = build_memory(use_cog=True, use_optimus=True)

# 1. remember — verified before storing
mem.remember("aspirin", "treats", "headache",
             source="PMID:123", evidence="RCT: aspirin relieved headache")
mem.remember("aspirin", "treats", "cancer")     # no evidence -> COG rejects it

# 2. recall — verified facts only, and it logs what this agent pulled
facts = mem.recall(subject="aspirin", agent="A")     # [Edge(aspirin|treats|headache), ...]

# 3. explain_action — honesty gate
ok  = mem.explain_action("recommend aspirin for headache",
                         ["aspirin|treats|headache"], agent="A")   # ok.sincere == True
bad = mem.explain_action("recommend aspirin for cancer",
                         ["aspirin|treats|cancer"], agent="A")     # bad.sincere == False

# 4. suggest_path — OPTIMUS proposes bridging concepts when a link is missing
mem.suggest_path("aspirin", "cancer")            # ["..."] or []
```

---

## API reference

### `build_memory(category=None, *, use_cog=True, use_optimus=True, domain="memory") -> KGMemory`
Factory. Tries to construct a real `CogVerifier` (and share its `Category` with
OPTIMUS); prints a notice and falls back to the stub if COG/OPTIMUS can't be
imported.

### `KGMemory`

| Method | Signature | Returns |
|---|---|---|
| `remember` | `(subject, relation, object, *, source="", evidence="")` | `RememberResult(stored, verdict, edge_id, reason)` |
| `recall` | `(subject=None, relation=None, object=None, *, agent="default", include_unverified=False)` | `list[Edge]` (logs retrieval per `agent`) |
| `verify` | `(subject, relation, object, *, source="", evidence="")` | verdict `str` (no store) |
| `explain_action` | `(action, cited_edge_ids, *, agent="default")` | `SincerityResult` |
| `suggest_path` | `(subject, object, depth=3)` | `list[str]` intermediate concepts (OPTIMUS) |
| `why` | `(edge_id)` | provenance `dict` or `None` |

### `Edge`
Fields: `subject, relation, object, source, evidence, verdict, reason`.
`edge.id == f"{subject}|{relation}|{object}"` — that's what you pass to
`explain_action` / `why`.

### `SincerityResult` (from `honesty.py`)
`.sincere: bool`, `.obstructions: list[{kind, detail}]`, `.to_cog_verdict() -> "AGREE"|"HOLLOW"`.
Obstruction kinds you'll see from memory: `fabricated_step` (cited a fact never recalled).

---

## How the gates work

### Write gate (`remember`)
The verifier returns one of:

| verdict | meaning | effect |
|---|---|---|
| `AGREE` | accepted | stored, recallable |
| `HOLLOW` | structurally plausible but not logically proven | **quarantined** (stored, not returned by `recall` unless `include_unverified=True`) |
| `REJECT` | unsupported | not stored |

**COG policy (important and deliberate):** COG cannot *derive* a brand-new
grounded fact from an empty graph, so gating *every* fact through COG would
reject valid new observations. Therefore:

- **Evidenced** facts (you passed `source` or `evidence`) are accepted as
  observations; COG only annotates them.
- **Unevidenced** facts (inferences, no source) are gated by COG:
  `AGREE`/`ORPHAN` → store, `HOLLOW` → quarantine, `REJECT` → refuse.

(`ORPHAN` from the dual engine = "logically entailed, no structural path yet";
the adapter maps it to `AGREE`.)

### Read logging (`recall`)
Every recall records the returned edge ids against the calling `agent`. This log
is what makes the honesty check *provable* rather than guessed.

### Honesty gate (`explain_action`)
Builds an identification between the **claimed** citations and the **actually
recalled** edges (via `honesty.check_sincerity`). Rules:

- Citing a fact you **never recalled** → `fabricated_step` → **not sincere**.
- Citing a **relevant subset** of what you recalled → **fine** (recalled facts
  are marked non-causal, so leaving some uncited is not "hiding" them).

### Gap-filling (`suggest_path`)
Delegates to `OPTIMUS.discover_intermediates(subject, object)` to propose
concepts `B` such that `subject → B → object`. Returns `[]` if OPTIMUS is absent.

---

## Plugging in your own verifier

`build_memory` uses the repo's COG by default. To supply your own gate (any
callable `(Edge, list[Edge]) -> (verdict, reason)`):

```python
from komposos_kg import KGMemory

def my_verifier(edge, existing):
    if contradicts(edge, existing):
        return "REJECT", "contradicts a known fact"
    return "AGREE", "ok"

mem = KGMemory(verifier=my_verifier)
```

This is the extension point for contradiction/entailment checking, domain
rules, or pointing at a future canonical `komposos-math` core.

---

## Verified demo output

`python -m komposos_kg.cog_adapter` (run with real COG + OPTIMUS present):

```
backend: REAL COG | OPTIMUS: True
WRITE GATE (real dual ZFC/CAT engine):
  aspirin->headache      AGREE   stored=True   (evidenced observation (COG=REJECT))
  aspirin->inflammation  AGREE   stored=True   (evidenced observation (COG=REJECT))
  aspirin->cancer        REJECT  stored=False  (inferred & unsupported by COG (REJECT))
RECALL (verified only, logged):
  ['aspirin|treats|headache', 'aspirin|treats|inflammation']
HONESTY GATE:
  cited a recalled fact       -> sincere=True
  cited a never-recalled fact -> sincere=False ['fabricated_step']
```

---

## Files

```
komposos_kg/
  __init__.py      exports: build_memory, KGMemory, Edge, check_sincerity, SincerityResult
  honesty.py       the honesty core (self-contained copy so the folder travels alone)
  memory.py        KGMemory: the gates + retrieval log
  cog_adapter.py   CogVerifier (real dual-engine) + build_memory factory + demo
  README.md        this file
```

## Design notes

- **No engine merge.** This package adapts to whatever COG/OPTIMUS a repo has;
  it does not contain or duplicate them. Diverged forks across repos stay where
  they are.
- **∞-Cosmos is intentionally not wired in** — it has no clear memory role yet.
  Things are added when they earn a job, not because they exist.
- `honesty.py` duplicates the repo's `honesty_intent.py` on purpose, so this
  folder is self-contained when copied elsewhere.
