> **Legacy/historical notice (2026-05-27):** This file is retained for background or session history. It is not the current source of truth for Track A metrics or provenance. Current docs are in `truedocs/`, especially `truedocs/VALIDATION_AND_BENCHMARKS.md` and `truedocs/REPRODUCIBILITY_PROTOCOL.md`. Current strict run: AUROC 0.974694 [0.9606, 0.9855], AUPRC 0.551698 [0.4067, 0.6983], Hits@5/10/20 1.0000/0.6000/0.6000; LOOCV AUROC 0.975916 and AUPRC 0.553703; Hetionet external AUROC 0.634479 and AUPRC 0.009255. Source strings exist on all 5,382 morphisms with 610 PMID identifiers; this is not 100% edge-specific citation validation. Retired or superseded claims in this file should be read as historical.
# External Audit Report: KOMPOSOS-IV-PHARM

Date: 2026-05-04
Auditor role: external technical/scientific reviewer
Scope: drug-repurposing software, medical-science rigor, bioinformatics validation, data provenance, reproducibility, and software auditability.

## Executive Verdict

The repo contains a working categorical knowledge-graph scoring prototype for Drug->Disease ranking. The narrow claimed AUROC of 0.884550 is reproducible with `verify_complete_auroc.py`, but that claim is not a robust full-database validation. It is now preserved as an explicit `legacy/as_loaded` benchmark view of `tier1.db` containing 28 drugs, 8 diseases, and 11 positive Drug->Disease edges, while the SQLite database itself contains 78 drugs, 20 diseases, and 16 positive Drug->Disease edges.

External audit conclusion: the current system is a research prototype, not a clinically or translationally validated drug-repurposing platform. The headline AUROC should be treated as a narrow internal benchmark only. The strongest defensible audit number from my read-only checks is approximately 0.772 AUROC under leave-one-approved-edge-out evaluation over the full typed database.

Confidence in published/production claims: LOW.
Confidence that the code has a useful mechanistic graph prototype: MEDIUM.
Clinical/translational readiness: NOT READY.

## Post-Audit Implementation Update

After the audit, the repo was updated to make the benchmark/discovery split
executable:

- `domains/bio/loader.py::BioDomainLoader` now loads all object rows before all
  morphisms instead of silently inheriting `KomposOSStore.list_objects()`'s
  default `limit=100`.
- `validation/repurposing_benchmark.py` preserves the historical truncated view
  explicitly as `--view legacy`.
- `verify_complete_auroc.py` now delegates to that named legacy view.
- `tests/test_repurposing_benchmark.py` locks the legacy AUROC, full typed
  counts, and full loader behavior.
- `validation/repurposing_benchmark_manifest.json` records the current DB
  checksum, benchmark commands, counts, positive labels, and AUROC values.

This remediates the hidden loader truncation defect. It does not remediate the
larger scientific audit issues: data provenance, small validation set,
open-world negatives, incomplete mechanisms, external validation, and
confidence intervals.

## Strategic Clarification

The full SQLite database is not automatically the best benchmark for the system. A larger graph can mix approved labels, holdout labels, weak hypotheses, expansion candidates, incomplete mechanism stubs, and exploratory objects. That is useful for discovery, but it is not automatically a clean AUROC task.

The audit concern is therefore not "use the full DB for everything." The concern is that every result needs a named graph view and a named label policy. The legacy 28-drug x 8-disease view can be kept as a historical AUROC hurdle if it is explicitly called `legacy_auroc`. The full typed graph should be used to monitor whether the tool remains useful as the discovery graph grows. A stricter leave-one-edge-out or direct-labels-removed protocol should be used for scientific claims.

Recommended operating model:

- `legacy_auroc`: frozen small benchmark for continuity with prior results.
- `full_typed_monitor`: full typed graph for drift, coverage, and broad ranking sanity checks.
- `label_removed_validation`: direct Drug->Disease labels removed, used to estimate mechanism-only performance.
- `loocv_validation`: leave-one-approved-edge-out, used for stronger but still internal validation.
- `discovery_graph`: largest useful graph, allowed to contain hypotheses, weak evidence, and candidate-expansion data, but not used as a clean AUROC benchmark without a manifest.

## Protocol Used

I treated code and live data as source of truth, with docs as context only. I inspected the loader, database, scoring strategies, AUROC scripts, validation scripts, and drug-network data definitions. I ran read-only Python checks against `data/drugs/tier1.db`, reproduced the claimed AUROC, ran the main pytest suite, and compared the repo against contemporary biomedical prediction expectations from:

- FDA Good Machine Learning Practice guiding principles for medical-device AI/ML: https://www.fda.gov/medical-devices/software-medical-device-samd/good-machine-learning-practice-medical-device-development-guiding-principles
- TRIPOD+AI reporting guidance for clinical prediction models: https://www.bmj.com/content/385/bmj-2023-078378
- Hetionet/Project Rephetio drug-repurposing KG benchmark: https://elifesciences.org/articles/26726
- TxGNN zero-shot drug-repurposing paper: https://www.nature.com/articles/s41591-024-03233-x
- Pushpakom et al. drug-repurposing review: https://www.nature.com/articles/nrd.2018.168

These references set the audit bar: transparent data provenance, clear task definition, leakage-resistant splits, baselines, confidence intervals, external validation, explainability, and clinical-use disclaimers.

## Reproduced Results

| Check | Result |
| --- | --- |
| `python verify_complete_auroc.py` | AUROC = 0.884550 over 224 pairs, 11 positives, 213 negatives |
| `python full_audit_diagnostic.py` | Simple-average AUROC = 0.957345 but only among 187 pairs with predictions; calibrated AUROC = 0.777401 |
| Direct SQLite counts | 190 objects, 333 morphisms, 78 drugs, 20 diseases, 16 Drug->Disease positives |
| Historical `legacy` benchmark view | 189 objects, 333 morphisms, 28 drugs, 8 diseases, 11 Drug->Disease positives, 89 auto-created `Object`-typed endpoints |
| Full typed DB scoring, same 7 strategies | AUROC = 0.794325 over 1,560 pairs, 16 positives |
| Full typed DB with all direct Drug->Disease edges removed | AUROC = 0.809019 |
| Full typed leave-one-positive-edge-out comparison | AUROC = 0.772081 |
| `pytest tests -q` after audit updates | 155 passed, 1 warning; however the run emitted a Windows native-library crash trace from `torchvision/transformers` after reporting pass |

The named benchmark harness added after this audit is `validation/repurposing_benchmark.py`.

Useful commands:

```powershell
python validation\repurposing_benchmark.py --view legacy --protocol as_loaded
python validation\repurposing_benchmark.py --view full_typed --protocol as_loaded
python validation\repurposing_benchmark.py --view full_typed --protocol remove_direct_labels
python validation\repurposing_benchmark.py --view full_typed --protocol loocv
```

The interrupted `validation/drug_repurposing_audit.py` run was not repeated because the user intentionally stopped it.

## Critical Findings

### 1. The headline AUROC is based on a truncated legacy view

Original audit finding: `domains/bio/loader.py` called `self.store.list_objects()` without a limit. In `data/store.py`, `list_objects()` defaults to `limit=100`. The loader then loaded all 333 morphisms, and `core/category.py` auto-created missing endpoints with default type `Object`.

Current implementation update: `BioDomainLoader` now loads all object rows. The truncated behavior is preserved only as the explicit `legacy` view in `validation/repurposing_benchmark.py`.

Evidence:

- `data/store.py:495` defines `list_objects(self, limit: int = 100, ...)`.
- Historical code path called `self.store.list_objects()` with no limit.
- `core/category.py:163-174` auto-creates missing morphism endpoints.

Impact:

- SQLite truth: 78 drugs, 20 diseases, 16 Drug->Disease positives.
- Legacy benchmark truth: 28 drugs, 8 diseases, 11 positives.
- The claimed 224-pair benchmark is not the full `tier1.db` task.
- Many entities become untyped `Object`, excluding them from Drug->Disease evaluation.

Severity before remediation: CRITICAL.
Residual severity after remediation: MEDIUM, because the legacy AUROC can still be misreported if the view is not named.

### 2. Database integrity is not clean

The SQLite database has 190 object rows, but morphism endpoints reference 189 distinct names plus 4 names missing from `objects`: `CXCL12`, `CXCR4`, `IFNG`, `PI3KCA`. Five object rows are not referenced by any morphism: `CD163`, `CD4`, `CD68`, `FOXP3`, `TOP2A`.

Impact:

- The graph is not referentially complete at the semantic level, even if the loader can auto-create endpoints.
- Missing endpoints get default `Object` type during Category loading, which changes downstream strategy behavior.

Severity: CRITICAL for auditability; HIGH for current prototype use.

### 3. AUROC scripts disagree on the evaluation universe

`verify_complete_auroc.py` includes no-prediction pairs as score 0 and reports 0.884550 over 224 pairs. `full_audit_diagnostic.py` builds `all_pair_data` only when at least one strategy predicts, so its "simple average" AUROC of 0.957345 excludes 37 no-prediction pairs, including one positive.

Evidence:

- `verify_complete_auroc.py:56-64` assigns score 0.0 when no strategy predicts.
- `full_audit_diagnostic.py:99-109` appends a pair only if there are votes.
- `full_audit_diagnostic.py:111-121` counts skipped pairs separately but excludes them from AUROC.

Impact:

- The repo has two incompatible AUROC definitions in active audit scripts.
- The larger 0.957345 number is not comparable to the 0.884550 claim.

Severity: CRITICAL.

### 4. Direct Drug->Disease labels remain in the graph during prediction

`ToposLogicStrategy` has been fixed for Drug->Disease pairs: it returns early through `_check_pathway_support()` and does not call `_has_direct_edge()` for repurposing pairs. That part is currently correct.

However, analogy/profile strategies still operate on a graph that includes direct `treats` edges. `KanExtensionStrategy` builds source outgoing profiles and target incoming profiles from all morphisms, including Drug->Disease labels. `YonedaPatternStrategy` also uses outgoing target overlap and returns no prediction for existing source-target pairs, meaning behavior differs between positives and negatives.

Evidence:

- `oracle/topos_strategy.py:98-116` routes Drug->Disease pairs through pathway support and returns.
- `oracle/strategies.py:105-118` and `oracle/strategies.py:129-145` build Kan-extension profiles from all morphisms.
- `oracle/strategies.py:536-578` uses outgoing hom-pattern overlap in Yoneda-pattern prediction.

Impact:

- This is not direct same-edge leakage in `topos_logic`, but it is still label contamination unless evaluation removes direct indication edges from training graphs.
- Leave-one-positive-edge-out AUROC on the full typed graph was 0.772081, materially below the headline 0.884550.

Severity: HIGH.

### 5. The current mechanistic graph misses canonical biology for key positives

Full DB disease support showed:

- `CML` has zero incoming protein/mechanism edges, so `Imatinib->CML` cannot be recovered mechanistically.
- `Type2_Diabetes` has zero incoming protein/mechanism edges, so `Metformin->Type2_Diabetes` cannot be recovered mechanistically.
- `Bevacizumab->Colorectal_Cancer` has no 2-hop Drug->Protein->Disease support under the current graph.
- `Trametinib->Melanoma` has no 2-hop support because the MEK-to-melanoma pathway is not represented directly enough for the scorer.

Impact:

- Several approved labels are present as direct ground truth without enough mechanistic support.
- For a mechanistic repurposing engine, this is a core data completeness issue.

Severity: HIGH.

### 6. The current validation set is too small and too internally curated

The narrow claim uses 11 positives. The full DB contains 16 positives. Either way, the positive sample size is too small for a strong biomedical performance claim. One or two rank changes materially alter AUROC. There are no confidence intervals, bootstrap intervals, disease-level splits, temporal splits, external holdout cohorts, or prospective validations in the working code path.

External context:

- Hetionet modeled 755 treatments and scored 209,168 compound-disease pairs using 29 public resources.
- TxGNN evaluated holdout and zero-shot settings across a much larger medical KG and reported confidence intervals and multiple baselines.

Severity: HIGH.

### 7. Negative labels are open-world unknowns, not confirmed negatives

The scripts treat all unobserved Drug->Disease pairs as negatives. That is common in early KG experiments, but it must be explicitly reported as an open-world assumption. Several "false" pairs may be approved elsewhere, plausible repurposing candidates, contraindications, or unreviewed hypotheses.

Impact:

- AUROC is a ranking-with-unlabeled-unknowns metric, not a clinical true/false efficacy metric.
- AUPRC, enrichment@K, Hits@K/MRR, calibration curves, and manually curated negative/contraindication sets should be reported alongside AUROC.

Severity: HIGH.

### 8. Production loader in `data/drugs/loader.py` appears broken

Static inspection shows `create_drug_store()` creates `category = Category(db_path)` but then uses `store` and `StoredObject`, neither imported/defined in the shown code path.

Evidence:

- `data/drugs/loader.py:78` passes `db_path` as the first `Category` argument, which is `name`, not `db_path`.
- `data/drugs/loader.py:85`, `88`, `96`, `104`, and later lines use `store`.
- `data/drugs/loader.py:114` and related code use `StoredObject` despite importing `Object`/`Morphism`.

Impact:

- The stated pathway for creating/loading the drug store is not reliable.
- Existing `tier1.db` may be a stale artifact rather than a reproducibly generated dataset.

Severity: HIGH.

### 9. Structure prediction, ABPP, ADMET, and drug-design modules are not production scientific modules

`boltz2_bridge.py` falls back to heuristic name-based scores when Boltz is unavailable and includes hardcoded known pairs. `abpp_bridge.py` creates an example ABPP JSON with six literature-like examples if no database exists. Various structure modules contain placeholders, mock MSAs, synthetic data, TODOs, or fallback contact predictors.

Impact:

- These modules should not be represented as validated drug-design, binding, ADMET, or experimental-validation capability.
- They are useful scaffolds only.

Severity: HIGH for scientific claims; MEDIUM for prototype engineering.

### 10. Reproducibility and packaging are incomplete

`pyproject.toml` declares only `numpy` as a runtime dependency and only `pytest` as a dev dependency, while many modules import `torch`, `torchvision`, `transformers`, `sentence-transformers`, `sklearn`, and other optional scientific tooling. The test run reports pass, but also emits a native Windows crash trace involving `torchvision/transformers`.

Impact:

- A clean external environment is unlikely to reproduce all claimed modules.
- Dependency groups should separate core, bio, structure, ML, and dev/test extras.

Severity: MEDIUM.

## Positive Findings

- The core 0.884550 narrow result is reproducible through the explicit legacy benchmark view.
- `ToposLogicStrategy` no longer directly returns the stored `treats` edge for Drug->Disease pairs.
- The system is deterministic enough for the read-only AUROC checks I ran.
- The direct mechanistic paths that do exist are interpretable, for example EGFR->NSCLC, BRAF->Melanoma, CDK4/CDK6->Breast_Cancer, BRCA1/BRCA2->Ovarian_Cancer, and JAK2->Myelofibrosis.
- The concept of category/path-based reasoning over a typed biomedical graph is scientifically plausible as an early-stage ranking approach.

## Recommended Claim Language

Do not claim:

- "Clinically validated drug repurposing oracle."
- "No leakage" without specifying the strategy set and split protocol.
- "AUROC 0.8846 on tier1.db" without stating that the `legacy/as_loaded` view is 28 drugs x 8 diseases and excludes much of the SQLite database.
- "Drug design works" or "ABPP/Boltz validates predictions" from current code.

More defensible wording:

> KOMPOSOS-IV-PHARM currently implements a research prototype for categorical reasoning over a curated drug-target-disease knowledge graph. On the explicit `legacy/as_loaded` benchmark view of `tier1.db` (28 drugs, 8 diseases, 11 approved indication edges), a seven-strategy simple-average scorer reproduces AUROC 0.884550. On a full typed read of the SQLite database (78 drugs, 20 diseases, 16 approved indication edges), the same scorer yields AUROC 0.794325, and a leave-one-approved-edge-out protocol yields AUROC 0.772081. These are internal retrospective ranking metrics under open-world negative assumptions and require stronger leakage control, external validation, and data provenance before translational claims.

## Required Remediation Before External Scientific Release

1. Keep the fixed `BioDomainLoader` behavior under regression test, and add a strict mode that fails if morphism endpoints are missing typed object rows.
2. Add confidence intervals and additional ranking metrics to the benchmark outputs.
3. Remove all direct Drug->Disease test labels from the graph during prediction. Report leave-one-edge-out, disease-level holdout, temporal holdout, and all-direct-labels-removed results.
4. Add confidence intervals by bootstrap or DeLong-style methods and report AUPRC, enrichment@K, Hits@K, MRR, calibration, and baselines.
5. Separate "approved indication", "repurposing hypothesis", "contraindication", "side effect", and "unknown" labels.
6. Add data provenance fields to every object and morphism in the persisted DB, not only Python comments.
7. Add mechanistic completeness checks for each positive indication. Canonical missing biology should include at least BCR-ABL->CML and AMPK/metabolic links for Type2_Diabetes if these labels remain in the benchmark.
8. Repair `data/drugs/loader.py` and add a reproducible build script for `tier1.db`.
9. Move placeholder, mock, and fallback scientific modules behind explicit experimental flags. Any use of fallback scoring should be visible in outputs.
10. Add dependency extras and environment lockfiles for core, bio-audit, and structure-prediction workflows.

## Final Verdict

The repo should pass as an exploratory software prototype, but it should not pass an external biomedical rigor audit for drug repurposing claims yet. The main blockers are not category theory; they are dataset definition, loader correctness, leakage-resistant validation, provenance, and missing external/temporal validation.
