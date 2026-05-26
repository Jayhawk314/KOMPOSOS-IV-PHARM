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

Full typed DB facts (2026-05-25, post-PMID verification and cleanup):
- 464 objects, 4956 morphisms
- 78 drugs, 20 diseases, 366 proteins
- 44 Drug->Disease approved indication labels (all FDA-approved, all with PMIDs)
- All 44 positives have mechanistic paths (Drug->Protein->Disease)
- 4939/4956 morphisms have provenance (99.7%): PMIDs + ChEMBL IDs
- 607 unique valid PMIDs (15 invalid PMIDs removed after manual verification)
- ~3,286 PubMed-derived Protein→Disease edges with categorical verification metadata
- ~1,670 curated edges from ChEMBL, FDA, KEGG, ESM2, STRING, ABPP
- ChEMBL drug names normalized (salt forms stripped, matched to base drugs)
- 17 new Drug->Protein edges added for base drugs via ChEMBL normalization
- DB SHA256: `85e73373e8dead78c8ba3a408cc0c92b44116cfcc5bad890286cc3cc63575005`

Current canonical harness:

```powershell
python validation\repurposing_benchmark.py --view legacy --protocol as_loaded
python validation\repurposing_benchmark.py --view full_typed --protocol as_loaded
python validation\repurposing_benchmark.py --view full_typed --protocol remove_direct_labels
python validation\repurposing_benchmark.py --view full_typed --protocol loocv
```

Add `--ci` for bootstrap 95% confidence intervals, `--baselines` for baseline
comparisons (random, degree, common-neighbor, shortest-path, path-count).

Current metrics (2026-05-24, 8 strategies, confidence-weighted paths, 44 positives):
- `full_typed/remove_direct_labels`: AUROC 0.956, AUPRC 0.537, Hits@5 1.00
- `full_typed/loocv`: AUROC 0.974, AUPRC 0.530, Hits@5 1.00, Hits@10 1.00, MRR 0.080
- `full_typed/as_loaded`: AUROC 0.887, AUPRC 0.135
- `legacy/as_loaded`: AUROC 0.931, AUPRC 0.465

Path bonus tuned via LOOCV grid search: min(0.25, 0.04 * sum(path_confidence)).
Confidence-weighted paths (2026-05-24): each path weighted by min-hop confidence.
Uniform strategy weights confirmed optimal by calibrate_loocv.py.

as_loaded protocols show Hits@K regression (now 0.00) because composition skips
existing edges — positives get zero path bonus while negatives can. This is an
artifact of the protocol, not real performance loss. The scientifically valid
protocols (loocv, remove_direct_labels) maintained or improved performance.

LOOCV baselines (AUROC, corrected 2026-05-11):
- strongest: shortest_path 0.931
- system AUROC: 0.974
- margin: +0.043 over strongest baseline

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
- `oracle/`: prediction/scoring strategies (8 strategies incl. binding_evidence).
- `oracle/binding_strategy.py`: BindingEvidenceStrategy (ABPP + Boltz2 + drug properties).
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
11. Expand data sources (ChEMBL SQLite - see `data/drugs/importers/CHEMBL_SETUP.md`).

## Verification

Focused regression:

```powershell
pytest tests\test_repurposing_benchmark.py -q
```

Full suite:

```powershell
pytest tests -q
```
