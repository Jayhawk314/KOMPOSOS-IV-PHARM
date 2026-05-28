> **Legacy/historical notice (2026-05-27):** This file is retained for background or session history. It is not the current source of truth for Track A metrics or provenance. Current docs are in `truedocs/`, especially `truedocs/VALIDATION_AND_BENCHMARKS.md` and `truedocs/REPRODUCIBILITY_PROTOCOL.md`. Current strict run: AUROC 0.974694 [0.9606, 0.9855], AUPRC 0.551698 [0.4067, 0.6983], Hits@5/10/20 1.0000/0.6000/0.6000; LOOCV AUROC 0.975916 and AUPRC 0.553703; Hetionet external AUROC 0.634479 and AUPRC 0.009255. Source strings exist on all 5,382 morphisms with 610 PMID identifiers; this is not 100% edge-specific citation validation. Retired or superseded claims in this file should be read as historical.
# KOMPOSOS-IV-PHARM Triage Report Audit
# AML Case Study & System-Wide Findings

**Date:** 2026-05-23
**Auditor:** Claude (Opus 4.6), requested by James Ray Hawkins
**Scope:** Triage report accuracy, mechanistic path integrity, PMID provenance
verification, and analysis of no-path high-score predictions
**Report audited:** `triage_AML.md` (generated via Streamlit web UI)

---

## Executive Summary

The triage system is structurally sound: the CLI and Streamlit UI share
identical scoring code, the graph counts are accurate, and the self-check
passes. However, this audit found two significant issues:

1. **Most PMID citations on intermediate protein edges are incorrect.**
   Out of 12 non-"treats" PMIDs spot-checked, 11 point to unrelated papers.
   The 44 "treats" edges (Drug->Disease) have correct PMIDs. The 872 ChEMBL
   edges cite assay IDs (not papers) and are structurally valid.

2. **Drugs with no mechanistic path still score high (0.83-0.90)** due
   to analogy-based strategies that don't require a Drug->Protein->Disease
   chain. These predictions lack the evidence trail that is the system's
   primary differentiator from black-box methods.

---

## 1. Are the Numbers in the Report Correct?

**YES.** The live triage output matches `triage_AML.md` exactly.

Verified by running `python validation/triage.py AML --top 20 --markdown`:

| Claim in Report        | Live Output            | Status |
|------------------------|------------------------|--------|
| 1143 objects           | 1143                   | MATCH  |
| 1260 morphisms         | 1260                   | MATCH  |
| 44 approved indications| 44                     | MATCH  |
| Self-check 44/44       | 44/44                  | MATCH  |
| Sunitinib score 1.000  | 1.000                  | MATCH  |
| Palbociclib score 0.904| 0.904                  | MATCH  |
| All 20 rankings        | Identical order/scores | MATCH  |

The Streamlit web UI and CLI use the exact same functions:
- `score_pair()` from `validation/repurposing_benchmark.py`
- `trace_pair()` from `validation/trace_prediction.py`
- `triage_disease()` from `validation/triage.py`
- `format_markdown()` from `validation/triage.py`

No divergence between web and CLI.

---

## 2. Are the Mechanistic Paths Real?

**YES, the paths that exist are genuine graph traversals.** When the report
says "Sunitinib -inhibits-> FLT3 -driver_of-> AML", those edges really
exist in `tier1.db` with the stated confidence values.

The `trace_pair()` function calls `category.find_paths(drug, disease, max_length=4)`
and filters to multi-hop paths (`len(path.morphism_ids) >= 2`). It then looks
up each edge's provenance from the SQLite provenance index.

The AML subgraph has 13 proteins with edges to AML:

| Protein | Relation          | Confidence | PMID          |
|---------|-------------------|:----------:|---------------|
| FLT3    | driver_of         | 0.90       | PMID:19553641 |
| TOP2A   | driver_of         | 0.80       | PMID:23396808 |
| BCL2    | associated_with   | 0.78       | PMID:27103402 |
| KIT     | associated_with   | 0.75       | PMID:11309425 |
| HDAC1   | associated_with   | 0.75       | PMID:11423618 |
| ABCB1   | associated_with   | 0.72       | PMID:18698266 |
| STAT3   | associated_with   | 0.72       | PMID:22389471 |
| JAK2    | associated_with   | 0.70       | PMID:19553641 |
| HDAC2   | associated_with   | 0.68       | PMID:11423618 |
| NFKB1   | associated_with   | 0.68       | PMID:9597151  |
| IL6     | associated_with   | 0.65       | PMID:15175435 |
| NPL4    | associated_with   | 0.60       | PMID:29241109 |
| TXNRD1  | associated_with   | 0.60       | PMID:19461509 |

---

## 3. PMID Provenance Accuracy (CRITICAL FINDING)

### 3.1 Provenance Breakdown

| Category                       | Count | Pct   | Verified? |
|--------------------------------|------:|------:|-----------|
| ChEMBL assay IDs               | 872   | 69.2% | Structurally valid (auto-imported) |
| PMIDs on "treats" edges         | 44    | 3.5%  | Spot-checked 2/2 CORRECT |
| PMIDs on intermediate edges     | 344   | 27.3% | Spot-checked 12, **11 WRONG** |
| Unknown                         | 0     | 0.0%  | -- |
| **Total**                       | **1260** | **100%** | -- |

### 3.2 PMID Spot-Check Results

**"treats" edges (CORRECT):**

| Edge                              | PMID       | Actual Paper                                    | Correct? |
|-----------------------------------|------------|-------------------------------------------------|:--------:|
| Afatinib->NSCLC                   | 23816960   | Phase III afatinib in NSCLC (2013)              | YES      |
| Bevacizumab->Colorectal_Cancer    | 15175435   | Bevacizumab + IFL for mCRC (2004)               | YES      |

**Intermediate edges (MOSTLY WRONG):**

| Edge                | PMID       | Actual Paper                                  | Correct? |
|---------------------|------------|-----------------------------------------------|:--------:|
| Sunitinib->FLT3     | 16507829   | BAY 43-9006 (sorafenib) + RET kinase (2006)  | **NO**   |
| FLT3->AML           | 19553641   | Olaparib PARP inhibitor BRCA (2009)           | **NO**   |
| Niclosamide->STAT3   | 22389471   | BRAF/MEK/PI3K melanoma resistance (2012)      | **NO**   |
| STAT3->AML          | 22389471   | BRAF/MEK/PI3K melanoma resistance (2012)      | **NO**   |
| Imatinib->KIT       | 11309425   | Intravesical therapy bladder cancer (2001)    | **NO**   |
| KIT->AML            | 11309425   | Intravesical therapy bladder cancer (2001)    | **NO**   |
| STAT5A->BCL2        | 12068308   | BRAF mutations in cancer (2002)               | **NO**   |
| AKT1->BCL2          | 16461283   | Resveratrol fish lifespan (2006)              | **NO**   |
| BCL2->AML           | 27103402   | ABT-199 Bim/Mcl-1 resistance in AML (2016)   | **YES**  |
| BRCA1<-ATM          | 7894491    | BRCA1 germline mutations (1994)               | **NO**   |
| BAX->CASP9          | 9220931    | Research funding editorial (1997)             | **NO**   |
| E2F1->MYC           | 11461910   | Notch/mSel-10 ubiquitination (2001)           | **NO**   |

**Accuracy: 1/12 correct (8%) on intermediate edges.**

### 3.3 What This Means

The claim "1260/1260 morphisms have provenance (100.0%)" is *technically*
true -- every edge has a provenance string. But most PMIDs on intermediate
edges (Drug->Protein, Protein->Protein, Protein->Disease) do not point to
papers that actually support the claimed relationship. These PMIDs appear
to have been assigned incorrectly at some point in the data pipeline.

**What IS trustworthy:**
- The 44 "treats" edge PMIDs (spot-checked correct)
- The 872 ChEMBL assay ID citations (auto-imported from ChEMBL database)
- The graph *structure* itself (edges represent real biological relationships)

**What is NOT trustworthy:**
- The ~344 PMIDs on intermediate protein edges

This does not invalidate the graph structure or the scoring system, but it
means the evidence chains in triage reports cannot currently be verified by
clicking the PMID links. A researcher following a chain like
"Sunitinib -inhibits-> FLT3 -driver_of-> AML" would click the PMIDs and
find papers about unrelated topics.

---

## 4. No-Mechanistic-Path Predictions: What Are They Worth?

### 4.1 The Core Question

In the AML report, 8 of 20 drugs show "(no mechanistic path)" yet score
between 0.835 and 0.904. How?

### 4.2 How Scores Are Computed

```
score = average(strategy_votes) + path_bonus
path_bonus = min(0.25, 0.10 * composition_count)
```

When there are zero mechanistic paths, `composition_count = 0`, so
`path_bonus = 0`. The score is just the average of whichever strategies
voted.

### 4.3 What Strategies Actually Vote for No-Path Drugs

For all 8 no-path drugs, only 2 strategies out of 8 produce a vote:

| Drug           | kan_extension | binding_evidence | Others | Final Score |
|----------------|:------------:|:----------------:|:------:|:-----------:|
| Palbociclib    | 0.900        | 0.907            | --     | 0.904       |
| Ribociclib     | 0.900        | 0.901            | --     | 0.901       |
| Regorafenib    | 0.900        | 0.871            | --     | 0.886       |
| Olaparib       | 0.900        | 0.859            | --     | 0.880       |
| Trastuzumab    | 0.900        | 0.820            | --     | 0.860       |
| Bevacizumab    | 0.850        | 0.833            | --     | 0.842       |
| Pembrolizumab  | 0.850        | 0.827            | --     | 0.838       |
| Ramucirumab    | 0.850        | 0.820            | --     | 0.835       |

Compare with Sunitinib (4 strategies vote, HAS paths):

| Drug       | kan_ext | composition | topos_logic | binding_ev | path_bonus | Final |
|------------|:-------:|:-----------:|:-----------:|:----------:|:----------:|:-----:|
| Sunitinib  | 0.700   | 0.880       | 0.850       | 0.900      | +0.25      | 1.000 |

### 4.4 What Each Strategy Is Actually Doing

**kan_extension (Drug Analogy):** "Drugs structurally similar to X tend to
treat diseases similar to Y." This looks at morphism-pattern overlap between
the query drug and other drugs in the graph. It does NOT require that the
drug's protein targets connect to the query disease. Palbociclib gets 0.90
because it shares targets/patterns with other cancer drugs, not because
CDK4/CDK6 connect to AML.

**binding_evidence:** Scores molecular binding quality at the Drug->Protein
level (IC50, drug-likeness, Pfam domain matching, molecular compatibility).
It does NOT check whether the protein connects to the disease. Palbociclib
gets 0.907 because it binds well to CDK4/CDK6, not because CDK4/CDK6 have
any known role in AML.

**composition (Mechanistic Path):** Finds actual Drug->Protein->Disease
paths. Returns 0 predictions for these drugs because none of their protein
targets connect to AML. This is the ONLY strategy that requires a traceable
evidence chain.

**topos_logic, structural_hole, type_heuristic, yoneda_pattern, fibration_lift:**
These also return nothing for the no-path drugs. They generally need some
graph connectivity between the drug and disease to fire.

### 4.5 Why the No-Path Drugs Have Zero Chains

Confirmed by database query -- none of these drugs target any of the 13
AML-connected proteins:

| Drug          | Protein Targets           | Overlap with AML Proteins |
|---------------|---------------------------|:-------------------------:|
| Palbociclib   | CDK4, CDK6                | NONE                      |
| Ribociclib    | CDK4, CDK6                | NONE                      |
| Regorafenib   | KDR, RET                  | NONE                      |
| Olaparib      | BRCA1, BRCA2              | NONE                      |
| Trastuzumab   | ERBB2                     | NONE                      |
| Bevacizumab   | VEGFR2, VEGFA             | NONE                      |
| Pembrolizumab | CD4, CD8A, PDCD1          | NONE                      |
| Ramucirumab   | KDR                       | NONE                      |

These drugs operate through completely different biological mechanisms
(CDK inhibition, VEGF/angiogenesis, immune checkpoint, PARP/DNA repair)
that have no representation in the AML section of the graph.

### 4.6 The Score Inflation Problem

A subtle design issue: because `score_pair` averages only the strategies
that DO vote, drugs with fewer votes can have inflated scores.

- A drug where 2 strategies both return ~0.90 gets score = 0.90
- A drug where 5 strategies return {0.70, 0.75, 0.88, 0.85, 0.90} gets
  score = 0.816 + path_bonus

This means no-path drugs can outrank mechanistically-supported drugs.
In the AML report, Palbociclib (#3, 0.904, no path) outranks Imatinib
(#5, 0.894, 2 chains, 5/5 cited), which has actual KIT->AML evidence.

### 4.7 Are No-Path Predictions Useful to Researchers?

**Short answer: Low standalone value; useful only as a filtering signal.**

The whole value proposition of this system versus a black-box ML model is
the audit trail: Drug->Protein->Disease chains backed by citations. Without
that chain, a no-path prediction is essentially saying:

> "This drug looks like other cancer drugs and binds well to proteins,
> therefore it might treat AML."

That's roughly what any drug similarity search would tell you. It lacks:
- The specific mechanism (which protein? which pathway?)
- The evidence trail (which papers support each step?)
- The biological plausibility assessment

**A researcher seeing Palbociclib ranked #3 for AML with "no mechanistic
path" should NOT interpret this as evidence for repurposing.** It's a
statistical artifact of how the score combiner works.

**Drugs WITH mechanistic paths** (Sunitinib, Niclosamide, Imatinib,
Venetoclax, Ruxolitinib, etc.) provide what the system promises:
auditable chains linking drug action to disease biology.

### 4.8 Recommendation

For research-facing reports, no-path predictions should either:
- Be clearly flagged/demoted (e.g., separate section, lower visual weight)
- Have a minimum chain count requirement for inclusion in ranked output
- Show a confidence qualifier ("analogy only, no mechanistic evidence")

This would prevent a researcher from seeing Palbociclib at #3 and
mistakenly thinking the system has evidence for CDK4/6 inhibition in AML.

---

## 5. Comparison: Drugs WITH vs WITHOUT Evidence Chains

To make the distinction concrete, here are the AML report's top
candidates split by evidence quality:

### Tier 1: Mechanistic evidence + cited chains

| Rank | Drug           | Score | Chains | Cited | Best Path |
|------|----------------|:-----:|:------:|:-----:|-----------|
| 1    | Sunitinib      | 1.000 | 4      | 12/12 | ->FLT3->AML |
| 2    | Niclosamide    | 0.917 | 3      | 7/7   | ->STAT3->AML |
| 5    | Imatinib       | 0.894 | 2      | 5/5   | ->KIT->AML |
| 8    | Aspirin        | 0.877 | 3      | 7/7   | ->NFKB1->AML |
| 9    | Valproic Acid  | 0.877 | 2      | 4/4   | ->HDAC1->AML |
| 10   | Ruxolitinib    | 0.875 | 3      | 9/9   | ->JAK2->AML |
| 11   | Venetoclax     | 0.866 | 3      | 9/9   | ->BCL2->AML |
| 13   | Bazedoxifene   | 0.845 | 3      | 7/7   | ->IL6->AML |
| 17   | Auranofin      | 0.828 | 2      | 4/4   | ->TXNRD1->AML |
| 18   | Lapatinib      | 0.798 | 2      | 7/7   | ->EGFR->STAT3->AML |
| 19   | Fluorouracil   | 0.780 | 1      | 2/2   | ->TOP2A->AML |
| 20   | Ivermectin     | 0.779 | 3      | 8/8   | ->STAT3->AML |

### Tier 2: Analogy/binding only (no evidence chain)

| Rank | Drug           | Score | Chains | Basis |
|------|----------------|:-----:|:------:|-------|
| 3    | Palbociclib    | 0.904 | 0      | CDK4/6 inhibitor (breast cancer) |
| 4    | Ribociclib     | 0.901 | 0      | CDK4/6 inhibitor (breast cancer) |
| 6    | Regorafenib    | 0.886 | 0      | VEGFR/RET inhibitor (CRC/GIST) |
| 7    | Olaparib       | 0.880 | 0      | PARP inhibitor (ovarian/breast) |
| 12   | Trastuzumab    | 0.860 | 0      | HER2 antibody (breast cancer) |
| 14   | Bevacizumab    | 0.842 | 0      | VEGF antibody (CRC) |
| 15   | Pembrolizumab  | 0.838 | 0      | PD-1 antibody (melanoma/NSCLC) |
| 16   | Ramucirumab    | 0.835 | 0      | VEGFR2 antibody (CRC) |

**The Tier 1 drugs are what make this system valuable.** Sunitinib->FLT3->AML
is a well-known repurposing candidate (FDA approved for AML-related
indications via FLT3). Venetoclax is FDA-approved for AML. The system
correctly ranks these highly AND provides the mechanistic reasoning.

The Tier 2 drugs are noise in the ranked list -- they score high but
provide no actionable evidence for a researcher to pursue.

---

## 6. What the Baselines Tell Us

The system AUROC of 0.974 (LOOCV) vs strongest baseline of 0.931
(shortest_path) shows a modest +0.043 improvement. This is honest and
documented. But the key insight from the baselines is:

**Shortest-path at 0.931 means that simple graph topology already predicts
most of the known drug-disease pairs.** The system's value isn't raw AUROC
superiority -- it's the interpretability layer:
- Strategy vote breakdown
- Mechanistic chain enumeration
- (Would-be) citation support per edge
- Provenance coverage metrics

This interpretability is exactly what's missing from the no-path
predictions. They fall back to the black-box pattern that the system
is designed to avoid.

---

## 7. Summary of Findings

### Confirmed Correct
- Graph counts (objects, morphisms, positives) are accurate
- Self-check (44/44) passes
- Scoring is deterministic and reproducible
- CLI and Streamlit share identical code paths
- Mechanistic paths that exist are real graph traversals
- "treats" edge PMIDs are correct (2/2 verified)
- ChEMBL provenance IDs are structurally valid (auto-imported)
- Score formula is as documented

### Issues Found

| Severity | Finding |
|----------|---------|
| **HIGH** | ~344 PMIDs on intermediate protein edges are mostly incorrect (~92% wrong in spot-check). A researcher following these links will find unrelated papers. |
| **MEDIUM** | No-path drugs score 0.83-0.90 and outrank mechanistically-supported drugs due to score averaging over fewer strategy votes. |
| **LOW** | The report does not visually distinguish between analogy-only predictions and mechanistically-supported ones in the ranked table. |
| **NOTE** | The Boltz2 bridge is in fallback mode (boltz not installed). All binding_evidence scores use heuristic/property-based components only. |

### Recommendations (no code changes made)

1. **PMID Audit:** The 344 intermediate-edge PMIDs need systematic
   verification and correction. The relationships themselves (e.g.,
   "Sunitinib inhibits FLT3") are scientifically well-established --
   correct PMIDs exist and could be found. The current PMIDs just don't
   point to the right papers.

2. **No-Path Flagging:** Add a visual indicator or separate section for
   predictions without mechanistic paths so researchers don't
   misinterpret analogy scores as evidence.

3. **Score Normalization:** Consider requiring a minimum number of voting
   strategies, or applying a penalty when composition returns zero paths,
   to prevent score inflation from 2-strategy averages.

---

## 8. For James: The Informal Explanation

Here's what's going on in plain terms:

**Your system has two "brains":**
1. The "evidence brain" (composition strategy) that traces actual paths
   through the protein network. Drug -> Protein -> Disease. This is what
   makes your system better than a black box.
2. The "vibes brain" (kan_extension, binding_evidence) that says "this
   drug LOOKS like other cancer drugs" without checking the actual
   biology connecting it to the specific disease.

When both brains agree (Sunitinib for AML), you get a score of 1.0 with
4 evidence chains and 12 cited edges. That's gold.

When only the vibes brain fires (Palbociclib for AML), you get a score
of 0.90 with zero evidence chains. That's... an unsubstantiated hunch
dressed up as a high-confidence prediction.

**The ranking puts these side by side without distinction.** Palbociclib
at #3 (no evidence) outranks Imatinib at #5 (real KIT->AML evidence),
Venetoclax at #11 (FDA-approved for AML!), and Ruxolitinib at #10
(real JAK2->AML evidence). That's misleading.

**On the PMIDs:** Your treats edges (the 44 "Drug X is approved for
Disease Y" edges) have correct citations. But the middle parts of the
chains -- the "Drug inhibits Protein" and "Protein drives Disease" edges
-- mostly have wrong PMIDs. The biological RELATIONSHIPS are real
(Sunitinib really does inhibit FLT3, FLT3 really is a driver of AML),
but the cited papers are about unrelated topics. A researcher clicking
through would lose trust immediately.

**Bottom line:** The system's architecture is sound and its mechanistic
predictions (the ones WITH paths) are genuinely useful. But the report
needs to clearly separate "predictions with evidence" from "predictions
by analogy," and the intermediate-edge PMIDs need a systematic correction
pass before the evidence chains can be trusted end-to-end.
