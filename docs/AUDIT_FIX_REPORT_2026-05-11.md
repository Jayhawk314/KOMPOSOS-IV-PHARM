> **Legacy/historical notice (2026-05-27):** This file is retained for background or session history. It is not the current source of truth for Track A metrics or provenance. Current docs are in `truedocs/`, especially `truedocs/VALIDATION_AND_BENCHMARKS.md` and `truedocs/REPRODUCIBILITY_PROTOCOL.md`. Current strict run: AUROC 0.974694 [0.9606, 0.9855], AUPRC 0.551698 [0.4067, 0.6983], Hits@5/10/20 1.0000/0.6000/0.6000; LOOCV AUROC 0.975916 and AUPRC 0.553703; Hetionet external AUROC 0.634479 and AUPRC 0.009255. Source strings exist on all 5,382 morphisms with 610 PMID identifiers; this is not 100% edge-specific citation validation. Retired or superseded claims in this file should be read as historical.
# Audit Fix Report - 2026-05-11

## Scope

This pass addressed the external audit findings for the drug repurposing
benchmark without adding OpenTargets disease edges. The goal was to fix audit
mechanics and documentation, not to tune the model to improve results.

## What Changed

### 1. Fixed LOOCV baseline label alignment

Finding: LOOCV system scores were assembled as held-out positives followed by
averaged negatives, but baseline scores were generated in nested `drug x disease`
order. That made the old LOOCV baseline table invalid.

Fix:
- `validation/repurposing_benchmark.py` now uses explicit `(drug, disease)` pair
  ordering for baseline scores.
- LOOCV baselines are computed on the same held-edge fold graphs as the system.
- `tests/test_repurposing_benchmark.py` adds a regression test that reversing
  pair order leaves baseline AUROC unchanged when labels are reversed with it.

Impact:
- System LOOCV AUROC remains high: `0.973930`.
- Corrected strongest LOOCV baseline is much higher than previously reported:
  `shortest_path = 0.930739`.
- The honest margin is about `+0.043 AUROC`, not `>0.40`.

### 2. Fixed manifest and endpoint integrity

Finding: `tier1_manifest.json` declared `morphism_count = 1377` but contained
`1260` morphisms. The graph also had `679` morphism endpoint names missing from
the object table, which were auto-created by the in-memory category loader.

Fix:
- Added the 679 missing ChEMBL-only source endpoints as explicit
  `ExternalCompound` objects.
- Corrected manifest counts to `1143` objects and `1260` morphisms.
- Evaluation drugs remain `78`; the new `ExternalCompound` support nodes are not
  included in the drug-repurposing candidate universe.

Impact:
- Missing endpoint edges: `0`.
- OpenTargets provenance edges: `0`.

### 3. Made DB rebuild audit-stable

Finding: the DB builder used wall-clock timestamps and did not create the same
indexes that `KomposOSStore` creates on open, so rebuild/read cycles could alter
the raw SQLite file hash.

Fix:
- `data/drugs/build_tier1.py` validates manifest counts before writing.
- It uses manifest `build_timestamp` instead of wall-clock time.
- It creates the runtime indexes during build so read-only benchmark runs do not
  mutate the DB file.

Current fingerprints:
- Raw DB SHA256:
  `F8C1042687B911286B7165A8C41B25165C58284C366C51895CE0AFA61A59142A`
- Semantic graph SHA256:
  `6AB835134DEC65E141F7B88E6B6DC856E9FDA2DCC3BD74A6903A73F5E77B5C00`

### 4. Updated audit documentation

Updated `EXTERNAL_AUDIT_GUIDE.md` and
`validation/repurposing_benchmark_manifest.json` with:
- Corrected DB counts and hashes.
- Corrected LOOCV and remove-direct baseline values.
- Clear disclosure that old low LOOCV baselines were a label-order artifact.
- Clearer caveats for external, temporal, disease-level, and OpenTargets claims.

## Current Benchmark Results

| Protocol | AUROC | AUPRC | Strongest Baseline |
|---|---:|---:|---:|
| legacy / as_loaded | 0.917262 | 0.536441 | shortest_path 1.0000 |
| full_typed / as_loaded | 0.890404 | 0.154351 | shortest_path 1.0000 |
| full_typed / remove_direct_labels | 0.973787 | 0.500438 | common_neighbor 0.938864 |
| full_typed / loocv | 0.973930 | 0.515465 | shortest_path 0.930739 |

## Interpretation

The system is still useful, but the strongest defensible claim is narrower:

> KOMPOSOS-IV-PHARM modestly improves over strong graph-topology baselines on
> the current internal drug-repurposing benchmark while providing strategy votes,
> mechanistic paths, and evidence tracing for triage.

It should not be claimed that the system beats simple graph baselines by a huge
margin. The high baseline is scientifically informative: much of the benchmark
signal is already encoded in the curated mechanistic graph.

## Verification

Commands run:

```powershell
python data/drugs/build_tier1.py --force
pytest tests/test_repurposing_benchmark.py -q -p no:cacheprovider
pytest tests -q -p no:cacheprovider
python validation/repurposing_benchmark.py --view full_typed --protocol loocv --baselines
```

Results:
- Focused benchmark tests: `6 passed`.
- Full test suite: `157 passed, 1 warning`.
- The full suite still prints a Windows `torchvision` native-extension fatal
  exception trace after pytest summary, but pytest returned exit code 0.

## Remaining Audit Risks

- External, temporal, and disease-level validation claims still need preserved,
  executable scripts and frozen held-out datasets before being treated as fully
  audit-reproduced.
- Unlabeled drug-disease pairs are open-world unknowns, not confirmed negatives.
- Path bonus parameters were tuned on the internal LOOCV setting, so AUROC may
  still be optimistic.
- Provenance is incomplete: `302/1260` morphisms remain `unknown`, and not every
  approved positive has a fully cited mechanistic path.
- Clinical use remains out of scope. This is a research triage system, not a
  clinical decision tool.
