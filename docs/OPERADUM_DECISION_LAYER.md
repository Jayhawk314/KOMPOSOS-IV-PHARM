# OPERADUM Decision Layer — User Guide (2026-06-04)

A guide for researchers using the **Decision ranking (OPERADUM)** mode in the
KOMPOSOS-IV-PHARM app. It assumes no category theory.

## What problem it solves

The rest of the app answers: *"For this disease, how do candidates rank on the
evidence?"* (Disease-first) or *"What's the evidence for this one pair?"* (Pair
detail). Those rank on **graph evidence**.

OPERADUM answers a different, downstream question:

> **"We can pursue only a few of these. Which one do we back, and what's the
> single best next step for it?"**

It takes the same KOMPOSOS shortlist and re-ranks the **decision**, folding the
graph evidence together with target engagement (ABPP), structure binding,
drug-likeness, and risk — under a profile you choose.

It is a **prioritization aid layered on Track A**. It is not a new evidence
source, not a safety/PK model, and not de-novo drug design (Track B). It does
not change any benchmark AUROC.

## Relation to PRONOIA

The UI now has a separate **Prediction audit (PRONOIA)** mode. Do not read it as
another OPERADUM profile; it answers a different question.

| Layer | UI mode | Question it answers |
|---|---|---|
| KOMPOSOS-IV-PHARM | Disease-first / Drug-first / Pair detail | What graph evidence and mechanistic paths support this pair? |
| OPERADUM | Decision ranking (OPERADUM) | Given a shortlist, which candidate/action should we back next under a decision profile? |
| PRONOIA | Prediction audit (PRONOIA) | Is the candidate treatment claim grounded by hidden-label evidence, and what is the auditable prediction trail? |

PRONOIA uses the same KOMPOSOS PHARM graph and provenance, but it reports
`BACK`/`ABSTAIN`, PHARM v2 score, grounding, raw MDL gain, and provenance-rich
evidence packets. OPERADUM remains the action/prioritization layer.

## Running it

```powershell
streamlit run app.py        # from the repo root
```

In the sidebar pick **Decision ranking (OPERADUM)**, then:

1. **Select disease** — the indication to rank candidates for.
2. **Shortlist size** — how many drugs to pull from KOMPOSOS triage first.
3. **Decision profile** — how to weight the figures (see below).
4. **Require strong evidence (≥ 0.8)** — whether the recommended *next action*
   must clear an evidence bar.

Press **Rank candidates**. You get a winner banner, a ranked table (decision
score, next action, and the raw per-source evidence scores), a **Download
Decision Report** button (a self-contained markdown record — recommendation,
full ranked table, per-candidate evidence, and the honest-limits footer, dated
and stamped with the profile and gate, suitable as an audit trail for a
prioritization decision), and a **Candidate Details** section expanding the
top candidates' evidence and next-action verdict.

For prediction audit reports, use **Prediction audit (PRONOIA)** instead. That
mode exports a separate markdown report with PRONOIA score, grounding,
`BACK`/`ABSTAIN`, top mechanism/path evidence, PMIDs/FDA provenance, and honest
limits.

## Reading the results

**Decision Score — lower is better, and negative is good.** The score is one
weighted number rolled up from every applicable figure. Figures you want to
*maximize* (evidence strength, confidence, drug-likeness) count negatively, so a
strong candidate lands clearly negative (e.g. −75) and a weak one sits near zero
(e.g. −10). The table is sorted ascending: the top row is the pick.

Scores are only meaningful **relative to each other within one ranking** — do
not compare a score across diseases or across profiles.

**How the figures combine** (this is what makes it more than a weighted average):

| Figure | Combine rule | Reading |
|---|---|---|
| time, money | **sum** | total cost to fully vet the candidate |
| confidence | **multiply** | you're only as sure as all independent checks agree |
| evidence strength | **weakest-link (min)** | the shakiest link caps the chain |
| risk (toxicity, off-target, hERG) | **probability union** | more ways to fail = more total risk |

**"no feasible action"** is a verdict, not a bug. With *Require strong evidence*
on, any candidate whose best next step cannot clear the 0.8 evidence bar is
flagged this way — meaning *not currently backable without gathering more
evidence first*. Uncheck the box to see its unconstrained next step.

## The three profiles

A profile just reweights the figures:

- **Portfolio (evidence + safety + developability)** — the default. Balances
  evidence, safety, and developability, and nearly cancels the fixed assay cost
  that every candidate shares, so the ranking turns on what *distinguishes*
  candidates. Best for "which one do we back?".
- **Evidence-first** — lets evidence strength and confidence dominate.
- **Fastest next step** — favours the quickest, cheapest move.

## Where the numbers come from

- **Graph** — existing drug→disease evidence paths in this checkout's knowledge
  graph (the same `tier1.db` Track A uses).
- **Engagement** — ABPP target-engagement data (`abpp_bridge.py`, 65
  experimental IC50/engagement entries) when the drug/target pair is present.
- **Binding** — structure-based binding. **Falls back to a heuristic unless
  Boltz is installed** (`pip install boltz`); the app says so in-line.
- **Drug-likeness** — Lipinski-style properties (`data/drugs/drug_properties.py`).

The **Target** column is inferred from the top mechanistic chain (drug → protein
→ disease). When no such path exists it is blank, and OPERADUM ranks that
candidate on fewer actions.

## Honest limits

- A prioritization aid on Track A, **not clinical, prospective, or Track B**.
  Same limits as the rest of the app: no patient context, no PK, no real safety
  model (the "risk" figures are coarse priors, not validated predictions).
- Structure binding is **fallback** unless Boltz is installed.
- Decision scores are relative, within one ranking only.
- The categorical fold is a principled way to combine figures; it is **not**
  independently validated as outperforming a hand-tuned scorecard. Treat it as a
  transparent, reproducible decision aid, not an oracle.

## For developers

- Bundle/import architecture:
  `docs/OPERADUM_PRONOIA_BUNDLE.md`.
- Ranking API: `vendor/operadum/operadum/integrations/drug_batch_ranker.py`
  (`rank_candidates`, `Candidate`, `RankedSlate`).
- Evidence client + world model:
  `vendor/operadum/operadum/integrations/komposos_drug_world.py`.
- `DRUG_PORTFOLIO` and the other profiles: `vendor/operadum/operadum/core/enrichment.py`.
- App wiring: the `Decision ranking (OPERADUM)` block in `app.py`.
