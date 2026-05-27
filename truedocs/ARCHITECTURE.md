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
         └─ Strategies (9 scoring strategies)
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
    confidence: float = 1.0
    metadata: dict
    provenance: str  # PMID or ChEMBL ID

class Morphism:
    name: str  # "inhibits", "mutated_in", "treats"
    source: Object
    target: Object
    confidence: float  # 0.0–1.0
    provenance: str

class Category:
    """Main runtime for drug repurposing graph"""
    def add(self, name: str, type_name: str) -> Object
    def connect(self, src: str, tgt: str, name: str, confidence: float) -> Morphism
    def find_paths(self, src: str, tgt: str, max_length: int = 4) -> List[Path]
    def score_pair(self, drug: str, disease: str) -> float
```

**Key design decisions**:

1. **Multiplicative composition**: Path confidence = product of edge confidences
   - If link A = 90% confident, link B = 80% confident, chain = 72%
   - Models honest uncertainty (uncertain links compound)

2. **Confidence as first-class value**: Every morphism carries a score 0.0–1.0
   - Allows nuanced prediction (not just binary relationships)
   - Propagates through paths automatically

3. **Persistence layer**: All objects/morphisms auto-sync to SQLite (`KomposOSStore`)
   - Database is the source of truth
   - No in-memory divergence from disk

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

**Integration**: COG scores are aggregated as one of the 9 strategies (weight 0.15).

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
from domains.bio.loader import BioDomainLoader

# Load database into Category
loader = BioDomainLoader()
cat = loader.load('data/drugs/tier1.db')

# cat now has 464 objects, 5382 morphisms
print(len(cat.objects), len(cat.morphisms))
```

### 2. Path Finding

```python
# Find all paths from Sorafenib to Melanoma (max 4 hops)
paths = cat.find_paths('Sorafenib', 'Melanoma', max_length=4)

for path in paths:
    hops = [morphism.name for morphism in path.morphisms]
    confidence = path.confidence  # multiplicative
    print(f"Path: {' → '.join(hops)}, Confidence: {confidence:.3f}")
```

Output:
```
Path: inhibits → mutated_in, Confidence: 0.865
Path: inhibits → promotes → supports, Confidence: 0.597
Path: inhibits → upregulates → activates, Confidence: 0.412
...
```

### 3. Strategy Voting

```python
from oracle import strategies

# Initialize all 9 strategies
score_composition = strategies.composition_score(cat, 'Sorafenib', 'Melanoma')
score_binding = strategies.binding_evidence_score(cat, 'Sorafenib', 'Melanoma')
score_yoneda = strategies.yoneda_distance_score(cat, 'Sorafenib', 'Melanoma')
# ... (6 more strategies)

# Aggregate votes (uniform weights)
final_score = mean([
    score_composition, score_binding, score_yoneda,
    score_coherence, score_conjecture, score_natural_transform,
    score_game_theory, score_bayesian
])
```

### 4. Persistence

All objects/morphisms auto-sync to SQLite:

```python
from data.store import KomposOSStore

store = KomposOSStore('data/drugs/tier1.db')
drug = store.get_object('Sorafenib')
morphisms_from_drug = store.list_morphisms(source='Sorafenib')
```

**Database schema**:
```sql
CREATE TABLE objects (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE,
    type_name TEXT,
    confidence REAL,
    provenance TEXT
);

CREATE TABLE morphisms (
    id INTEGER PRIMARY KEY,
    name TEXT,
    source_id INTEGER,
    target_id INTEGER,
    confidence REAL,
    provenance TEXT,
    FOREIGN KEY(source_id) REFERENCES objects(id),
    FOREIGN KEY(target_id) REFERENCES objects(id)
);
```

---

## Oracle Strategies (9 Total)

All strategy implementations are in `oracle/`:

| Strategy | File | Role | Weight |
|----------|------|------|--------|
| Composition | `oracle/composition_strategy.py` | Dominant path-based | Dominant |
| Path Bonus | `oracle/path_bonus_strategy.py` | High-confidence bonus | Tuning |
| Binding Evidence | `oracle/binding_strategy.py` | IC50 + drug properties | Moderate |
| Yoneda Distance | `oracle/yoneda_strategy.py` | Structural similarity | Bonus |
| Coherence | `oracle/coherence_strategy.py` | Logical consistency | Minor |
| Conjecture | `oracle/conjecture_strategy.py` | Rule learning | Minor |
| Natural Transform | `oracle/natural_transform_strategy.py` | Morphism alignment | Negligible |
| Game Theory | `oracle/game_theory_strategy.py` | Equilibrium analysis | Negligible |
| Bayesian | `oracle/bayesian_strategy.py` | Probabilistic | Negligible |

**Aggregation**: Normalize each strategy to [0, 1], compute arithmetic mean.

See [STRATEGIES_IN_DEPTH.md](STRATEGIES_IN_DEPTH.md) for mathematical details.

---

## Plugin System (Bridges)

Plugins extend functionality without modifying core:

### ABPP Bridge (`abpp_bridge.py`)

Loads experimental IC50 data (65 entries) and enriches morphisms.

```python
from bridges.abpp_bridge import ABPPBridge

bridge = ABPPBridge()
bridge.register()  # Hooks into morphism creation

# When a Drug-Protein morphism is created, ABPP queries:
# - Is there an IC50 value for this pair?
# - If yes, enrich morphism with quantitative data
```

### Boltz2 Bridge (`boltz2_bridge.py`)

Heuristic binding prediction (fallback when no ABPP data).

Uses:
- Lipinski drug-likeness rules
- Target properties (Pfam domains)
- Similarity to known binders

Confidence: 0.60–0.80 (lower than experimental ABPP)

### COG Reasoning Bridge (`bridges/cog_reasoning.py`)

Integrates claim verification.

```python
from bridges.cog_reasoning import COGBridge

cog = COGBridge()
# Analyzes prediction for logical consistency
consistency_score = cog.coherence_score(cat, 'Sorafenib', 'Melanoma')
```

---

## Execution Model: End-to-End

```
User input: triage.py Melanoma
         ↓
Load database: tier1.db → Category (464 objects, 5382 morphisms)
         ↓
For each drug in tier1.db:
  └─ Find all paths: Drug → ... → Melanoma (max 4 hops)
     ├─ Composition score: best path confidence
     ├─ Binding evidence: IC50 + drug properties
     ├─ Yoneda distance: structural similarity
     ├─ ... (6 more strategies)
     └─ Final score = mean of 9 strategy scores
         ↓
Rank drugs by score (descending)
         ↓
Format output: top 10 candidates with evidence chains + PMIDs
         ↓
Display to user
```

**Computational cost**:
- Path finding: O(n × m^h) where n=drugs, m=edges, h=max path length
- Strategy scoring: O(n × strategies) = O(78 × 9) = ~700 evaluations
- Typical runtime: 2–5 seconds for full disease triage (first run includes path cache)

---

## Module Dependency Map

```
triage.py (entry point)
    ↓
validation/triage.py
    ├─ core/category.py (Category runtime)
    ├─ oracle/ (9 strategies)
    ├─ domains/bio/loader.py (Database loading)
    ├─ data/store.py (SQLite backend)
    ├─ bridges/ (COG, OPTIMUS, ABPP, Boltz2)
    └─ chemistry/ (Pfam, drug properties)

repurposing_benchmark.py (evaluation harness)
    ├─ core/category.py
    ├─ oracle/
    ├─ domains/bio/loader.py
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

from core.category import Category

def my_strategy_score(cat: Category, drug: str, disease: str) -> float:
    """Your custom scoring logic"""
    # Compute score 0.0–1.0
    return score
```

### Step 2: Register in oracle/__init__.py

```python
from oracle.my_strategy import my_strategy_score

STRATEGIES = {
    'composition': composition_score,
    'binding_evidence': binding_evidence_score,
    ...
    'my_strategy': my_strategy_score,  # Add here
}
```

### Step 3: Add to aggregation

In `oracle/__init__.py` or `validation/repurposing_benchmark.py`:

```python
def score_pair(cat, drug, disease):
    votes = {
        'composition': composition_score(...),
        'binding_evidence': binding_evidence_score(...),
        ...
        'my_strategy': my_strategy_score(...),  # Include in voting
    }
    return mean(votes.values())
```

### Step 4: Test regression

```bash
pytest tests/test_oracle_strategies.py -k "my_strategy"
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
CREATE INDEX idx_morphism_source ON morphisms(source_id);
CREATE INDEX idx_morphism_target ON morphisms(target_id);
CREATE INDEX idx_object_name ON objects(name);
```

### Parallel Scoring

Score multiple drugs in parallel:

```python
from multiprocessing import Pool

def score_all_drugs(cat, disease, n_workers=4):
    with Pool(n_workers) as pool:
        scores = pool.starmap(
            lambda drug: (drug, score_pair(cat, drug, disease)),
            [(d, disease) for d in cat.drugs()]
        )
    return scores
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
- PMID citations in docstrings
- Example usage in module docstrings

---

## Deployment Checklist

Before merging to main:

- [ ] All tests pass (pytest tests/)
- [ ] 44/44 self-check passes
- [ ] AUROC ≥ 0.96 (remove_direct_labels protocol)
- [ ] Zero new orphaned morphisms (audit_provenance.py)
- [ ] 100% provenance on new edges (all have PMID/ChEMBL)
- [ ] Benchmark metrics reported with full protocol spec
- [ ] Code reviewed by 1+ other developer

---

## Next Steps

### To understand specific components:

- [API_REFERENCE.md](API_REFERENCE.md) — Core APIs with examples
- [STRATEGIES_IN_DEPTH.md](STRATEGIES_IN_DEPTH.md) — All 9 strategies
- [CONTRIBUTING.md](CONTRIBUTING.md) — Adding features

### To extend the system:

1. Add a new strategy (see "Adding a New Strategy" above)
2. Add new data source (modify `build_tier1.py`)
3. Add new object type (modify Category class)

### To audit the system:

- [VALIDATION_AND_BENCHMARKS.md](VALIDATION_AND_BENCHMARKS.md) — Metrics & validation
- [EVIDENCE_AND_PROVENANCE.md](EVIDENCE_AND_PROVENANCE.md) — Data sources

---

*Last updated: 2026-05-26 (5-layer stack, 9 strategies, Yoneda integration)*
