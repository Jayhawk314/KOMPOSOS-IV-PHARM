# KOMPOSOS-IV-PHARM — Current Docs (2026-06-02)

This folder is a **fresh, self-consistent snapshot** built directly from the live
database and benchmark runs on 2026-06-02. It supersedes the older, multi-generation
docs in `docs/` and `truedocs/`. If anything here disagrees with those, **this folder
and the live code/data win.**

Files:
- `VALIDATION.md` — all current benchmark results (strict, LOOCV, holdouts, baselines)
- `DATA.md` — database facts, evidence tiers, provenance tiers
- `REPRODUCE.md` — exact commands to reproduce every number here

## What it is

A drug-**repurposing** engine (Track A) over a curated drug → target → disease
knowledge graph, scored by category-theoretic link-prediction strategies plus
molecular/binding evidence. **Oncology only, 20 cancer types.** Research prototype —
not clinical, not prospective. (Track B, de-novo drug design, is a goal, not validated.)

## Headline (strict `full_typed / remove_direct_labels`, 44 positives)

| Metric | Value |
|---|---|
| AUROC | **0.970549** [95% CI 0.9519–0.9844] |
| AUPRC | 0.546427 [0.4025–0.6890] |
| Hits@5 / @10 / @20 | 1.000 / 0.600 / 0.600 |
| Strongest baseline | common_neighbor 0.6219 → margin **+0.3486** |

DB: 2,329 morphisms · 78 drugs · 20 diseases · 366 biological entities · 44 FDA
`treats` positives. DB SHA256 `09F849850C0E97051F9F2D0A2247FF24CDCC9D25A93BC0453C3C0B89DC32F6D3`.

## Interactive app & decision ranking

`streamlit run app.py` (from the repo root) opens the triage UI. Modes:
**Disease-first** / **Drug-first** / **Pair detail** rank and explain candidates
on graph evidence. **Decision ranking (OPERADUM)** takes a KOMPOSOS shortlist and
re-ranks the *decision* — which candidate to back, plus its best next action —
folding evidence with target engagement, structure binding, drug-likeness, and
risk under a chosen profile. It is a prioritization aid on Track A, not a new
evidence source; lower decision scores are better. See
`docs/OPERADUM_DECISION_LAYER.md` and the in-app **How Scoring Works** page.

## Honest limits (read before citing)

- **Not clinical / not prospective.** No safety, PK, toxicity, patient context.
- **External generalization is weak:** Hetionet external AUROC 0.6436, AUPRC 0.0095,
  Hits@20 = 0. Internal scores are far stronger than external — weigh this heavily.
- **Open-world negatives:** unlabeled pairs are unknown, not confirmed negative.
- **Literature edges** are single-PMID agent-adjudicated, not wet-lab confirmed.
- **Categorical framing is unproven as a value-add** over standard KG link prediction.

Author: James Ray Hawkins · Apache 2.0 / Commercial dual license ·
<https://github.com/Jayhawk314/KOMPOSOS-IV-PHARM>
