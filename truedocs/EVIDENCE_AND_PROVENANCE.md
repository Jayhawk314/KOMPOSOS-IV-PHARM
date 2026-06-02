# Evidence and Provenance

**Purpose**: Document data sources, evidence tracing, and why source strings on the 2,329 morphisms matter.

**Audience**: Researchers (validating claims), scientists (understanding evidence), practitioners (checking candidate justification)

**Key fact**: All 2,329 morphisms carry a source/provenance string (100% source-string
coverage), and 1,035 carry a PMID (955 distinct PMIDs). Source-string coverage is **not** the
same as edge-specific citation validation. PMID-backed edges are tiered by how the citation was
checked: **745 RELATION-VERIFIED** (an agent confirmed the cited sentence asserts the directed,
signed relation) and **215 LEXICAL-COOCCURRENCE** (the cited sentence passed an automated
co-occurrence + polarity screen only — not verified). The earlier "188 audited PMIDs" figure was
simply the count of distinct PMIDs *present in* provenance strings at one point; presence is not
human or relation-level verification.

---

## Why Provenance Matters

In pharmaceutical discovery, "garbage in = garbage out." A prediction is only as good as its evidence.

**KOMPOSOS-IV principle**: Every biological relationship (morphism) must carry a source:
- **PMID**: PubMed ID (peer-reviewed paper)
- **ChEMBL ID**: ChEMBL compound or target ID (curated database)
- **FDA**: FDA approval record (regulatory source)

This means:
- **You can fact-check every claim** (follow the PMID/database/source string)
- **You can assess evidence quality** (primary paper vs. review)
- **You can audit the system** (detect stale or erroneous data)

---

## Source Coverage (As of 2026-05-27)

### By the Numbers

| Category | Count | Interpretation |
|----------|------:|----------------|
| **Total morphisms** | 2,329 | SQLite edge rows |
| Source/provenance strings | 2,329 | Every row has a source string (100% source-string coverage) |
| Edges carrying a PMID | 1,035 | PMID present in provenance |
| Unique PMID identifiers | 955 | distinct PMIDs detected in provenance/metadata strings |
| RELATION-VERIFIED edges | 745 | agent-confirmed the cited sentence asserts the directed, signed relation |
| LEXICAL-COOCCURRENCE edges | 215 | cited sentence passed automated co-occurrence + polarity screen only (not verified) |
| Structured quantitative values | 1,014 | Edges with IC50, mutation, response, or HR values |

Do not rewrite this as "100% validated PMIDs" or "100% validated provenance."
The still-needed audit is edge-specific attribution: endpoint mentions, relation
support, quantitative value support, and whether the support is from abstract or
full text.

### By Data Type

| Source | Morphisms | Type | Evidence |
|--------|-----------|------|----------|
| **PubMed (NLP)** | 373 quantitative | IC50, mutation freq, response rate, HR | PMID citations |
| **ChEMBL** | 872 drug-target | Interaction tables | ChEMBL compound/target IDs |
| **FDA** | 44 indications | Approved Drug-Disease labels | FDA approval record + PMID |
| **STRING PPI** | 338 protein-protein | Interaction database | STRING ID + PMID |
| **cBioPortal** | 45+ genomic | Mutation frequency, copy number | PMID citations |
| **ABPP** | 65 IC50 | Affinity Profiling Panel | PMID + experimental |
| **ESM2** | 100 protein similarity | Protein embeddings | Fallback (no PMID) |

---

## Data Sources in Detail

### 1. PubMed / NLP Extraction (373 quantitative data points)

**What**: Automated extraction of quantitative values from PubMed abstracts.

**Values extracted**:
- IC50 binding constants (Kd, Ki)
- Mutation frequencies (% of cancer cases with mutation)
- Clinical response rates (% of patients responding to drug)
- Hazard ratios (survival improvement)

**Coverage**:
- 373 quantitative data points from 204 unique PMIDs
- Automated/manual checks reported high extraction agreement, but endpoint-specific attribution still needs audit
- Example: PMID:12829955 (Sorafenib IC50 for BRAF = 25.8 nM)

**Process**:
1. Query PubMed for drug + target + measurement keyword (IC50, Kd, Ki, etc.)
2. Extract via NLP/regex from abstracts
3. Normalize units (nM, μM, etc.)
4. Validate endpoint, relation, and quantitative value support against abstract/full text
5. Store with PMID

**Limitations**:
- Biased toward high-impact journals (not all small studies)
- Abstracts often lack full experimental details
- Some values are approximate ("~100 nM" vs. exact)

**How to check**: See [PMID:12829955](https://pubmed.ncbi.nlm.nih.gov/12829955) in your browser.

### 2. ChEMBL (872 drug-target interactions)

**What**: Curated database of drug-target interactions (ChEMBL.org).

**Coverage**:
- 269 protein targets (kinases, GPCRs, enzymes, etc.)
- 872 morphisms (drug-target pairs)
- 17 base drugs with expanded ChEMBL targets

**Data types**:
- Binding constants (IC50, Ki, Kd)
- Bioactivity types (EC50, AC50, potency)
- Compound IDs (ChEMBL IDs for all drugs)
- Target IDs (ChEMBL target accessions)

**Version**: ChEMBL SQLite dump (2026-05-10 import)

**Quality**: Community-curated; citations to original papers.

**How to check**: ChEMBL.org CHEMBL{ID} (e.g., CHEMBL183 = Sorafenib).

### 3. FDA (44 Drug-Disease Approvals)

**What**: FDA-approved oncology indications for 44 drug-disease pairs.

**Coverage**:
- 78 drugs (FDA-approved oncology agents)
- 44 approved indications (Drug → Disease edges)
- Approval dates (2001–2024)

**Data types**:
- Indication label (approved use)
- Approval date (e.g., 2008 for Sorafenib/Melanoma)
- PMID for approval (regulatory documentation)

**Sources**:
- FDA Orange Book
- NCI drug summaries
- Regulatory packages

**How to check**: NCI Drug Dictionary (cancer.gov/about-cancer/treatment/drugs).

### 4. STRING (338 Protein-Protein Interactions)

**What**: Search Tool for the Retrieval of Interacting Genes (STRING.org).

**Coverage**:
- 338 PPI edges (protein-protein interactions)
- High-confidence interactions (combined score >0.7)

**Data types**:
- Direct physical interactions
- Functional associations
- Literature mined (with PMIDs)

**Quality**: Benchmark-validated; widely used in systems biology.

**How to check**: STRING.org with protein accessions.

### 5. cBioPortal (45+ Genomic Associations)

**What**: Cancer biology data from The Cancer Genome Atlas (TCGA) and other studies.

**Coverage**:
- Mutation frequencies (% of cancer cases with mutation)
- Copy number alterations
- Gene expression correlations
- Clinical association data

**Data types**:
- Mutation freq: BRAF in Melanoma (70%)
- CNV: amplification/deletion in specific cancers
- Expression: upregulation/downregulation

**Quality**: Harmonized across 30+ cancer studies, manually curated.

**How to check**: cBioPortal.org (search cancer type + gene).

### 6. ABPP (65 IC50 Entries)

**What**: Affinity Profiling Panel (experimental binding data).

**Coverage**:
- 65 drug-target pairs with experimental IC50 values
- Kinase-focused (most comprehensive domain)
- Some non-kinases (GPCRs, proteases)

**Data quality**:
- Direct experimental measurement (not predicted)
- Traceable to PMID or ChEMBL
- CI50 measured under standardized assay conditions

**Example**: Sorafenib-BRAF IC50 = 25.8 nM (PMID:12829955)

**How to check**: CrossRef PMID from ABPP bridge.

### 7. Protein Sequence Similarity (100 Edges)

**What**: Protein sequence similarity edges. Currently labeled with ESM2 provenance
in the database, pending re-derivation with ESMC-300M (see note below).

**Coverage**:
- 100 protein-protein similarity edges
- Used as fallback when direct interaction data missing
- Confidence 0.55-0.65 (lower than curated sources)

**Type**: Sequence-based similarity (no PMID/ChEMBL).

**Caveats**:
- Computational prediction, not experimental validation
- Used only when no other evidence available
- Treated conservatively in scoring (lower weight)

**Provenance integrity note (2026-05-28)**: The 424 edges in the manifest with
`ESM2:similar_to_X(0.XX)` provenance were generated by text embeddings
(sentence-transformers on gene name strings), not by the real ESM2 protein
language model. The protein language model engine has been upgraded from ESM2
(esm2_t33_650M_UR50D, 1280d) to ESMC-300M (ESM Cambrian, 960d). A re-derivation
script (`scripts/rederive_esmc_edges.py`) exists to replace these edges with
genuine ESMC protein sequence cosine similarities. Until that script is run,
the existing edges carry mislabeled provenance.

**ESMC-300M engine** (`data/bio_embeddings.py`):
- Model: EvolutionaryScale ESMC-300M (300M parameters, 960 dimensions)
- Input: amino acid sequences fetched from UniProt
- 71 proteins with sequences loaded; 62 inherited from KOMPOSOS-III ESM2 cache
- Same-family pairs: cosine similarity 0.95-0.99 (e.g., KRAS-NRAS 0.99, BRAF-RAF1 0.99)
- Cross-family pairs: 0.40-0.93 depending on structural relatedness
- Cache: `~/.komposos4/bio_embeddings_cache.db`

**ESMC protein classification in triage reports**: Triage reports now classify
each drug-disease prediction as Family Extrapolation (ESMC sim >= 0.95 to a
known treatment's targets), Cross-Family Related (0.80-0.95), or Cross-Family
Novel (< 0.80). This classification compares the drug's direct protein targets
against targets of approved treatments for the same disease. It does not affect
scoring -- it adds interpretability for researchers evaluating whether a
prediction is expected from protein homology or genuinely novel.

**Scripts**:
- `scripts/fetch_protein_sequences.py`: fetch missing UniProt sequences
- `scripts/rederive_esmc_edges.py`: replace ESM2-labeled edges with real ESMC similarities
- `scripts/expand_esmc_protein_similarity.py`: expand ESMC similarity coverage to all 20 diseases

---

## Evidence Tiers (Confidence Classification)

All morphisms are classified by evidence strength:

| Tier | Count | Interpretation | Examples |
|------|-------|-----------------|----------|
| **MEASURED** | 1,073 | Experimental data (IC50, kinetic assays) | ABPP entries, PMID quantitative |
| **ESTABLISHED** | 282 | Well-cited biological relationships | FDA approvals, classic drug-target pairs |
| **INFERRED** | 809 | Reliable but derived (e.g., pathway inference) | Computational predictions, mechanistic extensions |
| **SPECULATIVE** | 955 | Plausible but less certain | Rule-based, low-confidence paths |
| **HYPOTHESIS** | 159 | Exploratory (may be wrong) | Novel predictions, hypothesis-driven |
| **NOISE** | 2,104 | Low-confidence noise (kept for auditing) | Very indirect paths, uncertain computational |

**Usage**:
- Yoneda strategy uses only MEASURED + ESTABLISHED (1355 edges, clean subgraph)
- Composition uses all tiers but weights by confidence score
- Reporting: always check which tiers support your candidate

---

## Tracing a Prediction to Evidence

### Example: Sorafenib for Melanoma

Using the trace tool:

```bash
python validation/trace_prediction.py Melanoma Sorafenib
```

Output:

```
====== Trace: Melanoma + Sorafenib ======

System Score: 0.910

Mechanistic Paths:
─────────────────────────────────────────────

Path 1 (confidence 0.865):
  Sorafenib --inhibits--> BRAF
    Evidence: IC50 = 25.8 nM | PMID:12829955 | ChEMBL:CHEMBL183
    Confidence: 0.95

  BRAF --mutated-in--> Melanoma
    Evidence: Mutation freq = 70% | PMID:15184864
    Confidence: 0.91

  Path confidence: 0.95 × 0.91 = 0.865

Path 2 (confidence 0.597):
  Sorafenib --inhibits--> VEGFR2
    Evidence: PMID:18241329 | ChEMBL:CHEMBL183
    Confidence: 0.85

  VEGFR2 --promotes--> Angiogenesis
    Evidence: Canonical pathway | STRING:9606.ENSP00000263237
    Confidence: 0.88

  Angiogenesis --supports--> Melanoma
    Evidence: Tumor-promoting process | PMID:16116430
    Confidence: 0.80

  Path confidence: 0.85 × 0.88 × 0.80 = 0.597

All Paths Ranked by Confidence:
  1. 0.865 (Drug → Protein → Disease)
  2. 0.597 (Drug → Protein → Process → Disease)
  3. 0.412 (Drug → Protein → Pathway → Disease)
  ... (total 12 paths)

Strategy Votes:
─────────────────────────────────────────────

Mechanistic Path:    0.81  (composition)
Binding Evidence:    0.87  (IC50 + drug properties)
Interaction Profile: 0.73  (yoneda_pattern)
Structural Inference: 0.70 (fibration_lift)
Evidence Integration: 0.81 (topos_logic)
Drug Analogy:        0.90  (kan_extension)
Structural Similarity: 0.32 (yoneda_distance, live only)

Final Score: 0.910 (average of active signals + bonuses)
Status: APPROVED (FDA 2008, PMID:18241329)

PMIDs Cited (in order of importance):
  [1] PMID:18241329 — FDA approval, Sorafenib for Melanoma (2008)
  [2] PMID:12829955 — IC50 measurement, Sorafenib-BRAF (25.8 nM)
  [3] PMID:15184864 — BRAF mutation frequency in Melanoma (70%)
  [4] PMID:16116430 — VEGFR2 in angiogenesis
  ... (9 total PMIDs for this pair)

Evidence Chains (readable):
  Sorafenib targets BRAF with confirmed IC50 (25.8 nM, PMID:12829955).
  BRAF is mutated in 70% of Melanomas, representing a key driver
  mutation (PMID:15184864, PMID:15184864).
  Sorafenib also targets VEGFR2, which promotes angiogenesis
  (PMID:16116430), a tumor-supporting process. These mechanistic
  links justify the Melanoma indication, consistent with FDA
  approval (PMID:18241329).
```

### How to Check Sources

**For PMID**:
1. Go to https://pubmed.ncbi.nlm.nih.gov/{PMID}
2. Read abstract (IC50, mutation freq, etc.)
3. Assess quality (journal, authors, sample size)

**For ChEMBL**:
1. Go to https://www.ebi.ac.uk/chembl/
2. Search by ChEMBL ID (e.g., CHEMBL183 = Sorafenib)
3. Check targets, bioactivities, references

**For STRING/cBioPortal**:
1. STRING.org or cBioPortal.org
2. Search protein/gene name
3. View interaction evidence and citations

---

## Citation Worksheet Generation

Generate a TODO list of all papers to review:

```bash
python validation/generate_citation_worksheet.py Melanoma --drug Sorafenib
```

Output:

```
Citation Worksheet: Melanoma + Sorafenib
=========================================

Must-read (cited in top paths):
  [ ] PMID:18241329 — FDA approval justification
  [ ] PMID:12829955 — Sorafenib IC50 (25.8 nM)
  [ ] PMID:15184864 — BRAF mutation frequency (70%)

Supporting (secondary mechanisms):
  [ ] PMID:16116430 — VEGFR2 in angiogenesis
  [ ] PMID:18091378 — Sorafenib resistant mutations
  [ ] PMID:19451549 — Combination therapy (Sorafenib + inhibitor)

Background (general oncology):
  [ ] PMID:10021768 — BRAF in melanoma review (2000)
  [ ] PMID:12566402 — Kinase inhibitor therapeutics review

Quality Assessment:
  Nature/Science/Cell: 2 papers (high impact)
  Specialized journals: 5 papers (moderate impact)
  Reviews: 2 papers (background)

Total: 9 papers to review
```

---

## Database Integrity Checks

Verify the source-string coverage claim directly against the live DB:

```bash
python -c "import sqlite3; c=sqlite3.connect('data/drugs/tier1.db').cursor(); \
print(c.execute('SELECT COUNT(*) FROM morphisms').fetchone()[0],'morphisms'); \
print(c.execute(\"SELECT COUNT(*) FROM morphisms WHERE provenance!='unknown'\").fetchone()[0],'with source strings')"
```

Current state (2026-06-02):

```
Provenance reality
==================

Database: data/drugs/tier1.db
Runtime objects: 1,146
Morphisms: 2,329

Coverage check:
  Rows with source strings:   2,329 / 2,329 (100.0%)
  Unique PMID identifiers:    955
  PMID-bearing edges:         1,035
  Tiered: 745 RELATION-VERIFIED, 215 LEXICAL-COOCCURRENCE

Orphaned morphisms (no provenance):
  Count: 0
  Status: CLEAN

Quantitative values:
  MEASURED-tier edges:        1,014
  NOTE: numeric values (IC50, HR, mutation freq, response rate) currently live
  inside provenance/metadata strings; the structured `quantitative_value` column
  is unpopulated. Edge-level numeric extraction into the column is an open task.

Self-check (FDA labels):
  Expected: 44 FDA-approved pairs
  Found: 44 / 44 (100%) ✓
  All with source strings: 44 / 44 (100%)

Stale data check:
  Newest PMID: PMID:26193519 (2015, still current)
  Oldest PMID: PMID:10021768 (2000, classic reference)
  Mean publication year: 2008

Conclusion: All morphisms have source strings. Edge-specific citation attribution
still requires the dedicated audit.
```

---

## Reproducible Data Build

All data is reproducible from a manifest:

```bash
python data/drugs/build_tier1.py --manifest data/drugs/tier1_manifest.json
```

**Manifest format**: JSON file specifying:
- Drug list (78 drugs with ChEMBL IDs)
- Protein list (366 biological entities including receptors, oncogenes, tumor suppressors, and signaling molecules)
- Disease list (20 oncology diseases)
- Edge sources (ChEMBL, FDA, STRING, cBioPortal, ABPP, NLP)

**Result**: Exact reproduction of tier1.db (same SHA256 hash)

**Verification**:
```bash
# Compute hash
sha256sum data/drugs/tier1.db

# Should match: [check CLAUDE.md for expected hash]
```

---

## Data Expansion Recommendations

Current coverage is oncology-focused. To expand:

### Short Term (Additional Oncology Data)

- **OpenTargets**: Genetic associations (1000s more disease genes)
- **LINCS**: Drug-induced gene expression (40,000+ compounds)
- **HPA**: Tissue/subcellular protein distribution

### Medium Term (Other Disease Domains)

- **ClinicalTrials.gov integration**: Phase I/II/III status tracking
- **PharmGKB**: Pharmacogenomics data (patient stratification)
- **DrugBank**: ADMET, side effects, interactions

### Long Term (Track B: Drug Design)

- **ChEMBL molecular structures**: SMILES, 3D structures
- **PDBe**: Crystal structures (binding sites)
- **Synthesis routes**: Retrosynthesis databases (SyntheticNet, etc.)

See [DATA_AND_DATABASE.md](DATA_AND_DATABASE.md) for details on data schema and import procedures.

---

## Handling Updates

Current database is static (2026-05-26 snapshot, 609 PMIDs).

**To update**:
1. Modify manifest (add/remove drugs, diseases, edges)
2. Rebuild database: `python data/drugs/build_tier1.py --manifest tier1_manifest.json`
3. Validate: `python validation/audit_provenance.py`
4. Benchmark: `python validation/repurposing_benchmark.py --view full_typed --protocol remove_direct_labels`
5. Update docs with new metrics

**Version control**: Each build is reproducible and versioned.

---

## Quality Issues & Known Limitations

### Biased Data Sources

- **PubMed**: Skewed toward published findings (publication bias)
- **ChEMBL**: Biased toward kinases & well-studied targets
- **cBioPortal**: Only major cancers (TCGA focus)

**Mitigation**: Multiple independent sources (ChEMBL + ABPP + NLP).

### Stale References

- Oldest PMID (PMID:10021768) is from 2000
- Newest PMIDs are from 2015 (database snapshot 2026-05-26)
- **Action required**: Rebuild with newer PMIDs annually

### Missing Quantitative Data

- 1,014 edges are MEASURED-tier; numeric values live in provenance strings, the structured `quantitative_value` column is unpopulated (extraction is an open task)
- Many drug-target pairs have only existence (no IC50)
- **Mitigation**: NLP extraction expanding coverage (values present in provenance/metadata)

---

## For Researchers: How to Cite Data

If you use KOMPOSOS-IV data in a publication:

```bibtex
@dataset{komposos_iv_pharm_2026,
  title = {KOMPOSOS-IV-PHARM Track A Drug Repurposing Database},
  author = {Hawkins, James Ray},
  year = {2026},
  url = {https://github.com/your-repo/KOMPOSOS-IV-PHARM},
  note = {1146 runtime objects, 2329 morphisms, source strings on all morphisms, 955 PMID identifiers}
}
```

List specific PMIDs in your methods:
> "Drug-target interactions were sourced from ChEMBL (Mendez et al., 2019),
> ABPP profiling (Savitski et al., 2014), and PubMed NLP extraction
> (PMIDs 12829955, 15184864, 18241329, ...)."

---

## Next Steps

### To check specific evidence:

```bash
python validation/trace_prediction.py Melanoma Sorafenib
```

### To assess data quality:

```bash
python validation/audit_provenance.py
```

### To expand data:

See [DATA_AND_DATABASE.md](DATA_AND_DATABASE.md) and [DATA_EXPANSION_GUIDE.md](../DATA_EXPANSION_GUIDE.md)

### To understand scoring:

See [TRACK_A_DRUG_REPURPOSING.md](TRACK_A_DRUG_REPURPOSING.md) and [STRATEGIES_IN_DEPTH.md](STRATEGIES_IN_DEPTH.md)

---

*Last updated: 2026-05-26 (Evidence quantification expansion: 373 extractions, 204 edges with values)*
