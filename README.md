# KOMPOSOS-IV-PHARM

A categorical AI runtime applied to pharmaceutical discovery.

- **Working capability (Track A):** drug *repurposing* over a curated
  drug–target–disease graph — ranking which drugs plausibly act on which
  diseases, with source-linked mechanistic evidence chains.
- **Long-term goal (Track B):** de-novo drug *design* (molecular generation,
  binding/efficacy/safety, ADMET). Not scientifically validated in this repo —
  do not read Track A metrics as Track B readiness.

Author: James Ray Hawkins · Code license: [Apache-2.0](LICENSE) · Third-party
data retain their own terms: [NOTICE](NOTICE) · Python 3.10+

> **Status:** working research prototype, **not** clinical or translational
> validation. Every AUROC below names its graph view, protocol, pair count,
> positive count, and label policy — see `CLAUDE.md` for the full audit trail.
>
> **Read [`HONEST_VALUE.md`](HONEST_VALUE.md) first** for a deliberately
> conservative, self-critical account of what this system is and is not worth.
>
> **Current project phase:** local feature development is paused pending
> external researcher workflow testing. See
> [`docs/LOCAL_COMPLETION_AND_EXTERNAL_VALIDATION.md`](docs/LOCAL_COMPLETION_AND_EXTERNAL_VALIDATION.md)
> for the stopping rationale, outreach targets, session protocol, and
> continue/narrow/archive decision.
>
> **New here?** [`docs/README.md`](docs/README.md) says which of the 145
> markdown files are current and which are historical records that should not be
> quoted for numbers.

---

## What this is actually useful for

The ranker is the least interesting thing in this repository. **The contribution
is a repurposing system that measured itself four times and reported four
negatives**, plus a finding about the clinical-trial literature that holds well
beyond this project.

| Measured result | Finding |
|---|---|
| [ESMC ablation](data/ESMC_ABLATION_RESULT.json) | A 422-edge protein-embedding similarity layer made the ranker **worse**. Removing it improved AUROC 0.9691 → 0.9784, so it is excluded by default |
| [Grounding permutation control](data/GROUNDING_NEGATIVE_CONTROL.json) | Post-hoc PubMed grounding measures **corpus density, not biology**. Real protein-disease pairings ground at 12.5%, randomly scrambled ones at 7.5% — Fisher p=0.28 |
| Horn composition | Categorical machinery added **nothing** over ordinary pairwise comparison |
| [PRISM adjudication](reports/prism_2026-08-14/README.md) | Pre-registered *before the scoring code existed*, against measured cell-line viability. **No candidate showed lineage-selective activity**, at any quality threshold. Zero of 60 standings changed |
| [Trial recovery](reports/trial_recovery_2026-08-12/README.md) | 75% of tracked trials never posted results, every recorded stop reason was operational or financial rather than efficacy or safety, and **13 trials have registry results with no publication of any kind** — invisible to any literature search |
| [60-candidate audit](reports/candidate_review_2026-08-01/README.md) | What the top of a ranked list actually contains when a human checks every row: **1 lead, 12 structurally invalid, 16 already clinically tested, 17 with nothing findable** |

The trial finding has a direct consequence for anyone building these systems: a
novelty signal built on literature absence **cannot distinguish "nobody tried
this" from "somebody tried it and ran out of money."**

If you are evaluating this as a source of drug candidates, read the 60-candidate
audit first — it will tell you honestly what to expect. If you are building a
knowledge-graph or ML repurposing system and want a validation template, the
pre-registration and correspondence patterns in
[`docs/PLAN_PRISM_ADJUDICATION_2026-08-14.md`](docs/PLAN_PRISM_ADJUDICATION_2026-08-14.md)
are the part worth stealing.

---

## Headline result (Track A)

Strict validation, `full_typed` view, `remove_direct_labels` protocol (the
direct Drug→Disease label is removed before scoring, so the ranker cannot read
the answer it is graded on):

```powershell
python validation\repurposing_benchmark.py --view full_typed --protocol remove_direct_labels --cohort core --baselines --ci
```

- **AUROC 0.9763**, AUPRC 0.5920 (2026-08-01)
- **precision@5 1.00, precision@10 0.70** · 44 local curated `treats` positives over 1,560
  pairs (core cohort). The tool prints these as "Hits@k" but computes
  `hits / min(positives, k)`, which is precision@k — hence the fall from k=5 to k=10.
- **Scored-only AUROC 0.9609**: 598 of the 1,560 pairs are abstentions scored 0.0
  and sit inside the headline AUROC. AUPRC is unchanged.
- **+0.23** over the strongest graph baseline (common_neighbor 0.7483)
- Measured on the ESMC-excluded default graph; see HONEST_VALUE.md for why the
  similarity-transfer layer is excluded. The current margin is +0.2280.

**External performance is currently undetermined, not weak** (revised 2026-07-31).
The previously listed Hetionet result (AUROC 0.644 / AUPRC 0.010) is **retired and
not executable** — `data/external/` is absent from this repository, so
`validation/external_validation.py` fails on a clean clone. The temporal holdout
still runs but is **stale and mis-cohorted**: rerun 2026-07-31 it gives AUROC
0.996 / AUPRC 0.156 on the `all` cohort, it leaves post-cutoff literature in the
graph, and its negative set contains approved indications — Dacomitinib→NSCLC,
approved 2018-09-27, currently ranks first among its "negatives." In-graph
recovery is strong; **what happens on novel pairs is unmeasured**, and no claim
should be made in either direction until the evaluation label set is complete.
See `HONEST_VALUE.md`.

**Installation:** the current package uses `setuptools.build_meta`. From a clone,
run `python -m pip install -e .`; use `python -m pip install -e ".[demo]"` for
the Streamlit UI.

---

## Search speedup (enrichment funnel)

The practical value isn't "the AI finds cures" — it's that it reorders a
1,560-pair search with a 2.8% base hit rate into a short list that is far denser
in real hits, so a scientist screens a fraction of the candidates and still
catches most of them. Measured under the strict protocol above:

**Search space:** 1560 drug-disease pairs | 44 known positives | base rate 2.82% | protocol `remove_direct_labels` (strict)

| Screen top | Pairs | Capture | Enrichment vs random |
|---|---|---|---|
| 5% | 78 | 31/44 (70%) | **14.1x** |
| 10% | 156 | 42/44 (95%) | **9.5x** |
| 20% | 312 | 43/44 (98%) | **4.9x** |

- Capture **50%** of known hits by screening **3%** of the list (41 pairs; skip 97%).
- Capture **80%** of known hits by screening **6%** of the list (91 pairs; skip 94%).
- Capture **100%** of known hits by screening **24%** of the list (375 pairs; skip 76%).

_Measured on **known** positives (recovery), so this quantifies search
acceleration on the curated graph — not a novel-discovery hit rate. Performance
on genuinely novel pairs is unmeasured; the previous external and temporal
checks are retired or invalid._

Regenerate any time the graph changes:

```powershell
python -m validation.enrichment_funnel              # terminal table
python -m validation.enrichment_funnel --markdown   # this section
python -m validation.enrichment_funnel --json       # structured output
```

---

## Disease-specific candidates (demote the hubs)

Promiscuous multi-kinase inhibitors top almost every disease — Imatinib lands in
14 of 20 disease top-5 lists — so the raw ranking keeps surfacing pan-cancer
hubs you already know. The **Disease-specific** view re-ranks by
`lift = raw score − the drug's mean across all diseases`, demoting the hubs so
the genuinely disease-specific candidates surface. On Melanoma this promotes the
actual approved MEK/checkpoint drugs (Binimetinib, Cobimetinib, Nivolumab,
Pembrolizumab) that the raw ranking buries. It is a presentation lens — it does
**not** change the scoring model or any AUROC.

![Disease-specific view for Melanoma](reports/disease_specific_melanoma.png)

```powershell
python -m validation.disease_specificity Melanoma   # or open the "Disease-specific" UI mode
```

---

## Quickstart

```powershell
# Rank all drugs for a disease (evidence chains, provenance, labels)
python validation\triage.py Melanoma

# Disease-specific candidates (demote the pan-cancer hub drugs)
python -m validation.disease_specificity Melanoma

# Rank all diseases for a drug
python validation\triage.py --drug Sorafenib

# Reproduce the strict benchmark (core cohort = the headline 0.9763; omit --cohort for the inflated all-cohort number)
python validation\repurposing_benchmark.py --view full_typed --protocol remove_direct_labels --cohort core --baselines --ci

# Interactive web app (Disease-first / Drug-first / Pair detail / Search speedup / ...)
streamlit run app.py
```

---

## Contextual evidence hypergraph

`Pair detail` now joins the scored Drug→Protein→Disease graph to a separate,
read-only contextual evidence database. The evidence layer preserves n-ary
study context—interventions, conditions, recruitment state, reviewed result
signal, contradictions, and source receipts—without changing the ranking score
or adding external terms to the scored graph.

The bundled database is rebuilt deterministically from the 60-candidate review:

```powershell
python -m evidence.build
```

Current materialization (2026-08-21): 60 reviewed claims, 77 registry studies,
148 receipts, 160 outcomes, 3,237 typed study roles, and 60 PRISM viability
observations. Pair detail also provides an FTS5
search over the reviewed local corpus. A failed local search renders as unknown,
not as evidence of absence. Vector retrieval is deliberately deferred until it
can beat this lexical baseline on a frozen retrieval task. See
[`docs/EVIDENCE_GRAPH_ARCHITECTURE.md`](docs/EVIDENCE_GRAPH_ARCHITECTURE.md)
for the before/after architecture and expected behavior, and
[`docs/EVIDENCE_HYPERGRAPH_PLAN.md`](docs/EVIDENCE_HYPERGRAPH_PLAN.md) for
delivery gates.

---

## How it works (briefly)

Live triage configures eight strategy modules — dominated by confidence-weighted
**mechanistic path composition** (Drug→Protein→Disease) plus a structural
**Yoneda similarity** bonus and a **binding-evidence** strategy (ABPP IC50s,
drug-likeness). Seven modules are active in the strict label-removed benchmark,
because Yoneda distance has no visible treatment comparators. Provenance is
tiered honestly: `RELATION-VERIFIED` (agent-
confirmed directed/signed relation) vs `LEXICAL-COOCCURRENCE` (automated screen
only). The `OPERADUM` decision layer ranks *which candidate to back next* on top
of Track A scores. See `CLAUDE.md` and `TECHNICAL_OVERVIEW.md` for architecture,
strategies, validation, and limitations.

## Scientific rules

1. Code and database queries outrank docs.
2. Every AUROC must specify view, protocol, pair count, positive count, label policy.
3. Direct Drug→Disease labels must be removed or held out for stronger claims.
4. Unlabeled pairs are open-world unknowns, not confirmed negatives.
5. Do not represent fallback/mock modules as production capability.

## Verification

```powershell
pytest tests\test_repurposing_benchmark.py -q   # focused regression
pytest tests -q                                  # full suite: 249 passed, 1 skipped
```

A clean `git clone` runs the full suite with no manual steps and no network
access. If it does not, that is a bug — please open an issue.

## Third-party data

The shipped graph `data/drugs/tier1.db` contains 2,462 edges drawn from ChEMBL,
PubMed, KEGG, COSMIC, FDA labels, DepMap and others. **Every edge records its
own provenance**, and the full inventory with per-source terms is in
[`NOTICE`](NOTICE). COSMIC and KEGG have the most restrictive redistribution
terms of the sources used; what is present is a small, attributed factual
extraction rather than a copy of either database, and commercial users should
obtain their own licences. If you are a rights holder and believe an extraction
here exceeds what your terms permit, please open an issue.
