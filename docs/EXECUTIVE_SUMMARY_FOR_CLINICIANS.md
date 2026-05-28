> **Legacy/historical notice (2026-05-27):** This file is retained for background or session history. It is not the current source of truth for Track A metrics or provenance. Current docs are in `truedocs/`, especially `truedocs/VALIDATION_AND_BENCHMARKS.md` and `truedocs/REPRODUCIBILITY_PROTOCOL.md`. Current strict run: AUROC 0.974694 [0.9606, 0.9855], AUPRC 0.551698 [0.4067, 0.6983], Hits@5/10/20 1.0000/0.6000/0.6000; LOOCV AUROC 0.975916 and AUPRC 0.553703; Hetionet external AUROC 0.634479 and AUPRC 0.009255. Source strings exist on all 5,382 morphisms with 610 PMID identifiers; this is not 100% edge-specific citation validation. Retired or superseded claims in this file should be read as historical.
# KOMPOSOS-IV-PHARM: Cancer Drug Repurposing System

**Author**: James Ray Hawkins
**Date**: 2026-05-12
**Status**: Research prototype for hypothesis generation -- not for clinical decisions

---

## What This Does

Ranks cheap, FDA-approved generic drugs for cancer indications using mechanistic
pathway evidence. Every prediction comes with a Drug->Protein->Disease chain and
literature citations (PMIDs) that a scientist can audit.

This is a triage tool. It narrows the search space for repurposing candidates. It
does not replace clinical judgment, trial design, or regulatory evaluation.

---

## Validation

**Primary metric** (leave-one-out cross-validation, full_typed/loocv protocol):

| Metric | Value |
|--------|-------|
| AUROC | 0.974 [95% CI: 0.965-0.983] |
| AUPRC | 0.515 |
| Hits@5 | 1.00 (all held-out positives in top 5) |
| Positives | 44 FDA-approved oncology indications |
| Pairs scored | 1560 (78 drugs x 20 diseases) |
| Strongest baseline | shortest_path AUROC 0.931 |
| System margin | +0.043 over strongest baseline |

The AUROC margin over graph baselines is modest. The system's value is the
combination of mechanistic chains, literature provenance, strategy transparency,
and triage interface -- not raw prediction accuracy alone.

**ClinicalTrials.gov cross-check** (30 top repurposing candidates verified):

| Status | Count | Percentage |
|--------|------:|----------:|
| IN_TRIALS (human clinical trials exist) | 19 | 63% |
| PRECLINICAL (published lab research) | 9 | 30% |
| NOVEL (no significant prior evidence) | 2 | 7% |

63% of the system's top candidates are already in human clinical trials. This
validates that the scoring identifies scientifically plausible candidates, not
noise.

**Ablation study** (which components matter):

| Component | Alone AUROC | Impact when removed |
|-----------|----------:|-------------------:|
| Composition (path counting) | 0.969 | -0.045 AUROC (dominant) |
| Topos Logic | 0.947 | -0.004 AUROC |
| Kan Extension | 0.497 | -0.008 AUROC |
| Path bonus | -- | -0.017 AUROC |

Composition (counting Drug->Protein->Disease paths) is the dominant strategy.
The system is primarily a mechanistic path ranker with mathematical refinements.

---

## Knowledge Graph

| Fact | Value |
|------|-------|
| Total objects | 1143 |
| Drugs | 78 |
| Diseases | 20 cancer types |
| Proteins | 366 |
| Compound nodes (ChEMBL) | 679 |
| Edges (morphisms) | 1260 |
| Provenance coverage | 1260/1260 (100%) -- all edges have PMIDs or ChEMBL IDs |
| Approved indications | 44 (all FDA-approved, all with PMIDs) |
| Mechanistic paths | All 44 positives have Drug->Protein->Disease paths |
| DB SHA256 | `0BA4A7E01BBA3E1E52A03CD7765A3E6523618F439AB8A90ED4BD6B4BD95BC8E6` |

---

## Top Multi-Disease Candidates

Drugs with mechanistic pathway support for 5+ cancers:

| Drug | Cost/month | Cancer types | Strongest indication | Score |
|------|-----------|-------------|---------------------|------:|
| Mebendazole | ~$5 | 9 | HCC (rank #1) | 0.903 |
| Aspirin | ~$2 | 8 | Myelofibrosis (rank #1) | 0.700 |
| Metformin | ~$4 | 6 | Breast Cancer (rank #1) | 0.975 |
| Niclosamide | ~$3 | 7 | AML (rank #2) | 0.902 |
| Auranofin | ~$50 | 7 | AML (rank #18) | 0.799 |

**Strongest trial-backed candidates:**
- **Aspirin / Colorectal Cancer** -- ALASCCA trial (NEJM 2025): 51% lower recurrence in PI3K-mutated CRC
- **Metformin / Breast Cancer** -- 57 registered trials, phase III MA.32 (3,649 patients)
- **Clarithromycin / Multiple Myeloma** -- BiRD regimen: 38.9% CR rate in newly diagnosed MM
- **Propranolol / Colorectal Cancer** -- COMPIT pilot: recurrence 50% to 12.5%; two phase III ongoing

---

## How to Run

```powershell
# Rank all drugs for a disease
python validation\triage.py Melanoma

# Rank all diseases for a drug
python validation\triage.py --drug Metformin

# Detailed report for a specific pair
python validation\triage.py Melanoma --drug Vemurafenib

# JSON or Markdown output
python validation\triage.py Melanoma --json
python validation\triage.py Melanoma --markdown
```

Reports include: ranked candidates, strategy vote breakdown, mechanistic chains
with PMIDs, provenance coverage, and APPROVED/NOT_APPROVED labels.

NOT_APPROVED means the pair is not among our 44 curated FDA-approved oncology
indications. It does not mean the combination is novel -- many are already in
clinical trials or published literature.

---

## Limitations

- Research tool only -- not for clinical decisions
- NOT_APPROVED candidates may already be known, in trials, or published
- No patient-specific context (no genomics, no tumor profiling)
- Graph is curated but covers only 20 cancer types and 78 drugs
- Unlabeled drug-disease pairs are open-world unknowns, not confirmed negatives
- AUROC margin over graph baselines is modest (+0.043)
- No prospective validation yet (no prediction tested then confirmed true)
- Bioavailability not modeled (e.g., mebendazole, niclosamide have poor oral absorption)

---

## What We Would Like From You

1. **Plausibility check**: Do the top-5 candidates for your cancer area look biologically plausible?
2. **Novelty check**: Which candidates are already in trials we missed?
3. **Feedback**: Is this useful for your workflow, or does it duplicate what you already have?

---

## Disclaimer

This is a research tool for hypothesis generation. All predictions require
experimental and clinical validation. Do not use for patient treatment without
proper validation, IRB approval, and clinical trial design.
