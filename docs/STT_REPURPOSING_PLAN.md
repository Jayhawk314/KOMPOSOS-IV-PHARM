> **Legacy/historical notice (2026-05-27):** This file is retained for background or session history. It is not the current source of truth for Track A metrics or provenance. Current docs are in `truedocs/`, especially `truedocs/VALIDATION_AND_BENCHMARKS.md` and `truedocs/REPRODUCIBILITY_PROTOCOL.md`. Current strict run: AUROC 0.974694 [0.9606, 0.9855], AUPRC 0.551698 [0.4067, 0.6983], Hits@5/10/20 1.0000/0.6000/0.6000; LOOCV AUROC 0.975916 and AUPRC 0.553703; Hetionet external AUROC 0.634479 and AUPRC 0.009255. Source strings exist on all 5,382 morphisms with 610 PMID identifiers; this is not 100% edge-specific citation validation. Retired or superseded claims in this file should be read as historical.
# STT-Enhanced Drug Repurposing: Implementation Plan

**Date:** 2026-05-26
**Author:** James Ray Hawkins + Claude
**Status:** Ready to implement next session
**Output:** Single file `stt_repurposing.py` in KOMPOSOS-IV-PHARM root

---

## Context

KOMPOSOS-IV-PHARM achieves AUROC 0.956 (main benchmark) on drug repurposing
with 8 path-walking strategies over tier1.db. The system has 5,382 morphisms
but 42.7% are NOISE and 19.4% SPECULATIVE. The 8 strategies weight by
confidence but don't extract structural implications from the graph shape.

KOMPOSOS-IV (in KOMPOSOS-MATH repo) has a Lean 4 library formalizing
Simplicial Type Theory: IsSegal, CovariantFibration, IsRezk, plus a thin
Python mirror in stt_logic.py.

**Goal:** Apply three STT concepts as new scoring strategies to tier1.db,
using evidence tiers to separate signal from noise. Measure whether they
improve predictions. One standalone script, no existing files modified.

---

## The Key Insight: STT Math + Evidence Tiers

The 8 existing strategies ask: "is there a path from Drug to Disease, and
how confident is it?" They're path-walkers on a noisy graph.

The 3 STT strategies ask: "what does the SHAPE of the relationship space
structurally imply?" They extract predictions from the graph's categorical
structure rather than individual paths.

But shape analysis on a graph that's 62% noise/speculative edges will find
noise-shapes. So each STT strategy operates on a **clean subgraph** of only
MEASURED + ESTABLISHED edges (1,355 of 5,382), then optionally incorporates
lower-tier edges with discounting.

---

## What the Script Does

### Step 0: Load Data

```python
# Use existing PHARM infrastructure
import sys
sys.path.insert(0, '.')
from validation.repurposing_benchmark import (
    load_full_typed_view, drug_disease_pairs, pairwise_auroc,
    make_strategies, score_pair
)
from core.category import Category
import sqlite3
```

Load tier1.db via `load_full_typed_view()`. Also open a direct sqlite3
connection for evidence-tier-aware queries:

```sql
SELECT source_id, target_id, name, confidence, evidence_tier
FROM morphisms
WHERE evidence_tier IN ('MEASURED', 'ESTABLISHED')
```

This gives the "clean subgraph" (~1,355 edges) for STT computation.

### Step 1: Build Clean Category

Construct a Category object containing ONLY MEASURED + ESTABLISHED edges.
This is the mathematically trustworthy substrate.

Also build an INFERRED category (adds ~809 edges) for comparison.

```python
clean_cat = Category("clean", db_path=":memory:")
inferred_cat = Category("inferred", db_path=":memory:")

# Populate from tier1.db filtered by evidence_tier
for row in cursor.execute(CLEAN_QUERY):
    clean_cat.add(row.source)
    clean_cat.add(row.target)
    clean_cat.connect(row.source, row.target, confidence=row.confidence, ...)
```

### Step 2: Yoneda Distance Strategy

**What it computes:** For each drug D, its Yoneda presheaf y(D) is the set
of all morphisms INTO D from every other object:

```
y(D)(X) = {m : X -> D | m in morphisms}
```

In tier1.db terms: y(Drug) = all proteins that target it, all pathways it
participates in, all diseases it treats -- but only along MEASURED/ESTABLISHED
edges.

**Drug-drug Yoneda distance:**

```python
def yoneda_fingerprint(drug, category):
    """All incoming morphisms to drug, as a set of (source, relation_type) pairs."""
    return {(m.source, m.name) for m in category.morphisms_to(drug)}

def yoneda_distance(drug1, drug2, category):
    fp1 = yoneda_fingerprint(drug1, category)
    fp2 = yoneda_fingerprint(drug2, category)
    if not fp1 and not fp2:
        return 1.0  # no data = max distance
    symmetric_diff = fp1.symmetric_difference(fp2)
    union = fp1.union(fp2)
    return len(symmetric_diff) / len(union)
```

**Scoring Drug-Disease pair via Yoneda:**

For each (Drug_X, Disease_Y):
1. Find all drugs D_known that are known to treat Disease_Y (the 44 FDA labels)
2. Compute yoneda_distance(Drug_X, D_known) for each
3. Score = max(1 - distance) across all known drugs

Intuition: if Drug_X has Yoneda distance ~0 from a drug known to treat
Disease_Y, then Drug_X relates to everything in the category the same way
that known drug does. It's a structural substitute.

**Disease-disease Yoneda distance (side output):**

Same computation but for diseases. Diseases with distance ~0 on the clean
subgraph have identical MEASURED relational profiles. Report these pairs --
they're either redundant data or a biological discovery.

### Step 3: CovariantFibration Transport Strategy

**What it computes:** The diseases form a base category. Over each disease D,
there's a fiber: the set of (Drug, Protein) pairs connected to D by
MEASURED/ESTABLISHED edges. Transport "lifts" these fibers along
disease-disease morphisms.

**Building the fibration:**

```python
def disease_fiber(disease, category):
    """All (drug, protein) pairs reachable from disease via measured edges."""
    proteins = {m.source for m in category.morphisms_to(disease)
                if object_type(m.source) == 'protein-like'}
    drugs = set()
    for protein in proteins:
        for m in category.morphisms_to(protein):
            if object_type(m.source) == 'Drug':
                drugs.add((m.source, protein))
    return drugs  # set of (drug, protein) tuples
```

**Disease-disease morphisms (base category):**

Two diseases D1, D2 have a base morphism if they share proteins in their
fibers. The morphism strength = Jaccard similarity of their protein sets
(using only MEASURED/ESTABLISHED edges).

```python
def base_morphism_strength(d1, d2, category):
    p1 = {m.source for m in category.morphisms_to(d1) if is_protein(m.source)}
    p2 = {m.source for m in category.morphisms_to(d2) if is_protein(m.source)}
    if not p1 or not p2:
        return 0.0
    return len(p1 & p2) / len(p1 | p2)
```

**Transport scoring:**

For (Drug_X, Disease_Y):
1. Find all diseases D_other where Drug_X is in the fiber (Drug_X treats D_other
   or Drug_X targets a protein connected to D_other)
2. For each D_other, compute base_morphism_strength(D_other, Disease_Y)
3. Transport score = sum of base_morphism_strengths, capped at 1.0

This captures: "Drug_X works for diseases that are mechanistically similar to
Disease_Y, measured by shared protein machinery."

**Axiom verification (auditing):**

- transport_id: transporting along identity (D -> D) must return same fiber.
  Verify for all 20 diseases.
- transport_comp: transporting D1 -> D2 -> D3 must equal D1 -> D3 (if direct
  morphism exists). Count violations -- these flag data inconsistencies.

Report axiom violations as data quality findings.

### Step 4: Rezk Completion Strategy

**What it computes:** Find diseases (or drugs) that are Yoneda-isomorphic on
the clean subgraph, merge them into equivalence classes, re-score on the
quotient graph.

```python
def rezk_equivalence_classes(objects, category, threshold=0.05):
    """Group objects with Yoneda distance < threshold."""
    classes = []  # list of sets
    assigned = set()
    for obj in objects:
        if obj in assigned:
            continue
        equiv_class = {obj}
        for other in objects:
            if other != obj and other not in assigned:
                if yoneda_distance(obj, other, category) < threshold:
                    equiv_class.add(other)
        classes.append(equiv_class)
        assigned.update(equiv_class)
    return classes
```

**Scoring after completion:**

1. Compute disease equivalence classes on clean subgraph
2. For each class, merge all known drug labels (FDA indications) -- if Drug_X
   treats any disease in the class, it treats ALL diseases in the class
3. Re-run the existing 8 strategies on the merged graph
4. Report: which new Drug-Disease predictions appear ONLY after merging?

**Side output:** report which diseases merged. These are either:
- Redundant entries in tier1.db (data quality finding)
- Diseases with identical mechanistic profiles (biological finding)

### Step 5: Combined Scoring and AUROC Comparison

For every Drug-Disease pair (78 drugs x 20 diseases = 1,560 pairs):

```python
scores = {
    'existing_8': score_pair(drug, disease, strategies, category),
    'yoneda': yoneda_score(drug, disease, clean_cat),
    'transport': transport_score(drug, disease, clean_cat),
    'rezk': rezk_score(drug, disease, clean_cat),
    'stt_combined': weighted_average(yoneda, transport, rezk),
    'all_11': weighted_average(existing_8, yoneda, transport, rezk),
}
```

Compute AUROC for each scoring method using `pairwise_auroc()` from the
existing benchmark harness. Use the same 44 positive labels.

### Step 6: Output

Print a comparison table:

```
STT Drug Repurposing Results
============================

AUROC Comparison (full_typed/remove_direct_labels):
  Existing 8 strategies:  0.956
  Yoneda distance only:   ???
  Fibration transport:    ???
  Rezk completion:        ???
  STT combined (3):       ???
  All 11 combined:        ???

Disease Yoneda Equivalence Classes:
  {Melanoma, ...} (distance 0.02)
  ...

Drug Yoneda Equivalence Classes:
  {Imatinib, ...} (distance 0.03)
  ...

Transport Axiom Violations: N
  D1 -> D2 -> D3 != D1 -> D3 for: ...

Top 10 STT-Enhanced Repurposing Candidates
(predicted by STT but NOT by existing 8):
  1. Drug -> Disease  (yoneda=0.85, transport=0.72, rezk=0.90)
  2. ...

Top 10 Candidates Where STT Disagrees With Existing:
  1. Drug -> Disease  (existing=0.92, stt=0.31) -- STT says NO
  2. ...
```

---

## File Structure

Single file: `KOMPOSOS-IV-PHARM/stt_repurposing.py`

```
stt_repurposing.py
├── load_clean_subgraph()      # MEASURED+ESTABLISHED only
├── yoneda_fingerprint()       # presheaf for an object
├── yoneda_distance()          # symmetric difference metric
├── YonedaStrategy             # scores Drug-Disease via nearest known drug
├── disease_fiber()            # (Drug, Protein) pairs over a disease
├── base_morphism_strength()   # shared-protein Jaccard between diseases
├── TransportStrategy          # scores via fibration transport
├── verify_transport_axioms()  # identity and composition checks
├── rezk_equivalence_classes() # Yoneda-iso grouping
├── RezkStrategy               # scores after merging equivalences
├── run_comparison()           # AUROC table for all methods
└── main()                     # entry point
```

Estimated size: 300-400 lines.

---

## Dependencies

Only what PHARM already has:
- sqlite3 (stdlib)
- numpy (for AUROC computation in benchmark harness)
- sklearn.metrics (already used by repurposing_benchmark.py)
- Everything else imported from existing PHARM modules

No new pip installs. No modifications to existing files.

---

## Run Command

```powershell
cd C:\Users\JAMES\github\KOMPOSOS-IV-PHARM
python stt_repurposing.py
```

Expected runtime: under 60 seconds (1,560 pairs, small graph).

---

## What We Learn From The Experiment

**If STT strategies improve AUROC:**
- The graph shape carries predictive signal beyond path-walking
- Evidence-tier-filtered Yoneda is a better similarity metric than shared targets
- Fibration transport generalizes drug efficacy across disease mechanisms
- Rezk completion reveals redundant or equivalent entities

**If STT strategies DON'T improve AUROC but find interesting equivalences:**
- The structural analysis is still valuable for data quality and hypothesis generation
- Disease equivalence classes are publishable findings
- Transport axiom violations flag data inconsistencies worth fixing

**If STT strategies hurt AUROC:**
- The clean subgraph (1,355 edges) may be too sparse for structural analysis
- Try relaxing to include INFERRED tier (2,164 edges)
- Or: the 20-disease, 78-drug graph is too small for shape to matter

**In all cases:** the transport axiom verification produces a data quality
report independent of scoring performance.

---

## Future Projects (Separate From This)

**Project 2: 78% Novel Reservoir Ranking**
Use Yoneda distance to rank the ~78% of candidates with no literature backing
by similarity to validated drugs. Turns untriaged noise into a ranked list.

**Project 3: Chromosomal Collapse / Segal Defect**
Compute Segal defect per disease (composition ambiguity count). Stratify
diseases into coherent vs collapsed. Run different scoring regimes per stratum.
Uses the STT infrastructure from Project 1.

**Project 4: Crystal Dreamer Bridge**
Functor chain Patient -> Collapse Signature -> Molecular Constraints.
Requires Project 3 (collapse detection) plus KOMPOSOS-III-LAMBDA-max-3D
integration. Novel drug design, not repurposing.

**Project 5: Platform Protocol**
Multi-user shared category with differential privacy (PLATFORM_PROTOCOL_DESIGN.md).
Requires Projects 1-4 to be working single-user first.

---

## Session Checklist

Next session, the agent should:

1. Read this plan file first
2. Read `validation/repurposing_benchmark.py` for exact API signatures
   (load_full_typed_view, score_pair, pairwise_auroc, make_strategies)
3. Read `oracle/strategies.py` for InferenceStrategy base class
4. Read `core/category.py` for Category API (add, connect, morphisms_to,
   morphisms_from, objects)
5. Check `core/evidence_tiers.py` for tier constants and classification
6. Write `stt_repurposing.py` following this plan exactly
7. Run it: `python stt_repurposing.py`
8. Report results
9. Do NOT modify any existing files
10. Do NOT launch background agents for exploration -- the plan is complete
