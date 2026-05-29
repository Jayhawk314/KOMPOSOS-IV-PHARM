# Validation and Benchmarks

**Purpose**: define the current validation protocols, exact reproduced metrics,
and the limits on what those metrics mean.

**Current source of truth**: executable runs from `validation/repurposing_benchmark.py`
and the 2026-05-28 holdout scripts. Code and live database state outrank older
session notes.

---

## Current Strict Benchmark

Command:

```powershell
python validation\repurposing_benchmark.py --view full_typed --protocol remove_direct_labels --baselines --ci
```

Current output, rerun on 2026-05-28:

| Metric | Value |
|--------|-------|
| View | `full_typed` |
| Protocol | `remove_direct_labels` |
| Runtime graph | 1,146 objects; 2,119 morphisms after label removal |
| Task | 78 drugs x 20 diseases = 1,560 pairs |
| Labels | 48 positives; 1,512 open-world unlabeled pairs |
| Scored | 1,182 scored; 378 unscored |
| Active strategy profile | 7 modules; Yoneda distance excluded |
| AUROC | **0.948640** [95% CI 0.9134, 0.9738] |
| AUPRC | **0.513498** [95% CI 0.3662, 0.6579] |
| Hits@5 | 1.0000 |
| Hits@10 | 0.6000 |
| Hits@20 | 0.6000 |
| MRR | 0.072453 |

Baselines on the same corrected graph:

| Baseline | AUROC | System Margin |
|----------|-------|---------------|
| common_neighbor | 0.6499 | +0.2987 |
| path_count | 0.6492 | +0.2994 |
| shortest_path | 0.6250 | +0.3236 |
| degree_product | 0.5877 | +0.3609 |
| random | 0.5504 | +0.3982 |

**Strategic Transparency**: Yoneda Distance uses only MEASURED+ESTABLISHED (1,391 edges).

The older `0.9689 AUROC / 0.661 AUPRC` claim is retired because the Yoneda
module could see held-out Drug->Disease labels. The later `0.9562` value was an
intermediate post-leakage audit result, superseded by the current Topos-aligned
strict run above.

Current runtime distinction:

- **Live triage / `as_loaded`**: 8 modules, including conditional Yoneda distance.
- **Strict `remove_direct_labels`**: 7 active modules. Yoneda distance is not listed
  as active because all visible Drug->Disease treatment comparators are removed.

---

## Protocol Definitions

### `remove_direct_labels`

This is the primary internal validation protocol.

1. Remove direct Drug->Disease approval labels.
2. Remove explicit label-derived Protein->Disease bridges.
3. Score all 1,560 drug-disease pairs.
4. Evaluate 48 FDA-approved pairs against 1,512 open-world unlabeled pairs.
5. Exclude Yoneda distance from the active strategy list because its comparator
   set is intentionally empty under this protocol.

Unlabeled pairs are unknowns, not confirmed negatives. AUROC measures ranking
order in this benchmark, not clinical probability.

### `loocv`

Command:

```powershell
python validation\repurposing_benchmark.py --view full_typed --protocol loocv
```

Current output:

| Metric | Value |
|--------|-------|
| AUROC | 0.975916 |
| AUPRC | 0.553703 |
| Hits@5 | 0.8000 |
| Hits@10 | 0.6000 |
| Hits@20 | 0.6000 |
| MRR | 0.077237 |

This hides one approved label at a time while retaining the rest of the training
graph. It is useful, but still retrospective.

### `as_loaded`

Command:

```powershell
python validation\repurposing_benchmark.py --view full_typed --protocol as_loaded
```

Current output:

| Metric | Value |
|--------|-------|
| AUROC | 0.738831 |
| AUPRC | 0.049407 |
| Hits@5 | 0.0000 |
| Hits@10 | 0.0000 |
| Hits@20 | 0.0000 |
| MRR | 0.002825 |

This is not the recommended repurposing validation protocol. It is retained as
a dataset/protocol artifact check.

---

## Additional Executable Holdouts

### Hetionet CtD External Validation

Command:

```powershell
python validation\external_validation.py
```

Current output:

| Metric | Value |
|--------|-------|
| External positives | 7 |
| Candidate pairs | 1,516 |
| AUROC | 0.634479 |
| AUPRC | 0.009255 |
| Hits@5 / Hits@10 / Hits@20 | 0.0000 / 0.0000 / 0.0000 |
| MRR | 0.003399 |

Interpretation: external precision-at-top is weak. This result should temper
internal AUROC claims.

### Temporal Holdout

Command:

```powershell
python validation\temporal_holdout.py --cutoff 2013
```

Current output:

| Metric | Value |
|--------|-------|
| Policy | approval year > 2013 |
| Held-out labels | 18 |
| AUROC | 0.977994 |
| AUPRC | 0.228793 |
| Hits@5 / Hits@10 / Hits@20 | 0.0000 / 0.2000 / 0.2222 |
| MRR | 0.039131 |

### Disease-Level Holdout

Command:

```powershell
python validation\disease_holdout.py --min-positives 2
```

Current output:

| Disease | AUROC | AUPRC |
|---------|-------|-------|
| Breast_Cancer | 0.986301 | 0.710000 |
| Colorectal_Cancer | 0.787162 | 0.147265 |
| GIST | 0.991111 | 0.866667 |
| HCC | 0.967105 | 0.366667 |
| Melanoma | 1.000000 | 1.000000 |
| NSCLC | 0.954106 | 0.694963 |
| RCC | 0.967123 | 0.672222 |

Summary:

| Metric | Value |
|--------|-------|
| Folds | 7 |
| Mean AUROC | 0.950416 |
| Median AUROC | 0.967123 |
| Mean AUPRC | 0.636826 |
| Median AUPRC | 0.694963 |
| AUROC range | 0.787162-1.000000 |

---

## Ranking Calibration

Ranking scores are not clinical probabilities. The calibration artifact maps
ranking-score bins to observed FDA-label rates in the strict benchmark:

```powershell
python validation\build_ranking_score_calibration.py
```

Current artifact: `reports/ranking_score_calibration_2026-05-28.json`

| Calibration Field | Value |
|-------------------|-------|
| Protocol | `remove_direct_labels` |
| Pairs | 1,560 |
| Positives | 48 |
| Benchmark prevalence | 0.030769 |
| Score AUROC | 0.948640 |
| Brier, benchmark label rate | 0.024562 |
| Top score bin | 0.774085-1.000000 |
| Top bin observed label rate | 0.230769 |

The UI label "benchmark label rate" means a score-bin FDA-label rate under this
benchmark. It is not a patient response probability.

---

## Evidence And Provenance Caveat

Current database facts:

- **100% provenance coverage**: 2,178/2,178 morphisms have source/provenance strings.
- **188 unique PMID identifiers** are verified from audit master.
- **1,014 morphisms** have structured quantitative values.

The system achieves 100% honest provenance after restoring 302 'unknown' edges from the verified master.
Every prediction can be traced to graph evidence chains with source strings
and verified citation identifiers.

---

## Interpretation Rules

1. Never report AUROC without view, protocol, positive count, negative policy,
   and confidence interval.
2. Never call a ranking score or strategy score a clinical probability.
3. Treat unlabeled drug-disease pairs as open-world unknowns.
4. Use AUPRC, Hits@K, MRR, and external validation alongside AUROC.
5. Treat Hetionet external validation as a current weakness: AUROC is only
   0.634479 and Hits@20 is 0.
6. The system's research value is the auditable mechanistic trail, not just the
   headline AUROC.
