# PHARM reviewer packet — 50 candidate pairs

Generated 2026-07-31. Graph fingerprint `fa99c35f30246320…`,
1956 scored morphisms, scorer `repurposing_benchmark.score_pair`.

## What I am asking

I am **not** asking whether these are good drugs. I am asking whether the evidence
shown is what you would need to **reject them quickly**.

The pairs below are in random order. Rank is deliberately withheld — I do not want
position to influence your reading.

## Task 1 — code every pair (about 45 minutes)

Assign each pair exactly one code:

| code | meaning |
|---|---|
| **A** | approved indication - this is an FDA-approved use and the label set missed it |
| **B** | in active clinical trial for this indication |
| **C** | published preclinical rationale exists |
| **D** | mechanistically plausible but I can find no documentation |
| **E** | wrong - or the cited evidence does not support the claimed relation |

Codes **A** and **B** matter most to me and are not a criticism of your time: they
tell me how much of what my system calls a false positive is really a gap in my
label set. I currently cannot tell those apart, which is why I will not make any
claim about this system's precision.

A one-line reason is more useful than a careful one. Write "obviously approved" or
"never seen this" and move on.

## Task 2 — blind citation check (about 20 minutes)

See `BLIND_CITATION_SUBSET.md`. Ten cited sentences, each with the relation it is
supposed to support. Answer yes / partially / no. Do that file **before** reading
the pairs below if you can, so the surrounding context does not colour it.

## Task 3 — the debrief question

> What would have to be on this page for you to spend an afternoon on the pairs
> you coded **D**?

---

### P01  —  Cerivastatin  ·  Melanoma

**Path 1** · `Cerivastatin —inhibits→ HMGCR —associated_with→ Melanoma`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Cerivastatin → HMGCR | `inhibits` | MEASURED | ChEMBL:CHEMBL1200563 | — | 1.00 |
| HMGCR → Melanoma | `associated_with` | INFERRED | PMID:40509568; [RELATION-SCREENED] | [40509568](https://pubmed.ncbi.nlm.nih.gov/40509568/) | 0.65 |

**Path 2** · `Cerivastatin —inhibits→ HMGCR —associated_with→ RCC —associated_with→ Melanoma`  ⚠ **routes through another disease — co-occurrence, not mechanism**

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Cerivastatin → HMGCR | `inhibits` | MEASURED | ChEMBL:CHEMBL1200563 | — | 1.00 |
| HMGCR → RCC | `associated_with` | INFERRED | PMID:34712689; [RELATION-SCREENED] | [34712689](https://pubmed.ncbi.nlm.nih.gov/34712689/) | 0.65 |
| RCC → Melanoma | `associated_with` | INFERRED | PMID:39842618; [RELATION-SCREENED] | [39842618](https://pubmed.ncbi.nlm.nih.gov/39842618/) | 0.65 |

**Path 3** · `Cerivastatin —inhibits→ HMGCR —associated_with→ Breast_Cancer —associated_with→ Melanoma`  ⚠ **routes through another disease — co-occurrence, not mechanism**

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Cerivastatin → HMGCR | `inhibits` | MEASURED | ChEMBL:CHEMBL1200563 | — | 1.00 |
| HMGCR → Breast_Cancer | `associated_with` | INFERRED | PMID:39143707; discovery-grounded; agent-adj | [39143707](https://pubmed.ncbi.nlm.nih.gov/39143707/) | 0.60 |
| Breast_Cancer → Melanoma | `associated_with` | INFERRED | PMID:30497674; [RELATION-SCREENED] | [30497674](https://pubmed.ncbi.nlm.nih.gov/30497674/) | 0.65 |

**What this candidate does not have:** every terminal Protein->Disease hop is `associated_with`, a co-occurrence relation, not a mechanistic claim; no quantitative value on any edge (the column is NULL graph-wide)

**Your code (A/B/C/D/E):** `____`    **Why:** 

---

### P02  —  Ibalizumab  ·  Melanoma

**Path 1** · `Ibalizumab —inhibits→ CD4 —associated_with→ Melanoma`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Ibalizumab → CD4 | `inhibits` | MEASURED | ChEMBL:CHEMBL1743029; PMID:41964438; [RELATI | [41964438](https://pubmed.ncbi.nlm.nih.gov/41964438/) | 1.00 |
| CD4 → Melanoma | `associated_with` | ESTABLISHED | PMID:42140948; [RELATION-VERIFIED] | [42140948](https://pubmed.ncbi.nlm.nih.gov/42140948/) | 0.80 |

**Path 2** · `Ibalizumab —inhibits→ CD4 —associated_with→ Ovarian_Cancer —associated_with→ Melanoma`  ⚠ **routes through another disease — co-occurrence, not mechanism**

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Ibalizumab → CD4 | `inhibits` | MEASURED | ChEMBL:CHEMBL1743029; PMID:41964438; [RELATI | [41964438](https://pubmed.ncbi.nlm.nih.gov/41964438/) | 1.00 |
| CD4 → Ovarian_Cancer | `associated_with` | INFERRED | PMID:35552285; discovery-grounded; agent-adj | [35552285](https://pubmed.ncbi.nlm.nih.gov/35552285/) | 0.60 |
| Ovarian_Cancer → Melanoma | `associated_with` | INFERRED | PMID:20301425; [RELATION-SCREENED] | [20301425](https://pubmed.ncbi.nlm.nih.gov/20301425/) | 0.65 |

**Path 3** · `Ibalizumab —inhibits→ CD4 —associated_with→ Ovarian_Cancer —associated_with→ Breast_Cancer —associated_with→ Melanoma`  ⚠ **routes through another disease — co-occurrence, not mechanism**

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Ibalizumab → CD4 | `inhibits` | MEASURED | ChEMBL:CHEMBL1743029; PMID:41964438; [RELATI | [41964438](https://pubmed.ncbi.nlm.nih.gov/41964438/) | 1.00 |
| CD4 → Ovarian_Cancer | `associated_with` | INFERRED | PMID:35552285; discovery-grounded; agent-adj | [35552285](https://pubmed.ncbi.nlm.nih.gov/35552285/) | 0.60 |
| Ovarian_Cancer → Breast_Cancer | `associated_with` | INFERRED | PMID:37455374; [RELATION-SCREENED] | [37455374](https://pubmed.ncbi.nlm.nih.gov/37455374/) | 0.65 |
| Breast_Cancer → Melanoma | `associated_with` | INFERRED | PMID:30497674; [RELATION-SCREENED] | [30497674](https://pubmed.ncbi.nlm.nih.gov/30497674/) | 0.65 |

**What this candidate does not have:** every terminal Protein->Disease hop is `associated_with`, a co-occurrence relation, not a mechanistic claim; no quantitative value on any edge (the column is NULL graph-wide)

**Your code (A/B/C/D/E):** `____`    **Why:** 

---

### P03  —  Ribociclib  ·  Melanoma

**Path 1** · `Ribociclib —inhibits→ CDK4 —associated_with→ Melanoma`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Ribociclib → CDK4 | `inhibits` | ESTABLISHED | FDA:NDA209092, mechanism:CDK4_6_inhibitor; P | [42192962](https://pubmed.ncbi.nlm.nih.gov/42192962/) | 0.96 |
| CDK4 → Melanoma | `associated_with` | INFERRED | cancer_proteins; PMID:42201696; [RELATION-VE | [42201696](https://pubmed.ncbi.nlm.nih.gov/42201696/) | 0.55 |

**Path 2** · `Ribociclib —inhibits→ CDK6 —associated_with→ Melanoma`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Ribociclib → CDK6 | `inhibits` | ESTABLISHED | FDA:NDA209092, mechanism:CDK4_6_inhibitor; P | [40722732](https://pubmed.ncbi.nlm.nih.gov/40722732/) | 0.95 |
| CDK6 → Melanoma | `associated_with` | INFERRED | cancer_proteins; PMID:39495991; [RELATION-VE | [39495991](https://pubmed.ncbi.nlm.nih.gov/39495991/) | 0.55 |

**Path 3** · `Ribociclib —inhibits→ CDK4 —phosphorylates→ RB1 —associated_with→ Melanoma`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Ribociclib → CDK4 | `inhibits` | ESTABLISHED | FDA:NDA209092, mechanism:CDK4_6_inhibitor; P | [42192962](https://pubmed.ncbi.nlm.nih.gov/42192962/) | 0.96 |
| CDK4 → RB1 | `phosphorylates` | ESTABLISHED | KEGG:hsa04110, cancer_proteins.py; PMID:4119 | [41196681](https://pubmed.ncbi.nlm.nih.gov/41196681/) | 0.97 |
| RB1 → Melanoma | `associated_with` | INFERRED | cancer_proteins; PMID:41936939; [LEXICAL-COO | [41936939](https://pubmed.ncbi.nlm.nih.gov/41936939/) | 0.55 |

**What this candidate does not have:** every terminal Protein->Disease hop is `associated_with`, a co-occurrence relation, not a mechanistic claim; no quantitative value on any edge (the column is NULL graph-wide)

**Your code (A/B/C/D/E):** `____`    **Why:** 

---

### P04  —  Osimertinib  ·  NSCLC

**Path 1** · `Osimertinib —inhibits→ EGFR —driver_of→ NSCLC`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Osimertinib → EGFR | `inhibits` | ESTABLISHED | FDA:NDA208065, mechanism:3rd_gen_EGFR_TKI; P | [42182601](https://pubmed.ncbi.nlm.nih.gov/42182601/) | 0.98 |
| EGFR → NSCLC | `driver_of` | ESTABLISHED | PMID:42182703; [LEXICAL-COOCCURRENCE] | [42182703](https://pubmed.ncbi.nlm.nih.gov/42182703/) | 0.95 |

**Path 2** · `Osimertinib —inhibits→ EGFR —activates→ KRAS —driver_of→ NSCLC`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Osimertinib → EGFR | `inhibits` | ESTABLISHED | FDA:NDA208065, mechanism:3rd_gen_EGFR_TKI; P | [42182601](https://pubmed.ncbi.nlm.nih.gov/42182601/) | 0.98 |
| EGFR → KRAS | `activates` | ESTABLISHED | KEGG:hsa04010, cancer_proteins.py | — | 0.95 |
| KRAS → NSCLC | `driver_of` | ESTABLISHED | PMID:42075590; [RELATION-VERIFIED] | [42075590](https://pubmed.ncbi.nlm.nih.gov/42075590/) | 0.88 |

**Path 3** · `Osimertinib —inhibits→ EGFR —activates→ STAT3 —associated_with→ NSCLC`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Osimertinib → EGFR | `inhibits` | ESTABLISHED | FDA:NDA208065, mechanism:3rd_gen_EGFR_TKI; P | [42182601](https://pubmed.ncbi.nlm.nih.gov/42182601/) | 0.98 |
| EGFR → STAT3 | `activates` | ESTABLISHED | KEGG:hsa04630, cancer_proteins.py; PMID:4217 | [42177207](https://pubmed.ncbi.nlm.nih.gov/42177207/) | 0.88 |
| STAT3 → NSCLC | `associated_with` | INFERRED | cancer_proteins | — | 0.55 |

**What this candidate does not have:** no quantitative value on any edge (the column is NULL graph-wide)

**Your code (A/B/C/D/E):** `____`    **Why:** 

---

### P05  —  Vemurafenib  ·  Melanoma

**Path 1** · `Vemurafenib —inhibits→ BRAF —driver_of→ Melanoma`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Vemurafenib → BRAF | `inhibits` | ESTABLISHED | PMID:42179788; [RELATION-VERIFIED] | [42179788](https://pubmed.ncbi.nlm.nih.gov/42179788/) | 0.97 |
| BRAF → Melanoma | `driver_of` | ESTABLISHED | PMID:42126185; [LEXICAL-COOCCURRENCE] | [42126185](https://pubmed.ncbi.nlm.nih.gov/42126185/) | 0.95 |

**Path 2** · `Vemurafenib —inhibits→ BRAF —phosphorylates→ MEK1 —driver_of→ Melanoma`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Vemurafenib → BRAF | `inhibits` | ESTABLISHED | PMID:42179788; [RELATION-VERIFIED] | [42179788](https://pubmed.ncbi.nlm.nih.gov/42179788/) | 0.97 |
| BRAF → MEK1 | `phosphorylates` | ESTABLISHED | KEGG:hsa04010, cancer_proteins.py | — | 0.99 |
| MEK1 → Melanoma | `driver_of` | ESTABLISHED | PMID:22389471 | [22389471](https://pubmed.ncbi.nlm.nih.gov/22389471/) | 0.90 |

**Path 3** · `Vemurafenib —inhibits→ BRAF —associated_with→ RCC —associated_with→ Melanoma`  ⚠ **routes through another disease — co-occurrence, not mechanism**

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Vemurafenib → BRAF | `inhibits` | ESTABLISHED | PMID:42179788; [RELATION-VERIFIED] | [42179788](https://pubmed.ncbi.nlm.nih.gov/42179788/) | 0.97 |
| BRAF → RCC | `associated_with` | MEASURED | ABPP; PMID:41562159; [RELATION-VERIFIED] | [41562159](https://pubmed.ncbi.nlm.nih.gov/41562159/) | 0.80 |
| RCC → Melanoma | `associated_with` | INFERRED | PMID:39842618; [RELATION-SCREENED] | [39842618](https://pubmed.ncbi.nlm.nih.gov/39842618/) | 0.65 |

**What this candidate does not have:** no quantitative value on any edge (the column is NULL graph-wide)

**Your code (A/B/C/D/E):** `____`    **Why:** 

---

### P06  —  Ceritinib  ·  NSCLC

**Path 1** · `Ceritinib —inhibits→ ALK —driver_of→ NSCLC`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Ceritinib → ALK | `inhibits` | MEASURED | ChEMBL:CHEMBL2403108; PMID:42181273; [RELATI | [42181273](https://pubmed.ncbi.nlm.nih.gov/42181273/) | 1.00 |
| ALK → NSCLC | `driver_of` | ESTABLISHED | PMID:42187575; [LEXICAL-COOCCURRENCE] | [42187575](https://pubmed.ncbi.nlm.nih.gov/42187575/) | 0.92 |

**Path 2** · `Ceritinib —inhibits→ ALK —associated_with→ Breast_Cancer —associated_with→ Multiple_Myeloma —associated_with→ NSCLC`  ⚠ **routes through another disease — co-occurrence, not mechanism**

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Ceritinib → ALK | `inhibits` | MEASURED | ChEMBL:CHEMBL2403108; PMID:42181273; [RELATI | [42181273](https://pubmed.ncbi.nlm.nih.gov/42181273/) | 1.00 |
| ALK → Breast_Cancer | `associated_with` | INFERRED | PMID:32954856; [RELATION-SCREENED] | [32954856](https://pubmed.ncbi.nlm.nih.gov/32954856/) | 0.65 |
| Breast_Cancer → Multiple_Myeloma | `associated_with` | INFERRED | PMID:33127577; [RELATION-SCREENED] | [33127577](https://pubmed.ncbi.nlm.nih.gov/33127577/) | 0.65 |
| Multiple_Myeloma → NSCLC | `associated_with` | INFERRED | PMID:36762777; [RELATION-SCREENED] | [36762777](https://pubmed.ncbi.nlm.nih.gov/36762777/) | 0.65 |

**Path 3** · `Ceritinib —inhibits→ ALK —associated_with→ Colorectal_Cancer —associated_with→ Multiple_Myeloma —associated_with→ NSCLC`  ⚠ **routes through another disease — co-occurrence, not mechanism**

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Ceritinib → ALK | `inhibits` | MEASURED | ChEMBL:CHEMBL2403108; PMID:42181273; [RELATI | [42181273](https://pubmed.ncbi.nlm.nih.gov/42181273/) | 1.00 |
| ALK → Colorectal_Cancer | `associated_with` | INFERRED | PMID:40493183; discovery-grounded; agent-adj | [40493183](https://pubmed.ncbi.nlm.nih.gov/40493183/) | 0.60 |
| Colorectal_Cancer → Multiple_Myeloma | `associated_with` | INFERRED | PMID:38967919; [RELATION-SCREENED] | [38967919](https://pubmed.ncbi.nlm.nih.gov/38967919/) | 0.65 |
| Multiple_Myeloma → NSCLC | `associated_with` | INFERRED | PMID:36762777; [RELATION-SCREENED] | [36762777](https://pubmed.ncbi.nlm.nih.gov/36762777/) | 0.65 |

**What this candidate does not have:** no quantitative value on any edge (the column is NULL graph-wide)

**Your code (A/B/C/D/E):** `____`    **Why:** 

---

### P07  —  Dostarlimab  ·  Melanoma

**Path 1** · `Dostarlimab —inhibits→ PDCD1 —associated_with→ Melanoma`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Dostarlimab → PDCD1 | `inhibits` | MEASURED | ChEMBL:CHEMBL4298124 | — | 1.00 |
| PDCD1 → Melanoma | `associated_with` | ESTABLISHED | PMID:40556672; [LEXICAL-COOCCURRENCE] | [40556672](https://pubmed.ncbi.nlm.nih.gov/40556672/) | 0.85 |

**Path 2** · `Dostarlimab —inhibits→ PDCD1 —associated_with→ RCC —associated_with→ Melanoma`  ⚠ **routes through another disease — co-occurrence, not mechanism**

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Dostarlimab → PDCD1 | `inhibits` | MEASURED | ChEMBL:CHEMBL4298124 | — | 1.00 |
| PDCD1 → RCC | `associated_with` | ESTABLISHED | PMID:26406148 | [26406148](https://pubmed.ncbi.nlm.nih.gov/26406148/) | 0.80 |
| RCC → Melanoma | `associated_with` | INFERRED | PMID:39842618; [RELATION-SCREENED] | [39842618](https://pubmed.ncbi.nlm.nih.gov/39842618/) | 0.65 |

**Path 3** · `Dostarlimab —inhibits→ PDCD1 —associated_with→ Ovarian_Cancer —associated_with→ Melanoma`  ⚠ **routes through another disease — co-occurrence, not mechanism**

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Dostarlimab → PDCD1 | `inhibits` | MEASURED | ChEMBL:CHEMBL4298124 | — | 1.00 |
| PDCD1 → Ovarian_Cancer | `associated_with` | INFERRED | PMID:28730785; discovery-grounded; agent-adj | [28730785](https://pubmed.ncbi.nlm.nih.gov/28730785/) | 0.60 |
| Ovarian_Cancer → Melanoma | `associated_with` | INFERRED | PMID:20301425; [RELATION-SCREENED] | [20301425](https://pubmed.ncbi.nlm.nih.gov/20301425/) | 0.65 |

**What this candidate does not have:** every terminal Protein->Disease hop is `associated_with`, a co-occurrence relation, not a mechanistic claim; no quantitative value on any edge (the column is NULL graph-wide)

**Your code (A/B/C/D/E):** `____`    **Why:** 

---

### P08  —  Palbociclib  ·  Melanoma

**Path 1** · `Palbociclib —inhibits→ CDK4 —associated_with→ Melanoma`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Palbociclib → CDK4 | `inhibits` | ESTABLISHED | PMID:42160728; [RELATION-VERIFIED] | [42160728](https://pubmed.ncbi.nlm.nih.gov/42160728/) | 0.97 |
| CDK4 → Melanoma | `associated_with` | INFERRED | cancer_proteins; PMID:42201696; [RELATION-VE | [42201696](https://pubmed.ncbi.nlm.nih.gov/42201696/) | 0.55 |

**Path 2** · `Palbociclib —inhibits→ CDK6 —associated_with→ Melanoma`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Palbociclib → CDK6 | `inhibits` | ESTABLISHED | PMID:41548293; [RELATION-VERIFIED] | [41548293](https://pubmed.ncbi.nlm.nih.gov/41548293/) | 0.96 |
| CDK6 → Melanoma | `associated_with` | INFERRED | cancer_proteins; PMID:39495991; [RELATION-VE | [39495991](https://pubmed.ncbi.nlm.nih.gov/39495991/) | 0.55 |

**Path 3** · `Palbociclib —inhibits→ CDK4 —phosphorylates→ RB1 —associated_with→ Melanoma`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Palbociclib → CDK4 | `inhibits` | ESTABLISHED | PMID:42160728; [RELATION-VERIFIED] | [42160728](https://pubmed.ncbi.nlm.nih.gov/42160728/) | 0.97 |
| CDK4 → RB1 | `phosphorylates` | ESTABLISHED | KEGG:hsa04110, cancer_proteins.py; PMID:4119 | [41196681](https://pubmed.ncbi.nlm.nih.gov/41196681/) | 0.97 |
| RB1 → Melanoma | `associated_with` | INFERRED | cancer_proteins; PMID:41936939; [LEXICAL-COO | [41936939](https://pubmed.ncbi.nlm.nih.gov/41936939/) | 0.55 |

**What this candidate does not have:** every terminal Protein->Disease hop is `associated_with`, a co-occurrence relation, not a mechanistic claim; no quantitative value on any edge (the column is NULL graph-wide)

**Your code (A/B/C/D/E):** `____`    **Why:** 

---

### P09  —  Entrectinib  ·  NSCLC

**Path 1** · `Entrectinib —inhibits→ ALK —driver_of→ NSCLC`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Entrectinib → ALK | `inhibits` | ESTABLISHED | FDA:NDA212725, mechanism:TRK_ROS1_ALK_inhibi | [41837926](https://pubmed.ncbi.nlm.nih.gov/41837926/) | 0.90 |
| ALK → NSCLC | `driver_of` | ESTABLISHED | PMID:42187575; [LEXICAL-COOCCURRENCE] | [42187575](https://pubmed.ncbi.nlm.nih.gov/42187575/) | 0.92 |

**Path 2** · `Entrectinib —inhibits→ ROS1 —driver_of→ NSCLC`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Entrectinib → ROS1 | `inhibits` | ESTABLISHED | FDA:NDA212725, mechanism:TRK_ROS1_ALK_inhibi | [41837926](https://pubmed.ncbi.nlm.nih.gov/41837926/) | 0.97 |
| ROS1 → NSCLC | `driver_of` | ESTABLISHED | PMID:42075590; [RELATION-VERIFIED] | [42075590](https://pubmed.ncbi.nlm.nih.gov/42075590/) | 0.85 |

**Path 3** · `Entrectinib —inhibits→ ALK —associated_with→ Breast_Cancer —associated_with→ Multiple_Myeloma —associated_with→ NSCLC`  ⚠ **routes through another disease — co-occurrence, not mechanism**

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Entrectinib → ALK | `inhibits` | ESTABLISHED | FDA:NDA212725, mechanism:TRK_ROS1_ALK_inhibi | [41837926](https://pubmed.ncbi.nlm.nih.gov/41837926/) | 0.90 |
| ALK → Breast_Cancer | `associated_with` | INFERRED | PMID:32954856; [RELATION-SCREENED] | [32954856](https://pubmed.ncbi.nlm.nih.gov/32954856/) | 0.65 |
| Breast_Cancer → Multiple_Myeloma | `associated_with` | INFERRED | PMID:33127577; [RELATION-SCREENED] | [33127577](https://pubmed.ncbi.nlm.nih.gov/33127577/) | 0.65 |
| Multiple_Myeloma → NSCLC | `associated_with` | INFERRED | PMID:36762777; [RELATION-SCREENED] | [36762777](https://pubmed.ncbi.nlm.nih.gov/36762777/) | 0.65 |

**What this candidate does not have:** no quantitative value on any edge (the column is NULL graph-wide)

**Your code (A/B/C/D/E):** `____`    **Why:** 

---

### P10  —  Capmatinib  ·  NSCLC

**Path 1** · `Capmatinib —inhibits→ MET —associated_with→ NSCLC`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Capmatinib → MET | `inhibits` | ESTABLISHED | FDA:NDA213591, mechanism:MET_TKI; PMID:42130 | [42130628](https://pubmed.ncbi.nlm.nih.gov/42130628/) | 0.98 |
| MET → NSCLC | `associated_with` | ESTABLISHED | PMID:42187575; [RELATION-VERIFIED] | [42187575](https://pubmed.ncbi.nlm.nih.gov/42187575/) | 0.80 |

**Path 2** · `Capmatinib —inhibits→ MET —activates→ KRAS —driver_of→ NSCLC`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Capmatinib → MET | `inhibits` | ESTABLISHED | FDA:NDA213591, mechanism:MET_TKI; PMID:42130 | [42130628](https://pubmed.ncbi.nlm.nih.gov/42130628/) | 0.98 |
| MET → KRAS | `activates` | ESTABLISHED | KEGG:hsa04014, cancer_proteins.py | — | 0.89 |
| KRAS → NSCLC | `driver_of` | ESTABLISHED | PMID:42075590; [RELATION-VERIFIED] | [42075590](https://pubmed.ncbi.nlm.nih.gov/42075590/) | 0.88 |

**Path 3** · `Capmatinib —inhibits→ MET —activates→ PI3KCA —associated_with→ NSCLC`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Capmatinib → MET | `inhibits` | ESTABLISHED | FDA:NDA213591, mechanism:MET_TKI; PMID:42130 | [42130628](https://pubmed.ncbi.nlm.nih.gov/42130628/) | 0.98 |
| MET → PI3KCA | `activates` | ESTABLISHED | PMID:34802045 | [34802045](https://pubmed.ncbi.nlm.nih.gov/34802045/) | 0.91 |
| PI3KCA → NSCLC | `associated_with` | INFERRED | PPI; PMID:41221490; [RELATION-VERIFIED] | [41221490](https://pubmed.ncbi.nlm.nih.gov/41221490/) | 0.50 |

**What this candidate does not have:** no quantitative value on any edge (the column is NULL graph-wide)

**Your code (A/B/C/D/E):** `____`    **Why:** 

---

### P11  —  Dostarlimab  ·  NSCLC

**Path 1** · `Dostarlimab —inhibits→ PDCD1 —associated_with→ NSCLC`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Dostarlimab → PDCD1 | `inhibits` | MEASURED | ChEMBL:CHEMBL4298124 | — | 1.00 |
| PDCD1 → NSCLC | `associated_with` | ESTABLISHED | PMID:40509568; [LEXICAL-COOCCURRENCE] | [40509568](https://pubmed.ncbi.nlm.nih.gov/40509568/) | 0.85 |

**Path 2** · `Dostarlimab —inhibits→ PDCD1 —associated_with→ RCC —associated_with→ Multiple_Myeloma —associated_with→ NSCLC`  ⚠ **routes through another disease — co-occurrence, not mechanism**

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Dostarlimab → PDCD1 | `inhibits` | MEASURED | ChEMBL:CHEMBL4298124 | — | 1.00 |
| PDCD1 → RCC | `associated_with` | ESTABLISHED | PMID:26406148 | [26406148](https://pubmed.ncbi.nlm.nih.gov/26406148/) | 0.80 |
| RCC → Multiple_Myeloma | `associated_with` | INFERRED | PMID:35528462; [RELATION-SCREENED] | [35528462](https://pubmed.ncbi.nlm.nih.gov/35528462/) | 0.65 |
| Multiple_Myeloma → NSCLC | `associated_with` | INFERRED | PMID:36762777; [RELATION-SCREENED] | [36762777](https://pubmed.ncbi.nlm.nih.gov/36762777/) | 0.65 |

**Path 3** · `Dostarlimab —inhibits→ PDCD1 —associated_with→ Colorectal_Cancer —associated_with→ Multiple_Myeloma —associated_with→ NSCLC`  ⚠ **routes through another disease — co-occurrence, not mechanism**

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Dostarlimab → PDCD1 | `inhibits` | MEASURED | ChEMBL:CHEMBL4298124 | — | 1.00 |
| PDCD1 → Colorectal_Cancer | `associated_with` | INFERRED | PMID:41655134; discovery-grounded; agent-adj | [41655134](https://pubmed.ncbi.nlm.nih.gov/41655134/) | 0.60 |
| Colorectal_Cancer → Multiple_Myeloma | `associated_with` | INFERRED | PMID:38967919; [RELATION-SCREENED] | [38967919](https://pubmed.ncbi.nlm.nih.gov/38967919/) | 0.65 |
| Multiple_Myeloma → NSCLC | `associated_with` | INFERRED | PMID:36762777; [RELATION-SCREENED] | [36762777](https://pubmed.ncbi.nlm.nih.gov/36762777/) | 0.65 |

**What this candidate does not have:** every terminal Protein->Disease hop is `associated_with`, a co-occurrence relation, not a mechanistic claim; no quantitative value on any edge (the column is NULL graph-wide)

**Your code (A/B/C/D/E):** `____`    **Why:** 

---

### P12  —  Mebendazole  ·  Melanoma

**Path 1** · `Mebendazole —inhibits→ BRAF —driver_of→ Melanoma`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Mebendazole → BRAF | `inhibits` | ESTABLISHED | literature (unverified); PMID:28157711; [REL | [28157711](https://pubmed.ncbi.nlm.nih.gov/28157711/) | 0.70 |
| BRAF → Melanoma | `driver_of` | ESTABLISHED | PMID:42126185; [LEXICAL-COOCCURRENCE] | [42126185](https://pubmed.ncbi.nlm.nih.gov/42126185/) | 0.95 |

**Path 2** · `Mebendazole —inhibits→ VEGFR2 —associated_with→ Melanoma`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Mebendazole → VEGFR2 | `inhibits` | ESTABLISHED | literature (unverified); PMID:22780961; [REL | [22780961](https://pubmed.ncbi.nlm.nih.gov/22780961/) | 0.82 |
| VEGFR2 → Melanoma | `associated_with` | INFERRED | cancer_proteins | — | 0.55 |

**Path 3** · `Mebendazole —activator→ TP53 —associated_with→ Melanoma`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Mebendazole → TP53 | `activator` | INFERRED | literature:tubulin_disruption_activates_p53 | — | 0.65 |
| TP53 → Melanoma | `associated_with` | INFERRED | cancer_proteins | — | 0.55 |

**What this candidate does not have:** no quantitative value on any edge (the column is NULL graph-wide)

**Your code (A/B/C/D/E):** `____`    **Why:** 

---

### P13  —  Dabrafenib  ·  Melanoma

**Path 1** · `Dabrafenib —inhibits→ BRAF —driver_of→ Melanoma`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Dabrafenib → BRAF | `inhibits` | ESTABLISHED | PMID:42143022; [RELATION-VERIFIED] | [42143022](https://pubmed.ncbi.nlm.nih.gov/42143022/) | 0.96 |
| BRAF → Melanoma | `driver_of` | ESTABLISHED | PMID:42126185; [LEXICAL-COOCCURRENCE] | [42126185](https://pubmed.ncbi.nlm.nih.gov/42126185/) | 0.95 |

**Path 2** · `Dabrafenib —synergizes_with→ Trametinib —inhibits→ MEK1 —driver_of→ Melanoma`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Dabrafenib → Trametinib | `synergizes_with` | ESTABLISHED | FDA:NDA202806_204114, approved_combination_B | [42169194](https://pubmed.ncbi.nlm.nih.gov/42169194/) | 0.97 |
| Trametinib → MEK1 | `inhibits` | ESTABLISHED | PMID:42152474; [RELATION-VERIFIED] | [42152474](https://pubmed.ncbi.nlm.nih.gov/42152474/) | 0.98 |
| MEK1 → Melanoma | `driver_of` | ESTABLISHED | PMID:22389471 | [22389471](https://pubmed.ncbi.nlm.nih.gov/22389471/) | 0.90 |

**Path 3** · `Dabrafenib —inhibits→ BRAF —phosphorylates→ MEK1 —driver_of→ Melanoma`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Dabrafenib → BRAF | `inhibits` | ESTABLISHED | PMID:42143022; [RELATION-VERIFIED] | [42143022](https://pubmed.ncbi.nlm.nih.gov/42143022/) | 0.96 |
| BRAF → MEK1 | `phosphorylates` | ESTABLISHED | KEGG:hsa04010, cancer_proteins.py | — | 0.99 |
| MEK1 → Melanoma | `driver_of` | ESTABLISHED | PMID:22389471 | [22389471](https://pubmed.ncbi.nlm.nih.gov/22389471/) | 0.90 |

**What this candidate does not have:** no quantitative value on any edge (the column is NULL graph-wide)

**Your code (A/B/C/D/E):** `____`    **Why:** 

---

### P14  —  Beperminogene Perplasmid  ·  NSCLC

**Path 1** · `Beperminogene Perplasmid —activates→ MET —associated_with→ NSCLC`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Beperminogene Perplasmid → MET | `activates` | MEASURED | ChEMBL:CHEMBL2108332 | — | 1.00 |
| MET → NSCLC | `associated_with` | ESTABLISHED | PMID:42187575; [RELATION-VERIFIED] | [42187575](https://pubmed.ncbi.nlm.nih.gov/42187575/) | 0.80 |

**Path 2** · `Beperminogene Perplasmid —activates→ MET —activates→ KRAS —driver_of→ NSCLC`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Beperminogene Perplasmid → MET | `activates` | MEASURED | ChEMBL:CHEMBL2108332 | — | 1.00 |
| MET → KRAS | `activates` | ESTABLISHED | KEGG:hsa04014, cancer_proteins.py | — | 0.89 |
| KRAS → NSCLC | `driver_of` | ESTABLISHED | PMID:42075590; [RELATION-VERIFIED] | [42075590](https://pubmed.ncbi.nlm.nih.gov/42075590/) | 0.88 |

**Path 3** · `Beperminogene Perplasmid —activates→ MET —activates→ PI3KCA —associated_with→ NSCLC`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Beperminogene Perplasmid → MET | `activates` | MEASURED | ChEMBL:CHEMBL2108332 | — | 1.00 |
| MET → PI3KCA | `activates` | ESTABLISHED | PMID:34802045 | [34802045](https://pubmed.ncbi.nlm.nih.gov/34802045/) | 0.91 |
| PI3KCA → NSCLC | `associated_with` | INFERRED | PPI; PMID:41221490; [RELATION-VERIFIED] | [41221490](https://pubmed.ncbi.nlm.nih.gov/41221490/) | 0.50 |

**What this candidate does not have:** no quantitative value on any edge (the column is NULL graph-wide)

**Your code (A/B/C/D/E):** `____`    **Why:** 

---

### P15  —  Lorlatinib  ·  NSCLC

**Path 1** · `Lorlatinib —inhibits→ ALK —driver_of→ NSCLC`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Lorlatinib → ALK | `inhibits` | ESTABLISHED | FDA:NDA210868, mechanism:3rd_gen_ALK_TKI; PM | [42170281](https://pubmed.ncbi.nlm.nih.gov/42170281/) | 0.99 |
| ALK → NSCLC | `driver_of` | ESTABLISHED | PMID:42187575; [LEXICAL-COOCCURRENCE] | [42187575](https://pubmed.ncbi.nlm.nih.gov/42187575/) | 0.92 |

**Path 2** · `Lorlatinib —inhibits→ ROS1 —driver_of→ NSCLC`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Lorlatinib → ROS1 | `inhibits` | ESTABLISHED | FDA:NDA210868, mechanism:ALK_ROS1_TKI; PMID: | [41704605](https://pubmed.ncbi.nlm.nih.gov/41704605/) | 0.95 |
| ROS1 → NSCLC | `driver_of` | ESTABLISHED | PMID:42075590; [RELATION-VERIFIED] | [42075590](https://pubmed.ncbi.nlm.nih.gov/42075590/) | 0.85 |

**Path 3** · `Lorlatinib —inhibits→ ALK —associated_with→ Breast_Cancer —associated_with→ Multiple_Myeloma —associated_with→ NSCLC`  ⚠ **routes through another disease — co-occurrence, not mechanism**

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Lorlatinib → ALK | `inhibits` | ESTABLISHED | FDA:NDA210868, mechanism:3rd_gen_ALK_TKI; PM | [42170281](https://pubmed.ncbi.nlm.nih.gov/42170281/) | 0.99 |
| ALK → Breast_Cancer | `associated_with` | INFERRED | PMID:32954856; [RELATION-SCREENED] | [32954856](https://pubmed.ncbi.nlm.nih.gov/32954856/) | 0.65 |
| Breast_Cancer → Multiple_Myeloma | `associated_with` | INFERRED | PMID:33127577; [RELATION-SCREENED] | [33127577](https://pubmed.ncbi.nlm.nih.gov/33127577/) | 0.65 |
| Multiple_Myeloma → NSCLC | `associated_with` | INFERRED | PMID:36762777; [RELATION-SCREENED] | [36762777](https://pubmed.ncbi.nlm.nih.gov/36762777/) | 0.65 |

**What this candidate does not have:** no quantitative value on any edge (the column is NULL graph-wide)

**Your code (A/B/C/D/E):** `____`    **Why:** 

---

### P16  —  Dacomitinib  ·  NSCLC

**Path 1** · `Dacomitinib —inhibits→ EGFR —driver_of→ NSCLC`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Dacomitinib → EGFR | `inhibits` | MEASURED | ChEMBL:CHEMBL2105719; PMID:42200352; [LEXICA | [42200352](https://pubmed.ncbi.nlm.nih.gov/42200352/) | 1.00 |
| EGFR → NSCLC | `driver_of` | ESTABLISHED | PMID:42182703; [LEXICAL-COOCCURRENCE] | [42182703](https://pubmed.ncbi.nlm.nih.gov/42182703/) | 0.95 |

**Path 2** · `Dacomitinib —inhibits→ ERBB2 —associated_with→ NSCLC`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Dacomitinib → ERBB2 | `inhibits` | MEASURED | ChEMBL:CHEMBL2105719; PMID:38724606; [LEXICA | [38724606](https://pubmed.ncbi.nlm.nih.gov/38724606/) | 1.00 |
| ERBB2 → NSCLC | `associated_with` | MEASURED | ABPP; PMID:41982617; [RELATION-VERIFIED] | [41982617](https://pubmed.ncbi.nlm.nih.gov/41982617/) | 0.80 |

**Path 3** · `Dacomitinib —inhibits→ EGFR —activates→ KRAS —driver_of→ NSCLC`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Dacomitinib → EGFR | `inhibits` | MEASURED | ChEMBL:CHEMBL2105719; PMID:42200352; [LEXICA | [42200352](https://pubmed.ncbi.nlm.nih.gov/42200352/) | 1.00 |
| EGFR → KRAS | `activates` | ESTABLISHED | KEGG:hsa04010, cancer_proteins.py | — | 0.95 |
| KRAS → NSCLC | `driver_of` | ESTABLISHED | PMID:42075590; [RELATION-VERIFIED] | [42075590](https://pubmed.ncbi.nlm.nih.gov/42075590/) | 0.88 |

**What this candidate does not have:** no quantitative value on any edge (the column is NULL graph-wide)

**Your code (A/B/C/D/E):** `____`    **Why:** 

---

### P17  —  Abemaciclib  ·  Melanoma

**Path 1** · `Abemaciclib —inhibits→ CDK4 —associated_with→ Melanoma`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Abemaciclib → CDK4 | `inhibits` | MEASURED | ChEMBL:CHEMBL3301610; PMID:42194689; [RELATI | [42194689](https://pubmed.ncbi.nlm.nih.gov/42194689/) | 1.00 |
| CDK4 → Melanoma | `associated_with` | INFERRED | cancer_proteins; PMID:42201696; [RELATION-VE | [42201696](https://pubmed.ncbi.nlm.nih.gov/42201696/) | 0.55 |

**Path 2** · `Abemaciclib —inhibits→ CDK6 —associated_with→ Melanoma`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Abemaciclib → CDK6 | `inhibits` | MEASURED | ChEMBL:CHEMBL3301610; PMID:41845059; [RELATI | [41845059](https://pubmed.ncbi.nlm.nih.gov/41845059/) | 1.00 |
| CDK6 → Melanoma | `associated_with` | INFERRED | cancer_proteins; PMID:39495991; [RELATION-VE | [39495991](https://pubmed.ncbi.nlm.nih.gov/39495991/) | 0.55 |

**Path 3** · `Abemaciclib —inhibits→ CDK4 —phosphorylates→ RB1 —associated_with→ Melanoma`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Abemaciclib → CDK4 | `inhibits` | MEASURED | ChEMBL:CHEMBL3301610; PMID:42194689; [RELATI | [42194689](https://pubmed.ncbi.nlm.nih.gov/42194689/) | 1.00 |
| CDK4 → RB1 | `phosphorylates` | ESTABLISHED | KEGG:hsa04110, cancer_proteins.py; PMID:4119 | [41196681](https://pubmed.ncbi.nlm.nih.gov/41196681/) | 0.97 |
| RB1 → Melanoma | `associated_with` | INFERRED | cancer_proteins; PMID:41936939; [LEXICAL-COO | [41936939](https://pubmed.ncbi.nlm.nih.gov/41936939/) | 0.55 |

**What this candidate does not have:** every terminal Protein->Disease hop is `associated_with`, a co-occurrence relation, not a mechanistic claim; no quantitative value on any edge (the column is NULL graph-wide)

**Your code (A/B/C/D/E):** `____`    **Why:** 

---

### P18  —  Sotorasib  ·  Melanoma

**Path 1** · `Sotorasib —indirect_inhibitor→ MAP2K1 —driver_of→ Melanoma`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Sotorasib → MAP2K1 | `indirect_inhibitor` | ESTABLISHED | literature (unverified) | — | 0.80 |
| MAP2K1 → Melanoma | `driver_of` | ESTABLISHED | PMID:22389471; PMID:36901951 | [22389471](https://pubmed.ncbi.nlm.nih.gov/22389471/), [36901951](https://pubmed.ncbi.nlm.nih.gov/36901951/) | 0.85 |

**Path 2** · `Sotorasib —inhibits→ KRAS —activates→ BRAF —driver_of→ Melanoma`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Sotorasib → KRAS | `inhibits` | ESTABLISHED | FDA:NDA214665, mechanism:KRAS_G12C_inhibitor | [42144204](https://pubmed.ncbi.nlm.nih.gov/42144204/) | 0.97 |
| KRAS → BRAF | `activates` | ESTABLISHED | KEGG:hsa04010, cancer_proteins.py; PMID:4186 | [41862948](https://pubmed.ncbi.nlm.nih.gov/41862948/) | 0.97 |
| BRAF → Melanoma | `driver_of` | ESTABLISHED | PMID:42126185; [LEXICAL-COOCCURRENCE] | [42126185](https://pubmed.ncbi.nlm.nih.gov/42126185/) | 0.95 |

**Path 3** · `Sotorasib —inhibits→ KRAS —activates→ RAF1 —associated_with→ Melanoma`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Sotorasib → KRAS | `inhibits` | ESTABLISHED | FDA:NDA214665, mechanism:KRAS_G12C_inhibitor | [42144204](https://pubmed.ncbi.nlm.nih.gov/42144204/) | 0.97 |
| KRAS → RAF1 | `activates` | ESTABLISHED | KEGG:hsa04010, cancer_proteins.py; PMID:3780 | [37805663](https://pubmed.ncbi.nlm.nih.gov/37805663/) | 0.96 |
| RAF1 → Melanoma | `associated_with` | INFERRED | cancer_proteins; PMID:39574163; [RELATION-VE | [39574163](https://pubmed.ncbi.nlm.nih.gov/39574163/) | 0.55 |

**What this candidate does not have:** no quantitative value on any edge (the column is NULL graph-wide)

**Your code (A/B/C/D/E):** `____`    **Why:** 

---

### P19  —  Cemiplimab  ·  Melanoma

**Path 1** · `Cemiplimab —inhibits→ PDCD1 —associated_with→ Melanoma`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Cemiplimab → PDCD1 | `inhibits` | MEASURED | ChEMBL:CHEMBL4297723 | — | 1.00 |
| PDCD1 → Melanoma | `associated_with` | ESTABLISHED | PMID:40556672; [LEXICAL-COOCCURRENCE] | [40556672](https://pubmed.ncbi.nlm.nih.gov/40556672/) | 0.85 |

**Path 2** · `Cemiplimab —inhibits→ PDCD1 —associated_with→ RCC —associated_with→ Melanoma`  ⚠ **routes through another disease — co-occurrence, not mechanism**

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Cemiplimab → PDCD1 | `inhibits` | MEASURED | ChEMBL:CHEMBL4297723 | — | 1.00 |
| PDCD1 → RCC | `associated_with` | ESTABLISHED | PMID:26406148 | [26406148](https://pubmed.ncbi.nlm.nih.gov/26406148/) | 0.80 |
| RCC → Melanoma | `associated_with` | INFERRED | PMID:39842618; [RELATION-SCREENED] | [39842618](https://pubmed.ncbi.nlm.nih.gov/39842618/) | 0.65 |

**Path 3** · `Cemiplimab —inhibits→ PDCD1 —associated_with→ Ovarian_Cancer —associated_with→ Melanoma`  ⚠ **routes through another disease — co-occurrence, not mechanism**

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Cemiplimab → PDCD1 | `inhibits` | MEASURED | ChEMBL:CHEMBL4297723 | — | 1.00 |
| PDCD1 → Ovarian_Cancer | `associated_with` | INFERRED | PMID:28730785; discovery-grounded; agent-adj | [28730785](https://pubmed.ncbi.nlm.nih.gov/28730785/) | 0.60 |
| Ovarian_Cancer → Melanoma | `associated_with` | INFERRED | PMID:20301425; [RELATION-SCREENED] | [20301425](https://pubmed.ncbi.nlm.nih.gov/20301425/) | 0.65 |

**What this candidate does not have:** every terminal Protein->Disease hop is `associated_with`, a co-occurrence relation, not a mechanistic claim; no quantitative value on any edge (the column is NULL graph-wide)

**Your code (A/B/C/D/E):** `____`    **Why:** 

---

### P20  —  Etoricoxib  ·  Melanoma

**Path 1** · `Etoricoxib —inhibits→ PTGS2 —associated_with→ Melanoma`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Etoricoxib → PTGS2 | `inhibits` | MEASURED | ChEMBL:CHEMBL416146; PMID:40257651; [RELATIO | [40257651](https://pubmed.ncbi.nlm.nih.gov/40257651/) | 1.00 |
| PTGS2 → Melanoma | `associated_with` | INFERRED | PMID:38934060; discovery-grounded; agent-adj | [38934060](https://pubmed.ncbi.nlm.nih.gov/38934060/) | 0.60 |

**Path 2** · `Etoricoxib —inhibits→ PTGS2 —associated_with→ HCC —associated_with→ RCC —associated_with→ Melanoma`  ⚠ **routes through another disease — co-occurrence, not mechanism**

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Etoricoxib → PTGS2 | `inhibits` | MEASURED | ChEMBL:CHEMBL416146; PMID:40257651; [RELATIO | [40257651](https://pubmed.ncbi.nlm.nih.gov/40257651/) | 1.00 |
| PTGS2 → HCC | `associated_with` | INFERRED | PMID:31679460; [RELATION-SCREENED] | [31679460](https://pubmed.ncbi.nlm.nih.gov/31679460/) | 0.65 |
| HCC → RCC | `associated_with` | INFERRED | PMID:37469132; [RELATION-SCREENED] | [37469132](https://pubmed.ncbi.nlm.nih.gov/37469132/) | 0.65 |
| RCC → Melanoma | `associated_with` | INFERRED | PMID:39842618; [RELATION-SCREENED] | [39842618](https://pubmed.ncbi.nlm.nih.gov/39842618/) | 0.65 |

**Path 3** · `Etoricoxib —inhibits→ PTGS2 —associated_with→ CML —associated_with→ Ovarian_Cancer —associated_with→ Melanoma`  ⚠ **routes through another disease — co-occurrence, not mechanism**

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Etoricoxib → PTGS2 | `inhibits` | MEASURED | ChEMBL:CHEMBL416146; PMID:40257651; [RELATIO | [40257651](https://pubmed.ncbi.nlm.nih.gov/40257651/) | 1.00 |
| PTGS2 → CML | `associated_with` | INFERRED | PMID:39450252; discovery-grounded; agent-adj | [39450252](https://pubmed.ncbi.nlm.nih.gov/39450252/) | 0.60 |
| CML → Ovarian_Cancer | `associated_with` | INFERRED | PMID:32169887; [RELATION-SCREENED] | [32169887](https://pubmed.ncbi.nlm.nih.gov/32169887/) | 0.65 |
| Ovarian_Cancer → Melanoma | `associated_with` | INFERRED | PMID:20301425; [RELATION-SCREENED] | [20301425](https://pubmed.ncbi.nlm.nih.gov/20301425/) | 0.65 |

**What this candidate does not have:** every terminal Protein->Disease hop is `associated_with`, a co-occurrence relation, not a mechanistic claim; no quantitative value on any edge (the column is NULL graph-wide)

**Your code (A/B/C/D/E):** `____`    **Why:** 

---

### P21  —  Doxycycline  ·  Melanoma

**Path 1** · `Doxycycline —inhibits→ MMP8 —associated_with→ Melanoma`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Doxycycline → MMP8 | `inhibits` | MEASURED | ChEMBL:CHEMBL1200699 | — | 1.00 |
| MMP8 → Melanoma | `associated_with` | INFERRED | PMID:21642878; discovery-grounded; agent-adj | [21642878](https://pubmed.ncbi.nlm.nih.gov/21642878/) | 0.60 |

**Path 2** · `Doxycycline —inhibits→ MMP13 —associated_with→ Melanoma`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Doxycycline → MMP13 | `inhibits` | MEASURED | ChEMBL:CHEMBL1200699 | — | 1.00 |
| MMP13 → Melanoma | `associated_with` | INFERRED | PMID:38527983; discovery-grounded; agent-adj | [38527983](https://pubmed.ncbi.nlm.nih.gov/38527983/) | 0.60 |

**Path 3** · `Doxycycline —inhibits→ MMP2 —associated_with→ Melanoma`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Doxycycline → MMP2 | `inhibits` | ESTABLISHED | literature (unverified) | — | 0.80 |
| MMP2 → Melanoma | `associated_with` | INFERRED | PMID:41793972; [LEXICAL-COOCCURRENCE] | [41793972](https://pubmed.ncbi.nlm.nih.gov/41793972/) | 0.65 |

**What this candidate does not have:** every terminal Protein->Disease hop is `associated_with`, a co-occurrence relation, not a mechanistic claim; no quantitative value on any edge (the column is NULL graph-wide)

**Your code (A/B/C/D/E):** `____`    **Why:** 

---

### P22  —  Dacomitinib Anhydrous  ·  NSCLC

**Path 1** · `Dacomitinib Anhydrous —inhibits→ EGFR —driver_of→ NSCLC`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Dacomitinib Anhydrous → EGFR | `inhibits` | MEASURED | ChEMBL:CHEMBL2110732 | — | 1.00 |
| EGFR → NSCLC | `driver_of` | ESTABLISHED | PMID:42182703; [LEXICAL-COOCCURRENCE] | [42182703](https://pubmed.ncbi.nlm.nih.gov/42182703/) | 0.95 |

**Path 2** · `Dacomitinib Anhydrous —inhibits→ ERBB2 —associated_with→ NSCLC`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Dacomitinib Anhydrous → ERBB2 | `inhibits` | MEASURED | ChEMBL:CHEMBL2110732 | — | 1.00 |
| ERBB2 → NSCLC | `associated_with` | MEASURED | ABPP; PMID:41982617; [RELATION-VERIFIED] | [41982617](https://pubmed.ncbi.nlm.nih.gov/41982617/) | 0.80 |

**Path 3** · `Dacomitinib Anhydrous —inhibits→ EGFR —activates→ KRAS —driver_of→ NSCLC`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Dacomitinib Anhydrous → EGFR | `inhibits` | MEASURED | ChEMBL:CHEMBL2110732 | — | 1.00 |
| EGFR → KRAS | `activates` | ESTABLISHED | KEGG:hsa04010, cancer_proteins.py | — | 0.95 |
| KRAS → NSCLC | `driver_of` | ESTABLISHED | PMID:42075590; [RELATION-VERIFIED] | [42075590](https://pubmed.ncbi.nlm.nih.gov/42075590/) | 0.88 |

**What this candidate does not have:** no quantitative value on any edge (the column is NULL graph-wide)

**Your code (A/B/C/D/E):** `____`    **Why:** 

---

### P23  —  Encorafenib  ·  Melanoma

**Path 1** · `Encorafenib —inhibits→ BRAF —driver_of→ Melanoma`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Encorafenib → BRAF | `inhibits` | ESTABLISHED | FDA:NDA210496, mechanism:BRAF_inhibitor; PMI | [41920914](https://pubmed.ncbi.nlm.nih.gov/41920914/) | 0.97 |
| BRAF → Melanoma | `driver_of` | ESTABLISHED | PMID:42126185; [LEXICAL-COOCCURRENCE] | [42126185](https://pubmed.ncbi.nlm.nih.gov/42126185/) | 0.95 |

**Path 2** · `Encorafenib —inhibits→ BRAF —phosphorylates→ MEK1 —driver_of→ Melanoma`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Encorafenib → BRAF | `inhibits` | ESTABLISHED | FDA:NDA210496, mechanism:BRAF_inhibitor; PMI | [41920914](https://pubmed.ncbi.nlm.nih.gov/41920914/) | 0.97 |
| BRAF → MEK1 | `phosphorylates` | ESTABLISHED | KEGG:hsa04010, cancer_proteins.py | — | 0.99 |
| MEK1 → Melanoma | `driver_of` | ESTABLISHED | PMID:22389471 | [22389471](https://pubmed.ncbi.nlm.nih.gov/22389471/) | 0.90 |

**Path 3** · `Encorafenib —inhibits→ BRAF —associated_with→ RCC —associated_with→ Melanoma`  ⚠ **routes through another disease — co-occurrence, not mechanism**

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Encorafenib → BRAF | `inhibits` | ESTABLISHED | FDA:NDA210496, mechanism:BRAF_inhibitor; PMI | [41920914](https://pubmed.ncbi.nlm.nih.gov/41920914/) | 0.97 |
| BRAF → RCC | `associated_with` | MEASURED | ABPP; PMID:41562159; [RELATION-VERIFIED] | [41562159](https://pubmed.ncbi.nlm.nih.gov/41562159/) | 0.80 |
| RCC → Melanoma | `associated_with` | INFERRED | PMID:39842618; [RELATION-SCREENED] | [39842618](https://pubmed.ncbi.nlm.nih.gov/39842618/) | 0.65 |

**What this candidate does not have:** no quantitative value on any edge (the column is NULL graph-wide)

**Your code (A/B/C/D/E):** `____`    **Why:** 

---

### P24  —  Crizotinib  ·  NSCLC

**Path 1** · `Crizotinib —inhibits→ ALK —driver_of→ NSCLC`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Crizotinib → ALK | `inhibits` | ESTABLISHED | FDA:NDA202570, mechanism:ALK_TKI; PMID:42136 | [42136678](https://pubmed.ncbi.nlm.nih.gov/42136678/) | 0.96 |
| ALK → NSCLC | `driver_of` | ESTABLISHED | PMID:42187575; [LEXICAL-COOCCURRENCE] | [42187575](https://pubmed.ncbi.nlm.nih.gov/42187575/) | 0.92 |

**Path 2** · `Crizotinib —inhibits→ ROS1 —driver_of→ NSCLC`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Crizotinib → ROS1 | `inhibits` | ESTABLISHED | FDA:NDA202570, mechanism:ALK_MET_ROS1_inhibi | [41754770](https://pubmed.ncbi.nlm.nih.gov/41754770/) | 0.91 |
| ROS1 → NSCLC | `driver_of` | ESTABLISHED | PMID:42075590; [RELATION-VERIFIED] | [42075590](https://pubmed.ncbi.nlm.nih.gov/42075590/) | 0.85 |

**Path 3** · `Crizotinib —inhibits→ MET —associated_with→ NSCLC`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Crizotinib → MET | `inhibits` | ESTABLISHED | FDA:NDA202570, mechanism:ALK_MET_ROS1_inhibi | [42015375](https://pubmed.ncbi.nlm.nih.gov/42015375/) | 0.93 |
| MET → NSCLC | `associated_with` | ESTABLISHED | PMID:42187575; [RELATION-VERIFIED] | [42187575](https://pubmed.ncbi.nlm.nih.gov/42187575/) | 0.80 |

**What this candidate does not have:** no quantitative value on any edge (the column is NULL graph-wide)

**Your code (A/B/C/D/E):** `____`    **Why:** 

---

### P25  —  Ensartinib  ·  NSCLC

**Path 1** · `Ensartinib —inhibits→ ALK —driver_of→ NSCLC`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Ensartinib → ALK | `inhibits` | MEASURED | ChEMBL:CHEMBL4113131; PMID:42137140; [RELATI | [42137140](https://pubmed.ncbi.nlm.nih.gov/42137140/) | 1.00 |
| ALK → NSCLC | `driver_of` | ESTABLISHED | PMID:42187575; [LEXICAL-COOCCURRENCE] | [42187575](https://pubmed.ncbi.nlm.nih.gov/42187575/) | 0.92 |

**Path 2** · `Ensartinib —inhibits→ ALK —associated_with→ Breast_Cancer —associated_with→ Multiple_Myeloma —associated_with→ NSCLC`  ⚠ **routes through another disease — co-occurrence, not mechanism**

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Ensartinib → ALK | `inhibits` | MEASURED | ChEMBL:CHEMBL4113131; PMID:42137140; [RELATI | [42137140](https://pubmed.ncbi.nlm.nih.gov/42137140/) | 1.00 |
| ALK → Breast_Cancer | `associated_with` | INFERRED | PMID:32954856; [RELATION-SCREENED] | [32954856](https://pubmed.ncbi.nlm.nih.gov/32954856/) | 0.65 |
| Breast_Cancer → Multiple_Myeloma | `associated_with` | INFERRED | PMID:33127577; [RELATION-SCREENED] | [33127577](https://pubmed.ncbi.nlm.nih.gov/33127577/) | 0.65 |
| Multiple_Myeloma → NSCLC | `associated_with` | INFERRED | PMID:36762777; [RELATION-SCREENED] | [36762777](https://pubmed.ncbi.nlm.nih.gov/36762777/) | 0.65 |

**Path 3** · `Ensartinib —inhibits→ ALK —associated_with→ Colorectal_Cancer —associated_with→ Multiple_Myeloma —associated_with→ NSCLC`  ⚠ **routes through another disease — co-occurrence, not mechanism**

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Ensartinib → ALK | `inhibits` | MEASURED | ChEMBL:CHEMBL4113131; PMID:42137140; [RELATI | [42137140](https://pubmed.ncbi.nlm.nih.gov/42137140/) | 1.00 |
| ALK → Colorectal_Cancer | `associated_with` | INFERRED | PMID:40493183; discovery-grounded; agent-adj | [40493183](https://pubmed.ncbi.nlm.nih.gov/40493183/) | 0.60 |
| Colorectal_Cancer → Multiple_Myeloma | `associated_with` | INFERRED | PMID:38967919; [RELATION-SCREENED] | [38967919](https://pubmed.ncbi.nlm.nih.gov/38967919/) | 0.65 |
| Multiple_Myeloma → NSCLC | `associated_with` | INFERRED | PMID:36762777; [RELATION-SCREENED] | [36762777](https://pubmed.ncbi.nlm.nih.gov/36762777/) | 0.65 |

**What this candidate does not have:** no quantitative value on any edge (the column is NULL graph-wide)

**Your code (A/B/C/D/E):** `____`    **Why:** 

---

### P26  —  Amivantamab  ·  NSCLC

**Path 1** · `Amivantamab —inhibits→ EGFR —driver_of→ NSCLC`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Amivantamab → EGFR | `inhibits` | MEASURED | ChEMBL:CHEMBL4297774; PMID:42048802; [RELATI | [42048802](https://pubmed.ncbi.nlm.nih.gov/42048802/) | 1.00 |
| EGFR → NSCLC | `driver_of` | ESTABLISHED | PMID:42182703; [LEXICAL-COOCCURRENCE] | [42182703](https://pubmed.ncbi.nlm.nih.gov/42182703/) | 0.95 |

**Path 2** · `Amivantamab —inhibits→ MET —associated_with→ NSCLC`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Amivantamab → MET | `inhibits` | MEASURED | ChEMBL:CHEMBL4297774; PMID:42048802; [RELATI | [42048802](https://pubmed.ncbi.nlm.nih.gov/42048802/) | 1.00 |
| MET → NSCLC | `associated_with` | ESTABLISHED | PMID:42187575; [RELATION-VERIFIED] | [42187575](https://pubmed.ncbi.nlm.nih.gov/42187575/) | 0.80 |

**Path 3** · `Amivantamab —inhibits→ EGFR —activates→ KRAS —driver_of→ NSCLC`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Amivantamab → EGFR | `inhibits` | MEASURED | ChEMBL:CHEMBL4297774; PMID:42048802; [RELATI | [42048802](https://pubmed.ncbi.nlm.nih.gov/42048802/) | 1.00 |
| EGFR → KRAS | `activates` | ESTABLISHED | KEGG:hsa04010, cancer_proteins.py | — | 0.95 |
| KRAS → NSCLC | `driver_of` | ESTABLISHED | PMID:42075590; [RELATION-VERIFIED] | [42075590](https://pubmed.ncbi.nlm.nih.gov/42075590/) | 0.88 |

**What this candidate does not have:** no quantitative value on any edge (the column is NULL graph-wide)

**Your code (A/B/C/D/E):** `____`    **Why:** 

---

### P27  —  Carprofen  ·  Melanoma

**Path 1** · `Carprofen —inhibits→ PTGS2 —associated_with→ Melanoma`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Carprofen → PTGS2 | `inhibits` | MEASURED | ChEMBL:CHEMBL1316 | — | 1.00 |
| PTGS2 → Melanoma | `associated_with` | INFERRED | PMID:38934060; discovery-grounded; agent-adj | [38934060](https://pubmed.ncbi.nlm.nih.gov/38934060/) | 0.60 |

**Path 2** · `Carprofen —inhibits→ PTGS2 —associated_with→ HCC —associated_with→ RCC —associated_with→ Melanoma`  ⚠ **routes through another disease — co-occurrence, not mechanism**

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Carprofen → PTGS2 | `inhibits` | MEASURED | ChEMBL:CHEMBL1316 | — | 1.00 |
| PTGS2 → HCC | `associated_with` | INFERRED | PMID:31679460; [RELATION-SCREENED] | [31679460](https://pubmed.ncbi.nlm.nih.gov/31679460/) | 0.65 |
| HCC → RCC | `associated_with` | INFERRED | PMID:37469132; [RELATION-SCREENED] | [37469132](https://pubmed.ncbi.nlm.nih.gov/37469132/) | 0.65 |
| RCC → Melanoma | `associated_with` | INFERRED | PMID:39842618; [RELATION-SCREENED] | [39842618](https://pubmed.ncbi.nlm.nih.gov/39842618/) | 0.65 |

**Path 3** · `Carprofen —inhibits→ PTGS2 —associated_with→ CML —associated_with→ Ovarian_Cancer —associated_with→ Melanoma`  ⚠ **routes through another disease — co-occurrence, not mechanism**

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Carprofen → PTGS2 | `inhibits` | MEASURED | ChEMBL:CHEMBL1316 | — | 1.00 |
| PTGS2 → CML | `associated_with` | INFERRED | PMID:39450252; discovery-grounded; agent-adj | [39450252](https://pubmed.ncbi.nlm.nih.gov/39450252/) | 0.60 |
| CML → Ovarian_Cancer | `associated_with` | INFERRED | PMID:32169887; [RELATION-SCREENED] | [32169887](https://pubmed.ncbi.nlm.nih.gov/32169887/) | 0.65 |
| Ovarian_Cancer → Melanoma | `associated_with` | INFERRED | PMID:20301425; [RELATION-SCREENED] | [20301425](https://pubmed.ncbi.nlm.nih.gov/20301425/) | 0.65 |

**What this candidate does not have:** every terminal Protein->Disease hop is `associated_with`, a co-occurrence relation, not a mechanistic claim; no quantitative value on any edge (the column is NULL graph-wide)

**Your code (A/B/C/D/E):** `____`    **Why:** 

---

### P28  —  Pralsetinib  ·  Melanoma

**Path 1** · `Pralsetinib —inhibits→ RET —associated_with→ Melanoma`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Pralsetinib → RET | `inhibits` | ESTABLISHED | FDA:NDA213721, mechanism:RET_TKI; PMID:42107 | [42107510](https://pubmed.ncbi.nlm.nih.gov/42107510/) | 0.99 |
| RET → Melanoma | `associated_with` | INFERRED | PMID:40555562; discovery-grounded; agent-adj | [40555562](https://pubmed.ncbi.nlm.nih.gov/40555562/) | 0.60 |

**Path 2** · `Pralsetinib —inhibits→ RET —associated_with→ Breast_Cancer —associated_with→ Melanoma`  ⚠ **routes through another disease — co-occurrence, not mechanism**

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Pralsetinib → RET | `inhibits` | ESTABLISHED | FDA:NDA213721, mechanism:RET_TKI; PMID:42107 | [42107510](https://pubmed.ncbi.nlm.nih.gov/42107510/) | 0.99 |
| RET → Breast_Cancer | `associated_with` | INFERRED | PMID:32080788; discovery-grounded; agent-adj | [32080788](https://pubmed.ncbi.nlm.nih.gov/32080788/) | 0.60 |
| Breast_Cancer → Melanoma | `associated_with` | INFERRED | PMID:30497674; [RELATION-SCREENED] | [30497674](https://pubmed.ncbi.nlm.nih.gov/30497674/) | 0.65 |

**Path 3** · `Pralsetinib —inhibits→ RET —associated_with→ HCC —associated_with→ RCC —associated_with→ Melanoma`  ⚠ **routes through another disease — co-occurrence, not mechanism**

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Pralsetinib → RET | `inhibits` | ESTABLISHED | FDA:NDA213721, mechanism:RET_TKI; PMID:42107 | [42107510](https://pubmed.ncbi.nlm.nih.gov/42107510/) | 0.99 |
| RET → HCC | `associated_with` | MEASURED | ABPP; PMID:41514495; [RELATION-VERIFIED] | [41514495](https://pubmed.ncbi.nlm.nih.gov/41514495/) | 0.80 |
| HCC → RCC | `associated_with` | INFERRED | PMID:37469132; [RELATION-SCREENED] | [37469132](https://pubmed.ncbi.nlm.nih.gov/37469132/) | 0.65 |
| RCC → Melanoma | `associated_with` | INFERRED | PMID:39842618; [RELATION-SCREENED] | [39842618](https://pubmed.ncbi.nlm.nih.gov/39842618/) | 0.65 |

**What this candidate does not have:** every terminal Protein->Disease hop is `associated_with`, a co-occurrence relation, not a mechanistic claim; no quantitative value on any edge (the column is NULL graph-wide)

**Your code (A/B/C/D/E):** `____`    **Why:** 

---

### P29  —  Cosibelimab  ·  NSCLC

**Path 1** · `Cosibelimab —inhibits→ CD274 —associated_with→ NSCLC`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Cosibelimab → CD274 | `inhibits` | MEASURED | ChEMBL:CHEMBL4297729 | — | 1.00 |
| CD274 → NSCLC | `associated_with` | ESTABLISHED | PMID:41699717; [RELATION-VERIFIED] | [41699717](https://pubmed.ncbi.nlm.nih.gov/41699717/) | 0.85 |

**Path 2** · `Cosibelimab —inhibits→ CD274 —inhibits→ PDCD1 —associated_with→ NSCLC`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Cosibelimab → CD274 | `inhibits` | MEASURED | ChEMBL:CHEMBL4297729 | — | 1.00 |
| CD274 → PDCD1 | `inhibits` | ESTABLISHED | PMID:41655134; [RELATION-VERIFIED] | [41655134](https://pubmed.ncbi.nlm.nih.gov/41655134/) | 0.95 |
| PDCD1 → NSCLC | `associated_with` | ESTABLISHED | PMID:40509568; [LEXICAL-COOCCURRENCE] | [40509568](https://pubmed.ncbi.nlm.nih.gov/40509568/) | 0.85 |

**Path 3** · `Cosibelimab —inhibits→ CD274 —associated_with→ Pancreatic_Cancer —associated_with→ Multiple_Myeloma —associated_with→ NSCLC`  ⚠ **routes through another disease — co-occurrence, not mechanism**

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Cosibelimab → CD274 | `inhibits` | MEASURED | ChEMBL:CHEMBL4297729 | — | 1.00 |
| CD274 → Pancreatic_Cancer | `associated_with` | INFERRED | PMID:38174993; [RELATION-SCREENED] | [38174993](https://pubmed.ncbi.nlm.nih.gov/38174993/) | 0.65 |
| Pancreatic_Cancer → Multiple_Myeloma | `associated_with` | INFERRED | PMID:38967919; [RELATION-SCREENED] | [38967919](https://pubmed.ncbi.nlm.nih.gov/38967919/) | 0.65 |
| Multiple_Myeloma → NSCLC | `associated_with` | INFERRED | PMID:36762777; [RELATION-SCREENED] | [36762777](https://pubmed.ncbi.nlm.nih.gov/36762777/) | 0.65 |

**What this candidate does not have:** every terminal Protein->Disease hop is `associated_with`, a co-occurrence relation, not a mechanistic claim; no quantitative value on any edge (the column is NULL graph-wide)

**Your code (A/B/C/D/E):** `____`    **Why:** 

---

### P30  —  Selpercatinib  ·  Melanoma

**Path 1** · `Selpercatinib —inhibits→ RET —associated_with→ Melanoma`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Selpercatinib → RET | `inhibits` | ESTABLISHED | FDA:NDA213246, mechanism:RET_TKI; PMID:42199 | [42199509](https://pubmed.ncbi.nlm.nih.gov/42199509/) | 0.99 |
| RET → Melanoma | `associated_with` | INFERRED | PMID:40555562; discovery-grounded; agent-adj | [40555562](https://pubmed.ncbi.nlm.nih.gov/40555562/) | 0.60 |

**Path 2** · `Selpercatinib —inhibits→ RET —associated_with→ Breast_Cancer —associated_with→ Melanoma`  ⚠ **routes through another disease — co-occurrence, not mechanism**

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Selpercatinib → RET | `inhibits` | ESTABLISHED | FDA:NDA213246, mechanism:RET_TKI; PMID:42199 | [42199509](https://pubmed.ncbi.nlm.nih.gov/42199509/) | 0.99 |
| RET → Breast_Cancer | `associated_with` | INFERRED | PMID:32080788; discovery-grounded; agent-adj | [32080788](https://pubmed.ncbi.nlm.nih.gov/32080788/) | 0.60 |
| Breast_Cancer → Melanoma | `associated_with` | INFERRED | PMID:30497674; [RELATION-SCREENED] | [30497674](https://pubmed.ncbi.nlm.nih.gov/30497674/) | 0.65 |

**Path 3** · `Selpercatinib —inhibits→ RET —associated_with→ HCC —associated_with→ RCC —associated_with→ Melanoma`  ⚠ **routes through another disease — co-occurrence, not mechanism**

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Selpercatinib → RET | `inhibits` | ESTABLISHED | FDA:NDA213246, mechanism:RET_TKI; PMID:42199 | [42199509](https://pubmed.ncbi.nlm.nih.gov/42199509/) | 0.99 |
| RET → HCC | `associated_with` | MEASURED | ABPP; PMID:41514495; [RELATION-VERIFIED] | [41514495](https://pubmed.ncbi.nlm.nih.gov/41514495/) | 0.80 |
| HCC → RCC | `associated_with` | INFERRED | PMID:37469132; [RELATION-SCREENED] | [37469132](https://pubmed.ncbi.nlm.nih.gov/37469132/) | 0.65 |
| RCC → Melanoma | `associated_with` | INFERRED | PMID:39842618; [RELATION-SCREENED] | [39842618](https://pubmed.ncbi.nlm.nih.gov/39842618/) | 0.65 |

**What this candidate does not have:** every terminal Protein->Disease hop is `associated_with`, a co-occurrence relation, not a mechanistic claim; no quantitative value on any edge (the column is NULL graph-wide)

**Your code (A/B/C/D/E):** `____`    **Why:** 

---

### P31  —  Cetuximab  ·  NSCLC

**Path 1** · `Cetuximab —inhibits→ EGFR —driver_of→ NSCLC`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Cetuximab → EGFR | `inhibits` | ESTABLISHED | PMID:15269313 | [15269313](https://pubmed.ncbi.nlm.nih.gov/15269313/) | 0.95 |
| EGFR → NSCLC | `driver_of` | ESTABLISHED | PMID:42182703; [LEXICAL-COOCCURRENCE] | [42182703](https://pubmed.ncbi.nlm.nih.gov/42182703/) | 0.95 |

**Path 2** · `Cetuximab —inhibits→ EGFR —activates→ KRAS —driver_of→ NSCLC`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Cetuximab → EGFR | `inhibits` | ESTABLISHED | PMID:15269313 | [15269313](https://pubmed.ncbi.nlm.nih.gov/15269313/) | 0.95 |
| EGFR → KRAS | `activates` | ESTABLISHED | KEGG:hsa04010, cancer_proteins.py | — | 0.95 |
| KRAS → NSCLC | `driver_of` | ESTABLISHED | PMID:42075590; [RELATION-VERIFIED] | [42075590](https://pubmed.ncbi.nlm.nih.gov/42075590/) | 0.88 |

**Path 3** · `Cetuximab —inhibits→ EGFR —activates→ STAT3 —associated_with→ NSCLC`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Cetuximab → EGFR | `inhibits` | ESTABLISHED | PMID:15269313 | [15269313](https://pubmed.ncbi.nlm.nih.gov/15269313/) | 0.95 |
| EGFR → STAT3 | `activates` | ESTABLISHED | KEGG:hsa04630, cancer_proteins.py; PMID:4217 | [42177207](https://pubmed.ncbi.nlm.nih.gov/42177207/) | 0.88 |
| STAT3 → NSCLC | `associated_with` | INFERRED | cancer_proteins | — | 0.55 |

**What this candidate does not have:** no quantitative value on any edge (the column is NULL graph-wide)

**Your code (A/B/C/D/E):** `____`    **Why:** 

---

### P32  —  Avelumab  ·  NSCLC

**Path 1** · `Avelumab —targets→ CD274 —associated_with→ NSCLC`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Avelumab → CD274 | `targets` | MEASURED | ChEMBL:CHEMBL3833373 | — | 1.00 |
| CD274 → NSCLC | `associated_with` | ESTABLISHED | PMID:41699717; [RELATION-VERIFIED] | [41699717](https://pubmed.ncbi.nlm.nih.gov/41699717/) | 0.85 |

**Path 2** · `Avelumab —targets→ CD274 —inhibits→ PDCD1 —associated_with→ NSCLC`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Avelumab → CD274 | `targets` | MEASURED | ChEMBL:CHEMBL3833373 | — | 1.00 |
| CD274 → PDCD1 | `inhibits` | ESTABLISHED | PMID:41655134; [RELATION-VERIFIED] | [41655134](https://pubmed.ncbi.nlm.nih.gov/41655134/) | 0.95 |
| PDCD1 → NSCLC | `associated_with` | ESTABLISHED | PMID:40509568; [LEXICAL-COOCCURRENCE] | [40509568](https://pubmed.ncbi.nlm.nih.gov/40509568/) | 0.85 |

**Path 3** · `Avelumab —targets→ CD274 —associated_with→ Pancreatic_Cancer —associated_with→ Multiple_Myeloma —associated_with→ NSCLC`  ⚠ **routes through another disease — co-occurrence, not mechanism**

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Avelumab → CD274 | `targets` | MEASURED | ChEMBL:CHEMBL3833373 | — | 1.00 |
| CD274 → Pancreatic_Cancer | `associated_with` | INFERRED | PMID:38174993; [RELATION-SCREENED] | [38174993](https://pubmed.ncbi.nlm.nih.gov/38174993/) | 0.65 |
| Pancreatic_Cancer → Multiple_Myeloma | `associated_with` | INFERRED | PMID:38967919; [RELATION-SCREENED] | [38967919](https://pubmed.ncbi.nlm.nih.gov/38967919/) | 0.65 |
| Multiple_Myeloma → NSCLC | `associated_with` | INFERRED | PMID:36762777; [RELATION-SCREENED] | [36762777](https://pubmed.ncbi.nlm.nih.gov/36762777/) | 0.65 |

**What this candidate does not have:** every terminal Protein->Disease hop is `associated_with`, a co-occurrence relation, not a mechanistic claim; no quantitative value on any edge (the column is NULL graph-wide)

**Your code (A/B/C/D/E):** `____`    **Why:** 

---

### P33  —  Durvalumab  ·  NSCLC

**Path 1** · `Durvalumab —inhibits→ CD274 —associated_with→ NSCLC`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Durvalumab → CD274 | `inhibits` | ESTABLISHED | FDA:BLA761069, mechanism:PD-L1_antibody | — | 0.98 |
| CD274 → NSCLC | `associated_with` | ESTABLISHED | PMID:41699717; [RELATION-VERIFIED] | [41699717](https://pubmed.ncbi.nlm.nih.gov/41699717/) | 0.85 |

**Path 2** · `Durvalumab —inhibits→ CD274 —inhibits→ PDCD1 —associated_with→ NSCLC`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Durvalumab → CD274 | `inhibits` | ESTABLISHED | FDA:BLA761069, mechanism:PD-L1_antibody | — | 0.98 |
| CD274 → PDCD1 | `inhibits` | ESTABLISHED | PMID:41655134; [RELATION-VERIFIED] | [41655134](https://pubmed.ncbi.nlm.nih.gov/41655134/) | 0.95 |
| PDCD1 → NSCLC | `associated_with` | ESTABLISHED | PMID:40509568; [LEXICAL-COOCCURRENCE] | [40509568](https://pubmed.ncbi.nlm.nih.gov/40509568/) | 0.85 |

**Path 3** · `Durvalumab —inhibits→ CD274 —associated_with→ Pancreatic_Cancer —associated_with→ Multiple_Myeloma —associated_with→ NSCLC`  ⚠ **routes through another disease — co-occurrence, not mechanism**

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Durvalumab → CD274 | `inhibits` | ESTABLISHED | FDA:BLA761069, mechanism:PD-L1_antibody | — | 0.98 |
| CD274 → Pancreatic_Cancer | `associated_with` | INFERRED | PMID:38174993; [RELATION-SCREENED] | [38174993](https://pubmed.ncbi.nlm.nih.gov/38174993/) | 0.65 |
| Pancreatic_Cancer → Multiple_Myeloma | `associated_with` | INFERRED | PMID:38967919; [RELATION-SCREENED] | [38967919](https://pubmed.ncbi.nlm.nih.gov/38967919/) | 0.65 |
| Multiple_Myeloma → NSCLC | `associated_with` | INFERRED | PMID:36762777; [RELATION-SCREENED] | [36762777](https://pubmed.ncbi.nlm.nih.gov/36762777/) | 0.65 |

**What this candidate does not have:** every terminal Protein->Disease hop is `associated_with`, a co-occurrence relation, not a mechanistic claim; no quantitative value on any edge (the column is NULL graph-wide)

**Your code (A/B/C/D/E):** `____`    **Why:** 

---

### P34  —  Lapatinib  ·  NSCLC

**Path 1** · `Lapatinib —inhibits→ EGFR —driver_of→ NSCLC`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Lapatinib → EGFR | `inhibits` | ESTABLISHED | FDA:NDA022059, mechanism:dual_EGFR_HER2_TKI; | [42089475](https://pubmed.ncbi.nlm.nih.gov/42089475/) | 0.94 |
| EGFR → NSCLC | `driver_of` | ESTABLISHED | PMID:42182703; [LEXICAL-COOCCURRENCE] | [42182703](https://pubmed.ncbi.nlm.nih.gov/42182703/) | 0.95 |

**Path 2** · `Lapatinib —inhibits→ ERBB2 —associated_with→ NSCLC`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Lapatinib → ERBB2 | `inhibits` | ESTABLISHED | FDA:NDA022059, mechanism:dual_EGFR_HER2_TKI | — | 0.93 |
| ERBB2 → NSCLC | `associated_with` | MEASURED | ABPP; PMID:41982617; [RELATION-VERIFIED] | [41982617](https://pubmed.ncbi.nlm.nih.gov/41982617/) | 0.80 |

**Path 3** · `Lapatinib —inhibits→ EGFR —activates→ KRAS —driver_of→ NSCLC`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Lapatinib → EGFR | `inhibits` | ESTABLISHED | FDA:NDA022059, mechanism:dual_EGFR_HER2_TKI; | [42089475](https://pubmed.ncbi.nlm.nih.gov/42089475/) | 0.94 |
| EGFR → KRAS | `activates` | ESTABLISHED | KEGG:hsa04010, cancer_proteins.py | — | 0.95 |
| KRAS → NSCLC | `driver_of` | ESTABLISHED | PMID:42075590; [RELATION-VERIFIED] | [42075590](https://pubmed.ncbi.nlm.nih.gov/42075590/) | 0.88 |

**What this candidate does not have:** no quantitative value on any edge (the column is NULL graph-wide)

**Your code (A/B/C/D/E):** `____`    **Why:** 

---

### P35  —  Adagrasib  ·  NSCLC

**Path 1** · `Adagrasib —inhibits→ KRAS —driver_of→ NSCLC`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Adagrasib → KRAS | `inhibits` | ESTABLISHED | FDA:NDA216340, mechanism:KRAS_G12C_inhibitor | [42122163](https://pubmed.ncbi.nlm.nih.gov/42122163/) | 0.97 |
| KRAS → NSCLC | `driver_of` | ESTABLISHED | PMID:42075590; [RELATION-VERIFIED] | [42075590](https://pubmed.ncbi.nlm.nih.gov/42075590/) | 0.88 |

**Path 2** · `Adagrasib —inhibits→ KRAS —pathway_crosstalk→ TP53 —associated_with→ NSCLC`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Adagrasib → KRAS | `inhibits` | ESTABLISHED | FDA:NDA216340, mechanism:KRAS_G12C_inhibitor | [42122163](https://pubmed.ncbi.nlm.nih.gov/42122163/) | 0.97 |
| KRAS → TP53 | `pathway_crosstalk` | ESTABLISHED | KEGG:hsa04014, cancer_proteins.py | — | 0.82 |
| TP53 → NSCLC | `associated_with` | ESTABLISHED | PMID:37683526 | [37683526](https://pubmed.ncbi.nlm.nih.gov/37683526/) | 0.90 |

**Path 3** · `Adagrasib —inhibits→ KRAS —activates→ BRAF —associated_with→ NSCLC`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Adagrasib → KRAS | `inhibits` | ESTABLISHED | FDA:NDA216340, mechanism:KRAS_G12C_inhibitor | [42122163](https://pubmed.ncbi.nlm.nih.gov/42122163/) | 0.97 |
| KRAS → BRAF | `activates` | ESTABLISHED | KEGG:hsa04010, cancer_proteins.py; PMID:4186 | [41862948](https://pubmed.ncbi.nlm.nih.gov/41862948/) | 0.97 |
| BRAF → NSCLC | `associated_with` | ESTABLISHED | cancer_proteins | — | 0.70 |

**What this candidate does not have:** no quantitative value on any edge (the column is NULL graph-wide)

**Your code (A/B/C/D/E):** `____`    **Why:** 

---

### P36  —  Etodolac  ·  Melanoma

**Path 1** · `Etodolac —inhibits→ PTGS2 —associated_with→ Melanoma`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Etodolac → PTGS2 | `inhibits` | MEASURED | ChEMBL:CHEMBL622 | — | 1.00 |
| PTGS2 → Melanoma | `associated_with` | INFERRED | PMID:38934060; discovery-grounded; agent-adj | [38934060](https://pubmed.ncbi.nlm.nih.gov/38934060/) | 0.60 |

**Path 2** · `Etodolac —inhibits→ PTGS2 —associated_with→ HCC —associated_with→ RCC —associated_with→ Melanoma`  ⚠ **routes through another disease — co-occurrence, not mechanism**

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Etodolac → PTGS2 | `inhibits` | MEASURED | ChEMBL:CHEMBL622 | — | 1.00 |
| PTGS2 → HCC | `associated_with` | INFERRED | PMID:31679460; [RELATION-SCREENED] | [31679460](https://pubmed.ncbi.nlm.nih.gov/31679460/) | 0.65 |
| HCC → RCC | `associated_with` | INFERRED | PMID:37469132; [RELATION-SCREENED] | [37469132](https://pubmed.ncbi.nlm.nih.gov/37469132/) | 0.65 |
| RCC → Melanoma | `associated_with` | INFERRED | PMID:39842618; [RELATION-SCREENED] | [39842618](https://pubmed.ncbi.nlm.nih.gov/39842618/) | 0.65 |

**Path 3** · `Etodolac —inhibits→ PTGS2 —associated_with→ CML —associated_with→ Ovarian_Cancer —associated_with→ Melanoma`  ⚠ **routes through another disease — co-occurrence, not mechanism**

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Etodolac → PTGS2 | `inhibits` | MEASURED | ChEMBL:CHEMBL622 | — | 1.00 |
| PTGS2 → CML | `associated_with` | INFERRED | PMID:39450252; discovery-grounded; agent-adj | [39450252](https://pubmed.ncbi.nlm.nih.gov/39450252/) | 0.60 |
| CML → Ovarian_Cancer | `associated_with` | INFERRED | PMID:32169887; [RELATION-SCREENED] | [32169887](https://pubmed.ncbi.nlm.nih.gov/32169887/) | 0.65 |
| Ovarian_Cancer → Melanoma | `associated_with` | INFERRED | PMID:20301425; [RELATION-SCREENED] | [20301425](https://pubmed.ncbi.nlm.nih.gov/20301425/) | 0.65 |

**What this candidate does not have:** every terminal Protein->Disease hop is `associated_with`, a co-occurrence relation, not a mechanistic claim; no quantitative value on any edge (the column is NULL graph-wide)

**Your code (A/B/C/D/E):** `____`    **Why:** 

---

### P37  —  Doxycycline Hyclate  ·  Melanoma

**Path 1** · `Doxycycline Hyclate —inhibits→ MMP8 —associated_with→ Melanoma`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Doxycycline Hyclate → MMP8 | `inhibits` | MEASURED | ChEMBL:CHEMBL3989740 | — | 1.00 |
| MMP8 → Melanoma | `associated_with` | INFERRED | PMID:21642878; discovery-grounded; agent-adj | [21642878](https://pubmed.ncbi.nlm.nih.gov/21642878/) | 0.60 |

**Path 2** · `Doxycycline Hyclate —inhibits→ MMP13 —associated_with→ Melanoma`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Doxycycline Hyclate → MMP13 | `inhibits` | MEASURED | ChEMBL:CHEMBL3989740 | — | 1.00 |
| MMP13 → Melanoma | `associated_with` | INFERRED | PMID:38527983; discovery-grounded; agent-adj | [38527983](https://pubmed.ncbi.nlm.nih.gov/38527983/) | 0.60 |

**Path 3** · `Doxycycline Hyclate —inhibits→ MMP7 —associated_with→ RCC —associated_with→ Melanoma`  ⚠ **routes through another disease — co-occurrence, not mechanism**

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Doxycycline Hyclate → MMP7 | `inhibits` | MEASURED | ChEMBL:CHEMBL3989740 | — | 1.00 |
| MMP7 → RCC | `associated_with` | INFERRED | PMID:27278120; [RELATION-SCREENED] | [27278120](https://pubmed.ncbi.nlm.nih.gov/27278120/) | 0.65 |
| RCC → Melanoma | `associated_with` | INFERRED | PMID:39842618; [RELATION-SCREENED] | [39842618](https://pubmed.ncbi.nlm.nih.gov/39842618/) | 0.65 |

**What this candidate does not have:** every terminal Protein->Disease hop is `associated_with`, a co-occurrence relation, not a mechanistic claim; no quantitative value on any edge (the column is NULL graph-wide)

**Your code (A/B/C/D/E):** `____`    **Why:** 

---

### P38  —  Cabozantinib S-Malate  ·  NSCLC

**Path 1** · `Cabozantinib S-Malate —inhibits→ MET —associated_with→ NSCLC`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Cabozantinib S-Malate → MET | `inhibits` | MEASURED | ChEMBL:CHEMBL2103868 | — | 1.00 |
| MET → NSCLC | `associated_with` | ESTABLISHED | PMID:42187575; [RELATION-VERIFIED] | [42187575](https://pubmed.ncbi.nlm.nih.gov/42187575/) | 0.80 |

**Path 2** · `Cabozantinib S-Malate —inhibits→ MET —activates→ KRAS —driver_of→ NSCLC`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Cabozantinib S-Malate → MET | `inhibits` | MEASURED | ChEMBL:CHEMBL2103868 | — | 1.00 |
| MET → KRAS | `activates` | ESTABLISHED | KEGG:hsa04014, cancer_proteins.py | — | 0.89 |
| KRAS → NSCLC | `driver_of` | ESTABLISHED | PMID:42075590; [RELATION-VERIFIED] | [42075590](https://pubmed.ncbi.nlm.nih.gov/42075590/) | 0.88 |

**Path 3** · `Cabozantinib S-Malate —inhibits→ MET —activates→ PI3KCA —associated_with→ NSCLC`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Cabozantinib S-Malate → MET | `inhibits` | MEASURED | ChEMBL:CHEMBL2103868 | — | 1.00 |
| MET → PI3KCA | `activates` | ESTABLISHED | PMID:34802045 | [34802045](https://pubmed.ncbi.nlm.nih.gov/34802045/) | 0.91 |
| PI3KCA → NSCLC | `associated_with` | INFERRED | PPI; PMID:41221490; [RELATION-VERIFIED] | [41221490](https://pubmed.ncbi.nlm.nih.gov/41221490/) | 0.50 |

**What this candidate does not have:** no quantitative value on any edge (the column is NULL graph-wide)

**Your code (A/B/C/D/E):** `____`    **Why:** 

---

### P39  —  Floxuridine  ·  Melanoma

**Path 1** · `Floxuridine —inhibits→ TYMS —associated_with→ Melanoma`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Floxuridine → TYMS | `inhibits` | MEASURED | ChEMBL:CHEMBL917 | — | 1.00 |
| TYMS → Melanoma | `associated_with` | INFERRED | PMID:17611626; discovery-grounded; agent-adj | [17611626](https://pubmed.ncbi.nlm.nih.gov/17611626/) | 0.60 |

**Path 2** · `Floxuridine —inhibits→ TYMS —associated_with→ RCC —associated_with→ Melanoma`  ⚠ **routes through another disease — co-occurrence, not mechanism**

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Floxuridine → TYMS | `inhibits` | MEASURED | ChEMBL:CHEMBL917 | — | 1.00 |
| TYMS → RCC | `associated_with` | INFERRED | PMID:18098291; discovery-grounded; agent-adj | [18098291](https://pubmed.ncbi.nlm.nih.gov/18098291/) | 0.60 |
| RCC → Melanoma | `associated_with` | INFERRED | PMID:39842618; [RELATION-SCREENED] | [39842618](https://pubmed.ncbi.nlm.nih.gov/39842618/) | 0.65 |

**Path 3** · `Floxuridine —inhibits→ TYMS —associated_with→ CLL —associated_with→ Melanoma`  ⚠ **routes through another disease — co-occurrence, not mechanism**

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Floxuridine → TYMS | `inhibits` | MEASURED | ChEMBL:CHEMBL917 | — | 1.00 |
| TYMS → CLL | `associated_with` | INFERRED | PMID:18945750; discovery-grounded; agent-adj | [18945750](https://pubmed.ncbi.nlm.nih.gov/18945750/) | 0.60 |
| CLL → Melanoma | `associated_with` | INFERRED | PMID:37946198; [RELATION-SCREENED] | [37946198](https://pubmed.ncbi.nlm.nih.gov/37946198/) | 0.65 |

**What this candidate does not have:** every terminal Protein->Disease hop is `associated_with`, a co-occurrence relation, not a mechanistic claim; no quantitative value on any edge (the column is NULL graph-wide)

**Your code (A/B/C/D/E):** `____`    **Why:** 

---

### P40  —  Atorvastatin  ·  Melanoma

**Path 1** · `Atorvastatin —inhibits→ HMGCR —associated_with→ Melanoma`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Atorvastatin → HMGCR | `inhibits` | MEASURED | ChEMBL:CHEMBL393220; PMID:41866501; [RELATIO | [41866501](https://pubmed.ncbi.nlm.nih.gov/41866501/) | 1.00 |
| HMGCR → Melanoma | `associated_with` | INFERRED | PMID:40509568; [RELATION-SCREENED] | [40509568](https://pubmed.ncbi.nlm.nih.gov/40509568/) | 0.65 |

**Path 2** · `Atorvastatin —indirect_inhibitor→ NRAS —associated_with→ Melanoma`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Atorvastatin → NRAS | `indirect_inhibitor` | INFERRED | literature (unverified) | — | 0.68 |
| NRAS → Melanoma | `associated_with` | ESTABLISHED | cancer_proteins; PMID:42193039; [RELATION-VE | [42193039](https://pubmed.ncbi.nlm.nih.gov/42193039/) | 0.70 |

**Path 3** · `Atorvastatin —indirect_inhibitor→ MTOR —associated_with→ Melanoma`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Atorvastatin → MTOR | `indirect_inhibitor` | INFERRED | literature (unverified); PMID:37181137; [REL | [37181137](https://pubmed.ncbi.nlm.nih.gov/37181137/) | 0.55 |
| MTOR → Melanoma | `associated_with` | INFERRED | cancer_proteins; PMID:42022563; [RELATION-VE | [42022563](https://pubmed.ncbi.nlm.nih.gov/42022563/) | 0.55 |

**What this candidate does not have:** every terminal Protein->Disease hop is `associated_with`, a co-occurrence relation, not a mechanistic claim; no quantitative value on any edge (the column is NULL graph-wide)

**Your code (A/B/C/D/E):** `____`    **Why:** 

---

### P41  —  Tepotinib  ·  NSCLC

**Path 1** · `Tepotinib —inhibits→ MET —associated_with→ NSCLC`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Tepotinib → MET | `inhibits` | ESTABLISHED | FDA:NDA214096, mechanism:MET_TKI; PMID:41760 | [41760894](https://pubmed.ncbi.nlm.nih.gov/41760894/) | 0.98 |
| MET → NSCLC | `associated_with` | ESTABLISHED | PMID:42187575; [RELATION-VERIFIED] | [42187575](https://pubmed.ncbi.nlm.nih.gov/42187575/) | 0.80 |

**Path 2** · `Tepotinib —inhibits→ MET —activates→ KRAS —driver_of→ NSCLC`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Tepotinib → MET | `inhibits` | ESTABLISHED | FDA:NDA214096, mechanism:MET_TKI; PMID:41760 | [41760894](https://pubmed.ncbi.nlm.nih.gov/41760894/) | 0.98 |
| MET → KRAS | `activates` | ESTABLISHED | KEGG:hsa04014, cancer_proteins.py | — | 0.89 |
| KRAS → NSCLC | `driver_of` | ESTABLISHED | PMID:42075590; [RELATION-VERIFIED] | [42075590](https://pubmed.ncbi.nlm.nih.gov/42075590/) | 0.88 |

**Path 3** · `Tepotinib —inhibits→ MET —activates→ PI3KCA —associated_with→ NSCLC`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Tepotinib → MET | `inhibits` | ESTABLISHED | FDA:NDA214096, mechanism:MET_TKI; PMID:41760 | [41760894](https://pubmed.ncbi.nlm.nih.gov/41760894/) | 0.98 |
| MET → PI3KCA | `activates` | ESTABLISHED | PMID:34802045 | [34802045](https://pubmed.ncbi.nlm.nih.gov/34802045/) | 0.91 |
| PI3KCA → NSCLC | `associated_with` | INFERRED | PPI; PMID:41221490; [RELATION-VERIFIED] | [41221490](https://pubmed.ncbi.nlm.nih.gov/41221490/) | 0.50 |

**What this candidate does not have:** no quantitative value on any edge (the column is NULL graph-wide)

**Your code (A/B/C/D/E):** `____`    **Why:** 

---

### P42  —  Lazertinib  ·  NSCLC

**Path 1** · `Lazertinib —inhibits→ EGFR —driver_of→ NSCLC`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Lazertinib → EGFR | `inhibits` | MEASURED | ChEMBL:CHEMBL4558324; PMID:41859193; [LEXICA | [41859193](https://pubmed.ncbi.nlm.nih.gov/41859193/) | 1.00 |
| EGFR → NSCLC | `driver_of` | ESTABLISHED | PMID:42182703; [LEXICAL-COOCCURRENCE] | [42182703](https://pubmed.ncbi.nlm.nih.gov/42182703/) | 0.95 |

**Path 2** · `Lazertinib —inhibits→ EGFR —activates→ KRAS —driver_of→ NSCLC`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Lazertinib → EGFR | `inhibits` | MEASURED | ChEMBL:CHEMBL4558324; PMID:41859193; [LEXICA | [41859193](https://pubmed.ncbi.nlm.nih.gov/41859193/) | 1.00 |
| EGFR → KRAS | `activates` | ESTABLISHED | KEGG:hsa04010, cancer_proteins.py | — | 0.95 |
| KRAS → NSCLC | `driver_of` | ESTABLISHED | PMID:42075590; [RELATION-VERIFIED] | [42075590](https://pubmed.ncbi.nlm.nih.gov/42075590/) | 0.88 |

**Path 3** · `Lazertinib —inhibits→ EGFR —activates→ STAT3 —associated_with→ NSCLC`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Lazertinib → EGFR | `inhibits` | MEASURED | ChEMBL:CHEMBL4558324; PMID:41859193; [LEXICA | [41859193](https://pubmed.ncbi.nlm.nih.gov/41859193/) | 1.00 |
| EGFR → STAT3 | `activates` | ESTABLISHED | KEGG:hsa04630, cancer_proteins.py; PMID:4217 | [42177207](https://pubmed.ncbi.nlm.nih.gov/42177207/) | 0.88 |
| STAT3 → NSCLC | `associated_with` | INFERRED | cancer_proteins | — | 0.55 |

**What this candidate does not have:** no quantitative value on any edge (the column is NULL graph-wide)

**Your code (A/B/C/D/E):** `____`    **Why:** 

---

### P43  —  Sorafenib  ·  Melanoma

**Path 1** · `Sorafenib —inhibits→ BRAF —driver_of→ Melanoma`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Sorafenib → BRAF | `inhibits` | ESTABLISHED | FDA:NDA021923, mechanism:multikinase_inhibit | [41497266](https://pubmed.ncbi.nlm.nih.gov/41497266/) | 0.85 |
| BRAF → Melanoma | `driver_of` | ESTABLISHED | PMID:42126185; [LEXICAL-COOCCURRENCE] | [42126185](https://pubmed.ncbi.nlm.nih.gov/42126185/) | 0.95 |

**Path 2** · `Sorafenib —inhibits→ VEGFR2 —associated_with→ Melanoma`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Sorafenib → VEGFR2 | `inhibits` | ESTABLISHED | FDA:NDA021923, mechanism:multikinase_inhibit | — | 0.90 |
| VEGFR2 → Melanoma | `associated_with` | INFERRED | cancer_proteins | — | 0.55 |

**Path 3** · `Sorafenib —inhibits→ RAF1 —associated_with→ Melanoma`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Sorafenib → RAF1 | `inhibits` | ESTABLISHED | FDA:NDA021923, mechanism:multikinase_inhibit | [41347828](https://pubmed.ncbi.nlm.nih.gov/41347828/) | 0.83 |
| RAF1 → Melanoma | `associated_with` | INFERRED | cancer_proteins; PMID:39574163; [RELATION-VE | [39574163](https://pubmed.ncbi.nlm.nih.gov/39574163/) | 0.55 |

**What this candidate does not have:** no quantitative value on any edge (the column is NULL graph-wide)

**Your code (A/B/C/D/E):** `____`    **Why:** 

---

### P44  —  Brigatinib  ·  NSCLC

**Path 1** · `Brigatinib —inhibits→ ALK —driver_of→ NSCLC`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Brigatinib → ALK | `inhibits` | ESTABLISHED | FDA:NDA208772, mechanism:ALK_TKI; PMID:42136 | [42136297](https://pubmed.ncbi.nlm.nih.gov/42136297/) | 0.98 |
| ALK → NSCLC | `driver_of` | ESTABLISHED | PMID:42187575; [LEXICAL-COOCCURRENCE] | [42187575](https://pubmed.ncbi.nlm.nih.gov/42187575/) | 0.92 |

**Path 2** · `Brigatinib —inhibits→ EGFR —driver_of→ NSCLC`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Brigatinib → EGFR | `inhibits` | ESTABLISHED | FDA:NDA208772, mechanism:ALK_EGFR_TKI; PMID: | [41611070](https://pubmed.ncbi.nlm.nih.gov/41611070/) | 0.75 |
| EGFR → NSCLC | `driver_of` | ESTABLISHED | PMID:42182703; [LEXICAL-COOCCURRENCE] | [42182703](https://pubmed.ncbi.nlm.nih.gov/42182703/) | 0.95 |

**Path 3** · `Brigatinib —inhibits→ EGFR —activates→ KRAS —driver_of→ NSCLC`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Brigatinib → EGFR | `inhibits` | ESTABLISHED | FDA:NDA208772, mechanism:ALK_EGFR_TKI; PMID: | [41611070](https://pubmed.ncbi.nlm.nih.gov/41611070/) | 0.75 |
| EGFR → KRAS | `activates` | ESTABLISHED | KEGG:hsa04010, cancer_proteins.py | — | 0.95 |
| KRAS → NSCLC | `driver_of` | ESTABLISHED | PMID:42075590; [RELATION-VERIFIED] | [42075590](https://pubmed.ncbi.nlm.nih.gov/42075590/) | 0.88 |

**What this candidate does not have:** no quantitative value on any edge (the column is NULL graph-wide)

**Your code (A/B/C/D/E):** `____`    **Why:** 

---

### P45  —  Crizotinib  ·  Melanoma

**Path 1** · `Crizotinib —inhibits→ MST1R —associated_with→ Melanoma`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Crizotinib → MST1R | `inhibits` | MEASURED | ChEMBL:CHEMBL601719 | — | 1.00 |
| MST1R → Melanoma | `associated_with` | INFERRED | PMID:38870080; discovery-grounded; agent-adj | [38870080](https://pubmed.ncbi.nlm.nih.gov/38870080/) | 0.60 |

**Path 2** · `Crizotinib —inhibits→ MET —activates→ PI3KCA —associated_with→ Melanoma`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Crizotinib → MET | `inhibits` | ESTABLISHED | FDA:NDA202570, mechanism:ALK_MET_ROS1_inhibi | [42015375](https://pubmed.ncbi.nlm.nih.gov/42015375/) | 0.93 |
| MET → PI3KCA | `activates` | ESTABLISHED | PMID:34802045 | [34802045](https://pubmed.ncbi.nlm.nih.gov/34802045/) | 0.91 |
| PI3KCA → Melanoma | `associated_with` | HYPOTHESIS | pathway:neighbor_of_ERBB2 | — | 0.60 |

**Path 3** · `Crizotinib —inhibits→ ALK —associated_with→ Breast_Cancer —associated_with→ Melanoma`  ⚠ **routes through another disease — co-occurrence, not mechanism**

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Crizotinib → ALK | `inhibits` | ESTABLISHED | FDA:NDA202570, mechanism:ALK_TKI; PMID:42136 | [42136678](https://pubmed.ncbi.nlm.nih.gov/42136678/) | 0.96 |
| ALK → Breast_Cancer | `associated_with` | INFERRED | PMID:32954856; [RELATION-SCREENED] | [32954856](https://pubmed.ncbi.nlm.nih.gov/32954856/) | 0.65 |
| Breast_Cancer → Melanoma | `associated_with` | INFERRED | PMID:30497674; [RELATION-SCREENED] | [30497674](https://pubmed.ncbi.nlm.nih.gov/30497674/) | 0.65 |

**What this candidate does not have:** every terminal Protein->Disease hop is `associated_with`, a co-occurrence relation, not a mechanistic claim; no quantitative value on any edge (the column is NULL graph-wide)

**Your code (A/B/C/D/E):** `____`    **Why:** 

---

### P46  —  Fluvastatin  ·  Melanoma

**Path 1** · `Fluvastatin —inhibits→ HMGCR —associated_with→ Melanoma`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Fluvastatin → HMGCR | `inhibits` | MEASURED | ChEMBL:CHEMBL2218894; PMID:24976507; [RELATI | [24976507](https://pubmed.ncbi.nlm.nih.gov/24976507/) | 1.00 |
| HMGCR → Melanoma | `associated_with` | INFERRED | PMID:40509568; [RELATION-SCREENED] | [40509568](https://pubmed.ncbi.nlm.nih.gov/40509568/) | 0.65 |

**Path 2** · `Fluvastatin —inhibits→ HMGCR —associated_with→ RCC —associated_with→ Melanoma`  ⚠ **routes through another disease — co-occurrence, not mechanism**

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Fluvastatin → HMGCR | `inhibits` | MEASURED | ChEMBL:CHEMBL2218894; PMID:24976507; [RELATI | [24976507](https://pubmed.ncbi.nlm.nih.gov/24976507/) | 1.00 |
| HMGCR → RCC | `associated_with` | INFERRED | PMID:34712689; [RELATION-SCREENED] | [34712689](https://pubmed.ncbi.nlm.nih.gov/34712689/) | 0.65 |
| RCC → Melanoma | `associated_with` | INFERRED | PMID:39842618; [RELATION-SCREENED] | [39842618](https://pubmed.ncbi.nlm.nih.gov/39842618/) | 0.65 |

**Path 3** · `Fluvastatin —inhibits→ HMGCR —associated_with→ Breast_Cancer —associated_with→ Melanoma`  ⚠ **routes through another disease — co-occurrence, not mechanism**

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Fluvastatin → HMGCR | `inhibits` | MEASURED | ChEMBL:CHEMBL2218894; PMID:24976507; [RELATI | [24976507](https://pubmed.ncbi.nlm.nih.gov/24976507/) | 1.00 |
| HMGCR → Breast_Cancer | `associated_with` | INFERRED | PMID:39143707; discovery-grounded; agent-adj | [39143707](https://pubmed.ncbi.nlm.nih.gov/39143707/) | 0.60 |
| Breast_Cancer → Melanoma | `associated_with` | INFERRED | PMID:30497674; [RELATION-SCREENED] | [30497674](https://pubmed.ncbi.nlm.nih.gov/30497674/) | 0.65 |

**What this candidate does not have:** every terminal Protein->Disease hop is `associated_with`, a co-occurrence relation, not a mechanistic claim; no quantitative value on any edge (the column is NULL graph-wide)

**Your code (A/B/C/D/E):** `____`    **Why:** 

---

### P47  —  Sotorasib  ·  NSCLC

**Path 1** · `Sotorasib —inhibits→ KRAS —driver_of→ NSCLC`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Sotorasib → KRAS | `inhibits` | ESTABLISHED | FDA:NDA214665, mechanism:KRAS_G12C_inhibitor | [42144204](https://pubmed.ncbi.nlm.nih.gov/42144204/) | 0.97 |
| KRAS → NSCLC | `driver_of` | ESTABLISHED | PMID:42075590; [RELATION-VERIFIED] | [42075590](https://pubmed.ncbi.nlm.nih.gov/42075590/) | 0.88 |

**Path 2** · `Sotorasib —indirect_inhibitor→ MAP2K1 —associated_with→ NSCLC`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Sotorasib → MAP2K1 | `indirect_inhibitor` | ESTABLISHED | literature (unverified) | — | 0.80 |
| MAP2K1 → NSCLC | `associated_with` | INFERRED | PMID:32361034; discovery-grounded; agent-adj | [32361034](https://pubmed.ncbi.nlm.nih.gov/32361034/) | 0.60 |

**Path 3** · `Sotorasib —inhibits→ KRAS —pathway_crosstalk→ TP53 —associated_with→ NSCLC`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Sotorasib → KRAS | `inhibits` | ESTABLISHED | FDA:NDA214665, mechanism:KRAS_G12C_inhibitor | [42144204](https://pubmed.ncbi.nlm.nih.gov/42144204/) | 0.97 |
| KRAS → TP53 | `pathway_crosstalk` | ESTABLISHED | KEGG:hsa04014, cancer_proteins.py | — | 0.82 |
| TP53 → NSCLC | `associated_with` | ESTABLISHED | PMID:37683526 | [37683526](https://pubmed.ncbi.nlm.nih.gov/37683526/) | 0.90 |

**What this candidate does not have:** no quantitative value on any edge (the column is NULL graph-wide)

**Your code (A/B/C/D/E):** `____`    **Why:** 

---

### P48  —  Capecitabine  ·  Melanoma

**Path 1** · `Capecitabine —inhibits→ TYMS —associated_with→ Melanoma`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Capecitabine → TYMS | `inhibits` | MEASURED | ChEMBL:CHEMBL1773; PMID:39163685; [RELATION- | [39163685](https://pubmed.ncbi.nlm.nih.gov/39163685/) | 1.00 |
| TYMS → Melanoma | `associated_with` | INFERRED | PMID:17611626; discovery-grounded; agent-adj | [17611626](https://pubmed.ncbi.nlm.nih.gov/17611626/) | 0.60 |

**Path 2** · `Capecitabine —inhibits→ TYMS —associated_with→ RCC —associated_with→ Melanoma`  ⚠ **routes through another disease — co-occurrence, not mechanism**

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Capecitabine → TYMS | `inhibits` | MEASURED | ChEMBL:CHEMBL1773; PMID:39163685; [RELATION- | [39163685](https://pubmed.ncbi.nlm.nih.gov/39163685/) | 1.00 |
| TYMS → RCC | `associated_with` | INFERRED | PMID:18098291; discovery-grounded; agent-adj | [18098291](https://pubmed.ncbi.nlm.nih.gov/18098291/) | 0.60 |
| RCC → Melanoma | `associated_with` | INFERRED | PMID:39842618; [RELATION-SCREENED] | [39842618](https://pubmed.ncbi.nlm.nih.gov/39842618/) | 0.65 |

**Path 3** · `Capecitabine —inhibits→ TYMS —associated_with→ CLL —associated_with→ Melanoma`  ⚠ **routes through another disease — co-occurrence, not mechanism**

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Capecitabine → TYMS | `inhibits` | MEASURED | ChEMBL:CHEMBL1773; PMID:39163685; [RELATION- | [39163685](https://pubmed.ncbi.nlm.nih.gov/39163685/) | 1.00 |
| TYMS → CLL | `associated_with` | INFERRED | PMID:18945750; discovery-grounded; agent-adj | [18945750](https://pubmed.ncbi.nlm.nih.gov/18945750/) | 0.60 |
| CLL → Melanoma | `associated_with` | INFERRED | PMID:37946198; [RELATION-SCREENED] | [37946198](https://pubmed.ncbi.nlm.nih.gov/37946198/) | 0.65 |

**What this candidate does not have:** every terminal Protein->Disease hop is `associated_with`, a co-occurrence relation, not a mechanistic claim; no quantitative value on any edge (the column is NULL graph-wide)

**Your code (A/B/C/D/E):** `____`    **Why:** 

---

### P49  —  Cemiplimab  ·  NSCLC

**Path 1** · `Cemiplimab —inhibits→ PDCD1 —associated_with→ NSCLC`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Cemiplimab → PDCD1 | `inhibits` | MEASURED | ChEMBL:CHEMBL4297723 | — | 1.00 |
| PDCD1 → NSCLC | `associated_with` | ESTABLISHED | PMID:40509568; [LEXICAL-COOCCURRENCE] | [40509568](https://pubmed.ncbi.nlm.nih.gov/40509568/) | 0.85 |

**Path 2** · `Cemiplimab —inhibits→ PDCD1 —associated_with→ RCC —associated_with→ Multiple_Myeloma —associated_with→ NSCLC`  ⚠ **routes through another disease — co-occurrence, not mechanism**

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Cemiplimab → PDCD1 | `inhibits` | MEASURED | ChEMBL:CHEMBL4297723 | — | 1.00 |
| PDCD1 → RCC | `associated_with` | ESTABLISHED | PMID:26406148 | [26406148](https://pubmed.ncbi.nlm.nih.gov/26406148/) | 0.80 |
| RCC → Multiple_Myeloma | `associated_with` | INFERRED | PMID:35528462; [RELATION-SCREENED] | [35528462](https://pubmed.ncbi.nlm.nih.gov/35528462/) | 0.65 |
| Multiple_Myeloma → NSCLC | `associated_with` | INFERRED | PMID:36762777; [RELATION-SCREENED] | [36762777](https://pubmed.ncbi.nlm.nih.gov/36762777/) | 0.65 |

**Path 3** · `Cemiplimab —inhibits→ PDCD1 —associated_with→ Colorectal_Cancer —associated_with→ Multiple_Myeloma —associated_with→ NSCLC`  ⚠ **routes through another disease — co-occurrence, not mechanism**

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Cemiplimab → PDCD1 | `inhibits` | MEASURED | ChEMBL:CHEMBL4297723 | — | 1.00 |
| PDCD1 → Colorectal_Cancer | `associated_with` | INFERRED | PMID:41655134; discovery-grounded; agent-adj | [41655134](https://pubmed.ncbi.nlm.nih.gov/41655134/) | 0.60 |
| Colorectal_Cancer → Multiple_Myeloma | `associated_with` | INFERRED | PMID:38967919; [RELATION-SCREENED] | [38967919](https://pubmed.ncbi.nlm.nih.gov/38967919/) | 0.65 |
| Multiple_Myeloma → NSCLC | `associated_with` | INFERRED | PMID:36762777; [RELATION-SCREENED] | [36762777](https://pubmed.ncbi.nlm.nih.gov/36762777/) | 0.65 |

**What this candidate does not have:** every terminal Protein->Disease hop is `associated_with`, a co-occurrence relation, not a mechanistic claim; no quantitative value on any edge (the column is NULL graph-wide)

**Your code (A/B/C/D/E):** `____`    **Why:** 

---

### P50  —  Afatinib  ·  NSCLC

**Path 1** · `Afatinib —inhibits→ EGFR —driver_of→ NSCLC`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Afatinib → EGFR | `inhibits` | ESTABLISHED | FDA:NDA201292, mechanism:irreversible_EGFR_T | [42151084](https://pubmed.ncbi.nlm.nih.gov/42151084/) | 0.97 |
| EGFR → NSCLC | `driver_of` | ESTABLISHED | PMID:42182703; [LEXICAL-COOCCURRENCE] | [42182703](https://pubmed.ncbi.nlm.nih.gov/42182703/) | 0.95 |

**Path 2** · `Afatinib —inhibits→ ERBB2 —associated_with→ NSCLC`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Afatinib → ERBB2 | `inhibits` | ESTABLISHED | FDA:NDA201292, mechanism:pan-HER_TKI; PMID:4 | [40612504](https://pubmed.ncbi.nlm.nih.gov/40612504/) | 0.95 |
| ERBB2 → NSCLC | `associated_with` | MEASURED | ABPP; PMID:41982617; [RELATION-VERIFIED] | [41982617](https://pubmed.ncbi.nlm.nih.gov/41982617/) | 0.80 |

**Path 3** · `Afatinib —inhibits→ EGFR —activates→ KRAS —driver_of→ NSCLC`

| edge | relation | tier | provenance | PMID | conf |
|---|---|---|---|---|---|
| Afatinib → EGFR | `inhibits` | ESTABLISHED | FDA:NDA201292, mechanism:irreversible_EGFR_T | [42151084](https://pubmed.ncbi.nlm.nih.gov/42151084/) | 0.97 |
| EGFR → KRAS | `activates` | ESTABLISHED | KEGG:hsa04010, cancer_proteins.py | — | 0.95 |
| KRAS → NSCLC | `driver_of` | ESTABLISHED | PMID:42075590; [RELATION-VERIFIED] | [42075590](https://pubmed.ncbi.nlm.nih.gov/42075590/) | 0.88 |

**What this candidate does not have:** no quantitative value on any edge (the column is NULL graph-wide)

**Your code (A/B/C/D/E):** `____`    **Why:** 

---
