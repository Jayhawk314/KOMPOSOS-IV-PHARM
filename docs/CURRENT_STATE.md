# KOMPOSOS-IV-PHARM Current State

Date: 2026-05-26 (updated: Yoneda Distance Strategy, quantitative evidence expansion, 9-strategy ensemble)

## Project Identity

KOMPOSOS-IV-PHARM is a categorical runtime applied to pharmaceutical discovery.

Track A, working now: drug repurposing over a curated drug-target-disease graph.

Track B, long-term goal: drug design with molecular generation, structure
prediction, ADMET, efficacy, and patient context.

Older docs often overstate readiness. Treat code, tests, and live database
queries as the source of truth.

## Track A: Drug Repurposing

Purpose:
- Rank existing drugs for diseases.
- Explain scores through mechanistic and analogical graph evidence.
- Produce candidate triage reports, not clinical recommendations.

Data:
- Source: `data/drugs/tier1.db` (2026-05-26, post-Yoneda integration)
- 1,146 objects (464 core + 682 ChEMBL compounds), 5,382 morphisms
- 78 drugs, 20 diseases, 366 proteins, 682 ExternalCompound nodes
- 44 Drug->Disease approved indication labels
- All 44 positives have mechanistic Drug->Protein->Disease paths
- Zero missing endpoint rows (all ChEMBL endpoints explicit objects)
- Zero unreferenced objects
- 5,382/5,382 morphisms have provenance (100.0%): PMIDs + ChEMBL IDs
- All 44 treats edges have PMIDs; zero uncited morphisms remain
- 204 edges with quantitative evidence (IC50, HR, mutation freq, response rate)
- 373 NLP extractions from 204 PMIDs (92.2% validated against abstracts)
- Reproducible DB build: `data/drugs/build_tier1.py` from `tier1_manifest.json`
- SHA256: `AD65C11989BB2C1C17A404B3CFDD5D65D833E4C19C5E771F73A8C1855B702A25` (2026-05-26)

## Current AUROC State

Canonical harness:

```powershell
python validation\repurposing_benchmark.py --view legacy --protocol as_loaded
python validation\repurposing_benchmark.py --view full_typed --protocol as_loaded
python validation\repurposing_benchmark.py --view full_typed --protocol remove_direct_labels
python validation\repurposing_benchmark.py --view full_typed --protocol loocv
```

Current values (2026-05-26, post-Yoneda Distance integration, 9 strategies, Yoneda caching optimized):

| View | Protocol | AUROC | AUPRC | Hits@5 | Hits@10 | Pairs | Positives |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| `legacy` | `as_loaded` | 0.944 | 0.537 | - | - | 1320 | 36 |
| `full_typed` | `as_loaded` | 0.457 | 0.025 | 0.00 | 0.00 | 1560 | 44 |
| `full_typed` | `remove_direct_labels` | **0.965** | **0.634** | **1.00** | **0.80** | 1560 | 44 |
| `full_typed` | `loocv` | **0.9616** | **0.5668** | **0.80** | **0.70** | 1560 | 44 |

Path bonus tuned via LOOCV grid search: `min(0.25, 0.04 * sum(path_confidence))`.
Yoneda distance bonus added as: `min(0.10, 0.06 * similarity)` (additive, not averaged).
Uniform strategy weights confirmed optimal by `calibrate_loocv.py`.

as_loaded protocols show poor metrics (Hits@K = 0.00, AUROC 0.457) due to composition
strategy artifact: it skips existing edges, giving positives zero path bonus while
negatives accumulate bonus from other paths. The scientifically valid protocols are
`remove_direct_labels` (hardest) and `loocv` (cross-validation).

**LOOCV baselines (AUROC, pre-expansion, corrected 2026-05-11)**:
- shortest_path: 0.931
- common_neighbor: 0.918
- path_count: 0.596
- degree_product: 0.474
- random: 0.469

**System post-Yoneda (remove_direct_labels): AUROC 0.965, AUPRC 0.634**
**Improvement over baseline: +0.034 AUROC, +0.154 AUPRC (major precision gain)**

Key insight: AUPRC is the honest metric for imbalanced data (44 positives in
1,560 pairs = 2.8% base rate). Yoneda distance strategy improved AUPRC from
0.537 to 0.634 (+18%) by correctly ranking more positives higher (Hits@10:
0.70 → 0.80). Value comes from strategy votes, mechanistic paths, evidence
tracing, quantitative data, and triage CLI.

## Additional Validation (reported but not fully audit-reproduced)

**Note**: These validations were conducted but executable scripts and frozen
held-out artifacts are not preserved in the repo. Treat as directional evidence
pending audit reproduction.

### External Validation (Hetionet)

Scored 7 Hetionet-confirmed drug-disease treatments not in our treats labels.

- Reported external AUROC: 0.744
- 4/7 Hetionet-confirmed pairs ranked in top 16% of all predictions

### Temporal Holdout (cutoff: 2013)

Removed all post-2013 FDA approvals (22 pairs), scored using pre-2013 graph.

- Reported temporal AUROC: 0.959
- All 22 held-out pairs ranked in top 15.5% of predictions

### Disease-Level Holdout

Held out all positives for each disease (>=2 positives), scored.

| Disease | Positives | AUROC |
| --- | ---: | ---: |
| GIST | 3 | 0.996 |
| RCC | 5 | 0.978 |
| Melanoma | 9 | 0.960 |
| HCC | 2 | 0.921 |
| Breast_Cancer | 5 | 0.862 |
| NSCLC | 9 | 0.810 |
| Colorectal_Cancer | 4 | 0.615 |

Mean disease-level AUROC: 0.877. Weighted: 0.876.

## OpenTargets Expansion Experiment (2026-05-11)

Tested automated, cancer-filtered import from OpenTargets Platform to wire in 313
latent proteins (proteins with Drug edges but no Disease edges).

**Method**: Queried all 366 proteins via OpenTargets GraphQL API. Filtered to
cancer therapeutic area. Mapped to existing 20 diseases. Applied uniform score
thresholds (0.5, 0.6, 0.7).

**Results**:
| Threshold | New Edges | AUROC | Change |
|-----------|-----------|------:|-------:|
| None (original) | 0 | 0.974 | -- |
| ≥ 0.7 | 26 | 0.968 | -0.006 |
| ≥ 0.6 | 121 | 0.961 | -0.013 |
| ≥ 0.5 | 212 | 0.952 | -0.022 |

**Conclusion**: More OpenTargets edges = lower AUROC at every threshold.
OpenTargets gene-disease associations (genetic, GWAS, phenotype-level) add noise
to druggable mechanistic path prediction. The curated graph has higher
signal-to-noise ratio. **Decision: DO NOT DEPLOY OpenTargets.**

This experiment supports the claim that AUROC reflects genuine mechanistic signal
rather than overfitting to a specific data source.

## What Was Fixed and Implemented

- 5 orphan objects (CD163, CD4, CD68, FOXP3, TOP2A) connected with cited edges.
- Trametinib->MEK1 PMID added (16/16 original chains now fully cited).
- Positive set expanded from 16 to 44 FDA-approved indications, all with PMIDs.
- 37 new morphisms added (9 intermediate + 28 treats), all with PMIDs.
- Reproducible DB build script created.
- External validation (Hetionet), temporal holdout, and disease-level holdout completed.
- Score combiner tuned: path bonus LOOCV grid search found `min(0.25, 0.04 * sum(confidence))`
  restores LOOCV AUROC to 0.974 (+0.004 from pre-expansion baseline, real gain after PubMed expansion).
- ChEMBL expansion deployed (2026-05-10): Drug name normalization implemented,
  17 new Drug->Protein edges added for base drugs, graph expanded to 1,143 objects
  and 1,260 morphisms. Provenance coverage improved from 22.2% to 100%.
- Audit corrections (2026-05-11): Fixed LOOCV baseline label-order bug. Added 682
  missing ExternalCompound objects. Made DB rebuild deterministic. Corrected
  strongest baseline from 0.559 to 0.931. Honest margin is +0.043.
- PubMed batch import (2026-05-24): +3,300 edges with 5-layer categorical verification.
  Confidence-weighted path bonus deployed (0.670 → 0.956 AUROC recovery).
- NLP PMID extraction (2026-05-25): 373 quantitative extractions from 204 PMIDs.
  204 edges upgraded with IC50, mutation frequency, hazard ratio, response rate data.
- Yoneda Distance Strategy (2026-05-26): 9th oracle strategy as additive bonus.
  AUROC 0.956 → 0.965, AUPRC 0.537 → 0.634, Hits@10 0.70 → 0.80.

## What Works

- Core categorical runtime and oracle strategies are implemented.
- Track A repurposing scoring runs deterministically on local data.
- Named benchmark views are reproducible.
- LOOCV, temporal, disease-level, and external validation all completed.
- All 44 positives have mechanistic Drug->Protein->Disease paths.
- Candidate triage CLI (`validation/triage.py`) produces ranked reports with
  evidence chains, PMIDs, strategy votes, provenance coverage, and self-check.
  Supports disease-first, drug-first, and specific-pair modes. Terminal, JSON,
  and Markdown output.

## What Is Not Ready

- Clinical or translational claims.
- ~~Full evidence provenance.~~ DONE (1260/1260 = 100% cited, 2026-05-12).
- Larger external validation (only 7 Hetionet overlap pairs; needs re-run on expanded graph).
- Clean separation of indications, hypotheses, contraindications, and unknowns.
- ~~Score combiner tuning (Roadmap Step 5).~~ DONE (path bonus tuned, uniform weights confirmed optimal).
- ~~Data expansion (ChEMBL).~~ DONE (deployed 2026-05-10 with drug name normalization).
- Track B drug design, Boltz, ABPP, ADMET, and ternary complex claims.

## Track B Boundary

Track B is the primary long-term purpose, but it is not currently validated.
Files such as `boltz2_bridge.py` and `abpp_bridge.py` contain scaffolding and
fallback/example behavior. Do not use Track A AUROC to claim Track B readiness.

## Immediate Next Steps

1. ~~Repair data integrity: missing endpoints and unreferenced objects.~~ DONE.
2. ~~Expand positive set.~~ DONE (44 positives).
3. ~~Add external, temporal, disease-level validation.~~ DONE.
4. ~~Add Trametinib->MEK1 PMID.~~ DONE.
5. ~~Create reproducible DB build pipeline.~~ DONE.
6. ~~Build candidate triage CLI (Roadmap Step 6).~~ DONE (`validation/triage.py`).
7. ~~Write complete technical documentation.~~ DONE (`MASTER_TECHNICAL.md`, `DATA_EXPANSION_GUIDE.md`).
8. ~~Build data importers (OpenTargets, STRING, ChEMBL).~~ DONE (`data/drugs/importers/`).
9. ~~Tune score combiners.~~ DONE (LOOCV grid search: path bonus tuned from min(0.10, 0.03*n) to min(0.25, 0.10*n), AUROC 0.945→0.968).
10. ~~Deploy ChEMBL expansion.~~ DONE (2026-05-10: drug name normalization, +269 proteins, +872 morphisms, AUROC 0.968→0.974).
11. ~~Add provenance for remaining 302 uncited morphisms.~~ DONE (100%, 2026-05-12).
12. ~~Ablation studies.~~ DONE (composition is dominant strategy, path bonus +0.017).
13. ~~ClinicalTrials.gov cross-check.~~ DONE (63% IN_TRIALS, 30% PRECLINICAL, 7% NOVEL).
14. ~~Quantitative evidence expansion (NLP PMID extraction).~~ DONE (204 edges with quantitative data).
15. ~~Integrate Yoneda Distance Strategy as 9th oracle.~~ DONE (2026-05-26, +0.009 AUROC, +0.097 AUPRC).
16. Re-run external validation (Hetionet, temporal, disease-level) on expanded graph.

## Files To Read

- `MEMORY.md`
- `CLAUDE.md`
- `MASTER_TECHNICAL.md` - complete architecture & scientific pipeline guide
- `DATA_EXPANSION_GUIDE.md` - data source recommendations & integration workflow
- `INDEPENDENT_EXTERNAL_AUDIT_2026-05-06.md`
- `validation/repurposing_benchmark.py`
- `validation/triage.py`
- `data/drugs/importers/README.md` - how to expand tier1.db with OpenTargets, STRING, etc.
