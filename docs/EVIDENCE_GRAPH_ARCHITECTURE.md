# Evidence graph architecture: what changed and what to expect

Status: implemented architecture reference, 2026-08-01.

## The short version

KOMPOSOS now has two graph-shaped layers with different jobs:

1. The **scored mechanism graph** proposes drug-disease pairs from paths such
   as `Drug -> Protein -> Disease`.
2. The **contextual evidence graph** records studies, interventions, disease
   context, outcomes, reviews, and source receipts for a proposed pair.

The second layer did not make the first graph more predictive. It made the
result easier to interpret honestly. A ranking asks, "Which pair should I
inspect?" The evidence layer asks, "What happened when people investigated
this pair, and which records did we actually check?"

## Before and after

| Concern | Before | After |
|---|---|---|
| Candidate generation | Binary drug-target-disease paths | Unchanged |
| Ranking score | Strategy votes plus path and conditional similarity bonuses | Unchanged |
| Trial representation | Trial identifiers and review prose in separate artifacts | Typed `Study` records linked to the reviewed pair |
| Study context | Easy to flatten into a drug-disease edge | N-ary roles preserve interventions, conditions, biomarkers, and combinations |
| Result meaning | "Already tried" could collapse positive, negative, and active trials | Testing state and result signal are stored separately |
| Missing evidence | Could be misread as support or novelty | Explicitly remains unknown or quarantined |
| Source handling | A provenance string could look like a validated citation | Receipts have identity, resolution status, relevance assessment, and review notes |
| UI | Mechanistic path and score | Mechanistic path plus contextual evidence in Pair detail |
| Search | Graph traversal and external manual searching | Graph traversal plus local FTS5 over the reviewed evidence corpus |
| Effect on benchmark | Scoring graph produced the benchmark | Evidence graph is excluded from scoring, so the benchmark is unchanged |

## System boundary

```text
Versioned graph sources
        |
        v
data/drugs/tier1.db
  binary scored graph
        |
        +--> candidate ranking
        +--> Drug -> Protein -> Disease explanation
        |
        | pair identity only
        v
Pair detail UI
        ^
        |
data/evidence/evidence.db
  Claim + Study + Role + Outcome + Receipt + Review
        ^
        |
60-row candidate review, trial history, PMID audits, manual receipt review
```

There is no scoring arrow from `evidence.db` back into `tier1.db`. That
separation is intentional. Human review and newly retrieved literature can
change quickly; the scored graph and its benchmark must not change implicitly
when an evidence note is edited.

## Layer 1: the scored mechanism graph

Source of truth: `data/drugs/tier1.db`.

The scored graph is a typed binary graph. Its useful primitive is a path:

```text
Drug --inhibits/targets--> Protein --driver_of/associated_with--> Disease
```

It is good at:

- enumerating drug names before a researcher knows which names to search;
- joining pharmacology to disease biology;
- ranking a batch of reachable pairs;
- showing the mechanistic route responsible for a suggestion;
- abstaining when no route exists.

It is not a database of clinical outcomes. A `driver_of` edge can justify
examining a target, but it does not say that a particular drug worked in
patients. An `associated_with` edge is co-occurrence and generally cannot
establish the required direction of effect.

Current scored-graph scale:

- 1,143 objects;
- 2,038 scored edges;
- 757 drugs and 20 disease nodes;
- 60 directed `driver_of` terminal edges;
- 746 `associated_with` terminal edges.

The raw graph database has 2,462 edge rows because it retains 424 ESMC
similarity-transfer edges that are excluded from scoring.

## Layer 2: the contextual evidence graph

Source of truth at runtime: `data/evidence/evidence.db`.

This is a relational materialization of hypergraph semantics, not a dependency
on a specialized hypergraph database. A study is represented as an entity with
many typed roles:

```text
Study
|- INTERVENTION ----------> drug or reported intervention
|- DISEASE / CONDITION ---> cancer, subtype, or reported condition
|- BIOMARKER -------------> molecular restriction
|- COMBINATION_PARTNER ---> other treatment
|- OUTCOME ---------------> reviewed result signal
`- RECEIPT ---------------> NCT, PMID, or other opened record
```

The representation matters because these two statements are not equivalent:

- "Drug X was studied in glioblastoma."
- "Drug X plus Drug Y was studied in biomarker-selected recurrent
  glioblastoma, the trial is recruiting, and no efficacy result is available."

A single binary `Drug -> Disease` edge loses the information needed to
distinguish them.

### Core records

| Record | Responsibility |
|---|---|
| `Claim` | Canonical subject-predicate-object assertion plus scope and polarity |
| `CandidateReview` | Human standing for one reviewed drug-disease pair |
| `Study` | Registry identity, phase, recruitment state, completion, and posted-results state |
| `StudyRole` | Typed participant or context attached to a study |
| `StudyPairLink` | Why a study is considered relevant to a reviewed pair |
| `Outcome` | Endpoint/result signal and its human-review status |
| `Receipt` | Source identity, URL, resolution status, relevance, and retrieval metadata |
| `ClaimEvidence` | Typed relation between a claim and a receipt |
| `ReviewEvent` | Appendable record of who assessed what, when, and how |
| `evidence_fts` | Lexical retrieval index over reviewed local content |

Current materialization:

- 60 candidate reviews and claims;
- 77 registry studies;
- 3,237 typed study roles;
- 141 outcomes;
- 148 source receipts.

These counts describe reviewed context, not the total oncology literature.

## How a researcher experiences the joined system

### 1. Disease-first discovery

The researcher selects a disease without supplying a drug. The scored graph
enumerates reachable drugs and ranks them. The evidence graph is not used to
inflate or suppress those scores.

Expected result: a mechanistically generated reading queue, not a recommendation
that any drug should be administered or tested.

### 2. Pair inspection

The researcher opens Pair detail for one drug and disease. The application
first shows the scored mechanistic path, then looks up the canonical pair in
`evidence.db`.

If the pair is among the completed reviews, the UI can show:

- evidence state;
- human testing state;
- result signal;
- pipeline assessment;
- registry studies and recruitment status;
- whether results were posted;
- negative-evidence notes;
- opened and unresolved receipts.

Expected result: the researcher can distinguish "tested with signal," "tested
and inactive," "currently recruiting," "category error," and "not reviewed."

### 3. Evidence search

The Pair detail page includes FTS5 search across the local reviewed corpus. It
retrieves review notes, study titles, and receipt context.

Expected result: fast retrieval inside what the project has reviewed. No match
means "not found in this local corpus," not "no publication exists."

### 4. Primary-source reading

The researcher opens the stored receipts and reads the papers or registry
records. Human reading remains the final step.

Expected result: the software reduces navigation and state-confusion; it does
not replace interpretation of methods, endpoints, patient selection, or
clinical relevance.

## Truth-preserving invariants

These rules are architectural, not presentation preferences:

1. Evidence retrieval never changes the ranking score automatically.
2. A recruiting trial is not a positive or negative efficacy outcome.
3. A completed trial is not automatically a failed trial.
4. "No approval found" is not a scientific outcome.
5. "No local evidence found" remains unknown, not supported.
6. An unresolved PMID remains unresolved even when the candidate appears
   biologically plausible.
7. External disease, intervention, and biomarker terms may be stored as
   literals without becoming scored graph nodes.
8. Reviews are imported losslessly through `raw_json` so interpretation can be
   revisited.
9. The scored graph can be rebuilt without the evidence database, and the
   evidence database can be rebuilt without changing the scored graph.

## Concrete expected cases

| Pair or case | Expected representation |
|---|---|
| Cimetidine - RCC | Human testing completed; mixed signal; not collapsed into "already tried" |
| Suramin - RCC | Completed phase 2 evidence with a negative/inactive result |
| Dacomitinib - glioblastoma | Published negative human evidence |
| Amivantamab - glioblastoma | Active recruiting study; result not available |
| Li-Fraumeni rows | Category error remains visible rather than becoming a tumour-treatment claim |
| Biomarker-restricted evidence | Stored with its restriction; not generalized to the whole disease |
| Unresolved KDR-GIST receipt | Candidate context and invalid receipt coexist; one does not repair the other |
| Pair outside the 60 reviews | Standing unknown; no assertion that it is untested |

## What this architecture improves

The change improves:

- semantic precision around human evidence;
- separation of mechanism, testing status, and outcome;
- auditability of what a reviewer opened;
- retrieval of previously reviewed context;
- reproducibility through a deterministic database build;
- future support for combinations, biomarkers, comparators, and multiple
  outcomes without corrupting the scored graph.

It does not yet prove:

- that candidates are novel or effective;
- that ranking saves researchers time;
- that the graph finds evidence a researcher would miss;
- that the 60-row evidence corpus is sufficiently broad;
- that graph visualization is preferable to a well-designed table;
- that vector retrieval improves on lexical search.

Those are workflow and evaluation questions, not database properties.

## Why SQLite remains appropriate

At the current scale, query performance is not the constraint. SQLite provides:

- deterministic, portable artifacts;
- foreign keys and explicit schema;
- FTS5 retrieval;
- simple packaging with the free application;
- no hosted-service dependency;
- easy inspection and export.

A property-graph or high-performance graph engine could be added as a read-only
projection if the corpus grows substantially or natural-language traversal is
demonstrated to help researchers. It should not replace either SQLite source of
truth merely to change database technology.

An export would map `Claim`, `Study`, `Outcome`, and `Receipt` to nodes and
`StudyRole`, `StudyPairLink`, and `ClaimEvidence` to typed edges. Any external
engine must preserve scope, polarity, review state, and receipt validity; a
prettier visualization is not permission to flatten those fields.

## Build, query, and verification

Rebuild the evidence database:

```powershell
python -m evidence.build
```

Read/query API:

- `evidence/models.py` - immutable pair result model;
- `evidence/store.py` - read-only pair, disease, count, and FTS queries;
- `evidence/build.py` - deterministic import and materialization;
- `data/evidence/schema.sql` - schema contract;
- `app.py` - joined presentation in Pair detail.

Regression coverage:

```powershell
python -m pytest tests/test_evidence_hypergraph.py -q
python -m pytest tests/ -q
```

The targeted tests lock the decisive positive, negative, active, category,
biomarker, missing, and invalid-receipt cases. They also verify that rebuilding
the evidence layer does not mutate `data/drugs/tier1.db`.

## Safe extension sequence

1. Add or revise versioned review artifacts.
2. Rebuild `evidence.db` deterministically.
3. Confirm lossless row counts and SQLite integrity.
4. Add a regression fixture for every new evidence state or role.
5. Render the context without feeding it into scoring.
6. Compare the researcher workflow with and without the new feature.
7. Promote the feature only if it saves time or prevents evidence errors.

Document embeddings remain optional retrieval aids. They may be evaluated
against the frozen FTS5 baseline, but retrieved text must not create graph edges,
set result polarity, or change candidate standing without a receipt and human
review.

## Related references

- `docs/EVIDENCE_HYPERGRAPH_PLAN.md` - delivery phases and stop/go gates.
- `data/evidence/schema.sql` - authoritative evidence schema.
- `reports/candidate_review_2026-08-01/README.md` - review corpus and field
  semantics.
- `HONEST_VALUE.md` - measured capabilities and limitations of the scored graph.
