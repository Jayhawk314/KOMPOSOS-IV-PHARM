# Candidate Reports: Cheap Generic Drug Repurposing

**Purpose**: Disease-by-disease breakdown of cheap, FDA-approved generic drugs ranked for oncology repurposing by the KOMPOSOS-IV-PHARM categorical inference system.

**Audience**: Researchers evaluating repurposing hypotheses, clinicians screening candidates for further investigation

**Prerequisites**: [TRACK_A_DRUG_REPURPOSING.md](TRACK_A_DRUG_REPURPOSING.md), [VALIDATION_AND_BENCHMARKS.md](VALIDATION_AND_BENCHMARKS.md)

---

## Executive Summary

This report identifies cheap, FDA-approved generic drugs with mechanistic pathway evidence for cancer repurposing. Every candidate is traceable to Drug->Protein->Disease evidence chains with primary literature citations.

**Key facts**:
- **37 cheap generics** screened across **20 cancer types**
- **70 drug-disease entries** with mechanistic pathway support
- Rankings based on 9 categorical inference strategies (composition, binding evidence, Yoneda distance, path bonus, coherence, conjecture, natural transform, game theory, bayesian)
- Every prediction backed by source-linked evidence chains (PMIDs, ChEMBL IDs, FDA/KEGG/STRING/computational provenance as applicable)
- System validation: AUROC 0.9747 [95% CI: 0.9606-0.9855] (remove_direct_labels, 44 FDA positives)
- ClinicalTrials.gov cross-check: 63% of top predictions already in human trials

**Important**: NOT_APPROVED means the drug-disease pair is not in our 44 FDA-approved oncology indications. It does **not** mean the combination is unstudied. Many candidates are already in clinical trials or published literature.

**This is a hypothesis generation tool, not a clinical recommendation.**

---

## How to Read This Report

Each candidate entry includes:

| Field | Meaning |
|-------|---------|
| **Rank** | Position among all 78 drugs for that disease |
| **Score** | Combined score from 9 strategies (0.0-1.0) |
| **Status** | APPROVED (in our 44 FDA labels) or NOT_APPROVED |
| **Mechanistic paths** | Count of Drug->Protein->Disease chains found |
| **Path details** | Specific protein intermediates with confidence scores |
| **PMIDs** | Literature citations for individual edges |
| **Quantitative evidence** | IC50, mutation freq, HR, response rates where available |

Scores above 0.80 indicate strong mechanistic support. Scores 0.70-0.80 indicate moderate support. Multiple mechanistic paths increase confidence.

---

## Why Cheap Generics Rank Lower Than Targeted Therapies

With the current 9-strategy system (including binding evidence and Yoneda distance), FDA-approved kinase inhibitors with strong experimental backing rank highest. Cheap generics typically appear in ranks 2-50 rather than top 10, reflecting calibration toward evidence-backed predictions.

**Targeted therapies** (Osimertinib, Sunitinib, Imatinib) benefit from:
- Extensive ABPP IC50 data (65 experimental entries)
- Crystal structures and Pfam domain mappings
- Published clinical trials with genomic correlation data
- FDA labels with explicit target mechanisms
- High Yoneda similarity to other approved drugs in same class

**Cheap generics** (Mebendazole, Niclosamide, Aspirin) typically have:
- Limited experimental binding data
- Broader, less specific target profiles
- Older literature with less quantitative evidence
- Off-label historical use rather than targeted mechanism

This ranking pattern is **correct behavior** -- the system properly weights experimental evidence. The cheap generics that still rank well despite this handicap (Mebendazole in 15 cancers, Niclosamide in 13) deserve attention precisely because they overcome the evidence gap through strong pathway connectivity.

---

## Multi-Disease Candidates

Cheap generics with mechanistic pathway support across multiple cancers. These are the most interesting candidates because cross-disease signal is harder to achieve by chance.

### Mebendazole (15 cancer types)

The strongest cheap drug candidate overall. An antihelmintic with unexpectedly broad oncology pathway connections through VEGFR2, BRAF, and TP53.

| Disease | Rank | Score | Paths | Key pathway |
|---------|-----:|------:|------:|-------------|
| GIST | 2 | 0.837 | 3 | VEGFR2, BRAF, TP53 |
| RCC | 3 | 0.847 | 2 | VEGFR2 |
| HCC | 7 | 0.827 | 1 | VEGFR2 |
| Melanoma | 7 | 0.816 | 2 | BRAF->MEK1 |
| Soft Tissue Sarcoma | 11 | 0.825 | 2 | TP53, VEGFR2 |
| Colorectal Cancer | 13 | 0.824 | 3 | VEGFR2, TP53, BRAF |
| Breast Cancer | 21 | 0.783 | 1 | TP53 |
| Li-Fraumeni Syndrome | 21 | 0.779 | 2 | TP53->MDM2 |
| NSCLC | 23 | 0.777 | 1 | VEGFR2 |
| CML | 24 | 0.733 | 1 | BCR-ABL pathway |
| Glioblastoma | 24 | 0.748 | 1 | VEGFR2 |
| Multiple Myeloma | 25 | 0.737 | 1 | VEGFR2 |
| Myelofibrosis | 22 | 0.737 | 1 | JAK-STAT pathway |
| CLL | 20 | 0.737 | 1 | BCL2 pathway |
| AML | 34 | 0.806 | 2 | VEGFR2, TP53 |

**Clinical context**: Mebendazole (Vermox) is a WHO Essential Medicine (~$0.05/dose). Multiple Phase I/II trials are ongoing for glioblastoma (NCT01729260) and colorectal cancer. Its BRAF inhibition (Melanoma rank 7) and VEGFR2 inhibition (RCC rank 3, HCC rank 7) suggest mechanisms beyond its antihelmintic action.

### Niclosamide (13 cancer types)

An anthelmintic with strong STAT3 and mTOR pathway connections. Strongest signal in AML.

| Disease | Rank | Score | Paths | Key pathway |
|---------|-----:|------:|------:|-------------|
| AML | 6 | 0.886 | 3 | STAT3->BCL2 |
| Breast Cancer | 15 | 0.805 | 2 | mTOR, TP53 |
| RCC | 16 | 0.790 | 2 | mTOR |
| Colorectal Cancer | 32 | 0.761 | 1 | STAT3 |
| Li-Fraumeni Syndrome | 29 | 0.743 | 1 | TP53 |
| NSCLC | 35 | 0.730 | 1 | STAT3 |
| CLL | 25 | 0.729 | 1 | STAT3->BCL2 |
| Melanoma | 31 | 0.720 | 1 | STAT3 |
| Glioblastoma | 29 | 0.719 | 1 | STAT3 |
| GIST | 34 | 0.718 | 1 | STAT3 |
| Pancreatic Cancer | 22 | 0.716 | 1 | STAT3 |
| HCC | 35 | 0.714 | 1 | STAT3 |
| CML | 28 | 0.715 | 1 | STAT3 |

**Clinical context**: Niclosamide (~$0.10/dose) is being investigated in Phase II trials for prostate cancer (NCT02532114) and colorectal cancer. Its STAT3 inhibition is well-documented (PMID:23149263).

### Aspirin (11 cancer types)

COX-2 inhibition provides the primary mechanistic link to colorectal cancer. Additional NF-kB pathway connections to other cancers.

| Disease | Rank | Score | Paths | Key pathway |
|---------|-----:|------:|------:|-------------|
| Colorectal Cancer | 19 | 0.812 | 2 | COX2 (driver), NF-kB |
| AML | 32 | 0.811 | 2 | NF-kB, STAT3 |
| Li-Fraumeni Syndrome | 32 | 0.732 | 1 | STAT3 |
| NSCLC | 37 | 0.726 | 1 | COX2 |
| Melanoma | 30 | 0.725 | 1 | NF-kB |
| CML | 27 | 0.719 | 1 | NF-kB |
| GIST | 30 | 0.722 | 1 | COX2 |
| HCC | 31 | 0.719 | 1 | COX2 |
| Prostate Cancer | 29 | 0.720 | 1 | COX2 |
| Soft Tissue Sarcoma | 39 | 0.709 | 1 | COX2 |
| Glioblastoma | 39 | 0.697 | 1 | COX2 |

**Clinical context**: Aspirin's colorectal cancer prevention is supported by large epidemiological studies (PMID:21355013). The USPSTF has recommended low-dose aspirin for CRC chemoprevention in specific populations.

### Metformin (6 cancer types)

mTOR/AMPK pathway inhibition provides mechanistic links to multiple cancers. Strongest signal in breast cancer.

| Disease | Rank | Score | Paths | Key pathway |
|---------|-----:|------:|------:|-------------|
| Breast Cancer | 12 | 0.808 | 3 | mTOR, AMPK, AKT1 |
| AML | 16 | 0.853 | 2 | mTOR |
| RCC | 21 | 0.774 | 2 | mTOR |
| Pancreatic Cancer | 28 | 0.703 | 1 | mTOR |
| CML | 47 | 0.647 | 1 | mTOR |
| CLL | 44 | 0.654 | 1 | mTOR |

**Clinical context**: Metformin (~$0.03/dose) has extensive epidemiological evidence for cancer risk reduction. Multiple Phase III trials are ongoing for breast cancer (NCT01101438) and pancreatic cancer. mTOR pathway: `Metformin -inhibits-> MTOR -associated_with-> Breast_Cancer` (confidence 0.624).

### Thalidomide (7 cancer types)

TNF-alpha and angiogenesis inhibition. Already FDA-approved for multiple myeloma (as Thalomid), so additional cancer signals are noteworthy.

| Disease | Rank | Score | Paths | Key pathway |
|---------|-----:|------:|------:|-------------|
| Prostate Cancer | 5 | 0.600 | 0 | TNF-alpha |
| GIST | 15 | 0.779 | 1 | VEGFR2 |
| RCC | 19 | 0.784 | 1 | VEGFR2 |
| HCC | 19 | 0.779 | 1 | VEGFR2 |
| Colorectal Cancer | 33 | 0.759 | 1 | VEGFR2 |
| Soft Tissue Sarcoma | 32 | pending | 1 | VEGFR2 |
| Glioblastoma | 36 | 0.702 | 1 | VEGFR2 |

### Atorvastatin (6 cancer types)

KRAS pathway modulation via indirect inhibition. Strongest mechanistic evidence in melanoma through KRAS->BRAF->MEK1 cascade.

| Disease | Rank | Score | Paths | Key pathway |
|---------|-----:|------:|------:|-------------|
| Melanoma | 14 | 0.817 | 6 | KRAS->BRAF->MEK1 |
| Pancreatic Cancer | 11 | 0.805 | 1 | KRAS |
| GIST | 6 | 0.800 | 0 | -- |
| CLL | 14 | 0.700 | 0 | -- |
| CML | 6 | 0.675 | 0 | -- |
| Prostate Cancer | 13 | 0.550 | 0 | -- |

**Clinical context**: Statins have shown cancer risk reduction in large observational studies. Atorvastatin's KRAS pathway connection (Melanoma: `Atorvastatin -indirect_inhibitor-> KRAS -activates-> BRAF -driver_of-> Melanoma`, 6 paths) is mechanistically plausible.

### Other Multi-Disease Candidates

| Drug | Cancers | Best rank | Key pathway | Notes |
|------|--------:|----------:|-------------|-------|
| Disulfiram | 5 | 8 (Li-Fraumeni) | TP53 activation | Alcohol deterrent, ~$0.50/day |
| Chloroquine | 4 | 4 (Myelofibrosis) | mTOR, TP53 | Antimalarial, autophagy inhibitor |
| Doxycycline | 3 | 4 (Breast Cancer) | MMP9, MMP2 | Antibiotic, MMP inhibition |
| Valproic Acid | 2 | 10 (AML) | HDAC1, HDAC2 | Anticonvulsant, HDAC inhibitor |
| Propranolol | 2 | 15 (Colorectal) | VEGFR2, NF-kB | Beta-blocker, anti-angiogenic |
| Clarithromycin | 3 | 3 (Multiple Myeloma) | IL6 | Antibiotic, IL-6 suppression |
| Cimetidine | 3 | 9 (GIST) | -- | H2-blocker, immune modulation |

---

## Disease-by-Disease Highlights

The following sections highlight the strongest cheap generic signals per disease. For full rankings including targeted therapies, run:

```powershell
python validation\triage.py <Disease> --top 20
```

### AML (Acute Myeloid Leukemia)

**5 cheap generics in top 35**. Strongest: Niclosamide (rank 6, score 0.886).

**Niclosamide** (rank 6, score 0.886, 3 paths):
- `Niclosamide -inhibits-> STAT3 -associated_with-> AML` (conf: 0.612)
- `Niclosamide -inhibits-> STAT3 -activates-> BCL2 -associated_with-> AML` (conf: 0.597)
- `Niclosamide -inhibits-> NFKB1 -associated_with-> AML` (conf: 0.510)

**Valproic Acid** (rank 10, score 0.854, 2 paths):
- `Valproic_Acid -inhibits-> HDAC1 -associated_with-> AML` (conf: 0.637)
- `Valproic_Acid -inhibits-> HDAC2 -associated_with-> AML` (conf: 0.564)

**Metformin** (rank 16, score 0.853, 2 paths):
- `Metformin -inhibits-> MTOR -associated_with-> AML` (conf: 0.640)

### Breast Cancer

**6 cheap generics in top 25**. Strongest: Metformin (rank 12, score 0.808).

**Metformin** (rank 12, score 0.808, 3 paths):
- `Metformin -inhibits-> MTOR -associated_with-> Breast_Cancer` (conf: 0.624)
- `Metformin -inhibits-> MTOR -regulates-> TP53 -associated_with-> Breast_Cancer` (conf: 0.544)
- `Metformin -activates-> AMPK -associated_with-> Breast_Cancer` (conf: 0.540) [PMID:11602624]

**Doxycycline** (rank 4, score 0.916, 2 paths):
- `Doxycycline -inhibits-> MMP9 -associated_with-> Breast_Cancer` (conf: 0.558)
- `Doxycycline -inhibits-> MMP2 -associated_with-> Breast_Cancer` (conf: 0.504)

**Niclosamide** (rank 15, score 0.805, 2 paths):
- `Niclosamide -inhibits-> MTOR -associated_with-> Breast_Cancer` (conf: 0.624)

### Colorectal Cancer

**3 cheap generics in top 20**. Strongest: Mebendazole (rank 13, score 0.824).

**Mebendazole** (rank 13, score 0.824, 3 paths):
- `Mebendazole -inhibits-> VEGFR2 -associated_with-> Colorectal_Cancer` (conf: 0.574) [PMID:15205295]
- `Mebendazole -activator-> TP53 -associated_with-> Colorectal_Cancer` (conf: 0.572)
- `Mebendazole -inhibits-> BRAF -associated_with-> Colorectal_Cancer` (conf: 0.525)

**Aspirin** (rank 19, score 0.812, 2 paths):
- `Aspirin -inhibits-> COX2 -driver_of-> Colorectal_Cancer` (conf: 0.760)
- `Aspirin -inhibits-> NFKB1 -associated_with-> Colorectal_Cancer` (conf: 0.504)

### Melanoma

**4 cheap generics in top 20**. Strongest: Mebendazole (rank 7, score 0.816).

**Mebendazole** (rank 7, score 0.816, 2 paths):
- `Mebendazole -inhibits-> BRAF -driver_of-> Melanoma` (conf: 0.665) [PMID:12068308]
- `Mebendazole -inhibits-> BRAF -phosphorylates-> MEK1 -driver_of-> Melanoma` (conf: 0.624) [PMID:22389471]

**Atorvastatin** (rank 14, score 0.817, 6 paths):
- `Atorvastatin -indirect_inhibitor-> KRAS -activates-> BRAF -driver_of-> Melanoma` (conf: 0.663) [PMID:12068308]
- `Atorvastatin -indirect_inhibitor-> KRAS -activates-> BRAF -phosphorylates-> MEK1 -driver_of-> Melanoma` (conf: 0.622) [PMID:22389471]

### RCC (Renal Cell Carcinoma)

**7 cheap generics in top 20**. Highest generic density of any disease. Strongest: Mebendazole (rank 3, score 0.847).

**Mebendazole** (rank 3, score 0.847, 2 paths):
- `Mebendazole -inhibits-> VEGFR2 -driver_of-> RCC` (conf: 0.722) [PMID:17332249]

**Niclosamide** (rank 16, score 0.790, 2 paths):
- `Niclosamide -inhibits-> MTOR -associated_with-> RCC` (conf: 0.640) [PMID:17229949]

**Metformin** (rank 21, score 0.774, 2 paths):
- `Metformin -inhibits-> MTOR -associated_with-> RCC` (conf: 0.640) [PMID:17229949]

### HCC (Hepatocellular Carcinoma)

**2 cheap generics in top 20**. Strongest: Mebendazole (rank 7, score 0.827).

**Mebendazole** (rank 7, score 0.827, 1 path):
- `Mebendazole -inhibits-> VEGFR2 -driver_of-> HCC` (conf: 0.672)

### GIST (Gastrointestinal Stromal Tumor)

**6 cheap generics in top 20**. Strongest: Mebendazole (rank 2, score 0.837).

**Mebendazole** (rank 2, score 0.837, 3 paths):
- VEGFR2, BRAF, TP53 pathways. Only targeted kinase inhibitors (Imatinib, Sunitinib) rank higher.

### Li-Fraumeni Syndrome

**4 cheap generics in top 15**. TP53 activators dominate due to TP53 being the defining driver.

**Mebendazole** (rank 21, score 0.779, 2 paths):
- `Mebendazole -activator-> TP53 -driver_of-> Li_Fraumeni_Syndrome` (conf: 0.643)

**Disulfiram** (rank 8, score 0.736, 2 paths):
- `Disulfiram -activator-> TP53 -driver_of-> Li_Fraumeni_Syndrome` (conf: 0.544)

### Soft Tissue Sarcoma

**2 cheap generics in top 20**. Strongest: Mebendazole (rank 11, score 0.825).

**Mebendazole** (rank 11, score 0.825, 2 paths):
- `Mebendazole -activator-> TP53 -driver_of-> Soft_Tissue_Sarcoma` (conf: 0.552)
- `Mebendazole -inhibits-> VEGFR2 -associated_with-> Soft_Tissue_Sarcoma` (conf: 0.533)

### Multiple Myeloma

**6 cheap generics in top 20**. Strongest: Clarithromycin (rank 3, score 0.713).

**Clarithromycin** (rank 3, score 0.713, 1 path):
- `Clarithromycin -inhibits-> IL6 -driver_of-> Multiple_Myeloma` (conf: 0.552)

### Other Diseases

| Disease | Top generic | Rank | Score | Key pathway |
|---------|-----------|-----:|------:|-------------|
| NSCLC | Mebendazole | 23 | 0.777 | VEGFR2 |
| Pancreatic Cancer | Atorvastatin | 11 | 0.805 | KRAS |
| Glioblastoma | Mebendazole | 24 | 0.748 | VEGFR2 |
| CML | Mebendazole | 24 | 0.733 | BCR-ABL pathway |
| CLL | Niclosamide | 25 | 0.729 | STAT3->BCL2 |
| Myelofibrosis | Aspirin | 1 | 0.700 | JAK-STAT |
| Prostate Cancer | Thalidomide | 5 | 0.600 | TNF-alpha |
| Ewing Sarcoma | Mebendazole | 5 | 0.613 | TP53 |
| Type 2 Diabetes | Ivermectin | 15 | 0.693 | -- |

---

## ClinicalTrials.gov Cross-Check

The top 30 NOT_APPROVED predictions (all drugs, not just generics) were cross-checked against ClinicalTrials.gov and PubMed:

| Category | Count | Percentage | Interpretation |
|----------|------:|----------:|----------------|
| **IN_TRIALS** | 19 | 63% | Already in active/completed human clinical trials |
| **PRECLINICAL** | 9 | 30% | Published preclinical evidence (in vitro, animal models) |
| **NOVEL** | 2 | 7% | No significant prior evidence found |

This means the system predominantly surfaces hypotheses that real clinical teams have independently found worth investigating -- validating the mechanistic reasoning approach.

---

## Getting Current Rankings

The scores in this document reflect the 2026-05-26 system state. For current rankings with detailed mechanistic paths and strategy votes, use the triage CLI:

```powershell
# Disease-first: rank all drugs for a disease
python validation\triage.py Melanoma --top 20

# Drug-first: rank all diseases for a drug
python validation\triage.py --drug Mebendazole

# Specific pair: detailed report with evidence chains
python validation\triage.py Melanoma --drug Mebendazole

# Machine-readable output
python validation\triage.py AML --json
python validation\triage.py AML --markdown

# Full ranking (all drugs)
python validation\triage.py Melanoma --all
```

---

## Methodology

### Scoring

Categorical AI analysis combining 9 strategies over the drug-target-disease knowledge graph:

```
base = mean(8 strategy confidences)         # composition, binding_evidence,
                                             # coherence, conjecture, natural_transform,
                                             # game_theory, bayesian, path_bonus
path_bonus = min(0.25, 0.04 * sum(path_confidence))  # confidence-weighted
yoneda_bonus = min(0.10, 0.06 * similarity)           # structural similarity
score = min(1.0, base + path_bonus + yoneda_bonus)
```

### Graph

- **464 objects**: 78 drugs, 366 proteins, 20 diseases
- **5,382 morphisms**: source strings on all morphisms; 610 PMID identifiers plus ChEMBL/FDA/KEGG/STRING/computational sources
- **204 edges** with quantitative evidence (IC50, mutation freq, HR, response rates)
- **Evidence tiers**: MEASURED 1,073 | ESTABLISHED 282 | INFERRED 809 | SPECULATIVE 955 | HYPOTHESIS 159 | NOISE 2,104

### Validation

| Protocol | AUROC | 95% CI | AUPRC |
|----------|------:|--------|------:|
| remove_direct_labels | 0.9747 | [0.9606, 0.9855] | 0.552 |
| loocv | 0.9759 | not bootstrapped in current rerun | 0.554 |

Strongest baseline: degree_product AUROC 0.6307 (margin: +0.3440).

### Status Labels

- **APPROVED**: One of 44 FDA-approved oncology indications in our database
- **NOT_APPROVED**: Not in our 44 labels. Does NOT mean unstudied -- the candidate may already be in clinical trials, published literature, or off-label use

---

## Disclaimer

This is a **research tool for hypothesis generation**, not a clinical decision support system. All predictions require experimental and clinical validation. Do not use for patient treatment without proper validation, IRB approval, and clinical trial design.

---

## See Also

- [TRACK_A_DRUG_REPURPOSING.md](TRACK_A_DRUG_REPURPOSING.md) -- How the system works
- [AUDIT_WALKTHROUGH.md](AUDIT_WALKTHROUGH.md) -- Worked examples tracing individual predictions
- [EVIDENCE_AND_PROVENANCE.md](EVIDENCE_AND_PROVENANCE.md) -- Data sources and provenance
- [VALIDATION_AND_BENCHMARKS.md](VALIDATION_AND_BENCHMARKS.md) -- Benchmark methodology

---

*Generated: 2026-05-26 | Source: KOMPOSOS-IV-PHARM tier1.db | Author: James Ray Hawkins*
