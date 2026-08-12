# AlphaFold Structural-Coherence Feasibility Result

Generated 2026-08-12 from 34 cancer-related human proteins inherited from the
older KOMPOSOS structural workspace.

## Result

This run produced **no AlphaFold-specific structural contradiction**.

| Outcome | Proteins | Meaning |
|---|---:|---|
| No AlphaFold conflict | 12 | AlphaFold agreed with the selected experimental structures under the provisional thresholds. |
| AlphaFold quarantine | 5 | Cross-domain PAE was too high to judge the relative domain pose. |
| Experimental and AlphaFold conflict | 3 | The experimental structures also disagreed with one another, so the result cannot be assigned specifically to AlphaFold. |
| Experimental conformational variation only | 1 | Experimental structures disagreed, while AlphaFold did not exceed the thresholds. |
| Structurally ineligible | 13 | Fewer than two usable domains or fewer than two experimental structures with sufficient observed residues. |

All 34 accessions completed acquisition and selection without processing errors.
Twenty-one were geometrically analyzable.

The three non-specific conflict cases were EGFR (`P00533`), MET (`P08581`) and
RAD51 (`Q06609`). VEGFR2 (`P35968`) showed experimental conformational variation
without an AlphaFold conflict. These are review targets, not discoveries that
AlphaFold is wrong.

## What changed during the run

The first pass trusted construct-level PDBe coverage. That admitted structures
whose sequence records spanned a domain even though the domain had no observed
coordinates. The final pass uses the SIFTS observed-residue table instead.

The sequence mapper also originally used a global alignment whose traceback
could choose the wrong equally scoring placement around long construct
deletions. The final mapper anchors exact same-protein sequence blocks first and
retains the global-alignment fallback for genuinely divergent homologs. Focused
tests cover both corrections.

## Inputs and receipts

- `SOURCE_ACCESSIONS.json`: the exact 34-accession input set.
- `SUMMARY.csv`: one row per accession with domains, PAE, experimental models,
  standing and classification.
- `COHORT.json`: the same result in machine-readable form.
- `RUN_METADATA.json`: command settings and completion counts.
- `data/external/alphafold_coherence_2026-08-12/`: cached source responses,
  coordinate files, manifests, SHA-256 provenance and complete Oracle reports.

Public sources are AlphaFold DB, InterPro, PDBe, RCSB PDB and the SIFTS
observed-residue export. The large cache is intentionally excluded from Git;
the builder recreates it.

Reproduce from the repository root:

```powershell
python validation/build_alphafold_coherence_cohort.py --max-experimental 3
```

## What this establishes

The software can acquire real public data, preserve receipts, align partial
experimental constructs, measure relative domain-pose defects, compose
structure transformations and refuse conclusions when AlphaFold's own PAE says
the pose is uncertain. It also separates an AlphaFold-specific discrepancy from
experimental conformational variation.

It does **not** establish that the measurements detect biologically important
AlphaFold errors. Synthetic unit tests prove the implementation responds to a
known injected pose error, but that is a technical control rather than a
biological sensitivity estimate.

## One required external next step

Before scaling to AlphaFold DB, freeze a literature-curated positive-control
set containing experimentally demonstrated AlphaFold domain-orientation or
interface errors, plus matched agreement and alternative-conformation cases.
Run it blind, compare against PAE and ordinary pairwise alignment, then decide
whether the horn-composition measurements add any useful signal. Until that
test succeeds, this remains a working auditor with a null feasibility result,
not a validated AlphaFold discovery system.
