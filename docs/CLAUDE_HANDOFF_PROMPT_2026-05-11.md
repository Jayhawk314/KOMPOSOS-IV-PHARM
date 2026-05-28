> **Legacy/historical notice (2026-05-27):** This file is retained for background or session history. It is not the current source of truth for Track A metrics or provenance. Current docs are in `truedocs/`, especially `truedocs/VALIDATION_AND_BENCHMARKS.md` and `truedocs/REPRODUCIBILITY_PROTOCOL.md`. Current strict run: AUROC 0.974694 [0.9606, 0.9855], AUPRC 0.551698 [0.4067, 0.6983], Hits@5/10/20 1.0000/0.6000/0.6000; LOOCV AUROC 0.975916 and AUPRC 0.553703; Hetionet external AUROC 0.634479 and AUPRC 0.009255. Source strings exist on all 5,382 morphisms with 610 PMID identifiers; this is not 100% edge-specific citation validation. Retired or superseded claims in this file should be read as historical.
# Handoff Prompt for Next Agent - Audit Fix Continuation

Use this prompt with Claude or another coding agent:

```text
We are working in C:\Users\JAMES\github\KOMPOSOS-IV-PHARM.

Please continue from the audit-fix state, not from older docs. Read these files first:

1. AUDIT_FIX_REPORT_2026-05-11.md
2. EXTERNAL_AUDIT_GUIDE.md
3. validation/repurposing_benchmark.py
4. validation/repurposing_benchmark_manifest.json
5. tests/test_repurposing_benchmark.py
6. data/drugs/build_tier1.py
7. data/drugs/tier1_manifest.json

Important context:

- We decided against deploying OpenTargets disease edges.
- Current DB contains zero OpenTargets provenance edges.
- The old LOOCV baseline table was wrong due to label-order mismatch.
- The model AUROC did NOT materially go down:
  - full_typed / remove_direct_labels AUROC: 0.973787
  - full_typed / loocv AUROC: 0.973930
- Corrected strongest LOOCV baseline is high:
  - shortest_path: 0.930739
  - system margin over strongest LOOCV baseline: about +0.043 AUROC
- Therefore, do not claim the system beats baselines by >0.40. The honest claim is a modest improvement over strong graph-topology baselines plus better triage/explanation/evidence tracing.

Changes already made:

- Fixed baseline score/label alignment in validation/repurposing_benchmark.py.
- Added explicit pair-order baseline regression test.
- Added 679 ChEMBL-only missing endpoint nodes as ExternalCompound objects.
- Corrected tier1_manifest.json counts to 1143 objects and 1260 morphisms.
- Made data/drugs/build_tier1.py validate manifest counts, use deterministic timestamps, and create runtime indexes up front.
- Updated validation/repurposing_benchmark_manifest.json with corrected hashes, counts, and baseline values.
- Updated EXTERNAL_AUDIT_GUIDE.md with corrected audit claims.

Verification already run:

- pytest tests/test_repurposing_benchmark.py -q -p no:cacheprovider
  Result: 6 passed
- pytest tests -q -p no:cacheprovider
  Result: 157 passed, 1 warning
- python validation/repurposing_benchmark.py --view full_typed --protocol loocv --baselines
  Result: AUROC 0.973930; strongest baseline shortest_path 0.930739

Current fingerprints:

- Raw DB SHA256:
  F8C1042687B911286B7165A8C41B25165C58284C366C51895CE0AFA61A59142A
- Semantic graph SHA256:
  6AB835134DEC65E141F7B88E6B6DC856E9FDA2DCC3BD74A6903A73F5E77B5C00

Please do the following next:

1. Review the audit-fix diffs for correctness. Do not revert the corrected baseline logic.
2. Update older docs like CLAUDE.md, CURRENT_STATE.md, DEPLOYMENT_2026-05-10.md, SESSION_SUMMARY_2026-05-11.md, and any AUROC summary docs so they no longer repeat the invalid low baseline table or the >0.40 margin claim.
3. Mark external, temporal, disease-level, and OpenTargets experiments as "reported but not fully audit-reproduced" unless executable scripts and frozen held-out artifacts are present.
4. Consider adding a fast JSON/export command for benchmark results so the manifest can be regenerated without hand-editing.
5. Consider optimizing LOOCV baseline runtime; it currently takes around 4 minutes.
6. Consider adding a provenance-quality audit target: every approved positive should have at least one fully cited Drug->Protein->Disease path.
7. Preserve the key scientific interpretation: useful research triage system, not a clinical tool; modest improvement over strong graph baselines; value comes from ranking plus mechanistic explanations and evidence tracing.

Avoid:

- Do not deploy OpenTargets disease edges unless explicitly asked.
- Do not tune the scoring formula just to widen the baseline margin.
- Do not describe unlabeled pairs as confirmed negatives.
- Do not claim external/temporal validation is audit-verified unless it is reproduced from runnable artifacts.
```

