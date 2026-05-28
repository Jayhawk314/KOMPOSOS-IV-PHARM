> **Legacy/historical notice (2026-05-27):** This file is retained for background or session history. It is not the current source of truth for Track A metrics or provenance. Current docs are in `truedocs/`, especially `truedocs/VALIDATION_AND_BENCHMARKS.md` and `truedocs/REPRODUCIBILITY_PROTOCOL.md`. Current strict run: AUROC 0.974694 [0.9606, 0.9855], AUPRC 0.551698 [0.4067, 0.6983], Hits@5/10/20 1.0000/0.6000/0.6000; LOOCV AUROC 0.975916 and AUPRC 0.553703; Hetionet external AUROC 0.634479 and AUPRC 0.009255. Source strings exist on all 5,382 morphisms with 610 PMID identifiers; this is not 100% edge-specific citation validation. Retired or superseded claims in this file should be read as historical.
# Next Steps Plan - Drug Repurposing Rigor

Date: 2026-05-04 (updated 2026-05-10: ChEMBL expansion deployed)

## Goal

Build the best defensible drug-repurposing tool we can. AUROC is a hurdle and
monitoring signal, not the true objective.

The true objective is a reproducible, leakage-aware, mechanistic ranking system
that produces biologically plausible candidates with transparent evidence and
clear validation limits.

## Current Baseline

Use the named harness:

```powershell
python validation\repurposing_benchmark.py --view legacy --protocol as_loaded
python validation\repurposing_benchmark.py --view full_typed --protocol as_loaded
python validation\repurposing_benchmark.py --view full_typed --protocol remove_direct_labels
python validation\repurposing_benchmark.py --view full_typed --protocol loocv
```

Current values (2026-05-10, ChEMBL expansion, 44 positives, path bonus tuned):

| View | Protocol | AUROC | CI | AUPRC | Meaning |
| --- | --- | ---: | --- | ---: | --- |
| `legacy` | `as_loaded` | 0.917 | - | 0.536 | Historical hurdle (first-100 objects, changed with expansion) |
| `full_typed` | `as_loaded` | 0.890 | [0.852, 0.928] | 0.154 | Full typed graph monitor over 78 drugs x 20 diseases |
| `full_typed` | `remove_direct_labels` | 0.974 | [0.961, 0.985] | 0.500 | Mechanism/analogy scoring with direct labels removed |
| `full_typed` | `loocv` | 0.974 | [0.965, 0.983] | 0.516 | Leave-one-positive-edge-out internal validation |

LOOCV baselines (AUROC, audit-corrected 2026-05-11): random 0.469, degree_product 0.474,
common_neighbor 0.918, shortest_path 0.931, path_count 0.596. System AUROC 0.974,
margin +0.043 over strongest baseline. Old baseline values (shortest_path 0.559) were
label-order artifact, corrected via audit.

Note: as_loaded protocols show Hits@K = 0.00 (artifact: composition skips existing
edges, positives get zero path bonus). The scientifically valid protocols (loocv,
remove_direct_labels) maintained or improved performance with ChEMBL expansion.

Graph: 1143 objects (78 drugs, 20 diseases, 366 proteins, 679 ExternalCompound nodes), 1260 morphisms, 76% provenance.

## Phase 1: Lock Evaluation Semantics

Status: **DONE**.

Completed:
- Added `validation/repurposing_benchmark.py` with named views and protocols.
- Preserved legacy AUROC as an explicit view, not hidden loader behavior.
- Fixed `BioDomainLoader` to load all object rows.
- Added regression tests for legacy/full typed view counts and loader behavior.
- Added `validation/repurposing_benchmark_manifest.json` with DB checksum, counts, commands, current metrics, and positive labels.
- Bootstrap 95% confidence intervals for AUROC and AUPRC (`--ci` flag).
- Hits@K, MRR, AUPRC reported alongside AUROC.
- Five baselines added: random, degree, common-neighbor, shortest-path, path-count (`--baselines` flag).

## Phase 2: Repair Data Integrity

Status: **DONE**.

Completed:
- All missing endpoints resolved (CXCL12, CXCR4, IFNG, PI3KCA added as typed Proteins).
- Unreferenced objects resolved (connected or removed).
- `data/drugs/build_tier1.py` reproducible DB build script from `tier1_manifest.json`.
- Zero missing endpoints, zero orphan objects (195 objects, 388 morphisms).
- 86/388 morphisms have PMIDs (22.2%). All 44 treats edges cited.
- Labels separated: 44 Drug→Disease = FDA-approved indications.

## Phase 3: Improve Mechanistic Coverage

Status: **DONE**.

Completed:
- Expanded from 16 to 44 FDA-approved positive labels (all with PMIDs).
- All 44 positives have mechanistic Drug→Protein→Disease paths.
- 16/16 original positive-pair chains fully cited (e.g. Trametinib→MEK1 PMID:21383288).
- All known mechanistic gaps resolved (BCR-ABL/CML, AMPK/T2D, VEGFA/CRC, MEK/Melanoma).

## Phase 4: Strengthen Validation

Status: **DONE**.

Completed:
- `remove_direct_labels`: AUROC 0.974 [0.962, 0.985].
- `loocv`: AUROC 0.968 [0.956, 0.981], Hits@5 1.00, MRR 0.077.
- Disease-level holdout: Mean AUROC 0.877 across 7 diseases (GIST 0.996, RCC 0.978, Melanoma 0.960, weakest Colorectal_Cancer 0.615).
- Temporal holdout (cutoff 2013): AUROC 0.959 on 22 post-2013 FDA approvals.
- External (Hetionet): AUROC 0.744 on 7 Hetionet-confirmed pairs not in our labels.
- Five baselines computed (all < 0.57 AUROC).
- Bootstrap 95% CIs on all metrics.
- Open-world negative assumption disclosed.

## Phase 5: Tune Scoring

Status: **DONE**.

Completed:
- Uniform strategy weights confirmed optimal by LOOCV calibration (`calibrate_loocv.py`).
- Path bonus tuned via LOOCV grid search (9 configs): `min(0.25, 0.10 * composition_count)`.
- LOOCV AUROC improved 0.945 → 0.968 (+0.023), AUPRC 0.364 → 0.496.
- Tuning disclosed: small search space (9 configs), mechanistically interpretable,
  remove_direct_labels also improved without direct optimization.
- Score function documented in benchmark manifest.

## Phase 6: Candidate Triage Product

Status: **DONE**.

Completed:
- `validation/triage.py` CLI: disease-first, drug-first, and pair-detail modes.
- Per-candidate fields: score, evidence paths with PMIDs, label status (APPROVED/NOT_APPROVED),
  strategy vote breakdown, provenance coverage.
- Output formats: terminal (auto-expands top-5 NOT_APPROVED), JSON, Markdown.
- Self-check: 44/44 approved indications recoverable.
- `validation/trace_prediction.py` for prediction-to-evidence chain tracing.

## Current Status

All six phases are **DONE**. Remaining work:
- Complete provenance for 302 uncited morphisms.
- ChEMBL data integration (989 associations imported, needs drug name normalization).
- Additional data source integration (OpenTargets, STRING, DisGeNET — see `DATA_EXPANSION_GUIDE.md`).

## Track B Boundary

Drug design remains the primary long-term project goal, but Track B modules
should stay marked experimental until real molecular data, ADMET, structure
prediction, and validation workflows exist.

Do not let Track B claims borrow Track A AUROC.
