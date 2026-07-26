# PHARM Presentation Lock

Date: 2026-06-05

Purpose: define the stable presentation state of KOMPOSOS-IV-PHARM after the
OPERADUM + PRONOIA integration.

## Status

PHARM is presentation-ready as a research prototype.

That means:

- The app runs from the KOMPOSOS-IV-PHARM repo.
- The bundled `vendor/operadum/` folder contains OPERADUM, PRONOIA, and `domain_core`.
- The UI can generate PRONOIA audit reports with relationship status, grounding,
  raw MDL transparency, evidence paths, PMIDs, and provenance.
- The strongest findings have been checked against public sources and separated
  into curation, research-review, and calibration groups.

It does not mean:

- The model is clinically validated.
- The graph is complete.
- PRONOIA v2 understands resistance, indication mismatch, or failed-trial
  context.

## Presentation Route

Use this order for a live walkthrough:

1. `streamlit run app.py`
2. Open **Prediction audit (PRONOIA)**.
3. Select `Pancreatic_Cancer`.
4. Keep **Hide direct Drug->Disease treatment labels** checked.
5. Run the audit.
6. Explain the top row using:
   - `Local Label`
   - `Relationship Status`
   - `Decision`
   - `PRONOIA Score`
   - `Grounding`
   - `Top Evidence`
   - `PMIDs`
7. Download the PRONOIA audit report.
8. Show **Decision ranking (OPERADUM)** only after the prediction audit is clear.

## Reviewer Explanation

Use this short explanation:

```text
KOMPOSOS provides the graph evidence. PRONOIA asks whether a candidate claim is
grounded by hidden-label mechanism/path evidence. OPERADUM is separate: it helps
rank what action to take next. The important point is that the UI now separates
known labels, inferred relationships, externally supported research leads, and
calibration/overreach cases.
```

## Strong Demo Examples

### Research/Trial-Supported

```text
Sotorasib -> Pancreatic_Cancer
Adagrasib -> Pancreatic_Cancer
```

Message: PRONOIA reconstructs a KRAS G12C pancreatic signal from mechanism/path
evidence with direct treatment labels hidden. This is research-review evidence,
not a treatment claim.

### Curation/Validation

```text
Trastuzumab_deruxtecan -> Breast_Cancer
Lorlatinib -> NSCLC
Brigatinib -> NSCLC
Adagrasib -> Colorectal_Cancer
Sotorasib -> Colorectal_Cancer
```

Message: these are local label-negative findings that external sources support,
so they are good benchmark-curation examples.

### Calibration / Overreach

```text
Afatinib -> Breast_Cancer
Cetuximab -> NSCLC
Lapatinib -> NSCLC
```

Message: PRONOIA v2 sees real mechanism biology, but v3 must learn when target
presence is not enough for an actionable indication.

## Stop Here Before Expanding

Do not expand the PHARM graph just to make the demo feel larger. More edges will
increase explanation burden. The next high-value PHARM work is not volume; it is
v3 scoring:

```text
contradiction/residual penalty
weak-association penalty
indication-mismatch penalty
```

## Files To Know

```text
REVIEWER_SUMMARY.md
docs/OPERADUM_PRONOIA_BUNDLE.md
operadum/docs/PHARM_FINDINGS_REPORT.md
operadum/docs/PHARM_RESEARCH_LEADS.md
operadum/docs/PHARM_LEAD_AUDIT_TRAIL_SUPPLEMENT.md
operadum/docs/PHARM_EXTERNAL_VALIDATION_REPORT.md
```

## Current Positioning

Say:

```text
This is an auditable graph/prediction-review prototype that independently
surfaces mechanism-backed candidates and separates known labels from inferred
relationships and calibration cases.
```

Do not say:

```text
This discovers treatments.
This proves efficacy.
This replaces expert review.
```
