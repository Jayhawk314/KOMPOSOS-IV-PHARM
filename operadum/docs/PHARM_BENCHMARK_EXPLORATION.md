# PHARM Benchmark Exploration

Date: 2026-06-05

This note records the first full Phase 1 benchmark of PRONOIA on the real
`KOMPOSOS-IV-PHARM` drug-repurposing universe.

For a human-readable interpretation of the data findings, not just benchmark
metrics, see `docs/PHARM_FINDINGS_REPORT.md`.

## Setup

Universe:

- 78 drugs
- 20 diseases
- 1,560 drug-disease pairs
- 44 positive `treats` labels

Primary command:

```powershell
python -m operadum.validation.pronoia_pharm_benchmark --protocol remove_direct_labels --quality all
```

The `remove_direct_labels` protocol hides direct Drug->Disease treatment labels
and label-derived bridges from PRONOIA evidence, while still scoring against the
full positive label set. This is the useful prediction protocol.

**Caveat for every AUROC/AUPRC below:** these are all **in-graph hidden-label**
metrics on the same 44 positives — the direct edge is hidden but the full
curated graph is still visible. A score family edging the KOMPOSOS baseline here
reflects in-graph recovery, not better generalization. External generalization
is weak for both engines (Hetionet CtD AUROC ~0.64, AUPRC ~0.01); read these
tables as search/recovery on the curated graph, not a novel-discovery hit rate.

## Raw-MDL Baseline Result

This was the first full run before PHARM score v2 was promoted. It is kept here
because it explains why raw zlib-MDL is now treated as an audit metric instead
of the primary rank score.

| Score family | AUROC | AUPRC | H@5 | H@10 | H@20 |
|---|---:|---:|---:|---:|---:|
| PRONOIA gated raw zlib-MDL | 0.393 | 0.021 | 0.000 | 0.000 | 0.000 |
| PRONOIA raw gain | 0.393 | 0.021 | 0.000 | 0.000 | 0.000 |
| Gain per evidence item | 0.388 | 0.022 | 0.000 | 0.000 | 0.000 |
| Gain per evidence kchar | 0.393 | 0.022 | 0.000 | 0.000 | 0.000 |
| Grounding alone | 0.359 | 0.021 | 0.000 | 0.000 | 0.000 |
| Evidence sum | 0.699 | 0.178 | 0.800 | 0.500 | 0.300 |
| Evidence max | 0.981 | 0.577 | 0.600 | 0.700 | 0.650 |
| Path max | 0.973 | 0.508 | 0.600 | 0.700 | 0.650 |
| Mechanism max | 0.981 | 0.577 | 0.600 | 0.700 | 0.650 |
| KOMPOSOS baseline | 0.971 | 0.546 | 1.000 | 0.600 | 0.600 |

Quality-tier check:

```powershell
python -m operadum.validation.pronoia_pharm_benchmark --protocol remove_direct_labels --quality high
```

High-tier evidence did not fix raw MDL. It improved `evidence_sum`, while
`evidence_max` and `mechanism_max` stayed strong.

| Score family | AUROC | AUPRC | H@5 | H@10 | H@20 |
|---|---:|---:|---:|---:|---:|
| PRONOIA gated raw zlib-MDL | 0.462 | 0.025 | 0.000 | 0.000 | 0.000 |
| Evidence sum | 0.952 | 0.335 | 0.400 | 0.600 | 0.450 |
| Evidence max | 0.981 | 0.577 | 0.600 | 0.700 | 0.650 |
| Path max | 0.973 | 0.506 | 0.600 | 0.700 | 0.650 |
| Mechanism max | 0.970 | 0.573 | 0.600 | 0.700 | 0.650 |
| KOMPOSOS baseline | 0.972 | 0.634 | 1.000 | 0.800 | 0.700 |

## PHARM Score v2 Result

Score v2 uses the strongest structured PHARM mechanism/path evidence as the
base prediction score, applies the L5 grounding gate as a penalty/abstention
signal, and keeps raw zlib-MDL gain in the report for transparency.

Primary commands:

```powershell
python -m operadum.validation.pronoia_pharm_benchmark --protocol remove_direct_labels --quality all
python -m operadum.validation.pronoia_pharm_benchmark --protocol remove_direct_labels --quality high
```

Current full `quality=all` result:

- 1,560 pairs
- 44 positives
- 257 abstentions (0.165)
- mean grounding 0.655

| Score family | AUROC | AUPRC | H@5 | H@10 | H@20 | MRR |
|---|---:|---:|---:|---:|---:|---:|
| PRONOIA v2 | 0.981 | 0.577 | 0.600 | 0.700 | 0.650 | 0.072 |
| PRONOIA raw gain | 0.393 | 0.021 | 0.000 | 0.000 | 0.000 | 0.002 |
| Evidence max | 0.981 | 0.577 | 0.600 | 0.700 | 0.650 | 0.072 |
| Path max | 0.973 | 0.508 | 0.600 | 0.700 | 0.650 | 0.069 |
| Mechanism max | 0.981 | 0.577 | 0.600 | 0.700 | 0.650 | 0.072 |
| KOMPOSOS baseline | 0.971 | 0.546 | 1.000 | 0.600 | 0.600 | 0.079 |

Current `quality=high` result:

- 1,560 pairs
- 44 positives
- 1,136 abstentions (0.728)
- mean grounding 0.658

| Score family | AUROC | AUPRC | H@5 | H@10 | H@20 | MRR |
|---|---:|---:|---:|---:|---:|---:|
| PRONOIA v2 | 0.981 | 0.577 | 0.600 | 0.700 | 0.650 | 0.072 |
| PRONOIA raw gain | 0.461 | 0.025 | 0.000 | 0.000 | 0.000 | 0.002 |
| Evidence max | 0.981 | 0.577 | 0.600 | 0.700 | 0.650 | 0.072 |
| Path max | 0.973 | 0.506 | 0.600 | 0.700 | 0.650 | 0.069 |
| Mechanism max | 0.970 | 0.573 | 0.600 | 0.700 | 0.650 | 0.072 |
| KOMPOSOS baseline | 0.972 | 0.634 | 1.000 | 0.800 | 0.700 | 0.084 |

## Diagnosis

The PHARM evidence adapter has real signal. `mechanism_max`, `path_max`,
`evidence_max`, and PRONOIA score v2 are competitive with the current KOMPOSOS
benchmark score on AUROC/AUPRC.

Raw PRONOIA zlib-MDL gain is not yet a good drug-repurposing ranker. It
over-ranks broad or long candidates, especially pairs whose evidence packet
contains many repeated tokens or long names. In the full run, the top raw-MDL
false positives were dominated by broad cancer-like evidence around
`Trastuzumab_deruxtecan` across many diseases.

Score v2 fixes the worst failure by making structured path/mechanism evidence
the primary score and leaving raw MDL gain as a transparency metric. The top
remaining false positives are more specific:

- `Adagrasib -> Pancreatic_Cancer`
- `Sotorasib -> Pancreatic_Cancer`
- `Trastuzumab_deruxtecan -> Breast_Cancer`

Those are plausible mechanism-rich pairs, so the next fix should be a real
contradiction/residual penalty, not more data movement.

## Conclusion

Keep:

- `domain_core`
- `KompososPharmEvidenceProvider`
- `PronoiaPredictor` as the report/trace wrapper
- the benchmark harness
- PHARM score v2 as the current primary PHARM ranker

Current PHARM score v2:

```text
final_score =
    evidence_path_or_mechanism_strength
    - ungrounded_penalty
    - contradiction_penalty   # placeholder, not yet wired
```

Raw zlib-MDL should remain a transparency metric, not the primary score, until a
domain-aware structured evidence codebook exists.

## Next Phase

Build **PRONOIA PHARM score v3**:

1. Add L1 sheaf contradiction/frustration as a real penalty.
2. Use the penalty to separate mechanism-rich false positives from supported
   positives.
3. Add a domain-aware codebook so MDL counts evidence structure, not compressed
   text length.
4. Keep the same benchmark harness and compare against the v2 table above.
