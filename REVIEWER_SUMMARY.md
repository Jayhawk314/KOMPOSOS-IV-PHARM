# KOMPOSOS-IV-PHARM — One-Page Summary for Reviewers

*Prepared 2026-06-02. Audience: oncologists, pharmacologists, comp-bio / ML reviewers.
This is a research prototype seeking expert critique, not a product or clinical tool.*

## What it is

A **drug-repurposing** engine over a curated **drug → target → disease** knowledge
graph. For a given drug–disease pair it scores the likelihood of a repurposing
relationship by combining category-theoretic link-prediction strategies
(composition of mechanistic paths, Yoneda-style structural similarity, Kan
extensions, topos logic) with molecular/binding evidence (ABPP IC50, drug-likeness).
**Scope: oncology only, 20 cancer types.** Every prediction is traceable to
mechanistic paths and cited literature.

A second ambition ("Track B", de-novo drug *design*) exists only as a goal and is
**not validated** — please disregard it for review.

## The data (live, reproducible from `data/drugs/build_tier1.py`)

- 464 stored objects: **78 drugs, 20 diseases, 366 biological entities** (proteins, etc.)
- **2,329 typed, directed edges** across 23 relation types
- **44 ground-truth positives** = FDA-approved oncology indications (`treats` edges); all 44 have a mechanistic drug→protein→disease path
- Provenance tiering (honest, metadata only — does **not** feed scoring): 745 edges agent-adjudicated as `RELATION-VERIFIED`, 215 `LEXICAL-COOCCURRENCE` (co-mention screen only)

## What is validated (internal)

Strict protocol `full_typed / remove_direct_labels` (removes the direct
Drug→Disease label *and* indication-derived bridge edges before scoring):

| Metric | Value |
|---|---|
| AUROC | **0.9705** [95% CI 0.9519–0.9844] |
| AUPRC | 0.5464 [0.4025–0.6890] |
| Hits@5 / @10 / @20 | 1.00 / 0.60 / 0.60 |
| Strongest baseline (common-neighbor) | 0.6219 → **margin +0.349** |
| LOOCV | AUROC 0.9674, AUPRC 0.5165 |
| Temporal holdout (approvals after 2013) | AUROC 0.9706, AUPRC 0.1938 |
| Disease holdout (7 folds) | mean AUROC 0.9378, mean AUPRC 0.6021 |

## What is NOT validated (please weigh these heavily)

- **Not clinical, not prospective.** No safety, PK, toxicity, or patient context.
- **External generalization is weak.** On Hetionet ChEMBL-derived external positives:
  **AUROC 0.644, AUPRC 0.0095, Hits@20 = 0** (near-zero precision-at-top). This is
  the most important caveat — internal scores are far stronger than external ones.
- **Open-world negatives:** unlabeled drug–disease pairs are treated as unknown, not
  confirmed negative; AUROC therefore measures label-recovery, not real-world success.
- **Small graph:** 464 objects vs. ~47k in published systems (Rephetio/Hetionet).
- **Literature edges are single-PMID, agent-adjudicated** (one human-style read of one
  cited sentence) — *not* wet-lab confirmation.
- **The categorical framing is unproven as a value-add.** We have not shown it beats a
  standard KG-embedding / GNN link-predictor on the same graph. (Genuine open question.)

## Questions we most want expert input on

1. **Protocol soundness** — are the leakage controls (`remove_direct_labels`, LOOCV,
   temporal, disease holdout) adequate, or is there residual leakage?
2. **External weakness** — is Hetionet AUROC 0.64 disqualifying, or expected at this
   graph size? What external benchmark would you trust?
3. **Biological plausibility** — do the top novel candidates make sense? (run the
   triage CLI below and judge the mechanistic chains).
4. **Method value** — does the category-theory machinery add anything over standard
   link prediction, or is the signal just graph topology + a good positive set?

## Reproduce in 3 commands

```powershell
# 1. Strict headline benchmark (with CIs + baselines)
python validation\repurposing_benchmark.py --view full_typed --protocol remove_direct_labels --ci --baselines

# 2. Rank repurposing candidates for a disease, with evidence chains + PMIDs
python validation\triage.py Melanoma

# 3. Interactive web app (graph stats, scoring breakdown, traceable evidence)
streamlit run app.py
```

Code: <https://github.com/Jayhawk314/KOMPOSOS-IV-PHARM> · License: Apache 2.0 /
Commercial dual · Author: James Ray Hawkins

**Standing principle of this project:** code and live data outrank docs; every AUROC
must name its view, protocol, positive count, and label policy. Findings here are
stated with their limits on purpose — we want them stress-tested, not sold.
