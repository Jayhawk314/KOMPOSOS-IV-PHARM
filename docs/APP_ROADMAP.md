> **Legacy/historical notice (2026-05-27):** This file is retained for background or session history. It is not the current source of truth for Track A metrics or provenance. Current docs are in `truedocs/`, especially `truedocs/VALIDATION_AND_BENCHMARKS.md` and `truedocs/REPRODUCIBILITY_PROTOCOL.md`. Current strict run: AUROC 0.974694 [0.9606, 0.9855], AUPRC 0.551698 [0.4067, 0.6983], Hits@5/10/20 1.0000/0.6000/0.6000; LOOCV AUROC 0.975916 and AUPRC 0.553703; Hetionet external AUROC 0.634479 and AUPRC 0.009255. Source strings exist on all 5,382 morphisms with 610 PMID identifiers; this is not 100% edge-specific citation validation. Retired or superseded claims in this file should be read as historical.
# Streamlit App Roadmap

## Priority 1: First 15 Minutes (build before outreach)

1. **Export button** -- `st.download_button` with CSV of results table (drug, disease, score, label, paths, PMIDs)
2. **Clickable PMIDs** -- render as `[PMID:12345](https://pubmed.ncbi.nlm.nih.gov/12345)` in st.markdown
3. **ClinicalTrials.gov status** -- add IN_TRIALS / PRECLINICAL / NOVEL column. Source: cross-check data from CHEAP_DRUG_REPURPOSING_CANDIDATES.md (load as lookup dict)
4. **Filtering** -- st.multiselect for label (APPROVED/NOT_APPROVED), slider for min mechanistic paths, slider for min score

## Priority 2: User-specific features (build after first contact responds)

### Cancer Center / Clinical Researcher
- Gene list upload (paste or file) -> show drugs targeting those genes
- Cancer subtype mutation filter (e.g., BRAF V600E -> Melanoma drugs)

### Rare Disease (Li-Fraumeni, etc.)
- Pathway browser: pick TP53 -> see all connected drugs and diseases
- Patient mutation profile comparison

### Drug Repurposing Nonprofit (Cures Within Reach, ReDO)
- Batch export: full Drug x Disease score matrix as CSV
- Cost/availability column (generic, branded, estimated price)
- Baseline comparison: show shortest-path rank alongside system rank

### Computational Biologist / Auditor
- Strategy disagreement view: highlight where strategies conflict
- Graph visualization: networkx/pyvis Drug->Protein->Disease path diagram
- Ablation toggle: checkboxes to enable/disable each of 7 strategies, re-score live

## Rule
Ask the contact: "What would make this useful for YOUR workflow?" Build that.
