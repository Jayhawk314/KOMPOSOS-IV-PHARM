# Improving PHARM citation provenance (instructions for later)

Notes for a future session, based on the measured run of
`KOMPOSOS-SEC/KOMPOSOS-IV/validation/citation_grounding.py` against
`KOMPOSOS-IV-PHARM` real data (2026-06-01). Read those numbers first; don't
re-derive them.

## What we measured (the starting point)

On 737 cited claims in `PHARM/data/action_verified_provenance.json`
(each = source, relation, target, pmid, proof_sentence):

- **71.9% GROUNDED** (both entities present + a relation cue in the proof sentence)
- **25.1% RELATION_UNVERIFIED** — both entities co-occur but the relation is
  never stated in the cited sentence (co-occurrence cited as a directed claim)
- **0.3% CONTRADICTED** (2), **2.7% UNGROUNDED** (entity not found)
- External check: on the 51 claims PHARM's own audit labeled
  `relation_support_heuristic=True`, our generic grounding check agreed **50/51 (98%)**.

**Honest caveats that bound all of the above:**
- The grounding check is a **lexical relation-cue heuristic, not entailment**.
  So 25% RELATION_UNVERIFIED is an **upper bound** — some are real relations
  phrased in words our cue lexicon misses.
- We validated only the **positive class** ("when PHARM says supported, do we
  agree?"). There is **no PHARM-labeled 'unsupported' set**, so the precision of
  the "unverified" flag is not yet measured.
- The audit's `source_mentioned`/`target_mentioned` columns are **NOT ground
  truth** — every PMID row has `has_full_text=False` (`pmid_identifier_only`),
  so those Falses mean "no text was available," not "entity absent." Only
  `relation_support_heuristic` is usable.

## The root problems to fix (in priority order)

### P1 — Fetch and store the actual abstracts (unblocks everything)
The audit shows `has_full_text=False` on every PMID row: PHARM mostly stored
PMIDs as bare identifiers. Grounding can only be as good as the text it sees.
- Extend the existing PubMed infra: `PHARM/scripts/import_pubmed_batch.py`,
  `scripts/scrape_triplet_pmids.py`, `apply_verified_pmids.py`.
- For every cited PMID, fetch the title+abstract (NCBI E-utilities `efetch`),
  store it next to the edge. Then grounding runs against the whole abstract, not
  just one curated `proof_sentence`.

### P2 — Entity alias normalization (kills the false UNGROUNDED)
The 2.7% UNGROUNDED is mostly aliasing, not real mis-citation:
- Genes: `BRAF` vs `B-Raf` vs `BRAFV600E` (the one validation miss was this).
  Use an HGNC symbol→alias map.
- Diseases: `Breast_Cancer` vs "breast cancer" / "breast carcinoma" / "BC".
  Use MeSH or Disease Ontology synonyms. (The underscore case is already handled
  in `citation_grounding.py::_mentioned`; alias maps are the next step.)

### P3 — Relation support by entailment, not co-occurrence (the real 25%)
This is the substantive one. A proof sentence that names both entities but never
states the relation should not count as "verified provenance."
- Replace/augment the lexical cue check with a relation-extraction or NLI step:
  does the sentence (or abstract) entail `source --relation--> target`?
- Options: a small biomedical NLI/relation-extraction model, or an LLM judge
  given (claim, abstract) returning supports / co-occurrence-only / contradicts.
  Keep it as a *gate*, and log its verdict per edge.

### P4 — Build a small human gold set (so precision is measurable)
We can't currently measure how many of the 25% are truly unsupported.
- Hand-adjudicate ~100–200 claims by reading the abstract: label
  supported / co-occurrence-only / contradicts / not-in-text.
- PHARM already has adjudication scaffolding: `data/_adjudication_input.json`,
  `_adjudication_remaining.json`, `scripts/inject_honest_provenance.py`. Reuse it.
- This gold set turns "upper bound" into a real precision/recall number.

### P5 — Gate new citations through komposos_kg (prevent the problem at the source)
Going forward, every new `(drug, relation, target, pmid)` should pass through
the verify-on-write gate before being labeled verified provenance:

```python
from komposos_kg import build_memory
mem = build_memory()   # plug a relation-support verifier (P3) as the gate
mem.remember(drug, relation, target,
             source=f"PMID:{pmid}", evidence=abstract_text)
# AGREE -> store as verified; HOLLOW/REJECT -> quarantine for review
```

Co-occurrence-only citations then never get stored as "verified" in the first
place — they land in quarantine instead of silently inflating the count.

### P6 — Re-tier evidence by grounding strength, and re-run the harness as the metric
- Make `evidence_tier` reflect actual grounding: relation-stated-in-abstract
  (strong) > co-occurrence-only (weak) > identifier-only/no-text (unverified).
- After each change, re-run `validation/citation_grounding.py` and track
  GROUNDED% up and RELATION_UNVERIFIED% down — against the P4 gold set for
  precision, not just the internal distribution.

## Quantitative claims (separate track)
`PHARM/data/pmid_validation_results.json` validates numeric values (ic50,
mutation_frequency, hazard_ratio) with "value confirmed in abstract" — but it's
small (28 records) and all `valid=True` (no negatives). To make it useful ground
truth, add negative cases (claimed values NOT confirmed) and expand coverage.

## Files to touch / reference
- Harness (the measurement loop): `KOMPOSOS-SEC/KOMPOSOS-IV/validation/citation_grounding.py`
- PHARM data: `data/action_verified_provenance.json`, `reports/citation_attribution_audit_2026-05-27.csv`,
  `data/pmid_validation_results.json`, `data/edge_support_counts.json`
- PHARM infra to extend: `scripts/import_pubmed_batch.py`, `scripts/scrape_triplet_pmids.py`,
  `scripts/inject_honest_provenance.py`, `apply_verified_pmids.py`

## One-line summary
The fix is: **get the abstracts (P1), resolve aliases (P2), check relation
entailment not co-occurrence (P3), build a gold set to measure it (P4), and gate
new citations on the way in (P5).** Everything else is bookkeeping.
