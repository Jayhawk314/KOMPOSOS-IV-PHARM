# Categorical Theory Primer

**Purpose**: Intuitive explanation of category theory concepts used in KOMPOSOS-IV, without heavy mathematics.

**Audience**: Mathematicians, researchers curious about categorical foundations

**Disclaimer**: This is intuition and metaphor, not rigorous mathematics. See cited textbooks for formal definitions.

---

## What is Category Theory?

Category theory is the study of **structure and composition**. Instead of studying individual objects (sets, groups, etc.), category theory studies **relationships between objects** and how to compose them.

**Key insight**: "Objects are defined by their relationships with other objects, not their internal structure."

---

## Core Concepts

### 1. Objects

**Definition**: The things we're studying. In KOMPOSOS-IV:
- Drugs (Sorafenib, Vemurafenib, ...)
- Proteins (BRAF, VEGFR2, ...)
- Diseases (Melanoma, Renal Cell Carcinoma, ...)

**Category Theory View**: Objects are atomic; their identity is intrinsic. We don't care about internal structure (whether a drug is a molecule or abstract label).

**Code**:
```python
class Object:
    name: str
    type_name: str  # "Drug", "Protein", "Disease"
```

---

### 2. Morphisms (Arrows)

**Definition**: A relationship between objects. "Source → Target."

**Examples** (KOMPOSOS-IV):
- Sorafenib → BRAF (inhibits)
- BRAF → Melanoma (mutated in)
- VEGFR2 → Angiogenesis (promotes)

**Each morphism has**:
- Source object
- Target object
- Name (inhibits, mutated_in, promotes, ...)
- Confidence [0, 1]

**Category Theory View**: Morphisms are the primary object of study, not the objects themselves. Relationships matter more than things.

**Code**:
```python
class Morphism:
    name: str  # "inhibits"
    source: Object
    target: Object
    confidence: float  # 0.0–1.0
```

---

### 3. Composition

**Definition**: Combining two morphisms in sequence.

**Example**:
```
Sorafenib → BRAF → Melanoma
(composition of two morphisms)
```

**Mathematical notation**:
```
(f ∘ g): Sorafenib → Melanoma (composition of two arrows)
```

**In KOMPOSOS-IV**: Composition is **multiplicative**:
```
confidence(f ∘ g) = confidence(f) × confidence(g)
```

**Why multiply?** Because uncertainty compounds. If link A is 90% confident and link B is 80% confident, the chain is 72% confident (not 85% or anything else).

**Code**:
```python
def compose(m1: Morphism, m2: Morphism) -> float:
    """Compose two morphisms"""
    if m1.target != m2.source:
        return None  # Can't compose
    return m1.confidence * m2.confidence
```

---

### 4. Categories

**Definition**: A collection of objects and morphisms with a composition rule.

**Requirements**:
1. For each pair of morphisms f: X → Y and g: Y → Z, composition f ∘ g: X → Z is defined
2. Composition is associative: (f ∘ g) ∘ h = f ∘ (g ∘ h)
3. Identity morphism: For each object X, there's an identity morphism id_X: X → X

**KOMPOSOS-IV as a Category**:
- **Objects**: Drugs, Proteins, Diseases (464 total)
- **Morphisms**: Relationships (5,382 total)
- **Composition**: Multiplicative confidence (path finding)
- **Identity**: Self-loops (drug treats drug with confidence 1.0)

**Key property**: We can compose paths (Drug → Protein → Disease) and compute their confidence automatically.

---

## Advanced Concepts (Infinity-Cosmos Layer)

### 5. Functors

**Definition**: A structure-preserving map between categories.

**Example**: A functor might map:
- Proteins in category C → Pathways in category C'
- Morphisms f: P → Q → Morphisms f': Path → Path'

**Use in KOMPOSOS-IV**: Functors allow us to "lift" predictions from one domain (drug-protein binding) to another (drug-disease efficacy).

---

### 6. 2-Cells (Morphisms Between Morphisms)

**Definition**: A morphism between two morphisms.

**Example**:
```
Two paths from Sorafenib to Melanoma:
  Path 1: Sorafenib → BRAF → Melanoma
  Path 2: Sorafenib → VEGFR2 → Angiogenesis → Melanoma

A 2-cell could say: "Path 1 is similar to Path 2 (both support Melanoma treatment)"
```

**Notation**:
```
m1 ⇒ m2 (a 2-cell relating two morphisms)
```

**In KOMPOSOS-IV**: 2-cells are used in Yoneda equivalence discovery:
- "Sorafenib and Vemurafenib have similar target profiles"
- This is formalized as a 2-cell relating their morphism neighborhoods

---

### 7. Presheaves (Yoneda Perspective)

**Definition**: A way to represent objects by their neighborhoods.

**Intuition**: Instead of defining an object by its internal structure, define it by what it relates to.

**Example (Yoneda presheaf for Sorafenib)**:
```
Sorafenib is defined by:
  {(BRAF, inhibits, 0.95), (VEGFR2, inhibits, 0.85), (FLT3, inhibits, 0.80), ...}
```

**Similarity**: Two drugs are similar if they have overlapping neighborhoods:
```
Sorafenib ≈ Vemurafenib if they both inhibit {BRAF, VEGFR2, ...}
```

**Mathematical basis**: Yoneda Lemma says "every object is uniquely determined by its morphisms."

**Code**:
```python
def build_presheaf(obj: Object, cat: Category) -> dict:
    """Define object by its neighborhood"""
    presheaf = {}
    for morphism in cat.morphisms_from(obj):
        key = (morphism.target.name, morphism.name)
        presheaf[key] = morphism.confidence
    return presheaf

def jaccard_similarity(presheaf1, presheaf2) -> float:
    """Yoneda-based similarity"""
    intersection = len(set(presheaf1.keys()) & set(presheaf2.keys()))
    union = len(set(presheaf1.keys()) | set(presheaf2.keys()))
    return intersection / union if union > 0 else 0.0
```

---

### 8. Fibrations (Hierarchical Structure)

**Definition**: A way to organize categories hierarchically.

**Example**: Drug-Protein interactions form a fibration over Diseases:
```
Disease1 ← {Drug-Protein interactions for Disease1}
Disease2 ← {Drug-Protein interactions for Disease2}
...
```

**Use in KOMPOSOS-IV**: Fibrations allow us to organize scoring computations per disease (disease-specific context).

---

### 9. Kan Extensions (Generalization)

**Definition**: A way to extend a functor beyond its original domain.

**Intuition**: If we have a pattern on a subset of objects, Kan extensions help us generalize to all objects.

**Example**: If we know Sorafenib works for 5 cancer types, Kan extensions might help us infer it might work for related (but untested) cancer types.

**Status in KOMPOSOS-IV**: Kan extensions are explored (Infinity-Cosmos layer) but not yet production-ready.

---

## Why Category Theory for Drug Discovery?

### 1. Composability

Paths compose naturally:
```
Drug → Protein → Disease (composition of morphisms)
confidence(path) = confidence(Drug→Protein) × confidence(Protein→Disease)
```

No need to manually "glue" different data sources—they compose automatically.

### 2. Extensibility

Adding new object types or morphism types is straightforward:
```
Add: Mutation (new object type)
Add: Has_mutation (morphism): Gene → Mutation
Add: Drives (morphism): Mutation → Disease

Automatically available for path finding without code changes.
```

### 3. Honesty

Confidence propagates automatically through composition:
```
Confident link × uncertain link = less confident path
(exactly what we want for biological reasoning)
```

### 4. Abstraction

Category theory is abstract enough to unify:
- Drug-target binding (biochemistry)
- Genetic associations (genomics)
- Clinical outcomes (epidemiology)

All become morphisms in one Category.

---

## Examples in Code

### Example 1: Finding Paths (Composition)

```python
# Find all morphisms from Sorafenib to Melanoma
# This is an application of composition:
# Sorafenib ← Object
# BRAF ← Object
# Melanoma ← Object
# Sorafenib → BRAF → Melanoma = composition

paths = cat.find_paths('Sorafenib', 'Melanoma', max_length=4)

for path in paths:
    # path.confidence = product of all edge confidences
    # This is the categorical composition rule!
    print(f"Confidence: {path.confidence}")
```

### Example 2: Yoneda Similarity

```python
# Define Sorafenib and Vemurafenib by their neighborhoods (presheaves)
sorafenib_presheaf = {
    ('BRAF', 'inhibits'): 0.95,
    ('VEGFR2', 'inhibits'): 0.85,
    ...
}

vemurafenib_presheaf = {
    ('BRAF', 'inhibits'): 0.97,
    ('VEGFR2', 'inhibits'): 0.88,
    ...
}

# Similarity = overlap of neighborhoods (Yoneda distance)
similarity = jaccard_similarity(sorafenib_presheaf, vemurafenib_presheaf)
# Result: high similarity → drugs are similar
```

### Example 3: Fibration (Disease Context)

```python
# Organize morphisms per disease (fibration)
disease_fibers = {}
for disease in diseases:
    # Get all drugs and targets relevant to this disease
    fiber = {
        'drugs': [d for d, _ in get_candidates(disease)],
        'proteins': [p for _, p in get_candidates(disease)],
        'morphisms': get_morphisms(disease),
    }
    disease_fibers[disease] = fiber

# Each disease has its own "context" (fiber)
# Scoring can be disease-specific
```

---

## Philosophical Perspective

### The Morphism-Centric View

**Traditional approach** (object-centric):
- "What is Sorafenib? A small-molecule kinase inhibitor with MW 465, LogP 3.8, ..."
- **Problem**: Requires knowing all internal details

**Category-Theoretic approach** (morphism-centric):
- "What is Sorafenib? The thing that inhibits BRAF, VEGFR2, FLT3, ... with these confidences"
- **Advantage**: Define by relationships, not internal structure
- **Advantage**: Relationships are what matter for biology (drug-target interaction, not drug's chemistry per se)

### Scalability

As we add more object types and morphism types:
- **Traditional**: Code becomes monolithic (special cases everywhere)
- **Category-theoretic**: New types compose automatically with existing types

### Honesty

Category theory forces us to be explicit about:
- What composes (morphisms must match: target of f = source of g)
- How it composes (we choose the rule: multiplicative, not additive)
- Confidence propagation (automatic via composition)

---

## References

**Beginner-friendly**:
- Fong & Spivak, "An Invitation to Applied Category Theory" (2019)
- Leinster, "Basic Category Theory" (2014)

**Categorical foundations**:
- Mac Lane, "Categories for the Working Mathematician" (1971, classic)
- Barr & Wells, "Toposes, Triples, and Theories" (1985)

**Applied to biology**:
- Spivak, "Category Theory for the Sciences" (2014)

---

## Common Misconceptions

**Misconception 1**: "Category theory is abstract and impractical."
- **Reality**: It's abstract but practical for designing composable systems.

**Misconception 2**: "We need to rewrite everything in category-theoretic language."
- **Reality**: We use categorical ideas (composition, functors) implicitly in code. No need to "change everything."

**Misconception 3**: "Categories only apply to pure mathematics."
- **Reality**: They apply to any domain with objects and relationships (biology, chemistry, databases, etc.).

---

## See Also

- [ARCHITECTURE.md](ARCHITECTURE.md) — 5-layer stack
- [STRATEGIES_IN_DEPTH.md](STRATEGIES_IN_DEPTH.md) — Yoneda distance strategy
- [TRACK_A_DRUG_REPURPOSING.md](TRACK_A_DRUG_REPURPOSING.md) — How composition works in practice

---

*Last updated: 2026-05-26*
