# PRISM adjudication — 2026-08-14

Reconnaissance for GRAND_PLAN Phase 1b. **Feasibility only — nothing has been
scored, and no acquisition code exists yet.** The proposal it feeds is
`docs/PLAN_PRISM_ADJUDICATION_2026-08-14.md`.

## Why this is safe to have run before pre-registration

`recon.py` reads only *metadata*: which compounds PRISM screened, and which
lineage each cell line belongs to. It never opens a viability matrix or a
dose-response parameter. Coverage is knowable without seeing a single outcome,
so freezing the candidate set after this is still a blind pre-registration.

Reading `secondary-screen-dose-response-curve-parameters.csv` would contaminate
it. That file is deliberately not downloaded yet.

## What it found

**PRISM Repurposing 19Q4** (DOI `10.6084/m9.figshare.9393293.v4`, Corsello et
al. 2020): 1,448 dose-response compounds, 4,518 single-dose, 568 cell lines,
24 lineages.

**Zero haematological cell lines**, in either screen. So the 60-candidate review
strata like this:

| Stratum | Pairs |
|---|---:|
| `TIER_A_HEADLINE` | **16** |
| `TIER_B_UNDERPOWERED` (soft tissue, n=5 lines) | 6 |
| `SECONDARY_SINGLE_DOSE_ONLY` | 5 |
| `REFUSED_DRUG_NOT_SCREENED` | 11 |
| `REFUSED_NO_CORRESPONDENCE` | 22 |

Of 40 candidate drugs: 21 dose-response, 6 single-dose only, 13 never screened.
Three are biologics a small-molecule viability screen cannot test at all;
most of the rest post-date the 19Q4 release, though nitroglycerin is an old drug
absent for library reasons rather than vintage. No absence is evidence of
inactivity.

This corrects the GRAND_PLAN's assumption that PRISM covers a large fraction of
the candidate space. It covers 16 pairs well. See the plan, section 2b.

## Access note

The DepMap portal serves a Cloudflare human-verification interstitial to
automated clients, so `depmap.org/portal/api/download/files` returns HTML rather
than JSON. The DepMap 24Q2 figshare deposit has CRISPR and omics matrices but no
Repurposing files. **19Q4 via figshare is the automatable release.**

## Files

- `recon.py` — reproduces `RECON_REPORT.json`. Metadata only, by construction.
- `RECON_REPORT.json` — distilled coverage facts. **Committed on purpose**, so
  the finding survives without the ~1 GB raw download.

Raw PRISM files are gitignored under
`data/external/prism_repurposing_2026-08-14/`.

## Reproduce

```powershell
python reports/prism_2026-08-14/recon.py
```

Re-downloading the metadata inputs, if the gitignored directory is absent:

```powershell
python -c "import json,urllib.request; print(json.load(urllib.request.urlopen('https://api.figshare.com/v2/articles/9393293'))['title'])"
```

The four metadata files needed are `primary-screen-cell-line-info.csv`,
`secondary-screen-cell-line-info.csv`, and both
`*-replicate-collapsed-treatment-info.csv`. `evidence/acquire_prism.py` will
automate this in step 4 of the plan's execution order.

## Next

Plan section 6, in order: write and **commit** the correspondence and
pre-registration files first, acquisition and scoring only after.
