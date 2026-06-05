# Graph Expansion Plan — Sources, Order, and Honesty-Gated Literature (2026-06-04)

This is the **constructive** plan: how to grow the drug / protein / disease graph
using the data sources we already have, in a sensible order, with PubMed
literature pulled through the **COG + honesty.py** verify-on-write layer so it
arrives *verified* rather than as co-mention noise.

It supersedes the worst-case framing in `GRAPH_SCALING_ANALYSIS.md` for
day-to-day planning. (That doc's engineering points — the path-search hotspot —
still apply once the graph gets large; see §5.)

---

## 0. The one principle that makes this safe

**Grow in connected, labeled slices — never bare nodes.** Every expansion unit is
a drug + its protein targets + the disease it treats, wired together, so:

- every new node sits on a real **Drug → Protein → Disease** path (it can be
  scored), and
- new approved drugs **bring their own `treats` labels**, so positive labels grow
  *with* the graph instead of lagging it.

That second point is the whole answer to the "label density collapses" worry:
because diseases enter **on the back of FDA approvals**, positives scale with the
graph rather than staying flat.

---

## 1. Where we are (baseline, live `tier1.db` 2026-06-04)

- ~1,146 objects: 78 drugs, 20 diseases, 366 biological entities; 2,329 edges.
- Evidence tiers: Measured 1,014 · Established 377 · Inferred 918 · Hypothesis 20.
- 44 FDA `treats` positives. Oncology, 20 cancer types.
- Sources already in the graph (edges may cite several): PubMed 1,036 ·
  ChEMBL 881 · ESMC 424 · KEGG 72 · FDA 61 · STRING 23 · ABPP 17.
- Strict internal AUROC 0.9705; disease-holdout mean 0.9378; temporal 0.9706;
  external (Hetionet) 0.6436; best baseline common_neighbor 0.6219 (margin +0.35).

We already own every source below. The only one that needs active pulling is
PubMed, and that now goes through the honesty gate.

---

## 2. Ingestion order (structured first, honesty-gated literature continuous)

Order is chosen so labels and mechanism arrive **before** noisy literature, and so
each new disease is fully wired and labeled the moment it enters.

### Phase A — Labels and mechanism (structured, low-risk, do first)

1. **FDA approvals.** The label backbone. Each approval is a verified `treats`
   edge = a new positive, and it pulls in the drug and the disease as connected,
   labeled nodes. **Diseases enter here**, never bare.
2. **ChEMBL.** Drug → target bioactivity. Measured-tier drug/target wiring;
   already the largest structured source (881 edges) and well understood.
3. **KEGG + STRING + cBioPortal.** The mechanism middle: pathways, protein–protein
   interactions, genomic associations. These are what turn a bare disease node
   into one with real Drug → Protein → Disease paths.
4. **ABPP.** Measured binding/engagement where available (the strongest evidence
   type; feeds the binding strategy and the OPERADUM engagement figure).

### Phase B — Representations

5. **ESMC embeddings.** Embed every new protein as it lands (ESMC-300M, 960-d).
   Needed for the structural/Yoneda strategies and for the retrieve-then-rerank
   shortlist (§5). This is the one real compute cost; batch it per ingestion.

### Phase C — Literature, honesty-gated (continuous, never blind)

6. **PubMed via COG + `komposos_kg/honesty.py`.** Each proposed PMID edge must
   carry a faithful reasoning trace — the cited sentence actually asserts the
   **directed, signed** relation. The honesty core checks that the stated
   justification matches what was actually verified (no fabricated / hidden /
   distorted step) and **abstains** when it can't witness it. Admit only
   **RELATION-VERIFIED** edges into the scored graph; keep
   **LEXICAL-COOCCURRENCE** in a separate tier that never silently inflates
   scores. This is the unlock: it converts "PubMed dilutes quality" into "PubMed
   adds verified evidence."

---

## 3. Quality discipline (carry forward what already works)

- **Tier on entry.** Every edge gets an `evidence_tier` at ingestion
  (Measured / Established / Inferred / Hypothesis). Watch the Measured:Inferred
  ratio — a batch that worsens it is a smell.
- **Provenance required.** No edge without a source string (the graph is already
  at 2,329/2,329; keep it there).
- **Dedup.** The Yoneda equivalence classes already surface near-duplicate
  drugs/targets; fold new data against them so expansion doesn't double-count.
- **Honesty is a hard constraint, not a score term.** Per `honesty.py`, a
  high-utility edge can't buy its way past a failed sincerity check — the system
  abstains instead. Keep it that way for ingestion.

---

## 4. Validation checkpoints (light, after each batch)

Run the harnesses you already have after each meaningful batch; treat them as a
gate, not a report:

- **Disease-holdout AUROC** — the direct test that adding diseases generalizes
  (baseline mean 0.9378 across 7 diseases).
- **Temporal holdout** (approval year > 2013) — guards against fitting the past.
- **External (Hetionet)** — the honest generalization signal (today 0.6436); this
  is the number to *move up*, and the real reason to expand.
- **Baseline margin** — re-measure common_neighbor etc.; the product claim is the
  **+0.35 margin**, and denser graphs can lift baselines, so confirm it holds.

**Rule:** a batch that holds or improves these is kept; a batch that drags
external AUROC or collapses the baseline margin gets rolled back and the source
(or the honesty trace) is inspected. Expansion that doesn't help generalization
is noise, however clean it looks.

---

## 5. When (not if) it gets big — engineering checkpoints

Today's scale is fine. These become relevant as the graph grows; they are not
blockers now, just the order to address them in:

- **Index the path search first.** `Category.find_paths` (`core/category.py:354`)
  scans all morphisms per expansion step (`:388`) instead of the adjacency index;
  same for `morphisms_from` (`:225`). Indexing these is the single highest-leverage
  fix and changes nothing about results. Do it when triage latency starts to bite.
- **Bound path enumeration.** It currently enumerates *all* simple paths to
  length 4; cap to k-best with confidence pruning when path counts balloon.
- **Retrieve-then-rerank.** Use the ESMC/Yoneda embeddings to shortlist top-N
  candidates, then run the full categorical strategies + OPERADUM ranking only on
  those N — so answer cost stays flat as the graph grows. (Same pattern OPERADUM
  already uses: shortlist → rerank.)

A good trigger: when interactive triage exceeds ~2 s/candidate, do the indexing
fix; when memory or path counts become the wall, do reranking.

---

## 6. Honest scope

- `honesty.py` detects **insincerity** given a faithful trace and makes honesty
  non-tradeable; it does **not** by itself guarantee a relation is *true* of the
  world. Truthfulness is the domain's job (domain invariants) — so pair the
  honesty gate with the existing relation-polarity checks, don't lean on it alone.
- The validation numbers above are the current strict figures; re-run them per
  batch rather than assuming they carry.
- This plan is Track A (repurposing). It deliberately keeps the sharp oncology
  focus; jumping to a new therapeutic area is allowed but is a re-validate-from-
  scratch move, not a drop-in batch.
