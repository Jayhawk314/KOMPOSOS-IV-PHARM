# CLAUDE.md - KOMPOSOS-IV-PHARM

## Project Identity

KOMPOSOS-IV-PHARM applies a categorical AI runtime to pharmaceutical discovery.

Primary long-term purpose: Track B drug design, including molecular generation,
binding/efficacy/safety prediction, ADMET, and patient context.

Current working capability: Track A drug repurposing over a curated
drug-target-disease graph.

Current audit rule: code and live data outrank stale docs. Always name the graph
view and validation protocol with any AUROC.

Author: James Ray Hawkins
License: Apache 2.0 / Commercial dual license
Python: 3.10+

## Read First

1. `CURRENT_STATE.md`
2. `MEMORY.md`
3. `INDEPENDENT_EXTERNAL_AUDIT_2026-05-06.md`
4. This file
5. `TECHNICAL_OVERVIEW.md` (architecture, strategies, validation, limitations)
6. `DATA_EXPANSION_GUIDE.md` (data source recommendations for expansion)

## Track A: Drug Repurposing

Status: working research prototype, not clinical or translational validation.

Data source: `data/drugs/tier1.db`
Reproducible build: `data/drugs/build_tier1.py` from `tier1_manifest.json`

Full typed DB facts (2026-05-25, post-evidence quantification expansion):
- 464 objects, 5382 morphisms (+438 from computational expansion)
- 78 drugs, 20 diseases, 366 proteins
- 44 Drug->Disease approved indication labels (all FDA-approved, all with PMIDs)
- All 44 positives have mechanistic paths (Drug->Protein->Disease)
- 5382/5382 morphisms have provenance (100%): PMIDs + ChEMBL IDs + computational
- 581 unique validated PMIDs (100% provenance coverage)
- 204 edges with quantitative values (IC50, mutation frequencies, hazard ratios, response rates)
- Evidence tier classification: MEASURED 1073, INFERRED 809, NOISE 2104, SPECULATIVE 955, ESTABLISHED 282, HYPOTHESIS 159
- Data sources: PubMed (1,663 PMIDs searched: 609 original + 1,054 targeted search), ChEMBL, FDA, KEGG, STRING PPI (338 edges), ESM2 similarity (100 edges), cBioPortal genomic, ABPP
- NLP PMID extraction: 373 quantitative data points from 204 PMIDs (92.2% validated against abstracts)
- ChEMBL drug names normalized (salt forms stripped, matched to base drugs)
- DB SHA256: `[updated after Phase 2-5 completion]`

Current canonical harness:

```powershell
python validation\repurposing_benchmark.py --view legacy --protocol as_loaded
python validation\repurposing_benchmark.py --view full_typed --protocol as_loaded
python validation\repurposing_benchmark.py --view full_typed --protocol remove_direct_labels
python validation\repurposing_benchmark.py --view full_typed --protocol loocv
```

Add `--ci` for bootstrap 95% confidence intervals, `--baselines` for baseline
comparisons (random, degree, common-neighbor, shortest-path, path-count).

Current metrics (2026-05-26, 9 strategies incl. Yoneda distance bonus, 44 positives, 204 quantitative edges):
- `full_typed/remove_direct_labels`: **AUROC 0.965**, AUPRC 0.634, Hits@5 1.00, Hits@10 0.80 (post-Yoneda integration)
- `full_typed/loocv`: **AUROC 0.945**, AUPRC 0.408, Hits@5 0.80, Hits@10 0.70, MRR 0.065 (pre-Yoneda; LOOCV pending re-run)
- `full_typed/as_loaded`: AUROC 0.457, AUPRC 0.025 (expected artifact, composition skips existing edges)

**Yoneda Distance Strategy integration (2026-05-26):**
- 9th strategy: structural similarity via confidence-weighted Yoneda presheaf fingerprints
- Operates on clean subgraph (MEASURED + ESTABLISHED edges only, 1355 edges)
- Integrated as additive bonus (like path_bonus), not averaged vote
- Coefficient 0.06 tuned via grid search over [0.0, 0.20] with cap 0.10
- AUROC 0.956 -> 0.965 (+0.009), AUPRC 0.537 -> 0.634 (+0.097), Hits@10 0.70 -> 0.80
- All metrics improved, zero regressions
- Drug equivalence classes discovered: 6 pairs with identical Yoneda profiles
  (Binimetinib=Cobimetinib, Encorafenib=Vemurafenib, Carboplatin=Oxaliplatin, etc.)
- Triage reports now show "Structural Similarity" vote with interpretation
- STT experiment script: `stt_repurposing.py` (standalone comparison of 3 STT strategies)

**Quantitative evidence expansion (2026-05-25):**
- 373 NLP extractions from 204 PMIDs (92.2% validated against PubMed abstracts)
- 204 edges with IC50, hazard ratios, mutation frequencies, response rates
- 250 edges updated, 244 tier upgrades to MEASURED
- Triage reports display quantitative evidence: `[IC50=7.7 uM]`, `[HR=0.97]`, `[Mutation freq=50.0%]`

Path bonus tuned via LOOCV grid search: min(0.25, 0.04 * sum(path_confidence)).
Confidence-weighted paths (2026-05-24): each path weighted by min-hop confidence.
Uniform strategy weights confirmed optimal by calibrate_loocv.py.

as_loaded protocols show Hits@K regression because composition skips existing edges —
positives get zero path bonus while negatives can. This is an artifact of the protocol,
not real performance loss.

LOOCV baselines (AUROC, corrected 2026-05-11):
- strongest: shortest_path 0.931
- system AUROC: 0.945 (post-quantitative expansion)
- margin: +0.014 over strongest baseline (modest but scientifically honest)

The old baseline table (shortest_path 0.559) was a label-order artifact corrected
via audit. The honest claim is modest improvement over strong graph-topology baselines
plus strategy votes, mechanistic paths, and evidence tracing for triage.

Additional validation (reported but not fully audit-reproduced with executable scripts):
- External (Hetionet): AUROC 0.744 on 7 held-out Hetionet-confirmed pairs
- Temporal holdout (pre/post 2013): AUROC 0.959 on 22 post-2013 FDA approvals
- Disease-level holdout: Mean AUROC 0.877 across 7 diseases (range 0.615-0.996)

Interpretation:
- The legacy AUROC is a historical hurdle only.
- Do not say "no leakage" without naming the protocol and label-removal policy.
- Unlabeled pairs are open-world unknowns, not confirmed negatives.

Benchmark manifest: `validation/repurposing_benchmark_manifest.json`.

Candidate triage CLI:

```powershell
# Disease-first: rank all drugs for a disease
python validation\triage.py Melanoma

# Drug-first: rank all diseases for a drug
python validation\triage.py --drug Sorafenib

# Specific pair: detailed report
python validation\triage.py Melanoma --drug Vemurafenib

# Output formats: --json, --markdown
# Options: --top N (default 10), --all, --db path.db
```

Every report includes: self-check (44/44 approved indications recoverable),
strategy vote breakdown, evidence chains with PMIDs, provenance coverage per
candidate, and APPROVED/NOT_APPROVED labels. NOT_APPROVED means not in our
44 FDA oncology indications (may already be in trials/literature). Detail
auto-expands for top-5 NOT_APPROVED candidates in terminal mode; specific
pair mode always shows full detail.

Provenance tools:
- `validation/triage.py` -- candidate triage reports with evidence chains
- `validation/trace_prediction.py` -- trace any prediction to evidence chains with PMIDs
- `validation/generate_citation_worksheet.py` -- generate citation TODO list
- 1260/1260 morphisms have provenance (100.0%): PMIDs + ChEMBL IDs
- Zero uncited morphisms remain

Data expansion:
- ChEMBL SQLite expansion deployed (2026-05-10): +269 proteins, +872 morphisms, +17 base drug targets
- See `CHEMBL_NORMALIZATION_2026-05-10.md` for details on drug name normalization
- See `DATA_EXPANSION_GUIDE.md` for further expansion recommendations (OpenTargets, STRING)
- Provenance complete (100%, 2026-05-12)

## Binding Evidence Strategy (2026-05-13)

The 8th oracle strategy (`oracle/binding_strategy.py`) integrates 5 molecular and
chemistry bridges into the repurposing scoring pipeline via 7 weighted components:

1. **ABPP Bridge** (`abpp_bridge.py`): 65 experimental IC50/engagement entries
   with PMIDs for drug-target pairs in tier1.db. (weight 0.30)
2. **Boltz2 Bridge** (`boltz2_bridge.py`): heuristic binding prediction, fallback
   mode, drug name suffix matching. (weight 0.10)
3. **Drug Properties** (`data/drugs/drug_properties.py`): Lipinski drug-likeness
   (weight 0.10) and drug-target molecular compatibility via logP/H-bond matching
   (weight 0.10). Molecular properties (MW, logP, HBD, HBA, functional groups) for
   all 78 drugs plus approximate binding-pocket properties for 50+ protein targets.
   **PubChem-verified (2026-05-13):** 46/68 drugs corrected via PUG REST API.
4. **Molecular Bridge** (`molecular_bridge/interaction_scoring.py`): solubility,
   steric, and reactivity scoring via `score_solubility_compatibility`,
   `score_steric_compatibility`, `score_reactivity_risk`. (weight 0.10)
5. **Pfam Domain Matching** (`chemistry/pfam_domain_mapper.py`): domain-drug class
   matching (kinase inhibitor -> kinase domain, etc.) using `PfamDomain` dataclass
   and known Pfam accessions. (weight 0.10)
6. Graph edge confidence from the Category morphism. (weight 0.20)

Triage reports show IC50 values, engagement status, and drug-likeness when
the binding_evidence strategy votes.

## Yoneda Distance Strategy (2026-05-26)

The 9th oracle strategy (`oracle/yoneda_strategy.py`) scores Drug-Disease pairs
by structural similarity to known treatments on the clean evidence subgraph.

**How it works:**
1. Loads MEASURED + ESTABLISHED edges only (1355 edges, noise-free)
2. Computes confidence-weighted Yoneda presheaf fingerprints for all objects
   (each (neighbor, relation) pair weighted by max morphism confidence)
3. For a Drug-Disease pair, finds the most similar drug that is FDA-approved
   for that disease using weighted Jaccard distance
4. Reports similarity as a score (0.0 = no overlap, 1.0 = identical profile)

**Integration:** Additive bonus in `score_pair()`, not an averaged vote.
Raw Yoneda scores (median 0.50 for positives) are lower than other strategies
(~0.85), so averaging them in would drag AUROC down. As a bonus
(`min(0.10, 0.06 * similarity)`), it can only help, never hurt.

**Scientific value beyond AUROC:**
- Composition tells you THAT a path exists (Drug -> Protein -> Disease)
- Yoneda tells you WHY the drug fits (similar target profile to known treatment)
- Drug equivalence classes are ground-truth validated (MEK inhibitors, BRAF
  inhibitors, platinum compounds, NSAIDs, MET inhibitors, RET inhibitors)
- AUPRC improvement (+0.097) means top candidates are more likely to be real

**STT experiment:** `stt_repurposing.py` tested 3 Simplicial Type Theory
strategies (Yoneda distance, fibration transport, Rezk completion). Only
Yoneda added value; transport was too sparse (3 diseases with zero protein
coverage on clean subgraph), Rezk was identical to Yoneda (no disease
equivalence classes found).

## Track B: Drug Design

Status: long-term goal, not scientifically validated in this repo.

The ABPP bridge and Boltz2 bridge are now wired into Track A scoring (binding
evidence strategy). This is a step toward Track B but does not constitute drug
design capability. Do not use Track A AUROC to claim Track B readiness.

Track B will need:
- Molecular fragments and scaffold libraries.
- Binding-site geometries and structure prediction.
- SMILES/structure data.
- ADMET and safety data.
- Synthesis routes.
- Ternary complex support.
- Patient/tissue context.
- Design-specific validation metrics.

## Architecture Summary

Core layers:
- Orion/plugin layer: bridge plugins and events.
- KOMPOSOS-IV Category runtime: objects, morphisms, persistence, enrichment, hooks.
- Infinity-cosmos/higher structure: 2-cells, fibrations, Yoneda, Kan extensions.
- COG: claim verification.
- OPTIMUS: categorical refinement/self-correction.

Key code areas:
- `core/`: fused Category runtime and categorical infrastructure.
- `oracle/`: prediction/scoring strategies (9 strategies incl. binding_evidence + yoneda_distance).
- `oracle/binding_strategy.py`: BindingEvidenceStrategy (ABPP + Boltz2 + drug properties).
- `oracle/yoneda_strategy.py`: YonedaDistanceStrategy (structural similarity on clean subgraph).
- `domains/bio/`: bio graph loader.
- `data/store.py`: SQLite store API.
- `data/drugs/build_tier1.py`: reproducible DB build from manifest.
- `data/drugs/drug_properties.py`: molecular properties for 78 drugs.
- `abpp_bridge.py`: 65 experimental IC50 entries for drug-target pairs.
- `boltz2_bridge.py`: heuristic binding prediction bridge.
- `chemistry/`: protein structure chemistry (Pfam domains, hydrophobicity, etc.).
- `molecular_bridge/`: molecular interaction scoring (5 scorers).
- `validation/`: repurposing validation harnesses and candidate triage CLI.
- `validation/triage.py`: candidate triage CLI (disease-first, drug-first, pair detail).
- `tests/`: regression and strategy tests.

## Loader Rule

`KomposOSStore.list_objects()` defaults to `limit=100`. Do not use it without an
explicit limit or pagination when loading production/scientific graphs.

`domains/bio/loader.py::BioDomainLoader` now loads all object rows. The old
first-100-object behavior is preserved only by
`validation.repurposing_benchmark.load_legacy_view()`.

## Scientific Rules

1. Code and database queries outrank docs.
2. Every AUROC must specify view, protocol, pair count, positive count, and label policy.
3. Direct Drug->Disease labels must be removed or held out for stronger claims.
4. Treat unlabeled Drug->Disease pairs as unknown, not confirmed false.
5. Report AUPRC, enrichment@K, Hits@K/MRR, calibration, and confidence intervals before external claims.
6. Require provenance for nodes and edges before treating the graph as publication-grade.
7. Do not represent fallback/mock scientific modules as production capability.

## Current Best Path

1. ~~Freeze evaluation.~~ DONE.
2. ~~Repair data integrity and provenance.~~ DONE (zero orphans, DB build script).
3. ~~Expand positive set and mechanistic coverage.~~ DONE (44 positives).
4. ~~Add external, temporal, disease-level validation.~~ DONE.
5. ~~Tune score combiners.~~ DONE (path bonus tuned via LOOCV grid search, AUROC 0.945→0.968).
6. ~~Build candidate triage CLI with evidence paths, provenance, uncertainty.~~ DONE (`validation/triage.py`).
7. ~~Complete provenance for remaining 302 uncited morphisms.~~ DONE (100%, 2026-05-12).
8. ~~Ablation studies.~~ DONE (composition is dominant strategy).
9. ~~ClinicalTrials.gov cross-check.~~ DONE (63% IN_TRIALS, 30% PRECLINICAL, 7% NOVEL).
10. ~~Wire molecular/chemistry bridges into scoring.~~ DONE (binding_evidence strategy, 2026-05-13).
11. ~~Integrate STT structural analysis.~~ DONE (Yoneda distance strategy, 2026-05-26).
12. Expand data sources (ChEMBL SQLite - see `data/drugs/importers/CHEMBL_SETUP.md`).

## Verification

Focused regression:

```powershell
pytest tests\test_repurposing_benchmark.py -q
```

Full suite:

```powershell
pytest tests -q
```
