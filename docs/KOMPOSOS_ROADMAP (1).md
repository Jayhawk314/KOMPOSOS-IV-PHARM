> **Legacy/historical notice (2026-05-27):** This file is retained for background or session history. It is not the current source of truth for Track A metrics or provenance. Current docs are in `truedocs/`, especially `truedocs/VALIDATION_AND_BENCHMARKS.md` and `truedocs/REPRODUCIBILITY_PROTOCOL.md`. Current strict run: AUROC 0.974694 [0.9606, 0.9855], AUPRC 0.551698 [0.4067, 0.6983], Hits@5/10/20 1.0000/0.6000/0.6000; LOOCV AUROC 0.975916 and AUPRC 0.553703; Hetionet external AUROC 0.634479 and AUPRC 0.009255. Source strings exist on all 5,382 morphisms with 610 PMID identifiers; this is not 100% edge-specific citation validation. Retired or superseded claims in this file should be read as historical.
# KOMPOSOS-IV-PHARM Roadmap

**Author:** Working draft for James Ray Hawkins
**Date:** 2026-05-04
**Source of truth:** `REPURPOSING_BEST_PATH_2026-05-04.md`, `EXTERNAL_AUDIT_REPORT_2026-05-04.md`, `MEMORY.md`, `CURRENT_STATE.md`. Nothing in this roadmap comes from outside those docs.

---

## The Thesis

KOMPOSOS-IV-PHARM is a **mechanistic candidate triage engine**. The deliverable is not a predictor's AUROC. It is a ranked report of drug-disease candidates, each with a traceable mechanistic derivation a scientist can audit in seconds.

This is what `REPURPOSING_BEST_PATH` Step 6 already calls out as the useful deliverable. The roadmap is what gets us from current state to a defensible, partner-ready version of that report.

The compositional structure of the engine matters because it changes how we think about "false positives." A high-scoring drug-disease pair that isn't a known indication isn't an error — it's a hypothesis with a mechanism attached. AUROC validates that the engine recovers known biology. The novel hypotheses *are the product*.

---

## What's Real Today

From `CURRENT_STATE.md` and the audit:

- **Core engine works.** Categorical runtime, oracle strategies, deterministic scoring on local data.
- **Reproducible AUROC under named protocols.** `legacy/as_loaded` 0.884550, `full_typed/as_loaded` 0.794325, `full_typed/remove_direct_labels` 0.809019, `full_typed/loocv` 0.772081. Full typed graph: 78 drugs, 20 diseases, 16 approved indications, 333 morphisms.
- **Named benchmark harness frozen.** `validation/repurposing_benchmark.py` with manifest and regression tests.
- **Audit completed and remediation queue documented.** This is itself an asset; most teams don't have it.

What's not real yet (audit findings):

- Four missing typed endpoints (CXCL12, CXCR4, IFNG, PI3KCA).
- Five unreferenced object rows.
- No source / evidence-type provenance on morphisms.
- No CIs, no AUPRC / Hits@K / MRR, no baselines.
- Four positives can't be recovered mechanistically (Imatinib→CML, Metformin→T2D, Bevacizumab→Colorectal_Cancer, Trametinib→Melanoma).
- `data/drugs/loader.py` broken.
- No reproducible DB build.
- No external or temporal validation.

Track B (drug design, ABPP, ADMET) is not validated and stays out of scope until Track A is shippable.

---

## The Roadmap

This is the six-step path from `REPURPOSING_BEST_PATH`, with concrete work specified per step. It is not phased by weeks. It is phased by **what unblocks what.** Each step has an exit condition. Don't move on until the exit condition is met.

### Step 1 — Freeze Evaluation

**Status:** Mostly done. Named harness, manifest, regression tests, decoupled legacy view all exist.

**Remaining work:**

- Add bootstrap confidence intervals to AUROC in the harness output.
- Add AUPRC, Hits@K, MRR alongside AUROC. Same harness, same protocols.
- Add baselines: random, degree, common-neighbor count, shortest path, path count. Run them through the same harness. Every report shows our scorer against these baselines.
- Mark older AUROC scripts as compatibility-only or retire them.

**Exit condition:** Every AUROC in any output document carries a CI, an AUPRC, a Hits@K, and a baseline comparison. No bare AUROC numbers anywhere.

### Step 2 — Repair Data

**Status:** Not started. The four missing endpoints are the most visible debt.

**Remaining work:**

- Decide for each of CXCL12, CXCR4, IFNG, PI3KCA: insert as typed `Protein` with UniProt ID and source citation, *or* remove the morphisms that reference them. The audit allows either path.
- Resolve the five unreferenced rows (CD163, CD4, CD68, FOXP3, TOP2A): connect with sourced morphisms or remove.
- Add `source` and `evidence_type` columns to morphisms. Backfill from PubMed, Reactome, OmniPath, SIGNOR. Every edge has provenance, or it's flagged as unsourced and excluded from "publication-grade" views.
- Repair `data/drugs/loader.py` so it actually imports what it uses. Add a reproducible `tier1.db` build script.
- Add a strict-mode flag that fails when morphism endpoints are missing typed object rows.

**Exit condition:** `tier1.db` rebuilds from source files via a single command. Every morphism has a source field populated or is flagged unsourced. Loader has strict mode.

### Step 3 — Complete Mechanisms

**Status:** Not started. The four broken positives are explicit gaps.

**Remaining work:**

- Add canonical biology so each positive becomes mechanistically recoverable under `remove_direct_labels`:
  - BCR-ABL → CML for Imatinib → CML.
  - AMPK and Complex I → Type2_Diabetes for Metformin → T2D.
  - VEGFA → Colorectal_Cancer for Bevacizumab → CRC.
  - MEK1/2 → ERK → Melanoma for Trametinib → Melanoma.
- Re-run the harness. Either label-removed AUROC and Hits@K rise, or we learn something diagnostic about the score function.
- For any positive that *still* isn't recoverable after canonical edges are added, exclude it from mechanism-only validation views and document why.

**Exit condition:** All 16 positives are either mechanistically recoverable under `remove_direct_labels`, or explicitly excluded with documented reason. The recovery rate is published alongside AUROC.

### Step 4 — Validate Harder

**Status:** Not started.

**Remaining work:**

- Disease-level holdout: leave one disease out entirely (all its positives), retrain / rescore, measure. Stronger than LOOCV because it tests transfer across diseases.
- Temporal holdout: timestamp morphisms (even approximately, by curation date or PubMed year). Train on pre-cutoff state, score, see which post-cutoff positives the engine surfaces.
- External validation: compare top-K hypotheses against an independent source. Hetionet's published predictions, ClinicalTrials.gov for drugs in active trials for diseases we surface, DrugBank's repurposing annotations. Pick one or two; report match rate.

**Exit condition:** At least one disease-level holdout result, one temporal holdout result, and one external comparison are in the manifest with CIs.

### Step 5 — Tune After Rigor

**Status:** Not started, and explicitly should not start until Steps 1–4 are done.

**Remaining work (only after Steps 1–4):**

- Simple average across the seven existing strategies remains the baseline.
- Any learned weighting uses nested cross-validation. No training on direct labels still in the graph.
- Prefer interpretable path features over opaque rank boosting.
- Document the score function in the same manifest as the AUROC results.

**Exit condition:** A tuned scorer that beats the simple-average baseline on `full_typed/loocv` AUPRC and Hits@K with non-overlapping CIs, *and* preserves interpretability (every score traceable to evidence paths).

### Step 6 — Ship Candidate Triage

**Status:** Not started. This is the actual deliverable.

**Remaining work:**

- A CLI that takes a disease (or drug, or pair) and emits a candidate triage report.
- Per-candidate fields, exactly as `REPURPOSING_BEST_PATH` Step 6 specifies: drug, disease, score with CI, evidence paths, source provenance per edge, label status (approved / hypothesis / contraindication / unknown), baseline rank comparison, contradictory or safety evidence if known.
- Output formats: JSON for tooling, Markdown for partners, one PNG of the evidence subgraph per candidate.
- A self-check section in every report: "Of N approved indications, M are mechanistically recoverable. Recovery rate K%." This is the credibility statement for non-ML audiences.
- Engine self-check beats AUROC for partner audiences. "It rediscovered Imatinib → CML through BCR-ABL on its own" lands harder than 0.81 ± 0.04.

**Exit condition:** Run the CLI on any disease in the graph and get a partner-readable report in under a minute. The report passes the audit doc's "Acceptance Criteria For A Serious External Claim."

---

## What's Optional (and Not on the Critical Path)

These are real, plausible additions. They're flagged as optional because nothing in your own audit or best-path docs requires them, and they each cost weeks of work that the core six steps don't yet have. **None of them ship before Step 6.**

### Spatial integration

You already have a spatial audit layer running on Lung 5 with multi-FOV replication. It's a real asset. The natural integration is: take Step 6's candidate triage report, add a "spatial coherence" column for diseases where we have spatial data.

**Why optional:** Step 6 is shippable without it. Spatial integration is an upgrade and it depends on having a stable per-candidate report format from Step 6 to attach to. It's also disease-restricted by data availability. Add it when a partner specifically needs it for a tissue-data disease.

### ESM-2 analogical edges

For every literature-supported Drug → Protein edge, embed both proteins with ESM-2, propose analogical edges to high-cosine-similarity proteins as new morphisms tagged `evidence_type: "analogical_esm2"`. Cheap (hours), provenance-friendly (each edge tagged with its source target and similarity score), and adds candidate volume.

**Why optional:** It's an edge-generation strategy, not a validation strategy. It only makes sense after Step 2 establishes provenance discipline (so analogical edges can be tagged distinctly) and after Step 4 establishes whether the engine's bottleneck is candidate volume or ranking quality. If Step 4 says "we have enough candidates, we just rank them poorly," ESM-2 expansion doesn't help.

### Boltz-2 structural confidence

Co-fold drug-protein pairs for top-ranked candidates, attach predicted affinity and model confidence as additional columns in the Step 6 report. Parallel evidence type, never fused into the score, never used as a promotion gate without per-target-family calibration.

**Why I pushed back on Boltz-2 earlier, plainly:** I wasn't pushing back on the tool. I was pushing back on putting it on the critical path before Step 5. Your own best-path doc Rule 5 says "tune score combiners only after evaluation and data integrity are stable." Boltz-2 integration is a score-combiner-shaped problem. Choosing thresholds (pIC50 cutoffs, confidence cutoffs) before Step 4 is done means those thresholds will need re-tuning when Step 4 changes what "stable" means.

Once Step 6 ships and rankings are stable, Boltz-2 becomes a natural ~1-week add-on: pick the top-25 hypotheses for a partner-relevant disease, fold them, attach the structural column. **It's not a reason to delay Steps 1–6.**

That's the whole pushback. Boltz-2 is a good tool that goes after the core path, not inside it.

---

## Acceptance Criteria for "Done"

Lifted directly from `REPURPOSING_BEST_PATH` and the audit:

- Reproducible DB build with checksum.
- No silent loader truncation.
- Every validation output includes view, protocol, pair count, positive count, negative assumption, date.
- Direct-label contamination controlled.
- Positives mechanistically recoverable or explicitly excluded.
- AUROC accompanied by AUPRC, enrichment@K, Hits@K, MRR, CIs.
- At least one external validation source.
- All claims say "research prototype" until clinical / translational validation exists.

When the candidate triage CLI from Step 6 produces reports that pass these criteria, the roadmap is done. Optional additions are upgrades, not completion blockers.

---

## What This Roadmap Won't Do

- **Won't reorder the six steps.** Your own best-path doc has them in dependency order. I tried twice to dress this up with phases, partner pilots, and disease-area picks; that was me importing other voices into your plan. The order in `REPURPOSING_BEST_PATH` is the order. Steps 1 and 2 unblock Step 3. Step 3 makes Step 4 meaningful. Steps 1–4 make Step 5 safe. Steps 1–5 are required for Step 6 to be defensible.
- **Won't pick a disease focus.** Your audit treats all four broken positives equally. Until you say one matters more than the others, they're a flat priority list.
- **Won't pick a partner.** Noetik is your example, not a target. The roadmap is partner-agnostic.
- **Won't smuggle in Track B.** Drug design, ABPP, ternary complex — none of it on this roadmap.
- **Won't optimize for a pitch.** The pitch is whatever Step 6 produces. If Step 6 produces a strong report, the pitch writes itself.

---

## Next Concrete Action

Step 1's remaining work is the smallest unit of progress: add CIs, AUPRC, Hits@K, MRR, and baselines to the existing harness. Two to four days. After this, every number in every doc has uncertainty and context.

Step 2 is mechanical and large; it's the right thing to start in parallel because it doesn't depend on Step 1.

Pick one. I'll execute.
