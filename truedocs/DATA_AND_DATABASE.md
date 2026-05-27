# Data and Database

**Purpose**: Database schema, statistics, reproducible build, and expansion options.

**Audience**: Researchers, developers extending the system

---

## Database Overview

**Primary database**: `data/drugs/tier1.db` (SQLite, 3.67 MB)

**Current stats** (2026-05-26):
- **Objects**: 464 (78 drugs, 20 diseases, 366 proteins)
- **Morphisms**: 5,382 (all with provenance)
- **Quantitative edges**: 204 (IC50, mutation freq, response rate, HR)
- **Unique PMIDs**: 581
- **Evidence tiers**: MEASURED 1073, ESTABLISHED 282, INFERRED 809, SPECULATIVE 955, HYPOTHESIS 159, NOISE 2104

---

## Database Schema

### Objects Table

```sql
CREATE TABLE objects (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    type_name TEXT NOT NULL,
    confidence REAL DEFAULT 1.0,
    provenance TEXT,
    embedding BLOB,
    metadata TEXT
);

CREATE INDEX idx_object_name ON objects(name);
CREATE INDEX idx_object_type ON objects(type_name);
```

**Columns**:
- `id`: Unique identifier (auto-incremented)
- `name`: String identifier (e.g., "Sorafenib", "BRAF", "Melanoma")
- `type_name`: Object type ("Drug", "Protein", "Disease")
- `confidence`: Prior confidence [0, 1]
- `provenance`: PMID, ChEMBL ID, or source reference
- `embedding`: Optional vector representation (NULL for now)
- `metadata`: JSON-serialized additional data

---

### Morphisms Table

```sql
CREATE TABLE morphisms (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    source_id INTEGER NOT NULL,
    target_id INTEGER NOT NULL,
    confidence REAL NOT NULL,
    provenance TEXT,
    evidence_tier TEXT,
    metadata TEXT,
    FOREIGN KEY(source_id) REFERENCES objects(id),
    FOREIGN KEY(target_id) REFERENCES objects(id)
);

CREATE INDEX idx_morphism_source ON morphisms(source_id);
CREATE INDEX idx_morphism_target ON morphisms(target_id);
CREATE INDEX idx_morphism_name ON morphisms(name);
```

**Columns**:
- `name`: Relation type ("inhibits", "mutated_in", "treats", etc.)
- `source_id`: Source object ID
- `target_id`: Target object ID
- `confidence`: Confidence [0, 1]
- `provenance`: PMID or ChEMBL ID
- `evidence_tier`: MEASURED, ESTABLISHED, INFERRED, SPECULATIVE, HYPOTHESIS, NOISE
- `metadata`: JSON (IC50 value, units, etc.)

---

### 2-Cells Table (Experimental)

```sql
CREATE TABLE two_cells (
    id INTEGER PRIMARY KEY,
    morphism1_id INTEGER,
    morphism2_id INTEGER,
    equivalence_score REAL,
    FOREIGN KEY(morphism1_id) REFERENCES morphisms(id),
    FOREIGN KEY(morphism2_id) REFERENCES morphisms(id)
);
```

Used for Yoneda equivalence discovery (morphisms between morphisms).

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

### Proteins (366 total)

**Types**:
1. **Drug targets**: Kinases, GPCRs, proteases (~100)
2. **Regulators**: Pathways, transcription factors (~150)
3. **Disease-associated**: Mutation drivers, biomarkers (~116)

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
| `treats` | 44 | Sorafenib treats Melanoma (FDA label) |
| `promotes` | ~60 | Angiogenesis promotes tumor growth |
| `drives` | ~40 | KRAS mutation drives NSCLC |
| ...and 15 more | ~4,623 | Various biological relationships |

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
11. Validate (100% provenance check)
12. Output: `data/drugs/tier1.db`

**Reproducibility**: Same manifest → same database (SHA256 hash).

---

## Data Import Process

### ChEMBL (872 morphisms)

```python
from data.drugs.importers.chembl_importer import import_chembl

# Import all drug-target interactions
import_chembl(store, chembl_db='data/external/chembl_33.db')

# Adds:
# - Drug nodes (if new)
# - Protein nodes (if new)
# - Inhibits/binds morphisms with ChEMBL ID provenance
# - IC50/Ki/Kd metadata
```

### FDA Labels (44 morphisms)

```python
from data.drugs.importers.fda_importer import import_fda_labels

# Import FDA-approved oncology indications
import_fda_labels(store, fda_file='data/drugs/fda_oncology_approvals.csv')

# Adds:
# - Treats morphisms (Drug → Disease)
# - PMID provenance
# - Approval date metadata
```

### STRING PPI (338 morphisms)

```python
from data.drugs.importers.string_importer import import_string

# Import protein-protein interactions
import_string(store, string_file='data/external/9606.protein.links.v11.5.txt')

# Adds:
# - Protein nodes
# - Activates/regulates/binds morphisms
# - Confidence score from STRING (combined_score)
```

### cBioPortal Genomics (45+ morphisms)

```python
from data.drugs.importers.cbioportal_importer import import_genomics

# Import mutation frequencies
import_genomics(store, mutations_file='data/external/cbioportal_mutations.csv')

# Adds:
# - Mutated_in morphisms (Protein → Disease)
# - Mutation frequency metadata
# - PMID provenance
```

### ABPP IC50 (65 morphisms)

```python
from data.drugs.importers.abpp_importer import import_abpp

# Import experimental IC50 data
import_abpp(store, abpp_file='data/external/abpp_ic50.tsv')

# Adds/updates:
# - IC50 metadata on inhibits morphisms
# - PMID provenance
```

### NLP PMID Extraction (373 quantitative points)

```python
from nlp.pmid_extractor import extract_quantitative_values

# Extract IC50, mutation freq, response rate from abstracts
values = extract_quantitative_values(pmid_list=list_of_pmids)

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
| **Morphisms with provenance** | 5382/5382 (100%) | 100% |
| **Morphisms with confidence** | 5382/5382 (100%) | 100% |
| **Quantitative edges** | 204/5382 (3.8%) | Target 5%+ |
| **FDA labels recovered** | 44/44 (100%) | 100% |

### Provenance

- **PMIDs**: 581 unique, all linked to morphisms
- **ChEMBL IDs**: All 78 drugs + targets mapped
- **Validation**: 92.2% accuracy on NLP extractions (vs. abstracts)

---

## Database Access Examples

### Query all drugs

```python
from data.store import KomposOSStore

store = KomposOSStore('data/drugs/tier1.db')
drugs = store.list_objects(type_name='Drug', limit=None)
print([d.name for d in drugs])
```

### Query all morphisms for a drug

```python
drug = store.get_object('Sorafenib')
morphisms = store.list_morphisms(source_id=drug.id, limit=None)
targets = [m.target.name for m in morphisms if m.name == 'inhibits']
print(f"Targets of Sorafenib: {targets}")
```

### Query quantitative data

```python
morphisms = store.list_morphisms(limit=None)
quantitative = [m for m in morphisms if 'ic50_nm' in (m.metadata or {})]
print(f"Morphisms with IC50: {len(quantitative)}")

for m in quantitative[:5]:
    ic50 = m.metadata.get('ic50_nm')
    print(f"{m.source.name} → {m.target.name}: IC50 = {ic50} nM")
```

---

## Version History

| Date | Version | Changes |
|------|---------|---------|
| 2026-05-26 | 2.0 | Yoneda integration, evidence quantification (373 extractions) |
| 2026-05-24 | 1.9 | Path bonus tuning, LOOCV calibration |
| 2026-05-13 | 1.8 | Binding evidence strategy, ABPP integration |
| 2026-05-10 | 1.7 | ChEMBL SQLite expansion (+269 proteins, +872 edges) |
| 2026-05-06 | 1.6 | External audit completion, 100% provenance |
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

*Last updated: 2026-05-26*
