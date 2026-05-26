# KOMPOSOS-IV-PHARM Candidate Triage: Disease: AML

## Graph Summary

- **Objects:** 1143
- **Morphisms:** 1260
- **Approved indications:** 44
- **Self-check:** 44/44 approved indications mechanistically recoverable

## Ranked Candidates

| Rank | Drug | Score | Label | Chains | Cited | Top Evidence Path |
|------|------|-------|-------|--------|-------|-------------------|
| 1 | Sunitinib | 1.000 | NOT_APPROVED | 4 | 12/12 | Sunitinib -inhibits-> FLT3 -driver_of-> AML |
| 2 | Niclosamide | 0.917 | NOT_APPROVED | 3 | 7/7 | Niclosamide -inhibits-> STAT3 -associated_with-> AML |
| 3 | Palbociclib | 0.904 | NOT_APPROVED | 0 | - | (no mechanistic path) |
| 4 | Ribociclib | 0.901 | NOT_APPROVED | 0 | - | (no mechanistic path) |
| 5 | Imatinib | 0.894 | NOT_APPROVED | 2 | 5/5 | Imatinib -inhibits-> KIT -associated_with-> AML |
| 6 | Regorafenib | 0.886 | NOT_APPROVED | 0 | - | (no mechanistic path) |
| 7 | Olaparib | 0.880 | NOT_APPROVED | 0 | - | (no mechanistic path) |
| 8 | Aspirin | 0.877 | NOT_APPROVED | 3 | 7/7 | Aspirin -inhibits-> NFKB1 -associated_with-> AML |
| 9 | Valproic_Acid | 0.877 | NOT_APPROVED | 2 | 4/4 | Valproic_Acid -inhibits-> HDAC1 -associated_with-> AML |
| 10 | Ruxolitinib | 0.875 | NOT_APPROVED | 3 | 9/9 | Ruxolitinib -inhibits-> JAK2 -associated_with-> AML |
| 11 | Venetoclax | 0.866 | NOT_APPROVED | 3 | 9/9 | Venetoclax -inhibits-> BCL2 -associated_with-> AML |
| 12 | Trastuzumab | 0.860 | NOT_APPROVED | 0 | - | (no mechanistic path) |
| 13 | Bazedoxifene | 0.845 | NOT_APPROVED | 3 | 7/7 | Bazedoxifene -inhibits-> IL6 -associated_with-> AML |
| 14 | Bevacizumab | 0.842 | NOT_APPROVED | 0 | - | (no mechanistic path) |
| 15 | Pembrolizumab | 0.838 | NOT_APPROVED | 0 | - | (no mechanistic path) |
| 16 | Ramucirumab | 0.835 | NOT_APPROVED | 0 | - | (no mechanistic path) |
| 17 | Auranofin | 0.828 | NOT_APPROVED | 2 | 4/4 | Auranofin -inhibits-> TXNRD1 -associated_with-> AML |
| 18 | Lapatinib | 0.798 | NOT_APPROVED | 2 | 7/7 | Lapatinib -inhibits-> EGFR -activates-> STAT3 -associated_with-> AML |
| 19 | Fluorouracil | 0.780 | NOT_APPROVED | 1 | 2/2 | Fluorouracil -associated_with-> TOP2A -driver_of-> AML |
| 20 | Ivermectin | 0.779 | NOT_APPROVED | 3 | 8/8 | Ivermectin -inhibits-> STAT3 -associated_with-> AML |

## Repurposing Candidate Details

*NOT_APPROVED means not in our 44 FDA-approved oncology indications.*
*These candidates may already be in clinical trials or published literature.*

### #1 Sunitinib -> AML

**Score:** 1.000

| Strategy | Score |
|----------|-------|
| kan_extension | 0.70 |
| composition | 0.88 |
| topos_logic | 0.85 |
| binding_evidence | 0.90 |

**Evidence chains:**

1. Sunitinib -inhibits-> FLT3 -driver_of-> AML
   - Sunitinib->FLT3: [PMID:16507829](https://pubmed.ncbi.nlm.nih.gov/16507829) (confidence: 0.88)
   - FLT3->AML: [PMID:19553641](https://pubmed.ncbi.nlm.nih.gov/19553641) (confidence: 0.90)
2. Sunitinib -inhibits-> KIT -associated_with-> AML
   - Sunitinib->KIT: [PMID:16507829](https://pubmed.ncbi.nlm.nih.gov/16507829) (confidence: 0.94)
   - KIT->AML: [PMID:11309425](https://pubmed.ncbi.nlm.nih.gov/11309425) (confidence: 0.75)
3. Sunitinib -inhibits-> FLT3 -phosphorylates-> STAT5A -activates-> BCL2 -associated_with-> AML
   - Sunitinib->FLT3: [PMID:16507829](https://pubmed.ncbi.nlm.nih.gov/16507829) (confidence: 0.88)
   - FLT3->STAT5A: [PMID:19553641](https://pubmed.ncbi.nlm.nih.gov/19553641) (confidence: 0.98)
   - STAT5A->BCL2: [PMID:12068308](https://pubmed.ncbi.nlm.nih.gov/12068308) (confidence: 0.91)
   - BCL2->AML: [PMID:27103402](https://pubmed.ncbi.nlm.nih.gov/27103402) (confidence: 0.78)
4. Sunitinib -inhibits-> FLT3 -activates-> AKT1 -activates-> BCL2 -associated_with-> AML
   - Sunitinib->FLT3: [PMID:16507829](https://pubmed.ncbi.nlm.nih.gov/16507829) (confidence: 0.88)
   - FLT3->AKT1: [PMID:19553641](https://pubmed.ncbi.nlm.nih.gov/19553641) (confidence: 0.89)
   - AKT1->BCL2: [PMID:16461283](https://pubmed.ncbi.nlm.nih.gov/16461283) (confidence: 0.91)
   - BCL2->AML: [PMID:27103402](https://pubmed.ncbi.nlm.nih.gov/27103402) (confidence: 0.78)

**Provenance:** 12/12 chain edges cited

### #2 Niclosamide -> AML

**Score:** 0.917

| Strategy | Score |
|----------|-------|
| kan_extension | 0.70 |
| composition | 0.72 |
| topos_logic | 0.69 |
| binding_evidence | 0.76 |

**Evidence chains:**

1. Niclosamide -inhibits-> STAT3 -associated_with-> AML
   - Niclosamide->STAT3: [PMID:22389471](https://pubmed.ncbi.nlm.nih.gov/22389471) (confidence: 0.85)
   - STAT3->AML: [PMID:22389471](https://pubmed.ncbi.nlm.nih.gov/22389471) (confidence: 0.72)
2. Niclosamide -inhibits-> STAT3 -activates-> BCL2 -associated_with-> AML
   - Niclosamide->STAT3: [PMID:22389471](https://pubmed.ncbi.nlm.nih.gov/22389471) (confidence: 0.85)
   - STAT3->BCL2: [PMID:12068308](https://pubmed.ncbi.nlm.nih.gov/12068308) (confidence: 0.90)
   - BCL2->AML: [PMID:27103402](https://pubmed.ncbi.nlm.nih.gov/27103402) (confidence: 0.78)
3. Niclosamide -inhibits-> NFKB1 -associated_with-> AML
   - Niclosamide->NFKB1: [PMID:22389471](https://pubmed.ncbi.nlm.nih.gov/22389471) (confidence: 0.75)
   - NFKB1->AML: [PMID:9597151](https://pubmed.ncbi.nlm.nih.gov/9597151) (confidence: 0.68)

**Provenance:** 7/7 chain edges cited

### #3 Palbociclib -> AML

**Score:** 0.904

| Strategy | Score |
|----------|-------|
| kan_extension | 0.90 |
| binding_evidence | 0.91 |


### #4 Ribociclib -> AML

**Score:** 0.901

| Strategy | Score |
|----------|-------|
| kan_extension | 0.90 |
| binding_evidence | 0.90 |


### #5 Imatinib -> AML

**Score:** 0.894

| Strategy | Score |
|----------|-------|
| kan_extension | 0.85 |
| composition | 0.75 |
| topos_logic | 0.67 |
| binding_evidence | 0.90 |

**Evidence chains:**

1. Imatinib -inhibits-> KIT -associated_with-> AML
   - Imatinib->KIT: [PMID:11309425](https://pubmed.ncbi.nlm.nih.gov/11309425) (confidence: 0.96)
   - KIT->AML: [PMID:11309425](https://pubmed.ncbi.nlm.nih.gov/11309425) (confidence: 0.75)
2. Imatinib -indirect_inhibitor-> AKT1 -activates-> BCL2 -associated_with-> AML
   - Imatinib->AKT1: [PMID:11309425](https://pubmed.ncbi.nlm.nih.gov/11309425) (confidence: 0.70)
   - AKT1->BCL2: [PMID:16461283](https://pubmed.ncbi.nlm.nih.gov/16461283) (confidence: 0.91)
   - BCL2->AML: [PMID:27103402](https://pubmed.ncbi.nlm.nih.gov/27103402) (confidence: 0.78)

**Provenance:** 5/5 chain edges cited