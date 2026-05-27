# STT Drug Repurposing: Full Roadmap

**Date:** 2026-05-26
**Author:** James Ray Hawkins + Claude
**Depends on:** STT_REPURPOSING_PLAN.md (Project 1 must run first)

---

## Project 1: Standalone STT Experiment (NEXT SESSION)

**Plan:** STT_REPURPOSING_PLAN.md
**Output:** `stt_repurposing.py` -- standalone script
**Measures:** AUROC for Yoneda, Transport, Rezk vs existing 8 strategies
**Decision gate:** Do STT strategies add signal? Which ones? On what subset?

---

## Project 2: Integration Into Oracle Pipeline

**Depends on:** Project 1 results
**Condition:** At least one STT strategy shows independent predictive value

### 2a: Rezk Completion as Preprocessing

Rezk completion doesn't score pairs -- it changes the graph. If Project 1
finds that diseases merge into meaningful equivalence classes, this should
run at DB load time before any scoring happens.

**Changes:**
- `domains/bio/loader.py`: After loading tier1.db, compute Yoneda distance
  between all disease pairs using MEASURED+ESTABLISHED edges only
- Merge diseases with distance < threshold (threshold determined by Project 1)
- Merged diseases inherit all drug labels from every member of the class
- All 8 existing strategies automatically benefit from richer label set

**Files modified:**
- `domains/bio/loader.py` -- add `rezk_complete_diseases()` call after load
- `core/rezk.py` (new) -- equivalence class computation, extracted from
  stt_repurposing.py

**Validation:**
- Run benchmark before and after Rezk preprocessing
- Report which diseases merged and what new labels appeared
- If AUROC drops, the threshold is too aggressive -- tighten it

### 2b: Yoneda Distance as Strategy 9

If Yoneda distance shows independent AUROC on the clean subgraph, add it
as a 9th strategy in the oracle ensemble.

**Changes:**
- `oracle/yoneda_strategy.py` (new) -- implements InferenceStrategy interface
- `validation/repurposing_benchmark.py` -- add to `make_strategies()` list

**Implementation:**
```python
class YonedaStrategy(InferenceStrategy):
    """Score Drug-Disease pairs by Yoneda distance to known treatments."""

    def __init__(self, category, clean_edges):
        self.category = category
        self.clean_cat = build_clean_category(clean_edges)
        self.fingerprints = precompute_all_fingerprints(self.clean_cat)

    def predict(self, drug, disease) -> Prediction:
        known_drugs = drugs_treating(disease)
        if not known_drugs:
            return Prediction(score=0.0, confidence=0.0)
        best_dist = min(yoneda_distance(drug, kd, self.fingerprints)
                        for kd in known_drugs)
        score = 1.0 - best_dist
        return Prediction(score=score, confidence=score,
                          explanation=f"Yoneda distance {best_dist:.3f} "
                                     f"from nearest known drug")
```

**Key detail:** The strategy must use the clean subgraph internally but
accept the full category for interface compatibility. The evidence-tier
filtering happens inside the strategy, not in the harness.

### 2c: Fibration Transport as Strategy 10

If transport scores show value, add as 10th strategy.

**Changes:**
- `oracle/transport_strategy.py` (new) -- implements InferenceStrategy
- `validation/repurposing_benchmark.py` -- add to `make_strategies()`

**Implementation:**
```python
class TransportStrategy(InferenceStrategy):
    """Score Drug-Disease pairs by fibration transport across diseases."""

    def predict(self, drug, disease) -> Prediction:
        # Find diseases where drug has measured connections
        source_diseases = diseases_connected_to_drug(drug, self.clean_cat)
        if not source_diseases:
            return Prediction(score=0.0, confidence=0.0)

        # Transport along base morphisms (shared protein Jaccard)
        total = 0.0
        paths = []
        for src_disease in source_diseases:
            strength = base_morphism_strength(src_disease, disease, self.clean_cat)
            if strength > 0:
                total += strength
                paths.append(f"{src_disease} -[{strength:.2f}]-> {disease}")

        score = min(total, 1.0)
        return Prediction(score=score, confidence=score,
                          explanation=f"Transport via: {'; '.join(paths)}")
```

### 2d: Strategy Weight Calibration

After adding strategies 9-10 (or 9-11), re-run `calibrate_loocv.py` to
find optimal weights. The current 8 strategies use uniform weights -- that
may not be optimal when STT strategies are added.

**Possible outcomes:**
- STT strategies get high weight, existing drop -- STT is replacing path noise
- STT strategies get low weight -- they're redundant with existing
- Mixed -- each STT strategy covers a different blind spot

---

## Project 3: 78% Novel Reservoir Ranking

**Depends on:** Project 2b (Yoneda strategy integrated)
**Condition:** Yoneda distance is a validated similarity metric

### Problem

~78% of PHARM's Drug-Disease candidates have no literature backing (the
ClinicalTrials.gov cross-check found 63% IN_TRIALS, 30% PRECLINICAL, 7% NOVEL).
The novel candidates are currently unranked -- they show up in triage but
without evidence chains.

### Solution

Use Yoneda distance to rank novel candidates by structural similarity to
validated drug-disease pairs:

1. For each novel candidate (Drug_X, Disease_Y):
   - Find the nearest VALIDATED pair (Drug_V, Disease_Y) by Yoneda distance
   - Score = 1 - yoneda_distance(Drug_X, Drug_V)
   - Explanation: "Drug_X has Yoneda distance 0.12 from Drug_V, which is
     FDA-approved for Disease_Y. They share N MEASURED protein targets."

2. Rank all novel candidates by this score

3. Output a prioritized list for researchers: "these novel candidates are
   structurally most similar to things we KNOW work"

**Output:** `stt_novel_ranking.py` or integrate into `validation/triage.py`

**Validation:** Check if the top-ranked novel candidates have any external
support (recent publications, clinical trials started after our data cutoff,
mechanistic plausibility). This is manual validation by a researcher.

---

## Project 4: Chromosomal Collapse / Segal Defect Scoring

**Depends on:** Projects 1-2 (STT infrastructure working)
**Separate intellectual project from Projects 1-3**

### The Idea

Some cancers are driven by point mutations on coherent pathways (SMT model).
Others are driven by chromosomal catastrophe -- chromothripsis, whole-genome
doubling, massive structural rearrangement. The current scoring system treats
all diseases the same. It shouldn't.

### Segal Defect Computation

For each disease D in tier1.db, measure how "categorically coherent" its
local neighborhood is:

```python
def segal_defect(disease, category):
    """Count composition ambiguities in disease's local subgraph."""
    proteins = proteins_connected_to(disease, category)
    defect = 0
    for p1 in proteins:
        for p2 in proteins_reachable_from(p1, category):
            for p3 in proteins_reachable_from(p2, category):
                # Check: does direct p1->p3 confidence match composed p1->p2->p3?
                direct = confidence(p1, p3, category)
                composed = min(confidence(p1, p2, category),
                              confidence(p2, p3, category))
                if direct and abs(direct - composed) > TOLERANCE:
                    defect += 1
    return defect
```

High defect = the protein interaction network around this disease has
contradictory paths. This correlates with chromosomal instability.

### Two-Regime Scoring

- **Low defect diseases:** Existing 8 + STT strategies work. Pathways are
  coherent, path-walking is valid.
- **High defect diseases:** Need different scoring. Drugs that target
  structural invariants of instability (mitotic checkpoint, proteostasis,
  cGAS-STING) should score higher. These are the "collapse co-limits."

### Implementation

```python
# Classify diseases
for disease in diseases:
    defect = segal_defect(disease, clean_cat)
    regime = 'coherent' if defect < THRESHOLD else 'collapsed'

# Score differently per regime
if regime == 'coherent':
    score = existing_11_strategies(drug, disease)
elif regime == 'collapsed':
    score = collapse_strategy(drug, disease)
```

**Collapse strategy scores drugs by whether they target:**
- Mitotic checkpoint proteins (KIF18A, PLK1, centrosome clustering)
- Proteotoxic stress pathways (HSP90, autophagy)
- cGAS-STING immune sensing (IFNG, CXCL12, CXCR4)

These are encoded as "structural dependency" morphisms in the category.

### Output

`stt_collapse_scoring.py` -- standalone script that:
1. Computes Segal defect for all 20 diseases
2. Reports which diseases are "collapsed" vs "coherent"
3. Runs two-regime scoring
4. Compares AUROC: single-regime vs two-regime

### Validation

- Do high-defect diseases correspond to known chromosomally unstable cancers?
- Do collapse-targeting drugs (Mebendazole, Disulfiram, Chloroquine) rank
  higher for high-defect diseases under two-regime scoring?
- Does two-regime scoring improve AUROC over single-regime?

---

## Project 5: Crystal Dreamer Bridge (Drug Design)

**Depends on:** Project 4 (collapse signatures), KOMPOSOS-III-LAMBDA-max-3D
**Long-term project -- not immediate**

### The Idea

Move from drug REPURPOSING (which existing drug works?) to drug DESIGN
(what new molecule would work?). Uses the Crystal Dreamer inverse design
logic from KOMPOSOS-III-LAMBDA-max-3D.

### Functor Chain

```
Patient Category -> Collapse Signature -> Molecular Constraints -> Drug Candidates

F1: PatientCat -> CollapseCat
    Patient mutations map to Segal defect pattern
    (which compositions are broken, which dependencies remain)

F2: CollapseCat -> ConstraintCat
    Collapse pattern maps to structural vulnerabilities
    (mitotic checkpoint dependency -> microtubule constraints,
     proteotoxic stress -> HSP90 binding pocket geometry)

F3: ConstraintCat -> MoleculeCat
    Constraints map to molecular structures via inverse design
    (Crystal Dreamer: given constraints, enumerate molecules that satisfy them)
```

Each functor is computable. F1 uses Project 4 infrastructure. F2 requires
mapping collapse patterns to protein structure targets (AlphaFold3 binding
pockets). F3 is Crystal Dreamer adapted from materials to drug molecules.

### Prerequisites

- Project 4 working (Segal defect, collapse classification)
- AlphaFold3 protein structure access (or precomputed binding pockets)
- Crystal Dreamer logic adapted from lattice constraints to molecular constraints
- Docking/scoring infrastructure (AutoDock Vina or similar)

### Output

Given a patient's mutation profile:
1. Compute collapse signature (F1)
2. Identify structural vulnerabilities (F2)
3. Generate candidate molecules (F3)
4. Score against patient's specific protein structures
5. Plan synthesis routes from available precursors

This is the CRYSTAL_DREAMER_DRUG_INTEGRATION.md vision, but grounded in the
categorical infrastructure from Projects 1-4 rather than built from scratch.

---

## Project 6: Platform Protocol (Multi-User)

**Depends on:** Projects 1-5 working single-user
**Infrastructure project -- not immediate**

As described in PLATFORM_PROTOCOL_DESIGN.md. The key insight: everything in
Projects 1-5 runs on one user's Category. The Platform Protocol lets multiple
users contribute morphisms (with differential privacy) to a shared consensus
Category, and Collective OPTIMUS discovers structural patterns across all users.

### Why it's last

Single-user must work first. If STT math doesn't improve predictions for one
user's data, it won't improve predictions for aggregate data. The platform
amplifies signal -- it doesn't create signal that isn't there.

---

## Summary: Execution Order

```
Project 1: Standalone STT experiment (stt_repurposing.py)
    |
    v
Project 2: Integrate what works into oracle pipeline
    |
    v
Project 3: Rank the 78% novel reservoir with Yoneda distance
    |
    v
Project 4: Segal defect / collapse-aware scoring (separate track)
    |
    v
Project 5: Crystal Dreamer drug design (long-term)
    |
    v
Project 6: Platform protocol (multi-user, long-term)
```

Projects 1-3 are a continuous thread: build STT, validate, integrate, apply.
Project 4 branches off after Project 1 -- it uses the same STT math but asks
a different question.
Projects 5-6 are long-term and depend on everything above.

---

## For Each Session

Start by reading:
1. This roadmap (know where you are)
2. The specific project plan (know what to build)
3. `MEMORY.md` (know the current system state)
4. The relevant source files listed in the project plan

Do NOT explore. Do NOT launch agents. Read the plan, write code, run it.
