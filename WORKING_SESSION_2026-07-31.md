# Working session — 2026-07-31

Live log for the post-audit implementation session. Updated as work proceeds, not
at the end. Supersedes nothing; `CLAUDE.md` and `HONEST_VALUE.md` remain the
source of truth for numbers.

## Approved sequence (from the corrected roadmap)

1. Correct the factual documents — **DONE**
2. Run the 50-pair human evidence and label-completeness audit — **packet built, awaiting reviewer**
3. Determine whether researchers find the evidence bundles useful — blocked on (2)
4. Repair packaging and establish a clean-clone test — **DONE**
5. Construct a complete, versioned evaluation label set — **seeded, incomplete**
6. Only then design the Beat AML experiment — not started
7. Defer combinations, toxicity, multi-omics, patient cases — deferred

## This session

| # | Item | Status |
|---|---|---|
| A | Quarantine headers on 5 research files | done |
| B | Packaging repair + clean-clone CI | done |
| C | 50-pair reviewer packet (25 NSCLC + 25 Melanoma) | done |
| D | Evaluation label set (schema + seed) | done, seed only |

## Decisions taken, with reasons

**Reviewer packet uses the `all` cohort, not `core`.** The exercise measures label
completeness and citation-to-assertion precision — it is not a benchmark. The
unlabelled approvals that codes A and B are designed to catch live almost entirely
among the 679 materialized ChEMBL drugs, which the `core` cohort excludes. Using
`core` would structurally suppress the signal the exercise exists to measure.
No AUROC, AUPRC, or precision claim may be derived from this packet.

**Pairs are shuffled before the reviewer sees them.** Rank is withheld until the
debrief. Presenting a ranked list invites the reviewer to anchor on position
rather than on the evidence shown, which would contaminate the code assignments.

**25 + 25 across two diseases rather than 50 on one.** Chosen by James. Weaker
statistics per disease, but it tests whether the evidence presentation holds
across two different biologies — and NSCLC and Melanoma are the only two diseases
with 9 positives each.

**Quarantine headers are comment-only.** No behaviour change, no deletions. The
files stay importable so any historical dependency review can still run them.

**Packaging fix is deliberately minimal.** Correct the build backend, widen the
package discovery, complete the declared dependencies, add CI. No refactor, no
restructuring, no module moves — those would be a separate change.

## What was built

| path | what it is |
|---|---|
| `.github/workflows/clean-clone.yml` | Builds a wheel, installs it into a fresh venv, runs the tests, reproduces the benchmark, and **fails the build if AUROC/AUPRC/pair counts drift**. Update the expected values only in the same commit as the docs. |
| `validation/build_reviewer_packet.py` | Generates the packet. Shuffles, hides rank, caps controls. |
| `validation/score_reviewer_packet.py` | Reads the returned sheets back into the two numbers. Dry-run verified end to end on a scratchpad copy. |
| `validation/check_label_set.py` | Structural validation plus a completeness report that refuses to make the seed look finished. |
| `data/labels/evaluation_labels_v1.csv` | 50 rows: 44 inherited-uncited, 6 verified against FDA sources. |
| `data/labels/README.md` | Schema, versioning rule, and why the biomarker column is not optional. |
| `reports/reviewer_audit_2026-07-31/` | The packet itself: `REVIEWER_PACKET.md`, `BLIND_CITATION_SUBSET.md`, two blank CSVs, and `MANIFEST.json`. |

**`MANIFEST.json` is the answer key. Do not send it to the reviewer.** Send the two
`.md` files and the two blank `.csv` files, nothing else.

Regression check after all changes: **166 passed, 1 skipped**; benchmark still
AUROC 0.978450 / AUPRC 0.612775 / 957 scored / common_neighbor +0.2355.

## Composition of the packet

50 pairs: 25 NSCLC + 25 Melanoma, of which **6 are already-labelled positives**
seeded as a calibration control and **44 are unlabelled** — which is where the
label-completeness question lives.

A first build took the top 25 outright and produced **17 known positives in 50
pairs**. That would have spent a third of the reviewer's budget on pairs whose
code is knowable before reading anything. Fixed by capping controls at 3 per
disease and filling from the top unlabelled pairs.

The blind citation subset was also rebalanced: the first build spent 2 of 10 slots
on `Disease -> Disease` co-occurrence edges. It now prioritises the terminal
`Protein -> Disease` hop (8 of 10), which is the least-verified layer and the one
the grounding negative control found carries no signal. It happens to include
`MET -> NSCLC`, and `MET` is one of the overloaded gene symbols flagged in
HONEST_VALUE.md as a known collision risk — a useful accidental test.

## A finding from doing the work

The verified approvals are **biomarker- and line-restricted**, and this changes
what the exercise can conclude:

- Lorlatinib: ALK-positive NSCLC **after progression on crizotinib plus another
  ALK inhibitor** — not NSCLC generally.
- Amivantamab: **EGFR exon 20 insertion**.
- Avapritinib: GIST with a **PDGFRA exon 18** mutation, a population that does not
  respond to standard GIST therapy.

So coding these as plain "approved, the label set missed it" would be an
overstatement in the *opposite* direction: it would credit PHARM with predicting
an approval whose real scope is a small molecularly defined subgroup the graph
cannot represent at all. The label schema now carries `biomarker_restriction` and
`line_of_therapy` for exactly this reason, and this is the concrete argument for
the Phase 2 claim model needing GA4GH VRS / Cat-VRS variant identity rather than
gene-level nodes.

## Known-incomplete, carried forward

- **The label set is a seed, not a complete table.** It covers the drugs that
  appear in the reviewer packet plus the contamination cases found during the
  audit. Completing it is step 5 and should be informed by what codes A and B
  return.
- **The reviewer packet has no reviewer.** It becomes evidence only when a domain
  reviewer fills in the coding sheet. Until then it is an artifact, not a result.
- **External evaluation is still retired.** `data/external/` remains absent;
  restoring or replacing Hetionet is not in this session.
- **Temporal holdout is still leaky.** It removes the label but leaves
  2026-derived Protein->Disease edges in the graph. A real temporal design needs
  edge-level publication dates, which do not exist yet.
- **`--json` output is not machine-parseable.** Import-time bridge banners
  (`[ABPPBridge] ...`, `[Boltz2Bridge] ...`) print to stdout ahead of the JSON
  payload. The CI works around it by slicing from the first `{`. Fixing it means
  moving those banners to stderr, which is a behaviour change and was out of
  scope for a packaging-only edit.
- **Two approval dates are year-precise only.** Amivantamab's 2021 exon-20
  approval and Avapritinib's 2020 approval are recorded without day precision;
  Brigatinib's row cites the FDA approvals index rather than a direct
  announcement URL. Re-verify all three before any of them appears in a
  published number.

## Streamlit work (added after the first session block)

**Calculations were never affected** by the audit or the doc corrections. The app
loads the graph through the same `load_full_typed_view` / `build_funnel` as
before. Its headline figures reproduce.

**Displayed numbers were badly stale**, and the app was the last surface still
carrying retired claims — the one being shown at the event. Corrected in `app.py`:

| was | now |
|---|---|
| Hetionet external 0.6436 / 0.0095 presented as a result | RETIRED, with the reason (inputs absent, wrong cohort) |
| Temporal holdout 0.9706 / 0.1938 | STALE and leaky, with the reruns and the leak explained |
| "Only 158 proteins carry any disease edge" | 107 nodes / 783 edges / 37 directed / **138 directed-reachable pairs** |
| "AUPRC (0.57)" | 0.6128 |
| Hits@5 / @10 / @20 | precision@5 / @10 / @20, with why |
| "External generalization is weak" (4 places) | "unmeasured", with the Dacomitinib example |
| "Oncology only: 20 cancer types" | 20 diseases incl. Type2_Diabetes; 6 with zero positives |
| — | added: scored-only AUROC 0.9642, coverage 957/1560, empty quantitative columns |

**New mode: Evidence card.** One candidate, three strongest paths, per-edge tier
and PMID, an explicit "what this does not have" line, and a standing
(`SUPPORTED_FOR_REVIEW` / `WEAK` / `NOT_ASSESSED`). Closes the Phase 0 item "one
compact evidence view". It imports `best_chains`, `missing_evidence_line` and
`pmids_from_edge` directly from `build_reviewer_packet`, so the screen and the
packet sent to an external reviewer cannot drift apart.

### A bug I introduced and caught before shipping

The first `_evidence_standing` graded **Nivolumab -> Melanoma** as
`SUPPORTED_FOR_REVIEW` because it found a "directed terminal hop" —
`Nivolumab -treats-> RCC`. That is **a different disease's FDA label being read as
mechanistic support**: precisely the label leakage the strict protocol exists to
prevent, reintroduced by me in the UI layer. Two fixes, both kept:

1. A qualifying terminal hop must land on *the target disease*, come from a
   protein, and not be a `treats` edge.
2. The Evidence card now runs on its own **label-removed** view
   (`load_strict_graph()`), so those edges are not present at all.

Nivolumab -> Melanoma now reads WEAK, correctly: its terminal hop is
`PDCD1 -associated_with-> Melanoma`, co-occurrence.

### Two demo cases this produced

- **Sorafenib -> Melanoma** — `SUPPORTED_FOR_REVIEW` via `BRAF -driver_of->
  Melanoma` on an ESTABLISHED drug-target edge. Shows the system at its best,
  and the readiness doc's point still stands: mechanistic plausibility is not
  clinical efficacy, and Sorafenib is not a melanoma therapy.
- **Venetoclax -> AML** — scores 0.840 and still reads **WEAK**, because every
  terminal hop to AML is `associated_with`. A genuinely approved AML regimen that
  this graph can only support by co-occurrence. That single card explains the
  138-pair constraint better than any slide.

## Step 5 — label set (started)

`python -m validation.build_label_worklist` ranks unlabelled pairs by how much
curating them would change the evaluation (reciprocal of rank within disease),
collapsing salt forms so each drug is one task.

**First run: 354 of the 400 highest-ranked pairs across 20 diseases carry no
label of any kind.** Six diseases are 20/20 unlabelled — AML, Ewing sarcoma,
glioblastoma, Li-Fraumeni, prostate, soft-tissue sarcoma. Best-covered are NSCLC
(8/20) and Melanoma (11/20), which is why those two were the right choice for the
reviewer packet.

### First curated tranche — 4 for 4 were real misses

Every rank-1-to-3 pair I checked against FDA turned out to be an approved
indication the gold set never recorded:

| pair | rank | approval | note |
|---|---|---|---|
| Gilteritinib -> AML | #3 | 2018-11-28, FLT3-mutated R/R AML | **AML's first `treats` label of any kind** |
| Adagrasib -> Colorectal_Cancer | #1 | 2024-06-21, KRAS G12C | **combination-only, with cetuximab** |
| Sotorasib -> Colorectal_Cancer | #2 | 2025-01-15, KRAS G12C | **combination-only, with panitumumab** |
| Cabozantinib -> HCC | #1 | 2019-01-14, after prior sorafenib | graph node is the salt form `Cabozantinib S-Malate` |

This is the audit's central claim moving from argument to evidence: the ranker's
top-of-list "false positives" include a substantial number of real approvals. It
still does **not** license a precision claim — four verified misses out of a
354-pair backlog is a direction, not a rate.

### Schema change forced by the curation

Two of the four are **combination-only** approvals. The schema had no way to say
so, and a bare `treats` row would have credited the ranker with predicting
monotherapy approvals that do not exist. Added `combination_partner`, required on
every row (`none` explicitly, never blank), surfaced by the validator, and
documented. A future metric now has to decide *explicitly* whether a monotherapy
prediction matching a combination-only approval is a hit.

That is the second time in this session that curating real data has produced a
schema gap the roadmap had only argued for abstractly — the first being
biomarker/line restriction. Both point the same way: gene-level nodes cannot
carry what oncology approvals actually say.

### Second tranche — 10 more rows, and a third schema gap

Worked ranks 1–6 across all 20 diseases (91 tasks), triaged, and verified the
plausible ones. Added:

| pair | rank | status |
|---|---|---|
| Fedratinib -> Myelofibrosis | #3 | APPROVED 2019-08-16 |
| Bosutinib -> CML | #5 | APPROVED 2012-09-04 |
| Asciminib -> CML | #6 | APPROVED 2024-10-29 |
| Trastuzumab_deruxtecan -> Breast_Cancer | #5 | APPROVED 2022-08-05 (HER2-low) |
| Imatinib -> Soft_Tissue_Sarcoma | #6 | APPROVED — **DFSP subtype only**, not the disease |
| Selpercatinib -> HCC / GIST / Prostate | #2/#5/#1 | **APPROVED_TUMOR_AGNOSTIC** (RET fusion) |
| Larotrectinib -> Prostate / Pancreatic | #4/#5 | **APPROVED_TUMOR_AGNOSTIC** (NTRK fusion) |

**Third schema gap: `APPROVED_TUMOR_AGNOSTIC`.** Selpercatinib for prostate
cancer is genuinely approvable — but only in the rare RET-fusion subgroup the
graph cannot see. Scoring it as a whole-disease hit overstates; scoring it as a
false positive understates. It is neither, so it gets its own status and any
metric must decide explicitly how to treat it.

**The sharpest finding of the session.** The ranker gives selpercatinib and
pralsetinib *identical* scores for HCC (0.8608, both top-3) — same target, same
pharmacology. But selpercatinib holds the tumour-agnostic RET solid-tumour
approval and **pralsetinib does not**: its NSCLC and RET-thyroid indications
stand, while its medullary thyroid indication was **withdrawn in July 2023**.
One is `APPROVED_TUMOR_AGNOSTIC` for HCC; the other is `UNKNOWN`. No graph
evidence separates them — only the regulatory record does. That is a clean,
demonstrable limit on what a drug-target-disease graph can conclude, and it is
worth saying out loud rather than discovering it in front of a reviewer.

### Deliberately not added

Dasatinib -> CML and cisplatin/carboplatin -> Ovarian_Cancer are near-certain
approvals, but I did not land a direct primary-source URL for them in this pass.
They stay `UNKNOWN` rather than entering the file uncited: the invariant that
every non-inherited row carries a working primary source is worth more than four
extra rows. They are the first tasks for the next pass.

## Next action

Send the packet. Nothing else in the sequence moves until a domain reviewer has
returned the two sheets — step 3 is literally "determine whether researchers find
the evidence bundles useful," and there is no way to answer it from inside the
repository.
