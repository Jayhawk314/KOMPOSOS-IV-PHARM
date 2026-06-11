# HONEST_VALUE.md — what KOMPOSOS-IV-PHARM is actually worth

A plain-language, self-critical assessment of what this system does and does not
provide, written for anyone deciding whether it is worth their time. It is
deliberately conservative. Where it disagrees with the more enthusiastic framing
elsewhere in the repo, believe this file — every claim here is backed by an
executable check named in the text.

Last reviewed: 2026-06-10.

---

## One-sentence version

It is a **search accelerator with a glass-box audit trail** over *known*
oncology pharmacology — strong for prioritizing and explaining candidates, weak
for novelty, and biased toward promiscuous "hub" drugs you already know about.

It is **not** a truth oracle, an efficacy/safety predictor, or a novel-target
discovery engine. Do not pitch it as "AI that finds new cures."

---

## The three things it genuinely provides

### 1. Search acceleration (strongest claim — measured)
The repurposing ranker concentrates real hits at the top of the list. Under the
strict protocol (`remove_direct_labels`, so the direct Drug→Disease label is
removed before scoring):

- Screening the **top 5%** of 1,560 pairs catches **73%** of known hits — a
  **14.5× enrichment** over screening blindly.
- Catch **80%** of known hits by screening **7%** of the list (skip 93%).

Reproduce: `python -m validation.enrichment_funnel`.

This is the honest value statement: *"reads 1,500 candidate pairs and hands you
the ~80 worth an afternoon, with the receipts."*

### 2. Explanation / auditability (real, and the point)
The score is not a black box with an explanation bolted on — **the score IS the
evidence**. A ranking is literally the set of Drug→Protein→Disease paths, each
carrying its own confidence, PMIDs, FDA labels, and evidence tier. A reviewer
can click each edge through to PubMed and reject it by hand. That glass-box
property is rare and is the main reason to use this over a plain ML ranker.

Reproduce: `python validation\triage.py Melanoma --drug Sorafenib`.

### 3. Honesty infrastructure (under-appreciated)
Tiered provenance (`RELATION-VERIFIED` vs `LEXICAL-COOCCURRENCE`), documented
label-leakage history, the strict label-removal protocol, and external/temporal
holdouts. The system tells you how much *not* to trust it. See `CLAUDE.md`.

---

## Honest limitations (read before believing any number)

### The categorical framing is oversold relative to what earns the metric
Topos logic, HoTT, cubical type theory, operads, the "SMT Level 4" proposal —
intellectually coherent, but **not** what produces the 0.97 AUROC. Ablate down
to *confidence-weighted mechanistic path composition + a Yoneda similarity bonus
+ binding evidence* and you keep almost all the performance. The grand framing
is scaffolding around a fairly classical graph-reasoning core. Judge the system
on the core, not the superstructure.

### Generalization to genuinely novel pairs is the real open question
- In-graph strict AUROC **0.9705**, AUPRC **0.546**.
- External (Hetionet) AUROC **0.644**, AUPRC **~0.010**.
- Temporal holdout (approvals after 2013): AUROC **0.971**, AUPRC **0.194**.

The model knows *this curated graph* very well. Top-of-list precision on truly
novel pairs is low (the Hetionet AUPRC). The temporal holdout shows the lift
does not fully collapse on unseen approvals — so the search acceleration is real
— but treat the funnel numbers as "acceleration on the curated graph," not a
novel-discovery hit rate.

### The same drugs top almost every disease (hub-drug bias)
Measured: **Imatinib is in the top-5 for 17 of 20 diseases; Sunitinib 14/20;
Afatinib 10/20.** Promiscuous multi-kinase inhibitors hit hub proteins on many
cancer pathways, so they float to the top of most diseases. This is *partly real
pan-cancer biology and partly a promiscuity/degree bias.* It is also why AUPRC
(0.55) is far below AUROC (0.97): the hubs cluster as false positives at the top.

**Mitigation shipped:** the **Disease-specific** view (UI mode, and
`python -m validation.disease_specificity <Disease>`) re-ranks by
`lift = raw score − the drug's mean across all diseases`, demoting the hubs so
disease-specific candidates surface. On Melanoma this promotes Binimetinib,
Cobimetinib, Nivolumab, Pembrolizumab (the actual approved MEK/checkpoint
drugs) above the pan-cancer kinase hubs. It is a *presentation lens*, not a
scoring change — it does not alter any AUROC.

### The audit trail is thin at the terminal hop
A trail is Drug→Protein→Disease. The Drug→Protein hops are well-cited (FDA,
ChEMBL IC50, RELATION-VERIFIED PMIDs). The terminal **Protein→Disease** hop is
the least-verified layer in the graph — frequently a literature co-mention, not
an edge-verified relation. The UI now labels this honestly (a reading note plus
a "disease link — weakest layer" tag) so a sparse last hop reads as a known data
gap, not a bug. Edge-level citation audit of these terminal edges is an open task.

### Scope
- Track A (repurposing) only. Track B (de-novo design) is a long-term goal, **not
  validated in this repo**. Do not read Track A metrics as Track B readiness.
- 78 drugs, 20 diseases, all oncology. Conclusions do not extend beyond this.
- Research prototype. **Not** clinical, translational, or regulatory validation.

---

## How to use it well

1. Run triage / the funnel to get a prioritized shortlist — that is the value.
2. Use the **Disease-specific** view to see past the pan-cancer hubs you already
   know to the candidates specific to your disease.
3. Read the evidence chains and **check the receipts** — especially the terminal
   Protein→Disease hop, which is the weakest link.
4. Treat every unlabeled pair as *unknown*, never as a confirmed negative, and
   every high score as a *hypothesis to test*, never as a prediction of efficacy.

---

## Reproduce everything in this file

```powershell
python validation\repurposing_benchmark.py --view full_typed --protocol remove_direct_labels --baselines --ci
python -m validation.enrichment_funnel
python -m validation.disease_specificity Melanoma
python validation\triage.py Melanoma --drug Sorafenib
```
