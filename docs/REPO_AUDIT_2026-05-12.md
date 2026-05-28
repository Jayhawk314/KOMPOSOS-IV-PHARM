> **Legacy/historical notice (2026-05-27):** This file is retained for background or session history. It is not the current source of truth for Track A metrics or provenance. Current docs are in `truedocs/`, especially `truedocs/VALIDATION_AND_BENCHMARKS.md` and `truedocs/REPRODUCIBILITY_PROTOCOL.md`. Current strict run: AUROC 0.974694 [0.9606, 0.9855], AUPRC 0.551698 [0.4067, 0.6983], Hits@5/10/20 1.0000/0.6000/0.6000; LOOCV AUROC 0.975916 and AUPRC 0.553703; Hetionet external AUROC 0.634479 and AUPRC 0.009255. Source strings exist on all 5,382 morphisms with 610 PMID identifiers; this is not 100% edge-specific citation validation. Retired or superseded claims in this file should be read as historical.
# REPO AUDIT 2026-05-12

**Auditor**: Claude Opus 4.6 (automated)
**Date**: 2026-05-12
**Method**: Full import-chain tracing from active entry points + doc number verification

**Ground truth** (from code/DB):
- AUROC: 0.974 (full_typed/loocv), CI [0.965, 0.983]
- Objects: 1143 (78 drugs, 20 diseases, 366 proteins, 679 ExternalCompound)
- Morphisms: 1260
- Positives: 44
- Provenance: 1260/1260 (100%)
- Strategies: 7 production
- DB SHA256: 0BA4A7E01BBA3E1E52A03CD7765A3E6523618F439AB8A90ED4BD6B4BD95BC8E6

---

## 1. Summary Table

### Active entry points (traced imports from these)

The ACTIVE dependency chain starts from:
- `validation/repurposing_benchmark.py` -> `core.category`, `data.store`, `oracle.strategies`, `oracle.topos_strategy`
- `validation/triage.py` -> `validation.repurposing_benchmark`, `validation.trace_prediction`
- `validation/trace_prediction.py` -> `validation.repurposing_benchmark`, `data.store`
- `tests/test_repurposing_benchmark.py` -> `validation.repurposing_benchmark`, `domains.bio.loader`
- `domains/bio/loader.py` -> `data.store`, `core.category`

---

### core/ (Category Runtime)

| File | Status | Reason |
|------|--------|--------|
| `core/__init__.py` | ACTIVE | Package init |
| `core/category.py` | ACTIVE | Imported by repurposing_benchmark, strategies, loader, triage, store_adapter, tests |
| `core/types.py` | ACTIVE | Imported by store_adapter, loader, tests, knowledge_manager |
| `core/enrichment.py` | ACTIVE | Imported by test_optimus_integration, enrichment_extension |
| `core/enrichment_extension.py` | UNWIRED | Only imports core.enrichment; not imported by any active file |
| `core/optimus.py` | UNWIRED | Imported by tests/test_optimus_integration, bridges/optimus_plugin, stress_test -- NOT by Track A |
| `core/cosmos.py` | UNWIRED | Imported by tests/test_infinity_cosmos, bridges/infinity_cosmos_plugin; imports categorical/ -- NOT Track A |
| `core/two_cell_bridge.py` | UNWIRED | Imported by tests/test_infinity_cosmos, bridges/infinity_cosmos_plugin; imports categorical/ |
| `core/formal_yoneda.py` | UNWIRED | Imported by tests/test_higher_order_yoneda only |
| `core/higher_order_optimus.py` | UNWIRED | Imported by tests/test_higher_order_yoneda only |
| `core/capability_graph.py` | UNWIRED | Imported by tests/test_infinity_cosmos only |
| `core/independence.py` | UNWIRED | Imported by tests/test_infinity_cosmos only |
| `core/architect.py` | UNWIRED | Imported by tests/test_infinity_cosmos only |
| `core/persistence.py` | UNWIRED | Not imported by any active file |
| `core/hooks.py` | UNWIRED | Not imported by any active file |
| `core/functor.py` | UNWIRED | Not imported by any active file |
| `core/limits.py` | UNWIRED | Not imported by any active file |
| `core/bridge.py` | UNWIRED | Not imported by any active file |
| `core/self_corrector.py` | UNWIRED | Not imported by any active file |
| `core/plugin_generator.py` | UNWIRED | Not imported by any active file |
| `core/typed_capabilities.py` | UNWIRED | Not imported by any active file |
| `core/adjunction.py` | UNWIRED | Not imported by any active file |
| `core/game_bridge.py` | ARCHIVE-CANDIDATE | Game theory bridge, not Track A |
| `core/geometry_bridge.py` | ARCHIVE-CANDIDATE | Geometry bridge, not Track A |
| `core/hott_bridge.py` | ARCHIVE-CANDIDATE | HoTT bridge, not Track A |
| `core/topology_bridge.py` | ARCHIVE-CANDIDATE | Topology bridge, not Track A |

### oracle/ (Prediction Strategies)

| File | Status | Reason |
|------|--------|--------|
| `oracle/__init__.py` | ACTIVE | Package init, re-exports strategies |
| `oracle/strategies.py` | ACTIVE | 7 production strategies (KanExtension, TypeHeuristic, StructuralHole, Composition, YonedaPattern, FibrationLift + base class) |
| `oracle/topos_strategy.py` | ACTIVE | 7th production strategy (ToposLogic), imported by repurposing_benchmark |
| `oracle/prediction.py` | ACTIVE | Prediction/PredictionType dataclasses, imported by strategies.py |
| `oracle/score_combination.py` | UNWIRED | ImprovedScoreCombiner, imported only by calibrate_and_measure.py (root script) |
| `oracle/calibration.py` | UNWIRED | StrategyCalibrator, imported only by root calibrate_*.py scripts |
| `oracle/coherence.py` | UNWIRED | SheafCoherenceChecker, imported by oracle/__init__.py but not by Track A |
| `oracle/optimizer.py` | UNWIRED | PredictionOptimizer, imported by oracle/__init__.py but not by Track A |
| `oracle/learner.py` | UNWIRED | OracleLearner, imported by oracle/__init__.py but not by Track A |
| `oracle/conjecture.py` | UNWIRED | ConjectureEngine, imported by validate_conjectures.py only |
| `oracle/fibration.py` | UNWIRED | Extended FibrationLiftStrategy, imported by oracle but separate from strategies.py built-in |
| `oracle/evidence_combination.py` | UNWIRED | EvidenceCombination strategy, not used by Track A |
| `oracle/natural_transformation.py` | UNWIRED | NaturalTransformation strategy, not used by Track A |
| `oracle/operadic_decomposition.py` | UNWIRED | Operadic strategy, not used by Track A |
| `oracle/boundary_detection.py` | UNWIRED | Boundary strategy, not used by Track A |
| `oracle/game_strategy.py` | UNWIRED | Game strategy, not used by Track A |
| `oracle/activity_analysis.py` | UNWIRED | Activity strategy, not used by Track A |
| `oracle/cellular_dynamics.py` | UNWIRED | Cellular strategy, not used by Track A |
| `oracle/streaming_forecast.py` | UNWIRED | Streaming strategy, not used by Track A |
| `oracle/topological_anomaly.py` | UNWIRED | Topological strategy, not used by Track A |
| `oracle/geometric_homotopy_strategy.py` | UNWIRED | Geometric homotopy strategy, not used by Track A |
| `oracle/cubical_gap_filling_strategy.py` | UNWIRED | Cubical strategy, not used by Track A |
| `oracle/categorical_verifier.py` | UNWIRED | Categorical verifier, not used by Track A |
| `oracle/zfc_verifier.py` | UNWIRED | ZFC verifier, not used by Track A |

### validation/

| File | Status | Reason |
|------|--------|--------|
| `validation/__init__.py` | ACTIVE | Package init |
| `validation/repurposing_benchmark.py` | ACTIVE | Canonical AUROC harness |
| `validation/triage.py` | ACTIVE | Candidate triage CLI |
| `validation/trace_prediction.py` | ACTIVE | Evidence chain tracer, imported by triage.py |
| `validation/store_adapter.py` | ACTIVE | Store adapter, imported by repurposing_benchmark |
| `validation/repurposing_benchmark_manifest.json` | ACTIVE | Frozen benchmark manifest |
| `validation/generate_citation_worksheet.py` | ACTIVE | Provenance tool |
| `validation/ablation_study.py` | ACTIVE | Ablation study script (recently run) |
| `validation/ablation_results.json` | ACTIVE | Ablation results data |
| `validation/add_provenance.py` | ACTIVE | Provenance completion tool (recently used) |
| `validation/add_provenance_round2.py` | ACTIVE | Provenance completion round 2 (recently used) |
| `validation/check_novelty.py` | UNWIRED | ClinicalTrials.gov cross-check (standalone script) |
| `validation/check_morphisms_schema.py` | UNWIRED | DB schema checker (standalone utility) |
| `validation/drug_repurposing_audit.py` | UNWIRED | Imports validation.scientific_audit, standalone |
| `validation/scientific_audit.py` | UNWIRED | Audit framework, imported by drug_repurposing_audit |
| `validation/validate_36_predictions.py` | ARCHIVE-CANDIDATE | Old validation (36 predictions, pre-expansion) |
| `validation/validate_conjectures.py` | UNWIRED | Conjecture validator (standalone) |
| `validation/validate_protein_conjectures.py` | UNWIRED | Protein conjecture validator (standalone) |
| `validation/chemical_constraint_validator.py` | ARCHIVE-CANDIDATE | Chemistry validation, Track B |
| `validation/chemistry_validator.py` | ARCHIVE-CANDIDATE | Chemistry validation, Track B |
| `validation/complete_validator.py` | ARCHIVE-CANDIDATE | Protein structure validation, Track B |
| `validation/experimental_validator.py` | ARCHIVE-CANDIDATE | Experimental validation, Track B |
| `validation/pfam_validator.py` | ARCHIVE-CANDIDATE | Pfam validation, Track B |
| `validation/protein_structure_validator.py` | ARCHIVE-CANDIDATE | Protein structure validation, Track B |
| `validation/semantic_validator.py` | ARCHIVE-CANDIDATE | Semantic validation, imported by chemistry_validator |
| `validation/spatial_biology_metrics.py` | ARCHIVE-CANDIDATE | Spatial biology metrics, Track B |
| `validation/citations_todo.csv` | ARCHIVE-CANDIDATE | Old citation TODO list (provenance now 100%) |
| `validation/README.md` | STALE | Needs check against current state |

### data/

| File | Status | Reason |
|------|--------|--------|
| `data/__init__.py` | ACTIVE | Package init |
| `data/store.py` | ACTIVE | KomposOSStore, imported everywhere |
| `data/embeddings.py` | ACTIVE | EmbeddingsEngine, imported by oracle/strategies.py |
| `data/config.py` | UNWIRED | Not imported by active chain |
| `data/sources.py` | UNWIRED | Not imported by active chain |
| `data/bio_embeddings.py` | UNWIRED | Not imported by active chain |
| `data/protein_embeddings.py` | UNWIRED | Not imported by active chain |
| `data/strategy_weights.json` | UNWIRED | Weight file, not loaded by benchmark |
| `data/strategy_weights_6basic_fixed.json` | ARCHIVE-CANDIDATE | Old weight config |
| `data/strategy_weights_all22.json` | ARCHIVE-CANDIDATE | Old weight config |
| `data/strategy_weights_best.json` | ARCHIVE-CANDIDATE | Old weight config |
| `data/strategy_weights_with_topos.json` | ARCHIVE-CANDIDATE | Old weight config |
| `data/tuning_results.json` | ARCHIVE-CANDIDATE | Old tuning results |
| `data/auroc_audit_results.json` | ARCHIVE-CANDIDATE | Old audit results |
| `data/abpp_results.json` | ARCHIVE-CANDIDATE | ABPP results, Track B |

### data/drugs/

| File | Status | Reason |
|------|--------|--------|
| `data/drugs/__init__.py` | ACTIVE | Package init |
| `data/drugs/tier1.db` | ACTIVE | Production database |
| `data/drugs/tier1_manifest.json` | ACTIVE | Canonical manifest (includes ChEMBL) |
| `data/drugs/build_tier1.py` | ACTIVE | Reproducible DB build |
| `data/drugs/loader.py` | UNWIRED | Old loader, imports cancer_proteins/aml_proteins/drug_network -- NOT used by Track A (BioDomainLoader used instead) |
| `data/drugs/drug_network.py` | UNWIRED | Imported by data/drugs/loader.py only |
| `data/drugs/tier1_manifest_base.json` | ARCHIVE-CANDIDATE | Backup of pre-ChEMBL manifest |
| `data/drugs/tier1_manifest_chembl.json` | ACTIVE | ChEMBL expansion manifest (used in build) |
| `data/drugs/tier1_chembl.db` | ARCHIVE-CANDIDATE | Old intermediate ChEMBL DB |
| `data/drugs/tier1_manifest_ot06.json` | ARCHIVE-CANDIDATE | OpenTargets experiment (DO NOT DEPLOY) |
| `data/drugs/tier1_manifest_ot07.json` | ARCHIVE-CANDIDATE | OpenTargets experiment (DO NOT DEPLOY) |
| `data/drugs/tier1_manifest_pre_opentargets.json` | ARCHIVE-CANDIDATE | Pre-OT backup |
| `data/drugs/tier1_manifest_with_ot_diseases_dry_run_report.json` | ARCHIVE-CANDIDATE | OT dry run |
| `data/drugs/noetik_expansion.py` | ARCHIVE-CANDIDATE | Old expansion script |
| `data/drugs/redo_expansion.py` | ARCHIVE-CANDIDATE | Old expansion script |
| `data/drugs/redo_full_expansion.py` | ARCHIVE-CANDIDATE | Old expansion script |

### data/drugs/importers/

| File | Status | Reason |
|------|--------|--------|
| `data/drugs/importers/import_chembl_sqlite.py` | ACTIVE | ChEMBL importer (deployed) |
| `data/drugs/importers/import_chembl.py` | UNWIRED | API-based ChEMBL importer (superseded by SQLite version) |
| `data/drugs/importers/import_opentargets.py` | UNWIRED | OpenTargets importer (experiment failed, DO NOT DEPLOY) |
| `data/drugs/importers/import_opentargets_diseases.py` | UNWIRED | OpenTargets disease importer |
| `data/drugs/importers/import_string.py` | UNWIRED | STRING importer (not deployed) |
| `data/drugs/importers/README.md` | ACTIVE | Importer documentation |
| `data/drugs/importers/CHEMBL_SETUP.md` | STALE | References 86/388 (22.2%), needs update to 1260/1260 (100%) |

### data/external/

| File | Status | Reason |
|------|--------|--------|
| `data/external/__init__.py` | UNWIRED | Package init for external loaders |
| `data/external/biogrid_loader.py` | UNWIRED | BioGRID loader, not used by Track A |
| `data/external/cache.py` | UNWIRED | Cache utility for external loaders |
| `data/external/chembl_loader.py` | UNWIRED | ChEMBL API loader (superseded by import_chembl_sqlite) |
| `data/external/confidence.py` | UNWIRED | Confidence scoring for external data |
| `data/external/cosmic_loader.py` | UNWIRED | COSMIC loader |
| `data/external/dgidb_loader.py` | UNWIRED | DGIdb loader |
| `data/external/hetionet_loader.py` | UNWIRED | Hetionet loader |
| `data/external/id_mapper.py` | UNWIRED | ID mapping utility |
| `data/external/opentargets_loader.py` | UNWIRED | OpenTargets loader |
| `data/external/rate_limiter.py` | UNWIRED | Rate limiter utility |
| `data/external/reactome_loader.py` | UNWIRED | Reactome loader |

### data/proteins/

| File | Status | Reason |
|------|--------|--------|
| `data/proteins/cancer_proteins.py` | UNWIRED | Imported by data/drugs/loader.py (itself unwired) |
| `data/proteins/aml_proteins.py` | UNWIRED | Imported by data/drugs/loader.py (itself unwired) |
| `data/proteins/loader.py` | UNWIRED | Imports cancer_proteins, standalone |
| `data/proteins/download_string.py` | UNWIRED | STRING download script |
| `data/proteins/load_string_dataset.py` | UNWIRED | STRING dataset loader |
| `data/proteins/*.db` | ARCHIVE-CANDIDATE | Old protein databases (aml.db, cancer_proteins.db, etc.) |
| `data/proteins/*.json` | ARCHIVE-CANDIDATE | Old protein data files |
| `data/proteins/string_conjectures.txt` | ARCHIVE-CANDIDATE | Old conjectures |

### data/spatial/

| File | Status | Reason |
|------|--------|--------|
| All files in `data/spatial/` | ARCHIVE-CANDIDATE | Spatial biology data, Track B |

### domains/

| File | Status | Reason |
|------|--------|--------|
| `domains/bio/__init__.py` | ACTIVE | Package init, exports BioDomainLoader |
| `domains/bio/loader.py` | ACTIVE | Production loader, imported by test_repurposing_benchmark |

### bridges/

| File | Status | Reason |
|------|--------|--------|
| `bridges/__init__.py` | UNWIRED | Package init |
| `bridges/cog_reasoning.py` | UNWIRED | COG bridge, imports cog.session/engine |
| `bridges/crypto_plugin.py` | UNWIRED | Crypto plugin |
| `bridges/infinity_cosmos_plugin.py` | UNWIRED | Infinity cosmos plugin, imports core.cosmos |
| `bridges/knowledge_manager.py` | UNWIRED | Knowledge manager, imports core.category/types |
| `bridges/optimus_plugin.py` | UNWIRED | Optimus plugin, imports core.optimus |
| `bridges/session_manager.py` | UNWIRED | Session manager, imports cog.session/engine |
| `bridges/telemetry_plugin.py` | UNWIRED | Telemetry plugin |
| `bridges/README.md` | UNWIRED | Bridge documentation |

### cog/ (COG MCP Server)

| File | Status | Reason |
|------|--------|--------|
| `cog/__init__.py` | ACTIVE | Package init (COG is the MCP server running now) |
| `cog/__main__.py` | ACTIVE | Entry point for MCP server |
| `cog/server.py` | ACTIVE | MCP server implementation |
| `cog/engine.py` | ACTIVE | COG engine, imports core.category |
| `cog/schema.py` | ACTIVE | Schema definitions |
| `cog/session.py` | ACTIVE | Session management, imports core.category/types |
| `cog/energy.py` | ACTIVE | Energy computation |
| `cog/router.py` | ACTIVE | Tier routing |
| `cog/security.py` | ACTIVE | Security scanning, imports data.store |
| `cog/serializers.py` | ACTIVE | Serialization utilities |

### tests/

| File | Status | Reason |
|------|--------|--------|
| `tests/test_repurposing_benchmark.py` | ACTIVE | Main regression tests (156 passing) |
| `tests/test_oracle_strategies.py` | ACTIVE | Strategy unit tests |
| `tests/test_cog_iv.py` | ACTIVE | COG tests |
| `tests/test_optimus_integration.py` | UNWIRED | Tests for optimus (not Track A critical) |
| `tests/test_infinity_cosmos.py` | UNWIRED | Tests for infinity cosmos |
| `tests/test_higher_order_yoneda.py` | UNWIRED | Tests for higher-order yoneda |
| `tests/stress_test_full_stack.py` | UNWIRED | Full stack stress test |

### Material Bridge Directories (ALL ARCHIVE-CANDIDATE -- Track B / materials science)

| Directory | Status | Reason |
|-----------|--------|--------|
| `battery_bridge/` (8 files) | ARCHIVE-CANDIDATE | Battery materials science |
| `ceramic_bridge/` (8 files) | ARCHIVE-CANDIDATE | Ceramic materials science |
| `glass_bridge/` (8 files) | ARCHIVE-CANDIDATE | Glass materials science |
| `metal_bridge/` (8 files) | ARCHIVE-CANDIDATE | Metal joining/welding |
| `mof_bridge/` (16 files) | ARCHIVE-CANDIDATE | Metal-organic frameworks |
| `molecular_bridge/` (8 files) | ARCHIVE-CANDIDATE | Molecular design |
| `pfas_bridge/` (7 files) | ARCHIVE-CANDIDATE | PFAS replacement |
| `polymer_bridge/` (8 files) | ARCHIVE-CANDIDATE | Polymer blends |
| `semiconductor_bridge/` (8 files) | ARCHIVE-CANDIDATE | Semiconductor heterostructures |
| `cross_bridge/` (8 files) | ARCHIVE-CANDIDATE | Cross-domain bridges |
| `composition_engine/` (16 files) | ARCHIVE-CANDIDATE | Materials composition |
| `synthesis_planner/` (8 files) | ARCHIVE-CANDIDATE | Synthesis route planning |

These are self-contained module clusters. They import each other internally and from `categorical/` but are NOT imported by any Track A code.

### Math/Science Infrastructure (mostly UNWIRED or ARCHIVE-CANDIDATE)

| Directory | Status | Reason |
|-----------|--------|--------|
| `categorical/` (20 files) | UNWIRED | Imported by core/cosmos.py, composition_engine, geometry -- NOT by Track A directly |
| `geometry/` (20 files) | ARCHIVE-CANDIDATE | Protein structure/geometry, Track B |
| `topology/` (3 files) | ARCHIVE-CANDIDATE | Persistent homology, Track B |
| `hott/` (4 files) | ARCHIVE-CANDIDATE | Homotopy type theory, Track B |
| `cubical/` (2 files) | ARCHIVE-CANDIDATE | Cubical type theory, Track B |
| `game/` (2 files) | ARCHIVE-CANDIDATE | Game theory, Track B |
| `zfc/` (12 files) | UNWIRED | ZFC set theory; zfc/store_adapter.py imports core.category |
| `chemistry/` (12 files) | ARCHIVE-CANDIDATE | Chemistry energy functions, Track B |
| `spatial_biology/` (5 files) | ARCHIVE-CANDIDATE | Spatial transcriptomics, Track B |
| `foundation/` (1 file) | ARCHIVE-CANDIDATE | Verdict bilattice |

### Root-level Python scripts

| File | Status | Reason |
|------|--------|--------|
| `__init__.py` | ACTIVE | Root package init |
| `calibrate_loocv.py` | ACTIVE | LOOCV calibration tool (referenced in docs as confirming uniform weights) |
| `tune_path_bonus.py` | ACTIVE | Path bonus tuner (referenced in docs as producing current tuning) |
| `generate_cheap_drug_report.py` | ACTIVE | Generates CHEAP_DRUG_REPURPOSING_CANDIDATES.md |
| `audit_db_check.py` | UNWIRED | DB audit tool (standalone) |
| `audit_mechanistic_paths.py` | UNWIRED | Mechanistic path auditor (standalone) |
| `audit_pmids.py` | UNWIRED | PMID auditor (standalone) |
| `audit_positive_citations.py` | UNWIRED | Citation auditor (standalone) |
| `audit_category_paths.py` | UNWIRED | Category path auditor (standalone) |
| `full_audit_diagnostic.py` | UNWIRED | Full audit diagnostic (standalone) |
| `check_data_leakage.py` | UNWIRED | Data leakage checker (standalone) |
| `calibrate_all_strategies.py` | ARCHIVE-CANDIDATE | Old calibration script |
| `calibrate_and_measure.py` | ARCHIVE-CANDIDATE | Old calibration script |
| `calibrate_best_strategies.py` | ARCHIVE-CANDIDATE | Old calibration script |
| `calibrate_solid_auroc.py` | ARCHIVE-CANDIDATE | Old calibration script |
| `confirm_auroc.py` | ARCHIVE-CANDIDATE | Old AUROC confirmation |
| `verify_auroc.py` | ARCHIVE-CANDIDATE | Old AUROC verification |
| `verify_complete_auroc.py` | ARCHIVE-CANDIDATE | Old AUROC verification |
| `measure_real_success.py` | ARCHIVE-CANDIDATE | Old measurement script |
| `measure_real_success_with_validation.py` | ARCHIVE-CANDIDATE | Old measurement script |
| `measure_repurposing_auroc.py` | ARCHIVE-CANDIDATE | Old AUROC measurement |
| `measure_repurposing_simple.py` | ARCHIVE-CANDIDATE | Old measurement script |
| `show_rankings.py` | ARCHIVE-CANDIDATE | Old ranking display |
| `run_bio_with_22_strategies.py` | ARCHIVE-CANDIDATE | Old 22-strategy runner |
| `run_oracle_no_embeddings.py` | ARCHIVE-CANDIDATE | Old oracle runner |
| `demo_complete_system.py` | ARCHIVE-CANDIDATE | Old demo |
| `demo_full_drug_validation.py` | ARCHIVE-CANDIDATE | Old demo |
| `demo_bioorthogonal_stability.py` | ARCHIVE-CANDIDATE | Old demo, Track B |
| `debug_weight_integration.py` | ARCHIVE-CANDIDATE | Old debug script |
| `test_6_basic_fixed.py` | ARCHIVE-CANDIDATE | Old test script |
| `test_bio_loader.py` | ARCHIVE-CANDIDATE | Old test script |
| `test_composition_fix.py` | ARCHIVE-CANDIDATE | Old test script |
| `test_integrated_auroc.py` | ARCHIVE-CANDIDATE | Old test script |
| `test_integration_complete.py` | ARCHIVE-CANDIDATE | Old test script |
| `test_opentargets_api.py` | ARCHIVE-CANDIDATE | OT experiment test |
| `test_opentargets_cancer_filter.py` | ARCHIVE-CANDIDATE | OT experiment test |
| `test_opentargets_coverage.py` | ARCHIVE-CANDIDATE | OT experiment test |
| `test_pathway_debug.py` | ARCHIVE-CANDIDATE | Old debug test |
| `test_real_oracle.py` | ARCHIVE-CANDIDATE | Old test |
| `test_simple_integration.py` | ARCHIVE-CANDIDATE | Old test |
| `test_topos_debug.py` | ARCHIVE-CANDIDATE | Old debug test |
| `test_topos_fix.py` | ARCHIVE-CANDIDATE | Old test |
| `test_with_topos.py` | ARCHIVE-CANDIDATE | Old test |
| `generate_embeddings.py` | ARCHIVE-CANDIDATE | Embedding generator |
| `optimus_core.py` | UNWIRED | Optimus core (standalone) |
| `abpp_bridge.py` | ARCHIVE-CANDIDATE | ABPP bridge, Track B |
| `boltz2_bridge.py` | ARCHIVE-CANDIDATE | Boltz2 bridge, Track B |

### Other root files

| File | Status | Reason |
|------|--------|--------|
| `pyproject.toml` | ACTIVE | Project configuration |
| `example_knowledge.db` | ARCHIVE-CANDIDATE | Example database |
| `sessions/alice.db` | ARCHIVE-CANDIDATE | Old session database |
| `nul` | ARCHIVE-CANDIDATE | Empty file (Windows artifact) |
| `files.zip` | ARCHIVE-CANDIDATE | Unknown zip file |
| `tier1_manifest_test.json` | ARCHIVE-CANDIDATE | Test manifest |
| `opentargets_test_results.json` | ARCHIVE-CANDIDATE | OT test results |
| `validation_output.txt` | ARCHIVE-CANDIDATE | Old validation output |
| `audit_updates.txt` | ARCHIVE-CANDIDATE | Old audit updates |
| `proteins_to_check.txt` | ARCHIVE-CANDIDATE | Old protein checklist |
| `This conceptual paradigm shift in o.txt` | ARCHIVE-CANDIDATE | Fragment text file |

### Markdown Files

| File | Status | Reason |
|------|--------|--------|
| `CLAUDE.md` | ACTIVE | Agent instructions, numbers correct |
| `MEMORY.md` | ACTIVE | Agent memory, numbers correct |
| `CURRENT_STATE.md` | ACTIVE | Current state, numbers correct |
| `TECHNICAL_OVERVIEW.md` | ACTIVE | Technical overview |
| `CHEAP_DRUG_REPURPOSING_CANDIDATES.md` | ACTIVE | Candidate report, numbers correct |
| `EXECUTIVE_SUMMARY_FOR_CLINICIANS.md` | ACTIVE | Clinical summary, numbers correct |
| `KOMPOSOS_ROADMAP.md` | ACTIVE | Roadmap, numbers correct |
| `AUROC_VERIFICATION_AND_AUDIT.md` | ACTIVE | Audit verification, numbers correct |
| `DATA_EXPANSION_GUIDE.md` | STALE | References 464 objects, 76% provenance -- should be 1143 objects, 100% |
| `MASTER_TECHNICAL.md` | STALE | References 195 objects, 388 morphisms, 86/388 PMIDs (22.2%) in several places |
| `MASTER_MANUAL.md` | STALE | Likely has old numbers (needs detailed check) |
| `EXTERNAL_AUDIT_GUIDE.md` | STALE | References 958/1260 (76.0%) provenance -- should be 100% |
| `INDEPENDENT_EXTERNAL_AUDIT_2026-05-06.md` | STALE-BUT-HISTORICAL | Reports 195 objects, 388 morphisms, 22.2% -- correct AT TIME OF AUDIT but pre-expansion |
| `AUDIT_FIX_REPORT_2026-05-11.md` | ACTIVE | Audit fix report, correct |
| `DEPLOYMENT_2026-05-10.md` | STALE-BUT-HISTORICAL | Reports 464 objects, 76% -- correct at deployment time, pre-audit |
| `CHEMBL_NORMALIZATION_2026-05-10.md` | STALE-BUT-HISTORICAL | Correct at time of writing |
| `SESSION_SUMMARY_2026-05-06.md` | ARCHIVE-CANDIDATE | Session summary |
| `SESSION_SUMMARY_2026-05-10.md` | ARCHIVE-CANDIDATE | Session summary |
| `SESSION_SUMMARY_2026-05-11.md` | ARCHIVE-CANDIDATE | Session summary |
| `CLAUDE_HANDOFF_PROMPT_2026-05-11.md` | ARCHIVE-CANDIDATE | Handoff prompt |
| `IMPLEMENTATION_PLAN_2026-05-10.md` | ARCHIVE-CANDIDATE | Implementation plan (completed) |
| `AUROC_1.0_ACHIEVEMENT.md` | STALE | Claims AUROC 1.0 -- this is an old, debunked claim |
| `AUROC_IMPROVEMENT_SUMMARY.md` | STALE | Old improvement summary |
| `AUROC_VERIFICATION_PROTOCOL.md` | STALE | Old verification protocol |
| `BRAINSTORM_NEXT_LEVEL.md` | ARCHIVE-CANDIDATE | Brainstorming doc |
| `CLINICAL_VALIDATION_PROPOSAL.md` | ARCHIVE-CANDIDATE | Clinical proposal |
| `CLAUDE_OPUS_ANALYSIS.md` | ARCHIVE-CANDIDATE | Analysis doc |
| `EXTERNAL_AUDIT_REPORT_2026-05-04.md` | STALE-BUT-HISTORICAL | Reports 16 positives, pre-expansion |
| `FIVE_LAYER_ARCHITECTURE.md` | ARCHIVE-CANDIDATE | Architecture doc |
| `GRAND_INTEGRATION_PLAN.md` | ARCHIVE-CANDIDATE | Integration plan |
| `INFINITY_COSMOS_INTEGRATION_BLUEPRINT.md` | ARCHIVE-CANDIDATE | Integration blueprint |
| `KOMPOSOS_ROADMAP (1).md` | ARCHIVE-CANDIDATE | Duplicate roadmap |
| `MIGRATION_COMPLETE.md` | STALE | Claims spatial AUROC 1.0 |
| `MIGRATION_SUCCESS.md` | STALE | Claims spatial AUROC 1.0 |
| `NEXT_STEPS_PLAN.md` | STALE | References 195 objects, 388 morphisms, 22.2% |
| `PLATFORM_PROTOCOL_DESIGN.md` | ARCHIVE-CANDIDATE | Platform design doc |
| `REPURPOSING_BEST_PATH_2026-05-04.md` | STALE | References 195 objects, 388 morphisms |
| `RULIAD_IMPLEMENTATION_ROADMAP.md` | ARCHIVE-CANDIDATE | Ruliad roadmap |
| `SOLID_IMPLEMENTATION_COMPLETE.md` | ARCHIVE-CANDIDATE | Old completion report |
| `STRATEGY_RESEARCH_FINDINGS.md` | ARCHIVE-CANDIDATE | Strategy research |
| `SYSTEM_ANALYSIS.md` | STALE | Likely has old numbers |
| `SYSTEM_AUDIT.md` | STALE | Likely has old numbers |
| `TESTING_CHECKLIST.md` | STALE | References 0.945, 195 objects, 388 morphisms, 22.2% |
| `THE_DEFINITIVE_GUIDE.md` | STALE | Likely has old numbers |
| `TRANSFORMATIVE_POSSIBILITIES.md` | ARCHIVE-CANDIDATE | Aspirational doc |
| `kid-fun-adventure-math-book.md` | ARCHIVE-CANDIDATE | Not related to project |
| `the-story-that-is-a-category.md` | ARCHIVE-CANDIDATE | Not related to project |

### Other directories

| File | Status | Reason |
|------|--------|--------|
| `archive/` (8 files) | ARCHIVE-CANDIDATE | Already archived |
| `examples/production_agent.py` | UNWIRED | Example COG agent |
| `examples/README.md` | UNWIRED | Example docs |
| `scripts/interpret_structure.py` | ARCHIVE-CANDIDATE | Structure interpretation, Track B |
| `scripts/lab_scale_test.py` | ARCHIVE-CANDIDATE | Lab scale test, Track B |
| `scripts/map_drug_targets.py` | UNWIRED | Drug target mapping |
| `scripts/mutation_impact.py` | ARCHIVE-CANDIDATE | Mutation impact, Track B |
| `scripts/predict_structure.py` | ARCHIVE-CANDIDATE | Structure prediction, Track B |
| `scripts/predict_structure_categorical.py` | ARCHIVE-CANDIDATE | Structure prediction, Track B |

---

## 2. UNWIRED Candidates for Re-integration

### High Value

| File | What It Does | Integration Effort |
|------|-------------|-------------------|
| `oracle/score_combination.py` | ImprovedScoreCombiner with path features | Low -- could replace simple weighted average in benchmark |
| `oracle/calibration.py` | StrategyCalibrator with weighted_average | Low -- already used by calibrate_loocv.py |
| `oracle/evidence_combination.py` | Evidence combination strategy | Medium -- add as 8th strategy |
| `oracle/natural_transformation.py` | Natural transformation detection | Medium -- add as 8th strategy |
| `data/external/hetionet_loader.py` | Hetionet data loader | Medium -- useful for external validation |

### Medium Value

| File | What It Does | Integration Effort |
|------|-------------|-------------------|
| `validation/drug_repurposing_audit.py` | Automated audit framework | Low -- standalone utility |
| `validation/scientific_audit.py` | Scientific audit checks | Low -- standalone utility |
| `validation/check_novelty.py` | ClinicalTrials.gov cross-check | Low -- standalone utility |
| `core/persistence.py` | Persistence layer | Medium -- alternative to SQLite store |
| `data/external/` (all loaders) | BioGRID, COSMIC, DGIdb, Reactome, ChEMBL, OpenTargets | Medium -- data expansion sources |

### Lower Value (but real code)

| File | What It Does | Integration Effort |
|------|-------------|-------------------|
| `oracle/operadic_decomposition.py` | Operadic strategy | Medium |
| `oracle/boundary_detection.py` | Boundary detection strategy | Medium |
| `oracle/game_strategy.py` | Game theory strategy | Medium |
| `oracle/conjecture.py` | Conjecture engine | Medium |
| `bridges/knowledge_manager.py` | Knowledge management | Medium |

---

## 3. Track B Archive List

These files should be moved to `archive/track_b/` when ready. They contain real code for future profitable use but are NOT needed for current Track A operations.

### Chemistry / Molecular Design
- `abpp_bridge.py` -- ABPP activity probe scaffolding
- `boltz2_bridge.py` -- Boltz2 structure prediction bridge
- `chemistry/` (12 files) -- Energy functions, H-bonds, vdW, rotamers, etc.
- `geometry/` (20 files) -- Ricci curvature, structure prediction, ESMFold pipeline
- `scripts/predict_structure.py`, `predict_structure_categorical.py`, `interpret_structure.py`
- `scripts/mutation_impact.py`, `lab_scale_test.py`

### Spatial Biology
- `spatial_biology/` (5 files) -- CosMx adapter, pathway scoring, validation
- `data/spatial/` (all CSV/JSON files)

### Materials Science Bridges
- `battery_bridge/` (8 files)
- `ceramic_bridge/` (8 files)
- `glass_bridge/` (8 files)
- `metal_bridge/` (8 files)
- `mof_bridge/` (16 files)
- `molecular_bridge/` (8 files)
- `pfas_bridge/` (7 files)
- `polymer_bridge/` (8 files)
- `semiconductor_bridge/` (8 files)
- `cross_bridge/` (8 files)
- `composition_engine/` (16 files)
- `synthesis_planner/` (8 files)

### Mathematical Infrastructure (not used by Track A)
- `hott/` (4 files)
- `cubical/` (2 files)
- `game/` (2 files)
- `topology/` (3 files)
- `foundation/` (1 file)

**Total Track B files: ~170 files across ~20 directories**

---

## 4. Stale Docs

| Doc | What's Wrong | Fix or Archive? |
|-----|-------------|-----------------|
| `MASTER_TECHNICAL.md` | Says 195 objects, 388 morphisms, 86/388 PMIDs (22.2%), AUROC 0.945 | **FIX** -- update to 1143/1260/100%/0.974 |
| `DATA_EXPANSION_GUIDE.md` | Says 464 objects, 76% provenance, AUROC 0.968 | **FIX** -- update to 1143/100%/0.974 |
| `EXTERNAL_AUDIT_GUIDE.md` | Says 958/1260 (76.0%) provenance | **FIX** -- update to 1260/1260 (100%) |
| `AUROC_1.0_ACHIEVEMENT.md` | Claims AUROC 1.0 (debunked) | **ARCHIVE** -- misleading |
| `AUROC_IMPROVEMENT_SUMMARY.md` | Old improvement numbers | **ARCHIVE** |
| `AUROC_VERIFICATION_PROTOCOL.md` | Old protocol | **ARCHIVE** |
| `MIGRATION_COMPLETE.md` | Claims spatial AUROC 1.0 | **ARCHIVE** |
| `MIGRATION_SUCCESS.md` | Claims spatial AUROC 1.0 | **ARCHIVE** |
| `NEXT_STEPS_PLAN.md` | Says 195 objects, 388 morphisms, LOOCV 0.968 | **ARCHIVE** (superseded by CURRENT_STATE) |
| `REPURPOSING_BEST_PATH_2026-05-04.md` | Says 195 objects, 388 morphisms | **ARCHIVE** (superseded) |
| `TESTING_CHECKLIST.md` | Says AUROC 0.945, 195 objects, 22.2% | **ARCHIVE** or **FIX** |
| `SYSTEM_ANALYSIS.md` | Likely stale numbers | Needs detailed check, probably **ARCHIVE** |
| `SYSTEM_AUDIT.md` | Likely stale numbers | Needs detailed check, probably **ARCHIVE** |
| `THE_DEFINITIVE_GUIDE.md` | Likely stale numbers | Needs detailed check, probably **ARCHIVE** |
| `data/drugs/importers/CHEMBL_SETUP.md` | Says 86/388 (22.2%) | **FIX** |

---

## 5. Recommended Cleanup Actions (Prioritized)

### Priority 1: Fix stale docs that users/auditors will read
1. **Fix `MASTER_TECHNICAL.md`** -- update all occurrences of 195/388/86/22.2% to 1143/1260/1260/100%
2. **Fix `DATA_EXPANSION_GUIDE.md`** -- update 464/76% to 1143/100%
3. **Fix `EXTERNAL_AUDIT_GUIDE.md`** -- update 76% to 100%
4. **Fix `data/drugs/importers/CHEMBL_SETUP.md`** -- update provenance numbers

### Priority 2: Archive misleading docs
5. Move `AUROC_1.0_ACHIEVEMENT.md` to `archive/` (claims debunked AUROC 1.0)
6. Move `MIGRATION_COMPLETE.md` and `MIGRATION_SUCCESS.md` to `archive/` (claim spatial AUROC 1.0)
7. Move `AUROC_IMPROVEMENT_SUMMARY.md` and `AUROC_VERIFICATION_PROTOCOL.md` to `archive/`

### Priority 3: Archive old scripts
8. Move ~30 root-level `test_*.py`, `verify_*.py`, `measure_*.py`, `calibrate_*.py`, `demo_*.py` scripts to `archive/scripts/`
9. Move old manifest backups (`tier1_manifest_base.json`, `*_ot06.json`, `*_ot07.json`, etc.) to `archive/data/`
10. Move session summaries to `archive/sessions/`

### Priority 4: Archive Track B (when ready for major cleanup)
11. Move all material bridge directories to `archive/track_b/materials/`
12. Move `chemistry/`, `geometry/`, `spatial_biology/` to `archive/track_b/`
13. Move `hott/`, `cubical/`, `game/`, `topology/`, `foundation/` to `archive/track_b/math/`

### Priority 5: Consider re-integrating valuable unwired code
14. Wire `oracle/calibration.py` into benchmark harness (provides weighted_average)
15. Wire `data/external/hetionet_loader.py` for external validation re-runs
16. Consider adding `oracle/evidence_combination.py` as 8th strategy

---

## 6. Statistics

| Category | Count |
|----------|------:|
| ACTIVE | ~45 files |
| UNWIRED | ~60 files |
| STALE docs | ~15 files |
| ARCHIVE-CANDIDATE | ~220+ files |
| Track B (subset of archive) | ~170 files |

The active Track A system runs on approximately **45 files**. The remaining ~270+ files are either unwired infrastructure, old scripts, stale docs, or Track B scaffolding. The repo has significant cleanup potential.

---

*Audit completed 2026-05-12 by Claude Opus 4.6. This is a read-only audit; no files were modified.*
