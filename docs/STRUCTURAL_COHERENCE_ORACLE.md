# KOMPOSOS Structural-Coherence Oracle

The AlphaFold structural auditor is exposed through a dedicated KOMPOSOS
Oracle specialization:

```powershell
python -m oracle.structural_coherence path/to/manifest.json --output oracle-report.json
```

The manifest format, measurements and uncertainty rules are documented in
`ALPHAFOLD_COHERENCE_AUDITOR.md`.

## Why this is an Oracle

For every related structure family, the Oracle:

1. constructs domain-specific rigid morphisms from measured residue
   correspondences;
2. enumerates relative domain arrangements;
3. enumerates structural A-to-B-to-C horns;
4. composes the A-to-B and B-to-C SE(3) transformations;
5. compares the composed filler with the directly observed A-to-C morphism;
6. ranks assessable conflicts and retains quarantined checks separately;
7. attaches the coordinate-file paths as receipts.

The result records every check. `ranked_findings` contains only
`INCONSISTENT` and `QUARANTINE` checks; passing triangles do not become anomaly
findings.

For an assessable conflict, `review_priority` is the largest measured defect
divided by its configured threshold. A value of `1.0` is the current boundary;
`3.0` means three times the boundary. This is a review-ordering ratio, not a
probability that AlphaFold is wrong.

Quarantined checks have `review_priority: null`. The Oracle does not turn a
missing PAE matrix, inadequate residue coverage or excessive uncertainty into
a weak score.

## Why it is not in the default drug Oracle

`CategoricalOracle.predict(source, target)` predicts a missing relation with a
scalar confidence. The structural Oracle instead compares observed spatial
transformations across an entire family. It therefore has a family-level API:

```python
from oracle.structural_coherence import StructuralCoherenceOracle

result = StructuralCoherenceOracle(config).audit_family(
    family_id="example-family",
    models=models,
    domains=domains,
    reference_model="AF_HUMAN",
)
```

Keeping the entry points separate prevents the AlphaFold experiment from
altering oncology candidate scores and prevents the general prediction schema
from erasing structural quarantine states.

## Interpretation

- `CONSISTENT` means all assessable requested checks pass the provisional
  thresholds.
- `INCONSISTENT` means at least one adequately supported transformation fails
  a threshold.
- `QUARANTINE` means the family lacks evidence needed for a requested check.

Inconsistency can reflect a prediction error, a genuine alternative
conformation, an incorrect homology/domain mapping or an unsuitable
experimental comparison. It is a review target, not an automatic rejection of
the AlphaFold model.
