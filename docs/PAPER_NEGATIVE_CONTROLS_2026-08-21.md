# Negative controls for knowledge-graph drug repurposing: three falsifications, a candidate audit, and a trial graveyard

**James Ray Hawkins**
Independent researcher · jhawk314@gmail.com
Code and data: https://github.com/Jayhawk314/KOMPOSOS-IV-PHARM

*Draft prepared for preprint submission, 2026-08-21. Supersedes the 2026-05-13
draft, whose framing and numbers are retired.*

---

## Abstract

Knowledge-graph drug repurposing systems routinely report areas under the ROC
curve above 0.95. Far fewer report the control experiments that would establish
what those numbers mean. We built such a system — an auditable, fully
provenance-tracked graph of 2,462 edges over 757 drugs and 20 diseases — and
then ran the controls on it. It attains AUROC 0.9763 (AUPRC 0.5920) on a
78-drug curated cohort under a strict label-removal protocol, comfortably above
every graph-topology baseline. We report three experiments that constrain what
that performance is.

First, an **ablation**: removing all 422 protein-embedding
similarity-transfer edges *improved* the ranker (AUROC 0.9691 → 0.9784, AUPRC
0.5661 → 0.6128), while improving a trivial common-neighbour baseline far more,
collapsing the honest margin from +0.356 to +0.236. The inferred edges most
likely to represent "connections not yet in the literature" were the ones the
system performed better without.

Second, a **permutation control** on post-hoc literature grounding: real
protein-disease pairings were supported by a retrieved PubMed sentence 12.5% of
the time, randomly scrambled pairings 7.5% of the time — statistically
indistinguishable (Fisher exact p=0.28, 95% CI on the difference −2.6 to
+12.6 percentage points). Hand-adjudication found comparable *quality* in both
arms (~1/3 valid). Post-hoc citation measured corpus density, not the proposed
relationship.

Third, a **pre-registered external adjudication**. We froze a candidate set, a
disease-to-cell-line correspondence, and every decision threshold, committed
them with cryptographic hashes *before writing the scoring code*, and then
scored against PRISM Repurposing cell-line viability. No candidate showed
lineage-selective activity at any quality threshold. Zero of 60 candidate
standings changed.

We further report a **human audit** of the 60 top-ranked candidates — 1 lead
with an early human signal, 12 structurally invalid, 16 already clinically
tested, 17 with no evidence findable in either direction — and a **trial
graveyard**: of 77 registered trials attached to those candidates, 75% never
posted results, every recorded stop reason was operational or financial rather
than efficacy or safety, and 13 trials have posted registry results with no
publication of any kind. The last finding generalises beyond this system: a
novelty signal computed from literature absence cannot distinguish an
unexplored hypothesis from a quietly abandoned one.

We argue that the AUROC in this literature is substantially a measure of
curation quality, that post-hoc grounding and similarity-inferred edges should
be assumed uninformative until controlled, and that pre-registration is both
cheap and necessary. All controls are reproducible from a single clone with one
command each.

**Keywords**: drug repurposing, knowledge graphs, negative controls,
pre-registration, reproducibility, publication bias, meta-research

---

## 1. Introduction

Computational drug repurposing has an evaluation problem, and it is not a
shortage of metrics.

The standard result in this literature is a held-out ranking score on a curated
biomedical knowledge graph. Rephetio [1] established the template; a large
subsequent literature has followed it, and recent reviews [2,3] count dozens of
systems reporting AUROC between 0.85 and 0.99. The metrics are computed
correctly. What is usually missing is any experiment that would distinguish
between three very different explanations for a high score:

1. the method recovers real biology that generalises to new pairs;
2. the method recovers the *curation* — the graph was assembled by people who
   already knew the answers, and any competent traversal finds them; or
3. the evaluation is contaminated, because unlabelled pairs are scored as
   negatives when many of them are simply unlabelled positives.

These are not exotic concerns. They are the ordinary failure modes of the
design, and separating them requires controls rather than more metrics.

This paper is an attempt to do that on a system we built ourselves, with the
result that three of its components did not survive. We report the controls
rather than the system, because the controls are the transferable part.

### 1.1 What we are and are not claiming

We are **not** claiming that our system is unusually bad. Its headline numbers
are ordinary for the field, and its curated backbone is unusually well
provenance-tracked: every edge carries a source identifier, and the terminal
disease-linking edges have been individually audited. If these controls
embarrass the system, the natural inference is not that this system is worse
than its peers but that the controls are rarely run.

We are also **not** claiming that a negative control invalidates a method.
Removing embedding edges improved our ranker; that is a fact about our graph, at
our scale, with our labels. What transfers is the *experiment*, not the sign of
the result.

### 1.2 Contributions

1. An **ablation protocol** for inferred edges, with a result showing that a
   plausible-sounding similarity-transfer layer was net harmful (§3).
2. A **permutation control** for post-hoc literature grounding, showing it
   carries no measurable signal about the proposed relationship (§4).
3. A **pre-registration protocol** for external adjudication, with the frozen
   artefacts committed before the scoring code was written, and the resulting
   null (§5).
4. A **human audit** of what the top of a ranked list actually contains (§6).
5. The **trial-graveyard** measurement and its consequence for novelty
   estimation (§7).
6. A set of concrete recommendations, and the observation that all of the above
   cost days rather than months (§9).

---

## 2. The system, in brief

Only enough detail to interpret the controls; full architecture is in the
repository.

**Graph.** 2,462 directed edges over drugs, proteins and diseases, stored as
SQLite. Node types: 757 drugs, 20 diseases (oncology-dominated but not
exclusively so — the set includes Type 2 diabetes and Li-Fraumeni syndrome), and
intermediate proteins. Every edge carries a `provenance` string and an evidence
tier. By source: ChEMBL 881, PubMed-derived 433, protein-embedding
similarity 422, curated cancer-protein lists 393, KEGG 72, FDA labels 61,
protein-protein interaction 22, COSMIC Cancer Gene Census 18, activity-based
protein profiling 15, DepMap 9, WHO classification 3.

**Predictions** are Drug→Protein→Disease paths. A candidate is scored by an
ensemble of path-composition and structural strategies with multiplicative
confidence propagation. Ablation of the ensemble shows path composition
dominates; the higher categorical machinery in the codebase is scaffolding and
we do not defend it here.

**Evaluation.** The strict protocol (`remove_direct_labels`) deletes the direct
Drug→Disease edge before scoring, so the ranker cannot read the answer. The
headline cohort is `core`: 78 curated drugs × 20 diseases = 1,560 pairs, with
44 curated `treats` positives.

**Headline performance.** AUROC 0.9763, AUPRC 0.5920. Precision@5 = 1.00,
precision@10 = 0.70, precision@20 = 0.70. Of 1,560 pairs, 962 receive a nonzero
score and 598 are abstentions scored 0.0; restricting to scored pairs gives
AUROC 0.9609. Best trivial baseline is common-neighbour at 0.7483, so the margin
is **+0.2280**.

**A note on the second cohort.** Expanding to all 757 drugs gives AUROC 0.9944 —
a better-looking number whose margin over common-neighbour is only +0.0251. We
quote the smaller, less flattering figure throughout, because the larger cohort
adds ~13,500 mostly unscoreable pairs while the positive count stays at 44. Any
system reporting a single AUROC without naming its cohort is not reporting
enough.

### 2.1 The structural constraint that governs everything

The graph's binding constraint is its terminal hop. On the default scored graph,
806 Protein→Disease edges connect 111 non-drug nodes to diseases. Of these,
**746 are `associated_with`** — co-occurrence, not mechanism — and only **60 are
directed `driver_of`**, spanning 45 source proteins. Of 757 drugs, 153 complete
any Drug→Protein→Disease path; through a *directed* terminal hop only 191 pairs
are reachable.

Every candidate this system emits descends from those 60 edges. Their quality is
therefore the ceiling on everything downstream, and §4 is in effect a measurement
of how that ceiling was built.

We also note that `quantitative_value` is populated on **0 of 2,462 edges**.
There is not one measured quantity in the scored graph; every edge asserts
something a human wrote down. This is typical of the genre and is the reason
§5's external adjudication mattered enough to pre-register.

---

## 3. Control 1 — Ablating similarity-inferred edges

### 3.1 Motivation

Embedding-based similarity transfer is a standard way to densify a sparse
biomedical graph: embed proteins, find neighbours, copy their disease
associations across. It is also the mechanism most often credited with
*novelty*, since transferred edges are by construction not stated in the
literature. We had 422 such edges, generated by a protein language model
(ESM-C), all of them Protein→Disease.

The obvious question — are they load-bearing? — is answered by deleting them.

### 3.2 Protocol

Strict `remove_direct_labels`, `core` cohort, positives held fixed at 44,
scoring the graph with and without the 422 edges. One command:

```
python -m validation.esmc_ablation --cohort core
```

### 3.3 Result

| Configuration | Edges | AUROC | AUPRC | Precision@20 | Best baseline | Margin |
|---|---:|---:|---:|---:|---:|---:|
| Full graph | 1,523 | 0.9691 | 0.5661 | 0.65 | 0.6132 | +0.3558 |
| Embeddings removed | 1,101 | **0.9784** | **0.6128** | **0.70** | 0.7429 | **+0.2355** |

Removing the layer improved every metric of the system. It is not merely
decorative; it was **mildly harmful**.

The second-order effect is the more interesting one. The common-neighbour
baseline improved much more than the model did (0.6132 → 0.7429). The embedding
edges were graph noise that a trivial baseline handled *worse* than the model
did, which inflated the apparent margin. The honest advantage over a trivial
baseline is **+0.236, not +0.356** — a third of the claimed edge was an artefact
of noise the baseline coped with badly.

### 3.4 Interpretation

This also settles a question we had been asking the wrong way. The
similarity-inferred edges are precisely the ones most likely to represent
"connections not in PubMed," and they are exactly the ones the ranker performs
better without. In this graph, novelty from that source is noise rather than
signal.

We removed them from the default scored graph and retained them behind an
explicit `[EMBEDDING-INFERRED]` tag. **A margin computed against a baseline that
the noise harms more than the model is not a margin.** Any system reporting a
lift over baselines should ablate its inferred layers and re-report, because the
baseline's degradation may be doing the work.

---

## 4. Control 2 — Permuting post-hoc literature grounding

### 4.1 Motivation

A common and intuitively reasonable validation step: after the graph proposes a
relationship, search PubMed for a sentence supporting it. If one is found, mark
the edge grounded. This *feels* like validation. The question is whether the
grounding rate depends on the proposal being correct.

The control is a permutation: hold the proteins fixed, randomly reassign the
diseases, and run the identical retrieval pipeline. If scrambled pairs ground at
the same rate, the pipeline is measuring how much has been written about those
entities — corpus density — and not whether the specific relationship holds.

### 4.2 Protocol

120 real `driver_of` proposals and 120 permuted pairs (seed 20260720), same
retrieval, same keyword-based relation screen, same verdicts. Reproduced by:

```
python scripts/grounding_negative_control.py
```

### 4.3 Result

| Arm | Probed | Grounded | Rate |
|---|---:|---:|---:|
| Real pairings | 120 | 15 | **12.5%** |
| Permuted pairings | 120 | 9 | **7.5%** |

Fisher exact two-sided **p = 0.282**; difference 5.0 percentage points, 95% CI
**[−2.6, +12.6]**. The interval includes zero.

Rates alone could hide a quality difference, so we hand-read all nine permuted
"grounded" hits. Roughly three to four are genuinely valid directed claims —
about the same ~1/3 survival rate as the real arm (5 of 15). Examples from the
**randomly paired** arm:

- *"Erythropoietin drives breast cancer progression by activation of its
  receptor EPOR"* — a clean, valid driver claim, from a random pairing.
- *"OPRK1 drives SLC9A3R1 progression to neuroendocrine prostate cancer."*
- *"IFNα activates TYK2/STAT/HSPA5 signaling to promote NSCLC cell proliferation
  and metastasis."*

The failure modes were also instructive, and are generic to keyword-based
relation screens:

- **Entity collision.** `AR → Colorectal_Cancer` was supported by a sentence
  about the β2-**adrenergic** receptor (β2-AR); the graph's `AR` is the
  **androgen** receptor. A string match on a two-letter symbol crossed two
  unrelated proteins.
- **The `promoter` artefact.** Sentences about *promoter* CpG-island methylation
  repeatedly matched a screen looking for the verb *promotes*.
- **Subject drift.** `MMP1 → Pancreatic_Cancer` came from "PRKRA promotes
  pancreatic cancer progression by upregulating MMP1" — the asserted subject is
  PRKRA; MMP1 is downstream.

### 4.4 Interpretation

Post-hoc PubMed grounding carried essentially no information about whether the
proposal was correct. You would find about as many true edges by picking
protein-disease pairs at random.

This does **not** mean the grounded edges are false — EPOR really does drive
breast cancer progression. It means the *proposal step* added no measurable
value, and that a grounded citation means "not absurd, start reading here"
rather than "validated." The pipeline is literature mining, and must not be
described as prediction validation.

We consequently do not treat a PMID on a Protein→Disease edge as support.
Drug→Protein citations from ChEMBL and FDA labels are independently derived and
are unaffected by this result.

---

## 5. Control 3 — A pre-registered external adjudication

### 5.1 Motivation

Sections 3 and 4 are internal. Neither answers the question that matters: does
the ranking correspond to anything measured outside the graph?

This system had never touched external ground truth. Its label set covers 64 of
15,140 possible pairs (0.42%), 44 of them inherited without citation. A
previously reported external benchmark was retired when its inputs proved absent
from the repository, and a temporal holdout was found to leak post-cutoff
literature into every "held-out" prediction *and* to run on the wrong cohort —
its top-ranked "negative" was an indication that had been FDA-approved since
2018.

That history is exactly why the next external test had to be pre-registered.

### 5.2 Pre-registration protocol

We used PRISM Repurposing 19Q4 [4]: pooled viability screening of ~1,448
compounds at eight doses across 568 cancer cell lines. It is a good adjudication
surface because it deliberately includes non-oncology drugs, and 54 of our 60
reviewed candidates are approved drugs proposed for a new cancer indication.

The essential design choice was **selectivity, not potency**. A compound that
kills every lineage is nonspecific cytotoxicity; one that kills only the
predicted lineage is signal. That contrast is itself a built-in negative control.

The freeze, in order, and this order is the claim:

1. A hand-written **disease-to-lineage correspondence**, recording for each of
   16 diseases either an accepted identification with its type
   (`DIRECT`/`NEAR`/`SUPERSET`), a justification, and a known discrepancy — or
   an explicit refusal.
2. A **pre-registration** naming the frozen candidate set, the primary endpoint
   (dose-response AUC), the statistic (two-sided Mann-Whitney U of target
   lineage versus all others), the multiplicity correction (Benjamini-Hochberg),
   every numeric threshold, and the verdict vocabulary.
3. Both files **committed with SHA-256 hashes** — the pre-registration pinning
   the correspondence by hash.
4. **Only then** was the scoring code written.

The commit history is the evidence: commit `dd59140` contains the freeze;
`5fdb40e`, which introduces the scoring module, comes after it.

Reconnaissance before freezing read **only metadata** — compound names and
cell-line lineages — never a viability matrix, so coverage was knowable without
seeing any outcome.

### 5.3 Correspondence, and the refusals

Naming which cell lines "are" a clinical disease is the step where this kind of
study usually goes quietly wrong. We required every identification to be written
down and typed. Of 16 diseases, 10 were accepted and 6 refused:

| Refused | Why |
|---|---|
| CLL, AML, myelofibrosis, multiple myeloma (12 pairs) | **PRISM 19Q4 contains zero haematological cell lines** — 568 adherent lines across 24 solid-tissue lineages, in both screens |
| GIST (4 pairs) | PRISM's `gastric` lineage is adenocarcinoma; GIST is a KIT/PDGFRA-driven mesenchymal tumour of the gut wall. Identifying them on the shared word "stomach" would join two different cells of origin |
| Li-Fraumeni syndrome (6 pairs) | A germline predisposition syndrome, not a tumour indication — already flagged as a category error by the audit in §6 |

Accepted identifications were typed honestly: only melanoma is `DIRECT`; NSCLC is
`NEAR` (PRISM's own `lung_NSC` annotation, but a clinical indication is not a
panel of 90 adherent lines); the remaining eight are `SUPERSET`, meaning the
result is a statement about the lineage rather than the clinical entity —
`glioma` includes grade II–III tumours that are not glioblastoma, `kidney` is
unsubtyped and may include non-RCC tumours.

Consequent strata: 16 pairs headline-eligible, 6 underpowered (soft tissue has
5 cell lines), 5 with single-dose data only, 11 whose compound was never
screened (3 of them biologics a small-molecule assay cannot test), and 22 with
no adjudication surface at all.

### 5.4 Result

**No candidate showed lineage-selective activity, at any quality threshold.**

| Curve-fit `r²` floor | Scorable | Selective | No selectivity | Inconclusive |
|---|---:|---:|---:|---:|
| **0.5 (pre-registered)** | 3 | **0** | 3 | 19 |
| 0.3 (sensitivity) | 6 | **0** | 6 | 16 |
| 0.0 (sensitivity) | 11 | **0** | 11 | 11 |

The sensitivity rows are reported for transparency; the pre-registered floor is
0.5 and stands as the result. **Zero of 60 candidate standings changed.**

The frozen rule demonstrably did work. Dacomitinib→glioblastoma reached
BH q = 0.002 — but with a selectivity delta of **−0.093**, meaning glioma lines
were *less* sensitive than other lineages. Because the pre-registered rule
required significance **and** the correct direction, it was recorded as no
selectivity. Without the direction requirement, a significant result pointing
the wrong way was available to be read as a hit.

### 5.5 Three thresholds we froze badly, reported rather than retuned

A pre-registration is only meaningful if you honour it when it hurts.

1. **An unenforceable requirement.** We froze `require_curve_convergence = true`.
   The shipped dataset has no `convergence` column, though its own README
   documents one; enforcing it failed 100% of rows. We recorded a declared
   deviation (`WAIVED_COLUMN_ABSENT`) rather than editing the frozen file. The
   waiver is defensible only because the absence was discovered in the file
   header, before any verdict was computed — it is not outcome-dependent.
2. **A biased quality filter.** We froze `r² ≥ 0.5`. Median curve `r²` across
   candidate compounds is 0.247, so the floor retains 26% of curves — and
   retains them *non-randomly*, because an inactive compound in a resistant line
   produces a flat curve with low `r²` by construction. The filter
   preferentially keeps lines where the drug did something, biasing the very
   contrast it feeds. A future pre-registration must choose a quality criterion
   uncorrelated with the effect being measured.
3. **A weak control-on-the-control.** We pre-registered that known broad
   cytotoxics must trip the pan-lineage flag. Only oxaliplatin did (median
   AUC 0.795); cisplatin (0.912) and carboplatin (0.873) did not. The rule
   required merely that *some* expected cytotoxic fire, so the run is valid as
   written — but the built-in negative control is weaker than intended.

### 5.6 What this null does and does not mean

- **It is not a precision estimate.** 16 pairs pre-registered, 3 measurable
  under the frozen rule. No AUROC, AUPRC or precision may be computed from it.
- **Cell lines are not patients.** A null in a dish is not clinical failure and
  retires no candidate. Cell-line panels notoriously fail to predict clinical
  outcome in both directions.
- **Coverage was the binding limit, not the result.** 22 of 60 pairs had no
  adjudication surface; 11 compounds were never screened. **Absence is recorded
  as absence, never as inactivity.**
- **Labels, not features.** These results are read by nothing in the scored
  path, enforced by a test that scans the scoring packages. Folding measured
  outcomes into the ranker would destroy the only independent test of it we have.

The honest summary: the first external adjudication in this project's history
executed as designed and returned nothing. That is a smaller claim than a
refutation and a much smaller claim than a validation, and it is the claim the
data supports.

---

## 6. What the top of the ranked list actually contains

Metrics describe a list; they do not describe what is *in* it. We took the 60
top-ranked candidates from the target zone and had a human check each one:
graph route, direction of effect, prior human testing, results, and primary
literature.

| Outcome | n |
|---|---:|
| Lead with an early human signal | **1** |
| Structurally invalid | **12** |
| Already clinically tested (not novel) | **16** |
| No direct evidence findable, in either direction | **17** |
| Intermediate states (under review, preclinical only, contradicted) | 14 |

The 12 structural failures are the most useful part, because they are bugs
rather than biology:

- Six rows proposed treating **Li-Fraumeni syndrome**, a germline predisposition
  syndrome represented in the graph as though it were a tumour indication.
- One row used a **drug as the intermediate node** in a Drug→Protein→Disease
  path.
- Several require a mutation the path does not encode (KRAS G12C for adagrasib
  and sotorasib), a formulation that does not exist systemically, or rest on a
  terminal edge whose citation does not support it.
- One PMID on a terminal edge (`KDR→GIST`) **does not resolve at all**.

We stress that the audit's own vocabulary separates dimensions that a single
verdict would conflate: what evidence exists, whether the pair was tested in
humans, what the result was, and what should happen to the candidate. "No direct
evidence found" is recorded as unresolved standing — **never as a pass**. The
17 such rows are not 17 failures; they are 17 unanswered questions, which is a
different and more honest thing to report.

The single lead — atorvastatin in pancreatic cancer — has an encouraging
single-arm phase II signal but no comparator, and the idea was already in
clinical testing. The system did not originate it.

---

## 7. The trial graveyard

### 7.1 The measurement

The audit's "no evidence found" bucket prompted a check of the registered-trial
record behind these candidates. We queried all NCT identifiers attached to the
60 reviewed pairs against the ClinicalTrials.gov v2 API. All resolved.

| Disposition | n |
|---|---:|
| No results located yet (search not exhausted) | 22 |
| Results posted on ClinicalTrials.gov | 19 |
| Still running — not a hole | 18 |
| Result or derived publication linked | 12 |
| Withdrawn with confirmed zero enrolment | 6 |

**Of 77 tracked trials, 75% never posted results.** Every recorded stop reason
was operational or financial — low accrual, lost funding, sponsor bankruptcy,
drug supply — and **not one was efficacy or safety**. Among trials with posted
registry results, **13 have no publication of any kind**: their outcomes exist,
are public, and are invisible to every literature search.

Eleven trials are `COMPLETED` with no posted results and no publication at all.
They ran, finished, and reported nothing.

### 7.2 Why this breaks novelty estimation

Many repurposing systems, including ours, estimate novelty from literature
absence — typically a PubMed co-mention count. That construction assumes silence
means nobody tried.

These data show silence is heavily confounded. A drug-disease pair with a
terminated phase II and no publication looks *identical*, to a co-mention
counter, to a pair nobody ever considered. Given that 75% of the trials here
never reported and every stop was operational, the confound is not a tail case.

The consequence is directional and uncomfortable: **literature-absence novelty
is biased toward hypotheses that have already failed operationally**, because
those are exactly the ones with trials that never produced a paper.

### 7.3 What we did about it

We recovered what was recoverable and **annotated rather than adjusted**. Each
candidate now displays the disposition of its prior trials alongside an
unchanged PubMed-derived novelty score.

It is tempting to fold trial existence into the novelty term as a correction. We
deliberately did not. Choosing that weight would reproduce exactly the pattern
we elsewhere quarantine as uncalibrated hand-set coefficients, and it would make
rankings incomparable with their own history. The reader is shown both numbers
and does the weighing. That is what a glass-box system owes its user.

A candidate whose only prior trial closed for low accrual is arguably a *better*
lead, not a discarded one — the science was never tested. We are not aware of
another repurposing tool that surfaces this distinction.

### 7.4 Scope

77 trials selected by one system's own top-60 candidates is a small,
non-random sample. **The 75% figure is illustrative of this cohort, not an
epidemiological estimate**, and must not be cited as one. Trial non-reporting is
a well-studied phenomenon with an established literature and remedies [5,6]. The
contribution here is not discovering it; it is quantifying how it corrupts a
computational novelty signal, with receipts, and fixing the tool accordingly.

---

## 8. A null we decline to count

For completeness, and because selective reporting of one's own negative results
would be self-defeating: we also built a structural-coherence auditor that
composes domain-pose transformations to look for AlphaFold domain-orientation
errors, and ran it on 34 cancer-related human proteins. It produced **no
AlphaFold-specific structural contradiction**: 12 no-conflict, 5 quarantined for
high cross-domain predicted aligned error, 3 where the experimental structures
also disagreed with each other, 1 experimental-variation-only, 13 structurally
ineligible.

We report this but **do not count it as a negative control**, because it lacks
positive controls. Without a curated set of literature-documented AlphaFold
orientation errors run blind, a null is uninterpretable: it cannot distinguish
"AlphaFold is right about these proteins" from "our measurement cannot detect
error." Subsequent review also found mundane explanations for three of the four
apparent anomalies — small anchor domains swinging large ones, and in one case
domains compared across different filament protomers.

The distinction between §§3–5 and this section is the point of the paper. A
negative control requires that you could have detected the effect had it been
there. Three of our four nulls meet that bar. This one does not, and saying so
is cheaper than defending it later.

---

## 9. Discussion

### 9.1 The AUROC is substantially measuring curation

Three observations point the same way. Our margin over a trivial
common-neighbour baseline is +0.228 on the curated 78-drug cohort but collapses
to +0.025 on the 757-drug graph. Removing an inferred edge layer improved the
model while improving the baseline more. And the entire prediction surface
descends from 60 hand-curated directed edges.

A high AUROC on a curated graph is substantially a statement that the curation
was good. That is worth something — it is not nothing to assemble a graph in
which correct answers are recoverable — but it is not evidence of discovery, and
it should not be reported as though it were.

### 9.2 Recommendations

For anyone building or reviewing these systems, in rough order of cost:

1. **Ablate every inferred layer and re-report the baseline too.** Report the
   margin *after* ablation. A margin sustained by noise that hurts your baseline
   more than your model is an artefact (§3). Cost: hours.
2. **Permute any post-hoc grounding step.** If scrambled entity pairs ground at
   a comparable rate, the step is measuring corpus density (§4). Cost: hours.
3. **Pre-register before adjudicating**, and commit the freeze before writing the
   scoring code so the commit order is the evidence. Report deviations rather
   than retuning (§5). Cost: a day.
4. **Write down every entity identification.** Naming which cell lines, tissues
   or ontology terms "are" a clinical disease is where silent errors enter.
   Require a type and a stated discrepancy per identification, and permit
   explicit refusal (§5.3). GIST is not gastric adenocarcinoma; NSCLC is not a
   panel of adherent lines.
5. **Have a human read the top 50.** No metric told us that six candidates
   proposed treating a germline predisposition syndrome, or that a drug was
   serving as a protein intermediate (§6). Cost: days.
6. **Never let absence render as a pass.** Distinguish tested-and-negative from
   nothing-found. They are different states and collapsing them manufactures
   confidence.
7. **Check the registry before trusting a novelty score** (§7).

### 9.3 On publishing negative controls

Every experiment here was cheap. The most expensive, the pre-registered
adjudication, took about a day of work plus a 310 MB download. The ablation is a
single command. What makes them rare is not cost but incentive: each one can
only reduce the apparent value of the system it is run on.

We would argue the opposite is true in the long run. A system that reports its
own falsifications is one whose remaining claims can be believed, and the
discipline is what makes the surviving number — AUROC 0.9763 on a named cohort
under a named protocol — worth quoting at all.

---

## 10. Limitations

- **Single system, single graph.** The *sign* of each result is specific to this
  graph and scale. The protocols transfer; the conclusions may not.
- **Small label set.** 44 positives over 78 drugs. Confidence intervals are
  wide (AUROC 95% CI [0.9638, 0.9866]; AUPRC [0.4506, 0.7287]).
- **Open-world negatives.** Unlabelled pairs are scored as negatives but are
  unknowns. We demonstrated this concretely: a retired temporal holdout ranked
  an FDA-approved indication first among its "negatives."
- **External precision remains undetermined.** §5 is an in-vitro adjudication of
  16 pairs, not a precision estimate. We make no claim in either direction.
- **The trial sample is non-random** (§7.4).
- **The structural null is uninterpretable** without positive controls (§8).
- **Not clinical validation.** This is a research prototype for hypothesis
  triage. Nothing here supports a treatment decision.

---

## 11. Reproducibility

All results reproduce from a single clone with no manual setup. The full test
suite (249 tests) passes on a fresh clone with no network access.

```
python validation/repurposing_benchmark.py --view full_typed \
    --protocol remove_direct_labels --cohort core --baselines --ci
python -m validation.esmc_ablation --cohort core            # §3
python scripts/grounding_negative_control.py                # §4
python -m evidence.prism_prereg --check                     # §5 freeze integrity
python -m evidence.acquire_prism --download                 # §5 scoring
python -m evidence.build                                    # §6, §7
python -m pytest tests/ -q
```

Frozen artefacts, provenance records with SHA-256 for every downloaded file, and
the committed pre-registration are under `reports/`. Raw third-party bulk data
are gitignored and re-fetched by the acquisition scripts; distilled records are
committed so the build is reproducible without them.

Third-party data retain their own terms; see `NOTICE` for a per-source
inventory. Code is Apache-2.0.

---

## References

1. Himmelstein DS, Lizee A, Hessler C, et al. Systematic integration of
   biomedical knowledge prioritizes drugs for repurposing. *eLife*.
   2017;6:e26726.
2. Tanoli Z, et al. Validation approaches for computational drug repurposing.
   *Brief Bioinform*. 2024;25(1).
3. Lobentanzer S, et al. Knowledge graphs for drug repurposing: a review.
   *Brief Bioinform*. 2024;25(6):bbae461.
4. Corsello SM, Nagari RT, Spangler RD, et al. Discovering the anticancer
   potential of non-oncology drugs by systematic viability profiling.
   *Nature Cancer*. 2020;1:235-248.
5. Chan A-W, Song F, Vickers A, et al. Increasing value and reducing waste:
   addressing inaccessible research. *Lancet*. 2014;383(9913):257-266.
6. Doshi P, Dickersin K, Healy D, et al. Restoring invisible and abandoned
   trials: a call for people to publish the findings. *BMJ*. 2013;346:f2865.
7. Benjamini Y, Hochberg Y. Controlling the false discovery rate. *J R Stat Soc
   B*. 1995;57(1):289-300.

---

## Author's note on scope

This paper reports negative results from a system built by one person without
funding. It is offered in the belief that the field has more unvalidated
computational claims than it has controls, and that publishing the experiments
that killed one's own components is more useful to other people than publishing
another AUROC.
