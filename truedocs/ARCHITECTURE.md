# Architecture

**Purpose**: Explain the 5-layer stack design, core runtime, and system components.

**Audience**: Developers, researchers understanding the system, architects designing extensions

**Key principle**: Categorical composition (Drug → Protein → Disease) is the dominant mechanism. Strategies are augmentations.

---

## 5-Layer Stack Overview

KOMPOSOS-IV-PHARM is built as a 5-layer categorical AI runtime:

```
Layer 5: OPTIMUS              Categorical gradient descent (self-correction)
         ↓
Layer 4: COG                  Cognitive co-processor (claim verification)
         ↓
Layer 3: Infinity-Cosmos      Higher structures (2-cells, fibrations, Yoneda, Kan)
         ↓
Layer 2: KOMPOSOS-IV Category Runtime
         ├─ Objects (drugs, proteins, diseases)
         ├─ Morphisms (relationships with confidence)
         ├─ Enrichment (quantale-based confidence composition)
         ├─ Persistence (SQLite backend)
         └─ Runtime strategy modules
         ↓
Layer 1: ORION                Plugin framework (bridges, events)
```

### Layer 1: ORION (Plugin Framework)

**Role**: Event-driven plugin system for extending functionality.

**Files**: `bridges/`, plugin system in `core/`

**Provides**:
- Hook system for data enrichment
- Plugin registration (COG, OPTIMUS, Infinity-Cosmos)
- Event dispatch (object creation, morphism addition, scoring)

**Example**: ABPP bridge registers as a plugin that enriches morphisms with IC50 data when objects are loaded.

### Layer 2: KOMPOSOS-IV Category Runtime (Core)

**Role**: Implements categorical structures and composition.

**Files**: `core/category.py`, `core/cosmos.py`, `core/persistence.py`, `core/enrichment.py`

**Key classes**:

```python
# Core data structures
class Object:
    name: str
    type_name: str  # "Drug", "Protein", "Disease"
    metadata: dict
    provenance: str

class Morphism:
    name: str  # "inhibits", "mutated_in", "treats"
    source: str
    target: str
    confidence: float  # 0.0–1.0
    provenance: str

class Category:
    """Main runtime for drug repurposing graph"""
    def add(self, name: str, **kwargs) -> Object
    def connect(self, source: str, target: str, name: str = "r", confidence: float = 1.0, **metadata) -> Morphism
    def find_paths(self, source: str, target: str, max_length: int = 10) -> List[Path]
    def objects(self) -> List[Object]
    def morphisms(self) -> List[Morphism]
```

**Key design decisions**:

1. **Multiplicative composition**: Path confidence = product of edge confidences
   - If link A = 90% confident, link B = 80% confident, chain = 72%
   - Models honest uncertainty (uncertain links compound)

2. **Confidence as first-class value**: Every morphism carries a score 0.0–1.0
   - Allows nuanced prediction (not just binary relationships)
   - Propagates through paths automatically

3. **Persistence layer**: `KomposOSStore` is the durable SQLite source for `tier1.db`.
   - Benchmark and triage loaders copy rows into a runtime `Category`
   - The runtime graph is treated as read-only during validation

### Layer 3: Infinity-Cosmos (Higher Categorical Structures)

**Role**: Extends Category to include 2-cells, fibrations, and presheaves.

**Files**: `core/cosmos.py`, `core/formal_yoneda.py`

**Provides**:

1. **2-cells**: Morphisms between morphisms
   - Example: `(Drug1 → Protein → Disease) ~ (Drug2 → Protein → Disease)` (similar paths)
   - Used for equivalence class discovery (Yoneda strategy)

2. **Fibrations**: Generalization of categorical structures
   - Used in higher-order strategy voting
   - Supports Kan extension inference (experimental)

3. **Yoneda Presheaves**: Objects defined by their relationships
   - Fingerprint = neighborhood in graph weighted by confidence
   - Similarity = presheaf overlap (Jaccard distance)
   - Used by Yoneda distance strategy

**Example (Yoneda presheaf for Sorafenib)**:
```python
presheaf = {
    ('BRAF', 'inhibits'): 0.95,
    ('VEGFR2', 'inhibits'): 0.85,
    ('FLT3', 'inhibits'): 0.80,
    ...
}
# Similarity to Vemurafenib presheaf: 0.89 (high overlap on BRAF, VEGFR2)
```

### Layer 4: COG (Cognitive Co-processor)

**Role**: Claim verification and logical consistency.

**Files**: `bridges/cog_reasoning.py`

**Provides**:

1. **Coherence strategy**: Are paths logically consistent?
   - Detects circular logic (Drug inhibits Protein, Protein inhibits Drug)
   - Scores based on verdict lattice (probabilistic logic)

2. **Contradiction detection**: Do multiple paths agree or contradict?
   - If one path says treatment works, another says it doesn't, lower confidence

3. **Claim auditing**: Did the system's evidence support its conclusion?
   - Logs reasoning chain for human inspection

**Integration**: COG/verification components support audit and scoring context; they are not counted as separate active modules in the current PHARM scorer.

### Layer 5: OPTIMUS (Categorical Gradient Descent)

**Role**: Self-correction and iterative refinement.

**Files**: `core/optimus.py`, `bridges/optimus_plugin.py`

**Provides**:

1. **Gradient descent on categorical structures**:
   - Adjusts morphism confidences to maximize internal consistency
   - Experimental (not used in current Track A scoring)

2. **Confidence calibration**: Recalibrate scores if external validation diverges
   - If Hetionet says a pair is real but we scored it low, raise confidence on supporting path

3. **Ablation & importance**: Which morphisms are most important for predictions?
   - Removes each edge, measures AUROC change
   - Identifies critical biological links

**Current status**: Mostly experimental. Used for analysis, not production scoring.

---

## Core Runtime: How It Works

### 1. Graph Loading

```python
from core.category import Category
from validation.repurposing_benchmark import load_full_typed_view
from data.store import KomposOSStore

# Load database into Category via benchmark view
store = KomposOSStore('data/drugs/tier1.db')
cat, diseases = load_full_typed_view(store, view="full_typed")

# cat now has 1,146 objects and 2,329 morphisms
print(len(cat.objects()), len(cat.morphisms()))
```

### 2. Path Finding

```python
# Find all paths from Sorafenib to Melanoma (max 4 hops)
paths = cat.find_paths('Sorafenib', 'Melanoma', max_length=4)

for path in paths:
    hops = path.morphism_ids
    confidence = path.weight  # multiplicative
    print(f"Path: {' -> '.join(hops)}, Confidence: {confidence:.3f}")
```

Illustrative output shape:
```
Path: inhibits:BRAF..., Confidence: 0.807
Path: inhibits:BRAF... -> phosphorylates:MEK1..., Confidence: 0.757
...
```

### 3. Strategy Voting

```python
from validation.repurposing_benchmark import make_strategies, score_pair

# Initialize active runtime strategy profile
strategies = make_strategies(category)
score, votes = score_pair(strategies, 'Sorafenib', 'Melanoma')

# Live triage includes Yoneda only when visible known-treatment comparators exist.
# Strict remove_direct_labels excludes Yoneda because those comparators are removed.
```

### 4. Persistence

For the durable `tier1.db` source, use `KomposOSStore`:

```python
from data.store import KomposOSStore

store = KomposOSStore('data/drugs/tier1.db')
drug = store.get_object('Sorafenib')
morphisms_from_drug = store.get_morphisms_from('Sorafenib')
```

**Database schema**:
```sql
CREATE TABLE objects (
    name TEXT PRIMARY KEY,
    type_name TEXT,
    metadata TEXT,
    embedding BLOB,
    created_at TEXT,
    updated_at TEXT,
    provenance TEXT
);

CREATE TABLE morphisms (
    id TEXT PRIMARY KEY,
    name TEXT,
    source_name TEXT,
    target_name TEXT,
    metadata TEXT,
    confidence REAL,
    provenance TEXT,
    evidence_tier TEXT,
    quantitative_value REAL,
    value_unit TEXT,
    sample_size INTEGER,
    confidence_lower REAL,
    confidence_upper REAL
);
```

---

## Runtime Strategy Profiles

The current drug-repurposing scorer is assembled by
`validation/repurposing_benchmark.py::make_strategies`.

| Profile | Active modules |
|---------|----------------|
| Strict `remove_direct_labels` | `kan_extension`, `structural_hole`, `composition`, `yoneda_pattern`, `fibration_lift`, `topos_logic`, `binding_evidence` |
| Live/as-loaded triage | Strict modules plus conditional `yoneda_distance` when Drug->Disease comparator labels are visible |

**Aggregation**: active non-Yoneda strategy scores are averaged; path confidence
adds a bounded path bonus; Yoneda distance, when present, contributes a bounded
bonus rather than being averaged into the base.

See [STRATEGIES_IN_DEPTH.md](STRATEGIES_IN_DEPTH.md) for mathematical details.

---

## Plugin System (Bridges)

Plugins extend functionality without modifying core:

### ABPP / Binding Evidence

Experimental IC50 data are used through `oracle/binding_strategy.py` and the
ABPP bridge classes it imports. The current database contains 65 ABPP entries
used by the binding evidence strategy.

### Boltz2 Fallback

Heuristic binding prediction (fallback when no ABPP data).

Uses:
- Lipinski drug-likeness rules
- Target properties (Pfam domains)
- Similarity to known binders

Confidence: 0.60–0.80 (lower than experimental ABPP)

### COG Reasoning Bridge (`bridges/cog_reasoning.py`)

Integrates claim verification.

```python
from bridges.cog_reasoning import CogReasoningPlugin

cog = CogReasoningPlugin()
# Asynchronous plugin for claim verification and explanation hooks.
```

---

## Execution Model: End-to-End

```
User input: triage.py Melanoma
         ↓
Load database: tier1.db → Category (464 objects, 2,329 morphisms)
         ↓
For each drug in tier1.db:
  └─ Find all paths: Drug → ... → Melanoma (max 4 hops)
     ├─ Composition score: best path confidence
     ├─ Binding evidence: IC50 + drug properties
     ├─ Conditional Yoneda distance: structural similarity when comparators exist
    └─ Final score = mean(active signals except Yoneda) + path bonus + conditional Yoneda bonus
         ↓
Rank drugs by score (descending)
         ↓
Format output: top 10 candidates with evidence chains + PMIDs
         ↓
Display to user
```

**Computational cost**:
- Path finding: O(n × m^h) where n=drugs, m=edges, h=max path length
- Strategy scoring: O(n × active modules) = O(78 × 7/8) per disease
- Typical runtime: 2–5 seconds for full disease triage (first run includes path cache)

---

## Module Dependency Map

```
triage.py (entry point)
    ↓
validation/triage.py
    ├─ core/category.py (Category runtime)
    ├─ oracle/ (runtime strategy modules)
    ├─ validation/repurposing_benchmark.py (Database loading + scoring)
    ├─ data/store.py (SQLite backend)
    ├─ bridges/ (COG, OPTIMUS, ABPP, Boltz2)
    └─ chemistry/ (Pfam, drug properties)

repurposing_benchmark.py (evaluation harness)
    ├─ core/category.py
    ├─ oracle/
    ├─ data/store.py
    └─ validation/repurposing_benchmark_manifest.json

build_tier1.py (reproducible data build)
    ├─ data/drugs/tier1_manifest.json
    ├─ data/store.py (SQLite write)
    ├─ domains/bio/loader.py
    └─ chemistry/drug_properties.py
```

---

## Adding a New Strategy

Follow this 6-step template:

### Step 1: Create strategy file

```python
# oracle/my_strategy.py

from oracle.strategies import InferenceStrategy

class MyStrategy(InferenceStrategy):
    name = "my_strategy"

    def predict(self, source: str, target: str):
        # Return list[Prediction]; see oracle/strategies.py for examples.
        return []
```

### Step 2: Wire into the active profile

```python
from oracle.my_strategy import MyStrategy

def make_strategies(category):
    strategies = [
        # existing modules...
        MyStrategy(category),
    ]
    return strategies
```

### Step 3: Verify aggregation

In `validation/repurposing_benchmark.py`, `score_pair()` aggregates strategy
`Prediction.confidence` values. If the new module needs special treatment
like Yoneda's bounded bonus, document and test it explicitly.


### Step 4: Test regression

```bash
python validation/repurposing_benchmark.py --view full_typed --protocol remove_direct_labels
```

Verify:
- Score range [0, 1]
- 44/44 self-check (approvals recoverable)
- AUROC ≥ 0.96 (doesn't hurt performance)

### Step 5: Benchmark ablation

```bash
python validation/ablation_study.py
```

Check: Does removing your strategy hurt AUROC significantly?

### Step 6: Document

Add to `[STRATEGIES_IN_DEPTH.md](STRATEGIES_IN_DEPTH.md)` with:
- What it measures
- Mathematical formula
- Code location
- Performance impact

---

## Performance Optimization

### Caching Paths

Paths are expensive to compute. Cache them:

```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def find_paths_cached(cat: Category, src: str, tgt: str) -> List[Path]:
    return cat.find_paths(src, tgt, max_length=4)
```

### Database Indexing

Ensure SQLite has indexes:

```sql
CREATE INDEX idx_morphism_source ON morphisms(source_name);
CREATE INDEX idx_morphism_target ON morphisms(target_name);
CREATE INDEX idx_object_name ON objects(name);
```

### Batch Scoring

Score multiple drugs with the benchmark scorer:

```python
def score_all_drugs(cat, disease):
    strategies = make_strategies(cat)
    drugs = [obj.name for obj in cat.objects() if obj.type_name == "Drug"]
    return {
        drug: score_pair(strategies, drug, disease)[0]
        for drug in drugs
    }
```

---

## Code Quality Standards

### Style

- PEP 8 (flake8 check)
- Type hints (Python 3.10+)
- Docstrings (Google style)

### Testing

- Unit tests for all strategies
- Regression test: 44/44 self-check must pass
- Integration test: AUROC ≥ 0.96

### Documentation

- Code comments for non-obvious logic
- Source/provenance strings on new scientific edges
- Example usage in module docstrings

---

## Deployment Checklist

Before merging to main:

- [ ] All tests pass (pytest tests/)
- [ ] 44/44 self-check passes
- [ ] AUROC ≥ 0.96 (remove_direct_labels protocol)
- [ ] Zero new orphaned morphisms (audit_provenance.py)
- [ ] source strings on all 2,329 morphisms remain populated after rebuild
- [ ] Benchmark metrics reported with full protocol spec
- [ ] Code reviewed by 1+ other developer

---

## Next Steps

### To understand specific components:

- [API_REFERENCE.md](API_REFERENCE.md) — Core APIs with examples
- [STRATEGIES_IN_DEPTH.md](STRATEGIES_IN_DEPTH.md) — Runtime strategy profiles
- [CONTRIBUTING.md](CONTRIBUTING.md) — Adding features

### To extend the system:

1. Add a new strategy (see "Adding a New Strategy" above)
2. Add new data source (modify `build_tier1.py`)
3. Add new object type (modify Category class)

### To audit the system:

- [VALIDATION_AND_BENCHMARKS.md](VALIDATION_AND_BENCHMARKS.md) — Metrics & validation
- [EVIDENCE_AND_PROVENANCE.md](EVIDENCE_AND_PROVENANCE.md) — Data sources

---

*Last updated: 2026-05-28 (runtime strategy profiles; conditional Yoneda integration)*
iles; conditional Yoneda integration)*
