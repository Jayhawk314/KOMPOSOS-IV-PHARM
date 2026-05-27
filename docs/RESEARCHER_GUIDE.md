# KOMPOSOS-IV-PHARM: Researcher Guide to Drug Repurposing Triage

## What This System Does

This system connects knowledge across medical databases to find drug
repurposing candidates for 20 cancer types. It bridges information silos:
a drug's binding data (from ChEMBL), a protein's role in disease (from
PubMed/KEGG), and FDA-approved mechanisms — information that exists in
separate databases and separate research communities.

The core insight: **Drug A binds Protein B** (known to pharmacologists) +
**Protein B drives Disease C** (known to oncologists) = **Drug A might
treat Disease C** (not obvious to either group alone).

Every prediction is a 2-hop mechanistic path: Drug -> Protein -> Disease.
Every hop has a citation (PMID, ChEMBL ID, KEGG pathway, FDA NDA number).
Nothing is a black box.

## What the System is NOT

- Not a clinical recommendation engine. Outputs are research hypotheses.
- Not validated in clinical trials. AUROC 0.965 with AUPRC 0.634 means the
  system ranks known repurposing successes above random with good precision,
  but false positives exist and clinical validation is required.
- Not comprehensive. It covers 78 drugs, 366 proteins, 20 cancer types.
  Many drugs and diseases are outside its scope.
- Not a replacement for literature review. It accelerates the search
  by surfacing connections you might not find otherwise.

## The Knowledge Graph

**5,382 evidence edges** connecting drugs, proteins, and diseases:

| Source | Edges | What it provides |
|--------|-------|------------------|
| ChEMBL binding assays | 881 | Drug->Protein binding affinity (IC50/Ki/Kd) |
| ESM2 protein embeddings | 422 | Protein->Protein structural similarity |
| PubMed literature | 3,754 | Protein->Disease associations with PMIDs |
| FDA approved mechanisms | 79 | Drug->Protein mechanisms from NDA labels |
| KEGG pathways | 72 | Protein->Protein pathway relationships |
| STRING PPI | 22 | Protein->Protein physical interactions |
| ABPP experimental | 17 | Drug->Protein IC50 from activity-based profiling |
| NLP quantitative extractions | 204 | IC50, mutation freq, hazard ratio, response rate (373 extractions, 92.2% validated) |

**20 cancer types** with drug coverage:

| Disease | High-confidence drug candidates | Total candidates |
|---------|-------------------------------|------------------|
| NSCLC | 28 | 61 |
| AML | 18 | 68 |
| HCC | 15 | 66 |
| Colorectal Cancer | 14 | 51 |
| Breast Cancer | 12 | 62 |
| GIST | 12 | 67 |
| RCC | 11 | 70 |
| Pancreatic Cancer | 11 | 59 |
| Melanoma | 9 | 63 |
| Glioblastoma | 7 | 65 |
| Soft Tissue Sarcoma | 5 | 65 |
| Li-Fraumeni Syndrome | 3 | 58 |
| CML | 2 | 67 |
| CLL | 1 | 65 |
| Multiple Myeloma | 1 | 62 |
| Myelofibrosis | 1 | 59 |
| Ewing Sarcoma | 0 | 55 |
| Ovarian Cancer | 0 | 56 |
| Prostate Cancer | 0 | 67 |
| Type 2 Diabetes | 0 | 66 |

"High-confidence" = both hops have confidence >= 0.70 (from authoritative
databases). "Total" includes speculative paths from PubMed co-mentions.

## How to Use the System

### 1. Disease-first: "What drugs might work for AML?"

```powershell
python validation/triage.py AML
```

This ranks all 78 drugs by their likelihood of treating AML. Output shows:
- Rank, score, and label (APPROVED or NOT_APPROVED)
- Number of independent mechanistic paths (evidence chains)
- Top evidence path with citations

### 2. Drug-first: "What diseases might Sorafenib treat?"

```powershell
python validation/triage.py --drug Sorafenib
```

Ranks all 20 diseases by how well Sorafenib's target profile matches them.

### 3. Specific pair: "Should I investigate Metformin for AML?"

```powershell
python validation/triage.py AML --drug Metformin
```

Full detailed report with every evidence chain, every citation, every
strategy vote, binding data if available.

### 4. Machine-readable output

```powershell
python validation/triage.py AML --json
python validation/triage.py AML --markdown
```

## Reading the Triage Report

### The Score (0.0 - 1.0)

The score is an average of 8 independent scoring strategies plus a bonus
for multiple mechanistic paths. Higher = more independent evidence that
this drug-disease pair is worth investigating.

**What the score is:** A ranking metric. Pairs scoring 0.90+ have strong
convergent evidence. Pairs scoring 0.50-0.70 have some evidence but are
speculative.

**What the score is not:** A probability of clinical success. A score of
0.90 does not mean 90% chance of working.

### The 8 Scoring Strategies

Each strategy is an independent signal. When multiple agree, confidence
increases:

| Strategy | What it asks | Signal type |
|----------|-------------|-------------|
| **Mechanistic Path** (composition) | Does Drug->Protein->Disease exist? | Direct evidence |
| **Drug Analogy** (Kan extension) | Do similar drugs treat this disease? | Analogy |
| **Interaction Profile** (Yoneda) | Does this drug's target pattern match known treatments? | Pattern |
| **Binding Evidence** | Is there IC50/binding data for drug-target pairs? | Experimental |
| **Evidence Integration** (topos) | Does cross-evidence support this pair? | Consistency |
| **Network Closure** | Would this edge close a structural hole? | Graph topology |
| **Type Match** | Do the types align for a treatment relationship? | Heuristic |
| **Structural Inference** (fibration) | Can we infer this from graph structure? | Structural |

When you see "6/8 strategies voted" in a report, it means 6 independent
methods found evidence supporting this pair. That is much stronger than
1/8 agreeing.

### Evidence Chains

Each chain is a Drug -> Protein -> Disease path with citations:

```
Sunitinib -[targets]-> FLT3 -[associated_with]-> AML
  FDA:NDA021938  (Sunitinib->FLT3)  confidence: 0.88
  PMID:42175928  (FLT3->AML)        confidence: 0.90
```

This tells you:
- **FDA:NDA021938**: Sunitinib's FDA label lists FLT3 as a target
- **PMID:42175928**: This paper links FLT3 mutations to AML
- **Confidence 0.88/0.90**: Both hops are from authoritative sources

You can look up the PMID at `https://pubmed.ncbi.nlm.nih.gov/42175928/`
and the NDA at `https://www.accessdata.fda.gov/` to verify each claim.

### Binding Evidence

When ABPP (Activity-Based Protein Profiling) data exists:

```
Binding evidence:
  Sorafenib->FLT3: IC50=0.058 uM  (87% inh.)  [PMID:28854174]
  Drug-likeness (Lipinski): 0.80
```

This is directly actionable: an IC50 of 0.058 uM with 87% inhibition
from a published study means the drug-target interaction is real and
potent. The PMID lets you read the original study.

### Confidence Levels

Each edge has a confidence value reflecting evidence quality:

| Confidence | Source | Meaning for researcher |
|------------|--------|----------------------|
| 0.90 - 1.00 | ChEMBL, FDA, KEGG | **Trust.** Authoritative database. Verify the citation for context. |
| 0.70 - 0.89 | Curated literature, ABPP | **Investigate.** Published data, worth reading the paper. |
| 0.50 - 0.69 | ESM2 similarity, curated | **Consider.** Computationally derived or broadly curated. Check the basis. |
| 0.40 - 0.54 | Verified PubMed (PARTIAL) | **Speculative but supported.** PubMed co-mention with some mechanistic backing. |
| 0.35 | PubMed (ORPHAN) | **Hypothesis only.** PubMed mentions both terms but no mechanistic path found. |
| 0.20 | PubMed (REJECT) | **Low confidence.** PubMed co-mention, failed categorical verification. Treat as noise unless you find supporting evidence independently. |

### The Categorical Verification System

PubMed edges (Protein->Disease associations found via literature search)
are classified by a 5-layer mathematical verification:

1. **Drug Path Witness**: Does any approved drug reach this protein for
   this disease? (HoTT path induction)
2. **Kan Extension Agreement**: Does the pattern of known drug-target
   associations predict this edge? (Left Kan extension)
3. **Mechanistic Reachability**: Can we reach this protein from known
   disease proteins via protein interaction networks? (BFS through graph)
4. **Protein Specificity**: Is this protein narrowly linked to this
   disease, or broadly linked to everything? (COG energy computation)
5. **Gray Interchange Coherence**: Does this edge fit consistently with
   the surrounding evidence? (Gray category interchange law)

Edges that pass all 5 layers are classified AGREE (confidence 0.75).
Edges that fail all 5 are classified REJECT (confidence 0.20). The
classification and per-layer scores are stored in edge metadata for
full transparency.

## Practical Workflow for Drug Repurposing Research

### Step 1: Screen a disease

```powershell
python validation/triage.py Melanoma --top 20
```

Look at the top-ranked NOT_APPROVED drugs. These are candidates the system
thinks are worth investigating but are not in our 44 FDA-approved oncology
indications. (NOT_APPROVED does not mean "won't work" — it means "not in
our curated list of known approvals.")

### Step 2: Check evidence quality

For each interesting candidate, look at:
- **How many strategies voted?** 6/8 = strong, 1/8 = weak
- **How many evidence chains?** Multiple independent paths = more robust
- **What confidence are the edges?** All >= 0.70 = trustworthy hops
- **Is there IC50 data?** Binding evidence makes it lab-actionable
- **Provenance fraction?** "14/14 cited" means every link is verifiable

### Step 3: Deep dive on promising candidates

```powershell
python validation/triage.py Melanoma --drug Metformin
```

Read the full evidence chains. Click the PMIDs. Check:
- Is the drug-target interaction real? (ChEMBL/ABPP data)
- Is the protein-disease link mechanistic or just co-mentioned in papers?
- Are there clinical trials already running? (Check ClinicalTrials.gov)
- What are the safety/toxicity concerns?

### Step 4: Cross-reference with literature

The system bridges knowledge silos, but it does not replace domain
expertise. Use the PMIDs and evidence chains as starting points for
a proper literature review. The value is in surfacing connections you
might not have found — not in replacing your judgment.

### Step 5: Validate with external databases

- ClinicalTrials.gov: Is this combination already in trials?
- DrugBank: Full drug profile and known interactions
- COSMIC: Mutation data for the target protein in this cancer
- cBioPortal: Patient-level genomic data

## Example: AML Drug Repurposing

The system finds 18 high-confidence drug candidates for AML. Some examples
of what a researcher would see:

**Sunitinib -> FLT3 -> AML** (confidence: 0.88/0.90)
- Sunitinib targets FLT3 (FDA-approved mechanism, NDA021938)
- FLT3 mutations drive AML (PMID:42175928)
- IC50 data available from ABPP
- Already in clinical trials for AML (the system correctly identifies this)

**Metformin -> MTOR -> AML** (confidence: 0.78/0.80)
- Metformin inhibits mTOR signaling (PMID:42166641)
- mTOR is active in AML blasts (curated from AML protein data)
- Drug-likeness: 0.65 (small molecule, oral, good safety profile)
- Multiple preclinical studies suggest benefit (literature search needed)

**Nelfinavir -> AKT1 -> AML** (confidence: 0.75/0.80)
- Nelfinavir (HIV protease inhibitor) inhibits AKT1 (PMID:34136086)
- AKT1 is part of the PI3K/AKT/mTOR axis in AML (curated)
- This is a classic repurposing hypothesis: cheap, available, well-characterized

Each of these gives the researcher a concrete starting point: a drug,
a target, a disease mechanism, and citations to follow.

## Benchmark Validation

The system is validated using the `remove_direct_labels` protocol
(Drug->Disease edges removed before scoring, forcing the system to
rediscover known approvals via mechanistic paths only). 44 FDA-approved
oncology indications as positive labels.

| Metric | Value |
|--------|-------|
| AUROC | 0.965 |
| AUPRC | 0.634 |
| Hits@5 | 1.00 |
| Hits@10 | 0.80 |

Graph: 5,382 edges (9 strategies with Yoneda distance bonus, 2026-05-26). AUPRC improvement (+18%) driven by Yoneda distance strategy on MEASURED+ESTABLISHED evidence subgraph.

**What the AUROC means for you:** If you pick a random known drug-disease
pair and a random unknown pair, the system ranks the known pair higher
97% of the time. This means the ranking is useful for prioritization —
always verify with the evidence chains and mechanistic paths.

## Limitations

1. **20 cancer types only.** Many cancers and all non-cancer diseases are
   outside scope.
2. **78 drugs only.** The drug set is focused on kinase inhibitors,
   checkpoint inhibitors, and a few repurposing candidates (Metformin,
   Thalidomide, etc.). Many approved oncology drugs are not included.
3. **2-hop paths only.** The system finds Drug->Protein->Disease chains.
   It does not find longer multi-step mechanisms (Drug->Protein A->
   Protein B->Disease). This is a design choice: 2-hop paths are the
   most interpretable for a researcher.
4. **PubMed co-mention != mechanism.** Many Protein->Disease edges come
   from PubMed searches where both terms appear in the same paper. The
   paper may not establish a mechanistic relationship. Always read the
   cited paper.
5. **No toxicity/safety modeling.** The system does not predict adverse
   effects, drug interactions, or safety risks.
6. **No patient stratification.** It does not account for patient
   subgroups, biomarkers, or genetic context.
7. **Open-world negatives.** Pairs labeled NOT_APPROVED are not confirmed
   negatives — many may be in clinical trials or published literature
   that our database does not cover.

## File Reference

| File | Purpose |
|------|---------|
| `validation/triage.py` | Main triage CLI (disease-first, drug-first, pair detail) |
| `validation/trace_prediction.py` | Trace any prediction to evidence chains |
| `validation/repurposing_benchmark.py` | Validation harness (AUROC, tier filters) |
| `data/drugs/tier1.db` | The knowledge graph (SQLite) |
| `abpp_bridge.py` | 65 experimental IC50 entries with PMIDs |
| `data/drugs/drug_properties.py` | Molecular properties for 78 drugs |
| `scripts/filter_pubmed_edges.py` | 5-layer categorical edge verification |
| `scripts/pubmed_edge_scores.json` | Per-edge verification scores and deltas |

## Contact

Author: James Ray Hawkins
License: Apache 2.0 / Commercial dual license
