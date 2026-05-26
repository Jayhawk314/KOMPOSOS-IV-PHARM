# Data Expansion Guide for KOMPOSOS-IV-PHARM

**Date**: 2026-05-14 (updated: 2026-05-24, PubMed expansion complete)
**Purpose**: Recommendations for expanding tier1.db with high-quality biomedical data sources
**Current State**: 464 objects (1,146 with ExternalCompound), 4,956 morphisms, 44 FDA-approved Drug→Disease labels, **100% provenance coverage**

---

## Current Data Sources in tier1.db

**Existing Sources**:
- **ChEMBL**: 679 ExternalCompound nodes, 881 drug-target bioactivity edges, all with ChEMBL IDs
- **DrugBank**: 78 FDA-approved drugs (oncology focus)
- **Manual curation**: 44 Drug→Disease treats edges (all with PMIDs), 366 proteins
- **PubMed batch import**: 3,145 Protein→Disease associations with PMIDs (categorically verified)
- **Literature mining**: 214 curated Protein-disease associations (all with PMIDs)
- **ESM-2**: 422 protein similarity edges
- **KEGG**: 72 pathway edges
- **STRING PPI**: 22 protein-protein interactions
- **ABPP**: 17 experimental drug-target IC50 entries

**Provenance Status** (2026-05-24):
- **4,956/4,956 morphisms have provenance (100.0%)**
- All 44 Drug→Disease treats edges cited (100%)
- Zero uncited morphisms remain
- PubMed batch edges classified by 5-layer categorical verification:
  PARTIAL (63 edges, conf 0.45-0.54), ORPHAN (960, conf 0.35), REJECT (2,122, conf 0.20)

---

## Recommended Data Sources for Expansion

### Priority 1: Immediate High-Impact Sources

#### 0. ChEMBL SQLite — ✅ DEPLOYED 2026-05-12 (COMPLETE)

**Status**: ChEMBL expansion complete. 100% provenance achieved.

**What was done**:
- Downloaded ChEMBL 36 (5.23 GB) via `chembl-downloader`
- Built importer: `data/drugs/importers/import_chembl_sqlite.py`
- Drug name normalization implemented (salt suffix stripping)
- **Provenance completion** (2026-05-12): All 1260 morphisms now cited
- 679 ExternalCompound nodes added as explicit objects (zero missing endpoint rows)
- 17 new Drug→Protein edges for base drugs

**Impact** (ChEMBL phase):
- Graph: 195→1143 objects, 388→1260 morphisms
- Provenance: 22.2%→**100.0%** (1260/1260 morphisms cited)
- LOOCV AUROC: 0.968→0.974, AUPRC 0.530, Hits@10 1.000, MRR 0.080
- All 44 positive-pair mechanistic chains fully cited

**Subsequently completed**: PubMed batch import (2026-05-24)
- Graph: 1260→4,956 morphisms (+3,696 PubMed Protein→Disease edges)
- remove_direct_labels AUROC: 0.956, AUPRC 0.537, Hits@5 1.00
- Path bonus changed to confidence-weighted: `min(0.25, 0.04 * sum(path_confidence))`

**Next**: Open Targets for target-disease expansion

---

#### 1. OpenTargets (opentargets.org)

**Why**: Best comprehensive drug-target-disease database with genetic evidence.

**What it provides**:
- 50,000+ drug-target-disease triples
- Genetic evidence scores (GWAS, rare variants)
- Clinical trial outcomes
- Known drug mechanisms
- All data has evidence provenance

**Data structure**:
- Drug → Target (proteins/genes)
- Target → Disease
- Evidence strength scores (0-1)
- Aggregates 20+ databases (including ChEMBL, ClinicalTrials.gov, PheWAS)

**Integration plan**:
```python
# Pseudocode
import opentargets_client

# 1. Query for all drug-target associations
drug_targets = client.get_drug_targets(min_score=0.7)

# 2. Add to tier1_manifest.json
for dt in drug_targets:
    objects.append({
        "name": dt.drug_name,
        "type": "Drug",
        "provenance": "opentargets_2026"
    })
    morphisms.append({
        "source": dt.drug_name,
        "target": dt.target_gene,
        "name": "inhibits" or "activates",  # from mechanism
        "confidence": dt.score,
        "provenance": f"OpenTargets:{dt.evidence_id}"
    })

# 3. Rebuild tier1.db
python data/drugs/build_tier1.py --manifest tier1_manifest.json
```

**Expected impact**:
- +30,000 morphisms (drug-target edges)
- +5,000 objects (new proteins/genes)
- Improved mechanistic path coverage (more Drug→Protein→Disease chains)
- Stronger provenance (all edges have evidence IDs)

**API**: Free, REST API, Python client available

---

#### 2. STRING (string-db.org)

**Why**: High-confidence protein-protein interaction network.

**What it provides**:
- 24 million protein-protein interactions
- Confidence scores (0-1000)
- Evidence types (experimental, database, text mining, co-expression)
- PMIDs for experimental evidence

**Data structure**:
- Protein A → Protein B (undirected, but can model as bidirectional)
- Combined score (recommended: use only combined_score > 700 = high confidence)

**Integration plan**:
```python
# Filter for high-confidence human PPIs only
ppi_data = string.get_interactions(species=9606, score_threshold=700)

for ppi in ppi_data:
    morphisms.append({
        "source": ppi.protein_a,
        "target": ppi.protein_b,
        "name": "interacts_with",
        "confidence": ppi.combined_score / 1000,  # Normalize to [0,1]
        "provenance": f"STRING:{ppi.evidence_sources}",
        "metadata": {"pmids": ppi.pubmed_ids}
    })
```

**Expected impact**:
- +500 morphisms (for proteins already in tier1.db)
- Improved composition paths (more intermediates for Drug→Protein→Protein→Disease)
- Boost YonedaPatternStrategy (more morphism profiles)

**API**: Free, downloadable bulk files, REST API

---

#### 8. DGIdb (Drug-Gene Interaction Database) - NEW 2026

**Why**: Aggregates 30+ sources into unified drug-gene interactions.

**What it provides**:
- 70,000+ drug-gene interactions
- 10,000+ genes, 20,000+ drugs
- GraphQL API, Python package (DGIpy)

**Expected impact**: +500-2,000 Drug→Gene edges for existing 78 drugs

**API**: Free, GraphQL at `https://dgidb.org/api/graphql`, TSV downloads

**Reference**: [DGIdb 5.0 (NAR 2024)](https://academic.oup.com/nar/article/52/D1/D1227/7416371)

---

#### 9. Pre-built Knowledge Graphs (for validation/benchmarking)

**DRKG** (Drug Repurposing KG):
- 5.8M triples, 97K entities, pre-trained TransE embeddings
- GitHub: `https://github.com/gnn4dr/DRKG`
- Use: Validation reference, import subgraphs

**PrimeKG** (Precision Medicine KG):
- 4M relationships, 17K diseases, includes contraindications
- Harvard/Zitnik Lab, via Therapeutics Data Commons
- Use: Benchmark against TxGNN predictions

**TxGNN** (Foundation Model):
- Trained on PrimeKG, zero-shot to 17K diseases
- AUPRC improvement: +49.2% (indications), +35.1% (contraindications)
- GitHub: `https://github.com/mims-harvard/TxGNN`
- Use: Compare categorical reasoning vs GNN predictions

**Reference**: [TxGNN (Nature Medicine 2024)](https://www.nature.com/articles/s41591-024-03233-x)

---

### Priority 2: Validation & Evidence Sources

#### 3. ClinicalTrials.gov

**Why**: Real-world clinical trial outcomes for temporal validation.

**What it provides**:
- 450,000+ clinical trials
- Drug-disease pairs with trial outcomes (success/failure)
- Trial start dates (for temporal holdout validation)
- Phase I-IV data

**Use case**:
- **Temporal validation**: Hold out trials started after 2020, score with pre-2020 graph
- **Outcome validation**: Do our high-scoring predictions correlate with trial success?
- **Contraindication detection**: Failed trials = negative labels

**Integration plan**:
```python
# Query for completed trials with results
trials = clinicaltrials.search(status="COMPLETED", has_results=True)

for trial in trials:
    if trial.outcome == "SUCCESS":
        # Add as positive Drug→Disease with trial date
        morphisms.append({
            "source": trial.drug,
            "target": trial.disease,
            "name": "treats",
            "confidence": 0.9 if trial.phase == "PHASE_4" else 0.7,
            "provenance": f"ClinicalTrials:{trial.nct_id}",
            "metadata": {"trial_date": trial.start_date, "phase": trial.phase}
        })
```

**Expected impact**:
- +1,000 Drug→Disease pairs (expand positive set from 44 to 1,000+)
- Temporal validation dataset (2010-2015 train, 2016-2020 test, 2021+ holdout)
- Better statistical power (more positives)

**API**: Free, REST API, bulk XML downloads

---

#### 4. DisGeNET (disgenet.org)

**Why**: Largest gene-disease association database.

**What it provides**:
- 1.1 million gene-disease associations
- Evidence scores (0-1)
- PMIDs (for most associations)
- Disease ontology mapping (UMLS, DO, ICD)

**Integration plan**:
```python
disgenet_data = disgenet.get_gene_disease_associations(min_score=0.4)

for gda in disgenet_data:
    morphisms.append({
        "source": gda.gene_symbol,
        "target": gda.disease_name,
        "name": "driver_of" if gda.score > 0.7 else "associated_with",
        "confidence": gda.score,
        "provenance": f"DisGeNET:{gda.source}",
        "metadata": {"pmids": gda.pmids}
    })
```

**Expected impact**:
- +2,000 Protein→Disease morphisms (complete more mechanistic paths)
- Improved provenance (PMIDs for protein-disease links with evidence scores)
- Higher-confidence protein-disease edges to complement PubMed co-mentions

**API**: Free for academic use, REST API, downloadable TSV

---

### Priority 3: Enrichment & ADMET (Track B Future)

#### 5. Reactome (reactome.org)

**Why**: Curated biological pathways with drug-pathway-disease links.

**What it provides**:
- 2,600+ curated pathways
- Drug → Pathway associations
- Pathway → Disease associations
- Hierarchical pathway structure

**Use case**:
- Add "Pathway" as new object type
- Drug → Pathway → Disease indirect paths
- Operadic decomposition (pathway = tree of reactions)

**Expected impact**:
- +100 Pathway objects
- +1,000 morphisms (Drug→Pathway, Pathway→Disease)
- Improved ToposLogicStrategy (more evidence for partial paths)

---

#### 6. TTD - Therapeutic Target Database (db.idrblab.net/ttd/)

**Why**: Focused on drug targets with clinical trial info.

**What it provides**:
- 3,100+ targets
- 36,000+ drugs
- Clinical trial statuses
- Target-disease relationships

**Expected impact**:
- +500 Drug→Target morphisms
- Validation dataset (TTD clinical trials vs our predictions)

---

#### 7. SIDER (sideeffects.embl.de)

**Why**: Side effects for contraindication detection.

**What it provides**:
- 140,000+ drug-side effect pairs
- Frequency data
- MedDRA ontology

**Use case**:
- Add "SideEffect" as new object type
- Drug → SideEffect morphisms
- Contraindication logic: if Drug_A → SideEffect_X and Disease_B → contraindicated_by_SideEffect_X, then Drug_A NOT for Disease_B

**Expected impact**:
- +500 SideEffect objects
- +5,000 morphisms
- Negative label generation (contraindications)

---

## Integration Workflow

### Step 1: Extend tier1_manifest.json

```json
{
  "version": "2026-06-01-expanded",
  "sources": [
    "opentargets_2026",
    "string_v12",
    "clinicaltrials_2026",
    "disgenet_v8"
  ],
  "objects": [
    ... existing 464 objects ...
    ... new objects from sources ...
  ],
  "morphisms": [
    ... existing 4,956 morphisms ...
    ... new morphisms from sources ...
  ]
}
```

### Step 2: Write Import Scripts

Create `data/drugs/importers/`:
- `import_opentargets.py`
- `import_string.py`
- `import_clinicaltrials.py`
- `import_disgenet.py`

Each script:
1. Query API or download bulk file
2. Filter (confidence thresholds, human-only, etc.)
3. Map to tier1_manifest.json format
4. Add PMIDs/provenance
5. Append to manifest

### Step 3: Rebuild tier1.db

```bash
python data/drugs/build_tier1.py --manifest data/drugs/tier1_manifest.json --output data/drugs/tier1.db
```

### Step 4: Re-run Benchmarks

```bash
python validation/repurposing_benchmark.py --view full_typed --protocol loocv --ci --baselines
```

**Acceptance criteria**:
- AUROC ≥ 0.95 (current baseline 0.956 on full graph; shouldn't drop with more data)
- AUPRC improves (current baseline 0.537; more mechanistic paths should help)
- Provenance coverage stays 100% (all new edges must have citations)

### Step 5: Update Audit

Re-run audit checks:
```bash
python audit_db_check.py
python audit_mechanistic_paths.py
python audit_pmids.py
```

---

## Expected Final State (After Priority 1+2)

**Before** (pre-PubMed expansion):
- 1,143 objects (464 core + 679 ExternalCompound)
- 1,260 morphisms
- 1,260/1,260 cited (100%)
- 44 Drug→Disease positives

**Current** (post-PubMed expansion, 2026-05-24):
- 1,146 objects (464 core + 682 ExternalCompound)
- 4,956 morphisms
- 4,956/4,956 cited (100%)
- 44 Drug→Disease positives
- AUROC 0.956 (remove_direct_labels, confidence-weighted path scoring)

**After** (with OpenTargets + STRING + ClinicalTrials + DisGeNET):
- ~10,000 objects (5,000 proteins, 100 pathways, 4,500 new drugs, 400 diseases)
- ~50,000+ morphisms
- All must have provenance (maintain 100% coverage)
- ~1,000 Drug→Disease positives

**Impact on benchmarks**:
- LOOCV: more positives → tighter CIs, higher statistical power
- External validation: larger overlap with Hetionet, DrugBank
- Temporal validation: 2010-2020 training set, 2021+ test set
- Key lesson from PubMed expansion: confidence-weighted path scoring prevents
  noise from low-quality edges degrading performance

---

## Data Quality Checklist

Before adding any source to tier1.db:

- [ ] **License check**: Can we use it? (Academic? Commercial?)
- [ ] **Provenance**: Does it have PMIDs or evidence IDs?
- [ ] **Confidence scores**: Does it provide reliability metrics?
- [ ] **Versioning**: Is it versioned? Can we reproduce builds?
- [ ] **Update frequency**: How often is it updated?
- [ ] **Species**: Human-only or filtered for human?
- [ ] **Ontology mapping**: Does it map to standard ontologies (UMLS, DO, Gene Ontology)?
- [ ] **Audit trail**: Can we trace every edge to a source?

---

## Timeline Recommendation

**Week 1-2**: OpenTargets integration
- Import drug-target data
- Add to manifest
- Rebuild + benchmark
- Expected: +30k morphisms, AUROC stable

**Week 3**: STRING integration
- Import high-confidence PPIs
- Expected: +500 morphisms, AUPRC +0.05

**Week 4**: ClinicalTrials.gov integration
- Import completed trials with results
- Temporal validation dataset
- Expected: +1000 positives, temporal AUROC 0.95+

**Week 5-6**: DisGeNET integration
- Import gene-disease associations
- Complete mechanistic paths
- Expected: +2,000 Protein→Disease edges with evidence scores

**Month 2**: Optional (Reactome, TTD, SIDER for Track B prep)

---

## Questions for Prioritization

1. **What's the timeline?** Quick (1 month) or thorough (3 months)?
2. **What's the goal?** Publication (need provenance) or internal tool (speed)?
3. **Track B timeline?** If Track B is 6+ months out, defer SIDER/Reactome.
4. **Compute budget?** Larger graph = slower queries. Need to optimize?

**My recommendation**: Start with **OpenTargets only** (week 1). If AUROC stable and provenance improves, continue with STRING → ClinicalTrials → DisGeNET.

---

**Author**: James Ray Hawkins
**Date**: 2026-05-14 (updated 2026-05-24)
**Status**: ChEMBL + PubMed complete; Open Targets ready for implementation

## Current Status

Completed expansions:
- **ChEMBL 36**: 679 ExternalCompound nodes, 881 binding assay edges, drug name normalization
- **PubMed batch**: 3,145 Protein->Disease edges, 5-layer categorical verification, confidence-weighted scoring

Current graph: 4,956 morphisms, 100% provenance, AUROC 0.956 (remove_direct_labels)

Next: Open Targets importer (estimated +5,000-30,000 edges for 20 oncology diseases)

**Implementation ready**: `import_opentargets.py` can be written following `import_chembl_sqlite.py` pattern.

**Key lesson from PubMed expansion**: New edges must be processed through the
categorical verification pipeline (`scripts/filter_pubmed_edges.py`) and assigned
confidence scores reflecting evidence quality. The confidence-weighted path bonus
`min(0.25, 0.04 * sum(path_confidence))` ensures low-quality edges contribute
proportionally less to scoring, preventing performance degradation.
