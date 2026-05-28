> **Legacy/historical notice (2026-05-27):** This file is retained for background or session history. It is not the current source of truth for Track A metrics or provenance. Current docs are in `truedocs/`, especially `truedocs/VALIDATION_AND_BENCHMARKS.md` and `truedocs/REPRODUCIBILITY_PROTOCOL.md`. Current strict run: AUROC 0.974694 [0.9606, 0.9855], AUPRC 0.551698 [0.4067, 0.6983], Hits@5/10/20 1.0000/0.6000/0.6000; LOOCV AUROC 0.975916 and AUPRC 0.553703; Hetionet external AUROC 0.634479 and AUPRC 0.009255. Source strings exist on all 5,382 morphisms with 610 PMID identifiers; this is not 100% edge-specific citation validation. Retired or superseded claims in this file should be read as historical.
# Data Expansion Testing Checklist

**Purpose**: Ensure new data sources don't degrade AUROC or introduce data quality issues.

**Use this checklist** every time you:
- Import new data sources (OpenTargets, STRING, ClinicalTrials, DisGeNET)
- Modify confidence thresholds
- Update morphism mapping logic
- Change tier1_manifest.json significantly

---

## Pre-Import Checklist

Before running any importer:

- [ ] **Backup current manifest**
  ```bash
  cp data/drugs/tier1_manifest.json data/drugs/tier1_manifest.backup.json
  cp data/drugs/tier1.db data/drugs/tier1.backup.db
  ```

- [ ] **Record baseline metrics**
  ```bash
  python validation/repurposing_benchmark.py --view full_typed --protocol loocv --ci > baseline_auroc.txt
  cat baseline_auroc.txt
  # Record: AUROC, CI, AUPRC, Hits@5, MRR
  ```

- [ ] **Check disk space** (OpenTargets adds ~30k morphisms, STRING downloads ~200MB)
  ```bash
  df -h  # Need at least 1GB free
  ```

- [ ] **Check internet connection** (importers query APIs)

---

## Import Testing Checklist

### Phase 1: Dry Run (Small Scale)

- [ ] **Test with limit=100**
  ```bash
  python data/drugs/importers/import_opentargets.py \
      --manifest data/drugs/tier1_manifest.json \
      --output tier1_manifest_test.json \
      --limit 100
  ```

- [ ] **Verify output manifest structure**
  ```bash
  python -c "import json; m=json.load(open('tier1_manifest_test.json')); print(f'Objects: {len(m[\"objects\"])}, Morphisms: {len(m[\"morphisms\"])}')"
  ```

- [ ] **Check for duplicate morphisms**
  ```bash
  python -c "import json; m=json.load(open('tier1_manifest_test.json')); pairs=[(x['source'],x['target'],x['name']) for x in m['morphisms']]; print(f'Unique: {len(set(pairs))}, Total: {len(pairs)}, Dupes: {len(pairs)-len(set(pairs))}')"
  ```

- [ ] **Inspect sample morphisms**
  ```bash
  python -c "import json; m=json.load(open('tier1_manifest_test.json')); print(json.dumps(m['morphisms'][-10:], indent=2))"
  ```

**Acceptance**: No duplicates, morphisms have valid source/target/confidence/provenance

### Phase 2: Full Import

- [ ] **Run full import**
  ```bash
  python data/drugs/importers/import_opentargets.py \
      --manifest data/drugs/tier1_manifest.json \
      --output tier1_manifest_opentargets.json \
      --min-score 0.7
  ```

- [ ] **Record import stats**
  ```
  Objects added: _____
  Morphisms added: _____
  Import time: _____ minutes
  ```

- [ ] **Rebuild database**
  ```bash
  python data/drugs/build_tier1.py \
      --manifest tier1_manifest_opentargets.json \
      --output tier1_opentargets.db
  ```

- [ ] **Verify database integrity**
  ```bash
  python audit_db_check.py --db tier1_opentargets.db
  # Check: zero orphans, zero missing endpoints
  ```

### Phase 3: AUROC Validation (CRITICAL)

- [ ] **Run LOOCV benchmark**
  ```bash
  python validation/repurposing_benchmark.py \
      --view full_typed --protocol loocv --ci --baselines \
      --db tier1_opentargets.db > new_auroc.txt
  ```

- [ ] **Compare to baseline**
  ```bash
  echo "=== BASELINE ===" && cat baseline_auroc.txt
  echo "=== NEW ===" && cat new_auroc.txt
  ```

- [ ] **Check acceptance criteria**
  - [ ] AUROC ≥ 0.94 (or within 0.01 of baseline)
  - [ ] AUROC CI lower bound ≥ 0.92
  - [ ] AUPRC not worse than baseline
  - [ ] Hits@5 ≥ 0.75
  - [ ] All baselines still exceeded

**If AUROC < 0.94**:
- [ ] Try increasing `--min-score` (0.8 or 0.9)
- [ ] Check if new morphisms are too low confidence
- [ ] Inspect morphisms with confidence < 0.5
- [ ] Re-run with adjusted thresholds

### Phase 4: Data Quality Checks

- [ ] **Check provenance coverage**
  ```bash
  python audit_pmids.py --db tier1_opentargets.db
  # Record: % morphisms with PMIDs or evidence IDs
  ```

- [ ] **Check mechanistic paths still exist**
  ```bash
  python audit_mechanistic_paths.py --db tier1_opentargets.db
  # All 44 positives should still have paths
  ```

- [ ] **Check for orphan objects**
  ```bash
  python audit_db_check.py --db tier1_opentargets.db | grep -i orphan
  # Should be: "0 unreferenced objects"
  ```

- [ ] **Spot check new morphisms**
  ```bash
  sqlite3 tier1_opentargets.db "SELECT source_name, target_name, name, confidence, provenance FROM morphisms WHERE provenance LIKE 'opentargets%' LIMIT 20;"
  ```

**Acceptance**: Provenance coverage improves, no orphans, paths intact

### Phase 5: Benchmark Regression Tests

- [ ] **Run full test suite**
  ```bash
  pytest tests/test_repurposing_benchmark.py -v
  ```

- [ ] **Check legacy view still works**
  ```bash
  python validation/repurposing_benchmark.py --view legacy --protocol as_loaded
  # Should match historical AUROC ~0.90
  ```

- [ ] **Run external validation**
  ```bash
  python validation/external_validation.py --db tier1_opentargets.db
  # Hetionet AUROC should be ≥0.74
  ```

- [ ] **Run temporal validation**
  ```bash
  python validation/temporal_validation.py --db tier1_opentargets.db --cutoff 2013
  # Temporal AUROC should be ≥0.95
  ```

**Acceptance**: All tests pass, metrics stable or improved

---

## Post-Import Checklist

### If AUROC ≥ 0.94 (SUCCESS ✅)

- [ ] **Replace original manifest**
  ```bash
  cp tier1_manifest_opentargets.json tier1_manifest.json
  ```

- [ ] **Rebuild main database**
  ```bash
  python data/drugs/build_tier1.py
  ```

- [ ] **Update documentation**
  - [ ] Update CURRENT_STATE.md with new object/morphism counts
  - [ ] Update DATA_EXPANSION_GUIDE.md to mark source as "DONE"
  - [ ] Update MEMORY.md with new baseline AUROC

- [ ] **Commit changes**
  ```bash
  git add tier1_manifest.json tier1.db
  git commit -m "Add OpenTargets data: +30k morphisms, AUROC 0.945 maintained"
  ```

- [ ] **Tag release**
  ```bash
  git tag -a v1.1.0-opentargets -m "Tier1.db expanded with OpenTargets"
  git push origin v1.1.0-opentargets
  ```

### If AUROC < 0.94 (FAILURE ⚠️)

- [ ] **Restore backup**
  ```bash
  cp tier1_manifest.backup.json tier1_manifest.json
  cp tier1.backup.db tier1.db
  ```

- [ ] **Analyze failure**
  - [ ] Which morphisms have lowest confidence?
  - [ ] Are new morphisms causing conflicts?
  - [ ] Is the min-score threshold too low?

- [ ] **Debug commands**
  ```bash
  # Find low-confidence morphisms from new source
  sqlite3 tier1_opentargets.db "SELECT * FROM morphisms WHERE provenance LIKE 'opentargets%' AND confidence < 0.5 ORDER BY confidence LIMIT 20;"

  # Check if new morphisms conflict with existing
  sqlite3 tier1_opentargets.db "SELECT m1.source_name, m1.target_name, m1.name, m1.confidence, m1.provenance FROM morphisms m1 JOIN morphisms m2 ON m1.source_name=m2.source_name AND m1.target_name=m2.target_name WHERE m1.provenance LIKE 'opentargets%' AND m2.provenance NOT LIKE 'opentargets%';"
  ```

- [ ] **Adjust and retry**
  - Increase `--min-score` to 0.8 or 0.9
  - Reduce `--limit` to import fewer edges
  - Check morphism type mapping logic

---

## Multi-Source Testing

After importing multiple sources (OpenTargets + STRING + ClinicalTrials):

- [ ] **Check for synergy**
  - AUPRC should improve (more mechanistic paths)
  - Provenance coverage should reach 50%+

- [ ] **Check for conflicts**
  - No duplicate morphisms with different confidences
  - No contradictory provenance

- [ ] **Run combined benchmark**
  ```bash
  python validation/repurposing_benchmark.py --view full_typed --protocol loocv --ci --baselines
  ```

**Acceptance**: AUROC ≥ 0.94, AUPRC ≥ 0.40, Provenance ≥ 50%

---

## Troubleshooting Guide

### Problem: AUROC drops significantly (>0.05)

**Likely causes**:
- Low-confidence morphisms diluting signal
- Incorrect morphism type mapping
- Duplicates with conflicting confidences

**Solutions**:
- Increase `--min-score` threshold
- Review morphism type inference logic
- Check for duplicates: `python -c "..."`

### Problem: Import fails with API error

**Likely causes**:
- No internet connection
- API rate limit exceeded
- API endpoint changed

**Solutions**:
- Check internet: `ping string-db.org`
- Wait 1 hour and retry (rate limit reset)
- Check API documentation for updates

### Problem: No new morphisms added

**Likely causes**:
- All associations already in manifest
- Filter threshold too high
- No existing proteins match new data

**Solutions**:
- Lower `--min-score` threshold
- Check existing proteins: `python -c "import json; m=json.load(open('tier1_manifest.json')); print([o['name'] for o in m['objects'] if o['type']=='Protein'][:20])"`
- Run OpenTargets before STRING (STRING needs existing proteins)

---

## Sign-Off Template

After successful import:

```
DATA IMPORT SIGN-OFF

Source: OpenTargets
Date: 2026-06-XX
Imported by: [Your Name]

METRICS:
- Baseline AUROC: 0.945 [0.921, 0.967]
- New AUROC: ____ [____, ____]
- Delta: ±____
- Acceptance: ✅ PASS / ⚠️ CONDITIONAL / ❌ FAIL

DATA:
- Objects: 195 → ____  (+____)
- Morphisms: 388 → ____ (+____)
- Provenance: 22.2% → ____% (+____%)

CHECKS:
- [ ] AUROC ≥ 0.94
- [ ] Provenance improved
- [ ] No orphans
- [ ] Mechanistic paths intact
- [ ] Tests pass

STATUS: APPROVED FOR PRODUCTION / NEEDS REVISION
```

---

**Created**: 2026-05-06
**Maintained by**: Development team
**Review frequency**: After each data source integration
