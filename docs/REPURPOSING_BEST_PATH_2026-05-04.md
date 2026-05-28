> **Legacy/historical notice (2026-05-27):** This file is retained for background or session history. It is not the current source of truth for Track A metrics or provenance. Current docs are in `truedocs/`, especially `truedocs/VALIDATION_AND_BENCHMARKS.md` and `truedocs/REPRODUCIBILITY_PROTOCOL.md`. Current strict run: AUROC 0.974694 [0.9606, 0.9855], AUPRC 0.551698 [0.4067, 0.6983], Hits@5/10/20 1.0000/0.6000/0.6000; LOOCV AUROC 0.975916 and AUPRC 0.553703; Hetionet external AUROC 0.634479 and AUPRC 0.009255. Source strings exist on all 5,382 morphisms with 610 PMID identifiers; this is not 100% edge-specific citation validation. Retired or superseded claims in this file should be read as historical.
# Repurposing Best Path

Date: 2026-05-04 (updated 2026-05-06)

## Decision

Use AUROC as a checkpoint, not the destination.

The best path is to make KOMPOSOS-IV-PHARM a rigorous mechanistic candidate
triage engine. The system should rank existing drugs for diseases, explain the
mechanistic paths behind each rank, disclose uncertainty, and separate approved
labels from hypotheses and unknowns.

## Why the Full DB Matters

The full DB matters for discovery because the tool needs broad drug, disease,
target, pathway, and evidence coverage.

The full DB is not automatically the best AUROC benchmark. A discovery graph can
contain approved labels, hypotheses, weak evidence, incomplete stubs, and future
candidate edges. That is useful for ranking, but it is not clean validation
unless the graph view and label policy are frozen.

Therefore:
- Use the full graph for discovery and drift monitoring.
- Use named validation views for claims.
- Preserve the legacy AUROC only as a compatibility hurdle.

## Current Operating Views

Current values (2026-05-06, 195 objects, 388 morphisms, 44 positives, path bonus tuned):

| View | Protocol | AUROC | CI | AUPRC | Purpose |
| --- | --- | ---: | --- | ---: | --- |
| `legacy` | `as_loaded` | 0.822 | - | 0.280 | Historical hurdle over 28 drugs x 8 diseases |
| `full_typed` | `as_loaded` | 0.890 | [0.852, 0.927] | 0.152 | Full graph monitor over 78 drugs x 20 diseases |
| `full_typed` | `remove_direct_labels` | 0.974 | [0.962, 0.985] | 0.501 | Mechanism/analogy validation with labels removed |
| `full_typed` | `loocv` | 0.968 | [0.956, 0.981] | 0.496 | Leave-one-positive-edge-out validation |
| `discovery_graph` | - | - | - | - | Largest useful graph; not a clean AUROC benchmark |

LOOCV baselines: random 0.468, degree 0.459, common_neighbor 0.508,
shortest_path 0.559, path_count 0.567. CI lower bound (0.956) exceeds all by >0.39.

## Scientific North Star

A strong repurposing result is not just a high AUROC. It should answer:

- Is the drug-disease candidate mechanistically supported?
- Are the support paths independent of the direct approved label?
- Is the evidence traceable to sources?
- Is the candidate novel, already approved, contraindicated, or merely unknown?
- Does it rank above simple baselines?
- Does it survive temporal, disease-level, and external validation?
- Can a scientist inspect why it ranked highly?

## Implementation Roadmap

### 1. Freeze Evaluation — DONE

- Named benchmark harness with views and protocols.
- CIs, AUPRC, Hits@K, MRR, 5 baselines all implemented (`--ci --baselines`).
- Benchmark manifest with DB checksum, counts, positive labels, metrics.

### 2. Repair Data — DONE

- Zero missing endpoints, zero orphans. 195 objects, 388 morphisms.
- Reproducible DB build: `data/drugs/build_tier1.py` from `tier1_manifest.json`.
- 86/388 morphisms have PMIDs (22.2%). 302 uncited morphisms remain.

### 3. Complete Mechanisms — DONE

- Expanded from 16 to 44 positive labels (FDA-approved, all with PMIDs).
- All 44 positives have mechanistic Drug→Protein→Disease paths.
- All original mechanistic gaps resolved (BCR-ABL/CML, AMPK/T2D, VEGFA/CRC, MEK/Melanoma).

### 4. Validate Harder — DONE

- External (Hetionet): AUROC 0.744 on 7 pairs.
- Temporal (pre/post 2013): AUROC 0.959 on 22 post-2013 FDA approvals.
- Disease-level holdout: Mean AUROC 0.877 across 7 diseases.
- 5 baselines under LOOCV (all < 0.57).

### 5. Tune After Rigor — DONE

- Path bonus tuned via LOOCV grid search: `min(0.25, 0.10 * composition_count)`.
- AUROC 0.945 → 0.968, AUPRC 0.364 → 0.496, Hits@5 0.80 → 1.00.
- Uniform strategy weights confirmed optimal.
- Tuning disclosed: small search space (9 configs), mechanistically interpretable.

### 6. Ship Candidate Triage — DONE

- `validation/triage.py`: disease-first, drug-first, pair detail modes.
- Per-candidate: score, strategy votes, evidence paths with PMIDs, label status, provenance coverage.
- Output: terminal (auto-expands top-5 NOVEL), JSON, Markdown.
- Self-check: 44/44 approved indications recoverable.

## Acceptance Criteria For A Serious External Claim

- Reproducible DB build or frozen DB manifest with checksum.
- No silent loader truncation.
- All validation outputs include view, protocol, positive count, negative assumption, and date.
- Direct-label contamination is controlled for scientific claims.
- Positive labels have independent mechanistic support or are excluded from mechanism-only tests.
- AUROC is accompanied by AUPRC/enrichment@K/Hits@K/MRR and uncertainty intervals.
- At least one external validation source is used.
- All claims say "research prototype" until clinical/translational validation exists.
