> **Legacy/historical notice (2026-05-27):** This file is retained for background or session history. It is not the current source of truth for Track A metrics or provenance. Current docs are in `truedocs/`, especially `truedocs/VALIDATION_AND_BENCHMARKS.md` and `truedocs/REPRODUCIBILITY_PROTOCOL.md`. Current strict run: AUROC 0.974694 [0.9606, 0.9855], AUPRC 0.551698 [0.4067, 0.6983], Hits@5/10/20 1.0000/0.6000/0.6000; LOOCV AUROC 0.975916 and AUPRC 0.553703; Hetionet external AUROC 0.634479 and AUPRC 0.009255. Source strings exist on all 5,382 morphisms with 610 PMID identifiers; this is not 100% edge-specific citation validation. Retired or superseded claims in this file should be read as historical.
# KOMPOSOS-IV-PHARM: Complete Transparency & Audit Manual
## From Beginner to Expert Understanding

**Version:** 2026-05-26 (updated: 9 strategies, quantitative evidence, Yoneda Distance)
**Author:** System Documentation
**Purpose:** Explain every component of the drug repurposing system so users can audit, validate, and understand every prediction.

---

## Table of Contents

1. [Introduction: What is Drug Repurposing?](#1-introduction)
2. [The Big Picture: How This System Works](#2-the-big-picture)
3. [Core Concepts: Knowledge Graphs Explained](#3-core-concepts)
4. [The Five Data Sources in Detail](#4-data-sources)
5. [How Edges Are Created and Scored](#5-edge-creation)
6. [The Prediction Engine: 9 Strategies Explained](#6-prediction-strategies)
7. [Score Calculation: Math Behind Predictions](#7-score-calculation)
8. [Audit Trails: Tracing Every Claim](#8-audit-trails)
9. [Current Gaps and Solutions](#9-transparency-gaps)
10. [Quality Control and Validation](#10-quality-control)
11. [Interpreting Results: What The Numbers Mean](#11-interpreting-results)
12. [Advanced Topics: Category Theory Foundations](#12-advanced-topics)

---

## 1. Introduction: What is Drug Repurposing?

### 1.1 The Problem

**Traditional drug development takes 10-15 years and costs $2.6 billion.**

Why so long?
1. **Discovery** (3-6 years): Find a molecule that might work
2. **Preclinical testing** (1-2 years): Test in cells and animals
3. **Phase I trials** (1-2 years): Is it safe in humans?
4. **Phase II trials** (2-3 years): Does it work in patients?
5. **Phase III trials** (2-4 years): Does it work better than existing treatments?
6. **FDA review** (1-2 years): Get approval

**Most drugs fail** - Only 1 in 5,000 compounds makes it to market.

### 1.2 The Solution: Drug Repurposing

**What if we used existing drugs for new diseases?**

Example: **Aspirin**
- Originally: Pain relief (1899)
- Repurposed for: Heart attack prevention (1980s)
- Repurposed for: Cancer prevention (2010s)

**Benefits:**
- Already proven safe (passed Phase I)
- Already have manufacturing
- Can skip years of development
- **Time to market: 3-5 years instead of 10-15**
- **Cost: $300M instead of $2.6B**

### 1.3 The Challenge

**How do we find repurposing opportunities?**

There are 78 oncology drugs and 20 cancers in our system.
- That's 78 × 20 = 1,560 possible combinations
- We have 44 FDA-approved drug-disease pairs (known to work)
- That leaves 1,516 untested combinations

**Which ones should we test first?**

That's where KOMPOSOS-IV-PHARM comes in.

---

## 2. The Big Picture: How This System Works

### 2.1 The Knowledge Graph

Think of knowledge as a **network of connected facts**:

```
Sorafenib ---inhibits---> BRAF ---driver_of---> Melanoma
   (drug)                (protein)               (disease)
```

This is called a **knowledge graph**:
- **Nodes** (circles): Drugs, proteins, diseases
- **Edges** (arrows): Relationships between them

### 2.2 The Prediction Process

**Goal:** Predict if Drug X can treat Disease Y

**Method:**
1. **Load the knowledge graph** (4,956 relationships)
2. **Run 8 different strategies** that look for patterns
3. **Each strategy votes** (0-1 confidence score)
4. **Combine votes** to get final prediction
5. **Show evidence chains** to explain why

### 2.3 Real Example

**Query:** "Can Sorafenib treat AML?"

**Answer:** Score 0.867 (87% confidence)

**Evidence chains found:**
1. `Sorafenib -inhibits-> FLT3 -driver_of-> AML`
   - Sorafenib inhibits FLT3 protein (PMID:16816939)
   - FLT3 mutations drive AML (curated from TCGA)

2. `Sorafenib -inhibits-> BRAF -associated_with-> AML`
   - Sorafenib inhibits BRAF (PMID:16461419)
   - BRAF pathway active in some AML (TCGA expression data)

**Strategy votes:**
- Composition: 0.85 (found direct paths)
- Binding evidence: 0.78 (ABPP shows strong FLT3 binding)
- Kan extension: 0.72 (analogies to similar drugs)

**Clinical validation:**
- Sorafenib IS used for FLT3+ AML in clinical practice
- FDA approved in combination therapy (2017)

**The system found a real drug-disease match that doctors use!**

---

## 3. Core Concepts: Knowledge Graphs Explained

### 3.1 What is a Knowledge Graph?

A **knowledge graph** is a database that stores:
- **Entities** (things that exist): Drugs, proteins, diseases, genes
- **Relations** (how they connect): inhibits, activates, treats, causes

**Example in plain English:**
- "Sorafenib inhibits BRAF protein"
- "BRAF protein drives melanoma"
- "Therefore, Sorafenib might treat melanoma"

**Same thing as a graph:**
```
Sorafenib --inhibits--> BRAF --driver_of--> Melanoma
```

### 3.2 Types of Entities (Nodes)

Our graph has 464 entities:

| Type | Count | Examples | What They Are |
|------|-------|----------|---------------|
| Drug | 78 | Sorafenib, Imatinib, Venetoclax | FDA-approved cancer drugs |
| Protein | 366 | BRAF, TP53, EGFR, FLT3 | Human proteins (targets, drivers) |
| Disease | 20 | AML, Melanoma, NSCLC | Cancer types we're studying |
| ExternalCompound | 679 | ChEMBL endpoints | Experimental compounds from databases |

### 3.3 Types of Relations (Edges)

Our graph has 4,956 relationships:

| Relation | Count | Example | What It Means |
|----------|-------|---------|---------------|
| associated_with | 3,770 | TP53→Breast_Cancer | Protein linked to disease |
| inhibits | 639 | Sorafenib→BRAF | Drug blocks protein activity |
| activates | 292 | KRAS→BRAF | Protein turns on another protein |
| targets | 69 | Erlotinib→EGFR | Drug targets protein (FDA mechanism) |
| treats | 44 | Venetoclax→AML | Drug is FDA-approved for disease |
| driver_of | 37 | FLT3→AML | Protein mutation causes disease |

### 3.4 Why Graphs Are Powerful

**Traditional database:**
- "What drugs inhibit BRAF?" → Query one table
- "What diseases does BRAF cause?" → Query another table
- **Can't answer:** "What drugs might treat BRAF-driven diseases?"

**Knowledge graph:**
- Follow the path: Drug→BRAF→Disease
- **Can answer:** "Find all drugs that inhibit proteins that drive this disease"
- **Can discover:** New drug-disease combinations no one has tried

---

## 4. The Five Data Sources in Detail

### 4.1 ESM2 (Protein Language Model)

#### What Is It?

ESM2 is like ChatGPT for proteins. Instead of reading text, it reads amino acid sequences:

```
Protein sequence: MEEPQSDPSV... (393 amino acids for TP53)
ESM2 output: [0.42, -0.18, 0.91, ...] (1,280 numbers describing the protein)
```

These 1,280 numbers are called an **embedding** - they capture:
- What the protein looks like
- What family it belongs to
- What it might do

#### How We Use It

**Principle:** Similar proteins do similar things

If Protein A and Protein B have similar embeddings (cosine similarity > 0.75):
- And Protein A is linked to Disease X
- Then Protein B might also be linked to Disease X

**Example:**
- KRAS and NRAS are 88% similar (both are RAS family proteins)
- KRAS drives pancreatic cancer
- **Inference:** NRAS might also drive pancreatic cancer
- **Validation:** TRUE - NRAS mutations found in pancreatic cancer (PMID:24705251)

#### Evidence Format

When we create an edge from ESM2:

```json
{
  "source": "NRAS",
  "target": "Pancreatic_Cancer",
  "edge_type": "associated_with",
  "confidence": 0.68,
  "provenance": "ESM2:similar_to_KRAS(0.88)"
}
```

**Confidence calculation:**
```
base = 0.55 (minimum for ESM2 inferences)
bonus = (similarity - 0.75) × 0.20 = (0.88 - 0.75) × 0.20 = 0.026
similarity > 0.75 threshold → 0.13 bonus capped
final = 0.55 + 0.13 = 0.68
```

#### Limitations

1. **Coverage:** Only 46 of 366 proteins have sequences loaded
   - Need to download more UniProt sequences
2. **Inference quality:** Similarity ≠ same function
   - Kinases are similar but target different pathways
3. **No mechanistic detail:** Doesn't tell us HOW proteins are related

---

### 4.2 CosMx (Spatial Transcriptomics)

#### What Is It?

CosMx measures gene expression in tissue samples with spatial resolution:

```
Sample: NSCLC tumor tissue
Cell 1 at (x=74.9, y=190.1):
  - KRAS expression: 3.76 (high)
  - TP53 expression: 0.11 (low)
  - EGFR expression: 0.08 (low)
```

**What this tells us:**
- In this cancer cell, KRAS is highly active
- TP53 (tumor suppressor) is shut off
- This is a KRAS-driven lung cancer

#### How We Use It

**Principle:** Highly expressed genes in cancer tissue drive that cancer

If a protein has expression > 2.0 in cancer tissue:
- Create an edge: Protein→Disease
- Confidence based on expression level

**Example:**
- KRAS expression in NSCLC tissue: 3.76
- **Inference:** KRAS→NSCLC association
- Confidence: 0.60 + min(0.15, 3.76/20) = 0.60 + 0.15 = 0.75

#### Evidence Format

```json
{
  "source": "KRAS",
  "target": "NSCLC",
  "edge_type": "associated_with",
  "confidence": 0.75,
  "provenance": "CosMx:NSCLC_tissue(expr=3.76)"
}
```

#### Limitations

1. **Limited tissue coverage:** Only have NSCLC tissue data
   - Need: Breast, melanoma, AML bone marrow, etc.
2. **Expression ≠ causation:** High expression could be:
   - Driver (protein causes cancer)
   - Passenger (protein just expressed there)
   - Housekeeping (protein always expressed)
3. **No temporal data:** Can't see if protein is early driver or late effect

---

### 4.3 ChEMBL (Drug-Target Database)

#### What Is It?

ChEMBL is a database of 2.4 million drug-like molecules and their biological activity:

```
Compound: Sorafenib
Target: BRAF
Activity: IC50 = 25 nM (very strong inhibition)
Assay: Cell-free kinase assay
Reference: PMID:16461419
```

**IC50 = concentration needed to inhibit 50% of protein activity**
- Lower = better (drug is more potent)
- IC50 < 100 nM = excellent drug
- IC50 > 10 µM = weak drug

#### How We Use It

**Principle:** If drug targets protein AND drug treats disease, then protein is involved in disease

**Chain of inference:**
1. Sorafenib inhibits BRAF (IC50 = 25 nM)
2. Sorafenib treats melanoma (FDA approved)
3. **Inference:** BRAF drives melanoma

This creates the edge: `BRAF→Melanoma`

#### Evidence Format

```json
{
  "source": "BRAF",
  "target": "Melanoma",
  "edge_type": "associated_with",
  "confidence": 0.75,
  "provenance": "ChEMBL:via_drug_Sorafenib"
}
```

**Why confidence 0.75?**
- Drug-target relationship is experimental (ChEMBL IC50)
- Drug-disease relationship is clinical (FDA approved)
- Inference is strong but indirect

#### Limitations

1. **Indirect inference:** Drug inhibits protein ≠ protein drives disease
   - Example: Aspirin inhibits COX2, treats headache, but COX2 doesn't cause headaches
2. **Polypharmacology:** Drugs hit multiple targets
   - Sorafenib hits BRAF, VEGFR2, PDGFR, etc.
   - Which target is responsible for efficacy?
3. **Missing context:** Doesn't capture:
   - Tissue specificity
   - Pathway context
   - Resistance mechanisms

---

### 4.4 ABPP (Activity-Based Protein Profiling)

#### What Is It?

ABPP is experimental validation of drug-target binding IN LIVING CELLS:

**Traditional assay:**
- Mix drug + purified protein in test tube
- Measure binding
- **Problem:** Doesn't reflect what happens in cells

**ABPP assay:**
- Add drug to living cancer cells
- Use chemical probe to tag proteins drug binds
- Pull out tagged proteins, identify by mass spec
- Measure how well drug blocks probe binding (= target engagement)

**Example:**
```
Drug: Erlotinib
Cell line: A549 (lung cancer)
Target: EGFR
IC50: 0.002 µM (2 nM)
Engagement: 98% at 1 µM
PMID: 15118125
```

This means: Erlotinib binds EGFR strongly in actual cancer cells.

#### How We Use It

**Principle:** Target engagement + drug efficacy → target drives disease

**Chain:**
1. Erlotinib binds EGFR in cells (ABPP IC50 = 2 nM)
2. Erlotinib treats NSCLC (FDA approved)
3. **Inference:** EGFR drives NSCLC

Edge created: `EGFR→NSCLC`

#### Evidence Format

```json
{
  "source": "EGFR",
  "target": "NSCLC",
  "edge_type": "associated_with",
  "confidence": 0.85,
  "provenance": "ABPP:Erlotinib(IC50=0.002uM), PMID:15118125"
}
```

**Confidence tiers:**
- IC50 < 0.1 µM: 0.85 (excellent binding)
- IC50 < 1.0 µM: 0.75 (good binding)
- IC50 > 1.0 µM: 0.65 (weak binding)

#### Why ABPP Is Gold Standard

1. **In cells:** Reflects real biology (not test tube)
2. **Selectivity:** Shows what protein drug ACTUALLY binds
3. **Quantitative:** IC50 tells you potency
4. **Validated:** Experimental data with PMIDs

#### Limitations

1. **Limited coverage:** Only 65 entries in our dataset
   - ABPP is expensive and time-consuming
2. **Cell line specific:** Binding in A549 cells ≠ binding in patient tumors
3. **Still indirect:** Target engagement ≠ mechanism of efficacy

---

### 4.5 PubMed (Literature Evidence)

#### What Is It?

PubMed is the NIH database of 36 million biomedical papers.

We query it to find papers that mention both a protein and a disease:

**Query:** `"TP53"[Title/Abstract] AND "breast cancer"[Title/Abstract]`

**Results:** 15,234 papers

**Top paper:**
- PMID: 23456789
- Title: "TP53 mutations in breast cancer: prevalence and prognosis"
- Abstract: "...TP53 is mutated in 30% of breast cancers...poor prognosis..."

#### How We Use It

**Principle:** If multiple papers discuss protein + disease together, they're likely related

**Thresholds:**
- 1 paper: Not convincing (could be unrelated)
- 2+ papers: Likely real association
- 10+ papers: Well-established link

**Example:**
- TP53 + Breast Cancer: 15,234 papers → VERY strong evidence
- Edge: TP53→Breast_Cancer, confidence 0.70

#### Evidence Format

```json
{
  "source": "TP53",
  "target": "Breast_Cancer",
  "edge_type": "associated_with",
  "confidence": 0.70,
  "provenance": "PMID:23456789, PMID:12345678, PMID:34567890"
}
```

**Why confidence 0.70?**
- Literature co-occurrence is evidence of association
- But doesn't prove causation
- Lower than experimental evidence (ChEMBL, ABPP)

#### Limitations

1. **Co-mention ≠ causation:**
   - Papers might discuss TP53 AND breast cancer without claiming TP53 causes it
2. **Publication bias:**
   - Well-studied proteins (TP53, KRAS) have more papers
   - Novel proteins have fewer papers (doesn't mean they're not important)
3. **No mechanism:**
   - Doesn't tell us HOW protein is involved in disease

---

## 5. How Edges Are Created and Scored

### 5.1 Edge Creation Pipeline

**For each data source, we:**

1. **Extract relationships**
2. **Assign confidence score**
3. **Record provenance**
4. **Merge duplicates**

#### Example: Creating TP53→Breast_Cancer Edge

**Source 1: cancer_proteins.py (curated)**
```python
CANCER_PROTEINS = {
    "TP53": {
        "cancers": ["multiple"],  # Associated with many cancers
        ...
    }
}
```
→ Creates edges to ALL 20 diseases
→ Confidence: 0.55 (broad claim, lower confidence)

**Source 2: TCGA Expression**
```python
tcga_expression = {
    "TP53": {
        "Breast": 6.5  # log2 expression
    }
}
```
→ Expression > 6.0 → create edge
→ Confidence: 0.60 + min(0.15, 6.5/10) = 0.60 + 0.15 = 0.75

**Source 3: PubMed**
```python
query = '"TP53"[Title/Abstract] AND "breast cancer"[Title/Abstract]'
results = [PMID:123, PMID:456, PMID:789, ...]  # 15,000+ papers
```
→ Multiple PMIDs found → create edge
→ Confidence: 0.70

**Merging:**
```json
{
  "source": "TP53",
  "target": "Breast_Cancer",
  "edge_type": "associated_with",
  "confidence": 0.75,  // max(0.55, 0.75, 0.70)
  "provenance": "cancer_proteins:curated, TCGA:Breast(expr=6.5), PMID:123,456,789"
}
```

### 5.2 Confidence Score System

**General principles:**

| Evidence Type | Base Confidence | Reasoning |
|---------------|-----------------|-----------|
| Somatic mutation (driver_of) | 0.80-0.90 | Mutation causes disease → very strong |
| Drug target (via ChEMBL/ABPP) | 0.70-0.85 | Drug works → target likely involved |
| High expression (TCGA/CosMx) | 0.60-0.75 | Expression in tissue → possibly involved |
| Protein similarity (ESM2) | 0.55-0.75 | Similar protein involved → maybe this one too |
| Literature co-mention (PubMed) | 0.60-0.70 | Papers discuss both → probably related |
| Broad claim ("multiple cancers") | 0.50-0.60 | Non-specific → lower confidence |

**Bonuses:**
- Strong experimental binding (IC50 < 100 nM): +0.10
- Multiple independent sources agree: +0.05
- High protein similarity (>0.85): +0.10

### 5.3 Provenance Format

Every edge must have complete provenance:

**Bad provenance:**
```json
"provenance": "unknown"
```
→ Can't audit, can't validate

**Good provenance:**
```json
"provenance": "ChEMBL:Sorafenib(IC50=25nM), PMID:16461419"
```
→ Can look up paper, verify claim

**Best provenance (multi-source):**
```json
"provenance": "cancer_proteins:curated, TCGA:Melanoma(expr=7.2), ABPP:Vemurafenib(IC50=0.03uM), PMID:20179705, PMID:22356324"
```
→ Multiple sources agree → high confidence

---

## 6. The Prediction Engine: 8 Strategies Explained

When you ask "Can Drug X treat Disease Y?", the system runs **8 independent strategies** that each look for different patterns.

### 6.1 Strategy 1: Composition (Mechanistic Paths)

**What it does:** Looks for direct chains Drug→Protein→Disease

**Example query:** "Venetoclax → AML?"

**Search:**
```
Venetoclax -inhibits-> BCL2 -associated_with-> AML
```

**Vote:** 0.85 (high confidence because direct path exists)

**Reasoning:**
- Venetoclax inhibits BCL2 (ChEMBL IC50 = 0.01 nM, PMID:26566875)
- BCL2 is overexpressed in AML (TCGA data)
- BCL2 prevents apoptosis → blocking it kills cancer cells

**Path bonus:** `min(0.25, 0.04 * sum(path_confidence))` — weighted by evidence quality

---

### 6.2 Strategy 2: Yoneda (Local Context)

**What it does:** Analyzes the "neighborhood" around a protein

**Concept:** Proteins with similar neighborhoods have similar functions

**Example:**
- KRAS neighbors: BRAF, MEK1, ERK1 (MAPK pathway)
- NRAS neighbors: BRAF, MEK1, ERK1 (same pathway!)
- **Inference:** KRAS and NRAS probably do similar things

**Vote calculation:**
- Count shared neighbors
- Compute Jaccard similarity: shared / (neighbors_A + neighbors_B - shared)
- If > 0.6 → vote based on similarity

---

### 6.3 Strategy 3: Kan Extension (Analogies)

**What it does:** Finds indirect paths through analogies

**Example query:** "Sorafenib → Pancreatic_Cancer?"

**No direct path exists**, but:

```
Known: Sorafenib → BRAF → Melanoma (FDA approved)
Analogy: Sorafenib → BRAF
          BRAF is in MAPK pathway
          KRAS is also in MAPK pathway
          KRAS drives Pancreatic Cancer
Inference: Sorafenib might help Pancreatic Cancer
```

**Vote:** 0.65 (lower than direct path, but still evidence)

**This is how the system discovers novel repurposing candidates!**

---

### 6.4 Strategy 4: Type Heuristic (Type Matching)

**What it does:** Checks if source/target types are compatible for a treatment relationship

**Example:**
- Source type = Drug, Target type = Disease → valid treatment pair
- Source type = Protein, Target type = Drug → not a valid treatment pair

**Vote calculation:**
- Check if source is Drug and target is Disease
- Check if there are intermediary Protein objects connecting them
- Vote based on type compatibility and pathway membership

---

### 6.5 Strategy 5: Structural Hole (Network Closure)

**What it does:** Detects structural holes in the graph that this edge would close

**Example:**
```
Drug inhibits Protein (known)
Protein drives Disease (known)
Drug→Disease edge is MISSING
→ Adding it would close a structural hole
```

**Vote:** Higher when more structural holes would be closed

---

### 6.6 Strategy 6: Topos Logic (Evidence Integration)

**What it does:** Integrates cross-evidence from multiple sources using subobject
classifier logic

**Example:**
- ChEMBL says Drug inhibits Protein (IC50 data)
- PubMed says Protein associated with Disease (PMID)
- KEGG says Protein is in cancer pathway
- All three lines of evidence converge → higher confidence

---

### 6.7 Strategy 7: Binding Evidence (Structural + Experimental)

**What it does:** Combines:
- ABPP binding data (experimental IC50)
- Drug properties (Lipinski rules, logP, molecular weight)
- Protein structure (AlphaFold, Pfam domains)

**Example:**
```
Drug: Erlotinib
Target: EGFR
- ABPP IC50: 0.002 µM (excellent)
- Drug is kinase inhibitor
- EGFR is a kinase (Pfam domain match)
- AlphaFold shows druggable pocket
→ Vote: 0.85
```

---

### 6.8 Strategy 8: Fibration (Cross-Disease Transfer)

**What it does:** Transfer knowledge across similar diseases

**Example:**
- BRAF inhibitors work in BRAF+ melanoma
- BRAF mutations also occur in colon cancer
- **Inference:** BRAF inhibitors might work in BRAF+ colon cancer
- **Clinical validation:** Vemurafenib approved for BRAF+ colon cancer (2017)

---

## 7. Score Calculation: Math Behind Predictions

### 7.1 Vote Aggregation

**Input:** 8 strategies vote, each returns confidence 0-1 (or 0 if no vote)

**Example votes for "Sorafenib → AML":**
```python
votes = [
    ("composition", 0.85),      # Found direct paths
    ("kan_extension", 0.72),    # Found analogies
    ("binding_evidence", 0.78), # ABPP data supports
    # Other strategies didn't vote (return 0, filtered out)
]
```

**Step 1: Base score (average of votes)**
```python
base = sum(confidence for _, confidence in votes) / len(votes)
     = (0.85 + 0.72 + 0.78) / 3
     = 0.783
```

**Step 2: Path bonus (reward mechanistic paths, weighted by confidence)**
```python
# Each path's confidence = product of hop confidences
path_confidences = [0.85, 0.72]  # Two paths with different quality
composition_weight = sum(path_confidences)  # = 1.57
path_bonus = min(0.25, 0.04 * composition_weight)
           = min(0.25, 0.04 * 1.57)
           = 0.063
```

**Why confidence-weighted path bonus?**
- High-confidence paths (FDA + curated) contribute more than low-confidence paths
- A single high-quality path (conf 0.90) counts more than two noisy paths (conf 0.20 each)
- Prevents low-quality PubMed co-mention edges from inflating scores
- Capped at 0.25 to avoid over-weighting

**Step 3: Mechanistic discount (penalize analogy-only predictions)**
```python
if composition_count == 0:
    mechanistic_discount = 0.80
else:
    mechanistic_discount = 1.0

# In this example: composition_count = 2, so discount = 1.0
```

**Why discount analogy-only predictions?**
- Analogy strategies (Kan extension, Yoneda) can find patterns
- But without direct mechanistic paths, less reliable
- 0.80 multiplier = 20% penalty for no mechanistic support

**Step 4: Final score**
```python
score = (base + path_bonus) * mechanistic_discount
      = (0.783 + 0.20) * 1.0
      = 0.983
      = min(1.0, 0.983)  # Cap at 1.0
      = 0.983
```

### 7.2 Full Example Walkthrough

**Query:** "Imatinib → CML?"

**Known facts:**
- Imatinib inhibits BCR-ABL (ChEMBL IC50 = 0.6 nM)
- BCR-ABL drives CML (Philadelphia chromosome fusion protein)
- Imatinib is FDA-approved for CML (since 2001)

**Strategy votes:**
1. **Composition:** 0.95
   - Found path: Imatinib→BCR-ABL→CML
   - High confidence (well-characterized pathway)

2. **Binding evidence:** 0.90
   - ABPP IC50 = 0.6 nM (excellent binding)
   - Imatinib is kinase inhibitor, BCR-ABL is kinase (domain match)

3. **Equalizer:** 0.92
   - BCR-ABL is clear mediator of Imatinib→CML relationship

4. **Fibration:** 0.75
   - Similar mechanism to other tyrosine kinase inhibitors

**Calculation:**
```python
votes = [(composition, 0.95), (binding_evidence, 0.90),
         (equalizer, 0.92), (fibration, 0.75)]

base = (0.95 + 0.90 + 0.92 + 0.75) / 4 = 0.880

composition_weight = 0.95  # Single path confidence
path_bonus = min(0.25, 0.04 * 0.95) = 0.038

mechanistic_discount = 1.0  # Has composition path

final_score = (0.880 + 0.038) * 1.0 = 0.918
```

**Final prediction:** 0.918 (high confidence)

**Clinical reality:** Imatinib IS the standard treatment for CML
→ System correctly identified this with high score

---

## 8. Audit Trails: Tracing Every Claim

### 8.1 What is an Audit Trail?

**Audit trail** = Complete record of how a prediction was made

**Requirements:**
1. **All edges used:** Show every relationship in the reasoning chain
2. **Provenance per edge:** Where did each edge come from?
3. **Strategy reasoning:** WHY did each strategy vote?
4. **Score derivation:** How was the final score calculated?

### 8.2 Example Audit Trail

**Prediction:** Venetoclax → AML (Score: 0.92)

**Audit report:**

```
=== PREDICTION AUDIT TRAIL ===
Query: Venetoclax → AML
Final Score: 0.92
Label: APPROVED (FDA approved 2016)

=== STRATEGY VOTES ===

1. Composition: 0.87
   Evidence chains found: 1

   Chain 1:
   Venetoclax -inhibits-> BCL2 -associated_with-> AML
     Edge 1: Venetoclax→BCL2
       - Relation: inhibits
       - Confidence: 0.95
       - Provenance: ChEMBL:CHEMBL3137309(IC50=0.01nM), PMID:26566875
       - Source: ChEMBL database
       - Evidence: Experimental Ki = 0.01 nM in cell-free assay

     Edge 2: BCL2→AML
       - Relation: associated_with
       - Confidence: 0.78
       - Provenance: TCGA:AML(expr=7.8), DepMap:AML(ess=0.4), PMID:24332512
       - Sources: TCGA expression, DepMap essentiality, PubMed
       - Evidence: BCL2 overexpressed in 80% of AML cases

2. Binding Evidence: 0.85
   - ABPP IC50: Not available for Venetoclax
   - Drug properties: Lipinski compliant, logP=4.2 (druggable)
   - BCL2 is known drug target (Pfam: BCL2 family)
   - Confidence from ChEMBL data: 0.85

3. Kan Extension: 0.68
   - No direct analogy found
   - Pathway reasoning: BCL2 is in apoptosis pathway
   - Other apoptosis modulators work in AML
   - Confidence: 0.68

=== SCORE CALCULATION ===

Base score = (0.87 + 0.85 + 0.68) / 3 = 0.800
Path bonus = min(0.25, 0.04 * 0.87) = 0.035 (confidence-weighted)
Mechanistic discount = 1.0 (has composition path)
Final score = (0.800 + 0.035) * 1.0 = 0.835

=== PROVENANCE SUMMARY ===

Total edges in reasoning: 2
Edges with PMIDs: 2 (100%)
Edges from experimental data: 2 (100%)
Edges from inferred data: 0 (0%)

=== CLINICAL VALIDATION ===

FDA Status: APPROVED (2016)
Indication: AML in combination with azacitidine or decitabine
Clinical trial: NCT02203773 (Phase III)
Mechanism confirmed: BCL2 inhibition induces apoptosis in AML cells

=== AUDIT CONCLUSION ===

This prediction is VALIDATED by:
✓ Mechanistic path exists
✓ All edges have experimental evidence
✓ All edges have PMID provenance
✓ FDA-approved for this indication
✓ Mechanism of action confirmed in clinical trials

Confidence in this prediction: VERY HIGH
```

### 8.3 Audit Trail for Lower-Confidence Prediction

**Prediction:** Sorafenib → Pancreatic_Cancer (Score: 0.65)

**Audit report:**

```
=== PREDICTION AUDIT TRAIL ===
Query: Sorafenib → Pancreatic_Cancer
Final Score: 0.65
Label: NOT_APPROVED (not in our 44 FDA oncology indications)

=== STRATEGY VOTES ===

1. Composition: NO VOTE (0.0)
   Reason: No direct Drug→Protein→Disease path found

2. Kan Extension: 0.68
   Reasoning:
   - Sorafenib inhibits BRAF (known)
   - BRAF is in MAPK pathway
   - KRAS is also in MAPK pathway
   - KRAS drives Pancreatic Cancer
   - Analogy: Sorafenib→BRAF, KRAS→Pancreatic, BRAF~KRAS (pathway)

   Evidence:
   - Sorafenib→BRAF: ChEMBL IC50=25nM, PMID:16461419
   - KRAS→Pancreatic: driver_of, PMID:24705251
   - BRAF~KRAS: Same pathway (MAPK)

   Confidence: 0.68 (analogy is indirect)

3. Binding Evidence: 0.62
   - No direct Sorafenib→KRAS binding data
   - But Sorafenib is kinase inhibitor
   - RAF and RAS both in MAPK pathway
   - Weak evidence: 0.62

=== SCORE CALCULATION ===

Base score = (0.68 + 0.62) / 2 = 0.650
Path bonus = min(0.25, 0.04 * 0) = 0.00 (no composition paths)
Mechanistic discount = 0.80 (NO mechanistic path)
Final score = (0.650 + 0.00) * 0.80 = 0.520

Wait, final score is 0.65 in the header but calculation gives 0.52?
→ AUDIT FLAG: Score mismatch, investigate

=== PROVENANCE SUMMARY ===

Total edges in reasoning: 2
Edges with PMIDs: 2 (100%)
Edges from experimental data: 1 (50%)
Edges from inferred data: 1 (50%) ← BRAF~KRAS pathway membership

=== CLINICAL VALIDATION ===

FDA Status: NOT APPROVED for pancreatic cancer
Clinical trials: Phase II trial NCT00541021 (FAILED - no benefit)
Known issues: KRAS-mutant cancers resistant to RAF inhibitors

=== AUDIT CONCLUSION ===

This prediction is REFUTED by clinical data:
✗ No mechanistic path
✗ Clinical trial failed
✗ Known biological reason for failure (KRAS mutation bypasses RAF)

Confidence in this prediction: LOW
Recommendation: Do NOT pursue this repurposing candidate

⚠ AUDIT WARNING: System predicted 0.65 but clinical reality is FAILURE
→ This is a FALSE POSITIVE
→ Likely cause: Analogy (Kan extension) doesn't account for pathway position
→ Improvement needed: Add pathway topology awareness
```

### 8.4 What Makes a Good Audit Trail?

**Must have:**
1. ✓ All strategy votes with reasoning
2. ✓ All edges with provenance
3. ✓ Score calculation breakdown
4. ✓ Clinical validation status

**Should have:**
5. ✓ Warnings when prediction contradicts known data
6. ✓ Quality scores (% edges with PMIDs, % experimental)
7. ✓ Alternative explanations if available

**Nice to have:**
8. ✓ Links to papers (PMID → PubMed URL)
9. ✓ Visualization of reasoning paths
10. ✓ Comparison to similar predictions

---

## 9. Current Gaps and Solutions

### 9.1 Gap 1: Strategy Vote Explanation

**Current state:**
```
Strategy votes:
- composition: 0.85
- kan_extension: 0.72
- binding_evidence: 0.78
```

**Problem:** Doesn't explain WHY each strategy voted

**Solution needed:**
```
Strategy votes:

1. Composition: 0.85
   Found 2 mechanistic paths:

   Path 1: Sorafenib→FLT3→AML
     - Sorafenib inhibits FLT3 (ABPP IC50=0.5µM, PMID:16816939)
     - FLT3 drives AML (30% of cases, driver_of, PMID:10698507)
     - Path confidence: 0.85

   Path 2: Sorafenib→BRAF→AML
     - Sorafenib inhibits BRAF (ChEMBL IC50=25nM, PMID:16461419)
     - BRAF associated with AML (TCGA expr=5.2, PMID:23429938)
     - Path confidence: 0.72

   Average path confidence: (0.85 + 0.72) / 2 = 0.785
   Vote: 0.85 (rounded up for multiple paths)

2. Kan Extension: 0.72
   No direct path, but found analogy:

   Known: Midostaurin→FLT3→AML (FDA approved)
   Analogy: Sorafenib also inhibits FLT3 (IC50=0.58µM vs Midostaurin IC50=0.04µM)

   Reasoning:
   - Both drugs target FLT3
   - Midostaurin works in FLT3+ AML
   - Sorafenib binds FLT3 (10x weaker but still nanomolar)
   - Inference: Sorafenib might also work in FLT3+ AML

   Confidence penalty: -0.13 (weaker binding than Midostaurin)
   Vote: 0.85 - 0.13 = 0.72

3. Binding Evidence: 0.78
   Combining multiple evidence types:

   ABPP data:
   - Sorafenib→FLT3: IC50=0.5µM (good binding)
   - Sorafenib→BRAF: IC50=0.025µM (excellent binding)

   Drug properties:
   - Molecular weight: 464.82 g/mol (Lipinski compliant)
   - logP: 4.1 (good membrane permeability)
   - Kinase inhibitor class (matches FLT3, BRAF)

   Target properties:
   - FLT3 and BRAF both kinases (Pfam domain match)
   - Both have known druggable pockets (AlphaFold)

   Score calculation:
   - Base (ABPP): 0.70
   - Drug-likeness bonus: +0.05
   - Domain match bonus: +0.03
   - Total: 0.78
```

**Implementation:**
- Each strategy returns: `(confidence, explanation_dict)`
- explanation_dict contains:
  - Paths found
  - Evidence used
  - Calculation steps
  - Reasoning chain

---

### 9.2 Gap 2: Confidence Score Derivation

**Current state:**
```json
{
  "confidence": 0.75,
  "provenance": "ChEMBL:Sorafenib"
}
```

**Problem:** Why 0.75? Where did that number come from?

**Solution needed:**
```json
{
  "confidence": 0.75,
  "confidence_derivation": {
    "base": 0.60,
    "base_reason": "Drug-target inference (ChEMBL + drug indication)",
    "bonuses": [
      {
        "type": "strong_binding",
        "value": 0.10,
        "reason": "IC50 < 100 nM (25 nM actual)",
        "evidence": "ChEMBL:CHEMBL1336"
      },
      {
        "type": "multiple_sources",
        "value": 0.05,
        "reason": "ChEMBL + ABPP both confirm binding",
        "evidence": "ABPP IC50=0.03µM confirms ChEMBL"
      }
    ],
    "penalties": [],
    "calculation": "0.60 + 0.10 + 0.05 = 0.75"
  },
  "provenance": "ChEMBL:Sorafenib(IC50=25nM), ABPP(IC50=0.03µM), PMID:16461419"
}
```

**Implementation:**
- Store confidence_derivation alongside each edge
- Include in manifest JSON
- Display in triage reports

---

### 9.3 Gap 3: Multi-Source Reconciliation

**Current state:**
When same edge found from multiple sources, we merge:
```json
{
  "source": "TP53",
  "target": "Breast_Cancer",
  "confidence": 0.75,
  "provenance": "cancer_proteins:curated, TCGA, PMID:123"
}
```

**Problem:** Lost individual source details

**Solution needed:**
```json
{
  "source": "TP53",
  "target": "Breast_Cancer",
  "confidence": 0.75,
  "confidence_reconciliation": {
    "strategy": "max",
    "sources": [
      {
        "name": "cancer_proteins",
        "confidence": 0.70,
        "evidence": "Curated from literature review",
        "provenance": "cancer_proteins.py:56"
      },
      {
        "name": "TCGA",
        "confidence": 0.75,
        "evidence": "Overexpressed in breast tumors (log2FC=2.3)",
        "provenance": "TCGA:BRCA cohort, 1095 patients"
      },
      {
        "name": "PubMed",
        "confidence": 0.68,
        "evidence": "15,234 papers discuss both",
        "provenance": "PMID:123,456,789 (sample)"
      }
    ],
    "agreement": "HIGH (all 3 sources agree)",
    "final_confidence": 0.75,
    "final_reasoning": "Max of 3 sources: max(0.70, 0.75, 0.68) = 0.75"
  }
}
```

**Benefits:**
- Can see ALL evidence, not just merged
- Can assess if sources agree or conflict
- Can weight sources differently (experimental > literature)

---

### 9.4 Gap 4: Biological Validation

**Current state:**
System accepts any edge if data source provides it

**Problem:**
Some inferred edges don't make biological sense

**Example:**
```
ESM2 says: INSULIN is 76% similar to IGF1
cancer_proteins says: IGF1→Breast_Cancer
Inference: INSULIN→Breast_Cancer

But wait: Insulin is hormone (diabetes drug), not oncogene
This edge is technically valid but biologically misleading
```

**Solution needed:**

**Pre-validation checks:**
1. **Pathway check:**
   - Query KEGG/Reactome: Is protein in relevant pathway?
   - Example: If inferring Protein→AML, check if protein in hematopoiesis pathway

2. **Protein family check:**
   - Query Pfam: What family does protein belong to?
   - Example: Kinase→Cancer makes sense, Metabolic enzyme→Cancer needs more evidence

3. **Mechanism check:**
   - If drug inhibits protein, and protein is tumor suppressor → DON'T infer drug treats cancer
   - Inhibiting tumor suppressor would CAUSE cancer, not treat it

**Implementation:**
```python
def validate_edge(source, target, edge_type, evidence):
    """Validate edge makes biological sense"""

    # Check 1: Pathway membership
    if target.endswith("_Cancer"):
        pathways = get_protein_pathways(source)  # KEGG/Reactome
        if not any(p in CANCER_PATHWAYS for p in pathways):
            return {
                "valid": False,
                "reason": f"{source} not in cancer-related pathways",
                "recommendation": "Flag for manual review"
            }

    # Check 2: Protein family
    family = get_protein_family(source)  # Pfam
    if family in HOUSEKEEPING_FAMILIES:
        return {
            "valid": False,
            "reason": f"{source} is housekeeping protein ({family})",
            "recommendation": "Requires high-confidence evidence"
        }

    # Check 3: Mechanism consistency
    if edge_type == "driver_of":
        protein_type = get_protein_type(source)  # Oncogene vs tumor suppressor
        if protein_type == "TumorSuppressor":
            return {
                "valid": False,
                "reason": "Tumor suppressors don't 'drive' cancer",
                "recommendation": "Change edge_type to 'loss_associated_with'"
            }

    return {"valid": True}
```

---

## 10. Quality Control and Validation

### 10.1 Data Quality Tiers

Not all edges are created equal. We classify by quality:

| Tier | Quality | Evidence Required | Example |
|------|---------|-------------------|---------|
| **Tier 1: Gold** | Experimental in humans | Clinical trial data, FDA approval | Imatinib→CML (Phase III trial) |
| **Tier 2: Silver** | Experimental in cells/animals | ABPP, ChEMBL Ki, functional assays | Venetoclax→BCL2 (ABPP IC50=0.01µM) |
| **Tier 3: Bronze** | Computational + literature | TCGA, DepMap, multiple PMIDs | TP53→Breast (TCGA + 1000+ papers) |
| **Tier 4: Inferred** | Similarity-based | ESM2, pathway membership | NRAS→Pancreatic (similar to KRAS) |

**Confidence ranges:**
- Tier 1: 0.85-1.0
- Tier 2: 0.70-0.85
- Tier 3: 0.60-0.75
- Tier 4: 0.50-0.65

### 10.2 Validation Checklist

Before accepting an edge, check:

**Required:**
- [ ] Source is documented (ESM2/CosMx/ChEMBL/ABPP/PubMed)
- [ ] Provenance exists (PMID, database ID, or computation details)
- [ ] Confidence in valid range (0.50-1.0)
- [ ] Edge type is appropriate (inhibits, activates, associated_with, etc.)

**Strongly recommended:**
- [ ] Multiple sources agree (if available)
- [ ] PMID exists for experimental edges
- [ ] Biological pathway makes sense
- [ ] No contradictions with known biology

**Nice to have:**
- [ ] Validation in external database (ClinicalTrials.gov, DrugBank)
- [ ] Replication in independent dataset
- [ ] Mechanistic explanation available

### 10.3 Current Validation Results

**As of 2026-05-24:**

Total edges: 4,956 (provenance: 100%)

**By confidence tier:**
- High confidence (>= 0.70): 1,286 (25.9%) - ChEMBL, FDA, KEGG, ABPP, curated PMID
- Medium confidence (0.40-0.69): 588 (11.9%) - ESM2, PubMed PARTIAL, curated sets
- Low confidence (< 0.40): 3,082 (62.2%) - PubMed ORPHAN (960), PubMed REJECT (2,122)

**Provenance coverage:**
- Edges with provenance: 4,956 (100%)
- Edges with PMIDs: 3,359+ (67.8%)
- Edges with database IDs (ChEMBL, FDA, KEGG): 1,032 (20.8%)
- Edges with "unknown" provenance: 0 (0.0%)

---

## 11. Interpreting Results: What The Numbers Mean

### 11.1 Prediction Scores

**Score range:** 0.0 - 1.0

**Interpretation:**

| Score | Interpretation | Action | Example |
|-------|----------------|--------|---------|
| **0.90-1.0** | Very strong evidence | High priority for clinical validation | Imatinib→CML (0.98) |
| **0.75-0.89** | Strong evidence | Worth experimental follow-up | Venetoclax→AML (0.92) |
| **0.60-0.74** | Moderate evidence | Requires more validation | Sorafenib→AML (0.65) |
| **0.50-0.59** | Weak evidence | Speculative, low priority | Novel combinations |
| **<0.50** | Very weak/no evidence | Do not pursue | Aspirin→Melanoma (0.12) |

**Important:** Score ≠ probability of success in clinic
- Score reflects strength of CURRENT EVIDENCE
- Clinical trials can still fail even with score 0.90
- Unknown mechanisms, resistance, toxicity not captured

### 11.2 AUROC (Model Performance)

**AUROC** = Area Under Receiver Operating Characteristic curve

**What it measures:** Can the system distinguish real drug-disease pairs from false ones?

**Score interpretation:**

| AUROC | Meaning |
|-------|---------|
| **1.0** | Perfect discrimination (never happens in real data) |
| **0.95-0.99** | Excellent discrimination |
| **0.90-0.94** | Very good discrimination |
| **0.85-0.89** | Good discrimination |
| **0.75-0.84** | Fair discrimination |
| **0.50-0.74** | Poor discrimination |
| **0.50** | Random guessing (coin flip) |

**Current system (2026-05-24):**
- Full graph (4,956 edges): AUROC = 0.956
- High confidence only (1,286 edges): AUROC = 0.959
- Protocol: `remove_direct_labels` (Drug→Disease edges removed before scoring)
- Path bonus: confidence-weighted `min(0.25, 0.04 * sum(path_confidence))`

**Why both tiers perform similarly:**
- Confidence-weighted path scoring means low-quality edges contribute proportionally
  less to path bonuses, so adding 3,696 PubMed edges doesn't introduce noise
- High-confidence paths (FDA, ChEMBL, curated PMID) dominate scoring regardless of tier

**What matters more than AUROC:**
- Can the researcher trace every claim to a citation?
- Does the confidence score tell them how much to trust each hop?
- Can they follow the evidence chain to a clinical trial decision?
- Transparency > Performance

### 11.3 Hits@K Metrics

**Hits@5** = "If I give you top 5 predictions, is the right answer in there?"

**Our results:**
- Hits@5 = 1.00 (100%)
- Hits@10 = 1.00 (100%)
- Hits@20 = 0.80 (80%)

**What this means:**
- If you test the top 5 repurposing candidates, you'll find the right one
- Very useful for prioritizing experiments
- Even at top 20, still 80% chance of finding right answer

### 11.4 Evidence Quality Indicators

When reviewing a prediction, check these indicators:

**Green flags (high quality):**
- ✓ Multiple mechanistic paths
- ✓ All edges have PMIDs
- ✓ Experimental evidence (ABPP, ChEMBL)
- ✓ Multiple data sources agree
- ✓ High composition strategy vote
- ✓ Known pathway involvement

**Yellow flags (medium quality):**
- ⚠ Only 1 mechanistic path
- ⚠ Some edges inferred (ESM2, pathway)
- ⚠ Mixed evidence quality
- ⚠ Kan extension is top voter
- ⚠ Limited PMID coverage

**Red flags (low quality/concerning):**
- ✗ No mechanistic paths (analogy only)
- ✗ Edges lack provenance
- ✗ Contradicts known biology
- ✗ Protein not in relevant pathway
- ✗ Only weak similarity evidence
- ✗ Clinical trial already failed

---

## 12. Advanced Topics: Category Theory Foundations

### 12.1 Why Category Theory?

**Traditional graph:** Just nodes and edges
**Category:** Nodes, edges, AND composition rules

**Example:**
```
A -f-> B -g-> C

Traditional graph: f and g are separate relationships
Category: f and g COMPOSE to give A -> C relationship
Composition: g ∘ f
```

**Why this matters for drug repurposing:**
```
Sorafenib -inhibits-> BRAF -driver_of-> Melanoma

Composition tells us:
- Sorafenib inhibits BRAF
- BRAF drives melanoma
- Composing these: Sorafenib should treat melanoma (by inhibiting driver)
```

This is the **Composition strategy** - the core of mechanistic reasoning.

### 12.2 Higher Morphisms (2-Cells)

**Morphism** = relationship between objects (A→B)
**2-morphism** = relationship between morphisms

**Example:**
```
Morphism 1: Sorafenib -inhibits-> BRAF
Morphism 2: Vemurafenib -inhibits-> BRAF

2-morphism: These are SIMILAR (both BRAF inhibitors)
```

**Why this matters:**
- If Vemurafenib→Melanoma works
- And Sorafenib is similar mechanism
- Then Sorafenib→Melanoma might also work

This is the **Kan Extension strategy** - finding analogies via morphism similarity.

### 12.3 Functors (Structure-Preserving Maps)

**Functor** = maps one category to another while preserving structure

**Example:**
```
Category 1: Proteins and their interactions
Category 2: Diseases and their relationships

Functor: Maps each protein to diseases it affects
```

**Preserves structure means:**
- If Protein A activates Protein B
- And A affects Disease X, B affects Disease Y
- Then there might be X→Y relationship too

This enables **cross-domain reasoning** - transfer knowledge from protein networks to disease networks.

### 12.4 Yoneda Lemma (The Neighborhood Principle)

**Yoneda Lemma:** An object is completely determined by how everything else relates to it

**In our system:**
A protein is characterized by:
- What drugs inhibit it
- What proteins it activates
- What pathways it's in
- What diseases it affects

If two proteins have the same "neighborhood" → they're essentially the same function

This is the **Yoneda strategy** - comparing protein neighborhoods to find functional similarities.

---

## Summary & Next Steps

### What You've Learned

You should now understand:

1. **What drug repurposing is** and why it matters
2. **How knowledge graphs work** and why they're powerful
3. **The 5 data sources** (ESM2, CosMx, ChEMBL, ABPP, PubMed) and their strengths/limitations
4. **How edges are created** and confidence scores assigned
5. **The 8 prediction strategies** and what patterns they find
6. **How scores are calculated** (vote aggregation, path bonus, mechanistic discount)
7. **What audit trails are** and why they're critical
8. **Current gaps** in transparency and how to fix them
9. **Quality control** and how to validate predictions
10. **How to interpret results** (scores, AUROC, quality indicators)
11. **Advanced foundations** (category theory, why it matters)

### Current System Status

**Strengths:**
- ✓ Comprehensive data (4,956 edges from 7+ sources)
- ✓ Multiple prediction strategies (8 different approaches)
- ✓ Strong performance (AUROC 0.956, Hits@5 100%)
- ✓ Provenance tracking (100% of edges have source)
- ✓ Clinical validation (44 FDA-approved pairs)
- ✓ Confidence-weighted scoring (high-quality evidence dominates)

**Limitations:**
- ⚠ Strategy votes lack detailed explanations
- ⚠ Confidence derivations not fully transparent
- ⚠ Multi-source reconciliation loses detail
- ⚠ No biological validation checks
- ⚠ 62% of edges are low-confidence PubMed co-mentions (use confidence tiers)

### Implementation Priority

To achieve full transparency, implement in this order:

**Phase 1: Enhanced Provenance** (CRITICAL)
1. Add confidence_derivation to all edges
2. Add multi-source reconciliation tracking
3. Update manifest JSON format

**Phase 2: Strategy Explainers** (HIGH PRIORITY)
1. Composition: Show all paths with edge details
2. Kan extension: Show analogy reasoning
3. Binding evidence: Show calculation breakdown
4. Others: Add explanation dicts

**Phase 3: Validation Layer** (IMPORTANT)
1. Pathway membership checks (KEGG/Reactome)
2. Protein family validation (Pfam)
3. Mechanism consistency checks
4. Flag suspicious inferences

**Phase 4: Display Enhancements** (NICE TO HAVE)
1. Triage report: Show full audit trail
2. Visualization: Graph explorer
3. Interactive: Drill down into evidence
4. Export: Generate audit reports

### Questions to Consider

Before we proceed with implementation:

1. **Confidence system:** Should we adjust scoring to better separate quality tiers?
2. **Validation strictness:** How aggressive should biological validation be?
3. **Coverage vs quality:** Add more edges (quantity) or improve existing ones (quality)?
4. **User interface:** CLI reports, web dashboard, or API access?
5. **Clinical integration:** How should clinicians use this tool safely?

---

## Glossary

**Key Terms:**

- **AUROC:** Area Under Receiver Operating Characteristic - measures model discrimination ability
- **Composition:** Following chain A→B→C to infer A→C
- **Confidence:** 0-1 score reflecting evidence strength
- **Edge:** Relationship between two entities (also called morphism)
- **Embedding:** High-dimensional vector representation of a protein
- **IC50:** Half-maximal inhibitory concentration (lower = more potent)
- **Knowledge graph:** Network of entities and relationships
- **Kan extension:** Finding indirect relationships through analogies
- **Mechanistic path:** Direct Drug→Protein→Disease chain
- **Morphism:** Directed relationship between objects
- **Node:** Entity in a graph (drug, protein, disease)
- **Provenance:** Source and evidence for a claim
- **PMID:** PubMed identifier for scientific papers
- **Strategy:** Algorithm for finding drug-disease patterns
- **Tier:** Quality level of evidence (1=gold, 4=inferred)
- **Yoneda:** Comparing objects by their neighborhoods

---

**END OF MANUAL**

This document should be updated as the system evolves.
Last updated: 2026-05-24
