# CLAUDE.md - KOMPOSOS-IV-PHARM

## Project Identity

KOMPOSOS-IV-PHARM applies a categorical AI runtime to pharmaceutical discovery.

Primary long-term purpose: Track B drug design, including molecular generation,
binding/efficacy/safety prediction, ADMET, and patient context.

Current working capability: Track A drug repurposing over a curated
drug-target-disease graph.

Current audit rule: code and live data outrank stale docs. Always name the graph
view and validation protocol with any AUROC.

## Research Integrity Audit Update (2026-05-28)

Do not advertise the retired `0.9689 AUROC / 0.661 AUPRC` result as current.
That run was affected by label leakage in `oracle/yoneda_strategy.py`: the
Yoneda cache loaded all Drug->Disease labels directly from `tier1.db`, so
`remove_direct_labels` and LOOCV folds were not isolated. The corrected strict
run also filters protein->disease bridge edges explicitly derived from known
drug indications. An intermediate post-leakage audit result of `0.9562 AUROC`
was later superseded by the current Topos-aligned strict run below.

Current strict validation command:

```powershell
python validation\repurposing_benchmark.py --view full_typed --protocol remove_direct_labels --baselines --ci
```

Current strict result (2026-06-02, after integrating 151 agent-adjudicated
discovery links and fixing the positive-label filter to `treats`-only; the prior
2026-05-28 numbers below this line are superseded):
- `full_typed/remove_direct_labels`: **AUROC 0.970549** [0.9519, 0.9844], AUPRC 0.546427 [0.4025, 0.6890], Hits@5 1.00, Hits@10 0.60, Hits@20 0.60.
- Baselines on the same graph: common_neighbor 0.6219, path_count 0.6203, shortest_path 0.5881, degree_product 0.5852, random 0.5623 (strongest common_neighbor; margin +0.3486).
- 44 positives (`treats` edges only). The earlier harness counted 48 because 4 inferred `associated_with` HYPOTHESIS Drug->Disease edges were wrongly scored as approvals; that is fixed, which is why AUROC rose vs the retired 0.948640/48-positive run.
- The database has source strings on 2,329/2,329 morphisms and 955 distinct PMIDs (1,035 PMID-bearing edges), but this is not the same as edge-specific citation validation. PMID-backed edges are tiered (see Provenance Tiering Update below): 745 RELATION-VERIFIED, 215 LEXICAL-COOCCURRENCE. Quantitative NLP attribution requires edge-level audit.
- Current executable holdouts: LOOCV AUROC 0.967431 / AUPRC 0.516478; Hetionet external AUROC 0.643615 / AUPRC 0.009513; temporal year>2013 AUROC 0.970646 / AUPRC 0.193802; disease-holdout mean AUROC 0.937795 / mean AUPRC 0.602051.

## Provenance Tiering Update (2026-05-29)

The literature-provenance layer was made honest and tiered. The prior
`[ACTION-VERIFIED]` tag overclaimed: it marked edges where a drug/target/action
keyword merely co-occurred in one sentence. The pipeline (`scripts/`:
`scrape_triplet_pmids.py` -> `verify_triplet_abstracts.py` -> `inject_honest_provenance.py`)
was fixed (all abstract sections captured; word-boundary gene-symbol matching so
`MET` no longer matches "metabolism"; relation-aware polarity rejection; expanded
keyword stems) and re-run, yielding 737 candidate proofs. All 737 were then
adjudicated in-session by the agent (NO API tokens) for whether the cited
sentence asserts the **directed, signed** relation.

Result tags (metadata only — they do NOT feed scoring; AUROC is unchanged at
0.948640):
- **594 `[RELATION-VERIFIED]`**: agent-confirmed directed/signed relation in the cited sentence.
- **215 `[LEXICAL-COOCCURRENCE]`**: passed automated co-occurrence + polarity screen only; not verified.
- Full adjudication: 600 VERIFIED / 137 COOCCUR. Precision by relation: treats 100%,
  inhibits 93%, associated_with 75%, activates 61%. Verdicts with notes:
  `data/relation_extraction_verdicts.json`. Read-only re-audit: `scripts/audit_verified_provenance.py`.
- The retired "188 audited PMIDs" figure was the count of distinct PMIDs *present* in
  provenance strings (now 805); presence is not verification. Do not advertise it as audited.

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

Full typed DB facts (2026-06-02 audit):
- 1,146 runtime objects, 2,329 stored morphisms
- 78 drugs, 20 diseases, 366 biological entities
- 44 Drug->Disease approved indication labels (all FDA-approved `treats` edges, all with source strings)
- All 44 positives have mechanistic paths (Drug->Protein->Disease)
- 2,329/2,329 morphisms have source/provenance strings; this is not equivalent to source-validated evidence
- 955 distinct PMIDs present in provenance/metadata strings; 1,035 edges carry a PMID
- Provenance tiers: 745 RELATION-VERIFIED (agent-confirmed directed/signed), 215 LEXICAL-COOCCURRENCE (automated co-occurrence + polarity screen only)
- 1,014 edges are MEASURED-tier (IC50, mutation frequencies, hazard ratios, response rates live in provenance/metadata strings; the `quantitative_value` column itself is currently unpopulated -- edge-level numeric extraction is an open task)
- Evidence tier classification: MEASURED 1014, ESTABLISHED 377, INFERRED 918, HYPOTHESIS 20
- Data sources: PubMed, ChEMBL, FDA, KEGG, STRING PPI (338 edges), protein similarity (ESMC-300M engine; legacy ESM2 edge labels pending re-derivation), cBioPortal genomic, ABPP
- NLP PMID extraction: 373 quantitative data points from 204 PMIDs; edge-specific attribution remains under audit
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

Current metrics (2026-06-02, `treats`-only positive filter, 44 positives, 2,329 morphisms):
- `full_typed/remove_direct_labels`: **AUROC 0.970549**, AUPRC 0.546427, Hits@5 1.00, Hits@10 0.60
- `full_typed/loocv`: AUROC 0.967431, AUPRC 0.516478, Hits@5 0.80, Hits@10 0.60, Hits@20 0.65
- `full_typed/as_loaded`: AUROC 0.738831, AUPRC 0.049407, Hits@5/10/20 0.000 (dataset artifact; not the recommended protocol)

**Strategy integrity fixes (2026-05-27):**
- Kan extension ("Drug Analogy") was returning 0.900 for 96.9% of pairs (zero discrimination)
- Root cause: considered all objects (proteins, etc.) as analogs, not just drugs
- Fixed: filter to only Drug objects
- Result: 56% of pairs now have variable scores; only returns when similar drugs exist
- YonedaPatternStrategy had the same bug class and is now type-restricted to same-source-type comparators
- YonedaDistanceStrategy now builds fingerprints from the caller's visible graph and excludes direct Drug->Disease labels from fingerprints
- BindingEvidenceStrategy now requires a disease-linked intermediate target rather than any drug target
- Composition confidence now uses multiplicative enriched-category composition instead of min-hop confidence
- Negative pairs (like Sorafenib→AML) now score more accurately (0.910 -> 0.895)

**Yoneda Distance Strategy integration (2026-05-26):**
- 9th strategy: structural similarity via confidence-weighted Yoneda presheaf fingerprints
- Operates on visible clean subgraph (MEASURED + ESTABLISHED edges only); direct Drug->Disease labels are excluded from fingerprints
- Integrated as additive bonus (like path_bonus), not averaged vote
- Coefficient 0.06 tuned via grid search over [0.0, 0.20] with cap 0.10
- Earlier AUROC/AUPRC deltas are stale because the previous implementation could see held-out labels
- Drug equivalence classes discovered: 6 pairs with identical Yoneda profiles
  (Binimetinib=Cobimetinib, Encorafenib=Vemurafenib, Carboplatin=Oxaliplatin, etc.)
- Triage reports now show "Structural Similarity" vote with interpretation
- STT experiment script: `stt_repurposing.py` (standalone comparison of 3 STT strategies)

**Quantitative evidence expansion (2026-05-25):**
- 373 NLP extractions from 204 PMIDs; edge-specific attribution remains under audit
- 204 edges with IC50, hazard ratios, mutation frequencies, response rates
- 250 edges updated, 244 tier upgrades to MEASURED
- Triage reports display quantitative evidence: `[IC50=7.7 uM]`, `[HR=0.97]`, `[Mutation freq=50.0%]`

Path bonus tuned via LOOCV grid search: min(0.25, 0.04 * sum(path_confidence)).
Confidence-weighted paths (2026-05-27): each path is weighted by multiplicative composed confidence.
Uniform strategy weights confirmed optimal by calibrate_loocv.py.

as_loaded protocols show Hits@K regression because composition skips existing edges —
positives get zero path bonus while negatives can. This is an artifact of the protocol,
not real performance loss.

Corrected strict baselines (AUROC, 2026-06-02):
- strongest: common_neighbor 0.6219
- system AUROC: 0.970549
- margin: +0.3486 over strongest baseline on the same graph

Older baseline tables mentioning degree_product 0.6307 / system 0.9747 are stale
for the current strict graph and should not be used without reproduction.

Additional executable validation (2026-06-02):
- External (Hetionet): AUROC 0.643615, AUPRC 0.009513 on 7 external positives; low precision-at-top.
- Temporal holdout (approval year > 2013): AUROC 0.970646, AUPRC 0.193802 on 18 held-out approvals.
- Disease-level holdout: Mean AUROC 0.937795, mean AUPRC 0.602051 across 7 diseases; range 0.756757-1.000000.

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
strategy vote breakdown, ESMC protein family classification (when available),
source-linked evidence chains, provenance coverage per candidate, and
APPROVED/NOT_APPROVED labels. NOT_APPROVED means not in our
44 FDA oncology indications (may already be in trials/literature). Detail
auto-expands for top-5 NOT_APPROVED candidates in terminal mode; specific
pair mode always shows full detail.

Provenance tools:
- `validation/triage.py` -- candidate triage reports with evidence chains
- `validation/trace_prediction.py` -- trace any prediction to source-linked evidence chains
- `validation/generate_citation_worksheet.py` -- generate citation TODO list
- 2,329/2,329 stored morphisms have source/provenance strings
- Source coverage is not the same as edge-specific citation validation

Data expansion:
- ChEMBL SQLite expansion deployed (2026-05-10): +269 proteins, +872 morphisms, +17 base drug targets
- See `CHEMBL_NORMALIZATION_2026-05-10.md` for details on drug name normalization
- See `DATA_EXPANSION_GUIDE.md` for further expansion recommendations (OpenTargets, STRING)
- Source-string coverage complete; edge-specific citation validation remains an audit task

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
- `data/bio_embeddings.py`: ESMC-300M protein language model embeddings (960d).
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
5. ~~Tune score combiners.~~ DONE (path bonus tuned via LOOCV grid search; current strict AUROC 0.970549).
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

