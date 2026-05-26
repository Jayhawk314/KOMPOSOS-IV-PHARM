# AUROC Verification And Audit Protocol

Date: 2026-05-06 (original)
Updated: 2026-05-24 (post-PubMed expansion, confidence-weighted path bonus)

## Purpose

The AUROC is a validation metric -- it confirms the ranking is useful. The actual
product is the researcher's audit trail: Drug->Protein->Disease paths with cited
evidence, confidence scores per hop, and strategy vote breakdowns that lead to
clinical trial decisions.

## Current Position (2026-05-24, post-PubMed expansion)

The graph expanded from 1,260 to 4,956 edges via PubMed batch import of 3,145
Protein->Disease associations. After switching to confidence-weighted path scoring,
the full graph AUROC is 0.956 (remove_direct_labels protocol).

Canonical harness:

```powershell
python validation\repurposing_benchmark.py --view full_typed --protocol remove_direct_labels
python validation\repurposing_benchmark.py --view full_typed --protocol remove_direct_labels --quality high
python validation\repurposing_benchmark.py --view full_typed --protocol loocv
```

Add `--ci` for bootstrap 95% confidence intervals (1000 resamples, seed=42).
Add `--baselines` for baseline comparisons (random, degree, common-neighbor,
shortest-path, path-count).

## Verified Metrics (2026-05-24, post-PubMed expansion)

| Graph | Protocol | Morphisms | AUROC | AUPRC | Hits@5 | Hits@10 | MRR |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Full graph | `remove_direct_labels` | 4,912 | 0.956 | 0.537 | 1.00 | 0.70 | 0.079 |
| High conf (>=0.70) | `remove_direct_labels` | 1,242 | 0.959 | 0.498 | 0.80 | 0.70 | 0.075 |

All runs: 78 drugs x 20 diseases = 1,560 pairs, 44 positives, 1,516 negatives.
Path bonus: `min(0.25, 0.04 * sum(path_confidence))`.

### Historical Metrics (2026-05-12, pre-PubMed expansion, 1,260 edges)

| View | Protocol | AUROC | AUPRC | Hits@5 | MRR |
| --- | --- | ---: | ---: | ---: | ---: |
| `legacy` | `as_loaded` | 0.931 | 0.465 | -- | -- |
| `full_typed` | `as_loaded` | 0.887 | 0.135 | 0.00 | 0.00 |
| `full_typed` | `remove_direct_labels` | 0.940 | 0.431 | -- | -- |
| `full_typed` | `loocv` | 0.974 | 0.530 | 1.00 | 0.080 |

These numbers were measured on the pre-expansion graph (1,260 curated edges) with
the old path bonus formula `min(0.25, 0.10 * composition_count)`.

### LOOCV Baselines (2026-05-11, pre-expansion graph)

| Baseline | AUROC |
| --- | ---: |
| shortest_path | 0.931 |
| common_neighbor | 0.918 |
| path_count | 0.596 |
| degree_product | 0.474 |
| random | 0.469 |
| **System** | **0.974** |
| **Margin** | **+0.043** |

The old baseline table (shortest_path 0.559) was a label-order artifact corrected
via audit on 2026-05-11. Baselines have not been re-run on the expanded graph.

## Dataset

Source: `data/drugs/tier1.db`

- 464 objects (1,146 with ExternalCompound nodes loaded), 4,956 morphisms
- 78 drugs, 20 diseases, 366 proteins, 679 ExternalCompound nodes
- 44 Drug->Disease approved indication labels (all FDA-approved, all with PMIDs)
- All 44 positives have mechanistic Drug->Protein->Disease paths
- 4,956/4,956 morphisms have provenance (100%)
- Confidence tiers: 1,286 high (>=0.70), 588 medium (0.40-0.69), 3,082 low (<0.40)
- PubMed batch edges classified: 63 PARTIAL, 960 ORPHAN, 2,122 REJECT
- Reproducible build: `data/drugs/build_tier1.py` from `tier1_manifest.json`

## Scoring System

Eight production strategies, combined via mean + confidence-weighted path bonus:

| Strategy | Role | Alone AUROC | Without AUROC |
| --- | --- | ---: | ---: |
| **composition** | Mechanistic 2-hop paths | 0.969 | 0.929 (-0.045) |
| **topos_logic** | Subobject classifier truth values | 0.947 | 0.970 (-0.004) |
| **binding_evidence** | ABPP + drug properties + Pfam | -- | -- |
| **kan_extension** | Left Kan extension | 0.497 | 0.966 (-0.008) |
| yoneda_pattern | Morphism pattern matching | 0.520 | 0.974 (~0) |
| type_heuristic | Type constraint rules | 0.500 | 0.974 (0) |
| structural_hole | Triangle closure | 0.500 | 0.974 (0) |
| fibration_lift | Fiber-based lifting | 0.500 | 0.974 (0) |

Ablation numbers are from the pre-expansion graph (1,260 edges). Composition
remains the dominant strategy on the expanded graph.

Score aggregation (`validation/repurposing_benchmark.py:score_pair`):
1. Each strategy's best prediction is collected.
2. Simple mean of all strategy confidences.
3. Confidence-weighted path bonus: `min(0.25, 0.04 * sum(path_confidence))`.
4. Final score: `min(1.0, base + path_bonus)`.

The path bonus was changed from `min(0.25, 0.10 * composition_count)` to
confidence-weighted on 2026-05-24. The old formula treated all paths equally
regardless of evidence quality, causing score saturation when 3,696 low-confidence
PubMed edges were added.

Path bonus tuned via LOOCV grid search. Uniform strategy weights confirmed optimal.

## AUROC Formula

AUROC is computed by pairwise comparison:

```text
AUROC = (concordant + 0.5 * tied) / (positives * negatives)
```

For the remove_direct_labels protocol (current canonical, full graph):

```text
positives = 44
negatives = 1516
concordant = 63777
discordant = 2884
tied = 43
AUROC = (63777 + 0.5 * 43) / (44 * 1516)
      = 0.956442
```

Bootstrap CI computed over the combined ranking, 1000 resamples with seed=42.

## Leakage Policy

`CompositionStrategy` finds Drug->Protein->Disease 2-hop paths and does not use
direct Drug->Disease edges.

`ToposLogicStrategy` routes Drug->Disease pairs through pathway support only. It
does not return the direct stored Drug->Disease label.

Profile/analogy strategies (KanExtension, YonedaPattern) can be influenced by
other direct Drug->Disease labels unless those labels are removed or held out.

For scientific claims, use `remove_direct_labels`, LOOCV, disease-level holdout,
temporal holdout, or external validation.

## ClinicalTrials.gov Cross-Check (2026-05-12)

30 top repurposing candidates verified against ClinicalTrials.gov and PubMed:
- 19/30 (63%) IN_TRIALS: human clinical trials exist
- 9/30 (30%) PRECLINICAL: published lab research, no trials
- 2/30 (7%) NOVEL: no significant prior evidence

This validates that the system identifies scientifically plausible candidates.

## Audit Checklist

1. Run the canonical harness commands with `--ci --baselines` and record view,
   protocol, object count, morphism count, drugs, diseases, positives, negatives,
   AUROC, CI, AUPRC, and baseline comparison.
2. Confirm `BioDomainLoader` loads all object rows.
3. Confirm `load_legacy_view()` is the only place using the old truncated view.
4. Inspect composition and topos_logic strategies for direct-edge use.
5. Inspect profile/analogy strategies for direct-label contamination.
6. Verify all 44 positives have mechanistic paths (test exists:
   `test_all_positives_have_mechanistic_paths`).
7. Check provenance: 4,956/4,956 morphisms cited (100%).
8. Treat unlabeled pairs as open-world unknowns, not proven negatives.
9. Confirm LOOCV CI lower bound exceeds all baselines.
10. Verify DB SHA256 matches manifest.

## Recommended Claim Language

Defensible:

> KOMPOSOS-IV-PHARM is a research prototype for drug repurposing over a
> curated drug-target-disease knowledge graph (4,956 edges, 100% provenance).
> Under the remove_direct_labels protocol on 78 drugs x 20 diseases (44
> FDA-approved indications), the eight-strategy scorer with confidence-weighted
> path bonus achieves AUROC 0.956. Every prediction traces to cited evidence
> chains (PMIDs, ChEMBL IDs, FDA NDA numbers) with confidence scores per hop.
> 63% of top repurposing candidates are already in human clinical trials.
> These are internal retrospective ranking metrics under open-world negative
> assumptions.

Do not claim:
- Clinical readiness.
- AUROC without specifying protocol and graph size.
- No leakage without naming the protocol.
- Drug design, Boltz, ABPP, or ADMET validation from Track A metrics.
- "Novel discovery" for candidates that may already be in trials.
- AUROC numbers from the pre-expansion graph (0.974) without noting graph size.

## Completed Audit Work (since 2026-05-06)

- ~~Add external validation~~ DONE (Hetionet AUROC 0.744, 7 pairs)
- ~~Add temporal holdout~~ DONE (AUROC 0.959, 22 post-2013 FDA approvals)
- ~~Add disease-level holdout~~ DONE (mean AUROC 0.877, 7 diseases)
- ~~Complete provenance~~ DONE (4,956/4,956, 100%, 2026-05-24)
- ~~Add reproducible DB build~~ DONE (`data/drugs/build_tier1.py`)
- ~~Resolve unreferenced objects~~ DONE (zero remaining)
- ~~Ablation studies~~ DONE (composition dominant, 2026-05-12)
- ~~ClinicalTrials.gov cross-check~~ DONE (63% IN_TRIALS, 2026-05-12)
- ~~Fix LOOCV baseline label-order bug~~ DONE (2026-05-11)

- ~~PubMed batch import~~ DONE (3,145 edges, 5-layer categorical verification, 2026-05-24)
- ~~Confidence-weighted path bonus~~ DONE (`min(0.25, 0.04 * sum(p.confidence))`, 2026-05-24)
- ~~Binding evidence strategy~~ DONE (8th strategy, ABPP + drug properties + Pfam)
- ~~Triage output fixes~~ DONE (binding dedup, ESM2 summarization, path quality breakdown)

Remaining:
- Re-run LOOCV baselines on expanded graph (4,956 edges)
- Re-run external validation on expanded graph (Hetionet, temporal, disease-level)
- Re-run ablation study on expanded graph
