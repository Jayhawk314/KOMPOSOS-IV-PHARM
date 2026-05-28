> **Legacy/historical notice (2026-05-27):** This file is retained for background or session history. It is not the current source of truth for Track A metrics or provenance. Current docs are in `truedocs/`, especially `truedocs/VALIDATION_AND_BENCHMARKS.md` and `truedocs/REPRODUCIBILITY_PROTOCOL.md`. Current strict run: AUROC 0.974694 [0.9606, 0.9855], AUPRC 0.551698 [0.4067, 0.6983], Hits@5/10/20 1.0000/0.6000/0.6000; LOOCV AUROC 0.975916 and AUPRC 0.553703; Hetionet external AUROC 0.634479 and AUPRC 0.009255. Source strings exist on all 5,382 morphisms with 610 PMID identifiers; this is not 100% edge-specific citation validation. Retired or superseded claims in this file should be read as historical.
# Implementation Plan: Latent Protein Wiring & Repurposing Enhancement

**Date**: 2026-05-10
**Context**: Post-ChEMBL expansion deployment
**Priority**: High-impact next steps based on latent protein analysis

---

## Executive Summary

**Current State:**
- 464 objects, 1260 morphisms, AUROC 0.974 [0.965, 0.983]
- **Problem Found**: 313 of 366 proteins (85.5%) are latent — no Disease edges
- **Impact**: ChEMBL expansion added Drug→Protein edges but not Protein→Disease, limiting new mechanistic paths

**Opportunity:**
- Wire in 313 latent proteins with Disease associations
- Could unlock significant AUROC gains (0.974 → 0.98+)
- Create hundreds of new drug-disease hypotheses through existing ChEMBL paths

**Current System Capability:**
- ✅ **Ready for use NOW** — `validation/triage.py` generates repurposing candidates
- ✅ Works for all 20 diseases in graph
- ✅ Finds cheap generics (Mebendazole, Atorvastatin, Metformin)
- ✅ Provides mechanistic explanations with PMIDs
- ⚠️ Research tool only — novel predictions need experimental validation

---

## Phase 1: Quick Wins (30-60 min)

### Task 1.1: Re-run External Validation ⭐ HIGH PRIORITY
**Goal**: Measure true impact of ChEMBL expansion on external datasets

**Commands:**
```bash
# Hetionet external validation (was AUROC 0.744 on base graph)
python validation/external_validation.py --hetionet

# Temporal holdout (was AUROC 0.959 on base graph)
python validation/temporal_holdout.py --cutoff 2013

# Disease-level holdout (was mean 0.877 on base graph)
python validation/disease_holdout.py
```

**Expected Time**: 5-10 minutes

**Why**: ChEMBL expansion may have had more impact than LOOCV suggests. External validation could show bigger improvements.

**Deliverable**: Updated metrics for docs (CURRENT_STATE.md, DEPLOYMENT_2026-05-10.md)

---

### Task 1.2: Generate Cheap Drug Repurposing Report ⭐ HIGH VALUE
**Goal**: Create user-facing report of cheap generic drugs for repurposing

**What to Include:**
- Top 10-20 cheap generic drugs per disease
- Focus on: Mebendazole, Metformin, Atorvastatin, Aspirin, Doxycycline, Cimetidine, Propranolol, Chloroquine, Niclosamide, Auranofin, Disulfiram, Ivermectin, Valproic_Acid, Verapamil
- Score, mechanistic path, PMIDs
- NOVEL vs APPROVED labels
- Cost estimate (generic pricing)

**Script Approach:**
```python
# For each of the 20 diseases:
python validation/triage.py <Disease> --all --json > disease_<name>.json

# Filter for cheap generics in top 20
# Compile into markdown report
```

**Expected Time**: 15-20 minutes

**Deliverable**: `CHEAP_DRUG_REPURPOSING_CANDIDATES.md`

**Value**: This is the MAIN USE CASE — finding cheap approved drugs for new indications

---

## Phase 2: Test OpenTargets Integration (30-60 min)

### Task 2.1: Assess OpenTargets Protein→Disease Coverage
**Goal**: Determine if OpenTargets can wire in the 313 latent proteins

**Approach:**
```python
# 1. Extract your 366 protein gene symbols
python -c "
import sqlite3
conn = sqlite3.connect('data/drugs/tier1.db')
c = conn.cursor()
c.execute('SELECT name FROM objects WHERE type_name NOT IN (\"Drug\", \"Disease\")')
proteins = [row[0] for row in c.fetchall()]
with open('proteins_to_check.txt', 'w') as f:
    f.write('\n'.join(proteins))
"

# 2. Query OpenTargets for these proteins
# Use existing importer: data/drugs/importers/import_opentargets.py
python data/drugs/importers/import_opentargets.py \
    --genes-file proteins_to_check.txt \
    --output opentargets_test.json \
    --min-score 0.5 \
    --limit 1000

# 3. Analyze overlap
python -c "
import json
with open('opentargets_test.json') as f:
    data = json.load(f)

# How many of your 366 proteins have disease associations?
# How many diseases overlap with your 20?
# How many NEW diseases would be added?
"
```

**Expected Time**: 30 minutes

**Key Questions to Answer:**
1. How many of the 313 latent proteins get Disease edges from OpenTargets?
2. What % of associations map to your existing 20 diseases?
3. How many NEW diseases would need to be added?
4. Are the associations well-cited (have PMIDs)?

**Decision Criteria:**
- **Deploy if**: >50% of latent proteins get wired in, >30% map to existing diseases
- **Expand diseases if**: Many proteins map to diseases not in your current 20
- **Skip if**: Poor overlap (<30% of latent proteins covered)

---

### Task 2.2: Estimate AUROC Impact
**Goal**: Predict performance improvement before full deployment

**Approach:**
```python
# Add a sample of OpenTargets Protein→Disease edges to a test manifest
# Rebuild test DB
# Run LOOCV on test DB
# Compare AUROC: current 0.974 vs test

# If test shows +0.01 to +0.02 improvement → deploy full
# If test shows +0.005 improvement → consider cost/benefit
# If test shows no improvement → investigate why
```

**Expected Time**: 20 minutes

---

## Phase 3: Deploy OpenTargets (1-2 hours) — Conditional

### Task 3.1: Full OpenTargets Protein→Disease Import
**Only proceed if Phase 2 test is promising (>50% coverage, >30% overlap)**

**Steps:**
1. Run full OpenTargets import for all 366 proteins
2. Add Protein→Disease morphisms to manifest
3. Add new Disease objects if needed (expand from 20 → ?)
4. Rebuild tier1.db from updated manifest
5. Run full benchmark suite (LOOCV, remove_direct_labels, as_loaded)
6. Compare AUROC before/after

**Command:**
```bash
python data/drugs/importers/import_opentargets.py \
    --genes-file proteins_to_check.txt \
    --manifest data/drugs/tier1_manifest.json \
    --output data/drugs/tier1_manifest_opentargets.json \
    --min-score 0.5

# Backup current manifest
cp data/drugs/tier1_manifest.json data/drugs/tier1_manifest_chembl_only.json

# Deploy OpenTargets expansion
cp data/drugs/tier1_manifest_opentargets.json data/drugs/tier1_manifest.json
python data/drugs/build_tier1.py --force

# Run benchmarks
python validation/repurposing_benchmark.py --view full_typed --protocol loocv --ci --baselines
python validation/repurposing_benchmark.py --view full_typed --protocol remove_direct_labels --ci
```

**Expected Time**: 1-2 hours

**Expected Impact:**
- Graph: 464 → 500-600 objects (if new diseases added)
- Morphisms: 1260 → 2000-3000 (with Protein→Disease edges)
- AUROC: 0.974 → 0.98-0.99 (if wiring is effective)
- Latent proteins: 313 → <100

**Deliverable**: Updated deployment doc with OpenTargets metrics

---

## Phase 4: Provenance Completion (Ongoing)

### Task 4.1: Prioritize High-Value Uncited Edges
**Current**: 302 uncited morphisms (24% of 1260)

**Priority Order:**
1. **Drug→Protein edges** (highest value for repurposing)
2. **Protein→Disease edges** (mechanistic explanations)
3. **Protein→Protein edges** (lower priority)

**Tool:**
```bash
python validation/generate_citation_worksheet.py > citations_todo.md
```

**Approach:**
- Focus on edges used in top predictions
- Use PubMed search: "[Drug] [Protein] mechanism"
- Batch process by pathway (e.g., all BRAF pathway edges)

**Target**: 76% → 90%+ provenance coverage

**Expected Time**: 5-10 hours spread over multiple sessions

---

## Phase 5: Documentation & Dissemination

### Task 5.1: Create User-Facing Repurposing Guide
**Deliverable**: `REPURPOSING_USER_GUIDE.md`

**Contents:**
- How to query for repurposing candidates
- Interpreting scores and evidence chains
- Limitations and caveats
- Example queries for all 20 diseases
- Top cheap generic candidates

### Task 5.2: Update All Metrics (if OpenTargets deployed)
**Files to Update:**
- CLAUDE.md
- MEMORY.md
- CURRENT_STATE.md
- MASTER_TECHNICAL.md
- DEPLOYMENT_2026-05-10.md (or create new DEPLOYMENT_2026-05-11.md)
- EXTERNAL_AUDIT_GUIDE.md

---

## Implementation Priority

### This Session (or Next):
1. ✅ **Task 1.1**: Re-run external validation (5-10 min)
2. ✅ **Task 1.2**: Generate cheap drug report (15-20 min)
3. ✅ **Task 2.1**: Test OpenTargets coverage (30 min)
4. ⏸️ **Task 2.2**: Estimate AUROC impact (20 min)

**Total**: ~1.5 hours for quick wins + OpenTargets test

### If OpenTargets Test is Promising:
5. **Task 3.1**: Deploy full OpenTargets import (1-2 hours)
6. **Task 5.1**: Create repurposing user guide (30 min)
7. **Task 5.2**: Update all docs (30 min)

### Ongoing (Multiple Sessions):
8. **Task 4.1**: Complete provenance (5-10 hours, batched)

---

## Decision Tree

```
START
  │
  ├─> Re-run external validation (Task 1.1)
  │   └─> Document results
  │
  ├─> Generate cheap drug report (Task 1.2)
  │   └─> DELIVERABLE: Repurposing candidates ready for use
  │
  ├─> Test OpenTargets coverage (Task 2.1)
      │
      ├─> >50% coverage, >30% overlap?
      │   │
      │   YES ─> Estimate AUROC impact (Task 2.2)
      │   │     │
      │   │     ├─> +0.01+ improvement predicted?
      │   │     │   │
      │   │     │   YES ─> Deploy full OpenTargets (Task 3.1)
      │   │     │   │     └─> Update docs (Task 5.2)
      │   │     │   │
      │   │     │   NO ─> Investigate why / Skip for now
      │   │     │
      │   NO ─> Consider alternatives:
      │         - DisGeNET instead of OpenTargets
      │         - Manual curation of key proteins
      │         - Focus on provenance instead
```

---

## Alternative Paths (if OpenTargets doesn't work)

### Alt 1: DisGeNET Gene-Disease Associations
- ~1M gene-disease associations from literature
- Free download, local SQLite
- May have better coverage than OpenTargets for some proteins

### Alt 2: Manual Curation of High-Value Proteins
- Identify the 50 most important latent proteins (most drug connections)
- Manually curate their disease associations
- Faster than 313, higher impact than random selection

### Alt 3: Focus on Provenance Instead
- Complete citations for 302 uncited morphisms
- Improve defensibility without changing graph structure
- Lower AUROC impact but higher scientific credibility

---

## Success Metrics

### Phase 1 Success:
- ✅ External validation metrics updated and documented
- ✅ Cheap drug repurposing report created
- ✅ Concrete value demonstrated to potential users/partners

### Phase 2 Success:
- ✅ Clear answer: Is OpenTargets worth deploying?
- ✅ Coverage analysis: X% of latent proteins can be wired in
- ✅ Impact estimate: +X AUROC improvement expected

### Phase 3 Success:
- ✅ AUROC improvement: 0.974 → 0.98+
- ✅ Latent proteins reduced: 313 → <100
- ✅ New drug-disease hypotheses unlocked through wired proteins
- ✅ All benchmarks re-run and documented

### Phase 4 Success:
- ✅ Provenance: 76% → 90%+
- ✅ High-value edges (Drug→Protein, Protein→Disease) fully cited

---

## Files Referenced

**Current State:**
- `data/drugs/tier1.db` — Current database (464 objects, 1260 morphisms)
- `data/drugs/tier1_manifest.json` — Current manifest (ChEMBL-normalized)
- `validation/triage.py` — Repurposing candidate CLI

**To Create:**
- `CHEAP_DRUG_REPURPOSING_CANDIDATES.md` — Cheap generic candidates report
- `REPURPOSING_USER_GUIDE.md` — User-facing guide
- `IMPLEMENTATION_PLAN_2026-05-10.md` — This document
- `proteins_to_check.txt` — List of 366 proteins for OpenTargets query
- `opentargets_test.json` — OpenTargets coverage test results

**To Update (if OpenTargets deployed):**
- All core docs (CLAUDE.md, MEMORY.md, CURRENT_STATE.md, etc.)
- New DEPLOYMENT_2026-05-11.md or update existing

---

## Key Insights

### What We Learned:
1. **85.5% of proteins are latent** — biggest untapped opportunity
2. **ChEMBL added breadth but not depth** — many proteins, few wired to diseases
3. **System is ready for use NOW** — triage CLI works, finds cheap generics
4. **External validation needed** — LOOCV doesn't tell full story

### What This Means:
1. **Quick value**: Generate repurposing reports TODAY (Task 1.2)
2. **High impact**: Wire in latent proteins for major AUROC gain (Phase 3)
3. **Low-hanging fruit**: Re-run external validation to show hidden impact (Task 1.1)

### Strategic Direction:
- **Short-term**: Demonstrate value with cheap drug report (users can start using NOW)
- **Medium-term**: Deploy OpenTargets if test is promising (unlock latent proteins)
- **Long-term**: Complete provenance, expand to more diseases, Track B capabilities

---

## Next Session Action Items

**For next Claude session or James:**

1. Load this plan: Read `IMPLEMENTATION_PLAN_2026-05-10.md`
2. Check task list: `TaskList` to see Tasks #1-5
3. Start with Task #1 (external validation) or Task #2 (cheap drug report)
4. If time permits, proceed to Task #3 (OpenTargets test)

**Session priority order:**
- Task 1.2 (cheap drug report) — Shows immediate value
- Task 1.1 (external validation) — Quick metrics update
- Task 2.1 (OpenTargets test) — Informs next major decision

**Estimated time for all Phase 1 + 2 tasks**: 1.5-2 hours

---

**Document Status**: ✅ Complete and ready for next session
**Author**: Claude Opus 4.6 + James Ray Hawkins
**Date**: 2026-05-10
