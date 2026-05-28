> **Legacy/historical notice (2026-05-27):** This file is retained for background or session history. It is not the current source of truth for Track A metrics or provenance. Current docs are in `truedocs/`, especially `truedocs/VALIDATION_AND_BENCHMARKS.md` and `truedocs/REPRODUCIBILITY_PROTOCOL.md`. Current strict run: AUROC 0.974694 [0.9606, 0.9855], AUPRC 0.551698 [0.4067, 0.6983], Hits@5/10/20 1.0000/0.6000/0.6000; LOOCV AUROC 0.975916 and AUPRC 0.553703; Hetionet external AUROC 0.634479 and AUPRC 0.009255. Source strings exist on all 5,382 morphisms with 610 PMID identifiers; this is not 100% edge-specific citation validation. Retired or superseded claims in this file should be read as historical.
# Provenance Architecture

Last updated: 2026-05-26

## Overview

Every morphism (edge) in tier1.db has a `provenance` field that documents
where the data came from. This is the audit trail -- a researcher can trace
any prediction back to its source.

**Current state: 5,382/5,382 morphisms have provenance (100%)**

The graph has grown from 1,260 curated edges to 5,382 edges through:
- PubMed batch import of 3,300+ Protein->Disease associations (2026-05-24)
- NLP quantitative evidence extraction from 204 PMIDs (373 data points, 2026-05-25)
- ChEMBL expansion and drug name normalization (2026-05-10)

All edges have citations (PMIDs or ChEMBL IDs) and were processed through categorical
verification or quantitative validation. 204 edges now include quantitative values
(IC50, mutation frequency, hazard ratio, response rate).

## Data Sources (by count)

| Source | Count | % | Description |
|--------|-------|---|-------------|
| PMID/Literature | 3,754 | 69.7% | PubMed literature citations (3,300 batch-imported + 454 curated/NLP) |
| ChEMBL | 881 | 16.4% | Drug-target binding assays (IC50, Ki, Kd) from ChEMBL database |
| NLP Quantitative | 204 | 3.8% | IC50, mutation frequency, hazard ratio, response rate (373 extractions from 204 PMIDs) |
| ESM-2 | 422 | 7.8% | Protein embeddings, similarity scores from Meta's protein language model |
| FDA | 79 | 1.5% | FDA-approved drug mechanisms with NDA/BLA numbers |
| KEGG | 72 | 1.3% | KEGG pathway database (canonical signaling cascades) |
| Curated protein sets | 51 | 0.9% | cancer_proteins.py / aml_proteins.py (curated from STRING/KEGG/Reactome) |
| STRING PPI | 22 | 0.4% | Protein-protein interactions from STRING database |
| ABPP | 17 | 0.3% | Activity-based protein profiling experimental data with PMIDs |
| Pathway inference | 16 | 0.3% | Pathway neighbor inference (protein linked via shared pathway) |
| Established mechanisms | 12 | 0.2% | Well-known pharmacology (COX inhibitors, AMPK activator, etc.) |
| GTEx | 12 | 0.2% | Gene expression from GTEx (tissue specificity) |
| Other | 13 | 0.2% | DepMap, clinical, review, preclinical, CosMx, misc |

## Confidence-Based Quality Tiers

Edges are classified into quality tiers by their assigned confidence value,
which reflects evidence strength:

### Quantitative Tier (NEW, 2026-05-25): 204 edges with real measurements
Edges upgraded from text-only PMID citations to include quantitative values:
- IC50/Ki/Kd binding affinity (nM, μM, mM)
- Mutation frequencies (%)
- Hazard ratios (HR)
- Response rates (% responding)
- All values validated against PubMed abstracts (92.2% accuracy)

### High Confidence (>= 0.70): 1,286 edges, 23.9%
Authoritative databases with reproducible data:
- ChEMBL assay results (IC50, Ki, Kd with assay IDs)
- FDA drug labels (NDA/BLA numbers)
- KEGG pathway database
- ESM-2 protein embeddings (high-similarity pairs)
- STRING PPI database
- ABPP experimental profiling
- Curated literature with PMID verification

### Medium Confidence (0.40 - 0.69): 588 edges, 10.9%
Computationally derived or partially verified:
- ESM-2 moderate-similarity pairs
- PubMed edges classified as PARTIAL (passed some categorical verification)
- Curated protein sets (cancer_proteins.py, aml_proteins.py)
- GTEx expression data

### Low Confidence (< 0.40): 3,508 edges, 65.2%
PubMed batch-imported edges that failed categorical verification:
- ORPHAN (960 edges, conf 0.35): PubMed co-mention, no mechanistic path found
- REJECT (2,122 edges, conf 0.20): Failed categorical verification, treat as noise

## PubMed Batch Import and Categorical Verification

### The Import (2026-05-24)

3,145 Protein->Disease associations were batch-imported from PubMed queries.
Each edge represents a protein-disease pair where at least one PubMed paper
mentions both terms. All edges have PMID citations.

### The 5-Layer Categorical Filter

Every PubMed batch edge was processed through 5 independent verification layers:

1. **Drug Path Witness (HoTT path induction)**: Does any FDA-approved drug
   reach this protein for this disease via a known mechanistic path?
   Score: 1.0 if witnessed, 0.0 if not.

2. **Kan Extension Agreement (Left Kan extension)**: Given the pattern of
   known drug-target associations, does this protein-disease edge fit the
   expected pattern? Score: 0.0-1.0 based on agreement strength.

3. **Mechanistic Reachability (BFS)**: Can this protein be reached from
   known disease-associated proteins via the protein interaction network?
   Score: 1.0 if reachable within 2 hops, 0.5 if 3 hops, 0.0 if unreachable.

4. **Protein Specificity (COG energy)**: Is this protein narrowly associated
   with this disease, or broadly linked to everything? A protein connected to
   all 20 diseases is less informative than one linked to 2-3 diseases.
   Score: higher for specific, lower for promiscuous.

5. **Gray Interchange Coherence (Gray category)**: Does this edge fit
   consistently with the surrounding graph structure? Checks for coherence
   with existing drug-protein and protein-protein edges.
   Score: 0.0-1.0 based on structural fit.

### Delta Classification

The 5 layer scores are combined into a composite score (0-1), and edges are
classified:

| Classification | Score Threshold | Confidence Assigned | Count |
|---------------|----------------|-------------------|-------|
| AGREE | >= 0.6 | 0.75 | 0 |
| PARTIAL | >= 0.3 (with mech support) | 0.45 - 0.54 | 63 |
| ORPHAN | >= 0.1 | 0.35 | 960 |
| REJECT | < 0.1 | 0.20 | 2,122 |

No PubMed batch edges achieved AGREE status (score >= 0.6). This reflects
the difficulty of PubMed co-mention edges meeting all 5 verification criteria.
The 63 PARTIAL edges have some mechanistic backing and are worth investigating.

### Metadata Storage

Each classified edge stores its verification results in the `metadata` JSON field:

```json
{
  "categorical_delta": "PARTIAL",
  "categorical_score": 0.44,
  "layer_scores": {
    "drug_witness": 0.0,
    "kan_agreement": 0.0,
    "mech_reach": 1.0,
    "specificity": 0.6,
    "gray_coherence": 1.0
  },
  "source_file": "pubmed_query"
}
```

This enables full auditability -- any edge's classification can be inspected
and the reasoning behind it understood.

## Provenance Format Examples

```
ChEMBL:CHEMBL941                                    # ChEMBL assay ID
ESM2:similar_to_STAT3(0.97); similar_to_AKT1(0.86) # ESM-2 similarity
PMID:42170277, PMID:42122163                        # PubMed article IDs
FDA:NDA202429, mechanism:BRAF_V600E_inhibitor       # FDA approval + mechanism
KEGG:hsa04010, cancer_proteins.py                   # KEGG pathway + source file
ABPP; PMID:11423618                                 # ABPP experiment + citation
PPI                                                 # STRING protein-protein
established:COX-1_COX-2_inhibitor                   # Known pharmacology
mechanism:DNA_crosslinking_activates_DDR_and_p53    # Known biology
pathway:neighbor_of_MET                             # Pathway proximity
```

## Edge Categories

### Drug -> Protein (inhibits/activates/targets) -- ~960 edges
- **FDA-approved targets** (79): Cite NDA/BLA number. Verifiable at FDA.gov.
- **ChEMBL quantitative** (881 incl. ExternalCompound): IC50/Ki/Kd values.
- **Repurposing hypotheses** (~50): PMID citations to papers proposing the mechanism.
  These are literature claims, not established facts.

### Protein -> Protein (activates/phosphorylates/inhibits) -- ~84 edges
- **KEGG pathway** (72): Canonical signaling cascades (MAPK, PI3K-AKT, p53, etc.)
- **PMID-cited** (12): Specific interactions from literature

### Protein -> Disease (associated_with/driver_of) -- ~3,868 edges
- **Curated** (~109 pre-expansion): Cancer/AML protein sets, literature-verified.
- **PubMed batch** (3,145): Automatically imported, categorically verified.
  Each has PMIDs and delta classification metadata.
- **Driver mutations** (37): Somatic mutations that cause disease (highest confidence).

### Drug -> Disease (treats) -- 44 edges
- **FDA-approved indications**: All 44 are FDA-approved oncology indications with PMIDs.

## Impact of PubMed Expansion on Validation

The expansion from 1,260 to 4,956 edges had measurable impact on benchmark AUROC.
Protocol: `remove_direct_labels` (Drug->Disease edges removed before scoring).
Path bonus: confidence-weighted `min(0.25, 0.04 * sum(path_confidence))`.

| Tier | Edges | AUROC | AUPRC | Hits@5 | Interpretation |
|------|-------|-------|-------|--------|---------------|
| Original curated (pre-expansion) | 1,216 | 0.971 | 0.530 | 1.00 | Baseline: high-quality edges only |
| High confidence (conf >= 0.70) | 1,242 | 0.959 | 0.498 | 0.80 | Near-original performance |
| All evidence (full graph) | 4,912 | 0.956 | 0.537 | 1.00 | Coverage + confidence weighting |

With confidence-weighted path scoring, the full graph achieves near-parity with
the high-confidence tier. Low-confidence edges contribute proportionally less to
path bonuses, so they add coverage without introducing noise. Researchers can use
the full graph for exploration while trusting confidence scores to signal quality.

## Verification Process

When verifying a prediction's audit trail:

1. **Check the Drug->Protein edge**: Is it FDA-cited or ChEMBL-cited? (strongest)
2. **Check the Protein->Disease edge**: What's the PMID? What delta classification?
   - PARTIAL (conf 0.45-0.54): Some mechanistic backing, worth reading the paper
   - ORPHAN (conf 0.35): Co-mention only, verify the paper establishes a mechanism
   - REJECT (conf 0.20): Likely noise, verify independently before trusting
3. **For protein-protein intermediates**: KEGG pathway ID is canonical, no verification needed.
4. **For curated edges**: Check provenance (cancer_proteins.py, aml_proteins.py) and
   the original source they cite (STRING, KEGG, Reactome).

## Files

- `data/drugs/tier1.db`: SQLite database with all edges
- `data/drugs/tier1_manifest.json`: Reproducible build manifest
- `data/drugs/build_tier1.py`: Build script from manifest
- `scripts/filter_pubmed_edges.py`: 5-layer categorical verification pipeline
- `scripts/pubmed_edge_scores.json`: Per-edge verification scores and deltas
- `scripts/unknown_edge_pmids.json`: PubMed query results (round 1)
- `validation/repurposing_benchmark.py`: Benchmark harness with quality tier filters
