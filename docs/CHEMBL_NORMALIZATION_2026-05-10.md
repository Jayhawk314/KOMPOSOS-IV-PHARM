> **Legacy/historical notice (2026-05-27):** This file is retained for background or session history. It is not the current source of truth for Track A metrics or provenance. Current docs are in `truedocs/`, especially `truedocs/VALIDATION_AND_BENCHMARKS.md` and `truedocs/REPRODUCIBILITY_PROTOCOL.md`. Current strict run: AUROC 0.974694 [0.9606, 0.9855], AUPRC 0.551698 [0.4067, 0.6983], Hits@5/10/20 1.0000/0.6000/0.6000; LOOCV AUROC 0.975916 and AUPRC 0.553703; Hetionet external AUROC 0.634479 and AUPRC 0.009255. Source strings exist on all 5,382 morphisms with 610 PMID identifiers; this is not 100% edge-specific citation validation. Retired or superseded claims in this file should be read as historical.
# ChEMBL Drug Name Normalization — 2026-05-10

## Summary

Fixed drug name mismatch between ChEMBL imports and base manifest. ChEMBL uses uppercase names with salt forms (e.g., `"IMATINIB MESYLATE"`), while the base manifest uses title-case base names (e.g., `"Imatinib"`). This prevented 989 imported drug-target edges from connecting to the 78 base drugs.

**Status:** Normalization implemented and tested. Expanded graph ready but not yet deployed as default.

## What Was Done

### 1. Normalization Logic Added

Updated `data/drugs/importers/import_chembl_sqlite.py`:

```python
def normalize_drug_name(self, chembl_name: str) -> str:
    """
    Normalize ChEMBL drug name to match base manifest style.

    - Strip salt suffixes (MESYLATE, HYDROCHLORIDE, DIMALEATE, etc.)
    - Title-case the base name
    - Match against existing base drug names
    """
```

**Salt suffixes stripped:** HYDROCHLORIDE, DIHYDROCHLORIDE, MALEATE, DIMALEATE, MESYLATE, BESYLATE, TARTRATE, CITRATE, FUMARATE, DITOSYLATE, TOSYLATE, SUCCINATE, MALONATE, HEMIFUMARATE, SULFATE, PHOSPHATE, SODIUM, POTASSIUM, CALCIUM, ACETATE, BROMIDE, CHLORIDE, NITRATE, ETHYLSUCCINATE, ETABONATE, XINAFOATE, PIVOXIL, AXETIL, DIPIVOXIL, DISOPROXIL, ALAFENAMIDE, MARBOXIL.

### 2. Existing Manifest Re-Normalized

Re-processed `tier1_manifest_chembl.json` to apply normalization to all 989 ChEMBL morphisms:

**Before normalization:**
- ChEMBL morphisms connecting to base drugs: **0**
- All 989 edges pointed to uppercase drug names that didn't exist in base

**After normalization:**
- ChEMBL morphisms connecting to base drugs: **17** (after deduplication)
- Drug names now match: `IMATINIB MESYLATE` → `Imatinib`, `AFATINIB DIMALEATE` → `Afatinib`, etc.

### 3. Validation Testing

Tested normalization on 13 known base drugs — all matched correctly:
- `IMATINIB MESYLATE` → `Imatinib` ✓
- `AFATINIB DIMALEATE` → `Afatinib` ✓
- `ERLOTINIB HYDROCHLORIDE` → `Erlotinib` ✓
- `DABRAFENIB MESYLATE` → `Dabrafenib` ✓
- `ATORVASTATIN CALCIUM` → `Atorvastatin` ✓
- `COBIMETINIB FUMARATE` → `Cobimetinib` ✓
- `LAPATINIB DITOSYLATE` → `Lapatinib` ✓
- And 6 more...

## Impact

### New Mechanistic Edges (17 total)

The following Drug→Protein edges now correctly connect to base drugs:

| Drug | Target | Evidence | Type |
|------|--------|----------|------|
| Afatinib | ERBB4 | ChEMBL:CHEMBL2105712 | inhibits |
| Atorvastatin | HMGCR | ChEMBL:CHEMBL393220 | inhibits |
| Bevacizumab | VEGFA | ChEMBL:CHEMBL1201583 | inhibits |
| Binimetinib | MAP2K2 | ChEMBL:CHEMBL3187723 | inhibits |
| Celecoxib | PTGS2 | ChEMBL:CHEMBL118 | inhibits |
| Cimetidine | HRH2 | ChEMBL:CHEMBL30 | inhibits |
| Cobimetinib | MAP2K2 | ChEMBL:CHEMBL2146883 | inhibits |
| Crizotinib | MST1R | ChEMBL:CHEMBL601719 | inhibits |
| Disulfiram | ALDH2 | ChEMBL:CHEMBL964 | inhibits |
| Doxycycline | MMP1 | ChEMBL:CHEMBL1200699 | inhibits |
| Doxycycline | MMP7 | ChEMBL:CHEMBL1200699 | inhibits |
| Doxycycline | MMP8 | ChEMBL:CHEMBL1200699 | inhibits |
| Doxycycline | MMP13 | ChEMBL:CHEMBL1200699 | inhibits |
| Everolimus | FKBP1A | ChEMBL:CHEMBL1908360 | inhibits |
| Imatinib | ABL1 | ChEMBL:CHEMBL1642 | inhibits |
| Imatinib | PDGFRB | ChEMBL:CHEMBL1642 | inhibits |
| Leflunomide | DHODH | ChEMBL:CHEMBL960 | inhibits |

All 17 are **new** — none were duplicates of existing base edges.

### Performance Improvement

LOOCV benchmark on expanded graph (2026-05-10):

**Metric** | **Base (388 morphisms)** | **Expanded (1260 morphisms)** | **Change**
-----------|--------------------------|-------------------------------|----------
AUROC | 0.968 [0.956, 0.981] | **0.974** | +0.006
AUPRC | 0.496 | 0.515 | +0.019
Hits@5 | 1.00 | 1.00 | —
MRR | 0.077 | 0.078 | +0.001

**Interpretation:** The 17 new mechanistic paths create additional composition opportunities, improving discriminative power. The improvement is modest because most of the 855 other ChEMBL morphisms connect to new drugs (not in the 78-drug base set).

## Files Ready

### Active (Current Default)
- `data/drugs/tier1_manifest.json` — base graph (195 objects, 388 morphisms)
- `data/drugs/tier1.db` — built from base manifest
- All current docs reference this version

### Ready for Deployment
- `data/drugs/tier1_manifest_chembl.json` — expanded graph (464 objects, 1260 morphisms, normalized)
- `data/drugs/tier1_manifest_base.json` — backup of original base manifest
- `data/drugs/importers/import_chembl_sqlite.py` — importer with normalization logic

### Build Note
The build script reported a morphism count mismatch (1260 vs 1377 in manifest). This is expected — the builder deduplicates morphisms by `(source, target, edge_type)` key, removing 117 duplicates from the ChEMBL import.

## Next Steps

### Option 1: Deploy ChEMBL Expansion as New Default
```bash
cp data/drugs/tier1_manifest_chembl.json data/drugs/tier1_manifest.json
python data/drugs/build_tier1.py --force
python validation/repurposing_benchmark.py --view full_typed --protocol loocv --ci --baselines
```

Then update all docs with new metrics (464 objects, 1260 morphisms, AUROC 0.974).

### Option 2: Keep Base as Default, ChEMBL as Expansion Option
Leave current docs unchanged. Document ChEMBL expansion as an alternative build for users who want broader mechanistic coverage.

### Option 3: Re-Import Fresh from ChEMBL SQLite
Use the updated importer with normalization logic to do a clean import from ChEMBL database:
```bash
python data/drugs/importers/import_chembl_sqlite.py \
    --chembl-db chembl_33/chembl_33_sqlite/chembl_33.db \
    --manifest data/drugs/tier1_manifest.json \
    --output data/drugs/tier1_manifest_chembl_fresh.json \
    --min-pchembl 6.0 \
    --limit 1000
```

The normalization will now work automatically during import.

## Technical Details

### Why Some Base Drugs Didn't Match
46 of the 78 base drugs (59%) didn't appear in the ChEMBL import at all. Reasons:
1. ChEMBL `drug_mechanism` table filters to `max_phase = 4` (FDA/EMA approved) with curated mechanisms
2. Some base drugs may come from different sources (Noetik, manual curation)
3. Some base drugs may use alternative names that ChEMBL doesn't recognize as `pref_name`

The 32 that matched (41%) now have 17 new mechanistic edges after deduplication.

### Provenance Coverage
The expanded graph includes ChEMBL evidence IDs but not all map to PMIDs. Coverage breakdown TBD — requires querying the expanded DB.

## Testing Checklist

Before deploying as default:
- [ ] Verify 44 positives still have mechanistic paths (run `tests/test_repurposing_benchmark.py`)
- [ ] Run all 4 benchmark protocols with `--ci --baselines`
- [ ] Run external validation (Hetionet, temporal, disease-level)
- [ ] Query DB to confirm provenance coverage
- [ ] Verify DB SHA256 checksum
- [ ] Check: how many of the 269 new proteins have Disease edges? (tells you if ChEMBL is wired in or latent)

---

**Date:** 2026-05-10
**Author:** Claude Opus 4.6 + James Ray Hawkins
**Status:** Implementation complete, deployment pending decision
