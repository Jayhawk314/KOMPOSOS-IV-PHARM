# KOMPOSOS-IV CHEM-TB Molecular Engine: Implementation Reference

## Executive Summary

This document describes the Category M Molecular Engine implemented in the `KOMPOSOS-IV-CHEM-TB` repository. The engine is a prototype molecular-design and triage system that connects 3D protein structures, categorical fragment assembly, medicinal-chemistry heuristics, PHARM-style binding priors, and benchmark reporting.

The system is designed to answer this early-stage research question:

> Given a protein structure and a disease/target context, can we generate chemically plausible fragment-based candidate molecules, explain why they were generated, and rank them well enough to decide what should move into docking, MD, or experimental validation?

It does not claim to prove binding. It currently provides triage and hypothesis-generation evidence. Binding proof still requires retrospective co-crystal benchmarks, active/decoy enrichment tests, docking or MD validation, and eventually wet-lab assays.

## Files Added Or Modified

### Core Molecular Engine

- `scripts/design_drug.py`
  - Main Category M molecular design CLI.
  - Parses PDB structures.
  - Detects or accepts a binding pocket.
  - Builds a fragment category.
  - Assembles fragments via morphisms.
  - Rejects bad assemblies by steric and pocket constraints.
  - Scores candidates.
  - Emits JSON and CSV reports.

### Integrated PHARM/Oracle Wrapper

- `scripts/design_drug_integrated.py`
  - Runs the molecular design engine.
  - Converts generated molecules into Track A/PHARM/Oracle evidence.
  - Emits raw design output and integrated handoff output.

### Benchmark Harness

- `scripts/benchmark_molecular_engine.py`
  - Runs the engine across one or more local PDB structures.
  - Reports candidate yield, runtime, rejection counts, score spread, pocket metadata, and ligand-pose proxy metrics when bound ligands exist.

### Evidence Adapters

- `molecular_bridge/design_evidence_adapter.py`
  - Converts generated candidates into integrated molecular evidence.
  - Produces Oracle-style prediction payloads.
  - Produces categorical store object/morphism payloads.
  - Produces PHARM handoff payloads.

- `molecular_bridge/pharm_binding_adapter.py`
  - Adds PHARM-style binding priors for generated candidates.
  - Uses known target properties, domain class, reference drugs, functional-group analogy, logP matching, and H-bond complementarity.

### Tests

- `tests/design_drug_test.py`
  - Verifies that the molecular engine generates candidates and writes CLI JSON.

- `tests/design_evidence_adapter_test.py`
  - Verifies PHARM/Oracle/store handoff payloads.

- `tests/benchmark_molecular_engine_test.py`
  - Verifies benchmark output, triage grades, and ligand-pose proxy reporting.

- `tests/pharm_binding_adapter_test.py`
  - Verifies PHARM binding priors for known and unknown targets.

### Planning And Reports

- `plans/MOLECULAR_ENGINE_PLAN.md`
  - Original implementation plan and architecture decision.

- `reports/molecular_engine_benchmark_local.json`
  - Local benchmark snapshot on four available structures.

- `reports/molecular_engine_benchmark_egfr_pharm.json`
  - EGFR-focused benchmark snapshot with PHARM binding priors enabled.

### Git Ignore Adjustment

- `.gitignore`
  - Updated to allow tracking the new files under the otherwise ignored `molecular_bridge/` directory.

## Core Architectural Model

The implementation follows the Category M philosophy:

- Chemical fragments are objects.
- Attachments and spatial transforms are morphisms.
- A candidate ligand is a colimit-like assembly of fragments.
- The receptor pocket acts as a functorial constraint environment.
- Integrated evaluation maps Category M evidence into Track A/PHARM/Oracle evidence.

The current system is not a statistical ML model. It is a structured search and scoring system with categorical provenance. This means every candidate can carry a trace:

- Which seed object was placed.
- Which pocket site it aligned to.
- Which morphisms attached additional fragments.
- Which filters accepted or rejected the branch.
- Which scoring terms produced the final rank.

## Pipeline Overview

The main pipeline is:

1. Read a PDB file.
2. Extract protein atoms and optional bound ligand atoms.
3. Define a pocket.
4. Build interaction sites inside the pocket.
5. Build a molecular fragment category.
6. Place seed fragments.
7. Expand assemblies by applying fragment morphisms.
8. Reject invalid assemblies.
9. Score surviving assemblies.
10. Convert top assemblies to candidate records.
11. Optionally integrate with PHARM binding priors.
12. Emit machine-readable reports.

## PDB Parsing

The parser lives in `scripts/design_drug.py`.

It reads:

- `ATOM` records as protein atoms.
- `HETATM` records as bound ligand atoms unless they are water.
- Chain IDs.
- Residue names.
- Residue IDs.
- Atom names.
- Elements.
- 3D coordinates.
- Approximate residue/atom charges.

Water residues are ignored:

- `HOH`
- `WAT`
- `DOD`
- `H2O`

Protein atom charges are approximate, not force-field charges. Examples:

- Lysine `NZ`: positive.
- Arginine terminal nitrogens: positive.
- Histidine nitrogens: weak positive.
- Aspartate oxygens: negative.
- Glutamate oxygens: negative.
- Generic oxygen: weak negative.
- Generic nitrogen: weak positive.

This is sufficient for triage scoring, but not for production binding-energy calculation.

## Pocket Definition

The engine supports multiple pocket-definition modes.

### Explicit Center

The user can provide:

```powershell
--center x,y,z
```

This is the most controlled mode when a researcher knows the active-site location.

### Residue-Centered Pocket

The user can provide:

```powershell
--residue A:123
```

or:

```powershell
--residue 123
```

The engine centers the pocket on that residue's atoms.

### Bound-Ligand Pocket

If non-water `HETATM` ligand atoms exist, the engine can use the ligand centroid as the pocket center.

This is useful for co-crystal benchmarking because the known ligand defines the ground-truth pocket.

### Grid Cavity And Hotspot Detection

The current default is grid cavity detection when no explicit center is supplied.

The grid method (largest-connected-cavity, validated 2026-05-29):

1. Builds a bounding grid around protein atoms.
2. Keeps void points that sit inside the protein envelope: a real clearance
   (3.0-5.5 Angstrom) from the nearest atom and at least 12 atoms within 9 Angstrom.
3. Keeps the concave subset by ray-cast buriedness (64 probe directions,
   buriedness >= 0.78), which selects pocket-like points over surface bumps.
4. Groups the kept points into connected cavities (linked if within 3.2 Angstrom).
5. Returns the centroid of the LARGEST cavity as the pocket center.

The drug-binding pocket is empirically the largest contiguous concave cavity.

History and validation: an earlier version maximised single-point buriedness,
which walked into the fully enclosed protein core (~22 Angstrom from the ligand) and
was WORSE than the protein-centroid fallback. The current largest-cavity method
was validated against co-crystals (`scripts/benchmark_pocket_recovery.py`):

- Training set (10 co-crystals): median pocket-center error 5.6 Angstrom, contact
  recall 0.70, beating the centroid baseline (11.9 Angstrom, 0.43) by 6.3 Angstrom.
- Held-out set (10 new co-crystals, 9 new target families, frozen thresholds):
  median 5.4 Angstrom, recall 0.81, beating centroid (12.2 Angstrom, 0.48) on 10/10.

The protein-centroid fallback still exists as a last resort but should not be
used for serious evaluation. For targets where the binding site is not the
largest cavity (some allosteric/shallow/channel-like sites, e.g. BRAF and COX-2
in the benchmark), supply the pocket via `--center` or `--residue`.

## Pocket Interaction Sites

Once the pocket atoms are selected, the engine annotates sites:

- `positive`
- `negative`
- `donor`
- `acceptor`
- `hydrophobic`
- `center`

These sites guide seed placement and scoring.

Examples:

- A positive lysine/arginine site favors negatively charged or acceptor-rich fragments.
- A donor protein site favors ligand acceptors.
- An acceptor protein site favors ligand donors.
- A hydrophobic site favors aromatic/carbon-rich fragments.

## Fragment Category

Fragments are represented as `MolecularFragment` objects.

Each fragment contains:

- Name.
- Atoms.
- Bonds.
- Connection points.
- Role.

Fragment roles:

- `seed`
  - Used as an initial placed object in the pocket.

- `linker`
  - Used to connect and extend assemblies.

- `cap`
  - Used to terminate or functionalize an assembly.

## Current Fragment Library

The current library includes:

### Aromatic And Heteroaromatic Seeds

- `benzene`
- `pyridine`
- `imidazole`
- `pyrimidine`
- `aminopyrimidine`
- `pyrazine`
- `pyrazole`

These are important for kinase-like pockets and many oncology targets because heteroaromatics often participate in hinge-binding and polar interactions.

### Linkers

- `methylene`
- `ethylene`
- `ether`
- `carbonyl`
- `amide`
- `urea`
- `sulfonamide`

These allow the engine to explore spatial extension and donor/acceptor placement.

### Caps And Functional Groups

- `amine`
- `hydroxyl`
- `carboxylate`
- `methyl`
- `nitrile`
- `fluoro`

These improve medicinal-chemistry diversity and support target-class priors.

## RDKit Integration

RDKit is available in the local environment and is now used optionally.

### ETKDG Fragment Conformers

The engine can replace toy coordinates with deterministic RDKit ETKDG/UFF-generated coordinates for fragments.

This improves 3D realism for:

- Ring geometry.
- Linker geometry.
- Heteroatom placement.
- Approximate relaxed fragment shape.

The feature can be disabled with:

```powershell
--no-rdkit-fragments
```

### UFF Relaxation Score

After assembly, the engine can generate an RDKit molecule from the fallback SMILES and run UFF relaxation to estimate whether the graph is chemically strained.

The term appears as:

```json
"rdkit_relaxation": ...
```

This feature can be disabled with:

```powershell
--no-rdkit-relax
```

Current limitation: this relaxation score is based on the candidate SMILES graph, not the exact assembled pose coordinates in the protein pocket. It is a chemical sanity term, not a docking score.

## Assembly Search

The engine uses beam search.

Default controls:

- `--beam-width`
- `--max-fragments`
- `--max-candidates`
- `--max-atoms`

Assembly process:

1. Seed fragments are placed near compatible pocket sites.
2. Candidate rotations are tried.
3. Seed placements are filtered.
4. Open connection points are expanded with linker or cap fragments.
5. New fragments are placed using alignment of source and target connection directions.
6. The assembly is validated.
7. The best assemblies stay in the beam.

Each accepted assembly preserves a categorical trace:

- Seed placement morphism.
- Fragment attachment morphisms.
- Source and target connection labels.
- Object names.

## Rejection Filters

The engine tracks rejection counts:

- `protein_clash`
- `self_clash`
- `pocket_escape`
- `max_atoms`
- `incompatible_bond`
- `duplicate`

The local benchmark showed that `protein_clash` is the dominant rejection mode. This means the main geometry bottleneck is still placement near pocket atoms and steric margins.

## Scoring Terms

Raw candidate scoring includes:

- `steric_fit`
  - Rewards distance margins from protein atoms.

- `electrostatics`
  - Rewards opposite-charge proximity and penalizes same-charge proximity.

- `hydrogen_bonds`
  - Rewards donor/acceptor complementarity at plausible distances.

- `hydrophobic`
  - Rewards hydrophobic ligand atoms near hydrophobic pocket sites.

- `shape_fit`
  - Rewards pocket filling around an expected radial shell.

- `synthetic_sanity`
  - Rewards reasonable atom count, heteroatom balance, and capped assemblies.

- `rdkit_relaxation`
  - Rewards low UFF strain in the generated chemical graph.

- `categorical_colimit`
  - Rewards categorical assembly completeness and morphism structure.

The raw total score is the sum of these terms.

## Candidate Output

Each raw candidate includes:

- `candidate_id`
- `score_total`
- `score_terms`
- `smiles`
- `smiles_validated`
- `fragment_trace`
- `fragments`
- `morphism_count`
- `atom_count`
- `formula`
- `molecular_weight`
- `pocket_residues`
- `coordinates`

The coordinates are generated candidate atom coordinates in the chosen pocket frame.

## SMILES Generation

SMILES generation is currently hybrid:

- Deterministic fallback strings from fragment names.
- Optional RDKit canonicalization if RDKit accepts the generated SMILES.

This is sufficient for triage, but not final chemistry. A production system should use a proper graph object throughout assembly and generate the SMILES directly from the molecular graph.

## Integrated Evidence Layer

The integrated layer converts raw candidate records into richer evidence.

The adapter is `molecular_bridge/design_evidence_adapter.py`.

It produces:

- Candidate molecular evidence.
- Property estimates.
- Math evidence.
- PHARM binding evidence.
- Integrated score terms.
- Oracle prediction payload.
- Categorical store payload.
- PHARM handoff payload.

## Property Estimates

The adapter estimates:

- H-bond donors.
- H-bond acceptors.
- logP proxy.
- Rotatable bond proxy.
- Aromatic ring proxy.
- Lipinski violation count.
- Functional groups.

These estimates are based on fragments and fallback SMILES features. They are not a replacement for RDKit descriptors or curated cheminformatics pipelines.

## Math Evidence

The adapter uses `geometry/spectral_structures.py` to evaluate the fragment graph.

It computes:

- Whether the fragment graph is connected.
- Algebraic connectivity.
- Spectral gap.
- Pharmacophore diversity from pocket site counts.
- Categorical trace length.

This is not a binding calculation. It is a coherence/structure signal: does the candidate have a connected, interpretable fragment-colimit structure and does it engage diverse pocket opportunities?

## PHARM Binding Prior

The PHARM prior adapter is `molecular_bridge/pharm_binding_adapter.py`.

It uses:

- PHARM drug-property table.
- Known target properties.
- Target domain class.
- Known reference drugs for target families.
- Functional-group similarity to known drugs.
- Candidate logP and H-bond complementarity to target pocket priors.

Examples:

- For `EGFR`, the adapter compares candidate motifs to known EGFR/ERBB inhibitor chemistry such as quinazoline/heteroaromatic/amine/amide patterns.
- For kinase targets, it rewards heteroaromatics, amines, amides, ureas, pyrimidines, pyrazines, pyrazoles, and related hinge-binding motifs.
- For COX-like targets, it rewards carboxylate/sulfonamide/aromatic groups.

Important limitation:

The PHARM prior is not experimental binding evidence for a generated molecule. It is a target-class and known-drug analogy prior. It answers:

> Does this generated molecule resemble chemistry that has worked for this target class?

It does not answer:

> Does this exact molecule bind this exact protein pocket?

## Integrated Score Terms

The integrated score fuses:

- `binding_proxy`
- `molecular_sanity`
- `categorical_coherence`
- `math_verification`
- `pharm_binding_prior`
- `track_a_context`

The current weights are heuristic and should be benchmark-tuned.

The output includes:

- `integrated_score`
- `confidence`
- `verdict`

Example verdicts:

- `prioritize_for_docking_or_md`
- `review_with_additional_filters`
- `low_priority_hypothesis`
- `deprioritize`

## Oracle Prediction Payload

Each integrated candidate includes an `oracle_prediction` field:

- `source`
  - Candidate ID.

- `target`
  - Track A target ID.

- `predicted_relation`
  - `candidate_binds_target`

- `prediction_type`
  - `ensemble`

- `strategy_name`
  - `category_m_integrated_design`

- `confidence`
  - Current integrated confidence.

- `reasoning`
  - Human-readable explanation.

- `evidence`
  - Integrated score terms and candidate metadata.

This is JSON-safe and does not require importing Oracle internals.

## Categorical Store Payload

Each candidate includes a `categorical_store` payload:

- Object:
  - Name: candidate ID.
  - Type: `DesignedMolecule`.
  - Metadata: SMILES, formula, MW, fragments, source.

- Morphism:
  - Name: `designed_binding_hypothesis`.
  - Source: candidate ID.
  - Target: target ID.
  - Confidence: integrated confidence.
  - Metadata: integrated score, verdict, mechanism, disease context.

This allows later import into KOMPOSOS category/runtime layers.

## PHARM Handoff Payload

Each candidate includes a `pharm_handoff` payload:

- `target_id`
- `protein_id`
- `disease_context`
- `candidate_smiles`
- `binding_score`
- `binding_confidence`
- `pharm_binding_prior`
- `mechanism_hypothesis`
- `verdict`

This is the main boundary object Track A can consume.

## CLI Usage

### Raw Design

```powershell
python scripts/design_drug.py --pdb target.pdb --center 0,0,0 --radius 8 --max-candidates 25
```

### Grid Pocket Detection

```powershell
python scripts/design_drug.py --pdb target.pdb --pocket-mode grid --radius 10
```

### Residue-Guided Pocket

```powershell
python scripts/design_drug.py --pdb target.pdb --residue A:797 --radius 10
```

### Integrated PHARM/Oracle Output

```powershell
python scripts/design_drug_integrated.py `
  --pdb data\proteins\structures\AF-P00533-F1-model_v6.pdb `
  --target-id EGFR `
  --protein-id P00533 `
  --disease-context lung_cancer `
  --radius 10
```

### Disable PHARM Prior

```powershell
python scripts/design_drug_integrated.py --pdb target.pdb --target-id EGFR --no-pharm-binding-prior
```

### Disable RDKit Fragment Coordinates

```powershell
python scripts/design_drug.py --pdb target.pdb --no-rdkit-fragments
```

### Disable RDKit Relaxation

```powershell
python scripts/design_drug.py --pdb target.pdb --no-rdkit-relax
```

### Benchmark Multiple Structures

```powershell
python scripts/benchmark_molecular_engine.py `
  --pdb data\cache\pdb_templates\1erj.pdb `
  --pdb data\proteins\structures\AF-P00533-F1-model_v6.pdb `
  --radius 10 `
  --beam-width 8 `
  --max-fragments 2 `
  --max-candidates 5 `
  --out reports\molecular_engine_benchmark_local.json
```

### EGFR Benchmark With PHARM Prior

```powershell
python scripts/benchmark_molecular_engine.py `
  --pdb data\proteins\structures\AF-P00533-F1-model_v6.pdb `
  --target-id EGFR `
  --protein-id P00533 `
  --disease-context lung_cancer `
  --radius 10 `
  --beam-width 8 `
  --max-fragments 2 `
  --max-candidates 5 `
  --out reports\molecular_engine_benchmark_egfr_pharm.json
```

## Local Benchmark Snapshot

The current local benchmark used four structures:

- `data/cache/pdb_templates/1erj.pdb`
- `data/proteins/structures/AF-P00533-F1-model_v6.pdb`
- `data/proteins/structures/AF-P01116-F1-model_v6.pdb`
- `data/proteins/structures/AF-Q07812-F1-model_v6.pdb`

With grid pocket detection, RDKit fragments, RDKit relaxation, and expanded fragments:

- Structures tested: 4.
- Structures OK: 4.
- Structures with candidates: 4.
- Candidate yield rate: 100%.
- Median runtime: about 15.6 seconds.
- Median top integrated score: about 0.687.
- Triage grades: 3 A, 1 B.

Interpretation:

- This is promising for triage.
- It shows the system can generate candidate hypotheses across structures.
- It does not prove binding because the local benchmark did not include useful bound ligand ground truth.

## EGFR PHARM Prior Snapshot

For `AF-P00533-F1-model_v6.pdb` with `target-id EGFR`:

- Top candidate: `Oc1cnccn1`.
- Integrated score: about 0.6797.
- PHARM binding prior: about 0.6263.
- Triage grade: A.

Interpretation:

- The candidate is ranked as follow-up-worthy by structural and PHARM prior terms.
- This is still not binding proof.
- The correct next validation layer is docking/MD and known-ligand benchmark comparison.

## Current Research Usefulness

The system is useful for:

- Early triage.
- Prioritizing pockets for follow-up.
- Generating fragment hypotheses.
- Producing explainable candidate rationales.
- Connecting Track A disease/target evidence to Track B molecular design.
- Reducing manual ideation burden.

It is not yet suitable for:

- Claiming exact binding.
- Predicting affinity values.
- Replacing docking.
- Replacing medicinal chemistry review.
- Replacing synthesis or assay validation.
- Making clinical or investment-grade claims about specific molecules.

## Expected Time Savings

Current realistic time savings are in early triage:

- Manual target-to-pocket inspection may take hours to days per target.
- The engine can produce structured hypotheses in seconds to minutes per structure.
- It may reduce the number of obviously weak starting ideas that need docking or expert review.

Reasonable current claim:

> The system can compress early ideation and triage from days to minutes for a target, provided its outputs are treated as hypotheses and passed into real validation.

Unreasonable current claim:

> The system proves a candidate binds or is a drug lead.

The system will save more time after benchmark calibration because researchers will know which score thresholds are meaningful.

## Known Limitations

### Binding Accuracy Is Not Proven

The engine has no retrospective active/decoy benchmark yet. It does not know whether it ranks true binders above matched decoys.

### Pocket Detection Is Now Co-Crystal Calibrated, But Not Universal

Grid (largest-cavity) pocket detection has been validated against co-crystals
(median ~5.5 Angstrom center error on both a training and a held-out set, beating the
centroid baseline). It still fails when the binding site is not the largest
cavity (allosteric/shallow/channel-like sites). For those, supply the pocket via
`--center`/`--residue`. Pose- and contact-level accuracy beyond pocket center
still needs docking/MD validation.

### Fragment Library Is Still Small

The current fragments are better than toy chemistry, but not yet broad enough for medicinal chemistry campaigns.

### Pose Generation Is Approximate

The categorical assembly pose is not a docked pose. The RDKit relaxation term is molecular graph sanity, not protein-ligand pose minimization.

### SMILES Generation Is Not Fully Graph-Native

Fallback SMILES are deterministic but simplified. Full graph-native assembly should replace this.

### PHARM Binding Prior Is Not Experimental Evidence

The PHARM prior provides target/domain analogy, not molecule-specific assay data.

### Scores Are Heuristic

Score weights need benchmark tuning.

## Validation Status

Implemented tests pass:

```powershell
pytest tests\design_drug_test.py tests\design_evidence_adapter_test.py tests\benchmark_molecular_engine_test.py tests\pharm_binding_adapter_test.py -q
```

The tests validate software behavior:

- Candidate generation.
- CLI JSON writing.
- Integrated report generation.
- Benchmark reporting.
- PHARM binding-prior scoring.

They do not validate biological binding.

## What A Researcher Should Do With Current Outputs

Use the outputs to answer:

- Which candidate fragments are worth docking first?
- Which target context makes the most sense?
- Which pocket residues are being used?
- Which scoring terms support the candidate?
- Does the candidate resemble known chemistry for this target class?
- Does the candidate fail obvious geometry or drug-likeness checks?

Do not use the outputs to answer:

- What is the exact binding affinity?
- Will this molecule bind experimentally?
- Is this molecule safe?
- Is this molecule synthesizable as written?
- Is this a lead compound?

## Recommended Operating Procedure

1. Choose a protein target from PHARM Track A.
2. Use a known PDB/co-crystal structure if available.
3. If only AlphaFold is available, provide active-site residues manually when possible.
4. Run `scripts/design_drug_integrated.py`.
5. Inspect top candidates and rejection counts.
6. Prefer candidates with:
   - PHARM binding prior support.
   - Strong H-bond/electrostatic/hydrophobic terms.
   - RDKit relaxation support.
   - Low clash-dominated failure modes.
   - Clear categorical trace.
7. Dock top candidates.
8. Compare docked contacts with known target pharmacophore.
9. Run MD or Boltz-style validation.
10. Only then consider experimental validation.

## Summary

We built a working Category M molecular-design prototype that:

- Reads protein structures.
- Detects pockets.
- Generates fragment-based candidate molecules.
- Scores candidates structurally and chemically.
- Uses RDKit for better 3D fragment geometry and relaxation sanity.
- Integrates PHARM target/domain binding priors.
- Emits Track A/Oracle/category handoff artifacts.
- Benchmarks local triage yield.

The system is now useful as a research triage engine. The next major task is proving enrichment and pose recovery against known co-crystal and active/decoy benchmarks.

