# Massive Graph Expansion — Analysis & Recommendation (2026-06-04)

**Question:** what happens if we massively expand the drug / protein / disease
counts — say from today's ~1,150 objects to a "massive" graph (10²–10³× larger)?
Is that actually the right move, or is there a better strategy?

**Short answer:** **Uniform massive expansion is not recommended as the next
step.** It would break computational tractability with the *current* scoring
engine, and — more importantly — it does **not** address the system's real
bottleneck, which is **external generalization and label/evidence quality**, not
graph size. The recommended path is **scale-engineer the scorer first, then grow
in quality-gated, validated, disease-focused increments** under a
retrieve-then-rerank architecture. Details and implementation stories below.

---

## 1. Where we are today (baseline)

From the live `tier1.db` (2026-06-04):

- ~1,146 objects: 78 drugs, 20 diseases, 366 biological entities.
- 2,329 edges; evidence tiers Measured 1,014 / Established 377 / Inferred 918 /
  Hypothesis 20.
- **44 positive labels** (FDA `treats` edges).
- Scoring: 7–8 strategies per pair (`validation/repurposing_benchmark.py:245`,
  `score_pair` at `:303`).
- Benchmark scores all drug × disease pairs = 78 × 20 = **1,560 pairs**.
- Strict internal AUROC **0.9705**; external (Hetionet) AUROC **0.6436**,
  AUPRC 0.0095.

That last line is the whole story in miniature: the system is excellent
**in-distribution** and weak **out-of-distribution**. Keep it in mind — it
determines whether "more data" helps.

---

## 2. What happens computationally (the hard wall)

### 2.1 The scorer is super-linear in graph size, by construction

The mechanistic signal comes from `CompositionStrategy`, which calls
`Category.find_paths(drug, disease, max_length=4)`
(`validation/triage.py:221`, `core/category.py:354`). Two properties make this
the scaling wall:

1. **It enumerates *all simple paths* up to length 4**, not the shortest or
   top-k. Path count grows roughly as `b^L` where `b` is average out-degree and
   `L = 4`. A denser, larger graph raises `b`, so this term **explodes
   combinatorially** as you add edges.
2. **Each node expansion does a full O(E) scan over every morphism**
   (`core/category.py:388`: `for m in self._morphisms.values(): ...`) instead of
   using the precomputed `_adjacency`. So a single `find_paths` call is roughly
   **O(paths_explored × E)**.

`Category.morphisms_from()` (`core/category.py:225`) has the same O(E)-scan
problem and is used elsewhere.

### 2.2 The benchmark/triage cost multiplies that per pair

The benchmark scores **D × S** pairs (drugs × diseases), and each pair runs
`find_paths` (plus the other strategies). So total work scales like:

```
cost  ≈  (D × S)  ×  (paths_explored per pair)  ×  E
```

Rough magnitudes:

| Scenario | Drugs | Diseases | Edges E | Pairs (D×S) | Relative cost |
|---|---:|---:|---:|---:|---:|
| Today | 78 | 20 | 2,329 | 1,560 | 1× |
| Modest 10× | ~780 | ~200 | ~25k | 156,000 | ~10³–10⁴× |
| "Massive" | ~5,000 | ~1,000 | ~2M | 5,000,000 | **~10⁷–10⁹×** |

The `D×S` term alone is ~3,200× at the massive end; the per-pair `paths × E`
term adds several more orders of magnitude. **The current benchmark would go
from seconds to effectively never**, and the live Streamlit triage (which runs
`find_paths` per candidate on every click) would time out.

### 2.3 Memory and embeddings

- The `Category` is **fully in-memory** (`core/category.py:69-72`: objects,
  morphisms, adjacency, reverse-adjacency dicts). Millions of Python `Morphism`
  objects is GB-scale and GC-heavy, though not the primary wall.
- Every new protein needs an **ESMC-300M embedding** (960-d). Generating
  thousands–millions of embeddings is a real one-time GPU/compute cost, plus
  storage and an index.

**Verdict on computation:** with no engine changes, anything beyond a ~5–10×
expansion is impractical, and "massive" is infeasible. The good news: the
hotspots are well-localized and fixable (Section 5).

---

## 3. What happens scientifically (the part that actually matters)

Even if compute were free, uniform expansion is the wrong scientific bet:

1. **Label sparsity collapses.** You have 44 positives. If nodes/edges grow 10³×
   but verified `treats` labels do not, positive *density* craters. AUPRC (which
   is already 0.55 strict, 0.0095 external) and calibration degrade — you would
   be ranking a far larger haystack with the same tiny set of known needles.

2. **It doesn't fix the generalization gap.** Internal 0.97 vs external 0.64
   means the model leans on in-distribution structure. Adding **more data of the
   same provenance and construction** tends to *amplify* in-distribution fit, not
   close the external gap. Bigger ≠ more generalizable.

3. **Evidence quality dilutes.** Massive expansion almost always comes from
   automated ingestion (bulk ChEMBL, PubMed co-mention, predicted edges). Those
   land in the **Inferred/Hypothesis** tiers. The honest Measured:Inferred ratio
   (today ~1,014:918) gets worse, and the provenance-verification pipeline
   (737 agent-adjudicated proofs) **does not scale** to millions of edges.

4. **Baselines catch up; the categorical edge may shrink.** Denser graphs make
   popularity/degree shortcuts stronger. The current **+0.35 AUROC margin over
   the best baseline** (common_neighbor 0.62) is the real product claim. On a
   massive co-mention-heavy graph, common_neighbor rises and that margin can
   erode — you must re-measure it, not assume it holds.

5. **More candidates ⇒ more false discoveries to adjudicate.** Today's
   open-world unlabeled pairs are manageable; at 5M pairs the "interesting
   NOT_APPROVED" list becomes an unreviewable firehose.

---

## 4. Recommendation

**Do not pursue uniform massive expansion.** Pursue, in this order:

1. **Engineer the scorer for scale first** (Section 5, Stories 1–4). Until
   `find_paths` is indexed and bounded, *no* expansion is safe. This is cheap and
   high-leverage.
2. **Grow in quality-gated, disease-focused increments** (Story 5), not a
   monolith. Expand one therapeutic area at a time, with provenance + tier gates.
3. **Grow labels and Measured-tier evidence proportionally to nodes** — treat
   verified positives as the scarce resource that bounds useful graph size.
4. **Gate every expansion on *external* validation** (Story 6). If a bigger graph
   doesn't move Hetionet/temporal AUROC, the new data is noise — roll it back.
5. **Adopt retrieve-then-rerank** (Story 4) so the expensive categorical
   strategies only ever run on a small shortlist, decoupling answer cost from
   total graph size. (This is exactly the pattern the OPERADUM decision layer
   already uses: KOMPOSOS shortlist → profile rerank.)

The throughline: **the graph should be as large as your verified labels,
external-validation budget, and reranking shortlist can support — and no
larger.** Quality and generalization are the binding constraints, not size.

---

## 5. Implementation stories (if you proceed)

Ordered by leverage. Stories 1–4 are prerequisites for *any* growth.

### Story 1 — Measure the real scaling curve (1–2 days)
Generate synthetic graphs at 2×, 5×, 10×, 20× (random + realistic degree
distributions). Plot benchmark wall-time and peak memory vs (objects, edges,
pairs). **Acceptance:** a measured cost curve and the size at which triage
exceeds an interactive latency budget (e.g. 2 s/candidate). This replaces the
estimates in Section 2 with facts before anyone ingests real data.

### Story 2 — Index the path search (1–2 days, high leverage)
Replace the O(E) inner scan in `find_paths` (`core/category.py:388`) and
`morphisms_from` (`:225`) with lookups over an
`outgoing: dict[node, list[Morphism]]` index built once at load. **Acceptance:**
identical path results; `find_paths` per-call cost drops from O(paths × E) to
O(paths × avg_degree); Story 1 curve re-measured (expect 1–2 orders of
magnitude on larger graphs).

### Story 3 — Bound path enumeration (2–3 days)
Stop enumerating *all* simple paths. Add k-shortest / beam-limited search with a
per-pair path cap and early pruning by composed confidence (you already weight
by it in `score_pair:336`). Keep `max_length=4`. **Acceptance:** AUROC within
noise of today on the current graph (prove the cap doesn't hurt accuracy) while
bounding worst-case path count per pair.

### Story 4 — Retrieve-then-rerank pipeline (1–2 weeks)
Precompute object embeddings (ESMC for proteins; structural/Yoneda fingerprints
for drugs/diseases) into an ANN index (FAISS/hnswlib). For a query, retrieve a
top-N candidate shortlist by cheap similarity, then run the full categorical
strategies + OPERADUM decision ranking **only on those N**. **Acceptance:**
answer latency independent of total graph size; recall@N vs the exhaustive
scorer measured on the current graph. This is the single change that makes a
large graph usable at all.

### Story 5 — Quality-gated, sharded ingestion (ongoing)
An ingestion path that: requires provenance, classifies evidence tier on entry,
deduplicates (the Yoneda equivalence classes already find near-duplicates),
caps Hypothesis-tier inflow, and ingests **per disease area** into subgraph
shards rather than one monolith. **Acceptance:** Measured:Inferred ratio does
not regress; every batch carries source + tier; a shard can be loaded/scored
independently.

### Story 6 — Expansion gated on external validation (1 week, then continuous)
Wire the existing external/temporal/disease-holdout harnesses into a gate that
runs on every ingestion batch and **blocks** a merge that doesn't hold or
improve external AUROC and the baseline margin. **Acceptance:** a red/green
report per batch; a documented rollback when a batch degrades generalization.

### Story 7 — Persisted / out-of-core graph (only if Stories 1–6 demand it)
If measured memory becomes the wall, move from the all-in-RAM `Category` to a
backing store with lazy adjacency (SQLite indexed edges, or a graph DB) behind
the same `Category` API. **Acceptance:** identical scores; memory flat as the
graph grows; the API surface (`objects`, `morphisms`, `find_paths`) unchanged so
nothing downstream breaks.

---

## 6. Honest caveats

- The cost magnitudes in Section 2 are **estimates**; Story 1 exists to replace
  them with measurements before any decision is funded.
- "Massive" here means 10²–10³× today. A **modest** 5–10× expansion of *verified,
  high-tier* data in a focused area is reasonable and may help — the objection is
  specifically to *uniform, unvalidated, size-first* growth.
- This analysis is about Track A repurposing. Track B (de-novo design) has
  different scaling characteristics and is out of scope here.
- None of this is a knock on the current system: it is strong at its current
  scale. The point is that the next 10× of *value* comes from generalization,
  labels, and reranking architecture — not from graph size.
