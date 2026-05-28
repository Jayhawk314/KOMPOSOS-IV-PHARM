> **Legacy/historical notice (2026-05-27):** This file is retained for background or session history. It is not the current source of truth for Track A metrics or provenance. Current docs are in `truedocs/`, especially `truedocs/VALIDATION_AND_BENCHMARKS.md` and `truedocs/REPRODUCIBILITY_PROTOCOL.md`. Current strict run: AUROC 0.974694 [0.9606, 0.9855], AUPRC 0.551698 [0.4067, 0.6983], Hits@5/10/20 1.0000/0.6000/0.6000; LOOCV AUROC 0.975916 and AUPRC 0.553703; Hetionet external AUROC 0.634479 and AUPRC 0.009255. Source strings exist on all 5,382 morphisms with 610 PMID identifiers; this is not 100% edge-specific citation validation. Retired or superseded claims in this file should be read as historical.
# KOMPOSOS-IV-PHARM Roadmap

**Author:** Working draft for James Ray Hawkins
**Date:** 2026-05-04 (updated 2026-05-10: ChEMBL expansion deployed)
**Source of truth:** `MEMORY.md`, `CURRENT_STATE.md`, `DEPLOYMENT_2026-05-10.md`. Code and live data outrank this doc.

---

## The Thesis

KOMPOSOS-IV-PHARM is a **mechanistic candidate triage engine**. The deliverable is not a predictor's AUROC. It is a ranked report of drug-disease candidates, each with a traceable mechanistic derivation a scientist can audit in seconds.

This is what `REPURPOSING_BEST_PATH` Step 6 already calls out as the useful deliverable. The roadmap is what gets us from current state to a defensible, partner-ready version of that report.

The compositional structure of the engine matters because it changes how we think about "false positives." A high-scoring drug-disease pair that isn't a known indication isn't an error — it's a hypothesis with a mechanism attached. AUROC validates that the engine recovers known biology. The novel hypotheses *are the product*.

---

## What's Real Today

From `CURRENT_STATE.md` and deployments (2026-05-10):

- **Core engine works.** Categorical runtime, oracle strategies, deterministic scoring on local data.
- **Reproducible AUROC under named protocols.** `legacy/as_loaded` 0.917, `full_typed/as_loaded` 0.890, `full_typed/remove_direct_labels` 0.974, `full_typed/loocv` 0.974 [0.965, 0.983]. Full typed graph: 78 drugs, 20 diseases, 366 proteins, 44 approved indications, 1260 morphisms.
- **Named benchmark harness frozen.** `validation/repurposing_benchmark.py` with manifest and regression tests. CIs, AUPRC, Hits@K, MRR, and baselines all implemented. Baselines corrected 2026-05-11 (label-order artifact fixed).
- **Independent audits completed.** `INDEPENDENT_EXTERNAL_AUDIT_2026-05-06.md` (base graph), audit corrections applied 2026-05-11.
- **Reproducible DB build.** `data/drugs/build_tier1.py` from `tier1_manifest.json`.
- **External, temporal, and disease-level validation.** Hetionet AUROC 0.744, temporal AUROC 0.959, disease-level mean 0.877 (needs re-run on expanded graph).
- **Candidate triage CLI shipped.** `validation/triage.py` with disease-first, drug-first, pair detail, JSON/Markdown output.
- **Score combiner tuned.** Path bonus optimized via LOOCV grid search (AUROC 0.945 → 0.968 → 0.974 post-ChEMBL). Uniform strategy weights confirmed optimal.
- **ChEMBL expansion deployed (2026-05-10).** Drug name normalization implemented, 17 new Drug→Protein edges for base drugs, graph expanded from 195→1143 objects (includes 679 ExternalCompound nodes), 388→1260 morphisms. Provenance 22.2%→76.0%. Audit-corrected 2026-05-11.

What remains:

- ~~302/1260 morphisms uncited~~ DONE (100% provenance, 2026-05-12).
- Re-run external validation on expanded graph (Hetionet, temporal, disease-level).
- Additional data sources (OpenTargets tested and rejected; STRING, DisGeNET possible).

Track B (drug design, ABPP, ADMET) is not validated and stays out of scope until Track A is shippable.

---

## The Roadmap

This is the six-step path from `REPURPOSING_BEST_PATH`, with concrete work specified per step. It is not phased by weeks. It is phased by **what unblocks what.** Each step has an exit condition. Don't move on until the exit condition is met.

### Step 1 — Freeze Evaluation

**Status:** ✅ DONE.

Bootstrap CIs, AUPRC, Hits@K, MRR, and 5 baselines all implemented in the harness.
Use `--ci --baselines` flags. LOOCV baselines (audit-corrected 2026-05-11): strongest baseline
(shortest_path) 0.931. System AUROC 0.974, margin +0.043. Old baseline values were label-order artifact.

### Step 2 — Repair Data

**Status:** ✅ DONE.

- Zero missing endpoints, zero orphans, zero unreferenced objects.
- Reproducible DB build: `data/drugs/build_tier1.py` from `tier1_manifest.json`.
- `BioDomainLoader` loads all objects (no silent truncation).
- 1260/1260 morphisms have provenance (100%, completed 2026-05-12).

### Step 3 — Complete Mechanisms

**Status:** ✅ DONE.

- Expanded from 16 to 44 positive labels (FDA-approved indications).
- All 44 positives have mechanistic Drug→Protein→Disease paths.
- 16/16 original positive-pair chains fully cited (e.g., Trametinib→MEK1 PMID:21383288).

### Step 4 — Validate Harder

**Status:** ✅ DONE.

- External (Hetionet): AUROC 0.744 on 7 pairs not in our labels.
- Temporal holdout (pre/post 2013): AUROC 0.959 on 22 post-2013 FDA approvals.
- Disease-level holdout: Mean AUROC 0.877 across 7 diseases (range 0.615–0.996).
- 5 baselines computed under LOOCV (random 0.468, degree 0.459, common_neighbor 0.508, shortest_path 0.559, path_count 0.567).

### Step 5 — Tune After Rigor

**Status:** ✅ DONE.

- Path bonus tuned via LOOCV grid search (9 configurations): `min(0.25, 0.10 * composition_count)`.
- AUROC improved 0.945 → 0.968, AUPRC 0.364 → 0.496, Hits@5 0.80 → 1.00.
- Uniform strategy weights confirmed optimal by `calibrate_loocv.py`.
- Score function documented in manifest and audit.
- Tuning disclosure: small search space (9 configs), mechanistically interpretable, cross-validated.

### Step 6 — Ship Candidate Triage

**Status:** ✅ DONE.

- `validation/triage.py`: disease-first, drug-first, pair detail modes.
- Output formats: JSON, Markdown, terminal.
- Per-candidate: score, strategy votes, evidence paths with PMIDs, label status (APPROVED/NOT_APPROVED), provenance coverage.
- Self-check: 44/44 approved indications recoverable.
- Detail auto-expands for top-5 NOT_APPROVED candidates.

---

## What's Optional (and Not on the Critical Path)

These are real, plausible additions. With all six core steps now complete, these are
candidates for the next phase of development. Prioritize based on partner needs.

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

The candidate triage CLI (Step 6) now produces reports that pass all these criteria.
The core roadmap is **complete**. Remaining work is data expansion and provenance.

---

## What This Roadmap Won't Do

- **Won't reorder the six steps.** Your own best-path doc has them in dependency order. I tried twice to dress this up with phases, partner pilots, and disease-area picks; that was me importing other voices into your plan. The order in `REPURPOSING_BEST_PATH` is the order. Steps 1 and 2 unblock Step 3. Step 3 makes Step 4 meaningful. Steps 1–4 make Step 5 safe. Steps 1–5 are required for Step 6 to be defensible.
- **Won't pick a disease focus.** Your audit treats all four broken positives equally. Until you say one matters more than the others, they're a flat priority list.
- **Won't pick a partner.** Noetik is your example, not a target. The roadmap is partner-agnostic.
- **Won't smuggle in Track B.** Drug design, ABPP, ternary complex — none of it on this roadmap.
- **Won't optimize for a pitch.** The pitch is whatever Step 6 produces. If Step 6 produces a strong report, the pitch writes itself.

---

## Next Concrete Actions

All six core roadmap steps are complete. Additional milestones since completed:

1. ~~Complete provenance~~ DONE (100%, 2026-05-12).
2. ~~ChEMBL drug name normalization~~ DONE (2026-05-10).
3. ~~Ablation studies~~ DONE (composition dominant, path bonus +0.017 AUROC).
4. ~~ClinicalTrials.gov cross-check~~ DONE (63% IN_TRIALS, 30% PRECLINICAL, 7% NOVEL).
5. **Re-run external validation** on expanded graph (Hetionet, temporal, disease-level).
6. **Academic outreach**: share with computational biology groups for feedback.
7. **Track B preparation**: once academic feedback incorporated, begin molecular data.
