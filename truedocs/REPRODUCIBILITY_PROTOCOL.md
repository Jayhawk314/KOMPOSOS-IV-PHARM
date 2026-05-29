# Reproducibility Protocol

**Purpose**: operational checklist for reproducing current metrics and auditing
data integrity.

**Rule**: code and database state outrank stale docs. Every metric must include
view, protocol, positive count, negative policy, and date.

---

## Current Verified Metrics (2026-05-28)

| Graph | Protocol | AUROC | AUPRC | Hits@5 | Hits@10 | Hits@20 | MRR |
|-------|----------|------:|------:|-------:|--------:|--------:|----:|
| Full graph | `remove_direct_labels` | 0.948640 | 0.513498 | 1.0000 | 0.6000 | 0.6000 | 0.076250 |
| Full graph | `loocv` | 0.949216 | 0.514703 | 0.8000 | 0.6000 | 0.6000 | 0.075237 |

Strict benchmark confidence intervals:

- AUROC: [0.9134, 0.9738]
- AUPRC: [0.3662, 0.6579]

All current benchmark runs use 78 drugs, 20 diseases, 48 positives, and 1,512
open-world unlabeled pairs. Unlabeled pairs are not confirmed negatives.

Strategic Transparency: Yoneda Distance uses only MEASURED+ESTABLISHED (1,391 edges).
The primary strict `remove_direct_labels` run uses 7 active modules because all
Drug->Disease comparator labels are removed before scoring.

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
Morphisms:  2130
Task:       78 drugs x 20 diseases = 1560 pairs
Labels:     48 positives, 1512 negatives
Scored:     1325 scored, 235 unscored
AUROC:      0.948640  95% CI [0.9134, 0.9738]
AUPRC:      0.513498  95% CI [0.3662, 0.6579]
Hits@5:     1.0000
Hits@10:    0.6000
Hits@20:    0.6000
MRR:        0.072453
```

Baselines:

```text
common_neighbor      AUROC 0.6499  (ours +0.2987)
path_count           AUROC 0.6492  (ours +0.2994)
degree_product       AUROC 0.5877  (ours +0.3609)
shortest_path        AUROC 0.6250  (ours +0.3236)
random               AUROC 0.5504  (ours +0.3982)
```

---

## Holdout Scripts

| Script | Current Result |
|--------|----------------|
| `validation\external_validation.py` | Hetionet CtD external AUROC 0.621479, AUPRC 0.008555, Hits@20 0.0000 |
| `validation\temporal_holdout.py --cutoff 2013` | Year > 2013 AUROC 0.941294, AUPRC 0.218793, Hits@20 0.2222 |
| `validation\disease_holdout.py --min-positives 2` | Mean AUROC 0.924416, mean AUPRC 0.486226 across 7 folds |

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
1146 2178 78 20 48
```

Current source-field count:

```powershell
python -c "import re,sqlite3; rows=sqlite3.connect('data/drugs/tier1.db').execute('select provenance, metadata, evidence_tier from morphisms').fetchall(); pmids=set(); [pmids.update(re.findall('PMID:?\\s*(\\d+)', ((p or '')+' '+(m or '')))) for p,m,t in rows]; print(len(rows), sum(1 for p,m,t in rows if p and p!='unknown'), len(pmids), sum(1 for p,m,t in rows if t=='MEASURED'))"
```

Expected:

```text
2178 2178 805 1014
```

Interpretation: 100% source-string coverage (2,178/2,178 edges have source strings — not the same as
citation validation), 805 distinct PMID identifiers are *present* in provenance/metadata (presence is
not verification), and 1,014 morphisms are MEASURED-tier (IC50/mutation/response/HR). Of the
PMID-backed edges, 594 are RELATION-VERIFIED (agent-confirmed directed/signed) and 215 are
LEXICAL-COOCCURRENCE (automated co-occurrence + polarity screen only).

---

## Evidence Audit Checks

```powershell
python validation\citation_attribution_audit.py --out reports\citation_attribution_audit_2026-05-28.csv
python validation\evidence_tier_audit.py --out reports\evidence_tier_split_2026-05-28.csv
```

The system achieves 100% source-string coverage after restoring 302 'unknown' edges (source-string presence is not edge-level citation verification).

---

## Retired And Superseded Numbers

- `0.974694 AUROC / 0.551698 AUPRC`: superseded by current verified audit.
- `0.9689 AUROC / 0.661 AUPRC`: retired because of Yoneda label leakage.
- `0.9562 AUROC`: intermediate post-leakage strict result.
- `shortest_path 0.931`: stale baseline claim.

---

## Recommended Claim Language

> KOMPOSOS-IV-PHARM is a research prototype for drug repurposing over a curated
> drug-target-disease knowledge graph. Under the `full_typed/remove_direct_labels`
> protocol on 78 drugs x 20 diseases (48 FDA-approved indications vs. 1,512
> open-world unlabeled pairs), the current strict 7-module scorer achieves AUROC
> 0.948640 [0.9134, 0.9738] and AUPRC 0.513498 [0.3662, 0.6579]. 100% source-string
> coverage (2,178/2,178 edges; not the same as citation validation). Every prediction can be traced to
> graph evidence chains with source strings and tiered citation identifiers (594 RELATION-VERIFIED, 215 LEXICAL-COOCCURRENCE).
> Strategic Transparency: Yoneda distance uses only MEASURED+ESTABLISHED evidence (1,391 edges).

Do not claim:

- Clinical readiness.
- "No leakage" without naming the protocol and label-removal policy.
- 100% validated citation provenance.
- External generalization without mentioning Hetionet AUROC 0.634479 and Hits@20 0.

---

*Last updated: 2026-05-27.*
