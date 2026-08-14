# PRISM adjudication — 2026-08-14

GRAND_PLAN Phase 1b. The first externally-measured adjudication in this
project's history, against **PRISM Repurposing 19Q4** (DOI
`10.6084/m9.figshare.9393293.v4`, Corsello et al. 2020).

The pre-registration was frozen and committed **before** `evidence/acquire_prism.py`
existed. That ordering is the whole point; without it this is a description, not
a test.

## Result

**No candidate shows lineage-selective in-vitro activity, and the null is robust
to the quality threshold.**

| curve `r2` floor | scorable | selective | no selectivity | inconclusive |
|---|---:|---:|---:|---:|
| **0.5 (pre-registered)** | 3 | **0** | 3 | 19 |
| 0.3 (sensitivity) | 6 | **0** | 6 | 16 |
| 0.0 (sensitivity) | 11 | **0** | 11 | 11 |

Not one pair reaches `LINEAGE_SELECTIVE_ACTIVITY` at any floor. The sensitivity
rows are reported for transparency and are **not** the result; the
pre-registered floor is 0.5 and stands.

**Answer to the Phase 1 gate — does recovered evidence change any candidate's
standing in the 60-candidate audit? No: zero of 60.** PRISM neither supports nor
refutes any reviewed candidate. That is an informative null, not a failure, and
it is the honest first external number.

The pre-registration did real work in one visible case. **R27
dacomitinib→glioblastoma** reached BH q=0.002 — but with a selectivity delta of
**−0.093**, meaning glioma lines were *less* sensitive than other lineages. The
frozen rule requires both significance and the correct direction, so it was
recorded `NO_LINEAGE_SELECTIVITY`. Without the direction requirement, a
significant result pointing the wrong way could have been read as a hit.

## Two problems with my own frozen thresholds — reported, not retuned

The pre-registration says a badly chosen threshold is a finding to report, never
a file to edit after scoring. Both of these are findings.

**1. `require_curve_convergence` was unenforceable.** The shipped dose-response
file has no `convergence` column, although the dataset readme documents one.
Enforcing it failed 100% of rows and returned every pair inconclusive, which is
not a measurement. It is recorded as a declared deviation
(`WAIVED_COLUMN_ABSENT`) in `PRISM_OBSERVATIONS.json`. The waiver is defensible
only because it was found in the file's header, before any verdict was
computed — it is not outcome-dependent.

**2. The `r2 >= 0.5` floor was a poor choice, and biased.** Median curve `r2`
across candidate compounds is **0.247**; the floor keeps only **26%** of curves.
Worse, it keeps them non-randomly: an inactive compound in a resistant line
produces a *flat* curve, which has low `r2` by construction. So the filter
preferentially retains lines where the drug did something, biasing the very
selectivity contrast it feeds. Combined with `min_target_lines_after_qc = 8`, it
left only 3 of 22 scorable pairs measurable. A future pre-registration should
filter on fit quality in a way that does not correlate with the effect being
measured.

**3. The pan-cytotoxicity control passed on a technicality.** Of three expected
broad cytotoxics, only oxaliplatin (median AUC 0.795) tripped the 0.80 floor;
cisplatin (0.912) and carboplatin (0.873) did not. Cimetidine (1.196) and
propranolol (0.940) correctly did not trip it. The frozen rule requires only
that *some* expected cytotoxic fires, so the run is valid as written — but the
built-in negative control is weaker than intended, and a 0.80 median-AUC floor
does not reliably detect known broad cytotoxicity.

**4. The Tier A/B split turned out redundant.** All six soft-tissue pairs fail
`min_target_lines_after_qc = 8` regardless, because the lineage has only 5 cell
lines in total. The power tier never had to do any work.

## Coverage — and a correction to the GRAND_PLAN

**PRISM 19Q4 contains zero haematological cell lines**, in either screen: 568
adherent lines across 24 solid-tissue lineages. The plan's assumption that PRISM
covers a large fraction of the candidate space does not survive the data.

| Stratum | Pairs |
|---|---:|
| `TIER_A_HEADLINE` | 16 |
| `TIER_B_UNDERPOWERED` (soft tissue, n=5 lines) | 6 |
| `SECONDARY_SINGLE_DOSE_ONLY` | 5 |
| `REFUSED_DRUG_NOT_SCREENED` | 11 |
| `REFUSED_NO_CORRESPONDENCE` | 22 |

Of 40 candidate drugs: 21 dose-response, 6 single-dose only, 13 never screened.
Three of those are biologics a small-molecule viability screen cannot test at
all; most of the rest post-date the 19Q4 release, though nitroglycerin is an old
drug absent for library reasons rather than vintage. **No absence is evidence of
inactivity.**

The 22 refusals are 12 haematological (CLL, myelofibrosis, myeloma, AML), 6
Li-Fraumeni (already a category error in the review), and 4 GIST. GIST is
refused on principle: PRISM's `gastric` lineage is adenocarcinoma, a different
cell of origin from a KIT-driven mesenchymal tumour, and joining them on the
shared word "stomach" is exactly the silent string join that corrupts every edge
crossing the seam.

**A repurposing candidate set drawn from this graph is 37% haematological or
category error, and the most-used public repurposing screen cannot touch any of
it.** That is itself a reportable finding about the candidate set.

## The hard boundary

**Labels, not features.** `app.py` is the only module that surfaces this;
nothing in `oracle/`, `core/`, `validation/` or `data/` reads it, and
`tests/test_prism_adjudication.py` enforces that by scanning those packages. If
measured viability fed the ranker, it could never again serve as an independent
test of it.

**Fill by retrieval, never by inference.** Absence from the screen is recorded
as absence. Every row carries `human_reviewed = 0` — automated extraction is not
review.

**Cell lines are not patients.** No verdict here supports an efficacy claim in
either direction. `NO_LINEAGE_SELECTIVITY` in a dish is not clinical failure,
and it does not retire a candidate.

**Do not compute a precision estimate.** 16 pre-registered pairs, of which 3
were measurable under the frozen rule, cannot support AUROC, AUPRC or precision,
for the same reason `data/labels/evaluation_labels_v1.csv` carries that warning.

## Files

- `DISEASE_CORRESPONDENCE.json` — the written pushout span. Ten accepted
  identifications, each with a type, a justification and a known discrepancy;
  six refusals. Hand-written before any outcome was read.
- `PREREGISTRATION.json` — frozen candidate set, thresholds, statistic,
  correction, verdict vocabulary. Pins the correspondence and review by SHA-256.
  **sha256 `31389f9901b71b6bfe61a812941f82e87890b05aa3a824a315e548b938660e4b`**
- `PRISM_OBSERVATIONS.json` — measured verdicts, declared deviations, control
  panel, sensitivity analysis. Read by `evidence/build.py`.
- `PROVENANCE.json` — URL, byte count and SHA-256 of every raw file used.
- `RECON_REPORT.json`, `recon.py` — the metadata-only feasibility pass.

Distilled records are **committed on purpose**; the build reads them, so a
gitignored cache would give two people different databases. Raw PRISM files
(~310 MB) stay gitignored under `data/external/prism_repurposing_2026-08-14/`.

## Access note

The DepMap portal serves a Cloudflare human-verification interstitial to
automated clients, so `depmap.org/portal/api/download/files` returns HTML rather
than JSON. The DepMap 24Q2 figshare deposit carries CRISPR and omics matrices
but no Repurposing files. **19Q4 via figshare is the automatable release.**

## Reproduce

```powershell
python reports/prism_2026-08-14/recon.py          # metadata-only feasibility
python -m evidence.prism_prereg --check           # frozen set still matches inputs
python -m evidence.acquire_prism --download       # ~310 MB, then score
python -m evidence.build                          # materialize into evidence.db
python -m pytest tests/test_prism_adjudication.py -q
```

`--check` and `--download` need the raw files; the build and the tests do not.

## Next

The 12 haematological pairs need a screen with suspension lines (GDSC or CTRP)
and **a separate correspondence document** — not a threshold change here. Phase
1c (DepMap CRISPR) is the other open branch, and its trap is already named:
CRISPR knockout is not drug inhibition.
