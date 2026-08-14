# Working session — 2026-08-14

GRAND_PLAN Phase 1b: PRISM Repurposing as an adjudication surface. Complete.

Started at `2993588` (suite 229 passed, 1 skipped), ended at `e949255`
(suite 249 passed, 1 skipped, **and a clean clone now passes too**).

## What this session was for

The scored graph has no measured numbers — `quantitative_value` is populated on
0 of 2,462 edges, and the terminal Protein→Disease hop is 60 directed edges.
Everything traces to what someone wrote down, which is why the PubMed grounding
permutation control came back at p=0.28. PRISM screened thousands of compounds
against cancer cell lines for viability, so it can supply *measured* outcomes for
candidates this system produced.

The point was never to improve the ranker. It was to give the ranker something
external to be judged against, for the first time in the project's history.

## Result

**No candidate shows lineage-selective in-vitro activity, and the null is robust
to the quality threshold.**

| curve `r2` floor | scorable | selective | no selectivity | inconclusive |
|---|---:|---:|---:|---:|
| **0.5 (pre-registered)** | 3 | **0** | 3 | 19 |
| 0.3 (sensitivity) | 6 | **0** | 6 | 16 |
| 0.0 (sensitivity) | 11 | **0** | 11 | 11 |

**Phase 1 gate — does any recovered evidence change a candidate's standing in
the 60-candidate audit? Zero of 60.** PRISM neither supports nor refutes any
reviewed candidate. An informative null, and the honest first external number.

The pre-registration visibly earned its keep once. R27 dacomitinib→glioblastoma
reached BH q=0.002 — but with a selectivity delta of **−0.093**, meaning glioma
lines were *less* sensitive than other lineages. Because the frozen rule
required significance **and** the correct direction, it recorded
`NO_LINEAGE_SELECTIVITY`. Without that requirement, a significant result
pointing the wrong way could have been read as a hit.

## The main system is untouched

Re-ran the canonical benchmark after all changes. Bit-identical:

- AUROC **0.976306**, AUPRC **0.592023**, precision@5/@10/@20 = 1.00 / 0.70 / 0.70
- Margin over common-neighbour **+0.2280**; 962 scored, 598 unscored

`data/drugs/tier1.db` was last modified 2026-08-01 and appears in no commit from
this session. No UI number or statement needed correcting — including
"`quantitative_value` reads NULL for all 2,462 edges", which remains true and
should stay, because filling it from PRISM is exactly what the boundary forbids.

## Three findings about thresholds I froze myself

Reported, not retuned. A pre-registration that gets edited after scoring is not
a pre-registration.

1. **`require_curve_convergence` was unenforceable.** The shipped dose-response
   file has no `convergence` column although the dataset readme documents one;
   enforcing it failed 100% of rows. Recorded as a declared
   `WAIVED_COLUMN_ABSENT` deviation. Defensible only because it was found in the
   file's header, before any verdict existed — it is not outcome-dependent.
2. **The `r2 >= 0.5` floor was poorly chosen and biased.** Median curve `r2` is
   0.247, so it keeps 26% of curves — and keeps them non-randomly, because an
   inactive compound in a resistant line produces a *flat* curve with low `r2`
   by construction. The filter preferentially retains lines where the drug did
   something, biasing the very contrast it feeds. A future pre-registration must
   filter on fit quality in a way that does not correlate with the effect.
3. **The pan-cytotoxicity control passed on a technicality.** Only oxaliplatin
   (median AUC 0.795) tripped the 0.80 floor; cisplatin (0.912) and carboplatin
   (0.873) did not. The built-in negative control is weaker than intended.

A fourth, smaller one: the Tier A/B power split turned out redundant, because
all six soft-tissue pairs fail the minimum-lines rule anyway — that lineage has
only 5 cell lines in total.

## A correction to the GRAND_PLAN's premise

The plan assumed that because 54 of 60 candidates are `KNOWN_DRUG_NEW_CANCER`,
PRISM would cover a large fraction of the candidate space. **It does not.**

PRISM 19Q4 contains **zero haematological cell lines** — the same 568 adherent
lines across 24 solid-tissue lineages in both screens. Coverage is limited by
lineage and screening vintage, not by candidate class:

| Stratum | Pairs |
|---|---:|
| `TIER_A_HEADLINE` | 16 |
| `TIER_B_UNDERPOWERED` (soft tissue, n=5 lines) | 6 |
| `SECONDARY_SINGLE_DOSE_ONLY` | 5 |
| `REFUSED_DRUG_NOT_SCREENED` | 11 |
| `REFUSED_NO_CORRESPONDENCE` | 22 |

GIST was refused on principle rather than joined to `gastric`: PRISM's gastric
lineage is adenocarcinoma, a different cell of origin from a KIT-driven
mesenchymal tumour, and joining them on the shared word "stomach" is exactly the
silent string join that corrupts every edge crossing the seam.

**A candidate set drawn from this graph is 37% haematological or category
error, and the most-used public repurposing screen cannot touch any of it.**
That is itself a reportable finding about the candidate set.

## Architecture — additive, and firewalled

Three roles, unchanged in kind:

- **Scoring substrate** — `data/drugs/tier1.db`. Untouched.
- **Adjudication surface** — `data/evidence/evidence.db`, now with 60 PRISM rows.
- **Presentation** — `app.py`, the only module that joins them.

Verified: nothing in `oracle/`, `core/`, `validation/`, `data/` or
`komposos_kg/` imports the `evidence` package or references PRISM.
`tests/test_prism_adjudication.py` scans those packages on every run and fails
if that changes, so a future session cannot quietly wire PRISM into the ranker.

## Two infrastructure bugs, both caught by testing a clone

Neither was visible from the local checkout. Cloning the repo and running the
suite inside the clone is now clearly worth doing routinely.

1. **Hash pins broke on checkout.** The pre-registration pins files by SHA-256
   over raw bytes. A clone with `core.autocrlf` enabled — true globally here,
   though false in this checkout — materialised the correspondence at 9,688
   bytes instead of 9,524, and every pin failed with nothing edited. Fixed with
   `.gitattributes` using `-text`, which preserves bytes in both directions and
   leaves the committed frozen file byte-identical. Regenerating the
   pre-registration to fix it would have meant editing it after scoring.
2. **The new test file was silently gitignored.** `tests/` carries a broad
   `test_*.py` ignore with per-file negations, so the boundary-enforcing test
   would not have survived a clean checkout. Fixed with a negation matching the
   existing convention, not `git add -f`.

## Two standing claims that did not survive checking

Both were stated confidently in the handoff and both were wrong. Recording them
so they are not repeated.

- **"`geometry/__init__.py` is gitignored."** It is not. `git check-ignore`
  returns nothing and the file has always been tracked.
- **"Committing it would break clean checkouts that import geometry as a PEP 420
  namespace package."** A clean checkout never had a namespace package; it had
  the older tracked version of that same file. Measured on a clean clone: as
  committed, 2 collection errors and the suite cannot run; with the repair,
  249 passed. Committing it **fixed** clean checkouts. Done in `e949255`,
  closing GRAND_PLAN Phase 0 item 2.

## Commits

| | |
|---|---|
| `dd59140` | Pre-register the adjudication, before any scoring code existed |
| `5fdb40e` | Adjudicate the frozen set against measured PRISM viability |
| `2c72092` | Stop git rewriting line endings of hash-pinned files |
| `e949255` | Let optional geometry subsystems degrade (Phase 0 item 2) |

`master` is **10 commits ahead of `origin/master` and unpushed.**

## Where to pick up

- **Push.** Ten unpushed commits is the largest loose end.
- **Phase 1c, DepMap CRISPR.** Its trap is already named: CRISPR knockout is not
  drug inhibition. Do not import the PRISM correspondence by analogy; gene
  essentiality and drug sensitivity are different measurements.
- **The 12 haematological pairs** need a screen with suspension lines (GDSC or
  CTRP) **and its own correspondence document**. Not a threshold change here.
- **Optional UI addition.** The honest-limits page does not yet mention that a
  first external adjudication exists and returned a null. Nothing there is
  *wrong*; this is an addition, not a correction.
- **Phase 3, the paper.** The null adds a fourth negative control alongside the
  ESMC ablation, the grounding permutation, and the horn-composition null. A
  paper that kills four of its own methods with controls is the actual product.
