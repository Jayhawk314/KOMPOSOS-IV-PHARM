# HONEST_VALUE.md — what KOMPOSOS-IV-PHARM is actually worth

A plain-language, self-critical assessment of what this system does and does not
provide, written for anyone deciding whether it is worth their time. It is
deliberately conservative. Where it disagrees with the more enthusiastic framing
elsewhere in the repo, believe this file — every claim here is backed by an
executable check named in the text.

Last reviewed: **2026-07-31**, in an independent technical audit that reproduced
the benchmark and queried the database directly. Every metric below is measured
against the current database. The two carried-forward external-generalization
numbers did **not** survive that audit — one is not reproducible and one is stale
— and are retired in place below rather than quietly refreshed.

Corrected on 2026-07-31: terminal-hop counts, reachable-pair counts, the stale
AUPRC 0.57, the "all oncology" scope claim, the external and temporal results,
and the meaning of the printed Hits@k. Three new defects were added to the known-
defects list, including that the repository does not currently `pip install`.

---

## One-sentence version

It is a **search accelerator with a glass-box audit trail** over *known*
oncology pharmacology — strong for prioritizing and explaining candidates, weak
for novelty, and biased toward promiscuous "hub" drugs you already know about.

It is **not** a truth oracle, an efficacy/safety predictor, or a novel-target
discovery engine. Do not pitch it as "AI that finds new cures."

---

## Read this before quoting any AUROC

The system now carries **two drug cohorts**, and their numbers are *not*
comparable. Quoting the wrong one is the easiest way to get caught overstating.

| | `--cohort core` | `--cohort all` |
|---|---|---|
| Drugs | 78 curated oncology | 757 (core + 679 ChEMBL) |
| Pairs | 1,560 | 15,140 |
| Positives | 44 | 44 |
| Base rate | 2.82% | 0.29% |
All numbers below are on the **ESMC-excluded default graph** (see the ablation
section). Similarity-transfer edges are out of the scored graph because removing
them improves the ranker.

| | `--cohort core` | `--cohort all` |
|---|---|---|
| Drugs | 78 curated oncology | 757 (core + 679 ChEMBL) |
| Pairs | 1,560 | 15,140 |
| Positives | 44 | 44 |
| Base rate | 2.82% | 0.29% |
| Strict AUROC | **0.9763** | ~0.99 (inflated) |
| Strict AUPRC | **0.5920** | ~0.41 |
| Hits@20 | **0.70** | 0.40 |
| Best baseline | common-neighbor 0.7483 | common-neighbor ~0.95 |
| **Margin over baseline** | **+0.2280** | **~+0.05** |

**The full-cohort ~0.99 is an artifact — do not report it as an improvement.**
Expanding the universe added ~13,500 mostly-unscoreable pairs while the positive
count stayed at 44. Adding easy negatives inflates AUROC mechanically. The honest
tells sit in the same run: AUPRC *fell* and the margin over a trivial
common-neighbor baseline collapsed to ~+0.05.

**Quote the `core` number (0.9763, +0.23 over baseline).** That is the defensible
one. Treat the `all` cohort as a *discovery surface* for finding candidates, never
as a benchmark. Reproduce:
`python validation/repurposing_benchmark.py --view full_typed --protocol remove_direct_labels --cohort core --baselines --ci`

Two caveats belong beside that number every time it is quoted (both added
2026-07-31):

- **The printed "Hits@k" is precision@k.** `compute_hits_at_k` in
  `validation/repurposing_benchmark.py` returns `hits / min(total_positives, k)`.
  That is why the run prints Hits@5 **1.00** and Hits@10 **0.70** — a true Hits@k
  cannot fall as k grows. Say "precision@k" out loud; a reviewer will spot the
  non-monotonicity in seconds.
- **598 of the 1,560 pairs are abstentions scored 0.0, and they are inside the
  AUROC.** All are negatives. Restricted to the 962 actually-scored pairs the
  AUROC is **0.9609**; AUPRC is unchanged at **0.5920**. So about 0.015 of the
  headline is coverage rather than ranking skill. Small, but report it rather
  than be asked for it.

---

## The three things it genuinely provides

### 1. Search acceleration (strongest claim — measured)
The repurposing ranker concentrates real hits at the top of the list. Under the
strict protocol (`remove_direct_labels`, so the direct Drug→Disease label is
removed before scoring), on the `core` cohort:

- Screening the **top 5%** of 1,560 pairs catches **73%** of known hits — a
  **14.5× enrichment** over screening blindly.
- Catch **80%** of known hits by screening **6%** of the list (skip 94%).
- Catch **95%** by screening the top 10%.

Reproduce: `python -m validation.enrichment_funnel --cohort core`.

This is the honest value statement: *"reads 1,500 candidate pairs and hands you
the ~100 worth an afternoon, with the receipts."*

### 2. Explanation / auditability (real, and the point)
The score is not a black box with an explanation bolted on — **the score IS the
evidence**. A ranking is literally the set of Drug→Protein→Disease paths, each
carrying its own confidence, PMIDs, FDA labels, and evidence tier. A reviewer
can click each edge through to PubMed and reject it by hand. That glass-box
property is rare and is the main reason to use this over a plain ML ranker.

Reproduce: `python validation\triage.py Melanoma --drug Sorafenib`.

**But read "What a PMID actually means here" below before treating a citation on
a Protein→Disease edge as validation.** Those citations were gathered *after* the
edge was proposed, and a negative control shows that step carries no measurable
signal. The Drug→Protein citations (ChEMBL, FDA) are unaffected — they are
independently derived.

### 3. Honesty infrastructure (under-appreciated)
Tiered provenance (`RELATION-VERIFIED` / `RELATION-SCREENED` /
`LEXICAL-COOCCURRENCE`), documented label-leakage history, the strict
label-removal protocol, the cohort split above, and external/temporal holdouts.
The system tells you how much *not* to trust it. See `CLAUDE.md`.

This now includes a **negative control against its own evidence pipeline** (below),
which returned a null. Most systems in this space never test whether their evidence
step does anything at all. Running that control and publishing the null is the most
credible thing in this repository — it is what separates a tool that *claims* to
find new biology from one that states what it does and shows the receipts for why.

---

## Honest limitations (read before believing any number)

### The categorical framing is oversold relative to what earns the metric
Topos logic, HoTT, cubical type theory, operads, the "SMT Level 4" proposal —
intellectually coherent, but **not** what produces the AUROC. Ablate down to
*confidence-weighted mechanistic path composition + a Yoneda similarity bonus +
binding evidence* and you keep almost all the performance. The grand framing is
scaffolding around a fairly classical graph-reasoning core. Judge the system on
the core, not the superstructure.

### Generalization to genuinely novel pairs is the real open question
**Corrected 2026-07-31. The honest statement is now that external precision is
*undetermined*, not weak.** Both carried-forward numbers below failed audit.

- In-graph strict (`core`, ESMC-excluded) AUROC **0.9763**, AUPRC **0.5920**
  (2026-08-01). Reproduces exactly.
- External (Hetionet) AUROC 0.644 / AUPRC ~0.010 — **RETIRED, not reproducible.**
  `data/external/` does not exist and is gitignored, so
  `validation/external_validation.py` raises `FileNotFoundError` on a clean
  clone. The script also never passes `cohort`, so it defaulted to the `all`
  cohort — the one this file forbids quoting. Do not cite this number again
  until the inputs are restored and it is rerun on `core`.
- Temporal holdout (approvals after 2013) AUROC 0.971 / AUPRC 0.194 — **STALE.**
  Rerun 2026-07-31 it gives AUROC **0.996095**, AUPRC **0.155975**, Hits@5
  **0.0000** over 15,114 `all`-cohort pairs. Two design faults make even the new
  number uninterpretable: it removes only the *label*, leaving 2026-derived
  Protein→Disease edges in the graph, so post-cutoff literature leaks into every
  "held-out" prediction; and it runs on the forbidden cohort.
- **The negative set is contaminated with true positives.** The top-ranked
  "negative" in that run is Dacomitinib→NSCLC, FDA-approved 2018-09-27. Also in
  the top 20: Lorlatinib, Brigatinib and Amivantamab in NSCLC, Avapritinib in
  GIST — all approved, all scored as false positives. The 44-label gold set
  covers only the 78 curated drugs, while the cohort contains 679 ChEMBL drugs
  with real approvals that were never labelled.

The model knows *this curated graph* very well. What happens on genuinely novel
pairs **is currently unmeasured**, because the evaluation cannot tell a false
positive from an unlabelled true one. That is not evidence that precision is
good; it is a statement that the question is open. Treat the funnel numbers as
"acceleration on the curated graph," never as a novel-discovery hit rate, and
make no precision claim in either direction until a complete, versioned label
set exists.

### The same drugs top almost every disease (hub-drug bias)
Measured on the 757-drug cohort: **Imatinib is top-5 for 14 of 20 diseases;
Sunitinib 10/20; Afatinib 7/20.** Promiscuous multi-kinase inhibitors hit hub
proteins on many cancer pathways, so they float to the top of most diseases. This
is *partly real pan-cancer biology and partly a promiscuity/degree bias.* It is
also why AUPRC (0.5920) is far below AUROC (0.9763): the hubs cluster as false
positives at the top. (The 0.57 previously quoted here was the pre-ESMC-removal
figure and is retired.)

Hub dominance fell slightly from the previous review (Imatinib was 17/20) only
because the expanded cohort gives it more competition — the bias itself is unchanged.

**Mitigations shipped:** the **Disease-specific** view re-ranks by
`lift = raw score − the drug's mean across all diseases`, demoting the hubs. The
**Non-obvious candidates** view (below) attacks the same problem from the
literature side. Both are *presentation lenses*, not scoring changes — neither
alters any AUROC.

### The audit trail is thin at the terminal hop — this is now the binding constraint
A trail is Drug→Protein→Disease. The Drug→Protein hops are well-cited (FDA,
ChEMBL, RELATION-VERIFIED PMIDs). The terminal **Protein→Disease** hop is the
least-verified layer and is now the main thing limiting the system:

Re-measured **2026-08-01**, after 23 textbook driver edges were added (2 hormone
receptors, 21 Cancer Gene Census / WHO-classification drivers). The figures from
2026-07-31 are superseded; the ones before that (158 proteins, 1,842 pairs) were
simply wrong. On the **default ESMC-excluded scored graph**:

- **111 non-drug/non-disease nodes** carry any disease edge at all.
- Those nodes carry **806 terminal edges**, of which **746 are `associated_with`**
  — a co-occurrence relation, **not** a mechanistic claim — and **60 are
  directed (`driver_of`), spanning 45 distinct sources**. That is 7.4% directed,
  up from 4.7% that morning.
- **153 of 757 drugs** can complete a Drug→Protein→Disease path (was 128). The
  other **604 remain stranded** with target pharmacology but no route to a
  disease.
- Through a **directed** terminal hop, **191 pairs** are reachable (was 138).
  That is the size of the mechanistically grounded surface, and every candidate
  the system produces traces back to one of the 60 directed edges — so their
  citation quality is the ceiling on everything it can claim. Of the original 37,
  only 10 carried a `[RELATION-VERIFIED]` citation; the 23 added on 2026-08-01
  cite the WHO classification or the COSMIC Cancer Gene Census.

Getting *directed* protein→disease edges (`driver_of` and similar) is the highest-value
next step for this repo. More `associated_with` edges add coverage, not credibility.

### The similarity-transfer layer was measured and removed (2026-07-21)

422 Protein→Disease edges were derived by ESMC protein-embedding similarity, not
observed: "ERBB2 ≈ BCL2 (0.88), BCL2 is linked to AML, therefore ERBB2 is linked
to AML." These were the natural candidates for "connections the literature hasn't
made yet." An ablation (`python -m validation.esmc_ablation --cohort core`) tested
whether they help:

| | Full graph | ESMC removed |
|---|---|---|
| AUROC | 0.9691 | **0.9784** |
| AUPRC | 0.5661 | **0.6128** |
| Hits@20 | 0.65 | **0.70** |

*Those are the figures as measured on 2026-07-21. The graph has since gained 23
driver edges, so the current headline is 0.9763/0.5920; the ablation's CONCLUSION
— that the similarity-transfer layer is not load-bearing — is unaffected.*

Removing them **improves** every metric — the layer is mild noise, not signal.
(It also inflated the apparent margin over baselines: on the cleaner graph the
common-neighbor baseline jumps to 0.743, so the honest margin is +0.24, not +0.36.
The noise was hurting trivial baselines more than the model.)

Consequence, and it answers the novelty question directly: the similarity-inferred
edges — the ones most likely to be "not in PubMed" — are exactly the ones the
ranker does **better without**. Novelty from that source is noise. So ESMC edges
are now **excluded from the default scored graph** (kept in the DB, tagged
`[EMBEDDING-INFERRED]`, restorable with `--include-inferred`). The honest
non-obvious signal is under-*discussed* real mechanism, not un-*evidenced*
inference. See `data/ESMC_ABLATION_RESULT.json`.

### What a PMID actually means here (measured, 2026-07-20)

This is the most important limitation in this file, and it is measured rather than
suspected.

**The problem.** Protein→Disease edges from the discovery pipeline are built by
proposing the edge FIRST and then searching PubMed for a sentence that supports it.
PubMed holds ~37 million abstracts, so for almost any protein and any common cancer
some supporting sentence exists. "We searched and found support" may therefore carry
no information at all — it may simply measure how densely the corpus is written.

**The test.** A permutation negative control: take the exact proteins probed in a
real Glioblastoma run, but pair each with a RANDOM DIFFERENT disease, then run the
identical pipeline. Same proteins, same disease vocabulary, same query construction,
same gate — only the specific pairing is destroyed.

| | grounded (gate AGREE) |
|---|---|
| Real pairings | 15/120 = **12.5%** |
| Randomly scrambled pairings | 9/120 = **7.5%** |

Fisher exact two-sided **p = 0.28**; difference 5.0 pp, 95% CI **[−2.6, +12.6] pp**
— the interval **includes zero**.

Hand-adjudicating all nine scrambled hits, roughly 3–4 are *genuinely valid*
directed claims — about the same ~1/3 survival rate as the real run's 5/15. The
clearest is a random pairing:

> "Erythropoietin drives breast cancer progression by activation of its receptor
> EPOR." — a clean, correct driver claim, from a pair the graph never proposed.

**The conclusion.** Post-hoc PubMed grounding carries essentially **no measurable
information** about whether the graph's proposal was correct.

Read that precisely. It does **not** mean the discovered edges are false — EPOR
really does drive breast cancer. It means the *proposal step added no signal*: you
would find about as many true edges by picking pairs at random. So this pipeline is
**literature mining, not prediction validation**, and must never be described as the
latter.

**Scope of the damage.** The Drug→Protein layer (ChEMBL, FDA labels) is
independently derived and entirely unaffected. This applies specifically to the
Protein→Disease layer: the `associated_with` edges, the 110 merged discoveries, and
all discovery output.

**So what is a PMID on those edges worth?** Not "this is validated." It is worth
*"this is not absurd, and here is where to start reading."* That is still useful to
a researcher triaging candidates. It is a much smaller claim than a citation
normally implies, and it should be stated as such wherever those edges surface.

**Honest caveat on the control itself.** N = 120 per arm, so the CI reaches +12.6 pp
and a moderate real effect is not excluded; a larger run could detect one. It tested
one relation (`driver_of`) against one real disease (Glioblastoma). Treat it as
strong evidence for a null, not proof of one — while noting the burden of proof sits
with the claim that grounding validates, and that claim currently has nothing behind it.

**If you want real validation** it must come from a signal the grounding search
cannot reach: a temporal holdout on edges published after a cutoff, or an
independent external KG.

Reproduce: `python scripts\grounding_negative_control.py --against data\DISCOVERED_DRIVER_GBM.json`

### Automated directed-relation extraction was tried and failed

To improve the Protein→Disease layer, a dependency-parse extractor with negation,
hedge, polarity and attribution guards was built (`komposos_kg/directed_extractor.py`).
On its 13-case AML tuning set it reached 4/4 precision. On a held-out Glioblastoma
set it scored **precision 3/9 = 0.33 with recall 3/5**, against the existing lexical
gate's **0.33 precision with 5/5 recall** — same precision, worse recall. The tuning
result was overfitting to 13 examples.

It is marked EXPERIMENTAL and is opt-in only (`--extractor directed`); the calibrated
`associated_with` path is untouched. The lesson recorded there: more hand-written
rules do not fix this. Biomedical abstracts have too many ways to mention a gene
without asserting anything about it. See `data/DRIVER_OF_HELDOUT_GBM.json` for the
per-case failure analysis.

### Scope
- Track A (repurposing) only. Track B (de-novo design) is a long-term goal, **not
  validated in this repo**. Do not read Track A metrics as Track B readiness.
- 757 drugs and 20 diseases. **"All oncology" is not accurate**: the disease set
  contains `Type2_Diabetes` and `Li_Fraumeni_Syndrome` (a cancer-predisposition
  syndrome, not a tumour type), and `Metformin → Type2_Diabetes` is one of the 44
  positives. Conclusions do not extend beyond this set.
- **6 of the 20 diseases carry zero positives** — AML, Glioblastoma,
  Ewing_Sarcoma, Prostate_Cancer, Soft_Tissue_Sarcoma, Li_Fraumeni_Syndrome — so
  disease-specific performance is undefined for 30% of the graph. AML in
  particular has **no `treats` label at all** and only two proteins (FLT3, TOP2A)
  reaching it through a directed edge.
- Research prototype. **Not** clinical, translational, or regulatory validation.

### Known defects, unfixed
- **Quantitative columns are empty.** `quantitative_value` / `sample_size` read
  NULL for every row, including 60 edges that carried real hazard ratios and
  mutation frequencies before the integrity audit. The UI and schema still imply
  this data is present. Some of it was rightly dropped (an Atezolizumab hazard
  ratio of 0.0 is impossible; `mutation_frequency` on a drug→disease `treats` edge
  is a unit mismatch), but the clean values went with it.
- **Salt-form duplication.** ChEMBL ships "Dacomitinib" and "Dacomitinib
  Anhydrous" as separate drugs. `validation/nonobvious.py` normalizes these;
  `validation/disease_specificity.py` does **not**, so a salt form can occupy its
  own slot in the hub table. Cosmetic, but it looks sloppy to a reviewer.
- **The `random` baseline scores ~0.55, not 0.50**, because it is a single
  unseeded draw rather than an average over draws.
- **Gene-symbol collisions in literature grounding.** The negative control
  grounded `AR` (androgen receptor, in this graph) on a sentence about
  **β2-adrenergic receptor**. Symbol matching is word-boundary but not
  sense-disambiguated, so short overloaded symbols (AR, MET, PC, ACE) can ground
  on the wrong protein entirely.
- **The repository does not install.** `pyproject.toml` declares
  `build-backend = "setuptools.backends._legacy:_Backend"`, a module that exists
  in no version of setuptools, so any build fails with `ModuleNotFoundError`. And
  `[tool.setuptools.packages.find]` sets `include = ["core*"]`, so a successful
  build would ship only `core/`. `requirements.txt` omits `scipy`,
  `scikit-learn`, and `pytest`; there is no CI. The benchmark runs fine from a
  checkout — it is *packaging*, not the science, that is broken — but a stranger
  cannot `pip install` this. (Found 2026-07-31.)
- **Dempster-Shafer conflict is structurally always zero.**
  `oracle/evidence_combination.py` encodes each strategy as
  `m({exists}) = c, m(Θ) = 1 − c` and never assigns mass to `not_exists`, so
  Dempster conflict cannot be non-zero. Strategies at 0.9 and 0.1 combine to
  conflict `K = 0.0` and a pignistic score of **0.955** — higher than either.
  The module docstring claims it "detects the conflict explicitly"; it does not.
  `combine_predictions()` in the same file is dead and raises `TypeError` twice.
  Not wired into `make_strategies()`, so **no benchmark number is affected**.
- **The combination layer is a separate, unvalidated system.** It runs on
  `data/omnipath_signed.tsv` (OmniPath), not on `tier1.db`, so it inherits none
  of the measured performance above. Its "8/8 direction" control is eight
  author-chosen perturbations with author-written expected signs in the same
  file, and its one labelled external test — CEGv2/NEGv1 essentiality — scores
  **AUROC 0.36**, below chance. `oracle/CELL_FATE_INTERPRETER.md` says so; read
  it before quoting anything from that layer.
- **`promot` matched `promoter`.** Fixed in the new directed extractor, still
  present in the legacy `RELATION_KEYWORDS` used for `activates` and `driver_of`.
  It has not contaminated the shipped graph (0 of 110 edges with proof sentences
  are affected) because the merged batch was all `associated_with`, whose
  vocabulary lacks that keyword. It would bite the next `activates` run.

---

## Finding what a researcher does *not* already know

Ranking by score alone surfaces what everyone already knows — the top of that
list is pan-cancer hubs whose evidence trail is short and famous. An audit trail
is only worth something when it points somewhere the reader has not already been.

The **Non-obvious candidates** view (UI mode, and
`python -m validation.nonobvious --disease <Disease>`) ranks on two axes:

    support  × novelty
    ↑ strength of a real, composed Drug→Protein→Disease chain
              ↑ 1 − log(PubMed co-mentions)/log(2000)

Novelty is measured **outside the graph** via live PubMed co-mention counts,
because deriving it from the same graph that produced the ranking would be
circular. A textbook pair (Vemurafenib/Melanoma, ~1,950 papers) scores ~0; an
unwritten pair scores ~1.

Every candidate ships with its full per-edge audit trail and a `mech` / `assoc`
flag marking whether the chain reaches the disease through a directed mechanistic
relation or mere co-occurrence. **Filter to `mech` before taking anything
seriously** — for Melanoma that cuts 12 candidates to 7.

Honest caveats, which the UI also displays:

- **Absence of literature is not evidence of efficacy.** A low co-mention count
  can equally mean "tried, failed, never published" or "ambiguous drug name."
- Support scores cluster narrowly (~0.76–0.89), so novelty does most of the
  ranking work. This is closer to *"sort plausible drugs by obscurity"* than a
  true two-axis discrimination.
- It is a **triage queue for a human**, not a prediction.

---

## How to use it well

1. Run triage / the funnel to get a prioritized shortlist — that is the value.
2. Use the **Disease-specific** view to see past the pan-cancer hubs.
3. Use **Non-obvious candidates**, filtered to `mech`, to find pairs that are
   well-supported but under-discussed — the ones that add something to your argument.
4. Read the evidence chains and **check the receipts** — especially the terminal
   Protein→Disease hop, which is the weakest link. Treat a PMID on that hop as a
   reading suggestion, not as validation; the negative control below explains why.
5. Treat every unlabeled pair as *unknown*, never as a confirmed negative, and
   every high score as a *hypothesis to test*, never as a prediction of efficacy.

---

## Reproduce everything in this file

```powershell
python validation\repurposing_benchmark.py --view full_typed --protocol remove_direct_labels --cohort core --baselines --ci
python validation\repurposing_benchmark.py --view full_typed --protocol remove_direct_labels --cohort all  --baselines --ci
python -m validation.enrichment_funnel --cohort core
python -m validation.disease_specificity Melanoma
python -m validation.nonobvious --disease Melanoma --top 12
python validation\triage.py Melanoma --drug Sorafenib
python scripts\grounding_negative_control.py --against data\DISCOVERED_DRIVER_GBM.json
```

Supporting evidence files:

| File | What it holds |
|---|---|
| `data/GROUNDING_NEGATIVE_CONTROL.json` | The null result, statistics, per-case adjudication |
| `data/DRIVER_OF_ADJUDICATION.json` | 13 AML candidates, 4 verified, 6 failure modes named |
| `data/DRIVER_OF_HELDOUT_GBM.json` | Held-out set showing the directed extractor did not generalize |
