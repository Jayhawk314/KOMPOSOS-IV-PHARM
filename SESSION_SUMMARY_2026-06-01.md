# Session Summary — 2026-06-01

Author of record: James Ray Hawkins. Work performed in-session (no LLM API
tokens consumed; all literature checks used NCBI eutils only).

This session had two halves: (1) audit and selectively integrate the Gemini
PMID-replacement work, and (2) begin wiring the COG + honesty gate into
`komposos_kg` as a real verify-on-write layer.

---

## Part 1 — PMID provenance: audited, then 12 corrections integrated

### What the Gemini artifacts actually are (verified, not assumed)
The `data/` artifacts (`GATHERED_PMID_LIST.json`, `TARGETED_SEARCH_RESULTS.json`,
`PMID_AUDIT_REPORT.json`) are **lexical co-occurrence screening**, not relation
entailment. The two scripts (`audit_all_pmids.py`, `targeted_pmid_search.py`)
check "drug + target + one action keyword in one sentence" — no directionality,
no sign.

- The advertised **"94.5% verified"** is inflated by a broad-keyword pass
  (keywords include `signaling`, `pathway`, `patient`, `marker`). The strict
  re-audit rate on the existing proof sentences is **80.9%** (596/737 AGREE).
- The "stubborn 40" failures are mostly relations the verifier has no vocabulary
  for (`indirect_inhibitor`, `synergizes_with` default to `["associated"]`).
- Correction to an earlier claim made mid-session: the original PMIDs were **not**
  garbage. A full-abstract recheck found 93/94 originals do mention both entities;
  only `Dabrafenib->BRAF` (orig `42143022`) was genuinely off-topic. Judging a
  citation by its title alone is unreliable.

### What we integrated (and what we deliberately did not)
Of 94 proposed replacements, 81 passed a live-PubMed recheck
(`verify_replacements.py`: real PMID + both entities + action keyword). But:

- **67 of those 81 targeted `[RELATION-VERIFIED]` edges** whose citations were
  already agent-adjudicated. Swapping their PMID for an un-adjudicated
  broad-keyword one while keeping the `[RELATION-VERIFIED]` tag would have made
  the tag lie. **Rule applied: agent adjudication outranks any keyword screen;
  never swap a RELATION-VERIFIED citation on co-occurrence evidence.** These were
  protected.
- Only the **14 `[LEXICAL-COOCCURRENCE]` -> `[LEXICAL-COOCCURRENCE]` swaps** were
  applied; then **2 weak keyword-coincidences were reverted** (`NRAS->Prostate`
  matched "affinity" in "affinity purification"; `MMP9->NSCLC`).
- Net: **12 citation corrections** landed (e.g. `ABCB1->Breast_Cancer` now cites
  *"ABCB1 Regulates Immune Genes in Breast Cancer"*). Tier counts unchanged
  (594 RELATION-VERIFIED / 215 LEXICAL-COOCCURRENCE). PMID strings do not feed
  scoring, so strict **AUROC is unchanged at 0.948640** (confirmed by benchmark).

Committed and pushed as `84acdcb`. The report generator
(`validation/trace_prediction.py`) and the UI PubMed links (`app.py`) read
provenance live from `tier1.db`, so they reflect the new PMIDs on a fresh run /
cache clear.

---

## Part 2 — COG + honesty gate wired into `komposos_kg`

### The hole we found (by running it, not reading docstrings)
`python -m komposos_kg.cog_adapter` printed:
```
aspirin->headache   AGREE  stored=True  (evidenced observation (COG=REJECT))
```
COG itself said **REJECT**, but the adapter overrode it to **AGREE** purely
because a source string existed. **The evidence text was never read.** So any
PMID-bearing pharm edge passed the gate unconditionally.

### What we built (wired + measured + tested; not yet adopted in production)
- `komposos_kg/pharm_verifier.py` — `PharmCitationVerifier`: reads the proof
  sentence and judges the **directed, signed** relation ->
  `AGREE` (relation-supported) / `HOLLOW` (co-occurrence -> quarantined) /
  `REJECT` (no usable evidence).
- `komposos_kg/cog_adapter.py` — `CogVerifier` gained a `content_verifier` param.
  Evidenced facts now run it instead of auto-AGREE; without one it honestly
  reports `content NOT inspected`. Only `AGREE` edges are committed to the Category.
- `komposos_kg/pharm_gate.py` — `build_pharm_memory()` composes the content gate
  with live COG annotation; demo ingests real proof sentences.
- `tests/test_pharm_gate.py` — 7 passing regression tests (23 related tests green).

### Measured against your own adjudication (`validate_gate.py`, n=729)
| | adj=VERIFIED | adj=COOCCUR |
|---|---|---|
| gate=VERIFIED | 494 (TP) | 110 (FP) |
| gate=COOCCUR | 101 (FN) | 24 (TN) |

**Precision 0.818, Recall 0.830, F1 0.824.** The 110 false positives are the key
finding: a pure lexical gate mislabels ~18% of its "verified" calls. Therefore
the gate's `AGREE` maps to **`RELATION-SCREENED`**, never the published
`RELATION-VERIFIED`. The automated gate can **quarantine**; promotion to verified
still requires adjudication.

---

## Recommendation on next step: wiring the honesty gate into `triage.py`

**Recommendation: WAIT. Not a no-brainer.**

`triage.py` builds its evidence chains deterministically via `trace_pair` over the
provenance index, then renders the exact edges (and their PMIDs) on each traversed
path. There is no generative step that could cite a fact it never retrieved — the
rendering *is* the recall. The honesty gate (`explain_action`) only earns its keep
when an agent **chooses** what to cite and could fabricate or cherry-pick
divorced from what was retrieved.

Wiring it into deterministic triage today would add a gate that **can never fail**
— dead weight that could also falsely advertise an "honesty guarantee" where there
is nothing to guard. That would itself be a mild form of verification theater.

**Wire it the moment there is an LLM/generative explanation step** — e.g. a prose
"why this drug" narrator in `app.py`, or any agent that writes
"Drug X treats Y because PMID:123". There, the honesty gate catches a hallucinated
or unrecalled PMID, which is exactly its job. Until that step exists, the value is
ceremony.

---

## Honest status line
- 12 PMID corrections: **done, committed, pushed**. AUROC unchanged.
- COG + honesty gate: **wired, measured (~0.82 precision), tested** — **not yet
  adopted** in the production import path or triage. `komposos_kg/` changes are
  uncommitted pending review.
