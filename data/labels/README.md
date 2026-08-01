# Evaluation label set

Roadmap **Phase 0.5**. This exists because PHARM currently cannot tell a false
positive from a true positive it never labelled, which is why no claim about its
precision — in either direction — is defensible today.

The evidence for that: in the temporal holdout, the top-ranked "negative" is
Dacomitinib → NSCLC, FDA-approved 2018-09-27. Lorlatinib, Brigatinib and
Amivantamab in NSCLC and Avapritinib in GIST sit in the same top 20, all approved,
all counted as false positives. The 44-label gold set covers only the 78 curated
drugs, while the graph carries 679 more from ChEMBL.

## Status: SEED, NOT COMPLETE

`evaluation_labels_v1.csv` is **not** a complete label set and must not be used as
one. It contains:

- the 44 inherited positives, marked `INHERITED_UNVERIFIED` — they were hand-typed
  into `validation/temporal_holdout.py` with **no citation of any kind**, and are
  carried here unchanged so the gap is visible rather than hidden;
- a small set of `APPROVED` rows verified individually against FDA sources during
  the 2026-07-31 audit, each carrying its source URL and verification date.

Completing it is the work the 50-pair reviewer exercise is designed to scope: the
codes **A** (approved, we missed it) and **B** (in trial) tell us how large the gap
actually is before anyone spends weeks on exhaustive curation.

## Why an unlabelled pair is not a negative

Every pair absent from this file is `UNKNOWN`, never `SCREENED_NEGATIVE`. Treating
absence as a negative is precisely the error that produced the contaminated
holdout. `SCREENED_NEGATIVE` is reserved for pairs where someone looked and
recorded a negative finding — a failed trial, a published null. PHARM has no such
data yet, so that status is currently unused and that is honest.

## Why the biomarker column is not optional

Several verified approvals are **biomarker- and line-restricted**:

- Lorlatinib is approved for ALK-positive NSCLC **after progression on crizotinib
  and another ALK inhibitor**, not for NSCLC generally.
- Amivantamab's first approval is for **EGFR exon 20 insertion** NSCLC.
- Avapritinib is for GIST harbouring a **PDGFRA exon 18** mutation, including
  D842V — a population that does **not** respond to standard GIST therapy.

Flattening these to "drug treats disease" would replace one overstatement with
another: it would credit PHARM with predicting an approval whose actual scope is
a small molecularly defined subgroup the graph cannot represent at all. The
`biomarker_restriction` and `line_of_therapy` columns keep that visible, and they
are the concrete reason the roadmap's Phase 2 claim model needs GA4GH VRS and
Cat-VRS variant identity rather than gene-level nodes.

## Why `combination_partner` was added

Curating the first worklist tranche immediately produced two approvals that are
**combination-only**:

- **Adagrasib** is approved for KRAS G12C colorectal cancer **only with
  cetuximab** — there is no monotherapy CRC approval.
- **Sotorasib** likewise **only with panitumumab**.

The ranker surfaced both at ranks #1 and #2 for colorectal cancer as single
drugs. Recording them as bare `treats` labels would credit it with predicting
monotherapy approvals that do not exist. The column exists so that a future
metric can decide, explicitly, whether a monotherapy prediction that matches a
combination-only approval counts as a hit — rather than that decision being made
silently by a missing field.

## Why `APPROVED_TUMOR_AGNOSTIC` exists

The second curation tranche produced a category that is **neither a hit nor a
false positive**, and forcing it into either would misrepresent the system.

Selpercatinib holds a tumour-agnostic approval for *RET fusion-positive solid
tumours* (accelerated 2022-09-21, traditional 2026-07-14). Larotrectinib holds one
for *NTRK fusion-positive solid tumours* (2018-11-26). So selpercatinib for
prostate cancer is genuinely approvable — but only in the small fraction of
prostate cancers carrying a RET fusion, which the graph cannot see, because it has
no variant-level representation at all.

- Scoring these as whole-disease hits **overstates**: it credits the ranker with
  predicting an indication that applies to a rare molecular subgroup.
- Scoring them as false positives **understates**: the drug is legitimately
  approved for that patient.

Any metric built on this file must decide explicitly which it does. That is the
entire reason the status is separate rather than folded into `APPROVED`.

### A distinction the graph cannot currently make

Selpercatinib and pralsetinib are both RET inhibitors and the ranker scores them
**identically** — 0.8608 each for HCC, both ranked in the top 3. Their regulatory
status is not identical:

- **Selpercatinib** has the tumour-agnostic RET-fusion solid-tumour approval.
- **Pralsetinib does not.** It holds NSCLC (regular) and RET-fusion thyroid
  (accelerated); its medullary thyroid indication was **withdrawn in July 2023**
  after the confirmatory study proved unfeasible.

So one is `APPROVED_TUMOR_AGNOSTIC` for HCC and the other is `UNKNOWN`, from
target pharmacology that is essentially the same. No amount of graph evidence
distinguishes them — only the regulatory record does. This is a concrete limit on
what a drug-target-disease graph can conclude, and it belongs in any honest
description of the system.

## Curating more

    python -m validation.build_label_worklist

Emits `reports/label_worklist.csv`, the unlabelled pairs ranked by how much
curating them would change the evaluation (reciprocal of rank within disease).
Salt forms are collapsed so each drug is one task.

**The first run found 354 of the 400 highest-ranked pairs across all 20 diseases
carry no label of any kind.** Six diseases — AML, Ewing sarcoma, glioblastoma,
Li-Fraumeni, prostate, soft-tissue sarcoma — are 20/20 unlabelled. That is the
number which makes a precision claim indefensible today, and it is *not* evidence
the ranker is good: an unlabelled pair says nothing about whether it is right.

## Schema

| column | meaning |
|---|---|
| `label_id` | stable identifier, never reused |
| `drug` | drug node name as it appears in `tier1.db` |
| `drug_inn` | normalized INN, salt/hydrate suffixes stripped |
| `disease` | disease node name as it appears in `tier1.db` |
| `status` | `APPROVED` / `APPROVED_TUMOR_AGNOSTIC` / `IN_TRIAL` / `PRECLINICAL` / `SCREENED_NEGATIVE` / `UNKNOWN` |
| `biomarker_restriction` | molecular population the approval is limited to, or `none` |
| `combination_partner` | the drug this approval requires alongside it, or `none`. **Never leave blank** |
| `line_of_therapy` | `first_line`, `later_line`, `post_progression`, `any`, `unknown` |
| `approval_year` | year of first US approval for this indication |
| `approval_date` | ISO date where verified, else empty |
| `source_type` | `FDA_ONCOLOGY_ANNOUNCEMENT` / `FDA_APPROVAL_LETTER` / `CLINICALTRIALS_GOV` / `INHERITED_UNVERIFIED` |
| `source_url` | direct link to the primary source |
| `verified_on` | ISO date the link was checked |
| `notes` | anything a reader needs in order not to misread the row |

## Versioning

Version the label set **independently of the graph**. A scoring change and a label
change must never be confounded — otherwise a metric moves and nobody can say
which caused it. Bump to `evaluation_labels_v2.csv` rather than editing v1 once
any published number depends on v1.

## Validate

    python -m validation.check_label_set
