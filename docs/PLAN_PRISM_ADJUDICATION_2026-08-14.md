# PLAN — PRISM Repurposing as an adjudication surface

Written 2026-08-14. GRAND_PLAN Phase 1b. **IMPLEMENTED AND SCORED — see
`reports/prism_2026-08-14/README.md` for the result.** The execution order in
section 6 was followed: the pre-registration was committed before
`evidence/acquire_prism.py` existed.

**Result in one line: no candidate shows lineage-selective in-vitro activity,
and the null holds at every quality floor tested. Zero of 60 candidate standings
change.** Two of the thresholds frozen below turned out to be poorly chosen and
one was unenforceable; all three are reported in the README rather than retuned,
per section 6. Read that file before trusting any number in this one.

## 0. Why PRISM

The scored graph contains no measured numbers. `quantitative_value` is populated
on 0 of 2,462 edges, and the terminal Protein→Disease hop is 60 directed edges.
Everything traces to what someone wrote down, which is why the PubMed grounding
permutation control came back at Fisher p=0.28 — post-hoc citation measures
corpus density, not biology.

PRISM screened thousands of compounds, deliberately including non-oncology
drugs, against cancer cell lines for viability. 54 of the 60 reviewed candidates
are `KNOWN_DRUG_NEW_CANCER`, so the screen's design intent overlaps this
project's candidate space with *measured* outcomes.

The negative control is built into the data. A drug that kills every lineage is
nonspecific cytotoxicity; a drug that kills only the predicted lineage is
signal. **Measure selectivity, not potency.** That contrast is the same shape as
the ESMC ablation and the grounding permutation control.

## 1. Hard boundaries (settled; not reopened here)

1. **Labels, not features.** PRISM must never feed the ranker. `app.py` is the
   only module that may import it; nothing in `oracle/`, `core/`, `validation/`,
   or `data/`. The moment it feeds scoring it is destroyed as validation
   permanently, and this project loses its only route to an external number.
   Same reasoning as `PLAN_TRIAL_RESULTS_RECOVERY_2026-08-12.md` section 4a.
2. **Pre-register before looking.** Freeze the candidate set and the
   adjudication rule, hash and timestamp them, *then* score. Looking first
   repeats the leaky-holdout mistake with the last clean data available.
3. **Fill by retrieval, never by inference.** Absence is never scored as a
   negative. A drug PRISM never screened is `NOT_SCREENED`, not `inactive`.
4. **`coproduct` by default; `pushout` only with a written correspondence.** A
   silent string join on disease or lineage name corrupts every edge crossing
   that seam. Every identification is stated explicitly in section 4.

No dosing language, per the project hard rule.

## 2. Reconnaissance result (2026-08-14, complete)

Reproduce: `python reports/prism_2026-08-14/recon.py`. It reads **only**
metadata — screened compound names and cell-line lineages — and never opens a
viability matrix or a dose-response parameter, so running it does not
contaminate the pre-registration. Reading
`secondary-screen-dose-response-curve-parameters.csv` *would*.

### 2a. Source, and a correction to the plan's assumption

**PRISM Repurposing 19Q4**, DOI `10.6084/m9.figshare.9393293.v4` (Corsello et
al., *Nature Cancer* 2020). Reachable over the figshare API without
authentication.

The DepMap portal itself now serves a **Cloudflare human-verification
interstitial** to automated clients, so `depmap.org/portal/api/download/files`
returns an HTML challenge page rather than JSON. The DepMap 24Q2 figshare
deposit carries CRISPR and omics matrices — useful for Phase 1c — but **no
Repurposing files**. 19Q4 is therefore the automatable release, and the pipeline
must not be built on the assumption that a newer one can be fetched unattended.

Scale: **1,448 compounds** with 8-point dose-response (secondary screen),
**4,518** at single dose (primary screen), **568 cell lines**, **24 lineages**.

### 2b. The finding that reshapes this phase

**PRISM 19Q4 contains zero haematological cell lines.** Not a gap in one screen —
both the primary and secondary cell-line tables list the same 568 adherent lines
across 24 solid-tissue lineages, with no blood, lymphoid, myeloid, or plasma-cell
entry.

The GRAND_PLAN's premise that "54 of 60 are `KNOWN_DRUG_NEW_CANCER`, so PRISM
covers a large fraction of your candidate space" **does not survive the data**.
Coverage is limited by lineage and by screening vintage, not by candidate class:

| Stratum | Pairs | Why |
|---|---:|---|
| `TIER_A_HEADLINE` | **16** | Dose-response drug, lineage with ≥15 cell lines |
| `TIER_B_UNDERPOWERED` | 6 | Dose-response drug, soft tissue (n=5 lines) |
| `SECONDARY_SINGLE_DOSE_ONLY` | 5 | Primary screen only; no dose-response curve |
| `REFUSED_DRUG_NOT_SCREENED` | 11 | Compound absent from both screens |
| `REFUSED_NO_CORRESPONDENCE` | 22 | No lineage exists to adjudicate against |

Of 40 candidate drugs, 21 have dose-response data, 6 have single-dose only, and
13 were never screened. Three are **biologics a small-molecule viability screen
cannot test at all** (amivantamab, ramucirumab, beperminogene perplasmid). Most
of the rest are approvals that post-date the 19Q4 release, but that split is
asserted per compound at step 4 against recorded approval dates rather than from
memory — **nitroglycerin is an old drug and its absence is library composition,
not vintage**, which is why `NOT_SCREENED_UNKNOWN_REASON` exists in the
vocabulary. None of these absences is evidence of inactivity.

The 22 refused for lineage are 12 haematological (CLL 5, Myelofibrosis 4,
Multiple_Myeloma 2, AML 1), 6 Li-Fraumeni (already a category error in the
review), and 4 GIST (section 4b).

**So the honest scope of Phase 1b is 16 pre-registered pairs**, plus 11 reported
under explicit limitation labels. This is not enough for a precision estimate
and must never be presented as one. It is enough to ask, of 16 named
predictions, whether measured lineage-selective activity exists — which is 16
more than this project has ever had.

## 3. Schema

Two committed JSON artifacts under `reports/prism_2026-08-14/`, mirroring the
proven trial-recovery pattern: raw data gitignored under `data/external/`,
distilled records committed under `reports/` because the build reads them (a
gitignored cache gives two people different databases).

### 3a. `DISEASE_CORRESPONDENCE.json` — the written identification

One record per PHARM disease. This is the pushout span, made reviewable.

```json
{
  "pharm_disease": "RCC",
  "prism_lineage": {"primary_tissue": "kidney", "secondary_tissue": null},
  "n_cell_lines": 19,
  "correspondence_type": "SUPERSET",
  "justification": "PRISM's kidney lineage is not subtyped; it contains renal cell carcinoma lines but is not restricted to them.",
  "known_discrepancy": "Non-RCC kidney tumours (e.g. Wilms) may be present. A selectivity result is over 'kidney', not over 'RCC'.",
  "power_tier": "A",
  "decided_on": "2026-08-14"
}
```

`correspondence_type` is one of `DIRECT`, `NEAR`, `SUPERSET`, `REFUSED`. There
is no default and no fallback: a disease absent from this file is `REFUSED`, and
a `REFUSED` disease can never acquire a lineage by string similarity.

### 3b. `PRISM_OBSERVATIONS.json` — the measured rows

One record per (candidate pair, compound, screen), written **after** scoring.

```json
{
  "review_id": "R07",
  "drug": "Mebendazole",
  "broad_id": "BRD-K...",
  "disease": "RCC",
  "prism_lineage": "kidney",
  "screen_id": "MTS010",
  "endpoint": "dose_response_auc",
  "n_target_lines": 19,
  "n_other_lines": 549,
  "median_auc_target": null,
  "median_auc_other": null,
  "selectivity_delta": null,
  "mannwhitney_p": null,
  "bh_q": null,
  "pan_lineage_cytotoxic": false,
  "verdict": "…",
  "stratum": "TIER_A_HEADLINE",
  "source_file": "secondary-screen-dose-response-curve-parameters.csv",
  "source_sha256": "…",
  "human_reviewed": 0
}
```

Every row records where it came from. `human_reviewed = 0` throughout —
automated extraction is not review, exactly as with recovered trial results.

### 3c. Verdict vocabulary

Retrieval and measurement only. No verdict asserts clinical efficacy.

- `LINEAGE_SELECTIVE_ACTIVITY` — target lineage more sensitive, and the compound
  is not pan-lineage cytotoxic.
- `PAN_LINEAGE_CYTOTOXIC` — active broadly; the built-in negative control fired.
  This is a *disconfirmation of selectivity*, not a pass.
- `NO_LINEAGE_SELECTIVITY` — screened, curve fit, no target-lineage preference.
- `SCREENED_INCONCLUSIVE` — screened but curve fits failed convergence or `r2`
  thresholds in too many lines.
- `NOT_SCREENED_BIOLOGIC` / `NOT_SCREENED_POST_DATING_RELEASE` /
  `NOT_SCREENED_UNKNOWN_REASON` — absence, categorised, never scored.
- `NO_LINEAGE_CORRESPONDENCE` — no adjudication surface exists.
- `UNDERPOWERED_REPORTED` — Tier B; effect size reported, excluded from headline.

## 4. The correspondence, stated explicitly

**Default is coproduct.** `PHARM:RCC` and `PRISM:kidney` remain distinct
objects; the PHARM candidate is *annotated* with a PRISM observation and no
identity is asserted. A pushout — gluing the two along a span — is used only
where section 3a records a justification, and the resulting verdict always names
the PRISM lineage rather than the clinical entity.

### 4a. Accepted identifications

| PHARM disease | PRISM lineage | n | Type | Tier |
|---|---|---:|---|---|
| Melanoma | skin / melanoma | 43 | `DIRECT` | A |
| NSCLC | lung / lung_NSC | 90 | `NEAR` | A |
| Glioblastoma | central_nervous_system / glioma | 39 | `SUPERSET` | A |
| Pancreatic_Cancer | pancreas | 37 | `SUPERSET` | A |
| Colorectal_Cancer | colorectal | 35 | `SUPERSET` | A |
| Breast_Cancer | breast | 26 | `SUPERSET` | A |
| HCC | liver | 21 | `SUPERSET` | A |
| RCC | kidney | 19 | `SUPERSET` | A |
| Soft_Tissue_Sarcoma | soft_tissue | 5 | `SUPERSET` | **B** |
| Prostate_Cancer | prostate | 4 | `SUPERSET` | **B** |

`NEAR` rather than `DIRECT` for NSCLC is deliberate. PRISM labels these lines
`lung_NSC`, which is a genuine non-small-cell annotation and closer than the
TCGA LUAD+LUSC join the boundary rules warn about — but a clinical NSCLC
indication is still not a panel of 90 adherent lines, and the driver
distribution differs. State it; do not silently equate it.

`SUPERSET` is load-bearing, not decorative. `glioma` includes grade II–III
tumours that are not glioblastoma; `liver` includes one hepatoblastoma line,
excluded by name; `kidney` is unsubtyped. A selectivity result is a statement
about the PRISM lineage, and the verdict text must say so.

### 4b. Refusals, and why each is a refusal

- **GIST → nothing.** GIST is a KIT/PDGFRA-driven mesenchymal tumour of the gut
  wall. PRISM's `gastric` lineage is 18 adenocarcinoma lines plus 3 others —
  a different cell of origin with different drivers. Joining them on "stomach"
  is precisely the silent string join the boundary rule forbids. 4 pairs refused.
- **CLL, AML, Myelofibrosis, Multiple_Myeloma → nothing.** No haematological
  lineage exists in 19Q4. 12 pairs refused. This is the phase's largest loss and
  it cannot be repaired by choosing a different threshold.
- **Li_Fraumeni_Syndrome → nothing.** A germline predisposition syndrome, not a
  tumour indication; the 60-candidate review already classified these as
  `EXCLUDE_CATEGORY_ERROR`. 6 pairs refused, consistent with the existing verdict.

### 4c. Compound identification

Drug→compound matching is a correspondence too, and a lowercase string match is
not good enough to stand alone. Matching runs on name, then is **verified
against the `smiles` column** carried in the treatment-info tables; any pair that
matches by name but disagrees on structure is recorded as `AMBIGUOUS_MATCH` and
excluded rather than guessed. Salt and formulation variants sharing a `broad_id`
prefix are collapsed only with the collapse recorded per row.

## 5. The adjudication rule (pre-registered; frozen before scoring)

**Primary endpoint.** Dose-response `auc` from
`secondary-screen-dose-response-curve-parameters.csv`, screen `MTS010` where
available per the dataset readme, otherwise the earlier screen, with the choice
recorded per row. Lower AUC is greater sensitivity.

**Quality filter, applied before any comparison.** Drop cell lines whose curve
fit did not converge or falls below a fixed `r2` floor; drop lines failing STR
profiling. Both thresholds are fixed in the pre-registration, not tuned.

**Selectivity statistic.** For compound *c* and target lineage *L*:
`selectivity_delta = median(AUC outside L) − median(AUC in L)`, positive meaning
the target lineage is more sensitive. Significance by two-sided Mann-Whitney U
of target versus non-target lines, Benjamini-Hochberg corrected across the 16
Tier A pairs. Rank-based because AUC is bounded and non-normal.

**The built-in negative control.** Independently of the above, a compound is
`pan_lineage_cytotoxic` when its median AUC across *all* lineages falls below a
pre-set floor. Such a compound cannot receive `LINEAGE_SELECTIVE_ACTIVITY` even
if its delta is significant. The platinums (cisplatin, carboplatin, oxaliplatin)
are expected to trip this, and that expectation is itself the control on the
control: if they do not, the threshold is wrong and the run is invalid.

**Abstention.** A pair is `SCREENED_INCONCLUSIVE` when fewer than a pre-set
number of target-lineage lines survive the quality filter. Abstention is a
recorded outcome, never silently a negative.

**Thresholds are named as numbers in the frozen file, not here**, so that this
prose can never drift from what was actually committed.

## 6. Execution order — do not reorder

1. Write `DISEASE_CORRESPONDENCE.json` and the frozen candidate set with its
   strata (16 / 6 / 5 / 11 / 22 as measured in section 2b).
2. Write `PREREGISTRATION.json`: the frozen pair list, every numeric threshold,
   the statistic, the correction, and the verdict vocabulary.
3. **Hash and commit both.** SHA-256 recorded in the commit message; the commit
   timestamp is the pre-registration time. Nothing after this point may alter
   them — a threshold that turns out badly chosen is a finding to report, not a
   file to edit.
4. Only then write `evidence/acquire_prism.py`, download the dose-response file
   to gitignored `data/external/`, and score.
5. Import inside `evidence/build.py` so the records survive a rebuild, with
   offline tests against a small committed fixture.
6. Surface in `app.py` only. Verify by grep that no other package imports it.

Steps 1–3 must be a separate commit from step 4. If they are not, there is no
pre-registration.

## 7. What this can and cannot support

- **Cell lines are not patients.** No result here supports an efficacy claim, in
  either direction. A lineage-selective in-vitro signal is a reason to read
  further, nothing more.
- **CRISPR knockout is not drug inhibition.** That conflation is Phase 1c's trap;
  it is named here so it is not imported by analogy.
- **PRISM hit rates are low and confounded by general toxicity.** That is what
  the pan-lineage control is for, and it will likely fire on more compounds than
  it does not.
- **16 pairs is not a precision estimate.** Do not compute one. Do not compute
  AUROC or AUPRC against these labels and present it as a measurement, for the
  same reason `data/labels/evaluation_labels_v1.csv` carries that warning.
- **A null result is the expected outcome and is publishable.** If none of the
  16 shows lineage-selective activity, that is the fourth negative control and
  it belongs in the Phase 3 paper beside the other three.

## 8. Go/no-go

Go. 16 pre-registered pairs against measured viability is the first
externally-measured adjudication in this project's history, and the refusals are
themselves a reportable finding: **a repurposing candidate set drawn from this
graph is 37% haematological or category-error, and the most-used public
repurposing screen cannot touch any of it.**

If a future session wants the 12 haematological pairs adjudicated, that needs a
different screen (GDSC and CTRP both include suspension lines) and a separate
correspondence document. It is not a threshold change here.
