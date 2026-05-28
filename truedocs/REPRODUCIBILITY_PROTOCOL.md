# Reproducibility Protocol

**Purpose**: operational checklist for reproducing current metrics and auditing
data integrity.

**Rule**: code and database state outrank stale docs. Every metric must include
view, protocol, positive count, negative policy, and date.

---

## Current Verified Metrics (2026-05-27)

| Graph | Protocol | AUROC | AUPRC | Hits@5 | Hits@10 | Hits@20 | MRR |
|-------|----------|------:|------:|-------:|--------:|--------:|----:|
| Full graph | `remove_direct_labels` | 0.974694 | 0.551698 | 1.0000 | 0.6000 | 0.6000 | 0.078750 |
| Full graph | `loocv` | 0.975916 | 0.553703 | 0.8000 | 0.6000 | 0.6000 | 0.077237 |
| Full graph | `as_loaded` | 0.738831 | 0.049407 | 0.0000 | 0.0000 | 0.0000 | 0.002825 |

Strict benchmark confidence intervals:

- AUROC: [0.9606, 0.9855]
- AUPRC: [0.4067, 0.6983]

All current benchmark runs use 78 drugs, 20 diseases, 44 positives, and 1,516
open-world unlabeled pairs. Unlabeled pairs are not confirmed negatives.

---

## Canonical Commands

```powershell
# Primary strict metric
python validation\repurposing_benchmark.py --view full_typed --protocol remove_direct_labels --baselines --ci

# Leave-one-positive-edge-out validation
python validation\repurposing_benchmark.py --view full_typed --protocol loocv

# Dataset/protocol artifact check
python validation\repurposing_benchmark.py --view full_typed --protocol as_loaded

# External, temporal, and disease holdouts
python validation\external_validation.py
python validation\temporal_holdout.py --cutoff 2013
python validation\disease_holdout.py --min-positives 2
```

---

## Expected Strict Output

```text
View:       full_typed
Protocol:   remove_direct_labels
Objects:    1146
Morphisms:  5329
Task:       78 drugs x 20 diseases = 1560 pairs
Labels:     44 positives, 1516 negatives
Scored:     1325 scored, 235 unscored
AUROC:      0.974694  95% CI [0.9606, 0.9855]
AUPRC:      0.551698  95% CI [0.4067, 0.6983]
Hits@5:     1.0000
Hits@10:    0.6000
Hits@20:    0.6000
MRR:        0.078750
```

Baselines:

```text
degree_product       AUROC 0.6307  (ours +0.3440)
common_neighbor      AUROC 0.6260  (ours +0.3487)
path_count           AUROC 0.5777  (ours +0.3970)
shortest_path        AUROC 0.5775  (ours +0.3972)
random               AUROC 0.5623  (ours +0.4124)
```

---

## Holdout Scripts

| Script | Current Result |
|--------|----------------|
| `validation\external_validation.py` | Hetionet CtD external AUROC 0.634479, AUPRC 0.009255, Hits@20 0.0000 |
| `validation\temporal_holdout.py --cutoff 2013` | Year > 2013 AUROC 0.977994, AUPRC 0.228793, Hits@20 0.2222 |
| `validation\disease_holdout.py --min-positives 2` | Mean AUROC 0.950416, mean AUPRC 0.636826 across 7 folds |

External Hetionet performance is weak at the top of the ranking and should be
reported as a limitation.

---

## Database Checks

Current runtime graph:

```powershell
python -c "from validation.repurposing_benchmark import load_full_typed_view, drug_disease_pairs; c,_=load_full_typed_view(); d,dis,pos=drug_disease_pairs(c); print(len(c.objects()), len(c.morphisms()), len(d), len(dis), len(pos))"
```

Expected:

```text
1146 5382 78 20 44
```

Current source-field count:

```powershell
python -c "import re,sqlite3; rows=sqlite3.connect('data/drugs/tier1.db').execute('select provenance, metadata, quantitative_value from morphisms').fetchall(); pmids=set(); [pmids.update(re.findall('PMID:?\\s*(\\d+)', ((p or '')+' '+(m or '')))) for p,m,q in rows]; print(len(rows), sum(1 for p,m,q in rows if p and p!='unknown'), len(pmids), sum(1 for p,m,q in rows if q is not None))"
```

Expected:

```text
5382 5382 610 204
```

Interpretation: all morphisms have source/provenance strings, 610 unique PMID
identifiers are present, and 204 morphisms have structured quantitative values.
This is not the same as edge-specific citation validation.

---

## Evidence Audit Checks

```powershell
python validation\citation_attribution_audit.py --out reports\citation_attribution_audit_2026-05-27.csv
python validation\evidence_tier_audit.py --out reports\evidence_tier_split_2026-05-27.csv
```

Current risk flags:

| Flag | Count |
|------|------:|
| PMID without context | 549 |
| MEASURED-tier mismatch | 156 |
| Quantitative value not endpoint-specific | 27 |

Do not claim "100% validated provenance." The defensible claim is "source
strings on all morphisms, with edge-specific attribution audit still required."

---

## Retired And Superseded Numbers

- `0.9689 AUROC / 0.661 AUPRC`: retired because of Yoneda label leakage.
- `0.9562 AUROC`: intermediate post-leakage strict result, superseded by the
  current `0.974694` strict run after Topos/scoring alignment.
- `shortest_path 0.931`: stale baseline claim; current strongest simple
  baseline is degree_product AUROC 0.6307.

---

## Recommended Claim Language

> KOMPOSOS-IV-PHARM is a research prototype for drug repurposing over a curated
> drug-target-disease knowledge graph. Under the `full_typed/remove_direct_labels`
> protocol on 78 drugs x 20 diseases (44 FDA-approved indications vs. 1,516
> open-world unlabeled pairs), the current nine-strategy scorer achieves AUROC
> 0.974694 [0.9606, 0.9855] and AUPRC 0.551698 [0.4067, 0.6983]. Every
> prediction can be traced to graph evidence chains with source strings and edge
> confidence values. These are retrospective ranking metrics, not clinical
> probabilities.

Do not claim:

- Clinical readiness.
- "No leakage" without naming the protocol and label-removal policy.
- 100% validated citation provenance.
- External generalization without mentioning Hetionet AUROC 0.634479 and Hits@20 0.

---

*Last updated: 2026-05-27.*
