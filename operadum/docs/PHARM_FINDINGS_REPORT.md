# PHARM Findings Report

Date: 2026-06-05

This is a human-readable findings report from the current PRONOIA PHARM run. It
is about what the PHARM data is showing, not about the architecture.

For an external public-source check of these findings, see
`docs/PHARM_EXTERNAL_VALIDATION_REPORT.md`.

Important boundary: this is graph/data analysis, not medical advice or a
clinical recommendation. A "label-negative" pair below means the pair is not a
positive `treats` label in the local PHARM benchmark set used for scoring. It
does not mean the claim is clinically false.

## Run Context

Protocol:

```powershell
python -m operadum.validation.pronoia_pharm_benchmark --protocol remove_direct_labels --quality all
```

The `remove_direct_labels` protocol hides direct Drug->Disease treatment labels
from the evidence PRONOIA sees. PRONOIA must rank drug/disease pairs from
mechanistic graph support such as:

```text
Drug -> target protein -> disease
Drug -> pathway node -> target protein -> disease
```

Current benchmark:

| Metric | Value |
|---|---:|
| Drugs | 78 |
| Diseases | 20 |
| Drug/disease pairs | 1,560 |
| Positive labels | 44 |
| Abstentions | 257 |
| Mean grounding | 0.655 |
| PRONOIA v2 AUROC | 0.981 |
| PRONOIA v2 AUPRC | 0.577 |
| KOMPOSOS baseline AUROC | 0.971 |
| KOMPOSOS baseline AUPRC | 0.546 |

## Main Finding

PRONOIA can recover many hidden benchmark-positive treatment links from
mechanism alone. The direct treatment edge is hidden, but the graph still
contains target/disease structure strong enough to reconstruct the relationship.

Examples:

| Pair | PRONOIA score | Label | Main evidence PRONOIA used |
|---|---:|---:|---|
| Imatinib -> CML | 99.0 | positive | Imatinib inhibits BCR_ABL; BCR_ABL driver_of CML |
| Ruxolitinib -> Myelofibrosis | 97.0 | positive | Ruxolitinib inhibits JAK2; JAK2 driver_of Myelofibrosis |
| Imatinib -> GIST | 97.0 | positive | Imatinib inhibits KIT; KIT driver_of GIST |
| Osimertinib -> NSCLC | 96.5 | positive | Osimertinib inhibits EGFR; EGFR driver_of NSCLC |
| Trastuzumab -> Breast_Cancer | 96.5 | positive | Trastuzumab inhibits ERBB2; ERBB2 driver_of Breast_Cancer |

This is the useful "new eye" of the system: it does not just say a treatment
label exists. It shows the graph mechanism that made the label recoverable.

## High-Signal Label-Negative Pairs

These are the most interesting human-review findings. They are not counted as
positive labels in the local benchmark, but PRONOIA found strong mechanism/path
support.

| Pair | PRONOIA score | Grounding | Main evidence PRONOIA used | Human interpretation |
|---|---:|---:|---|---|
| Adagrasib -> Pancreatic_Cancer | 97.0 | 0.783 | Adagrasib inhibits KRAS; KRAS driver_of Pancreatic_Cancer | Strong mechanism-rich review candidate |
| Sotorasib -> Pancreatic_Cancer | 97.0 | 0.783 | Sotorasib inhibits KRAS; KRAS driver_of Pancreatic_Cancer | Strong mechanism-rich review candidate |
| Trastuzumab_deruxtecan -> Breast_Cancer | 96.5 | 0.794 | Trastuzumab_deruxtecan inhibits ERBB2; ERBB2 driver_of Breast_Cancer | Possible label-set/curation audit |
| Lorlatinib -> NSCLC | 95.4 | 0.562 | Lorlatinib inhibits ALK and ROS1; both driver_of NSCLC | Possible label-set/curation audit |
| Afatinib -> Breast_Cancer | 95.0 | 0.700 | Afatinib inhibits ERBB2; ERBB2 driver_of Breast_Cancer | Mechanism-rich but needs indication context |
| Cetuximab -> NSCLC | 95.0 | 0.533 | Cetuximab inhibits EGFR; EGFR driver_of NSCLC | Mechanism-rich but needs indication context |
| Brigatinib -> NSCLC | 95.0 | 0.562 | Brigatinib inhibits ALK; ALK driver_of NSCLC | Possible label-set/curation audit |
| Lapatinib -> NSCLC | 94.5 | 0.533 | Lapatinib inhibits EGFR; EGFR driver_of NSCLC | Mechanism-rich but needs indication context |
| Adagrasib -> Colorectal_Cancer | 93.4 | 0.741 | Adagrasib inhibits KRAS; KRAS driver_of Colorectal_Cancer | Strong mechanism-rich review candidate |
| Sotorasib -> Colorectal_Cancer | 93.4 | 0.741 | Sotorasib inhibits KRAS; KRAS driver_of Colorectal_Cancer | Strong mechanism-rich review candidate |

The important pattern is that the graph has strong target-disease support for
KRAS, ERBB2, EGFR, ALK, and ROS1. PRONOIA is surfacing those mechanism-rich
relationships even when the benchmark label table does not mark them positive.

That is useful, but it also explains the next hard problem: a mechanism-rich
pair is not automatically a good treatment claim. The next scorer needs a
contradiction/residual penalty and more indication-specific context.

## Weakest Hidden Positives

These are benchmark-positive labels that PRONOIA still backs, but with lower
mechanism strength after direct treatment labels are hidden.

| Pair | PRONOIA score | Grounding | Main evidence PRONOIA used | Human interpretation |
|---|---:|---:|---|---|
| Bevacizumab -> Colorectal_Cancer | 78.5 | 0.759 | Bevacizumab indirect_inhibitor VEGFR2; VEGFR2 associated_with Colorectal_Cancer | Positive label has weaker indirect graph support |
| Regorafenib -> GIST | 83.9 | 0.562 | Regorafenib inhibits RET/KDR; RET associated_with GIST; KDR driver_of GIST | Supported, but not as sharply as top target-driver pairs |
| Regorafenib -> Colorectal_Cancer | 84.9 | 0.759 | Regorafenib inhibits KDR/RET; KDR driver_of Colorectal_Cancer | Supported, lower than direct oncogene-driver patterns |
| Regorafenib -> HCC | 84.9 | 0.533 | Regorafenib inhibits KDR/RET; KDR driver_of HCC | Supported, lower grounding |
| Sorafenib -> HCC | 85.9 | 0.462 | Sorafenib inhibits VEGFR2/RAF1; VEGFR2 driver_of HCC | Supported, but evidence is less concentrated |
| Cetuximab -> Colorectal_Cancer | 87.2 | 0.741 | Cetuximab inhibits EGFR; EGFR associated_with Colorectal_Cancer; KRAS path support | Positive label has mechanism support but lower than direct driver cases |
| Metformin -> Type2_Diabetes | 87.5 | 0.708 | Metformin activates AMPK; AMPK associated_with Type2_Diabetes | Supported through association rather than driver edge |
| Ribociclib -> Breast_Cancer | 87.6 | 0.682 | Ribociclib inhibits CDK4/CDK6; CDK4/CDK6 paths through RB1 to Breast_Cancer | Supported through pathway mediation |

"Weakest" here does not mean clinically weak. It means the hidden-label graph
evidence is less direct, more indirect, or less concentrated than the top
mechanism cases.

## Data Insights

1. The strongest recoverable treatment evidence is usually a short two-step
   mechanism:

```text
drug inhibits target
target driver_of disease
```

2. The largest review queue is not random. It clusters around target families:

| Family | Pairs surfaced |
|---|---|
| KRAS/RAS pathway | Adagrasib/Sotorasib with Pancreatic_Cancer, Colorectal_Cancer, NSCLC |
| EGFR/ERBB2 | Trastuzumab_deruxtecan, Afatinib, Cetuximab, Lapatinib across Breast_Cancer/NSCLC |
| ALK/ROS1 | Lorlatinib and Brigatinib with NSCLC |
| VEGF/VEGFR/KDR | Bevacizumab, Regorafenib, Sorafenib positives have support, but less concentrated |

3. PRONOIA v2 is currently excellent at finding mechanism-rich pairs, but less
   conservative than KOMPOSOS at the very top of the ranking. That is why PRONOIA
   beats/equals KOMPOSOS on AUROC/AUPRC in this run, while KOMPOSOS still has
   stronger H@5 precision.

4. Raw zlib-MDL is not the PHARM finding engine. It failed as a primary ranker
   because text compression over-rewards broad/long evidence packets. The useful
   signal is structured graph evidence plus grounding.

## What A Human Should Review First

Priority 1: curation/label audit

- Trastuzumab_deruxtecan -> Breast_Cancer
- Lorlatinib -> NSCLC
- Brigatinib -> NSCLC

These look like cases where the mechanism path is very direct and the local
benchmark label table may simply not reflect the relationship.

Priority 2: mechanism-rich repurposing hypotheses

- Adagrasib -> Pancreatic_Cancer
- Sotorasib -> Pancreatic_Cancer
- Adagrasib -> Colorectal_Cancer
- Sotorasib -> Colorectal_Cancer
- Afatinib -> Breast_Cancer
- Cetuximab -> NSCLC
- Lapatinib -> NSCLC

These need stronger indication context before being treated as predictions.

Priority 3: evidence-gap review for known positives

- Bevacizumab -> Colorectal_Cancer
- Regorafenib -> GIST
- Regorafenib -> HCC
- Sorafenib -> HCC
- Metformin -> Type2_Diabetes
- Ribociclib -> Breast_Cancer

These are positive benchmark labels whose hidden-label mechanism support is
present but not as decisive. The graph may need richer evidence edges,
provenance, or pathway annotations.

## Next Analysis Step

Build PHARM score v3 around the current failure mode:

```text
score_v3 =
    mechanism/path support
    - contradiction or residual penalty
    - weak-association penalty
    - indication-mismatch penalty
```

The immediate goal is not higher AUROC. It is better top-of-list precision:
separate true label omissions and plausible repurposing hypotheses from
mechanism-only overreach.
