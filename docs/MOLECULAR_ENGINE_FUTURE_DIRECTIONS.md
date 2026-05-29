# KOMPOSOS-IV CHEM-TB Molecular Engine: Future Directions And Validation Roadmap

## Executive Summary

The Molecular Engine now functions as an integrated triage prototype. It can generate candidate molecules, score them against protein pockets, integrate PHARM target priors, and report benchmark-style metrics.

The central question for the next phase is no longer:

> Can the system run?

It is:

> Does the system enrich for real binders and recover real binding-site geometry better than simple baselines?

This document lays out the roadmap to move from prototype triage toward scientifically defensible molecular-design evidence.

## Current Status

The current system can:

- Parse local PDB structures.
- Detect pockets using grid cavity and hotspot scoring.
- Assemble fragments categorically.
- Use RDKit ETKDG conformers for fragment geometries.
- Score sterics, electrostatics, H-bonds, hydrophobic complementarity, shape fit, synthetic sanity, RDKit relaxation, and categorical coherence.
- Integrate PHARM binding priors.
- Emit Oracle-style and PHARM-style handoff payloads.
- Run local benchmark reports.

The current system cannot yet:

- Prove binding.
- Predict quantitative affinity.
- Guarantee correct pose.
- Rank actives above decoys with measured enrichment.
- Replace docking or MD.
- Replace wet-lab validation.

## Strategic Goal

The target state is a layered validation system:

1. Category M generates explainable molecular candidates.
2. PHARM Track A provides target/disease/known-drug priors.
3. Known co-crystal benchmarks prove whether pocket and pose recovery are meaningful.
4. Active/decoy benchmarks prove whether ranking is enriched.
5. Docking/MD/Boltz-style systems provide stronger 3D validation.
6. Prospective experiments test whether the system saves real researcher time.

The practical goal is not to replace drug discovery. The practical goal is to compress early triage and improve decision quality before expensive validation steps.

## What "Good" Means

For this system, "good" should be defined operationally.

### Bad Definition

> The model says this molecule binds.

This is not enough.

### Better Definition

> On retrospective benchmark targets, the system recovers known binding pockets, places plausible pharmacophore fragments near known ligand interaction zones, ranks known actives above decoys, and produces fewer false-positive follow-up candidates than baseline methods.

This can be measured.

## Time Savings Model

The system saves time only if it reduces low-value manual work or expensive downstream computation.

### Current Time Savings

Current version likely saves time in:

- Target-to-pocket ideation.
- Fragment hypothesis generation.
- First-pass candidate ranking.
- Explaining why a candidate was produced.
- Rejecting obvious geometry failures.

Current rough time impact:

- Manual early target/pocket ideation: hours to days per target.
- Current engine: seconds to minutes per target.
- Practical savings: potentially 50-80% of early ideation and manual triage time.

This is not yet proven across real targets.

### What Must Be Proven

We need evidence that the system saves time without simply producing confident false positives.

Useful productivity metrics:

- Time to first plausible hypothesis.
- Number of candidates sent to docking.
- Fraction of candidates rejected by expert review.
- Fraction of docking jobs wasted on impossible poses.
- Fraction of top candidates matching known pharmacophores.
- Retrospective enrichment over random fragment generation.

## Validation Ladder

The correct validation ladder has five levels.

### Level 1: Software Correctness

Question:

> Does the pipeline run and produce structured outputs?

Current status:

- Yes.

Evidence:

- Unit tests pass.
- Benchmark harness runs.
- JSON/CSV outputs are generated.

Limit:

- This says nothing about binding accuracy.

### Level 2: Pocket Recovery

Question:

> Does the pocket detector find the real binding pocket?

Required data:

- Co-crystal PDBs with known ligands.

Metrics:

- Predicted pocket center to ligand centroid distance.
- Fraction of predictions within 4 Angstrom.
- Fraction within 6 Angstrom.
- Pocket residue overlap with known ligand-contact residues.
- Grid cavity rank of known ligand pocket.

Success criteria:

- Median centroid error below 4-6 Angstrom on benchmark set.
- Strong enrichment over protein-centroid baseline.

### Level 3: Pharmacophore/Contact Recovery

Question:

> Do generated fragments recover the correct interaction pattern?

Metrics:

- Hinge residue contact recovery for kinases.
- H-bond donor/acceptor match to known ligand interactions.
- Hydrophobic pocket occupancy.
- Salt bridge/polar contact recovery.
- Contact precision and recall against known ligand contacts.

Success criteria:

- Top candidates recover a useful fraction of known ligand-contact residues.
- Contact recovery is better than random fragments placed in the pocket.

### Level 4: Active/Decoy Enrichment

Question:

> Does the ranking put real binders above non-binders?

Required data:

- Known actives.
- Matched decoys.
- Same target context.

Metrics:

- AUROC.
- AUPRC.
- Enrichment factor at top 1%, 5%, 10%.
- BEDROC if early recognition is important.
- Top-k hit rate.

Success criteria:

- Meaningful enrichment over random ranking and simple property baselines.
- Stable performance across targets, not one cherry-picked case.

### Level 5: Prospective Validation

Question:

> Can the system nominate candidates before seeing results?

Required process:

1. Freeze the engine.
2. Choose targets.
3. Generate candidates.
4. Run docking/MD and expert review.
5. Select a small prospective set.
6. Assay experimentally.

Metrics:

- Hit rate.
- Time saved.
- Cost per validated hit.
- Novelty of candidates.
- Expert acceptance rate.

Success criteria:

- The system improves hit rate or reduces cost/time compared with a reasonable baseline workflow.

## Co-Crystal Benchmark Plan

The next most important deliverable is a co-crystal benchmark set.

### Target Families

Start with target families where PHARM already has priors:

- EGFR.
- BRAF.
- ALK.
- MET.
- RET.
- ROS1.
- CDK4.
- CDK6.
- JAK2.
- MEK1/MAP2K1.
- MTOR.
- COX2.
- BCL2.
- KRAS/GTPase if structures are available.

### Benchmark Inputs

For each target:

- PDB ID.
- Protein chain.
- Ligand residue name.
- Ligand SMILES if available.
- Known active drug name if applicable.
- Active-site residue annotations.
- Disease context.
- Target ID.
- Protein ID.

### Benchmark Outputs

For each structure:

- Pocket mode.
- Predicted pocket center.
- Known ligand centroid.
- Centroid distance.
- Known ligand-contact residues.
- Candidate-contact residues.
- Contact precision.
- Contact recall.
- Top candidate SMILES.
- Top candidate score.
- PHARM prior.
- Docking score if available later.
- Verdict.

### Minimum Viable Benchmark

A useful first benchmark can be small:

- 5 targets.
- 2-3 co-crystal structures per target.
- 10-15 total structures.

This is enough to expose obvious failure modes.

### Better Benchmark

A stronger benchmark:

- 20 targets.
- 5 structures per target.
- 100 structures.
- Known actives and decoys for each target.

This is enough to tune weights and estimate generalization.

## Known-Ligand Pose Recovery

The benchmark should not only ask whether the engine produces candidates. It should ask whether the generated candidate occupies the correct region.

Useful pose proxy metrics:

- Candidate centroid to ligand centroid distance.
- Candidate atom fraction within 2.5 Angstrom of known ligand atoms.
- Candidate atom fraction within 4.0 Angstrom of known ligand atoms.
- Known ligand contact residues recovered by candidate.
- Candidate contact residue precision.
- Candidate contact residue recall.
- H-bond donor/acceptor contact recovery.
- Aromatic/hydrophobic pocket overlap.

These are not docking RMSD, but they provide signal before full docking is implemented.

## Active/Decoy Benchmark Plan

Pocket recovery proves geometry. It does not prove ranking.

For ranking, use active/decoy tests.

### Data Sources

Potential sources:

- DUD-E style target/decoy sets.
- ChEMBL target activity data.
- BindingDB.
- PDBbind for structural complexes.
- Internal PHARM target/drug graph.

### Required Normalization

For each target:

- Map protein IDs to target names.
- Normalize drug names.
- Normalize SMILES.
- Remove duplicates.
- Separate actives from weak/inactive/unknown.
- Build property-matched decoys.

### Metrics

Use:

- AUROC.
- AUPRC.
- Enrichment factor at top 1%, 5%, 10%.
- Hit rate at top k.
- Calibration curves.

### Baselines

Compare against:

- Random ranking.
- Molecular weight/logP-only ranking.
- PHARM prior alone.
- Pocket score alone.
- RDKit descriptor similarity alone.
- Docking alone if available.

The system is useful only if the integrated score beats reasonable baselines.

## How PHARM Binding Evidence Should Be Used

PHARM evidence is valuable, but it must be used correctly.

### What PHARM Evidence Can Do

PHARM can:

- Identify disease-relevant targets.
- Identify known drug-target relationships.
- Identify domain families.
- Identify known functional groups for target classes.
- Provide repurposing priors.
- Penalize target contexts with weak disease evidence.
- Prioritize candidates that resemble known active chemistry.

### What PHARM Evidence Cannot Do

PHARM cannot prove:

- A generated molecule binds.
- A generated molecule has the correct pose.
- A generated molecule has acceptable ADMET.
- A generated molecule is synthesizable.
- A generated molecule is selective.

### Best Use

Use PHARM as a Bayesian prior:

> This target class has known chemistry, and this generated candidate shares relevant motifs.

Then combine it with:

- Pocket geometry.
- Contact recovery.
- Docking.
- MD.
- Experimental data.

## Proving Binding With A Similar System

A similar computational system can help prove binding only if it produces evidence at multiple levels.

### Computational Evidence

Useful computational evidence includes:

- Correct binding pocket recovery.
- Correct contact recovery.
- Docking pose with reasonable score.
- MD-stable pose.
- Water/protonation-aware interactions.
- Free-energy perturbation or MM/PBSA-style estimates.
- Agreement across independent methods.

But computational evidence alone is still not final proof.

### Experimental Evidence

Binding proof requires assays such as:

- SPR.
- ITC.
- DSF/thermal shift.
- Enzyme inhibition assay.
- Competition binding assay.
- Cellular target-engagement assay.
- ABPP where appropriate.
- Co-crystal or cryo-EM structure.

### Practical Proof Path

For each nominated molecule:

1. Generate candidate.
2. Dock against target pocket.
3. Run short MD stability check.
4. Compare contacts to known pharmacophore.
5. Check selectivity risks.
6. Check synthetic accessibility.
7. Purchase or synthesize.
8. Run biochemical binding assay.
9. Run orthogonal target-engagement assay.
10. If successful, attempt structural confirmation.

## Improving 3D Prediction

The strongest improvements are in 3D.

### Better Pocket Detection

Current grid/hotspot detection should be expanded to:

- Multi-pocket detection.
- Pocket ranking.
- Solvent exposure scoring.
- Concavity scoring.
- Druggability scoring.
- Conserved residue scoring.
- Known motif detection.
- Ligandability from homologous PDB structures.

### Pocket Graph Model

Represent the pocket as a graph:

- Atoms as nodes.
- Residue sites as supernodes.
- Spatial contacts as edges.
- Hotspot types as labels.

Use existing geometry/math modules:

- Spectral clustering to identify pocket subregions.
- Ricci curvature to identify bottlenecks and channels.
- Flow to smooth pocket regions.
- Topology to detect cavities and tunnels.

### Better Fragment Placement

Current placement is simple alignment.

Future placement should:

- Use pharmacophore triplets.
- Align multiple fragment points simultaneously.
- Use constrained conformer search.
- Rotate torsions during placement.
- Allow fragment bending and minimization.
- Penalize unsatisfied polar groups.
- Reward known motif contacts.

### Pose Relaxation

Needed:

- Local minimization of ligand pose in pocket.
- Protein-ligand steric relaxation.
- Side-chain rotamer adjustment.
- Optional water handling.
- Protonation-state selection.

Possible tools:

- RDKit UFF/MMFF for ligand.
- AutoDock Vina or similar docking.
- OpenMM for local minimization.
- GROMACS for MD if available.
- Boltz-style structural scoring if stable.

## Fragment Library Expansion

The current fragment library should become target-aware.

### Kinase Library

Add:

- Quinazoline.
- Indazole.
- Purine.
- Triazine.
- Pyrrolopyrimidine.
- Aminopyridine.
- Anilide.
- Hinge-binding donor/acceptor pairs.
- Solvent-front piperazine/morpholine groups.
- Urea/sulfonamide extended hinge motifs.

### Oncology General Library

Add:

- Indole.
- Benzimidazole.
- Oxazole.
- Thiazole.
- Isoxazole.
- Triazole.
- Morpholine.
- Piperazine.
- Piperidine.
- Cyclopropyl.
- Phenyl sulfone.
- Acrylamide warhead as optional covalent fragment.

### Safety

Covalent warheads should be opt-in only. They should never be generated silently as generic candidates.

## Graph-Native Molecular Assembly

The current fallback SMILES logic should be replaced by graph-native construction.

Needed:

- Atom graph object.
- Bond graph object.
- Valence validation.
- Aromaticity handling.
- Ring closure handling.
- Formal charge handling.
- RDKit molecule conversion.
- Canonical SMILES generation.
- SDF/MOL output.

This will improve:

- Chemical validity.
- Descriptor calculation.
- Docking preparation.
- Synthetic planning.

## Scoring Improvements

### Current Scoring Weakness

Current scoring is additive and heuristic.

Future scoring should be calibrated against benchmark data.

### Add Terms

Add:

- Unsatisfied polar penalty.
- Desolvation penalty.
- Ligand efficiency.
- Lipophilic ligand efficiency.
- Strain energy.
- Synthetic accessibility.
- PAINS/toxicophore filters.
- Selectivity risk.
- Covalent risk.
- ADMET proxy.

### Weight Calibration

Weights should be learned or tuned using:

- Known co-crystal structures.
- Active/decoy sets.
- Cross-validation by target family.
- Calibration plots.

Avoid overfitting by:

- Holding out target families.
- Holding out scaffolds.
- Reporting performance across target classes.

## Docking Integration

Docking is the most practical next validation layer.

### Minimal Docking Flow

1. Convert candidate SMILES to 3D ligand.
2. Prepare receptor pocket.
3. Dock candidate into predicted pocket.
4. Collect docking score and pose.
5. Compare docked pose to generated pose.
6. Compare docked contacts to known pharmacophore.

### Docking Metrics

- Docking score.
- Pose convergence.
- Contact recovery.
- H-bond recovery.
- Clash count.
- Ligand strain.
- Docked ligand efficiency.

### How To Use Docking

Docking should not replace the categorical engine. It should be a downstream verifier.

The categorical engine proposes.

Docking disposes.

PHARM contextualizes.

Oracle fuses.

## MD Integration

MD is more expensive and should be used after docking.

### Short MD Triage

Run:

- 1-5 ns quick stability simulations for top candidates.

Measure:

- Ligand RMSD.
- Contact persistence.
- H-bond persistence.
- Pocket stability.
- Water-mediated interactions.
- Energy drift.

### Longer MD

For serious candidates:

- 50-100 ns simulations.
- Replicates.
- MM/PBSA or related estimates.

### Existing Infrastructure

The repo contains `oracle/md_integration.py`, which is oriented toward GROMACS workflows. This should be connected after docking-ready ligand/receptor preparation exists.

## Boltz-Style Structural Scoring

The repo has Boltz-related bridge logic. This can become another independent validation source.

Use it for:

- Protein-ligand binding plausibility.
- Structural confidence.
- Cross-checking docking.

Do not use it as a single source of truth.

## Selectivity And Off-Target Risk

A candidate that binds one target may bind many similar targets.

Future work:

- Run candidates against target-family panels.
- Penalize broad kinase promiscuity unless desired.
- Compare target-pocket similarity across proteins.
- Use PHARM disease context to decide whether polypharmacology is useful or dangerous.

## Synthesis Planning

The current system can generate candidates that may not be synthetically practical.

Future integration:

- Use `synthesis_planner/` if applicable.
- Add RDKit synthetic accessibility.
- Add fragment availability.
- Add purchasability checks.
- Add route complexity.

Candidates should receive:

- Synthetic accessibility score.
- Commercial availability score.
- Route confidence.
- Estimated synthesis burden.

## Researcher Workflow

The target researcher workflow should become:

1. Select disease and target from PHARM.
2. Pull target structure or co-crystal.
3. Run molecular engine.
4. Review top candidates and explanations.
5. Run docking on top 50.
6. Run MD on top 5-10.
7. Run expert medicinal chemistry review.
8. Purchase/synthesize top 1-5.
9. Run binding or activity assay.
10. Feed results back into calibration.

## Productive Claims

Claims that can be made after current implementation:

- The system generates explainable fragment-based molecular hypotheses.
- The system integrates structural, categorical, chemical, and PHARM target priors.
- The system can perform early triage across structures.
- The system produces machine-readable evidence for downstream validation.

Claims that require future validation:

- The system enriches for true binders.
- The system predicts binding pose.
- The system improves docking hit rate.
- The system saves a measured amount of researcher time.
- The system identifies novel leads.

Claims that should not be made:

- The system proves binding.
- The system replaces docking or assays.
- The system is clinically predictive.
- The system has validated drug-discovery accuracy.

## Concrete Next Milestones

### Milestone 1: Co-Crystal Benchmark Loader

Deliver:

- `data/benchmarks/pdbbind_small.json`
- PDB path/ID.
- Ligand residue ID.
- Chain.
- Target ID.
- Disease context.
- Known ligand metadata.

Metrics:

- Pocket center error.
- Contact recovery.
- Candidate overlap.

### Milestone 2: Known-Ligand Pocket Benchmark

Deliver:

- Run benchmark across 10-20 co-crystals.
- Compare grid pocket vs ligand pocket vs centroid.
- Report failure modes.

Success:

- Grid pocket significantly better than centroid.
- Known ligand contact residues recovered above baseline.

### Milestone 3: Graph-Native Candidate Molecules

Deliver:

- RDKit molecule construction from categorical assembly.
- Valid canonical SMILES.
- SDF output.
- Descriptor calculation.

Success:

- Most generated candidates are RDKit-valid.
- Fragment trace remains attached to molecular graph.

### Milestone 4: Docking Adapter

Deliver:

- Prepare receptor and ligand.
- Run docking if tool is installed.
- Parse score and pose.
- Add docking term to integrated evidence.

Success:

- Top candidates can be docked automatically.
- Docked contacts are reported.

### Milestone 5: Active/Decoy Benchmark

Deliver:

- Active/decoy dataset for at least 5 targets.
- Integrated ranking report.
- AUROC/AUPRC/enrichment metrics.

Success:

- Integrated score beats random and simple descriptor baselines.

### Milestone 6: Prospective Pilot

Deliver:

- Select 1-2 targets.
- Freeze model.
- Generate candidates.
- Run docking/MD.
- Select candidates for assay.
- Record result.

Success:

- Demonstrated hit or clear quantified learning from failure.

## Risk Register

### Risk: False Confidence

The system can output precise-looking scores that are not experimentally validated.

Mitigation:

- Always label as triage.
- Keep limitations in reports.
- Add benchmark confidence intervals.

### Risk: Pocket Detection Failure

Grid cavity detection may find irrelevant cavities.

Mitigation:

- Use co-crystal benchmarks.
- Add residue-guided mode.
- Add target motif detection.

### Risk: Fragment Library Bias

The system may overproduce heteroaromatic fragments.

Mitigation:

- Add target-specific libraries.
- Add diversity constraints.
- Benchmark against actives/decoys.

### Risk: PHARM Prior Overdominates

Known-drug analogy may make generated candidates look better than they are.

Mitigation:

- Keep PHARM prior as one term.
- Allow `--no-pharm-binding-prior`.
- Report term breakdown.
- Benchmark PHARM prior alone versus integrated score.

### Risk: Chemistry Invalidity

Fallback SMILES may be too simplified.

Mitigation:

- Move to graph-native RDKit molecule construction.
- Validate valence and aromaticity.

## How We Should Talk About The System

Use:

- "early molecular triage"
- "explainable fragment hypothesis generation"
- "PHARM-informed molecular prioritization"
- "candidate generation for docking/MD follow-up"

Avoid:

- "binding proven"
- "drug discovered"
- "validated lead"
- "affinity predicted"

## Final Recommendation

The next engineering work should focus on evidence quality, not more architecture.

Priority order:

1. Co-crystal benchmark loader.
2. Pocket/contact recovery metrics.
3. Graph-native RDKit candidate assembly.
4. Docking adapter.
5. Active/decoy enrichment benchmark.
6. Prospective validation.

If these steps show enrichment over baselines, the system becomes more than a clever architecture: it becomes a practical researcher triage accelerator.

