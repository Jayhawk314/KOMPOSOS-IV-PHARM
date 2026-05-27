# Cheap Drug Repurposing Candidates

**Generated**: 2026-05-26 (post-Yoneda Distance Strategy, quantitative evidence)
**Source**: KOMPOSOS-IV-PHARM tier1.db
**Graph**: 1,146 objects, 5,382 morphisms (464 core + 682 ChEMBL compounds)
**Validation**: remove_direct_labels AUROC 0.965, AUPRC 0.634; LOOCV AUROC 0.9616, AUPRC 0.5668; 44 positives
**Strongest baseline**: shortest_path AUROC 0.931 (margin +0.034)

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

Drugs with mechanistic pathway support for multiple cancers (highest priority for investigation):

### Mebendazole

**Cancer types**: 9

- **Colorectal_Cancer**: Rank 3, Score 0.992, 3 mechanistic paths (NOT_APPROVED)
- **Soft_Tissue_Sarcoma**: Rank 6, Score 0.945, 6 mechanistic paths (NOT_APPROVED)
- **HCC**: Rank 1, Score 0.903, 2 mechanistic paths (NOT_APPROVED)
- **RCC**: Rank 4, Score 0.855, 1 mechanistic paths (NOT_APPROVED)
- **Melanoma**: Rank 12, Score 0.852, 2 mechanistic paths (NOT_APPROVED)
- **Breast_Cancer**: Rank 17, Score 0.831, 6 mechanistic paths (NOT_APPROVED)
- **Li_Fraumeni_Syndrome**: Rank 5, Score 0.801, 2 mechanistic paths (NOT_APPROVED)
- **GIST**: Rank 14, Score 0.800, 0 mechanistic paths (NOT_APPROVED)
- **Ewing_Sarcoma**: Rank 5, Score 0.613, 1 mechanistic paths (NOT_APPROVED)

### Aspirin

**Cancer types**: 8

- **Colorectal_Cancer**: Rank 4, Score 0.966, 3 mechanistic paths (NOT_APPROVED)
- **AML**: Rank 15, Score 0.837, 3 mechanistic paths (NOT_APPROVED)
- **Melanoma**: Rank 18, Score 0.800, 0 mechanistic paths (NOT_APPROVED)
- **RCC**: Rank 13, Score 0.800, 0 mechanistic paths (NOT_APPROVED)
- **Glioblastoma**: Rank 15, Score 0.700, 0 mechanistic paths (NOT_APPROVED)
- **Multiple_Myeloma**: Rank 5, Score 0.700, 0 mechanistic paths (NOT_APPROVED)
- **Myelofibrosis**: Rank 1, Score 0.700, 0 mechanistic paths (NOT_APPROVED)
- **Prostate_Cancer**: Rank 11, Score 0.550, 0 mechanistic paths (NOT_APPROVED)

### Auranofin

**Cancer types**: 7

- **Melanoma**: Rank 19, Score 0.800, 0 mechanistic paths (NOT_APPROVED)
- **RCC**: Rank 14, Score 0.800, 0 mechanistic paths (NOT_APPROVED)
- **AML**: Rank 18, Score 0.799, 2 mechanistic paths (NOT_APPROVED)
- **CLL**: Rank 15, Score 0.700, 0 mechanistic paths (NOT_APPROVED)
- **Multiple_Myeloma**: Rank 6, Score 0.700, 0 mechanistic paths (NOT_APPROVED)
- **Ewing_Sarcoma**: Rank 17, Score 0.550, 0 mechanistic paths (NOT_APPROVED)
- **Prostate_Cancer**: Rank 14, Score 0.550, 0 mechanistic paths (NOT_APPROVED)

### Niclosamide

**Cancer types**: 6

- **AML**: Rank 2, Score 0.902, 3 mechanistic paths (NOT_APPROVED)
- **Breast_Cancer**: Rank 8, Score 0.883, 5 mechanistic paths (NOT_APPROVED)
- **RCC**: Rank 10, Score 0.834, 1 mechanistic paths (NOT_APPROVED)
- **CLL**: Rank 11, Score 0.701, 1 mechanistic paths (NOT_APPROVED)
- **Multiple_Myeloma**: Rank 20, Score 0.700, 0 mechanistic paths (NOT_APPROVED)
- **Myelofibrosis**: Rank 8, Score 0.700, 0 mechanistic paths (NOT_APPROVED)

### Ivermectin

**Cancer types**: 6

- **AML**: Rank 17, Score 0.811, 3 mechanistic paths (NOT_APPROVED)
- **GIST**: Rank 13, Score 0.800, 0 mechanistic paths (NOT_APPROVED)
- **Myelofibrosis**: Rank 6, Score 0.700, 0 mechanistic paths (NOT_APPROVED)
- **Type2_Diabetes**: Rank 15, Score 0.693, 0 mechanistic paths (NOT_APPROVED)
- **CML**: Rank 8, Score 0.675, 0 mechanistic paths (NOT_APPROVED)
- **Prostate_Cancer**: Rank 4, Score 0.600, 0 mechanistic paths (NOT_APPROVED)

### Metformin

**Cancer types**: 6

- **Breast_Cancer**: Rank 1, Score 0.975, 8 mechanistic paths (NOT_APPROVED)
- **RCC**: Rank 11, Score 0.831, 2 mechanistic paths (NOT_APPROVED)
- **HCC**: Rank 10, Score 0.800, 0 mechanistic paths (NOT_APPROVED)
- **CML**: Rank 5, Score 0.679, 0 mechanistic paths (NOT_APPROVED)
- **Li_Fraumeni_Syndrome**: Rank 14, Score 0.671, 5 mechanistic paths (NOT_APPROVED)
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

## Disease-by-Disease Breakdown

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

## ClinicalTrials.gov Cross-Check (2026-05-12)

30 top repurposing candidates verified against ClinicalTrials.gov and PubMed:

| Drug | Disease | Score | Trial Status | Key Evidence |
|------|---------|------:|-------------|-------------|
| Mebendazole | Colorectal Cancer | 0.992 | IN_TRIALS | NCT03925662 (adjuvant to bevacizumab+FOLFOX4) |
| Mebendazole | HCC | 0.903 | IN_TRIALS | NCT04443049 (+ lenvatinib) |
| Mebendazole | Soft Tissue Sarcoma | 0.945 | PRECLINICAL | Preclinical anti-angiogenesis models |
| Mebendazole | Melanoma | 0.852 | PRECLINICAL | Xenograft models via Bcl-2 |
| Mebendazole | Breast Cancer | 0.831 | PRECLINICAL | HIF-1/2 inhibition, radiation potentiation |
| Mebendazole | RCC | 0.855 | PRECLINICAL | Modest in vitro activity |
| Metformin | Breast Cancer | 0.975 | IN_TRIALS | 57 trials; Phase III MA.32 (3,649 patients) |
| Metformin | RCC | 0.831 | IN_TRIALS | Pooled analysis: OS 29.3 vs 20.9 months |
| Metformin | HCC | 0.800 | IN_TRIALS | Clinical cohorts: prolonged survival |
| Metformin | CML | 0.679 | IN_TRIALS | NCT02348957; enhanced TKI response |
| Aspirin | Colorectal Cancer | 0.966 | IN_TRIALS | ALASCCA (NEJM 2025): 51% lower recurrence |
| Aspirin | Myelofibrosis | 0.700 | IN_TRIALS | Registry: thrombosis reduction |
| Aspirin | AML | 0.837 | PRECLINICAL | Epidemiological risk reduction |
| Niclosamide | AML | 0.902 | IN_TRIALS | NCT05188170 (Phase 1 + cytarabine) |
| Niclosamide | Breast Cancer | 0.883 | PRECLINICAL | CSC inhibition; bioavailability limits |
| Niclosamide | RCC | 0.834 | PRECLINICAL | Wnt/beta-catenin inhibition |
| Ivermectin | AML | 0.811 | PRECLINICAL | Synergy with cytarabine/daunorubicin |
| Ivermectin | Prostate Cancer | 0.600 | IN_TRIALS | NCT05318469 (+ balstilimab) |
| Atorvastatin | Melanoma | 0.817 | PRECLINICAL | Retrospective: HR 0.38 for OS |
| Atorvastatin | Pancreatic Cancer | 0.805 | PRECLINICAL | Transgenic mice: 85% to 35% PDAC |
| Doxycycline | Breast Cancer | 0.916 | IN_TRIALS | NEODOXy trial; CSC marker reduction |
| Disulfiram | Soft Tissue Sarcoma | 0.773 | PRECLINICAL | ROS induction, proteasome inhibition |
| Disulfiram | Li-Fraumeni | 0.736 | NOVEL | No significant prior evidence |
| Chloroquine | Breast Cancer | 0.818 | IN_TRIALS | Phase II CQ+taxanes: 45% ORR |
| Chloroquine | Li-Fraumeni | 0.676 | NOVEL | No significant prior evidence |
| Valproic Acid | AML | 0.854 | IN_TRIALS | AML 06-04 RCT: superior 5-year RFS |
| Valproic Acid | Breast Cancer | 0.824 | IN_TRIALS | Window-of-opportunity: Ki-67 reduction |
| Auranofin | AML | 0.799 | PRECLINICAL | Selective AML cytotoxicity in vitro |
| Propranolol | Colorectal Cancer | 0.863 | IN_TRIALS | COMPIT pilot: recurrence 50% to 12.5% |
| Clarithromycin | Multiple Myeloma | 0.713 | IN_TRIALS | BiRD regimen: 38.9% CR rate |

**Summary**: 19/30 IN_TRIALS (63%), 9/30 PRECLINICAL (30%), 2/30 NOVEL (7%)

---

## Methodology

**Scoring**: 7 categorical AI strategies over the drug-target-disease knowledge
graph. Each candidate is scored by averaging strategy confidences and adding a
path bonus for Drug->Protein->Disease mechanistic chains:
`score = mean(strategy_confidences) + min(0.25, 0.10 * composition_path_count)`

**Note on confidence values**: Individual edge confidences in mechanistic paths
(e.g., 0.61, 0.68) reflect the biological plausibility of single Drug→Protein
or Protein→Disease relationships. Final scores (0.9+) are higher because they
combine votes from multiple strategies plus path bonuses. A score of 0.90 with
path confidences 0.6-0.7 means multiple independent pathways support the
prediction.

**Dominant strategy**: Composition (Drug->Protein->Disease path counting) alone
achieves AUROC 0.969. Removing it drops system AUROC by 0.045.

**Graph Source**: tier1.db (SHA256: `0BA4A7E01BBA3E1E52A03CD7765A3E6523618F439AB8A90ED4BD6B4BD95BC8E6`)
- 1143 objects: 78 drugs, 366 proteins, 20 diseases, 679 ExternalCompound nodes
- 1260 morphisms (edges)
- 44 FDA-approved oncology indications (ground truth labels)
- 1260/1260 morphisms with provenance (100%): PMIDs + ChEMBL IDs

**Validation** (audit-reproduced):
- LOOCV AUROC: 0.974 [95% CI: 0.965-0.983] (full_typed/loocv protocol, 44 positives)
- Strongest baseline: shortest_path AUROC 0.931 (margin: +0.043)
- Other baselines: common_neighbor 0.918, path_count 0.596, degree_product 0.474, random 0.469

**Validation** (reported, not yet audit-reproduced):
- External (Hetionet): AUROC 0.744 on 7 held-out pairs
- Temporal holdout (2013 cutoff): AUROC 0.959 on 22 post-2013 FDA approvals
- Disease-level holdout: Mean AUROC 0.877 across 7 diseases

**Status Labels**:
- **APPROVED**: FDA-approved oncology indication (one of 44 in our database)
- **NOT_APPROVED**: Not in our 44 FDA-approved oncology indications. This does NOT mean the drug-disease combination is novel or unstudied. It may already be in clinical trials, published literature, or off-label use. The label only reflects what is in our curated database.

## Disclaimer

This is a **research tool for hypothesis generation**, not a clinical decision support system. All predictions require experimental and clinical validation before any clinical use. Do not use for patient treatment without proper validation, IRB approval, and clinical trial design.

---

**Generated by**: KOMPOSOS-IV-PHARM
**License**: Apache 2.0 / Commercial dual license
**Author**: James Ray Hawkins
