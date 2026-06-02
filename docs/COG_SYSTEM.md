# The COG System — what it is and what it actually does

COG is the **claim-verification / cognitive co-processor layer** of KOMPOSOS-IV.
Its job is not to *predict* (that's the oracle) but to **judge whether a claim is
supported**, and to keep an agent **honest** about what it relied on. This
document describes the parts as they actually behave (verified by running them),
and is explicit about the limits.

> Audit rule for this doc: where it says "verified", it means observed by running
> the code in this repo on 2026-06-01. Docstrings are claims, not guarantees.

---

## The pieces

```
                 ┌─────────────────────────────────────────────┐
   a claim  ───▶ │  COG: is this SUPPORTED?                     │
 (s, rel, o)     │   • ZFC engine  — does logic entail it?      │
                 │   • CAT engine  — does structure support it? │
                 │   → delta: AGREE / ORPHAN / HOLLOW / REJECT   │
                 └─────────────────────────────────────────────┘
                                    │
   an agent ───▶ honesty core ──────┤  did the agent only use what it actually had?
                                    │   • sincerity: claimed reasoning == real reasoning
                                    │   • intent: honesty is a HARD constraint, not a price
                                    ▼
                 komposos_kg memory: verify-on-write + honest-on-read gates
```

### 1. The dual ZFC/CAT engine (`zfc/bridge.py` → `DualEngineBridge`)

A claim `relation(source, target)` is judged by two independent engines:

- **ZFC engine** (`zfc/logic.py`, `well_ordering.py`) — proposes: is the claim a
  **logical entailment** of what the store already contains (transitive chains,
  ordinal rank structure)?
- **CAT engine** (the Category + optional `CategoricalVerifier`) — verifies
  **structurally**: is there a path / neighborhood / curvature pattern that
  supports it?

The two judgments combine into a **delta type**:

| delta | ZFC | CAT | meaning |
|---|---|---|---|
| **AGREE** | yes | yes | logic proves it and structure confirms it |
| **ORPHAN** | yes | no | logically forced but no structural path yet |
| **HOLLOW** | no | yes | structural pattern with no logical proof (novel, or noise) |
| **REJECT** | no | no | neither engine supports it |

A **System 3 / Meta-Kan** layer (`zfc/meta_kan.py`) records each query as an
episode and learns to predict which delta to expect — a cheap "should I bother
running both engines" meta-oracle. (Present and wired; not independently
benchmarked here.)

**The oracle-side adapter** (`oracle/zfc_verifier.py`, `OracleZFCBridge`) wraps an
existing `CategoricalOracle` and tags each *prediction* with a delta, rather than
re-predicting. This is the path the repurposing pipeline can use to flag
predictions that are structurally plausible but logically baseless (HOLLOW) vs
fully supported (AGREE).

### 2. The honesty / intent core (`komposos_kg/honesty.py`)

Domain-agnostic, no dependencies. Two ideas:

- **Sincerity** — "the explanation matches the actual reasoning." Modeled as an
  *identification* between the **claimed** reasoning trace and the **actual** one.
  Failures are structured, not a bare boolean:
  - `FABRICATED` — a step claimed but never run,
  - `HIDDEN` — a causal step run but not disclosed,
  - `DISTORTED` — claimed justification ≠ actual,
  - `CONCLUSION_MISMATCH`.
  This has *teeth only when the trace is the real causal driver and is
  inspectable* (symbolic mode). For neural/black-box reasoning there is a
  `measured_sincerity` fallback that **bounds** insincerity via probes — it does
  not prove honesty.
- **Intent as constrained optimization** — `decide()` maximizes a domain utility
  **within the honest feasible set** (lexicographic order). Honesty is a **hard
  constraint, never a weighted term**, so a high-utility lie can never win; if no
  honest action is feasible, the system **abstains**. (There's a runnable
  self-test at the bottom of the file proving the high-utility lie is rejected.)

> Truthfulness (does the claim match the world?) is a **separate** problem and the
> domain's job, expressed through `domain_invariants` — the honesty core does not
> pretend to settle it.

### 3. The memory gates (`komposos_kg/memory.py` → `KGMemory`)

The graph itself is ordinary; the value is the two gates:

- **verify-on-write (`remember`)** — a verifier judges a fact **before** storing:
  `AGREE` → stored & recallable; `HOLLOW` → **quarantined** (stored but not
  returned by `recall` unless asked); `REJECT` → refused.
- **honest-on-read (`recall` + `explain_action`)** — every `recall` logs which
  edge ids an agent pulled. `explain_action` then checks the agent only cited
  facts it **actually recalled**; citing a never-recalled fact is a
  `fabricated_step`. This is what makes the honesty check *provable* rather than
  guessed.
- **gap-filling (`suggest_path`)** — delegates to OPTIMUS to propose intermediate
  concepts `B` for `subject → B → object` when a direct link is missing.

### 4. The content verifier added 2026-06-01 (`komposos_kg/pharm_verifier.py`)

The stock `CogVerifier` had a deliberate but dangerous policy: an **evidenced**
fact (one with any `source`/`evidence` string) was accepted as an observation
**without reading the evidence**. Verified by running the demo — a `COG=REJECT`
fact was stored as `AGREE`. So citations were never actually checked.

`PharmCitationVerifier` closes that: it reads the proof sentence and judges the
**directed, signed** relation (entities by word boundary + relation keyword +
polarity check) → `AGREE` / `HOLLOW` (co-occurrence, quarantined) / `REJECT`.
`CogVerifier` now accepts a `content_verifier` and runs it on evidenced facts;
without one it honestly reports `content NOT inspected`.

**Honest scope (measured):** the gate is a lexical **screen**, ~**0.82 precision /
0.83 recall** vs in-session adjudication (`validate_gate.py`, n=729). So its
`AGREE` maps to **`RELATION-SCREENED`**, *never* the published
`RELATION-VERIFIED` tier. The gate can quarantine co-occurrence; it cannot mint
"verified" on its own.

### 5. COG as an MCP server (`cog/`, tools `mcp__komposos-cog__*`)

The same engine is exposed to agents as MCP tools — `cog_assert`, `cog_check`,
`cog_query`, `cog_coherence`, `cog_energy`, `cog_explain`, `cog_scan`,
`cog_threat_model`. These let an agent assert/check claims against the categorical
knowledge layer at runtime, outside the Python import path.

---

## What COG is good for here

- **Flagging predictions that are structurally plausible but logically baseless**
  (HOLLOW) vs fully supported (AGREE) — a second opinion on the oracle.
- **Quarantining weak citations** at write time so co-occurrence never silently
  becomes "verified."
- **Keeping a citing agent honest** — catching a PMID it never actually retrieved.

## What COG is *not* (limits, stated plainly)

- It does **not** establish that a stored fact is **true in the world**. Evidenced
  facts are treated as observations; truth is the domain's job.
- The sincerity proof is only as good as the trace you feed it. Garbage trace in →
  garbage verdict out. For neural reasoning it only *bounds* insincerity.
- The content gate is **lexical**, not semantic entailment — a screen with a
  measured error rate, not a guarantee.
- System 3 / Meta-Kan is wired but **not independently benchmarked** in this repo.
- COG cannot *derive* a brand-new grounded fact from an empty graph; that's why
  the gate accepts evidenced observations rather than demanding COG-derivability.

---

## Pointers

- `zfc/bridge.py` — dual engine + delta classification.
- `oracle/zfc_verifier.py` — wraps oracle predictions with deltas.
- `komposos_kg/honesty.py` — sincerity + constrained-intent core (+ self-test).
- `komposos_kg/memory.py` — the write/read gates.
- `komposos_kg/cog_adapter.py` — wires the real engine as a verifier.
- `komposos_kg/pharm_verifier.py` + `pharm_gate.py` — the content gate (2026-06-01).
- `validate_gate.py` — measures the gate against in-session adjudication.
- `komposos_kg/README.md` — the package's own honest status notes.
