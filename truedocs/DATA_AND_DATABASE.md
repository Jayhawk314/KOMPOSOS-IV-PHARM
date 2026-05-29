# Data and Database

**Purpose**: Database schema, statistics, reproducible build, and expansion options.

**Audience**: Researchers, developers extending the system

---

## Database Overview

**Primary database**: `data/drugs/tier1.db` (SQLite, 3.67 MB)

**Current stats** (2026-05-28 audit):
- **Objects**: 1,146 total (including referenced types)
- **Morphisms**: 2,178 (100% source-string coverage; ≠ citation validation)
- **FDA Labels**: 48 approved Drug->Disease pairs
- **Quantitative edges**: 1,014 (IC50, mutation freq, response rate, HR)
- **PMID-backed edges**: 884 carry a PMID (805 distinct); 594 RELATION-VERIFIED (agent-confirmed directed/signed), 215 LEXICAL-COOCCURRENCE (automated co-occurrence + polarity screen only)
- **Evidence tiers**: MEASURED 1014, ESTABLISHED 377, INFERRED 767, HYPOTHESIS 20
- **Strategic Transparency**: Yoneda Distance uses only MEASURED+ESTABLISHED (1,391 edges).

Audit note: 100% source-string coverage (2,178/2,178 edges) achieved after restoring 302 'unknown' source strings. Source-string coverage is not the same as edge-level citation validation.

---

## Database Schema

### Objects Table

```sql
CREATE TABLE objects (
    name TEXT PRIMARY KEY,
    type_name TEXT NOT NULL,
    metadata TEXT NOT NULL,
    embedding BLOB,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    provenance TEXT NOT NULL
);

CREATE INDEX idx_object_name ON objects(name);
CREATE INDEX idx_object_type ON objects(type_name);
```

**Columns**:
- `name`: Primary string identifier (e.g., "Sorafenib", "BRAF", "Melanoma")
- `type_name`: Object type ("Drug", "Protein", "Disease")
- `metadata`: JSON-serialized additional data
- `embedding`: Optional vector representation (NULL for now)
- `created_at`, `updated_at`: Row timestamps
- `provenance`: PMID, ChEMBL ID, or source reference

---

### Morphisms Table

```sql
CREATE TABLE morphisms (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    source_name TEXT NOT NULL,
    target_name TEXT NOT NULL,
    metadata TEXT NOT NULL,
    confidence REAL NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    provenance TEXT NOT NULL,
    evidence_tier TEXT,
    quantitative_value REAL,
    value_unit TEXT,
    sample_size INTEGER,
    confidence_lower REAL,
    confidence_upper REAL
);

CREATE INDEX idx_morphism_source ON morphisms(source_name);
CREATE INDEX idx_morphism_target ON morphisms(target_name);
CREATE INDEX idx_morphism_name ON morphisms(name);
```

**Columns**:
- `id`: Deterministic string ID (`name:source->target`)
- `name`: Relation type ("inhibits", "mutated_in", "treats", etc.)
- `source_name`: Source object name
- `target_name`: Target object name
- `metadata`: JSON (IC50 value, units, etc.)
- `confidence`: Confidence [0, 1]
- `created_at`, `updated_at`: Row timestamps
- `provenance`: PMID or ChEMBL ID
- `evidence_tier`: MEASURED, ESTABLISHED, INFERRED, SPECULATIVE, HYPOTHESIS, NOISE
- `quantitative_value`, `value_unit`, `sample_size`, `confidence_lower`, `confidence_upper`: optional normalized quantitative fields

---

### Paths and Higher-Categorical Tables

```sql
CREATE TABLE paths (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    morphism_ids TEXT NOT NULL,
    source_name TEXT NOT NULL,
    target_name TEXT NOT NULL,
    length INTEGER NOT NULL,
    metadata TEXT NOT NULL,
    confidence REAL NOT NULL,
    created_at TIMESTAMP NOT NULL,
    provenance TEXT NOT NULL
);

CREATE TABLE higher_morphisms (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    source_morphism_id TEXT NOT NULL,
    target_morphism_id TEXT NOT NULL,
    metadata TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL
);

CREATE TABLE equivalence_classes (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    object_names TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL
);
```

These tables support path caching and higher-categorical experiments. In the
current `tier1.db` snapshot they are present but empty.

---

## Object Types

### Drugs (78 total)

**Sample**: Sorafenib, Vemurafenib, Imatinib, Alectinib, Crizotinib, ...

**Properties**:
- `name`: Drug name (e.g., "Sorafenib")
- `smiles`: SMILES string (optional)
- `molecular_weight`: Float (da)
- `logp`: Float (lipophilicity)
- `hbd`: Integer (hydrogen bond donors)
- `hba`: Integer (hydrogen bond acceptors)

**Sourced from**: ChEMBL, FDA, PubChem

---

### Diseases (20 total)

**Sample**: Melanoma, Renal Cell Carcinoma, Non-Small-Cell Lung Cancer, Hepatocellular Carcinoma, Ovarian Cancer, ...

**Properties**:
- `name`: Disease name
- `icd10`: ICD-10 code (optional)
- `oncology_type`: Tumor type classification

**Sourced from**: FDA, NCI, WHO

---

### Proteins and Typed Biological Objects

**Types**:
1. **Protein rows**: 269 objects with `type_name = "Protein"`
2. **Typed protein/pathway classes**: signaling, receptor, transcription, apoptosis, tumor suppressor, oncogene, regulator, and related classes
3. **Disease-associated entities**: mutation drivers, biomarkers, pathways, and drug targets

**Properties**:
- `name`: Protein name or gene symbol
- `uniprot_id`: UniProt accession (optional)
- `ensembl_id`: Ensembl ID (optional)
- `pfam_domain`: Pfam domain (for kinases, GPCRs, etc.)

**Sourced from**: ChEMBL, STRING, cBioPortal, UniProt

---

## Morphism Types

| Type | Count | Example |
|------|-------|---------|
| `inhibits` | ~200 | Sorafenib inhibits BRAF |
| `mutated_in` | ~45 | BRAF mutated in Melanoma |
| `regulates` | ~120 | TP53 regulates apoptosis |
| `upregulates` | ~80 | TGFβ upregulates EMT |
| `activates` | ~90 | BRAF activates MEK |
| `treats` | 48 | Sorafenib treats Melanoma (FDA label) |
| `promotes` | ~60 | Angiogenesis promotes tumor growth |
| `drives` | ~40 | KRAS mutation drives NSCLC |
| ...and 15 more | ~1,543 | Various biological relationships |

---

## Reproducible Build

### Manifest File

`data/drugs/tier1_manifest.json` specifies:

```json
{
  "version": "2.0",
  "build_date": "2026-05-26",
  "objects": {
    "drugs": [
      {"name": "Sorafenib", "chembl_id": "CHEMBL183", "cas": "475207-59-1"},
      ...
    ],
    "diseases": [
      {"name": "Melanoma", "icd10": "C80.0"},
      ...
    ],
    "proteins": [
      {"name": "BRAF", "uniprot_id": "P15056"},
      ...
    ]
  },
  "sources": {
    "chembl": "version 33",
    "fda": "approved_oncology_drugs.txt",
    "string": "9606.protein.links.v11.5.txt",
    "cbioportal": "mutation_frequencies.csv",
    "abpp": "ic50_entries.tsv",
    "nlp": "pmid_extractions.csv"
  }
}
```

### Build Script

```bash
python data/drugs/build_tier1.py --manifest data/drugs/tier1_manifest.json
```

**Process**:
1. Load manifest
2. Create empty SQLite database
3. Add all objects (drugs, diseases, proteins)
4. Import edges from ChEMBL (manifest specifies version)
5. Import FDA labels
6. Import STRING PPI edges
7. Import cBioPortal genomic data
8. Import ABPP IC50 entries
9. Import NLP-extracted quantitative values
10. Compute evidence tiers
11. Validate (source strings on all 2,178 morphisms check)
12. Output: `data/drugs/tier1.db`

**Reproducibility**: Same manifest → same database (SHA256 hash).

---

## Data Import Process

### ChEMBL

```python
from data.drugs.importers.import_chembl import import_chembl

# Import all drug-target interactions
import_chembl(store, chembl_db='data/external/chembl_33.db')

# Adds:
# - Drug nodes (if new)
# - Protein nodes (if new)
# - Inhibits/binds morphisms with ChEMBL ID provenance
# - IC50/Ki/Kd metadata
```

### FDA Labels (48 morphisms)

```python
# FDA labels are loaded by the tier1 build from curated manifest/source files.

# Adds:
# - Treats morphisms (Drug → Disease)
# - PMID provenance
# - Approval date metadata
```

### STRING PPI

```python
from data.drugs.importers.import_string import import_string

# Import protein-protein interactions
import_string(store, string_file='data/external/9606.protein.links.v11.5.txt')

# Adds:
# - Protein nodes
# - Activates/regulates/binds morphisms
# - Confidence score from STRING (combined_score)
```

### cBioPortal Genomics (45+ morphisms)

```python
# cBioPortal-derived mutation-frequency edges are loaded by the tier1 build
# from curated manifest/source files.

# Adds:
# - Mutated_in morphisms (Protein → Disease)
# - Mutation frequency metadata
# - PMID provenance
```

### ABPP IC50 (65 morphisms)

```python
# ABPP IC50 values are consumed by the binding evidence strategy and tier1 build.

# Adds/updates:
# - IC50 metadata on inhibits morphisms
# - PMID provenance
```

### NLP PMID Extraction (373 quantitative points)

```python
# Quantitative extractions are represented in morphism metadata and normalized
# quantitative columns where available.

# Adds metadata to morphisms:
# - IC50 values (nM, μM units normalized)
# - Mutation frequencies (%)
# - Clinical response rates (%)
# - Hazard ratios (survival)
```

---

## Data Expansion Recommendations

### High-Priority (Known Quality)

1. **OpenTargets** (200+ new targets)
   - Genetic associations (GWAS, rare variants)
   - Expression quantitative trait loci (eQTL)
   - Import: `scripts/import_opentargets.py`

2. **LINCS** (40,000+ compounds)
   - Drug-induced transcriptomic changes
   - Cell-line specific responses
   - Selective import for 78 drugs + 20 diseases

3. **HPA** (Tissue/subcellular localization)
   - Protein localization context
   - Drug target accessibility
   - Import: `scripts/import_hpa.py`

### Medium-Priority

4. **ClinicalTrials.gov** (Phase I/II/III status)
   - Validate predictions against trials
   - Track moving from candidate → approved

5. **PharmGKB** (Pharmacogenomics)
   - Patient stratification biomarkers
   - Gene-drug interactions

### Long-Term (Track B: Drug Design)

6. **PDBe** (Protein structures)
   - Crystal structures for binding site analysis
   - Docking validations

7. **ChEMBL Structures** (SMILES, 3D)
   - Molecular fingerprints
   - Similarity calculations

8. **Synthesis Routes** (SyntheticNet, RetroPath)
   - Synthetic feasibility scoring
   - Manufacturing constraints

---

## Data Quality Metrics

### Completeness

| Metric | Value | Target |
|--------|-------|--------|
| **Objects with type_name** | 464/464 (100%) | 100% |
| **Morphisms with provenance** | 2178/2178 (100%) | 100% |
| **Morphisms with confidence** | 2178/2178 (100%) | 100% |
| **Quantitative edges** | 1014/2178 (46.5%) | Target 50%+ |
| **FDA labels recovered** | 48/48 (100%) | 100% |

### Provenance

PMID-backed edges: 884 carry a PMID (805 distinct). Tiered by how checked: 594 RELATION-VERIFIED
(agent-confirmed the cited sentence asserts the directed, signed relation), 215 LEXICAL-COOCCURRENCE
(automated co-occurrence + polarity screen only — not verified). Source-string coverage is not citation validation.
- **ChEMBL IDs**: All 78 drugs + targets mapped
- **Strategic Transparency**: Yoneda Distance restricted to MEASURED+ESTABLISHED evidence.

---

## Database Access Examples

### Query all drugs

```python
from data.store import KomposOSStore

store = KomposOSStore('data/drugs/tier1.db')
drugs = store.get_objects_by_type('Drug')
print([d.name for d in drugs])
```

### Query all morphisms for a drug

```python
morphisms = store.get_morphisms_from('Sorafenib')
targets = [m.target_name for m in morphisms if m.name == 'inhibits']
print(f"Targets of Sorafenib: {targets}")
```

### Query quantitative data

```python
morphisms = store.list_morphisms(limit=None)
quantitative = [m for m in morphisms if 'ic50_nm' in (m.metadata or {})]
print(f"Morphisms with IC50: {len(quantitative)}")

for m in quantitative[:5]:
    ic50 = m.metadata.get('ic50_nm')
    print(f"{m.source_name} → {m.target_name}: IC50 = {ic50} nM")
```

---

## Version History

| Date | Version | Changes |
|------|---------|---------|
| 2026-05-29 | 2.3 | Full 737-proof adjudication (in-session, no API): 594 RELATION-VERIFIED, 215 LEXICAL-COOCCURRENCE. Precision treats 100% / inhibits 93% / associated_with 75% / activates 61%. Scoring unchanged (AUROC 0.948640) |
| 2026-05-28 | 2.2 | Honest provenance tiering begun (initial 78 RELATION-VERIFIED); corrected "188 audited PMIDs" overclaim (805 distinct PMIDs present, presence ≠ verification) |
| 2026-05-28 | 2.1 | 100% source-string coverage (2,178/2,178), 48 FDA labels |
| 2026-05-26 | 2.0 | Yoneda integration, evidence quantification (373 extractions) |
| 2026-05-24 | 1.9 | Path bonus tuning, LOOCV calibration |
| 2026-05-13 | 1.8 | Binding evidence strategy, ABPP integration |
| 2026-05-10 | 1.7 | ChEMBL SQLite expansion (+269 proteins, +872 edges) |
| 2026-05-06 | 1.6 | External audit completion, source strings on all 5,382 morphisms |
| 2026-05-01 | 1.5 | Quantitative evidence expansion |
| 2026-04-15 | 1.4 | FDA label curation (44 pairs) |
| 2026-04-01 | 1.3 | Initial tier1.db build |

---

## Next Steps

### To rebuild the database:

```bash
python data/drugs/build_tier1.py --manifest data/drugs/tier1_manifest.json
```

### To expand with new data:

1. Update manifest
2. Run import script (or modify `build_tier1.py`)
3. Validate: `python validation/audit_provenance.py`
4. Benchmark: `python validation/repurposing_benchmark.py --view full_typed --protocol remove_direct_labels`

### See Also

- [EVIDENCE_AND_PROVENANCE.md](EVIDENCE_AND_PROVENANCE.md) — Data sources & traceability
- [DATA_EXPANSION_GUIDE.md](../DATA_EXPANSION_GUIDE.md) — Detailed expansion instructions

---

*Last updated: 2026-05-28*
