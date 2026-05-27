# KOMPOSOS-IV-PHARM: Technical Overview

**Author**: James Ray Hawkins
**Date**: 2026-05-13
**License**: Apache 2.0 / Commercial dual license
**Python**: 3.10+

---

## 1. Purpose

KOMPOSOS-IV-PHARM is a categorical AI runtime applied to pharmaceutical
discovery. The current working capability is drug repurposing (Track A): ranking
existing drugs for diseases using mechanistic pathway evidence over a curated
knowledge graph.

Track B (drug design: molecular generation, binding prediction, ADMET) is a
long-term goal with scaffolding code but no scientific validation in this repo.

---

## 2. Architecture

```
Layer 5: OPTIMUS          Categorical gradient descent (self-refinement)
Layer 4: COG              Cognitive co-processor (claim verification)
Layer 3: Infinity-Cosmos  Higher structure (2-cells, fibrations, Yoneda, Kan)
Layer 2: KOMPOSOS-IV      Category runtime (objects, morphisms, enrichment, persistence)
Layer 1: ORION            Plugin framework (bridges, events, hot-loading)
```

**Key code areas:**

| Directory | Purpose |
|-----------|---------|
| `core/` | Category runtime: `Category` class, types, enrichment, persistence, hooks |
| `oracle/` | Prediction strategies: 8 production (incl. binding evidence) |
| `domains/bio/` | `BioDomainLoader` -- loads tier1.db into Category |
| `data/store.py` | `KomposOSStore` -- SQLite backend API |
| `data/drugs/` | `build_tier1.py` (reproducible build), `tier1_manifest.json` |
| `validation/` | Benchmark harness, triage CLI, trace tools |
| `tests/` | 156 tests (all passing) |

---

## 3. Core Runtime

The `Category` class (`core/category.py`) is an enriched category over a
quantale (partially ordered monoid).

```python
from core.category import Category

cat = Category("DrugRepurposing")
cat.add("Sorafenib", type_name="Drug")
cat.add("VEGFR2", type_name="Receptor")
cat.add("RCC", type_name="Disease")

cat.connect("Sorafenib", "VEGFR2", name="inhibits", confidence=0.95)
cat.connect("VEGFR2", "RCC", name="driver_of", confidence=0.85)

paths = cat.find_paths("Sorafenib", "RCC", max_length=4)
```

**Key types:**
- `Object`: name, type_name, metadata, optional embedding, provenance
- `Morphism`: name, source, target, confidence (float 0-1), provenance
- `Path`: ordered sequence of morphisms
- `HigherMorphism`: 2-cells (morphisms between morphisms)

**Enrichment:** Multiplicative quantale by default: `conf(A->C) = conf(A->B) * conf(B->C)`.

**Persistence:** All operations auto-persist to SQLite via `KomposOSStore`.

**Loader rule:** `KomposOSStore.list_objects()` defaults to `limit=100`. The
`BioDomainLoader` explicitly loads all rows. Never use the default limit for
production graphs.

---

## 4. Production Strategies

The benchmark harness uses exactly 8 strategies (`oracle/strategies.py`,
`oracle/binding_strategy.py`, `make_strategies()`):

| # | Strategy | Alone AUROC | Without AUROC | Role |
|---|----------|----------:|-------------:|------|
| 1 | **composition** | 0.969 | 0.929 (-0.045) | Count Drug->Protein->Disease paths. **Dominant.** |
| 2 | **topos_logic** | 0.947 | 0.970 (-0.004) | Subobject classifier truth values |
| 3 | **kan_extension** | 0.497 | 0.966 (-0.008) | Left Kan extension along forgetful functor |
| 4 | **yoneda_pattern** | 0.520 | 0.974 (~0) | Yoneda embedding similarity |
| 5 | **type_heuristic** | 0.500 | 0.974 (0) | Type-based heuristic matching |
| 6 | **structural_hole** | 0.500 | 0.974 (0) | Burt structural holes |
| 7 | **fibration_lift** | 0.500 | 0.974 (0) | Cartesian lift in fibrations |
| 8 | **binding_evidence** | -- | -- | Molecular/chemistry binding evidence |

Strategies 5-7 are inactive on the current graph (contribute zero signal) but
are retained for future graph expansions.

Strategy 8 (binding_evidence) aggregates 5 molecular bridges: ABPP experimental
IC50 data, Boltz2 heuristic binding, drug-likeness (Lipinski), drug-target
molecular compatibility, molecular bridge scorers, and Pfam domain matching.
Drug properties are PubChem-verified (46/68 drugs corrected 2026-05-13).

Additional experimental strategies exist in `oracle/` (geometric homotopy,
boundary detection, cellular dynamics, etc.) but are not used in the benchmark
harness.

---

## 5. Scoring Formula

From `validation/repurposing_benchmark.py`:

```python
def score_pair(strategies, source, target):
    votes = []
    composition_count = 0
    for strategy in strategies:
        preds = strategy.predict(source, target)
        if preds:
            best = max(preds, key=lambda p: p.confidence)
            votes.append((strategy.name, best.confidence))
            if strategy.name == "composition":
                composition_count = len(preds)

    if not votes:
        return 0.0, votes

    base = sum(c for _, c in votes) / len(votes)
    path_bonus = min(0.25, 0.10 * composition_count)
    return min(1.0, base + path_bonus), votes
```

1. Each strategy predicts independently; take best confidence per strategy
2. Average all strategy confidences: `base = mean(confidences)`
3. Add path bonus: `min(0.25, 0.10 * composition_count)`
4. Final score: `min(1.0, base + path_bonus)`

Path bonus was tuned via LOOCV grid search. Uniform strategy weights confirmed
optimal by `calibrate_loocv.py`.

---

## 6. Knowledge Graph

**Source:** `data/drugs/tier1.db`
**Reproducible build:** `python data/drugs/build_tier1.py` from `tier1_manifest.json`
**SHA256:** `0BA4A7E01BBA3E1E52A03CD7765A3E6523618F439AB8A90ED4BD6B4BD95BC8E6`

| Fact | Value |
|------|-------|
| Objects | 1143 |
| Morphisms | 1260 |
| Drugs | 78 |
| Diseases | 20 cancer types |
| Proteins | 366 |
| ExternalCompound nodes | 679 (ChEMBL endpoints) |
| Approved indications | 44 (all FDA-approved, all with PMIDs) |
| Provenance | 1260/1260 (100%): PMIDs + ChEMBL IDs |
| Mechanistic paths | All 44 positives have Drug->Protein->Disease paths |
| Orphan objects | 0 |
| Missing endpoints | 0 |

**Object types:** Drug, Disease, Receptor, Signaling, Transcription,
TumorSuppressor, Apoptosis, Oncogene, DNARepair, CellCycle, Regulator,
Splicing, Epigenetic, Metabolic, Structural, Chaperone, Transporter, Ligand,
Enzyme, Marker, ExternalCompound.

**Edge types:** treats, targets, inhibits, activates, phosphorylates, binds,
driver_of, associated_with, interacts, cooperates, regulated_by, pathway_crosstalk,
sequesters, ubiquitinates, activated_by, activity (ChEMBL).

---

## 7. Validation Protocols

### 7.1 Named Benchmark Views

```powershell
python validation\repurposing_benchmark.py --view <view> --protocol <protocol>
```

| View | Protocol | AUROC | AUPRC | Hits@5 | Pairs | Positives |
|------|----------|------:|------:|-------:|------:|----------:|
| legacy | as_loaded | 0.931 | 0.465 | -- | 1320 | 36 |
| full_typed | as_loaded | 0.887 | 0.135 | 0.00 | 1560 | 44 |
| full_typed | remove_direct_labels | 0.940 | 0.431 | 0.60 | 1560 | 44 |
| full_typed | loocv | 0.974 | 0.530 | 1.00 | 1560 | 44 |

- `legacy`: first 100 objects only (historical hurdle)
- `full_typed`: all objects loaded, typed
- `as_loaded`: use graph as-is (includes direct Drug->Disease edges)
- `remove_direct_labels`: remove all direct Drug->Disease edges before scoring
- `loocv`: leave one positive edge out per fold

The scientifically valid protocols are `loocv` and `remove_direct_labels`.
`as_loaded` shows Hits@K=0.00 as an artifact (composition skips existing edges).

Add `--ci` for bootstrap 95% confidence intervals, `--baselines` for baseline
comparisons.

### 7.2 Baselines (LOOCV, corrected 2026-05-11)

| Baseline | AUROC |
|----------|------:|
| shortest_path | 0.931 |
| common_neighbor | 0.918 |
| path_count | 0.596 |
| degree_product | 0.474 |
| random | 0.469 |
| **System** | **0.974** |
| **Margin** | **+0.043** |

### 7.3 Additional Validation (reported, not audit-reproduced)

| Validation | AUROC | Notes |
|------------|------:|-------|
| External (Hetionet) | 0.744 | 7 held-out Hetionet-confirmed pairs |
| Temporal (2013 cutoff) | 0.959 | 22 post-2013 FDA approvals held out |
| Disease-level holdout | 0.877 mean | 7 diseases, range 0.615-0.996 |

### 7.4 ClinicalTrials.gov Cross-Check

30 top repurposing candidates verified against ClinicalTrials.gov and PubMed:
- 19/30 (63%) have human clinical trials (IN_TRIALS)
- 9/30 (30%) have preclinical/observational research (PRECLINICAL)
- 2/30 (7%) have no significant prior evidence (NOVEL)

### 7.5 OpenTargets Experiment

Tested cancer-filtered OpenTargets import at 3 score thresholds (0.5, 0.6, 0.7).
All degraded AUROC (0.974 -> 0.952-0.968). The curated graph has higher
signal-to-noise. Decision: not deployed.

---

## 8. Candidate Triage CLI

```powershell
python validation\triage.py Melanoma              # disease-first
python validation\triage.py --drug Metformin       # drug-first
python validation\triage.py Melanoma --drug Vemurafenib  # specific pair
python validation\triage.py Melanoma --json        # JSON output
python validation\triage.py Melanoma --markdown    # Markdown output
python validation\triage.py Melanoma --all         # all candidates
python validation\triage.py Melanoma --top 20      # top 20
```

Reports include:
- Self-check: 44/44 approved indications recoverable
- Ranked candidates with scores
- Strategy vote breakdown per candidate
- Mechanistic Drug->Protein->Disease chains with PMIDs
- Provenance coverage per candidate (cited edges / total edges)
- APPROVED / NOT_APPROVED labels

NOT_APPROVED means not in our 44 FDA-approved oncology indications. Candidates
may already be in clinical trials or published literature.

---

## 9. Reproducible Build

```powershell
python data\drugs\build_tier1.py
```

Builds `tier1.db` from `tier1_manifest.json`. The manifest contains all objects,
morphisms, and provenance. The build is deterministic: same manifest always
produces the same database.

Verify: `pytest tests\test_repurposing_benchmark.py -q` checks object counts,
morphism counts, AUROC values, and manifest SHA256 against the current database.

---

## 10. Limitations and Honest Claims

**What the system does well:**
- Ranks drug-disease pairs with mechanistic chains and citations
- 63% of top candidates validated as already in human clinical trials
- 100% edge provenance (every edge has a PMID or ChEMBL ID)
- Reproducible: deterministic build, frozen manifest, 156 passing tests

**What the system does not do:**
- Clinical decision support
- Patient-specific predictions (no genomics, tumor profiling)
- Bioavailability or ADMET modeling
- Prospective validation (no prediction tested then confirmed)
- Novel drug design (Track B is scaffolding only)

**Honest AUROC interpretation:**
- +0.043 over strongest graph baseline is a modest margin
- The 44-positive set is small; CIs are [0.965, 0.983]
- Unlabeled pairs are open-world unknowns, not confirmed negatives
- Value is mechanistic chains + provenance + triage, not raw accuracy

---

## 11. Key Files

| File | Purpose |
|------|---------|
| `validation/repurposing_benchmark.py` | Canonical AUROC benchmark harness |
| `validation/triage.py` | Candidate triage CLI |
| `validation/trace_prediction.py` | Trace predictions to evidence chains |
| `validation/ablation_study.py` | Strategy ablation experiments |
| `validation/ablation_results.json` | Frozen ablation results |
| `validation/repurposing_benchmark_manifest.json` | Frozen benchmark counts and metrics |
| `data/drugs/tier1.db` | Production knowledge graph |
| `data/drugs/build_tier1.py` | Reproducible DB build |
| `data/drugs/tier1_manifest.json` | Canonical graph manifest |
| `core/category.py` | Category runtime |
| `oracle/strategies.py` | 7 graph-topology scoring strategies |
| `oracle/binding_strategy.py` | Binding evidence strategy (ABPP, Boltz2, drug props) |
| `data/drugs/drug_properties.py` | PubChem-verified molecular properties for 78 drugs |
| `domains/bio/loader.py` | BioDomainLoader |
| `tests/test_repurposing_benchmark.py` | Regression tests |
| `CURRENT_STATE.md` | Project status |
| `MEMORY.md` | Quick reference for agents |
| `CLAUDE.md` | Operating instructions |
