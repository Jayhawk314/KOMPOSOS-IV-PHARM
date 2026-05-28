> **Legacy/historical notice (2026-05-27):** This file is retained for background or session history. It is not the current source of truth for Track A metrics or provenance. Current docs are in `truedocs/`, especially `truedocs/VALIDATION_AND_BENCHMARKS.md` and `truedocs/REPRODUCIBILITY_PROTOCOL.md`. Current strict run: AUROC 0.974694 [0.9606, 0.9855], AUPRC 0.551698 [0.4067, 0.6983], Hits@5/10/20 1.0000/0.6000/0.6000; LOOCV AUROC 0.975916 and AUPRC 0.553703; Hetionet external AUROC 0.634479 and AUPRC 0.009255. Source strings exist on all 5,382 morphisms with 610 PMID identifiers; this is not 100% edge-specific citation validation. Retired or superseded claims in this file should be read as historical.
# AUROC Verification Protocol

**Purpose**: Protocol for verifying AUROC computation correctness in KOMPOSOS-IV-PHARM
**Audience**: Internal validation, external auditors, and technical reviewers
**Version**: 2026-05-10

---

## Overview

This protocol defines how to independently verify that AUROC values are computed
correctly without methodological errors. It does NOT specify what the AUROC
should be (see `CURRENT_STATE.md` for current values) — it specifies HOW to
verify the computation is correct.

---

## Part 1: Canonical Benchmark Harness

The system provides a single reproducible command-line harness for all AUROC
computations. All claimed metrics must be reproducible using this harness.

### 1.1 Canonical Commands

```powershell
python validation\repurposing_benchmark.py --view legacy --protocol as_loaded
python validation\repurposing_benchmark.py --view full_typed --protocol as_loaded
python validation\repurposing_benchmark.py --view full_typed --protocol remove_direct_labels
python validation\repurposing_benchmark.py --view full_typed --protocol loocv
```

Optional flags:
- `--ci`: Add bootstrap 95% confidence intervals (1000 resamples, seed=42)
- `--baselines`: Add baseline comparisons (random, degree, common-neighbor, shortest-path, path-count)

### 1.2 What Each Protocol Tests

| Protocol | What It Tests | Label Removal Policy |
|----------|---------------|----------------------|
| `as_loaded` | Broad monitoring | No removal (direct edges present) |
| `remove_direct_labels` | Indirect-only scoring | ALL Drug→Disease labels removed |
| `loocv` | Internal validation | One Drug→Disease label held out per fold |

**Primary metric**: `full_typed/loocv` is the most defensible internal validation.

**Strongest claim**: `remove_direct_labels` removes ALL labels and proves scoring
works without direct Drug→Disease edges.

---

## Part 2: AUROC Formula Verification

### 2.1 Correct AUROC Formula

AUROC is computed by pairwise comparison:

```text
AUROC = (concordant + 0.5 * tied) / (positives * negatives)
```

Where:
- **concordant**: number of (pos, neg) pairs where score(pos) > score(neg)
- **discordant**: number of (pos, neg) pairs where score(pos) < score(neg)
- **tied**: number of (pos, neg) pairs where score(pos) == score(neg)

### 2.2 Verification Checklist

**Location**: `compute_auroc()` in `validation/repurposing_benchmark.py`

Verify:
- [ ] All positive pairs have label = 1
- [ ] All negative pairs have label = 0
- [ ] Pairwise comparison counts concordant/discordant/tied correctly
- [ ] AUROC = (concordant + 0.5 * tied) / (P * N)
- [ ] No off-by-one errors
- [ ] No duplicate (drug, disease) pairs counted twice

### 2.3 Bootstrap CI Verification

**Location**: `bootstrap_ci()` in `validation/repurposing_benchmark.py`

Verify:
- [ ] Resamples (score, label) pairs with replacement
- [ ] Skips degenerate resamples (all-positive or all-negative)
- [ ] Uses fixed seed (42) for reproducibility
- [ ] Reports 2.5th and 97.5th percentiles (95% CI)
- [ ] Uses 1000 resamples
- [ ] Resampling is stratified or accounts for class imbalance

---

## Part 3: Data Leakage Verification

### 3.1 LOOCV Label Removal

**Question**: When scoring pair (DrugA, DiseaseB) under LOOCV, is the
Drug→Disease label for that pair removed from the graph?

**Location**: `evaluate_loocv()` in `validation/repurposing_benchmark.py`

**Verification**:
- [ ] Calls `load_full_typed_view(db_path, skip_pair=held_pair)`
- [ ] The `skip_pair` parameter removes the specific Drug→Disease label
- [ ] Strategies cannot access the held-out label during scoring
- [ ] Other Drug→Disease labels remain (standard LOOCV, allows cross-label contamination)

**Expected behavior**: Only the single held-out edge is removed. Other labels
remain to allow profile-based strategies to use cross-label information.

### 3.2 remove_direct_labels Protocol

**Question**: Are ALL Drug→Disease labels removed?

**Location**: `load_full_typed_view()` in `validation/repurposing_benchmark.py`

**Verification**:
- [ ] `skip_all_drug_disease=True` removes all Drug→Disease morphisms
- [ ] Scoring uses only Drug→Protein→Disease indirect paths
- [ ] No direct edges available for composition to skip

**Expected behavior**: All Drug→Disease edges removed. Scoring must rely entirely
on mechanistic and analogical reasoning.

### 3.3 Composition Strategy Edge Skipping

**Question**: Does the composition strategy skip existing edges?

**Location**: `CompositionStrategy` in `oracle/strategies.py` (~line 615-617)

**Verification**:
- [ ] Composition checks if Drug→Disease edge already exists
- [ ] If exists, composition returns None (no prediction)
- [ ] This causes composition to NOT contribute a path bonus for positives in as_loaded

**Expected behavior**: Composition skips existing edges to avoid trivial paths.
This is correct behavior but causes as_loaded metrics to be lower (positives get
no path bonus).

### 3.4 Negative Label Construction

**Critical issue**: Unlabeled Drug→Disease pairs are NOT confirmed negatives.
They are open-world unknowns.

**Location**: `drug_disease_pairs()` in `validation/repurposing_benchmark.py`

**Verification**:
- [ ] All Drug × Disease combinations not in positive set are treated as negatives
- [ ] This is standard practice (see Rephetio: 755 pos vs 29,044 "non-treatments")
- [ ] Documentation discloses this limitation
- [ ] AUROC measures ranking ability, not clinical true/false efficacy

---

## Part 4: Baseline Verification

### 4.1 Baseline Validity

**Location**: `compute_baselines()` in `validation/repurposing_benchmark.py`

Verify:
- [ ] Each baseline uses only graph structure, never strategy scores
- [ ] Labels are identical to those used for the main AUROC
- [ ] Random baseline uses fixed seed (42)
- [ ] Shortest-path and path-count use BFS up to depth 3
- [ ] Baselines are computed on the same graph view as the main AUROC
- [ ] No data leakage: baselines don't access held-out labels in LOOCV

### 4.2 Baseline Comparison

The system's CI lower bound should exceed all baselines. If any baseline exceeds
the system's lower CI bound, the system's performance is not statistically
distinguishable from that baseline.

**Checklist**:
- [ ] All baseline AUROCs are below the system's CI lower bound
- [ ] Margin is substantial (>0.1 recommended for robustness)
- [ ] Baselines were run on same data, same protocol, same labels

---

## Part 5: Score Combination Formula

### 5.1 Current Formula

**Location**: `score_pair()` in `validation/repurposing_benchmark.py`

```python
base = sum(confidence for _, confidence in votes) / len(votes)
path_bonus = min(0.25, 0.10 * composition_count)
return min(1.0, base + path_bonus)
```

### 5.2 Verification Checklist

- [ ] Simple mean of strategy confidences (uniform weights)
- [ ] Path bonus is additive, capped at 0.25
- [ ] Bonus comes from composition path count (Drug→Protein→Disease chains)
- [ ] Final score is capped at 1.0
- [ ] Parameters (0.25 cap, 0.10 multiplier) were tuned via LOOCV grid search

### 5.3 Tuning Bias Note

The path bonus parameters were optimized on the LOOCV protocol. This is a
potential source of optimistic bias (tuning on evaluation set). An auditor should:
- [ ] Note this in any external audit report
- [ ] Verify the grid search was small (9 configurations in original tuning)
- [ ] Verify the improvement is mechanistically interpretable
- [ ] Consider this when interpreting CI bounds (may be slightly optimistic)

---

## Part 6: Regression Test Suite

### 6.1 Automated Tests

```powershell
pytest tests/test_repurposing_benchmark.py -q
pytest tests -q
```

### 6.2 Test Coverage Checklist

- [ ] All 44 positives have mechanistic Drug→Protein→Disease paths
- [ ] Zero missing endpoints in database
- [ ] Zero orphaned objects
- [ ] AUROC computation matches expected formula
- [ ] Bootstrap CI computation is reproducible
- [ ] Baseline computations are deterministic (fixed seeds)

---

## Part 7: External Validation Protocols

### 7.1 Hetionet External Validation

**Purpose**: Score drug-disease pairs confirmed in Hetionet but not in our positive set.

**Checklist**:
- [ ] Exclude all of our 44 known positives
- [ ] Score Hetionet-confirmed pairs as positives
- [ ] Report AUROC on this external set
- [ ] Document overlap limitations (name-matching between databases)

### 7.2 Temporal Holdout Validation

**Purpose**: Remove all post-cutoff FDA approvals, score using pre-cutoff graph.

**Checklist**:
- [ ] Define clear cutoff date (e.g., 2013)
- [ ] Remove all post-cutoff Drug→Disease labels
- [ ] Remove post-cutoff mechanistic knowledge if possible
- [ ] Score held-out approvals
- [ ] Report AUROC and rank distribution

### 7.3 Disease-Level Holdout

**Purpose**: Hold out all positives for each disease, score.

**Checklist**:
- [ ] For each disease with ≥2 positives
- [ ] Hold out all positives for that disease
- [ ] Score using remaining graph
- [ ] Report per-disease AUROC
- [ ] Report mean and weighted mean across diseases

---

## Part 8: Documentation Cross-Check

### 8.1 Claimed Values

All AUROC claims in documentation must:
- [ ] Specify the view (legacy, full_typed)
- [ ] Specify the protocol (as_loaded, remove_direct_labels, loocv)
- [ ] Specify the pair count and positive count
- [ ] Include 95% CI if claiming statistical significance
- [ ] Include AUPRC alongside AUROC

### 8.2 Files to Cross-Check

- [ ] `CLAUDE.md` - current metrics table
- [ ] `CURRENT_STATE.md` - current metrics table
- [ ] `MEMORY.md` - current metrics summary
- [ ] `DEPLOYMENT_*.md` - deployment-specific metrics
- [ ] `INDEPENDENT_EXTERNAL_AUDIT_*.md` - external audit reports

---

## Part 9: Database Verification

### 9.1 Reproducible Build

The database must be reproducible from the manifest:

```powershell
python data/drugs/build_tier1.py --force
```

**Checklist**:
- [ ] Build completes without errors
- [ ] Object count matches manifest
- [ ] Morphism count matches manifest (within deduplication tolerance)
- [ ] All provenance fields preserved
- [ ] Database SHA256 checksum is documented

### 9.2 Database Integrity

```powershell
python -c "
import sqlite3
conn = sqlite3.connect('data/drugs/tier1.db')

# Check for orphans
c = conn.cursor()
c.execute('''
    SELECT COUNT(*) FROM objects o
    WHERE NOT EXISTS (SELECT 1 FROM morphisms WHERE source = o.name)
    AND NOT EXISTS (SELECT 1 FROM morphisms WHERE target = o.name)
''')
print(f'Orphans: {c.fetchone()[0]}')

# Check for missing endpoints
c.execute('''
    SELECT COUNT(*) FROM morphisms m
    WHERE NOT EXISTS (SELECT 1 FROM objects WHERE name = m.source)
    OR NOT EXISTS (SELECT 1 FROM objects WHERE name = m.target)
''')
print(f'Missing endpoints: {c.fetchone()[0]}')
"
```

**Checklist**:
- [ ] Zero orphan objects
- [ ] Zero missing morphism endpoints
- [ ] All Drug objects have type_name = 'Drug'
- [ ] All Disease objects have type_name = 'Disease'

---

## Summary Checklist

Use this checklist for any AUROC verification:

- [ ] Reproduced all 4 canonical benchmark commands
- [ ] AUROC values match claimed values (±0.003)
- [ ] CI bounds are within ±0.01 of claimed values
- [ ] All baselines fall below system's CI lower bound
- [ ] LOOCV removes held-out labels correctly
- [ ] remove_direct_labels removes ALL Drug→Disease labels
- [ ] Negative labels are acknowledged as open-world unknowns
- [ ] Score combination formula is correct and documented
- [ ] Tuning bias (if any) is disclosed
- [ ] Regression tests pass
- [ ] Database integrity verified (zero orphans, zero missing endpoints)
- [ ] All documentation cross-checked and consistent

---

**Version**: 2026-05-10
**See also**: `EXTERNAL_AUDIT_GUIDE.md` for complete external audit protocol
