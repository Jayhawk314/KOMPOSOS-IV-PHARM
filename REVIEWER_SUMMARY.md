# KOMPOSOS-IV-PHARM Presentation Packet

Prepared: 2026-06-05

Audience: oncologists, pharmacologists, computational biology reviewers, and
potential validation partners.

This is a research prototype for expert review. It is not medical advice, not a
clinical decision system, and not a treatment recommendation engine.

## One-Sentence Summary

KOMPOSOS-IV-PHARM ranks oncology drug-disease candidates from a typed biomedical
graph, while the bundled OPERADUM + PRONOIA stack turns those candidates into
auditable decision and prediction reports with explicit evidence trails.

## What To Show First

Run the app:

```powershell
streamlit run app.py
```

Use these UI modes in order:

1. **Disease-first**: show the original KOMPOSOS graph triage and evidence paths.
2. **Prediction audit (PRONOIA)**: show relationship status, grounding, PHARM v2
   score, raw MDL transparency, PMIDs/provenance, and the downloadable audit
   report.
3. **Decision ranking (OPERADUM)**: show how a shortlist becomes an action or
   prioritization report.

For the cleanest reviewer demo, start with **Prediction audit (PRONOIA)**, choose
`Pancreatic_Cancer`, keep direct Drug->Disease labels hidden, and download the
PRONOIA audit report.

## Current System Split

```text
KOMPOSOS-IV-PHARM
  graph, PHARM SQLite database, labels, provenance, PMIDs, Streamlit UI

OPERADUM
  candidate packaging and decision/prioritization reports

PRONOIA
  prediction audit: mechanism/path strength, grounding, abstention,
  raw MDL transparency, evidence trail

domain_core
  shared contracts between the engines
```

No Orion dependency is required or intended.

## What The Relationship Status Means

The PRONOIA UI now separates the final drug-disease relationship from the
evidence trail:

| Status | Meaning |
|---|---|
| Known label | Positive in the local PHARM FDA-label benchmark |
| Inferred from established path | Not locally labeled positive, but supported by measured/established mechanism-path edges |
| Research/trial-supported | Matched an externally checked research, trial, approval, or curation lead |
| Needs calibration / possible overreach | Mechanism-rich graph signal that needs indication/resistance context or expert rejection |

This distinction matters. An edge can be established while the final
drug-disease relationship is still inferred.

## Current Benchmark Snapshot

KOMPOSOS strict hidden-label benchmark:

| Metric | Value |
|---|---:|
| Objects | 1,143 |
| Typed edges | 2,329 |
| FDA-positive drug-disease labels | 44 |
| KOMPOSOS AUROC | 0.9705 |
| KOMPOSOS AUPRC | 0.5464 |

The strong AUROC is in-graph recovery. External generalization is weaker
(Hetionet CtD AUROC 0.6436, AUPRC 0.0095); present this as a search accelerator
on the curated graph, not a novel-discovery hit rate.

PRONOIA PHARM v2 hidden-label benchmark:

| Metric | Value |
|---|---:|
| Drug-disease pairs | 1,560 |
| Positive labels | 44 |
| Mean grounding | 0.655 |
| PRONOIA v2 AUROC | 0.981 |
| PRONOIA v2 AUPRC | 0.577 |
| Hits@5 / @10 / @20 | 0.600 / 0.700 / 0.650 |

Like the KOMPOSOS AUROC above, this 0.981 is an **in-graph hidden-label**
benchmark on the same 44 positives, not an external test. It is not evidence
that PRONOIA generalizes better than KOMPOSOS to novel pairs; read both as
in-graph recovery, and weigh external generalization by the Hetionet result.

Raw zlib-MDL is retained as a transparency metric, but it is not the primary
PHARM ranker.

## Strongest Presentation Findings

Validation/curation cases:

```text
Trastuzumab_deruxtecan -> Breast_Cancer
Lorlatinib -> NSCLC
Brigatinib -> NSCLC
Adagrasib -> Colorectal_Cancer
Sotorasib -> Colorectal_Cancer
```

These are useful because PRONOIA surfaced local label-negative pairs that are
externally supported. That suggests local benchmark curation gaps or
underrepresented indication/combination context.

Research-review cases:

```text
Sotorasib -> Pancreatic_Cancer
Adagrasib -> Pancreatic_Cancer
```

These should be framed as KRAS G12C research/trial-context findings, not general
treatment claims.

Calibration cases:

```text
Afatinib -> Breast_Cancer
Cetuximab -> NSCLC
Lapatinib -> NSCLC
```

These are useful because they show the next scorer must distinguish target
biology from actionable indication fit.

## What To Send To A Professional

Do not send the whole repo first. Send a short result packet:

1. Drug-disease pair.
2. Relationship status.
3. PRONOIA score and grounding.
4. Evidence path, e.g. `Drug -> Target -> Disease`.
5. PMIDs/FDA provenance from the audit report.
6. Caveat: this is expert-review evidence, not a clinical recommendation.

Recommended supporting docs:

```text
operadum/docs/PHARM_FINDINGS_REPORT.md
operadum/docs/PHARM_RESEARCH_LEADS.md
operadum/docs/PHARM_LEAD_AUDIT_TRAIL_SUPPLEMENT.md
operadum/docs/PHARM_EXTERNAL_VALIDATION_REPORT.md
docs/OPERADUM_PRONOIA_BUNDLE.md
```

## What Not To Claim

- Do not claim clinical discovery.
- Do not claim the system proves treatment efficacy.
- Do not claim `NOT_APPROVED` means false.
- Do not claim every PMID is an edge-specific figure/table proof.
- Do not claim PRONOIA v2 already handles resistance or indication mismatch.
- Do not over-read a drug that tops many diseases: promiscuous multi-kinase
  inhibitors (Imatinib tops 17/20 diseases) crowd the top of most rankings, so a
  high rank for one is weak disease-specific evidence. Use the app's
  **Disease-specific** view, which demotes these hubs.

For the full conservative assessment, see `HONEST_VALUE.md` in the repo root.

## Honest Limit

PHARM is ready to present as an auditable graph/prediction-review prototype. It
is not finished science. The next research upgrade is PRONOIA PHARM v3:

```text
score_v3 =
    mechanism/path support
    - contradiction or residual penalty
    - weak-association penalty
    - indication-mismatch penalty
```

Until v3 exists, the system's strongest use is expert review, benchmark curation,
and generating clear audit trails for mechanism-backed candidates.
