# Mathematical Foundations

**Purpose**: Document the mathematical systems implemented in KOMPOSOS-IV-PHARM -- what they are, how they work, where they live in code, and how they contribute to drug repurposing predictions.

**Audience**: Mathematicians, computational scientists, reviewers evaluating the theoretical basis

**Prerequisites**: Basic familiarity with category theory helps but is not required. See [CATEGORICAL_THEORY_PRIMER.md](CATEGORICAL_THEORY_PRIMER.md) for an accessible introduction.

---

## Overview: A Multi-Engine Mathematical Architecture

KOMPOSOS-IV-PHARM is not a single algorithm. It is built on multiple interlocking mathematical frameworks, each providing a different lens on the same biological data:

| Engine | Mathematical Basis | Role | Code Location |
|--------|--------------------|------|---------------|
| **Enriched Categories** | Quantale-enriched categories (Lawvere) | Core data model, confidence composition | `core/category.py`, `categorical/enriched_category.py` |
| **Yoneda Presheaves** | Yoneda lemma, presheaf fingerprints | Structural similarity (STT origin) | `oracle/yoneda_strategy.py`, `categorical/presheaf_topos.py` |
| **Gray Coherence** | Gray categories (semistrict 3-categories) | Interchange cost, reaction ordering | `categorical/gray_category.py` |
| **ZFC-CAT Dual Engine** | Set theory + category theory bridge | Claim verification (AGREE/ORPHAN/HOLLOW/REJECT) | `zfc/bridge.py`, `zfc/logic.py` |
| **COG Tiered Verification** | Energy-based routing, 5-tier computation | Knowledge graph verification | `cog/engine.py`, `cog/energy.py`, `cog/router.py` |
| **OPTIMUS Monad** | Endofunctor + monad, Tarski fixpoints | Categorical self-correction | `optimus_core.py` |
| **Infinity-Cosmos** | Riehl-Verity infinity-categories | Higher structure: 2-cells, fibrations, Kan extensions | `core/cosmos.py`, `categorical/` |
| **Simplicial Type Theory** | STT strategies (Yoneda, fibration transport, Rezk) | Structural drug repurposing scoring | `stt_repurposing.py` |
| **Kan Extensions** | Left/right Kan extensions (Mac Lane) | Prediction by universal extension | `categorical/kan_extensions.py` |

---

## 1. Enriched Category Theory (Core Engine)

### What It Is

The knowledge graph is modeled as a category **enriched over a multiplicative quantale**: a complete lattice ([0,1], x, 1) where composition is multiplication and the unit is 1.0.

This means:
- **Objects** are drugs, proteins, and diseases
- **Morphisms** are directed relationships with confidence values in [0,1]
- **Composition** is multiplicative: `conf(A->C) = conf(A->B) * conf(B->C)`

Multiplicative composition is not arbitrary -- it models honest uncertainty propagation. If link A->B has confidence 0.8 and B->C has confidence 0.7, the composed path A->B->C has confidence 0.56. Uncertain links compound through chains.

### Why This Quantale

Three quantale types are implemented (`categorical/quantales.py`):

| Quantale | Tensor | Unit | Order | Semantics |
|----------|--------|------|-------|-----------|
| **Multiplicative** | a * b | 1.0 | a >= b (higher = better) | Confidence, affinity |
| **Additive** | a + b | 0.0 | a <= b (lower = better) | Cost, distance, toxicity |
| **Probabilistic** | 1-(1-a)(1-b) | 0.0 | -- | Risk, probability |

Drug repurposing uses the multiplicative quantale because biological confidence composes multiplicatively: a chain of uncertain steps produces an even more uncertain conclusion.

### Code

```python
# categorical/enriched_category.py
MULTIPLICATIVE_QUANTALE = MonoidalStructure(
    tensor=lambda a, b: a * b,
    unit=1.0,
    compare=lambda a, b: a >= b,
    name="Multiplicative([0,1], x, 1)"
)

# core/category.py -- composition uses this implicitly
# Path confidence = product of hop confidences
```

**Mathematical reference**: Lawvere, "Metric spaces, generalized logic, and closed categories" (1973); Fong & Spivak, "Seven Sketches in Compositionality" (2019), Def 2.46.

---

## 2. Yoneda Presheaves and Structural Similarity

### What It Is

The Yoneda lemma says: an object is completely determined by how other objects map into (and out of) it. In KOMPOSOS-IV-PHARM, this means a drug is characterized by its **presheaf fingerprint** -- the set of all its morphisms, weighted by confidence.

Two drugs with similar fingerprints are **structurally similar** even if they share no explicit annotation. This is the mathematical basis for drug equivalence classes.

### How It Works (Production)

The Yoneda Distance Strategy (`oracle/yoneda_strategy.py`) is the 9th scoring strategy:

1. Load only MEASURED + ESTABLISHED edges (1,355 edges, noise-free subgraph)
2. For each object, compute a confidence-weighted fingerprint:
   ```
   fingerprint(X) = {(neighbor, relation): max_confidence}
   ```
3. For a Drug-Disease pair, find the most similar drug that treats that disease
4. Similarity = weighted Jaccard: `|intersection| / |union|` where weights are max confidence per key
5. Integrated as additive bonus: `min(0.10, 0.06 * similarity)`

### Drug Equivalence Classes Discovered

Drugs with identical Yoneda presheaf fingerprints on the clean subgraph:

| Drug A | Drug B | Class | Validated |
|--------|--------|-------|-----------|
| Binimetinib | Cobimetinib | MEK inhibitors | FDA labels match |
| Encorafenib | Vemurafenib | BRAF inhibitors | FDA labels match |
| Carboplatin | Oxaliplatin | Platinum compounds | FDA labels match |

These equivalence classes are discovered purely from morphism structure -- no drug class annotations are used. They are biologically plausible and overlap with FDA-labeled drug classes, but the ablation effect should be rerun under the corrected loader before quoting as a current effect size.

### Impact on Metrics

| Metric | Current strict run |
|--------|-------------------:|
| AUROC | 0.9747 |
| AUPRC | 0.552 |
| Hits@5 / Hits@10 / Hits@20 | 1.00 / 0.60 / 0.60 |

Older Yoneda ablation deltas were development measurements. Treat them as
historical until rerun under the corrected loader and leakage controls.

### Origin: Simplicial Type Theory Experiment

The Yoneda Distance Strategy originated from an STT (Simplicial Type Theory) experiment (`stt_repurposing.py`) that tested three strategies:

1. **Yoneda Distance** -- presheaf fingerprint similarity (kept, integrated as 9th strategy)
2. **Fibration Transport** -- lift drug efficacy along disease-disease morphisms (dropped: too sparse, 3 diseases with zero protein coverage on clean subgraph)
3. **Rezk Completion** -- merge Yoneda-isomorphic entities, propagate labels (dropped: identical to Yoneda, no disease equivalence classes found)

Only Yoneda added value. The other two STT strategies failed not because the math is wrong, but because the current graph lacks the density they need (disease-disease morphisms are sparse).

**Code**: `stt_repurposing.py` (standalone experiment), `oracle/yoneda_strategy.py` (production integration)

**Mathematical reference**: Mac Lane, "Categories for the Working Mathematician" (1978), Chapter III; Riehl, "Category Theory in Context" (2016), Chapter 2.

---

## 3. Gray Coherence (Interchange Law)

### What It Is

A **Gray category** is a semistrict 3-category where the interchange law holds up to **weak isomorphism**, not strict equality. In standard 2-categories:

```
(f tensor g) compose (h tensor k) = (f compose h) tensor (g compose k)
```

In a Gray category, this equality becomes an isomorphism -- there is a **cost** to swapping the order of operations. The 2-cell witnessing this isomorphism measures the swap cost.

### Application: Bioorthogonal Reaction Planning

In `categorical/gray_category.py`, the Gray category models chemical reactions where order matters:

- **1-morphisms**: bioorthogonal click reactions (azide-alkyne, tetrazine-TCO, etc.)
- **2-cells**: cost of swapping reaction order at a site (the interchange witness)
- **Interference detection**: flags reactions that won't commute before wet-lab synthesis

```python
# categorical/gray_category.py
class InterchangeCell:
    """
    2-cell representing the cost of swapping two reactions.
    In a Gray category, the interchange law holds up to WEAK isomorphism.
    This 2-cell IS the witness to that weak isomorphism.
    """
    reaction_1: ReactionMorphism
    reaction_2: ReactionMorphism
    swap_cost: float  # 0 = free swap, 1 = impossible
    interference_type: Optional[str]  # "cross_reactivity", "steric_clash"
```

### What It Catches

The Gray category prevents trying two clicks in the wrong order and getting cross-reactivity:

| Reaction Pair | Swap Cost | Interference | Result |
|--------------|----------:|-------------|--------|
| Azide-alkyne + Tetrazine-TCO | 0.1 | None | Safe to swap |
| Tetrazine-TCO + Norbornene-tetrazine | 0.9 | Cross-reactivity | Do NOT swap |
| Same-site reactions | +0.3 penalty | Steric clash | Order matters |

### Status

Gray coherence is implemented and functional for bioorthogonal chemistry planning. It is not yet integrated into the Track A drug repurposing scoring pipeline -- it applies to Track B reaction planning where the question is "in what order should we perform these chemical modifications?"

**Code**: `categorical/gray_category.py`

**Mathematical reference**: Gray, "Formal Category Theory: Adjointness for 2-Categories" (1974); Gurski, "An algebraic theory of tricategories" (2006).

---

## 4. ZFC-CAT Dual Engine

### What It Is

The dual engine runs two independent verification systems on every claim:

1. **ZFC (Set Theory)**: proposes claims via logical entailment, transitive chains, well-ordering
2. **CAT (Category Theory)**: verifies claims structurally via curvature, topology, neighborhoods

The two engines produce independent verdicts that are combined into a **delta classification**:

| ZFC Says | CAT Says | Delta | Meaning |
|----------|----------|-------|---------|
| Proves it | Confirms structurally | **AGREE** | Strong evidence from both foundations |
| Proves it | Structure doesn't support | **ORPHAN** | Logically forced but geometrically unsound |
| Can't prove | Structural pattern exists | **HOLLOW** | Novel discovery -- geometrically real, logically baseless |
| No support | No support | **REJECT** | Neither engine supports it |

### Why Two Foundations?

ZFC and category theory have different strengths:

- **ZFC** is good at: transitive closure, well-ordering, membership, exhaustive enumeration
- **CAT** is good at: structural similarity, composition, universal properties, functorial relationships

ORPHAN claims (logically valid but structurally unsound) often indicate brittle reasoning chains. HOLLOW claims (structurally real but logically baseless) are the most interesting -- they represent novel discoveries that formal logic hasn't caught up with yet.

### Architecture

```
StoreAdapter (shared data layer)
   /              \
 ZFC               CAT (CategoricalVerifier)
(LogicOracle,      (structural verification)
 OrdinalOracle)
   \              /
 DualEngineBridge
       |
    System 3 (Meta Kan Extension)
```

**System 3** (Meta Kan Extension) resolves disagreements between ZFC and CAT using Kan extension-based prediction: it extends the pattern of past AGREE/ORPHAN/HOLLOW resolutions to predict how a new disagreement should resolve.

**Code**: `zfc/bridge.py` (DualEngineBridge), `zfc/logic.py` (LogicOracle), `zfc/well_ordering.py` (OrdinalOracle), `zfc/meta_kan.py` (System 3)

---

## 5. COG: Tiered Verification

### What It Is

COG (Cognitive Co-processor) is an energy-based routing system that decides how much computation to spend verifying a claim. Claims that fit naturally into the knowledge graph get fast, cheap verification. Claims that are surprising or contradictory get progressively deeper analysis.

### Energy Model

Every claim has an **energy** score (0.0 = fits perfectly, 1.0+ = high resistance):

| Component | Weight | What It Measures |
|-----------|-------:|-----------------|
| NOVELTY | 0.15 | Are source/target known objects? |
| PATH_RESISTANCE | 0.30 | How far apart in the graph? |
| CONTRADICTION | 0.35 | Conflicts with existing knowledge? |
| CONFIDENCE_GAP | 0.10 | Differs from existing confidence? |
| TYPE_MISMATCH | 0.10 | Valid relation for these types? |

### 5-Tier Architecture

Energy determines which computational tier handles the claim:

| Tier | Name | Cost | Threshold | What It Does |
|-----:|------|-----:|----------:|--------------|
| 0 | Graph Lookup | ~1ms | < 0.2 | Direct lookup: `category.get()`, `morphisms_from()` |
| 1 | Composition + Paths | ~10ms | < 0.5 | Path finding: `category.find_paths()` |
| 2 | Sheaf + Kan | ~100ms | < 0.7 | Sheaf coherence checker, Kan extension oracle |
| 3 | ZFC Dual Engine | ~1s | < 0.85 | Full dual engine: AGREE/ORPHAN/HOLLOW/REJECT |
| 4 | Full Topology + Flow | ~10s | < 1.0 | Progressive refinement with budget (30s max): 2-cells, h2K, oracle strategies, Ricci curvature, interchange law |

Tier 4 has a configurable budget and early-exits when confidence exceeds 0.95 or time runs out.

### Antonym Detection

COG maintains a dictionary of antonym relation pairs for contradiction detection:

```python
# cog/energy.py
ANTONYM_RELATIONS = {
    "supports": "contradicts",
    "causes": "prevents",
    "entails": "refutes",
    "trusts": "distrusts",
    "mitigates": "exposes",
    "sanitizes": "bypasses",
    ...
}
```

If the graph contains `A supports B` and a new claim asserts `A contradicts B`, the CONTRADICTION component fires with high energy.

**Code**: `cog/engine.py` (CogEngine), `cog/energy.py` (EnergyComputer), `cog/router.py` (TierRouter), `cog/schema.py` (data types)

---

## 6. OPTIMUS: Categorical Self-Correction

### What It Is

OPTIMUS is a **monad** on the runtime category that discovers better factorizations of morphisms. Instead of gradient descent (adjusting parameters), OPTIMUS searches for intermediate objects that improve path confidence.

### The Categorical Gradient

```
Classical ML:   x_{t+1} = x_t - eta * grad(L(x_t))
OPTIMUS:        m_{t+1} = argmax_{f in factorizations(m_t)} w(f)
```

Instead of adjusting parameters, OPTIMUS discovers intermediate objects. The "gradient direction" is the set of all factorizations A->B->C of a morphism A->C. Better factorizations = higher confidence paths = uphill in the quantale order.

### Monad Structure

```
unit     : m -> Optimus(m)              -- lift (identity action)
multiply : Optimus^2(m) -> Optimus(m)   -- collapse nested search
bind     : m -> (m -> Optimus(n)) -> Optimus(n)  -- chain refinements
```

### Tarski Stability

Every rewrite must satisfy `w(new) >= w(old)` in the quantale order. This guarantees **monotone convergence to a fixpoint** -- the system can only improve, never degrade.

### Yoneda Replication

Every object X is represented by its relational fingerprint:
- `hom_in(X) = {f : A -> X for all A}`
- `hom_out(X) = {f : X -> B for all B}`

Two objects with identical fingerprints are categorically indistinguishable. This is the same mathematical principle used by the Yoneda Distance Strategy, but OPTIMUS uses it for self-correction rather than similarity scoring.

**Code**: `optimus_core.py` (Quantale, FreeCategory, RuntimeCategory, OptimisMonad)

---

## 7. Infinity-Cosmos (Higher Structure)

### What It Is

Based on Riehl & Verity's "Infinity category theory from scratch" (arXiv:1608.05314), the infinity-cosmos layer provides higher-dimensional structure on top of the base category:

- **2-cells** (morphisms between morphisms): `alpha : f => g` where f,g : A -> B
- **Isofibrations**: morphisms with cartesian lifting properties
- **Cartesian fibrations**: classified via the Grothendieck construction
- **Yoneda embedding**: into the presheaf infinity-cosmos
- **Kan extensions**: pointwise left and right extensions

### What It Provides

The base category has objects and morphisms (1-dimensional). The infinity-cosmos adds:

| Structure | Dimension | What It Models |
|-----------|----------:|----------------|
| 2-cells | 2 | "This drug inhibits BRAF more strongly than that drug" |
| Fibrations | -- | Structured families of morphisms over a base |
| Kan extensions | -- | "Best approximation" predictions |
| Grothendieck construction | -- | Fiber-wise data integration |

### Homotopy 2-Category h2K

The homotopy 2-category extracts a strict 2-category from the infinity-cosmos, enabling:
- 2-cell lookup between morphisms
- Horizontal and vertical composition of 2-cells
- Natural transformation detection

**Code**: `core/cosmos.py` (InfinityCosmos), `categorical/two_categories.py` (TwoCategory), `categorical/fibrations.py` (GenericFibration), `categorical/kan_extensions.py` (LeftKanExtension, RightKanExtension), `categorical/grothendieck.py` (GrothendieckConstruction), `categorical/presheaf_topos.py` (PresheafTopos)

**Mathematical reference**: Riehl & Verity, "Infinity category theory from scratch" (2018); Riehl, "Category Theory in Context" (2016).

---

## 8. Simplicial Type Theory (STT)

### What It Is

Simplicial Type Theory provides a type-theoretic framework for reasoning about infinity-categories. In KOMPOSOS-IV-PHARM, three STT-inspired strategies were tested for drug repurposing:

### Three STT Strategies Tested

**1. Yoneda Distance** (integrated as 9th strategy):
- Compute presheaf fingerprints on clean evidence subgraph (MEASURED + ESTABLISHED only)
- Score drug-disease pairs by similarity to known treatments
- Uses confidence-weighted Jaccard distance
- **Development result**: historical ablations suggested AUROC/AUPRC lift, but the effect size must be rerun under the corrected loader before being treated as current.

**2. Fibration Transport** (not integrated):
- Lift drug efficacy along disease-disease morphisms via cartesian transport
- If Disease_A is similar to Disease_B and Drug_X treats Disease_A, transport Drug_X to Disease_B
- **Result**: Too sparse. Only 3 diseases had protein coverage on the clean subgraph. Transport had nothing to lift.

**3. Rezk Completion** (not integrated):
- Merge Yoneda-isomorphic entities, propagate labels through equivalence classes
- If Drug_A = Drug_B (by Yoneda) and Drug_A treats Disease_X, then Drug_B treats Disease_X
- **Result**: Identical to Yoneda Distance. No disease equivalence classes were found (diseases have distinct protein profiles).

### Why Only Yoneda Worked

The key insight: the current graph has dense drug-protein edges but sparse disease-disease structure. Yoneda operates on drug neighborhoods (dense), while fibration transport and Rezk completion need disease neighborhoods (sparse). As the graph grows with more disease-disease relationships, these strategies may become viable.

**Code**: `stt_repurposing.py` (standalone experiment comparing all 3)

---

## 9. Sheaf Coherence

### What It Is

The sheaf condition from algebraic geometry: **local data must glue consistently to global data**. In KOMPOSOS-IV-PHARM, this means predictions about overlapping drug-protein-disease regions must agree.

The `SheafCoherenceChecker` (`oracle/coherence.py`) validates predictions by:
1. Checking that predictions for the same source-target pair agree in direction
2. Detecting semantic contradictions via antonym pair detection
3. Filtering incoherent predictions before scoring

This is one of the 9 oracle strategies (the "coherence" strategy), contributing to the ensemble vote.

**Code**: `oracle/coherence.py` (SheafCoherenceChecker)

---

## 10. Kan Extensions (Prediction Engine)

### What It Is

Mac Lane called Kan extensions "the most important concept in category theory." Given a functor F: C -> D and an embedding K: C -> E, we want to extend F along K to get F-hat: E -> D.

| Extension | Formula | Use Case |
|-----------|---------|----------|
| **Left Kan** (Lan_K F) | colim over comma category | Predict unknown from known (forward extrapolation) |
| **Right Kan** (Ran_K F) | lim over comma category | Synthesize goal from current (backward deduction) |

In drug repurposing:
- **Lan**: "Given what we know about Drug X's targets, predict which diseases it might treat"
- **Ran**: "Given that we want to treat Disease Y, what drug properties do we need?"

**Code**: `categorical/kan_extensions.py` (LeftKanExtension, RightKanExtension, CommaCategory, Functor)

---

## How the Math Contributes to Drug Repurposing

### Production Pipeline (9 Strategies)

The 9 oracle strategies that produce the current AUROC 0.9747 result use these mathematical frameworks:

| Strategy | Math Framework | Historical ablation note |
|----------|---------------|------------------------:|
| **Composition** | Enriched category composition (quantale) | -0.153 (dominant) |
| **Binding Evidence** | Molecular chemistry + graph confidence | -0.045 |
| **Path Bonus** | Confidence-weighted path aggregation | -0.015 |
| **Yoneda Distance** | Yoneda presheaf fingerprints (STT) | -0.009 |
| **Coherence** | Sheaf coherence (contradiction detection) | -0.005 |
| **Conjecture** | Inductive rule learning from path patterns | -0.002 |
| **Natural Transform** | Morphism alignment scoring | ~0 |
| **Game Theory** | Equilibrium analysis | ~0 |
| **Bayesian** | Probabilistic scoring | ~0 |

### Score Aggregation

```
base = mean(8 strategy confidences)           # First 8 strategies
path_bonus = min(0.25, 0.04 * sum(path_conf)) # Confidence-weighted
yoneda_bonus = min(0.10, 0.06 * similarity)   # Yoneda presheaf distance
score = min(1.0, base + path_bonus + yoneda_bonus)
```

### Infrastructure (Not Yet in Scoring Pipeline)

| System | Status | Potential Application |
|--------|--------|----------------------|
| Gray Coherence | Implemented | Track B: reaction ordering |
| ZFC-CAT Dual Engine | Implemented | Claim verification, HOLLOW discovery |
| COG Tiered Verification | Implemented (MCP server) | Energy-based claim routing |
| OPTIMUS Monad | Implemented | Self-correction, factorization search |
| Fibration Transport (STT) | Tested, too sparse | Disease-level prediction (needs more data) |
| Rezk Completion (STT) | Tested, identical to Yoneda | Entity merging (needs disease equivalences) |

---

## Mathematical Honesty

### What the math genuinely contributes

1. **Composition** (+0.153 AUROC): The enriched category framework naturally handles multi-hop inference with confidence propagation. This is the core engine.

2. **Yoneda**: Structural similarity without feature engineering. Drug equivalence classes are discovered, not hardcoded; historical AUPRC lift estimates should be rerun under the corrected loader before being quoted.

3. **Type safety**: Category theory enforces that Drug->Disease predictions require protein intermediates. You can't accidentally compose Drug->Drug paths.

4. **Auditability**: Every mathematical operation has a precise definition. A researcher can trace exactly why a prediction was made.

### What the math does NOT do

- The categorical framework does not outperform graph baselines by a large margin (+0.3440 AUROC over degree_product). Most predictive signal comes from graph connectivity and curation quality.

- The more sophisticated structures (Gray coherence, ZFC dual engine, OPTIMUS) are implemented but not yet proven to improve drug repurposing metrics. They represent architectural investments for future capability.

- The infinity-cosmos layer provides theoretical infrastructure but has not been shown to produce predictions that simpler methods cannot.

The honest claim: category theory provides a principled, auditable, extensible framework for biomedical reasoning. The performance is competitive with larger, noisier knowledge graphs -- and every prediction is traceable to primary literature.

---

## References

1. Mac Lane S. *Categories for the Working Mathematician*. Springer, 1978.
2. Riehl E. *Category Theory in Context*. Dover, 2016.
3. Fong B, Spivak DI. *An Invitation to Applied Category Theory*. Cambridge University Press, 2019.
4. Lawvere FW. "Metric spaces, generalized logic, and closed categories." *Rendiconti del Seminario Matematico e Fisico di Milano*. 1973;43(1):135-166.
5. Riehl E, Verity D. "Infinity category theory from scratch." arXiv:1608.05314, 2018.
6. Gray JW. *Formal Category Theory: Adjointness for 2-Categories*. Springer LNM 391, 1974.
7. Gurski N. "An algebraic theory of tricategories." PhD thesis, University of Chicago, 2006.

---

## See Also

- [CATEGORICAL_THEORY_PRIMER.md](CATEGORICAL_THEORY_PRIMER.md) -- Accessible introduction to category theory concepts
- [STRATEGIES_IN_DEPTH.md](STRATEGIES_IN_DEPTH.md) -- Detailed strategy descriptions with pseudocode
- [ARCHITECTURE.md](ARCHITECTURE.md) -- System architecture and module map
- [AUDIT_WALKTHROUGH.md](AUDIT_WALKTHROUGH.md) -- Worked examples showing math in action

---

*Last updated: 2026-05-26*
