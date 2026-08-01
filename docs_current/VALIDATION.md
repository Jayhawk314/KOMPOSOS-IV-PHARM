# Validation — SUPERSEDED historical snapshot (2026-06-02)

> **⚠ SUPERSEDED. Do not quote any number on this page.**
>
> This file is a dated snapshot of the graph as it stood on **2026-06-02**, before
> the July integrity work. It is retained for history only. Every headline figure
> below has since been retired or replaced:
>
> - The primary AUROC **0.970549** predates the ESMC similarity-transfer exclusion.
>   The current strict `core` result is **AUROC 0.9784 / AUPRC 0.6128**
>   (scored-only AUROC **0.9642**), with a **+0.24** margin over common-neighbor
>   **0.7429** — not the +0.35 shown below.
> - "Hits@5 / @10 / @20" on this page is **precision@k**, not Hits@k.
> - The **Hetionet external row is retired and is not reproducible**:
>   `data/external/` is absent from the repository and gitignored, so
>   `validation/external_validation.py` raises `FileNotFoundError`.
> - The **temporal holdout row is stale and was run on the wrong (`all`) cohort**;
>   it also leaves post-cutoff literature in the graph, and its negative set
>   contains approved indications.
> - The **LOOCV and disease-holdout rows have not been re-measured** since the ESMC
>   exclusion and should be treated as unverified.
>
> **Current source of truth: `HONEST_VALUE.md`, then `CLAUDE.md`, then the
> executable reproduce commands.** External precision is *undetermined*, not weak.

All numbers below are from runs on `data/drugs/tier1.db` (2,329 morphisms) on
2026-06-02 and are preserved unedited as a historical record.

## Primary strict benchmark

`full_typed` view, `remove_direct_labels` protocol (removes the direct Drug→Disease
label *and* indication-derived bridge edges before scoring).

| Metric | Value |
|---|---|
| Positives | 44 (FDA `treats` indications only) |
| Negatives | 1,516 open-world unlabeled pairs |
| Pairs scored | 1,293 (267 unscored) |
| AUROC | **0.970549** [95% CI 0.9519, 0.9844] |
| AUPRC | 0.546427 [95% CI 0.4025, 0.6890] |
| Hits@5 / @10 / @20 | 1.0000 / 0.6000 / 0.6000 |

> Note: positives are `treats` edges only. An earlier harness counted 48 by
> including 4 inferred `associated_with` HYPOTHESIS Drug→Disease edges as
> "approvals"; that was a bug, now fixed (hence 44, and a higher AUROC than the
> retired 0.948640/48-positive run).

## Baselines (same graph)

| Baseline | AUROC | System margin |
|---|---|---|
| common_neighbor | 0.6219 | +0.3486 |
| path_count | 0.6203 | +0.3502 |
| shortest_path | 0.5881 | +0.3825 |
| degree_product | 0.5852 | +0.3853 |
| random | 0.5623 | +0.4083 |

## Holdouts

| Validation | AUROC | AUPRC | Notes |
|---|---|---|---|
| LOOCV | 0.967431 | 0.516478 | Hits@5 0.80 / @10 0.60 / @20 0.65 |
| Temporal (approvals after 2013) | 0.970646 | 0.193802 | 18 held-out approvals |
| Hetionet CtD (external) | 0.643615 | 0.009513 | 7 external positives; Hits@20 = 0 (weak) |
| Disease holdout (7 folds) | mean 0.937795 / median 0.967105 | mean 0.602051 / median 0.596190 | AUROC range 0.756757–1.000000 |

## Interpretation

- The strict AUROC measures **label recovery** under leakage controls, not
  real-world repurposing success.
- The **external Hetionet result is the key caveat**: strong internal numbers do
  not transfer to an independent external positive set at this graph size.
- All claims must name view, protocol, positive count, and label policy.
