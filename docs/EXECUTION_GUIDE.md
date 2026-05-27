# Evidence Quantification Execution Guide

**Status:** Phase 1 ✅ Complete | Phase 5 ✅ Built | Ready to extract!

## What's Been Implemented

### ✅ Phase 1: Evidence Tier Classification (COMPLETE)
- **6-tier system** distinguishes MEASURED data from graph coherence
- **4944 morphisms classified:**
  - MEASURED (20.9%): ChEMBL IC50, ABPP experiments
  - ESTABLISHED (7.5%): FDA approvals, KEGG pathways
  - INFERRED (8.3%): ESM2, STRING PPI
  - HYPOTHESIS (1.3%): PubMed AGREE/PARTIAL
  - SPECULATIVE (19.4%): PubMed ORPHAN
  - NOISE (42.7%): PubMed REJECT

- **UI updated** to show tier breakdown for each candidate
- **Database schema** extended with evidence_tier, quantitative_value, value_unit columns

### ✅ Phase 5: NLP Extraction Pipeline (BUILT, ready to run!)
- **Extracts from all 609 PMIDs:**
  - IC50/Ki/Kd binding affinities
  - Clinical response rates (ORR)
  - Hazard ratios (survival)
  - Mutation frequencies
  - Sample sizes

- **Automatic tier upgrade:** High-confidence extractions (≥0.7) upgrade edges to MEASURED
- **Validation report:** Lists all extractions with confidence scores and context

## Quick Start: Extract Quantified PMID Data NOW

```bash
# Install required package (if not already installed)
pip install biopython

# Run NLP extraction on all 609 PMIDs
python scripts/extract_all_pmids.py
```

**This will:**
1. Fetch abstracts from PubMed for all 609 unique PMIDs
2. Extract IC50, response rates, hazard ratios using regex + NLP
3. Update tier1.db with quantitative_value for each extraction
4. Upgrade high-confidence edges to MEASURED tier
5. Generate validation report in `data/pmid_extraction_report.txt`

**Expected output:**
- 150-250 PMIDs with quantitative data (25-40% success rate)
- 300-500 new MEASURED edges (upgraded from HYPOTHESIS)
- Detailed extraction report with confidence scores

**Runtime:** ~10-15 minutes (rate-limited to 3 NCBI requests/second)

## Phase 2-4: Additional Data Sources (optional, can run later)

### Phase 2: Clinical Trial Data
```bash
# Requires manual NCT ID mapping for 44 FDA pairs
python scripts/extract_clinical_trials.py
```

### Phase 3: Data Expansion
```bash
# ESM2 expansion (requires ESM2 model)
python scripts/expand_esm2.py  # TODO: implement

# STRING PPI import
python scripts/import_string_ppi.py  # TODO: implement

# OpenTargets associations
python scripts/import_opentargets.py  # TODO: implement
```

### Phase 4: Bayesian Scoring
```bash
# Hybrid evidence scorer (prefers MEASURED > INFERRED > HYPOTHESIS)
python validation/repurposing_benchmark.py --bayesian  # TODO: implement
```

## Verification

After extraction, verify the results:

```bash
# Check how many edges were upgraded to MEASURED
python -c "
import sqlite3
conn = sqlite3.connect('data/drugs/tier1.db')
cursor = conn.cursor()
cursor.execute(\"SELECT evidence_tier, COUNT(*) FROM morphisms GROUP BY evidence_tier\")
for tier, count in cursor.fetchall():
    print(f'{tier}: {count}')
"

# View extraction report
cat data/pmid_extraction_report.txt
```

## Testing the UI

```bash
# Launch Streamlit app to see evidence tiers in action
streamlit run app.py
```

**What to check:**
1. Click on any disease → Run triage
2. Expand top candidate details
3. Look for "Evidence Quality Tiers" section
4. Should see counts for MEASURED, ESTABLISHED, INFERRED, etc.
5. Edges with extracted IC50 data will show "MEASURED" tier

## Expected Results

**Before extraction:**
- MEASURED: 1033 edges (ChEMBL/ABPP only)
- HYPOTHESIS: 63 edges (PubMed AGREE/PARTIAL)

**After NLP extraction:**
- MEASURED: 1300-1500 edges (+300-500 from NLP)
- Many PubMed edges upgraded with actual IC50/response rate values
- Quantitative data visible in UI and reports

## Validation & Quality Control

The extraction pipeline includes automatic validation:

1. **Range checks:** IC50 should be 0.001-1000 μM, response rates 0-100%
2. **Confidence scores:** 0-1 scale based on pattern strength and value plausibility
3. **Context capture:** ±50 chars around each extraction for manual review
4. **Low-confidence flagging:** Extractions with confidence < 0.5 are marked for review

**Manual validation recommended for:**
- Top 10 NOT_APPROVED candidates per disease
- Any extraction with confidence < 0.6
- Unusual values (IC50 > 100 μM, response rate > 95%)

## Next Steps After Extraction

1. **Review validation report:**
   ```bash
   less data/pmid_extraction_report.txt
   ```

2. **Spot-check high-impact extractions:**
   - For each MEASURED edge, verify the PMID actually supports the value
   - Check context snippets to ensure extraction accuracy

3. **Update scoring system:**
   - Modify `validation/repurposing_benchmark.py` to prefer MEASURED edges
   - Give higher weight to quantified relationships

4. **Run benchmark with new data:**
   ```bash
   python validation/repurposing_benchmark.py --view full_typed --protocol remove_direct_labels
   ```

5. **Generate new triage reports:**
   ```bash
   python validation/triage.py Melanoma --json > melanoma_quantified.json
   ```

## Troubleshooting

**"No module named 'Bio'"**
```bash
pip install biopython
```

**"NCBI rate limit exceeded"**
- The script includes automatic rate limiting (0.4s/request)
- If still hitting limits, increase sleep time in `nlp/pmid_extractor.py` line 209

**"Evidence tier column not found"**
```bash
# Re-run Phase 1 classification
python scripts/classify_evidence_tiers.py
```

**"No quantitative data extracted"**
- Check `data/pmid_extractions.json` for raw extraction results
- Many PMIDs may not contain extractable quantitative data (reviews, hypothesis papers)
- Expected success rate: 25-40% of PMIDs

## Files Created

- `core/evidence_tiers.py` - Evidence tier enum and classification logic
- `scripts/classify_evidence_tiers.py` - Classify all morphisms into tiers
- `nlp/pmid_extractor.py` - NLP extraction engine
- `scripts/extract_all_pmids.py` - Main extraction script for all 609 PMIDs
- `scripts/extract_clinical_trials.py` - ClinicalTrials.gov API extractor
- `data/pmid_extractions.json` - Raw extraction results (after running)
- `data/pmid_extraction_report.txt` - Validation report (after running)

## Database Schema Changes

```sql
-- Added to morphisms table:
ALTER TABLE morphisms ADD COLUMN evidence_tier TEXT DEFAULT 'HYPOTHESIS';
ALTER TABLE morphisms ADD COLUMN quantitative_value REAL;
ALTER TABLE morphisms ADD COLUMN value_unit TEXT;
ALTER TABLE morphisms ADD COLUMN sample_size INTEGER;
ALTER TABLE morphisms ADD COLUMN confidence_lower REAL;
ALTER TABLE morphisms ADD COLUMN confidence_upper REAL;
```

## Commit History

- `4653f15` - Phase 1: Evidence tier classification system
- (Next) - Phase 5: NLP extraction from all PMIDs

## Future Work (Phase 2-4)

- [ ] Complete NCT ID mapping for 44 FDA-approved pairs
- [ ] Implement cBioPortal mutation frequency extraction
- [ ] ESM2 expansion to all 20 diseases
- [ ] STRING PPI high-confidence import
- [ ] OpenTargets gene-disease associations
- [ ] Bayesian evidence integration
- [ ] Uncertainty quantification (confidence intervals)

---

**YOLO MODE ACTIVATED! 🚀**

Run `python scripts/extract_all_pmids.py` to get quantified PMID data RIGHT NOW!
