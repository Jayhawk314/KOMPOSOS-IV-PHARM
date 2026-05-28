> **Legacy/historical notice (2026-05-27):** This file is retained for background or session history. It is not the current source of truth for Track A metrics or provenance. Current docs are in `truedocs/`, especially `truedocs/VALIDATION_AND_BENCHMARKS.md` and `truedocs/REPRODUCIBILITY_PROTOCOL.md`. Current strict run: AUROC 0.974694 [0.9606, 0.9855], AUPRC 0.551698 [0.4067, 0.6983], Hits@5/10/20 1.0000/0.6000/0.6000; LOOCV AUROC 0.975916 and AUPRC 0.553703; Hetionet external AUROC 0.634479 and AUPRC 0.009255. Source strings exist on all 5,382 morphisms with 610 PMID identifiers; this is not 100% edge-specific citation validation. Retired or superseded claims in this file should be read as historical.
# External Audit Guide for KOMPOSOS-IV-PHARM

**Version**: 2026-05-11 audit-fixed (post-ChEMBL, no OpenTargets deployment)
**Scope**: Track A drug repurposing system
**Intended audience**: Independent third-party auditors with bioinformatics,
pharmacology, or biostatistics expertise

---

## Purpose

This guide enables an external auditor to independently verify the scientific
accuracy, statistical validity, and bioinformatics correctness of KOMPOSOS-IV-PHARM's
drug repurposing claims. The system is a research prototype, not a clinical tool.

The core audit questions are:

1. **Are the biological relationships in the knowledge graph correct?**
2. **Is the AUROC computed without methodological errors?**
3. **Do the claims match what the data and code actually produce?**
4. **Are the limitations honestly disclosed?**

---

## Part 1: Environment Setup

### 1.1 Requirements

- Python 3.10+
- Git clone of this repository
- No external API keys or accounts required
- All data is local (SQLite database)

### 1.2 Install Dependencies

```powershell
pip install -r requirements.txt   # if present
pip install numpy                 # minimum dependency
```

### 1.3 Verify Database Exists

```powershell
python -c "from pathlib import Path; print(Path('data/drugs/tier1.db').stat().st_size, 'bytes')"
```

The database is currently ~640 KB. If missing, rebuild from manifest:

```powershell
python data/drugs/build_tier1.py
```

---

## Part 2: Reproduce All Claimed Metrics

Run all four canonical benchmarks. These are the **only** commands needed to
reproduce every claimed AUROC:

```powershell
python validation/repurposing_benchmark.py --view legacy --protocol as_loaded --ci --baselines
python validation/repurposing_benchmark.py --view full_typed --protocol as_loaded --ci --baselines
python validation/repurposing_benchmark.py --view full_typed --protocol remove_direct_labels --ci --baselines
python validation/repurposing_benchmark.py --view full_typed --protocol loocv --ci --baselines
```

Also run all regression tests:

```powershell
pytest tests/test_repurposing_benchmark.py -q
pytest tests -q
```

### 2.1 Expected Current Values (2026-05-11 Audit-Fixed, Post-ChEMBL Expansion)

These are the audit-fixed values after correcting the manifest/DB endpoint
integrity issue and the LOOCV baseline label-order bug. Your reproduced values
should match to 3 decimal places.

**Database state**: 1143 objects, 1260 morphisms, 78 evaluation drugs, 20 diseases, 366 protein-like nodes, 679 ChEMBL supporting compounds
**Provenance**: 958/1260 morphisms cited (76.0%) -- 86 PMIDs, 872 ChEMBL/DOI
**DB SHA256**: `F8C1042687B911286B7165A8C41B25165C58284C366C51895CE0AFA61A59142A`
**Semantic DB SHA256**: `6AB835134DEC65E141F7B88E6B6DC856E9FDA2DCC3BD74A6903A73F5E77B5C00`

Verify with:

```powershell
python -c "import hashlib; print(hashlib.sha256(open('data/drugs/tier1.db','rb').read()).hexdigest().upper())"
```

| View | Protocol | AUROC | 95% CI | AUPRC | Hits@5 | Pairs | Positives |
|------|----------|------:|--------|------:|-------:|------:|----------:|
| legacy | as_loaded | 0.917 | [0.826, 0.990] | 0.536 | 0.60 | 1320 | 36 |
| full_typed | as_loaded | 0.890 | [0.852, 0.928] | 0.154 | 0.00 | 1560 | 44 |
| full_typed | remove_direct_labels | 0.974 | [0.961, 0.985] | 0.500 | 0.60 | 1560 | 44 |
| full_typed | loocv | 0.974 | [0.965, 0.983] | 0.516 | 1.00 | 1560 | 44 |

**Note**: as_loaded shows Hits@5 = 0.00 (artifact: composition skips existing edges).
The scientifically valid protocols are loocv and remove_direct_labels.

### 2.2 Corrected Baseline AUROC Values

The 2026-05-11 audit found and fixed a LOOCV baseline label-order bug. The old
LOOCV baseline table (`random ~0.468`, `degree_product ~0.474`,
`common_neighbor ~0.508`, `shortest_path ~0.559`, `path_count ~0.566`) was
invalid because baseline scores were generated in nested `drug x disease`
order but compared against positive-first LOOCV labels.

Corrected LOOCV baselines are:

| Baseline | Expected AUROC | Margin vs. Lower Bound |
|----------|---------------:|-----------------------:|
| random | 0.562 | +0.403 |
| degree_product | 0.701 | +0.264 |
| common_neighbor | 0.895 | +0.070 |
| shortest_path | 0.931 | +0.034 |
| path_count | 0.826 | +0.139 |

The system still exceeds the corrected graph baselines, but the margin over the
strongest baseline is modest (~0.043 AUROC against shortest path), not >0.40.
For `remove_direct_labels`, corrected baselines are: random 0.562,
degree_product 0.680, common_neighbor 0.939, shortest_path 0.931, path_count
0.899.

### 2.3 What to Record

For each run, record: exact AUROC, CI bounds, AUPRC, Hits@5, MRR, pair count,
positive count, morphism count. Compare to claimed values.

---

## Part 3: Audit the AUROC Methodology

This section addresses whether the AUROC is computed correctly and whether
common evaluation pitfalls apply. References:

- [Validation approaches for computational drug repurposing (PMC10785886)](https://pmc.ncbi.nlm.nih.gov/articles/PMC10785886/)
- [Knowledge Graphs for drug repurposing: a review (PMC11426166)](https://pmc.ncbi.nlm.nih.gov/articles/PMC11426166/)
- [Strategies for robust benchmarking of drug discovery platforms (Bioinformatics 2025)](https://academic.oup.com/bioinformatics/article/41/11/btaf604/8315141)
- [Project Rephetio: Systematic integration of biomedical knowledge (eLife 2017)](https://elifesciences.org/articles/26726)

### 3.1 AUROC Computation Method

**Check**: Is AUROC computed via the Wilcoxon-Mann-Whitney (pairwise concordance)
method or via sklearn/trapezoidal integration?

**Location**: `validation/repurposing_benchmark.py`, function `pairwise_auroc()`

The system uses pairwise concordance: for every (positive, negative) pair, count
whether the positive scores higher (concordant), lower (discordant), or equal
(tied). AUROC = (concordant + 0.5 * tied) / total.

**Verify**: This is mathematically equivalent to the trapezoidal AUROC and is
the standard approach (see Hanley & McNeil, 1982).

### 3.2 Data Leakage Checks

Data leakage is the most common source of inflated AUROC in drug repurposing
benchmarks. Check these specific leakage vectors:

#### 3.2.1 Direct Edge Leakage

**Question**: When scoring Drug->Disease pair X, can any strategy directly look
up the stored Drug->Disease label for X?

**How to check**: Read `oracle/strategies.py` and `oracle/topos_strategy.py`.
For each of the 7 strategies, trace whether it queries `category.get_morphisms()`
for direct Drug->Disease edges.

- `CompositionStrategy`: Looks for 2-hop paths Drug->Protein->Disease. Check
  lines ~615-617 — it skips if a direct edge exists.
- `ToposLogicStrategy`: Check `_check_pathway_support()` — should route
  Drug->Disease pairs to pathway-only prediction.
- Profile strategies (KanExtension, YonedaPattern): These use analogical
  reasoning. They may be influenced by OTHER Drug->Disease labels (cross-label
  contamination), but should not use the specific edge being tested.

#### 3.2.2 Cross-Label Contamination

**Question**: When scoring pair (DrugA, DiseaseB) under LOOCV, are other
Drug->Disease labels still present in the graph?

**How to check**: Read `evaluate_loocv()` in `repurposing_benchmark.py`. It
calls `load_full_typed_view(db_path, skip_pair=held_pair)` which removes only
the single held-out edge. Other Drug->Disease labels remain. This is standard
LOOCV behavior but means profile strategies can use cross-label information.

**Assessment**: This is a known limitation, properly disclosed. The
`remove_direct_labels` protocol removes ALL Drug->Disease labels and achieves
AUROC 0.974 [0.961, 0.985] (same as LOOCV), confirming that scoring is not
dependent on label leakage.

#### 3.2.3 Temporal Leakage

**Question**: Could the knowledge graph contain information that was not
available at the time a drug was approved?

**How to check**: The graph is constructed from curated sources. Some
Drug->Protein->Disease pathways may encode post-approval knowledge. This is a
form of retrospective bias common to all knowledge graph approaches (see
Himmelstein et al., eLife 2017). A temporal holdout validation (pre/post 2013)
has been reported at AUROC 0.959 on 22 post-2013 approvals, but auditors should
treat that as a reported result until the exact runnable script and frozen
temporal graph artifact are available in the repo.

### 3.3 Negative Label Construction

**Critical issue**: In drug repurposing, unlabeled Drug->Disease pairs are NOT
confirmed negatives. They are open-world unknowns — the drug may treat the
disease but no trial has been conducted.

**How to check**: Read `drug_disease_pairs()` in `repurposing_benchmark.py`.
All Drug x Disease combinations not in the positive set are treated as negatives
for AUROC computation.

**Assessment**: This inflates apparent specificity. It is standard practice in
the field (see Rephetio: 755 positives vs 29,044 "non-treatments"), but means
AUROC measures ranking ability, not clinical true/false efficacy. Verify this
caveat is disclosed in documentation.

### 3.4 Bootstrap Confidence Intervals

**Location**: `bootstrap_ci()` in `repurposing_benchmark.py`

**Verify**:
- Resamples (score, label) pairs with replacement
- Skips degenerate resamples (all-positive or all-negative)
- Uses fixed seed (42) for reproducibility
- Reports 2.5th and 97.5th percentiles (95% CI)
- Uses 1000 resamples

### 3.5 Baseline Validity

**Location**: `compute_baselines()` in `repurposing_benchmark.py`

**Verify**:
- Each baseline uses only graph structure, never strategy scores
- Labels are identical to those used for the main AUROC
- Baseline score order is aligned to the same explicit `(drug, disease)` pair
  order as the labels. This is covered by
  `test_baselines_are_aligned_to_explicit_pair_order`.
- Random baseline uses fixed seed (42)
- Shortest-path and path-count use BFS up to depth 3
- Baselines are computed on the same graph view as the main AUROC

### 3.6 Score Combination Formula

**Location**: `score_pair()` in `repurposing_benchmark.py`

Current formula:

```python
base = sum(confidence for _, confidence in votes) / len(votes)
path_bonus = min(0.25, 0.10 * composition_count)
return min(1.0, base + path_bonus)
```

**Verify**:
- Simple mean of strategy confidences (uniform weights confirmed optimal by
  LOOCV calibration in `calibrate_loocv.py`)
- Path bonus is additive, capped at 0.25
- Bonus comes from composition path count (Drug->Protein->Disease chains)
- Parameters were tuned via LOOCV grid search (`tune_path_bonus.py`)
- Tuning was done on the same LOOCV protocol — this means the path bonus
  parameters are optimized on the evaluation set. An auditor should note this
  as a potential source of optimistic bias, though the 9-configuration grid
  is small and the improvement is mechanistically interpretable.

---

## Part 4: Audit Bioinformatics and Medical Accuracy

This is the most domain-specific part of the audit. It requires pharmacology
or bioinformatics expertise.

### 4.1 Positive Label Verification

The system claims 44 Drug->Disease pairs as "FDA-approved indications." Each
must be a real, current FDA-approved use.

**How to audit**:

1. Extract the 44 positive labels:

```powershell
python -c "
import sys; sys.path.insert(0, '.')
from validation.repurposing_benchmark import load_full_typed_view, drug_disease_pairs
cat, _ = load_full_typed_view('data/drugs/tier1.db')
_, _, positives = drug_disease_pairs(cat)
for drug, disease in sorted(positives):
    print(f'{drug} -> {disease}')
"
```

2. For each pair, verify against:
   - [FDA Drugs@FDA](https://www.accessdata.fda.gov/scripts/cder/daf/)
   - [DailyMed](https://dailymed.nlm.nih.gov/)
   - [DrugBank](https://go.drugbank.com/)

3. Check for:
   - **False positives**: Drugs labeled as treating a disease they are NOT
     approved for (would inflate AUROC)
   - **Missing indications**: Known approvals not in the positive set (would
     deflate AUROC by counting them as negatives)
   - **Indication specificity**: "NSCLC" vs "non-small cell lung cancer" —
     is the disease category appropriately specific?
   - **Withdrawn approvals**: Drugs whose indication was later withdrawn

### 4.2 Drug-Target Relationship Verification

The knowledge graph contains Drug->Protein edges (e.g., "Imatinib inhibits
BCR_ABL"). These must be biologically correct.

**How to audit**:

1. Extract drug-target edges:

```powershell
python -c "
import sys, sqlite3; sys.path.insert(0, '.')
conn = sqlite3.connect('data/drugs/tier1.db')
cursor = conn.execute('''
    SELECT m.source, m.target, m.name, m.provenance
    FROM morphisms m
    JOIN objects s ON m.source = s.name
    JOIN objects t ON m.target = t.name
    WHERE s.type_name = 'Drug'
    AND t.type_name NOT IN ('Disease')
    ORDER BY m.source
''')
for row in cursor:
    print(f'{row[0]} --{row[2]}--> {row[1]}  [{row[3] or \"no provenance\"}]')
"
```

2. For each drug-target edge, verify:
   - **Is this a known pharmacological target?** Check ChEMBL, DrugBank, or
     UniProt for the drug's mechanism of action.
   - **Is the edge type correct?** "inhibits" vs "activates" vs "modulates" —
     does the actual mechanism match?
   - **Is the target gene symbol correct?** Map to UniProt/HGNC and verify.

3. Spot-check at least 10 drug-target edges against ChEMBL or primary literature.

### 4.3 Protein-Disease Relationship Verification

The graph contains Protein->Disease edges (e.g., "BRAF driver_of Melanoma").
These represent established gene-disease associations.

**How to audit**:

1. Extract protein-disease edges:

```powershell
python -c "
import sys, sqlite3; sys.path.insert(0, '.')
conn = sqlite3.connect('data/drugs/tier1.db')
cursor = conn.execute('''
    SELECT m.source, m.target, m.name, m.provenance
    FROM morphisms m
    JOIN objects s ON m.source = s.name
    JOIN objects t ON m.target = t.name
    WHERE t.type_name = 'Disease'
    AND s.type_name NOT IN ('Drug')
    ORDER BY m.target, m.source
''')
for row in cursor:
    print(f'{row[0]} --{row[2]}--> {row[1]}  [{row[3] or \"no provenance\"}]')
"
```

2. For each protein-disease edge, verify against:
   - [COSMIC Cancer Gene Census](https://cancer.sanger.ac.uk/census)
   - [DisGeNET](https://www.disgenet.org/)
   - [OMIM](https://www.omim.org/)
   - Primary literature (PMIDs where provided)

3. Check:
   - **Is this gene actually implicated in this disease?** Not all kinases are
     oncogenic in all cancers.
   - **Is the relationship type correct?** "driver_of" vs "associated_with" vs
     "biomarker_of" have different strengths.
   - **Is the edge biologically plausible?** A gene expressed only in liver
     tissue should not be a "driver_of" brain cancer without evidence.

### 4.4 Provenance Verification

The system claims 958/1260 morphisms have provenance (76.0%):
- 86 PMIDs (primary literature)
- 872 ChEMBL/DOI (database evidence)
- 302 morphisms remain uncited ("unknown" provenance)

**How to audit**:

1. Extract all PMID-cited morphisms:

```powershell
python -c "
import sys, sqlite3; sys.path.insert(0, '.')
conn = sqlite3.connect('data/drugs/tier1.db')
cursor = conn.execute('''
    SELECT source_name, target_name, name, provenance
    FROM morphisms WHERE provenance LIKE 'PMID:%'
    ORDER BY provenance
''')
for row in cursor:
    print(f'{row[0]} -> {row[1]} ({row[2]}) [{row[3]}]')
print(f'Total: {cursor.rowcount}')
"
```

2. Spot-check at least 10 PMIDs:
   - Look up each PMID on [PubMed](https://pubmed.ncbi.nlm.nih.gov/)
   - Verify the paper actually supports the claimed relationship
   - Check for retracted papers
   - Verify the paper is not about a different organism (mouse vs human)

3. For uncited morphisms (302/1260), assess:
   - Are they well-known pharmacological relationships that don't need citation?
   - Or are they controversial claims that require evidence?
   - Priority audit targets: Drug->Protein and Protein->Disease edges without provenance

### 4.5 Mechanistic Path Verification

The system claims all 44 positives have mechanistic Drug->Protein->Disease paths.

**How to audit**:

```powershell
pytest tests/test_repurposing_benchmark.py::test_all_positives_have_mechanistic_paths -v
```

Then verify a sample of paths manually:
- Does Imatinib actually work through BCR_ABL to treat CML?
- Does Vemurafenib actually work through BRAF to treat Melanoma?
- Does Pembrolizumab actually work through PD1/PDL1 to treat NSCLC?

### 4.6 Disease Ontology Consistency

**Check**:
- Are disease names consistent? (e.g., "NSCLC" used everywhere, not mixed with
  "Non_Small_Cell_Lung_Cancer")
- Are diseases at the right granularity? "Cancer" is too broad; "EGFR-mutant
  stage IIIB adenocarcinoma" is too specific for this graph.
- Do all 20 diseases represent distinct clinical entities?

---

## Part 5: Additional Validation Checks

### 5.1 External Validation

An external validation was conducted against Hetionet-confirmed drug-disease
treatments not in our positive set.

**Reproduce**:
- See validation scripts or `CURRENT_STATE.md` for external validation results.
- Reported external AUROC: 0.744 on 7 Hetionet-confirmed pairs.

**Assess**: 7 pairs is small. This provides directional evidence only. As of
the 2026-05-11 audit pass, this result is not considered fully reproduced
unless the auditor can run the exact validation script and confirm the same
held-out pair list.

### 5.2 Temporal Holdout Validation

The system removed all post-2013 FDA approvals (22 pairs) and scored them using
only pre-2013 graph data.

**Reported result**: Temporal AUROC 0.959 on 22 post-2013 approvals.

**Assess**: This would be a strong validation signal if reproduced. Verify the
2013 cutoff date is correctly applied and that no post-2013 edges remain in the
training graph. Do not treat the temporal claim as audit-verified without the
frozen script/artifact pair.

### 5.3 Disease-Level Holdout

All positives for each disease (with >=2 positives) were held out and scored.

**Reported results**: Mean disease-level AUROC 0.877 across 7 diseases.

**Assess**: Range 0.615-0.996 shows variable performance. Colorectal Cancer
(0.615) is notably weak. Check whether this correlates with graph coverage
for that disease. This should also be reproduced from executable artifacts
before being used as an external audit claim.

### 5.4 Candidate Triage Report

The system includes a triage CLI for inspecting individual predictions:

```powershell
python validation/triage.py Melanoma
python validation/triage.py --drug Sorafenib
python validation/triage.py Melanoma --drug Vemurafenib
```

**Verify**: Reports include strategy vote breakdown, evidence chains, PMIDs,
and APPROVED/NOT_APPROVED labels. Check that APPROVED labels match the positive set
and that NOT_APPROVED predictions are biologically plausible. Note: NOT_APPROVED
means not in our 44 FDA oncology indications; candidates may already be in clinical
trials or published literature.

### 5.5 OpenTargets Expansion Experiment (2026-05-11)

An automated, cancer-filtered import from OpenTargets Platform was tested to
wire in 313 latent proteins (proteins with Drug edges but no Disease edges).

**Method**: Queried all 366 proteins via OpenTargets GraphQL API. Filtered to
cancer therapeutic area (MONDO_0045024). Mapped to existing 20 diseases. Applied
uniform score thresholds.

**Script**: `data/drugs/importers/import_opentargets_diseases.py`

**Reported results at three thresholds**:

| Threshold | New Edges | AUROC | 95% CI | Change |
|-----------|-----------|------:|--------|-------:|
| None (original) | 0 | 0.974 | [0.965, 0.983] | -- |
| >= 0.7 | 26 | 0.968 | [0.955, 0.979] | -0.006 |
| >= 0.6 | 121 | 0.961 | [0.947, 0.976] | -0.013 |
| >= 0.5 | 212 | 0.952 | [0.934, 0.969] | -0.022 |

**Conclusion**: More OpenTargets edges = lower AUROC at every threshold.
OpenTargets gene-disease associations (genetic, GWAS, phenotype-level) add
noise to druggable mechanistic path prediction. The curated graph has a higher
signal-to-noise ratio. The expansion was **not deployed**.

**What this means for auditors**: The system was tested against automated data
expansion and the curated graph reportedly outperformed. Treat this as a
documented experiment unless the generated OpenTargets manifests and benchmark
logs for each threshold are reproduced locally. The current DB and manifest
contain zero OpenTargets provenance edges.

**Backup manifest**: `data/drugs/tier1_manifest_pre_opentargets.json` is a
pre-experiment backup. It is no longer byte-identical to the canonical
audit-fixed manifest because the canonical manifest now includes explicit
`ExternalCompound` endpoint rows and corrected count fields.

---

## Part 6: Red Flags Checklist

An auditor should flag any of the following:

### Statistical Red Flags

- [ ] AUROC reported without specifying graph view and protocol
- [ ] AUROC reported without confidence intervals
- [ ] AUROC reported without baseline comparison
- [ ] Baseline scores compared against labels in a different pair order
- [ ] Claims of "no leakage" without naming the strategy set and label-removal policy
- [ ] Treating unlabeled pairs as confirmed negatives (not just ranking negatives)
- [ ] Path bonus parameters optimized on evaluation data without disclosure
- [ ] CI computed incorrectly (not resampling score-label pairs)

### Bioinformatics Red Flags

- [ ] Drug-target relationships that contradict ChEMBL/DrugBank
- [ ] PMIDs that don't support the claimed relationship
- [ ] Retracted papers cited as evidence
- [ ] Gene symbols that don't map to valid HGNC identifiers
- [ ] Protein-disease links not supported by COSMIC, DisGeNET, or OMIM
- [ ] FDA indications that are incorrect or withdrawn
- [ ] Missing well-known indications (Imatinib->GIST, etc.)

### System Red Flags

- [ ] Claiming Track B drug design validation from Track A AUROC
- [ ] Claiming clinical readiness from retrospective ranking metrics
- [ ] Using fallback/mock scientific modules without disclosure
- [ ] Quoting the as_loaded AUROC as the primary metric (it includes direct labels)
- [ ] Comparing to baselines without showing the baseline is computed on the
      same graph and labels

---

## Part 7: Comparison to Published Benchmarks

For context, here are AUROC values from published drug repurposing systems:

| System | AUROC | Positives | Graph Size | Validation |
|--------|------:|----------:|-----------:|------------|
| Rephetio (Himmelstein 2017) | 0.97 | 755 | 47k nodes, 2.25M edges | 10-fold CV |
| KOMPOSOS-IV-PHARM (this) | 0.974 | 44 | 1143 objects, 1260 morphisms | LOOCV |
| Drug Repurposing KG (typical) | 0.85-0.95 | 100-1000 | varies | varies |

**Key differences to note**:
- Our graph is much smaller (1143 objects vs 47k nodes)
- Our positive set is much smaller (44 vs 755)
- LOOCV is more rigorous than k-fold CV for small datasets
- Direct comparison is not valid without matching graph, labels, and protocol

---

## Part 8: Verdict Template

Complete this template after your audit:

```text
EXTERNAL AUDIT VERDICT
======================
Auditor:
Date:
Auditor expertise:

METRIC REPRODUCTION
  Claimed LOOCV AUROC:          0.974
  Reproduced LOOCV AUROC:       ___
  Match (within 0.001):         YES / NO
  95% CI reproduced:            ___
  Baselines reproduced:         YES / NO

AUROC METHODOLOGY
  Pairwise computation correct:             YES / NO
  Direct edge leakage found:                YES / NO
  Cross-label contamination disclosed:      YES / NO
  Negative set construction described:      YES / NO
  Bootstrap CI implementation valid:        YES / NO
  Path bonus tuning on eval data disclosed: YES / NO

BIOINFORMATICS ACCURACY
  FDA indications verified (sample of N):   ___ / ___  correct
  Drug-target edges verified (sample of N): ___ / ___  correct
  Protein-disease edges verified (N):       ___ / ___  correct
  PMIDs spot-checked (sample of N):         ___ / ___  support claimed relationship
  Retracted papers found:                   ___ / ___
  Gene symbols valid (HGNC check):          ___ / ___  valid

DATA INTEGRITY
  Object count matches:                     YES / NO
  Morphism count matches:                   YES / NO
  All positives have mechanistic paths:     YES / NO
  Provenance coverage:                      ___ / ___ morphisms cited

ADDITIONAL VALIDATION
  External validation present:              YES / NO
  Temporal holdout present:                 YES / NO
  Disease-level holdout present:            YES / NO
  Clinical disclaimers present:             YES / NO

RED FLAGS FOUND
  (list any)

OVERALL ASSESSMENT
  Metric accuracy:       VERIFIED / NOT VERIFIED
  Bioinformatics accuracy: HIGH / MEDIUM / LOW / NOT ASSESSED
  Statistical rigor:     HIGH / MEDIUM / LOW
  Generalization confidence: HIGH / MEDIUM / LOW
  Clinical readiness:    NOT READY (research prototype only)

RECOMMENDATIONS
  (list any required remediation)
```

---

## Part 9: Files Reference

| File | Purpose |
|------|---------|
| `CLAUDE.md` | Project instructions, current metrics, scientific rules |
| `CURRENT_STATE.md` | Current system state and validation results |
| `MEMORY.md` | Development history and roadmap |
| `validation/repurposing_benchmark.py` | Benchmark harness (scoring, AUROC, baselines, CI) |
| `validation/repurposing_benchmark_manifest.json` | Frozen benchmark state |
| `validation/triage.py` | Candidate triage CLI |
| `validation/trace_prediction.py` | Prediction tracing with evidence chains |
| `oracle/strategies.py` | 7 oracle strategies |
| `oracle/topos_strategy.py` | ToposLogic pathway scoring |
| `data/drugs/tier1.db` | SQLite knowledge graph |
| `data/drugs/build_tier1.py` | Reproducible DB build from manifest |
| `data/drugs/tier1_manifest.json` | Source manifest for DB build |
| `calibrate_loocv.py` | LOOCV strategy weight calibration |
| `tune_path_bonus.py` | Path bonus parameter grid search |
| `tests/test_repurposing_benchmark.py` | Regression tests |
| `data/drugs/importers/import_opentargets_diseases.py` | OpenTargets cancer-filtered import (tested, not deployed) |
| `data/drugs/tier1_manifest_pre_opentargets.json` | Backup manifest before OpenTargets experiment |
| `opentargets_test_results.json` | OpenTargets coverage test results |
| `CHEAP_DRUG_REPURPOSING_CANDIDATES.md` | Cheap generic repurposing candidates report |
| `generate_cheap_drug_report.py` | Script to generate cheap drug report |
| `IMPLEMENTATION_PLAN_2026-05-10.md` | Implementation plan and roadmap |

---

## References

1. Hanley JA, McNeil BJ. The meaning and use of the area under a receiver
   operating characteristic (ROC) curve. *Radiology*. 1982;143(1):29-36.
2. Himmelstein DS, et al. Systematic integration of biomedical knowledge
   prioritizes drugs for repurposing. *eLife*. 2017;6:e26726.
   https://elifesciences.org/articles/26726
3. Tanoli Z, et al. Validation approaches for computational drug repurposing:
   a review. *Brief Bioinform*. 2024;25(1). PMC10785886.
   https://pmc.ncbi.nlm.nih.gov/articles/PMC10785886/
4. Lobentanzer S, et al. Knowledge Graphs for drug repurposing: a review of
   databases and methods. *Brief Bioinform*. 2024;25(6):bbae461. PMC11426166.
   https://pmc.ncbi.nlm.nih.gov/articles/PMC11426166/
5. Bittner DM, et al. Strategies for robust, accurate, and generalizable
   benchmarking of drug discovery platforms. *Bioinformatics*. 2025;41(11):btaf604.
   https://academic.oup.com/bioinformatics/article/41/11/btaf604/8315141
6. Kim M, et al. Benchmarking heterogeneous network-based methods for drug
   repurposing. *npj Syst Biol Appl*. 2025.
   https://www.nature.com/articles/s41540-025-00633-8
