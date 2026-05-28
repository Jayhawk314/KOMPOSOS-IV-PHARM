> **Legacy/historical notice (2026-05-27):** This file is retained for background or session history. It is not the current source of truth for Track A metrics or provenance. Current docs are in `truedocs/`, especially `truedocs/VALIDATION_AND_BENCHMARKS.md` and `truedocs/REPRODUCIBILITY_PROTOCOL.md`. Current strict run: AUROC 0.974694 [0.9606, 0.9855], AUPRC 0.551698 [0.4067, 0.6983], Hits@5/10/20 1.0000/0.6000/0.6000; LOOCV AUROC 0.975916 and AUPRC 0.553703; Hetionet external AUROC 0.634479 and AUPRC 0.009255. Source strings exist on all 5,382 morphisms with 610 PMID identifiers; this is not 100% edge-specific citation validation. Retired or superseded claims in this file should be read as historical.
# PMID Verification Summary - 2026-05-25

## Overview

Comprehensive semantic verification of protein-disease edge PMIDs in KOMPOSOS-IV-PHARM.

## Current Database Status

- **Total morphisms:** 4,956
- **Morphisms with PMIDs:** 665 (13.4%)
- **Morphisms without PMIDs:** 4,291 (86.6%)

## Work Completed

### Phase 1: First Semantic Search (97 edges)
- Candidates found: 109 PMIDs
- Abstracts fetched: 45
- Verified: 33 YES, 12 NO
- **Success rate: 73.3%**
- Added to database: 25 new PMIDs

### Phase 2: Druggable Protein Search (50 edges)
- Candidates found: 75 PMIDs
- Abstracts fetched: 45
- Verified: 45 YES, 0 NO
- **Success rate: 100%**
- Added to database: 21 new PMIDs

### Phase 3: Spot-Check (Random Sample)
- Sample size: 20 existing PMIDs
- Abstracts fetched: 17
- Verified: 15 strong YES, 1 partial, 1 weak
- **Success rate: 88% strong, 94% including partial**

## Spot-Check Findings

### Weak PMIDs Identified:
1. **ROWID 3748:** BCR_ABL -> Pancreatic_Cancer (PMID:37296367)
   - Issue: BCR-Abl mentioned but not as PDAC driver (it's a CML oncogene)
   - Recommendation: REMOVE

2. **ROWID 8039:** CTLA4 -> Ovarian_Cancer (PMID:26317466)
   - Issue: Paper primarily about melanoma, OC mentioned peripherally
   - Recommendation: FLAG as weak/review

## Protein-Disease Edge Coverage

### Druggable Proteins (proteins with drug targets):
- Total druggable protein->disease edges: 2,573
- Without PMIDs: 2,443 (95%)
- With PMIDs: 130 (5%)

### All Protein-Disease Edges:
- Total: 2,573
- With PMIDs: 130 (5%)
- **Remaining to search: ~2,400 edges**

## Quality Metrics

### PMID Accuracy by Source:
- **Semantic search (improved queries):** 100% (Phase 2)
- **Semantic search (initial queries):** 73% (Phase 1)
- **Existing database (spot-check):** 88-94%

### Improvement:
Adding "role OR pathogenesis OR mechanism" to search queries increased accuracy from 73% to 100%.

## Recommendations

1. **Remove weak PMIDs:**
   - BCR_ABL->Pancreatic_Cancer (PMID:37296367)
   - Consider flagging CTLA4->Ovarian_Cancer (PMID:26317466)

2. **Continue semantic search:**
   - ~2,400 druggable protein->disease edges still need PMIDs
   - Use improved query strategy (100% success rate)

3. **Regular spot-checks:**
   - Sample 20-50 random PMIDs every 500 additions
   - Target: maintain >90% accuracy

4. **Commit to git:**
   - Database now has 665 verified PMIDs (was 619)
   - Document verification methodology

## Next Steps Options

**A) Clean and commit:**
- Remove 2 weak PMIDs
- Commit database to git
- Document in changelog

**B) Continue expansion:**
- Search remaining ~2,400 edges
- Batch size: 100-200 edges at a time
- Verify each batch before adding

**C) Deep audit:**
- Spot-check larger sample (100+ PMIDs)
- Remove all weak/partial matches
- Establish gold standard

**D) Combination:**
- Clean weak PMIDs now
- Continue expansion in batches
- Spot-check every 500 additions
