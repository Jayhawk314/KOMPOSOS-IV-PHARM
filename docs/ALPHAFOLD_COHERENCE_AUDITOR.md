# AlphaFold Structural-Coherence Auditor

## Purpose

`geometry/alphafold_coherence.py` audits a related family of predicted and
experimental protein structures. It asks whether their domain arrangements and
structural alignments are mutually coherent.

It does **not** predict protein structures, reconstruct missing residues,
estimate thermodynamic stability, or infer a folding pathway. It also does not
declare that an inconsistent AlphaFold prediction is wrong. A genuine
alternative conformation can produce the same signal and must be investigated.

This module replaces the old structural code's qualitative category-theory
claims with two explicit measurements:

1. **Domain-arrangement defect.** Fit a rigid transformation on one domain and
   apply it to a second domain. Measure how far the second domain lies from its
   observed counterpart. A separate fit on the second domain distinguishes
   internal fold disagreement from relative domain-pose disagreement.
2. **Compositional horn defect.** For three structures A, B and C, fit A-to-B,
   B-to-C and A-to-C transformations on the same domain. Compose A-to-B-to-C
   and compare it with directly observed A-to-C. This is the concrete
   horn-filling test.

Kabsch alignment supplies the measured rigid morphisms. Category theory
supplies the composition and coherence question; it is not itself presented as
biological evidence.

## Inputs

The CLI accepts a versioned JSON manifest. Domain coordinates are one-based,
inclusive positions on the selected reference model's sequence.

```json
{
  "schema_version": 1,
  "family_id": "example-protein-family",
  "reference_model": "AF_HUMAN",
  "models": [
    {
      "model_id": "AF_HUMAN",
      "kind": "prediction",
      "path": "structures/AF-P12345-F1-model_v6.cif",
      "chain": "A",
      "pae_path": "structures/AF-P12345-F1-predicted_aligned_error_v6.json"
    },
    {
      "model_id": "AF_MOUSE",
      "kind": "prediction",
      "path": "structures/AF-Q12345-F1-model_v6.cif",
      "chain": "A",
      "pae_path": "structures/AF-Q12345-F1-predicted_aligned_error_v6.json"
    },
    {
      "model_id": "PDB_EXPERIMENT",
      "kind": "experimental",
      "path": "structures/8XYZ.cif",
      "chain": "B"
    }
  ],
  "domains": [
    {"domain_id": "D1", "start": 20, "end": 145},
    {"domain_id": "D2", "start": 162, "end": 310}
  ],
  "config": {
    "minimum_residues": 8,
    "minimum_domain_coverage": 0.6,
    "minimum_plddt": 50.0,
    "maximum_assessable_pae": 15.0,
    "arrangement_rmsd_threshold": 5.0,
    "arrangement_rotation_threshold_deg": 20.0,
    "composition_rmsd_threshold": 2.0,
    "composition_rotation_threshold_deg": 10.0,
    "require_pae_for_predictions": true,
    "quarantine_on_any_missing_check": true
  }
}
```

Paths are resolved relative to the manifest. PDB and mmCIF coordinate files
are supported. Current matrix-style AlphaFold PAE JSON and the older
`residue1`/`residue2`/`distance` representation are supported.

Only a single chain is audited at a time. If a coordinate file contains more
than one chain, `chain` is required. Reference and comparison sequences are
globally aligned; missing residues and insertions are permitted subject to the
configured coverage threshold.

Run it from the repository root:

```powershell
python geometry/alphafold_coherence.py path/to/manifest.json --output report.json
```

Omit `--output` to print JSON to standard output.

## Report standing

- `CONSISTENT`: every assessable relation passed the current thresholds.
- `INCONSISTENT`: at least one adequately supported relation exceeded a
  configured review threshold.
- `QUARANTINE`: evidence needed for a requested check was missing, degraded or
  too uncertain. By default, any quarantined subcheck quarantines the family
  result.

Predicted models require PAE by default. High cross-domain PAE quarantines a
domain-arrangement conclusion because AlphaFold itself reports that the
relative placement is uncertain. Low PAE allows the geometric check to be
assessed, but does not make the structure experimentally true.

Important report fields include:

- `arrangement_rmsd`: mobile-domain RMSD after alignment on the anchor domain.
- `mobile_internal_rmsd`: best RMSD when the mobile domain is independently
  aligned.
- `excess_arrangement_rmsd`: pose disagreement after removing the mobile
  domain's internal fitting error in quadrature.
- `rotation_disagreement_deg`: angle between independently fitted domain poses.
- `centroid_displacement`: translation disagreement for the mobile domain.
- `filler_rmsd`: disagreement between composed and directly fitted maps on the
  source coordinates.

## Threshold status

The default thresholds are explicit starting hypotheses. They have not yet
been calibrated as biological decision boundaries. They must be compared with
experimental structures before the auditor is used to prioritize laboratory
work.

A useful validation cohort should contain multi-domain protein families with:

- AlphaFold models and PAE matrices;
- experimentally determined structures excluded from morphism construction
  until evaluation;
- known domain-orientation or interface disagreements;
- plausible alternative conformations, labelled separately from prediction
  errors.

The primary comparison should test whether the coherence measurements predict
experimental domain-orientation error beyond pLDDT, PAE, sequence identity and
an ordinary pairwise structural-alignment baseline. If they do not add signal,
the category-theoretic formulation should not be scaled to the full AlphaFold
database.

## Reproducible public-data cohort

The cohort builder acquires current AlphaFold DB models and PAE, InterPro domain
annotations, PDBe experimental mappings, SIFTS observed-residue ranges and RCSB
mmCIF coordinates. Downloads are cached and checksummed so an interrupted run
can resume without silently changing its inputs.

```powershell
python validation/build_alphafold_coherence_cohort.py --max-experimental 3
```

The default accession set is the 34 cancer-related proteins inherited from the
older KOMPOSOS structural workspace. A domain pair is eligible only when at
least two experimental structures contain sufficient *observed* coordinates
for both domains. SEQRES or construct-level coverage is not treated as observed
structure.

The dated result and its interpretation are in
`reports/alphafold_coherence_2026-08-12/README.md`. This is a feasibility cohort,
not a calibrated benchmark: it contains technical synthetic controls but does
not yet contain a literature-curated set of known AlphaFold domain-orientation
errors.

## Why this is separate from the old interpreter

The legacy `alphafold_interpreter.py` contains unimplemented or hardcoded TDA,
Nash and curvature interpretations. This auditor neither imports nor reports
those values. It is a separate experimental capability with inspectable inputs,
numeric outputs, uncertainty handling and falsifiable tests.
