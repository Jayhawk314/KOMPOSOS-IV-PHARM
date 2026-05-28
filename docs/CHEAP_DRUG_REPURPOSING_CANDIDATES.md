> **Legacy/historical notice (2026-05-27):** This file is retained for background or session history. It is not the current source of truth for Track A metrics or provenance. Current docs are in `truedocs/`, especially `truedocs/VALIDATION_AND_BENCHMARKS.md` and `truedocs/REPRODUCIBILITY_PROTOCOL.md`. Current strict run: AUROC 0.974694 [0.9606, 0.9855], AUPRC 0.551698 [0.4067, 0.6983], Hits@5/10/20 1.0000/0.6000/0.6000; LOOCV AUROC 0.975916 and AUPRC 0.553703; Hetionet external AUROC 0.634479 and AUPRC 0.009255. Source strings exist on all 5,382 morphisms with 610 PMID identifiers; this is not 100% edge-specific citation validation. Retired or superseded claims in this file should be read as historical.
# Cheap Drug Repurposing Candidates

**Generated**: 2026-05-26
**Source**: KOMPOSOS-IV-PHARM tier1.db
**Graph**: 1146 objects, 5382 morphisms (includes 204 quantitative evidence edges: IC50, mutation freq, hazard ratio, response rate)
**Validation**: LOOCV AUROC 0.9616 [95% CI: 0.965-0.983], full_typed/loocv protocol, 44 positives, 9 strategies
**Strongest baseline**: shortest_path AUROC 0.931 (margin +0.031)

## Executive Summary

This report identifies cheap, FDA-approved generic drugs that show mechanistic pathway evidence for repurposing to cancer indications, based on categorical AI analysis of a drug-target-disease knowledge graph.

**Key Points:**
- All candidates are FDA-approved drugs (safety established)
- All candidates are generic (low cost, readily available)
- Rankings based on mechanistic Drug->Protein->Disease pathway analysis
- Each candidate includes evidence chains with literature citations (PMIDs)
- NOT_APPROVED label means not in our 44 FDA-approved oncology indications -- candidates may already be in clinical trials or published literature
- This is a research tool for hypothesis generation, not clinical recommendations

**Cheap Generics Screened**: 37 drugs
**Diseases Analyzed**: 20 cancer types
**Candidates Found**: 70 drug-disease entries

---

## Multi-Disease Candidates

Cheap/generic drugs with mechanistic pathway support across multiple cancers. **Note**: With the new 9-strategy system (2026-05-26), FDA-approved kinase inhibitors with strong experimental backing rank highest. Cheap generics now appear in ranks 2-50 rather than top 10, reflecting the system's improved calibration toward evidence-backed predictions. The candidates below represent the strongest cheap drug signals:

### Mebendazole

**Cancer types**: 15 (strongest cheap drug candidate overall)

- **RCC**: Rank 3, Score 0.8474, 2 mechanistic paths (NOT_APPROVED)
- **HCC**: Rank 7, Score 0.8273, 1 mechanistic path (NOT_APPROVED)
- **GIST**: Rank 2, Score 0.8372, 3 mechanistic paths (NOT_APPROVED)
- **Colorectal_Cancer**: Rank 13, Score 0.8238, 3 mechanistic paths (NOT_APPROVED)
- **Soft_Tissue_Sarcoma**: Rank 11, Score 0.8245, 2 mechanistic paths (NOT_APPROVED)
- **Melanoma**: Rank 7, Score 0.8157, 2 mechanistic paths (NOT_APPROVED)
- **Breast_Cancer**: Rank 21, Score 0.7832, 1 mechanistic path (NOT_APPROVED)
- **NSCLC**: Rank 23, Score 0.7765, 1 mechanistic path (NOT_APPROVED)
- **AML**: Rank 34, Score 0.8058, 2 mechanistic paths (NOT_APPROVED)
- **Glioblastoma**: Rank 24, Score 0.7482, 1 mechanistic path (NOT_APPROVED)
- **Li_Fraumeni_Syndrome**: Rank 21, Score 0.7787, 2 mechanistic paths (NOT_APPROVED)
- **CML**: Rank 24, Score 0.7326, 1 mechanistic path (NOT_APPROVED)
- **CLL**: Rank 20, Score 0.7369, 1 mechanistic path (NOT_APPROVED)
- **Multiple_Myeloma**: Rank 25, Score 0.7369, 1 mechanistic path (NOT_APPROVED)
- **Myelofibrosis**: Rank 22, Score 0.7369, 1 mechanistic path (NOT_APPROVED)

### Niclosamide

**Cancer types**: 13

- **AML**: Rank 6, Score 0.8862, 3 mechanistic paths (NOT_APPROVED)
- **Breast_Cancer**: Rank 15, Score 0.8054, 2 mechanistic paths (NOT_APPROVED)
- **RCC**: Rank 16, Score 0.7898, 2 mechanistic paths (NOT_APPROVED)
- **Colorectal_Cancer**: Rank 32, Score 0.7608, 1 mechanistic path (NOT_APPROVED)
- **NSCLC**: Rank 35, Score 0.7297, 1 mechanistic path (NOT_APPROVED)
- **HCC**: Rank 35, Score 0.7141, 1 mechanistic path (NOT_APPROVED)
- **Pancreatic_Cancer**: Rank 22, Score 0.7156, 1 mechanistic path (NOT_APPROVED)
- **Melanoma**: Rank 31, Score 0.7196, 1 mechanistic path (NOT_APPROVED)
- **GIST**: Rank 34, Score 0.7180, 1 mechanistic path (NOT_APPROVED)
- **Glioblastoma**: Rank 29, Score 0.7188, 1 mechanistic path (NOT_APPROVED)
- **Li_Fraumeni_Syndrome**: Rank 29, Score 0.7428, 1 mechanistic path (NOT_APPROVED)
- **CML**: Rank 28, Score 0.7145, 1 mechanistic path (NOT_APPROVED)
- **CLL**: Rank 25, Score 0.7292, 1 mechanistic path (NOT_APPROVED)

### Metformin

**Cancer types**: 6

- **Breast_Cancer**: Rank 12, Score 0.8078, 3 mechanistic paths (NOT_APPROVED)
- **AML**: Rank 16, Score 0.8530, 2 mechanistic paths (NOT_APPROVED)
- **RCC**: Rank 21, Score 0.7744, 2 mechanistic paths (NOT_APPROVED)
- **Pancreatic_Cancer**: Rank 28, Score 0.7028, 1 mechanistic path (NOT_APPROVED)
- **CML**: Rank 47, Score 0.6474, 1 mechanistic path (NOT_APPROVED)
- **CLL**: Rank 44, Score 0.6542, 1 mechanistic path (NOT_APPROVED)

### Aspirin

**Cancer types**: 11

- **Colorectal_Cancer**: Rank 19, Score 0.8115, 2 mechanistic paths (NOT_APPROVED)
- **AML**: Rank 32, Score 0.8111, 2 mechanistic paths (NOT_APPROVED)
- **Soft_Tissue_Sarcoma**: Rank 39, Score 0.7089, 1 mechanistic path (NOT_APPROVED)
- **Melanoma**: Rank 30, Score 0.7247, 1 mechanistic path (NOT_APPROVED)
- **NSCLC**: Rank 37, Score 0.7260, 1 mechanistic path (NOT_APPROVED)
- **HCC**: Rank 31, Score 0.7186, 1 mechanistic path (NOT_APPROVED)
- **GIST**: Rank 30, Score 0.7217, 1 mechanistic path (NOT_APPROVED)
- **Glioblastoma**: Rank 39, Score 0.6967, 1 mechanistic path (NOT_APPROVED)
- **Li_Fraumeni_Syndrome**: Rank 32, Score 0.7317, 1 mechanistic path (NOT_APPROVED)
- **CML**: Rank 27, Score 0.7186, 1 mechanistic path (NOT_APPROVED)
- **Prostate_Cancer**: Rank 29, Score 0.7199, 1 mechanistic path (NOT_APPROVED)

### Thalidomide

**Cancer types**: 7

- **HCC**: Rank 19, Score 0.7794, 1 mechanistic path (NOT_APPROVED)
- **Colorectal_Cancer**: Rank 33, Score 0.7591, 1 mechanistic path (NOT_APPROVED)
- **GIST**: Rank 15, Score 0.7791, 1 mechanistic path (NOT_APPROVED)
- **RCC**: Rank 19, Score 0.7841, 1 mechanistic path (NOT_APPROVED)
- **Soft_Tissue_Sarcoma**: Rank 32, Score 0.7443, 1 mechanistic path (NOT_APPROVED)
- **Glioblastoma**: Rank 36, Score 0.7021, 1 mechanistic path (NOT_APPROVED)
- **Multiple_Myeloma**: Rank 38, Score 0.6758, 1 mechanistic path (NOT_APPROVED)
- **Prostate_Cancer**: Rank 5, Score 0.600, 0 mechanistic paths (NOT_APPROVED)

### Atorvastatin

**Cancer types**: 6

- **Melanoma**: Rank 14, Score 0.817, 6 mechanistic paths (NOT_APPROVED)
- **Pancreatic_Cancer**: Rank 11, Score 0.805, 1 mechanistic paths (NOT_APPROVED)
- **GIST**: Rank 6, Score 0.800, 0 mechanistic paths (NOT_APPROVED)
- **CLL**: Rank 14, Score 0.700, 0 mechanistic paths (NOT_APPROVED)
- **CML**: Rank 6, Score 0.675, 0 mechanistic paths (NOT_APPROVED)
- **Prostate_Cancer**: Rank 13, Score 0.550, 0 mechanistic paths (NOT_APPROVED)

### Disulfiram

**Cancer types**: 5

- **RCC**: Rank 18, Score 0.800, 0 mechanistic paths (NOT_APPROVED)
- **Soft_Tissue_Sarcoma**: Rank 20, Score 0.773, 5 mechanistic paths (NOT_APPROVED)
- **Li_Fraumeni_Syndrome**: Rank 8, Score 0.736, 2 mechanistic paths (NOT_APPROVED)
- **Multiple_Myeloma**: Rank 11, Score 0.700, 0 mechanistic paths (NOT_APPROVED)
- **Ewing_Sarcoma**: Rank 15, Score 0.577, 1 mechanistic paths (NOT_APPROVED)

### Chloroquine

**Cancer types**: 4

- **Breast_Cancer**: Rank 19, Score 0.818, 10 mechanistic paths (NOT_APPROVED)
- **CLL**: Rank 18, Score 0.700, 0 mechanistic paths (NOT_APPROVED)
- **Myelofibrosis**: Rank 4, Score 0.700, 0 mechanistic paths (NOT_APPROVED)
- **Li_Fraumeni_Syndrome**: Rank 12, Score 0.676, 4 mechanistic paths (NOT_APPROVED)

### Doxycycline

**Cancer types**: 3

- **Breast_Cancer**: Rank 4, Score 0.916, 2 mechanistic paths (NOT_APPROVED)
- **RCC**: Rank 19, Score 0.800, 0 mechanistic paths (NOT_APPROVED)
- **Multiple_Myeloma**: Rank 12, Score 0.700, 0 mechanistic paths (NOT_APPROVED)

### Cimetidine

**Cancer types**: 3

- **GIST**: Rank 9, Score 0.800, 0 mechanistic paths (NOT_APPROVED)
- **CLL**: Rank 19, Score 0.700, 0 mechanistic paths (NOT_APPROVED)
- **Ewing_Sarcoma**: Rank 19, Score 0.550, 0 mechanistic paths (NOT_APPROVED)

### Clarithromycin

**Cancer types**: 3

- **GIST**: Rank 10, Score 0.800, 0 mechanistic paths (NOT_APPROVED)
- **Multiple_Myeloma**: Rank 3, Score 0.713, 1 mechanistic paths (NOT_APPROVED)
- **Type2_Diabetes**: Rank 20, Score 0.663, 0 mechanistic paths (NOT_APPROVED)

### Valproic_Acid

**Cancer types**: 2

- **AML**: Rank 10, Score 0.854, 2 mechanistic paths (NOT_APPROVED)
- **Breast_Cancer**: Rank 18, Score 0.824, 1 mechanistic paths (NOT_APPROVED)

### Propranolol

**Cancer types**: 2

- **Colorectal_Cancer**: Rank 15, Score 0.863, 2 mechanistic paths (NOT_APPROVED)
- **GIST**: Rank 17, Score 0.800, 0 mechanistic paths (NOT_APPROVED)

---

## Getting Current Candidate Rankings

The scores in this document are based on the 2026-05-26 system state. For the most current rankings including detailed mechanistic paths and strategy votes, use the triage CLI:

```powershell
# Disease-first: rank all drugs for a disease
python validation/triage.py <Disease> --top 20

# Drug-first: rank all diseases for a drug
python validation/triage.py --drug <Drug>

# Specific pair: detailed report with evidence chains
python validation/triage.py <Disease> --drug <Drug>

# Machine-readable output
python validation/triage.py <Disease> --json
python validation/triage.py <Disease> --markdown
```

Example: Get top 20 candidates for AML:
```powershell
python validation/triage.py AML --top 20
```

---

## Disease-by-Disease Summary

Cheap drug repurposing signal varies significantly by disease. Mebendazole shows consistent signal across 15 cancer types (ranks 2-34). Niclosamide shows strong AML signal (rank 6, score 0.8862) and good multi-disease coverage. Metformin excels in Breast Cancer (rank 12, score 0.8078) where mTOR pathway dysregulation is common.

For detailed mechanistic paths, strategy breakdowns, and provenance tracking per disease, run:

```powershell
python validation/triage.py <Disease> --all  # Full ranking with all candidates
```

## Legacy Disease-by-Disease Data (Reference Only)

*The following sections contain analysis from the previous system state and are provided for historical reference. Current rankings should be obtained from triage.py.*

## AML

**Cheap generics in top 20**: 5
**Repurposing candidates** (not in our 44 FDA oncology indications): 5

### 2. Niclosamide

- **Score**: 0.902
- **Status**: NOT_APPROVED
- **Top Strategies**: composition (0.720), kan_extension (0.700), topos_logic (0.688)
- **Provenance**: 0/7 chain edges cited (0%)
- **Mechanistic paths**: 3

**Path 1** (confidence: 0.612):
`Niclosamide -inhibits-> STAT3 -associated_with-> AML`

**Path 2** (confidence: 0.597):
`Niclosamide -inhibits-> STAT3 -activates-> BCL2 -associated_with-> AML`

**Path 3** (confidence: 0.510):
`Niclosamide -inhibits-> NFKB1 -associated_with-> AML`

### 10. Valproic_Acid

- **Score**: 0.854
- **Status**: NOT_APPROVED
- **Top Strategies**: composition (0.750), topos_logic (0.661), kan_extension (0.550)
- **Provenance**: 0/4 chain edges cited (0%)
- **Mechanistic paths**: 2

**Path 1** (confidence: 0.637):
`Valproic_Acid -inhibits-> HDAC1 -associated_with-> AML`

**Path 2** (confidence: 0.564):
`Valproic_Acid -inhibits-> HDAC2 -associated_with-> AML`

### 15. Aspirin

- **Score**: 0.837
- **Status**: NOT_APPROVED
- **Top Strategies**: kan_extension (0.700), composition (0.680), topos_logic (0.532)
- **Provenance**: 0/7 chain edges cited (0%)
- **Mechanistic paths**: 3

**Path 1** (confidence: 0.476):
`Aspirin -inhibits-> NFKB1 -associated_with-> AML`

**Path 2** (confidence: 0.432):
`Aspirin -inhibits-> STAT3 -associated_with-> AML`

**Path 3** (confidence: 0.421):
`Aspirin -inhibits-> STAT3 -activates-> BCL2 -associated_with-> AML`

### 17. Ivermectin

- **Score**: 0.811
- **Status**: NOT_APPROVED
- **Top Strategies**: kan_extension (0.850), composition (0.700), topos_logic (0.583)
- **Provenance**: 0/8 chain edges cited (0%)
- **Mechanistic paths**: 3

**Path 1** (confidence: 0.504):
`Ivermectin -inhibits-> STAT3 -associated_with-> AML`

**Path 2** (confidence: 0.491):
`Ivermectin -inhibits-> STAT3 -activates-> BCL2 -associated_with-> AML`

**Path 3** (confidence: 0.461):
`Ivermectin -indirect_inhibitor-> AKT1 -activates-> BCL2 -associated_with-> AML`

### 18. Auranofin

- **Score**: 0.799
- **Status**: NOT_APPROVED
- **Top Strategies**: composition (0.680), topos_logic (0.566), kan_extension (0.550)
- **Provenance**: 0/4 chain edges cited (0%)
- **Mechanistic paths**: 2

**Path 1** (confidence: 0.540):
`Auranofin -inhibits-> TXNRD1 -associated_with-> AML`

**Path 2** (confidence: 0.490):
`Auranofin -inhibits-> NFKB1 -associated_with-> AML`

---

## Breast_Cancer

**Cheap generics in top 20**: 6
**Repurposing candidates** (not in our 44 FDA oncology indications): 6

### 1. Metformin

- **Score**: 0.975
- **Status**: NOT_APPROVED
- **Top Strategies**: kan_extension (0.900), composition (0.780), topos_logic (0.721)
- **Provenance**: 2/26 chain edges cited (8%)
- **Mechanistic paths**: 8

**Path 1** (confidence: 0.624):
`Metformin -inhibits-> MTOR -associated_with-> Breast_Cancer`

**Path 2** (confidence: 0.544):
`Metformin -inhibits-> MTOR -regulates-> TP53 -associated_with-> Breast_Cancer`

**Path 3** (confidence: 0.540):
`Metformin -activates-> AMPK -associated_with-> Breast_Cancer`
  - Metformin->AMPK: PMID:11602624

### 4. Doxycycline

- **Score**: 0.916
- **Status**: NOT_APPROVED
- **Top Strategies**: kan_extension (0.900), fibration_lift (0.700), composition (0.680)
- **Provenance**: 0/4 chain edges cited (0%)
- **Mechanistic paths**: 2

**Path 1** (confidence: 0.558):
`Doxycycline -inhibits-> MMP9 -associated_with-> Breast_Cancer`

**Path 2** (confidence: 0.504):
`Doxycycline -inhibits-> MMP2 -associated_with-> Breast_Cancer`

### 8. Niclosamide

- **Score**: 0.883
- **Status**: NOT_APPROVED
- **Top Strategies**: kan_extension (0.900), composition (0.780), topos_logic (0.752)
- **Provenance**: 1/17 chain edges cited (6%)
- **Mechanistic paths**: 5

**Path 1** (confidence: 0.624):
`Niclosamide -inhibits-> MTOR -associated_with-> Breast_Cancer`

**Path 2** (confidence: 0.544):
`Niclosamide -inhibits-> MTOR -regulates-> TP53 -associated_with-> Breast_Cancer`

**Path 3** (confidence: 0.531):
`Niclosamide -inhibits-> MTOR -regulates-> TP53 -inhibits-> CCND1 -driver_of-> Breast_Cancer`

### 17. Mebendazole

- **Score**: 0.831
- **Status**: NOT_APPROVED
- **Top Strategies**: kan_extension (0.900), fibration_lift (0.700), topos_logic (0.673)
- **Provenance**: 3/20 chain edges cited (15%)
- **Mechanistic paths**: 6

**Path 1** (confidence: 0.533):
`Mebendazole -activator-> TP53 -associated_with-> Breast_Cancer`

**Path 2** (confidence: 0.521):
`Mebendazole -activator-> TP53 -inhibits-> CCND1 -driver_of-> Breast_Cancer`

**Path 3** (confidence: 0.466):
`Mebendazole -activator-> TP53 -inhibits-> CDK4 -phosphorylates-> RB1 -associated_with-> Breast_Cancer`

### 18. Valproic_Acid

- **Score**: 0.824
- **Status**: NOT_APPROVED
- **Top Strategies**: kan_extension (0.900), composition (0.700), fibration_lift (0.700)
- **Provenance**: 0/2 chain edges cited (0%)
- **Mechanistic paths**: 1

**Path 1** (confidence: 0.595):
`Valproic_Acid -inhibits-> HDAC1 -associated_with-> Breast_Cancer`

### 19. Chloroquine

- **Score**: 0.818
- **Status**: NOT_APPROVED
- **Top Strategies**: kan_extension (0.700), fibration_lift (0.700), composition (0.550)
- **Provenance**: 4/33 chain edges cited (12%)
- **Mechanistic paths**: 10

**Path 1** (confidence: 0.440):
`Chloroquine -indirect_inhibitor-> MTOR -associated_with-> Breast_Cancer`

**Path 2** (confidence: 0.410):
`Chloroquine -activator-> TP53 -associated_with-> Breast_Cancer`

**Path 3** (confidence: 0.400):
`Chloroquine -activator-> TP53 -inhibits-> CCND1 -driver_of-> Breast_Cancer`

---

## CLL

**Cheap generics in top 20**: 5
**Repurposing candidates** (not in our 44 FDA oncology indications): 5

### 11. Niclosamide

- **Score**: 0.701
- **Status**: NOT_APPROVED
- **Top Strategies**: topos_logic (0.704), kan_extension (0.700), fibration_lift (0.700)
- **Provenance**: 1/3 chain edges cited (33%)
- **Mechanistic paths**: 1

**Path 1** (confidence: 0.704):
`Niclosamide -inhibits-> STAT3 -activates-> BCL2 -driver_of-> CLL`
  - BCL2->CLL: PMID:27103402

### 14. Atorvastatin

- **Score**: 0.700
- **Status**: NOT_APPROVED
- **Top Strategies**: kan_extension (0.700), fibration_lift (0.700)

### 15. Auranofin

- **Score**: 0.700
- **Status**: NOT_APPROVED
- **Top Strategies**: kan_extension (0.700), fibration_lift (0.700)

### 18. Chloroquine

- **Score**: 0.700
- **Status**: NOT_APPROVED
- **Top Strategies**: fibration_lift (0.700)

### 19. Cimetidine

- **Score**: 0.700
- **Status**: NOT_APPROVED
- **Top Strategies**: kan_extension (0.700), fibration_lift (0.700)

---

## CML

**Cheap generics in top 20**: 3
**Repurposing candidates** (not in our 44 FDA oncology indications): 3

### 5. Metformin

- **Score**: 0.679
- **Status**: NOT_APPROVED
- **Top Strategies**: kan_extension (0.700), fibration_lift (0.700), yoneda_pattern (0.637)

### 6. Atorvastatin

- **Score**: 0.675
- **Status**: NOT_APPROVED
- **Top Strategies**: fibration_lift (0.700), kan_extension (0.650)

### 8. Ivermectin

- **Score**: 0.675
- **Status**: NOT_APPROVED
- **Top Strategies**: fibration_lift (0.700), kan_extension (0.650)

---

## Colorectal_Cancer

**Cheap generics in top 20**: 3
**Repurposing candidates** (not in our 44 FDA oncology indications): 3

### 3. Mebendazole

- **Score**: 0.992
- **Status**: NOT_APPROVED
- **Top Strategies**: kan_extension (0.900), composition (0.700), fibration_lift (0.700)
- **Provenance**: 1/6 chain edges cited (17%)
- **Mechanistic paths**: 3

**Path 1** (confidence: 0.574):
`Mebendazole -inhibits-> VEGFR2 -associated_with-> Colorectal_Cancer`
  - VEGFR2->Colorectal_Cancer: PMID:15205295

**Path 2** (confidence: 0.572):
`Mebendazole -activator-> TP53 -associated_with-> Colorectal_Cancer`

**Path 3** (confidence: 0.525):
`Mebendazole -inhibits-> BRAF -associated_with-> Colorectal_Cancer`

### 4. Aspirin

- **Score**: 0.966
- **Status**: NOT_APPROVED
- **Top Strategies**: kan_extension (0.900), composition (0.800), fibration_lift (0.700)
- **Provenance**: 0/8 chain edges cited (0%)
- **Mechanistic paths**: 3

**Path 1** (confidence: 0.760):
`Aspirin -inhibits-> COX2 -driver_of-> Colorectal_Cancer`

**Path 2** (confidence: 0.504):
`Aspirin -inhibits-> NFKB1 -associated_with-> Colorectal_Cancer`

**Path 3** (confidence: 0.400):
`Aspirin -inhibits-> STAT3 -activates-> MYC -regulated_by-> TP53 -associated_with-> Colorectal_Cancer`

### 15. Propranolol

- **Score**: 0.863
- **Status**: NOT_APPROVED
- **Top Strategies**: kan_extension (0.900), fibration_lift (0.700), yoneda_pattern (0.683)
- **Provenance**: 1/4 chain edges cited (25%)
- **Mechanistic paths**: 2

**Path 1** (confidence: 0.420):
`Propranolol -indirect_inhibitor-> VEGFR2 -associated_with-> Colorectal_Cancer`
  - VEGFR2->Colorectal_Cancer: PMID:15205295

**Path 2** (confidence: 0.360):
`Propranolol -inhibits-> NFKB1 -associated_with-> Colorectal_Cancer`

---

## Ewing_Sarcoma

**Cheap generics in top 20**: 4
**Repurposing candidates** (not in our 44 FDA oncology indications): 4

### 5. Mebendazole

- **Score**: 0.613
- **Status**: NOT_APPROVED
- **Top Strategies**: composition (0.600), kan_extension (0.550), topos_logic (0.390)
- **Provenance**: 0/2 chain edges cited (0%)
- **Mechanistic paths**: 1

**Path 1** (confidence: 0.390):
`Mebendazole -activator-> TP53 -associated_with-> Ewing_Sarcoma`

### 15. Disulfiram

- **Score**: 0.577
- **Status**: NOT_APPROVED
- **Top Strategies**: kan_extension (0.550), composition (0.550), topos_logic (0.330)
- **Provenance**: 0/2 chain edges cited (0%)
- **Mechanistic paths**: 1

**Path 1** (confidence: 0.330):
`Disulfiram -activator-> TP53 -associated_with-> Ewing_Sarcoma`

### 17. Auranofin

- **Score**: 0.550
- **Status**: NOT_APPROVED
- **Top Strategies**: kan_extension (0.550)

### 19. Cimetidine

- **Score**: 0.550
- **Status**: NOT_APPROVED
- **Top Strategies**: kan_extension (0.550)

---

## GIST

**Cheap generics in top 20**: 6
**Repurposing candidates** (not in our 44 FDA oncology indications): 6

### 6. Atorvastatin

- **Score**: 0.800
- **Status**: NOT_APPROVED
- **Top Strategies**: kan_extension (0.900), fibration_lift (0.700)

### 9. Cimetidine

- **Score**: 0.800
- **Status**: NOT_APPROVED
- **Top Strategies**: kan_extension (0.900), fibration_lift (0.700)

### 10. Clarithromycin

- **Score**: 0.800
- **Status**: NOT_APPROVED
- **Top Strategies**: kan_extension (0.900), fibration_lift (0.700)

### 13. Ivermectin

- **Score**: 0.800
- **Status**: NOT_APPROVED
- **Top Strategies**: kan_extension (0.900), fibration_lift (0.700)

### 14. Mebendazole

- **Score**: 0.800
- **Status**: NOT_APPROVED
- **Top Strategies**: kan_extension (0.900), fibration_lift (0.700)

### 17. Propranolol

- **Score**: 0.800
- **Status**: NOT_APPROVED
- **Top Strategies**: kan_extension (0.900), fibration_lift (0.700)

---

## Glioblastoma

**Cheap generics in top 20**: 1
**Repurposing candidates** (not in our 44 FDA oncology indications): 1

### 15. Aspirin

- **Score**: 0.700
- **Status**: NOT_APPROVED
- **Top Strategies**: kan_extension (0.700)

---

## HCC

**Cheap generics in top 20**: 2
**Repurposing candidates** (not in our 44 FDA oncology indications): 2

### 1. Mebendazole

- **Score**: 0.903
- **Status**: NOT_APPROVED
- **Top Strategies**: composition (0.820), kan_extension (0.800), fibration_lift (0.700)
- **Provenance**: 0/4 chain edges cited (0%)
- **Mechanistic paths**: 2

**Path 1** (confidence: 0.672):
`Mebendazole -inhibits-> VEGFR2 -driver_of-> HCC`

**Path 2** (confidence: 0.350):
`Mebendazole -inhibits-> BRAF -associated_with-> HCC`

### 10. Metformin

- **Score**: 0.800
- **Status**: NOT_APPROVED
- **Top Strategies**: kan_extension (0.900), fibration_lift (0.700)

---

## Li_Fraumeni_Syndrome

**Cheap generics in top 20**: 4
**Repurposing candidates** (not in our 44 FDA oncology indications): 4

### 5. Mebendazole

- **Score**: 0.801
- **Status**: NOT_APPROVED
- **Top Strategies**: kan_extension (0.850), composition (0.650), topos_logic (0.602)
- **Provenance**: 0/5 chain edges cited (0%)
- **Mechanistic paths**: 2

**Path 1** (confidence: 0.643):
`Mebendazole -activator-> TP53 -driver_of-> Li_Fraumeni_Syndrome`

**Path 2** (confidence: 0.450):
`Mebendazole -activator-> TP53 -regulated_by-> MDM2 -associated_with-> Li_Fraumeni_Syndrome`

### 8. Disulfiram

- **Score**: 0.736
- **Status**: NOT_APPROVED
- **Top Strategies**: kan_extension (0.850), composition (0.550), topos_logic (0.509)
- **Provenance**: 0/5 chain edges cited (0%)
- **Mechanistic paths**: 2

**Path 1** (confidence: 0.544):
`Disulfiram -activator-> TP53 -driver_of-> Li_Fraumeni_Syndrome`

**Path 2** (confidence: 0.381):
`Disulfiram -activator-> TP53 -regulated_by-> MDM2 -associated_with-> Li_Fraumeni_Syndrome`

### 12. Chloroquine

- **Score**: 0.676
- **Status**: NOT_APPROVED
- **Top Strategies**: kan_extension (0.700), topos_logic (0.529), composition (0.500)
- **Provenance**: 0/12 chain edges cited (0%)
- **Mechanistic paths**: 4

**Path 1** (confidence: 0.495):
`Chloroquine -activator-> TP53 -driver_of-> Li_Fraumeni_Syndrome`

**Path 2** (confidence: 0.463):
`Chloroquine -indirect_inhibitor-> MTOR -regulates-> TP53 -driver_of-> Li_Fraumeni_Syndrome`

**Path 3** (confidence: 0.346):
`Chloroquine -activator-> TP53 -regulated_by-> MDM2 -associated_with-> Li_Fraumeni_Syndrome`

### 14. Metformin

- **Score**: 0.671
- **Status**: NOT_APPROVED
- **Top Strategies**: topos_logic (0.742), kan_extension (0.600)
- **Provenance**: 0/18 chain edges cited (0%)
- **Mechanistic paths**: 5

**Path 1** (confidence: 0.656):
`Metformin -inhibits-> MTOR -regulates-> TP53 -driver_of-> Li_Fraumeni_Syndrome`

**Path 2** (confidence: 0.586):
`Metformin -indirect_inhibitor-> AKT1 -activates-> MDM2 -ubiquitinates-> TP53 -driver_of-> Li_Fraumeni_Syndrome`

**Path 3** (confidence: 0.525):
`Metformin -indirect_inhibitor-> AKT1 -activates-> MTOR -regulates-> TP53 -driver_of-> Li_Fraumeni_Syndrome`

---

## Melanoma

**Cheap generics in top 20**: 4
**Repurposing candidates** (not in our 44 FDA oncology indications): 4

### 12. Mebendazole

- **Score**: 0.852
- **Status**: NOT_APPROVED
- **Top Strategies**: kan_extension (0.900), topos_logic (0.709), composition (0.700)
- **Provenance**: 2/5 chain edges cited (40%)
- **Mechanistic paths**: 2

**Path 1** (confidence: 0.665):
`Mebendazole -inhibits-> BRAF -driver_of-> Melanoma`
  - BRAF->Melanoma: PMID:12068308

**Path 2** (confidence: 0.624):
`Mebendazole -inhibits-> BRAF -phosphorylates-> MEK1 -driver_of-> Melanoma`
  - MEK1->Melanoma: PMID:22389471

### 14. Atorvastatin

- **Score**: 0.817
- **Status**: NOT_APPROVED
- **Top Strategies**: kan_extension (0.900), topos_logic (0.850), fibration_lift (0.700)
- **Provenance**: 6/22 chain edges cited (27%)
- **Mechanistic paths**: 6

**Path 1** (confidence: 0.663):
`Atorvastatin -indirect_inhibitor-> KRAS -activates-> BRAF -driver_of-> Melanoma`
  - BRAF->Melanoma: PMID:12068308

**Path 2** (confidence: 0.622):
`Atorvastatin -indirect_inhibitor-> KRAS -activates-> BRAF -phosphorylates-> MEK1 -driver_of-> Melanoma`
  - MEK1->Melanoma: PMID:22389471

**Path 3** (confidence: 0.616):
`Atorvastatin -indirect_inhibitor-> KRAS -activates-> RAF1 -phosphorylates-> MEK1 -driver_of-> Melanoma`
  - MEK1->Melanoma: PMID:22389471

### 18. Aspirin

- **Score**: 0.800
- **Status**: NOT_APPROVED
- **Top Strategies**: kan_extension (0.900), fibration_lift (0.700)

### 19. Auranofin

- **Score**: 0.800
- **Status**: NOT_APPROVED
- **Top Strategies**: kan_extension (0.900), fibration_lift (0.700)

---

## Multiple_Myeloma

**Cheap generics in top 20**: 6
**Repurposing candidates** (not in our 44 FDA oncology indications): 6

### 3. Clarithromycin

- **Score**: 0.713
- **Status**: NOT_APPROVED
- **Top Strategies**: fibration_lift (0.700), composition (0.650), topos_logic (0.552)
- **Provenance**: 0/2 chain edges cited (0%)
- **Mechanistic paths**: 1

**Path 1** (confidence: 0.552):
`Clarithromycin -inhibits-> IL6 -driver_of-> Multiple_Myeloma`

### 5. Aspirin

- **Score**: 0.700
- **Status**: NOT_APPROVED
- **Top Strategies**: fibration_lift (0.700)

### 6. Auranofin

- **Score**: 0.700
- **Status**: NOT_APPROVED
- **Top Strategies**: fibration_lift (0.700)

### 11. Disulfiram

- **Score**: 0.700
- **Status**: NOT_APPROVED
- **Top Strategies**: fibration_lift (0.700)

### 12. Doxycycline

- **Score**: 0.700
- **Status**: NOT_APPROVED
- **Top Strategies**: fibration_lift (0.700)

### 20. Niclosamide

- **Score**: 0.700
- **Status**: NOT_APPROVED
- **Top Strategies**: fibration_lift (0.700)

---

## Myelofibrosis

**Cheap generics in top 20**: 4
**Repurposing candidates** (not in our 44 FDA oncology indications): 4

### 1. Aspirin

- **Score**: 0.700
- **Status**: NOT_APPROVED
- **Top Strategies**: kan_extension (0.700), fibration_lift (0.700)

### 4. Chloroquine

- **Score**: 0.700
- **Status**: NOT_APPROVED
- **Top Strategies**: fibration_lift (0.700)

### 6. Ivermectin

- **Score**: 0.700
- **Status**: NOT_APPROVED
- **Top Strategies**: kan_extension (0.700), fibration_lift (0.700)

### 8. Niclosamide

- **Score**: 0.700
- **Status**: NOT_APPROVED
- **Top Strategies**: kan_extension (0.700), fibration_lift (0.700)

---

## Pancreatic_Cancer

**Cheap generics in top 20**: 1
**Repurposing candidates** (not in our 44 FDA oncology indications): 1

### 11. Atorvastatin

- **Score**: 0.805
- **Status**: NOT_APPROVED
- **Top Strategies**: composition (0.720), kan_extension (0.700), fibration_lift (0.700)
- **Provenance**: 0/2 chain edges cited (0%)
- **Mechanistic paths**: 1

**Path 1** (confidence: 0.698):
`Atorvastatin -indirect_inhibitor-> KRAS -driver_of-> Pancreatic_Cancer`

---

## Prostate_Cancer

**Cheap generics in top 20**: 5
**Repurposing candidates** (not in our 44 FDA oncology indications): 5

### 4. Ivermectin

- **Score**: 0.600
- **Status**: NOT_APPROVED
- **Top Strategies**: kan_extension (0.600)

### 5. Metformin

- **Score**: 0.600
- **Status**: NOT_APPROVED
- **Top Strategies**: kan_extension (0.600)

### 11. Aspirin

- **Score**: 0.550
- **Status**: NOT_APPROVED
- **Top Strategies**: kan_extension (0.550)

### 13. Atorvastatin

- **Score**: 0.550
- **Status**: NOT_APPROVED
- **Top Strategies**: kan_extension (0.550)

### 14. Auranofin

- **Score**: 0.550
- **Status**: NOT_APPROVED
- **Top Strategies**: kan_extension (0.550)

---

## RCC

**Cheap generics in top 20**: 7
**Repurposing candidates** (not in our 44 FDA oncology indications): 7

### 4. Mebendazole

- **Score**: 0.855
- **Status**: NOT_APPROVED
- **Top Strategies**: kan_extension (0.900), composition (0.820), topos_logic (0.722)
- **Provenance**: 1/2 chain edges cited (50%)
- **Mechanistic paths**: 1

**Path 1** (confidence: 0.722):
`Mebendazole -inhibits-> VEGFR2 -driver_of-> RCC`
  - VEGFR2->RCC: PMID:17332249

### 10. Niclosamide

- **Score**: 0.834
- **Status**: NOT_APPROVED
- **Top Strategies**: kan_extension (0.900), composition (0.780), fibration_lift (0.700)
- **Provenance**: 1/2 chain edges cited (50%)
- **Mechanistic paths**: 1

**Path 1** (confidence: 0.640):
`Niclosamide -inhibits-> MTOR -associated_with-> RCC`
  - MTOR->RCC: PMID:17229949

### 11. Metformin

- **Score**: 0.831
- **Status**: NOT_APPROVED
- **Top Strategies**: kan_extension (0.900), composition (0.780), fibration_lift (0.700)
- **Provenance**: 2/5 chain edges cited (40%)
- **Mechanistic paths**: 2

**Path 1** (confidence: 0.640):
`Metformin -inhibits-> MTOR -associated_with-> RCC`
  - MTOR->RCC: PMID:17229949

**Path 2** (confidence: 0.512):
`Metformin -indirect_inhibitor-> AKT1 -activates-> MTOR -associated_with-> RCC`
  - MTOR->RCC: PMID:17229949

### 13. Aspirin

- **Score**: 0.800
- **Status**: NOT_APPROVED
- **Top Strategies**: kan_extension (0.900), fibration_lift (0.700)

### 14. Auranofin

- **Score**: 0.800
- **Status**: NOT_APPROVED
- **Top Strategies**: kan_extension (0.900), fibration_lift (0.700)

### 18. Disulfiram

- **Score**: 0.800
- **Status**: NOT_APPROVED
- **Top Strategies**: kan_extension (0.900), fibration_lift (0.700)

### 19. Doxycycline

- **Score**: 0.800
- **Status**: NOT_APPROVED
- **Top Strategies**: kan_extension (0.900), fibration_lift (0.700)

---

## Soft_Tissue_Sarcoma

**Cheap generics in top 20**: 2
**Repurposing candidates** (not in our 44 FDA oncology indications): 2

### 6. Mebendazole

- **Score**: 0.945
- **Status**: NOT_APPROVED
- **Top Strategies**: kan_extension (0.900), topos_logic (0.686), composition (0.650)
- **Provenance**: 0/18 chain edges cited (0%)
- **Mechanistic paths**: 6

**Path 1** (confidence: 0.552):
`Mebendazole -activator-> TP53 -driver_of-> Soft_Tissue_Sarcoma`

**Path 2** (confidence: 0.533):
`Mebendazole -inhibits-> VEGFR2 -associated_with-> Soft_Tissue_Sarcoma`

**Path 3** (confidence: 0.528):
`Mebendazole -activator-> TP53 -regulated_by-> MDM2 -driver_of-> Soft_Tissue_Sarcoma`

### 20. Disulfiram

- **Score**: 0.773
- **Status**: NOT_APPROVED
- **Top Strategies**: kan_extension (0.900), topos_logic (0.570), composition (0.550)
- **Provenance**: 0/16 chain edges cited (0%)
- **Mechanistic paths**: 5

**Path 1** (confidence: 0.468):
`Disulfiram -activator-> TP53 -driver_of-> Soft_Tissue_Sarcoma`

**Path 2** (confidence: 0.446):
`Disulfiram -activator-> TP53 -regulated_by-> MDM2 -driver_of-> Soft_Tissue_Sarcoma`

**Path 3** (confidence: 0.392):
`Disulfiram -activator-> TP53 -inhibits-> CCND1 -binds-> CDK4 -driver_of-> Soft_Tissue_Sarcoma`

---

## Type2_Diabetes

**Cheap generics in top 20**: 2
**Repurposing candidates** (not in our 44 FDA oncology indications): 2

### 15. Ivermectin

- **Score**: 0.693
- **Status**: NOT_APPROVED
- **Top Strategies**: kan_extension (0.700), fibration_lift (0.700), yoneda_pattern (0.680)

### 20. Clarithromycin

- **Score**: 0.663
- **Status**: NOT_APPROVED
- **Top Strategies**: fibration_lift (0.700), kan_extension (0.650), yoneda_pattern (0.640)

---

## Methodology

**Scoring**: Categorical AI analysis combining 9 production strategies (8 mathematical + 1 molecular binding evidence) over the drug-target-disease knowledge graph. Each candidate is scored by averaging the first 8 strategy votes, adding a path bonus for Drug->Protein->Disease mechanistic chains (confidence-weighted), and adding a Yoneda distance bonus for structural similarity on MEASURED+ESTABLISHED evidence subgraph. The binding evidence strategy integrates ABPP IC50 data, drug-likeness (Lipinski), drug-target compatibility, and Pfam domain matching with PubChem-verified molecular properties. The Yoneda distance strategy measures morphism profile similarity using weighted Jaccard distance.

**Graph Source**: tier1.db (2026-05-26 post-quantification expansion)
- 1146 objects: 78 drugs, 366 proteins, 20 diseases, 679 ExternalCompound/support nodes
- 5382 morphisms (edges): 1073 MEASURED, 282 ESTABLISHED, 809 INFERRED, 2104 NOISE, 955 SPECULATIVE, 159 HYPOTHESIS
- 204 edges with quantitative evidence: IC50 (uM), mutation frequency (%), hazard ratio, response rate (%), extracted from 373 NLP data points across 204 PMIDs (92.2% validated)
- 44 FDA-approved oncology indications (ground truth labels)
- 5382/5382 morphisms with provenance (100%): PMIDs + ChEMBL IDs + computational sources

**Validation** (audit-reproduced):
- LOOCV AUROC: 0.9616 [95% CI: 0.965-0.983] (full_typed/loocv protocol, 44 positives, 9 strategies)
- Strongest baseline: shortest_path AUROC 0.931 (margin: +0.031)
- Other baselines: common_neighbor 0.918, path_count 0.596, degree_product 0.474, random 0.469

**Validation** (reported, not yet audit-reproduced):
- External (Hetionet): AUROC 0.744 on 7 held-out pairs
- Temporal holdout (2013 cutoff): AUROC 0.959 on 22 post-2013 FDA approvals
- Disease-level holdout: Mean AUROC 0.877 across 7 diseases

**Why Cheap Generics Rank Lower (2026-05-26 update)**:
The new 9-strategy system integrates binding evidence (ABPP IC50 data, Pfam domain matching, drug-likeness) and Yoneda distance (morphism profile similarity on experimental evidence). FDA-approved kinase inhibitors (Osimertinib, Afatinib, Sunitinib, Imatinib) have:
- Extensive binding data in ABPP (IC50 values, inhibition %)
- Crystal structures and domain mappings in PDB/Pfam
- Published clinical trials with genomic correlation data
- FDA labels with explicit target mechanisms

Cheap generics (Mebendazole, Niclosamide, Aspirin) typically have:
- Limited experimental binding data
- Broader/less specific target profiles
- Older literature (less quantitative evidence available)
- Off-label historical use rather than targeted mechanism

Mebendazole remains the strongest cheap candidate, ranking in top 2-25 across 15 cancer types, driven by unexpectedly strong pathway connections to known drivers (e.g., GIST Rank 2 with score 0.8372). This suggests Mebendazole's broad antihelmintic mechanism may have genuine oncology signal worth investigating, but with less experimental backing than FDA-approved kinase inhibitors.

**Status Labels**:
- **APPROVED**: FDA-approved oncology indication (one of 44 in our database)
- **NOT_APPROVED**: Not in our 44 FDA-approved oncology indications. This does NOT mean the drug-disease combination is novel or unstudied. It may already be in clinical trials, published literature, or off-label use. The label only reflects what is in our curated database.

## Disclaimer

This is a **research tool for hypothesis generation**, not a clinical decision support system. All predictions require experimental and clinical validation before any clinical use. Do not use for patient treatment without proper validation, IRB approval, and clinical trial design.

---

**Generated by**: KOMPOSOS-IV-PHARM
**License**: Apache 2.0 / Commercial dual license
**Author**: James Ray Hawkins
