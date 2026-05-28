# API Reference

**Purpose**: Detailed API documentation with code examples.

**Audience**: Developers integrating or extending the system

---

## Core Runtime API

### Category Class

Main entry point for the categorical runtime.

```python
from core.category import Category

cat = Category(name='DrugRepurposing')
```

#### Methods

##### `add(name: str, **kwargs) -> Object`

Add an object to the category.

```python
drug = cat.add('Sorafenib', type_name='Drug',
               metadata={'smiles': 'CC(C)Nc1cc(I)c(Nc2ccc(F)c(Cl)c2)cc1F'})
protein = cat.add('BRAF', type_name='Protein')
disease = cat.add('Melanoma', type_name='Disease')
```

**Parameters**:
- `name`: Unique identifier (string)
- `type_name`: Object type ('Drug', 'Protein', 'Disease', custom); default is `"Object"`
- `metadata`: Dict with optional properties (SMILES, molecular weight, etc.)
- `provenance`: Optional source string for the object

**Returns**: Object instance

---

##### `connect(source: str, target: str, name: str = "r", confidence: float = 1.0, fn: Callable = None, **metadata) -> Morphism`

Add a morphism (relationship) between objects.

```python
m1 = cat.connect('Sorafenib', 'BRAF', name='inhibits',
                 confidence=0.95, source_ref='PMID:15001789')

m2 = cat.connect('BRAF', 'Melanoma', name='mutated_in',
                 confidence=0.91, source_ref='PMID:15184864')
```

**Parameters**:
- `source`: Source object name
- `target`: Target object name
- `name`: Morphism type ('inhibits', 'mutated_in', 'treats', etc.)
- `confidence`: Relationship strength [0, 1]
- `fn`: Optional callable for executable morphisms
- `metadata`: Extra key-value data. In the current `connect()` shorthand, extra
  fields are stored in `morphism.metadata`; construct `Morphism(...)` and call
  `add_morphism()` when you need to set the dedicated `provenance` field.

**Returns**: Morphism instance

---

##### `find_paths(source: str, target: str, max_length: int = 10) -> List[Path]`

Find all paths between two objects.

```python
paths = cat.find_paths('Sorafenib', 'Melanoma', max_length=4)

for path in paths:
    print(f"Weight: {path.weight:.3f}")
    print(f"Morphism ids: {path.morphism_ids}")
```

**Parameters**:
- `source`: Start object name
- `target`: End object name
- `max_length`: Maximum path length (default 4)

**Returns**: List of Path objects (ordered by confidence, descending)

**Path properties**:
```python
path.morphism_ids  # Ordered morphism ids along the path
path.weight        # Product of morphism confidences under the multiplicative quantale
path.length        # Number of edges in path
path.source        # Start object name
path.target        # End object name
```

---

### Drug Repurposing Scoring API

`core.Category` does not expose a `score_pair()` method. Drug-repurposing
scoring lives in `validation.repurposing_benchmark`:

```python
from validation.repurposing_benchmark import load_full_typed_view, make_strategies, score_pair

category, _ = load_full_typed_view(remove_direct_labels=False)
strategies = make_strategies(category)
score, votes = score_pair(strategies, 'Sorafenib', 'Melanoma', fail_on_error=True)
print(f"Score: {score:.3f} (threshold: 0.50)")
```

Live/as-loaded scoring uses 8 modules when Yoneda has visible known-treatment
comparators. Strict `remove_direct_labels` scoring uses 7 active modules because
those comparators are removed before scoring.

---

##### `get(name: str) -> Object | None`

Retrieve an object by name.

```python
drug = cat.get('Sorafenib')
print(f"Type: {drug.type_name}")
```

---

##### `objects() -> List[Object]`

List all objects (optionally filtered by type).

```python
all_drugs = [obj for obj in cat.objects() if obj.type_name == 'Drug']
drugs_subset = all_drugs[:10]

print(f"Total drugs: {len(all_drugs)}")
```

---

##### `morphisms()`, `morphisms_from(source)`, `morphisms_to(target)`

List morphisms (optionally filtered).

```python
# All morphisms from Sorafenib
morphisms_from_drug = cat.morphisms_from('Sorafenib')

# All morphisms to Melanoma
morphisms_to_disease = cat.morphisms_to('Melanoma')
```

---

## Persistence API

### KomposOSStore

SQLite-backed persistence layer.

```python
from data.store import KomposOSStore

store = KomposOSStore('data/drugs/tier1.db')
```

#### Methods

##### `get_object(name: str) -> StoredObject | None`

Retrieve object from database.

```python
drug = store.get_object('Sorafenib')
```

---

##### `add_object(obj: StoredObject) -> bool`

Write object to database.

```python
from data.store import StoredObject

obj = StoredObject(name='NewDrug', type_name='Drug')
store.add_object(obj)
```

---

##### `list_objects(limit: int = 100, offset: int = 0) -> List[StoredObject]`

Query objects with pagination.

```python
# Safe for production: always use limit=None for full results
all_objects = store.list_objects(limit=None)

# Type-specific query
drugs = store.get_objects_by_type('Drug')
```

---

##### `list_morphisms(limit: int = 100, offset: int = 0) -> List[StoredMorphism]`

Query morphisms.

```python
morphisms = store.list_morphisms(limit=None)
```

---

## Validation API

### Benchmark Harness

```python
from validation.repurposing_benchmark import load_full_typed_view, evaluate_category

# Load database
category, missing_endpoints = load_full_typed_view(remove_direct_labels=True)

# Evaluate protocol
result = evaluate_category(
    category,
    view='full_typed',
    protocol='remove_direct_labels',
    compute_ci=False,
)

# Report metrics
print(f"AUROC: {result.auroc:.3f}")
print(f"AUPRC: {result.auprc:.3f}")
print(f"Hits@10: {result.hits_at_10:.2f}")
```

---

### Triage CLI

```bash
python validation/triage.py Melanoma --top 10 --json
```

Programmatic access uses the same helper functions as the CLI:

```python
from validation.repurposing_benchmark import load_full_typed_view, drug_disease_pairs, make_strategies
from validation.triage import triage_disease

category, _ = load_full_typed_view()
drugs, diseases, positives = drug_disease_pairs(category)
strategies = make_strategies(category)
results = triage_disease(category, strategies, 'Melanoma', positives, top=10, show_all=False)
```

---

### Trace Prediction

```bash
python validation/trace_prediction.py Sorafenib Melanoma
```

Programmatic access:

```python
from validation.repurposing_benchmark import load_full_typed_view, make_strategies
from validation.trace_prediction import trace_pair

category, _ = load_full_typed_view()
strategies = make_strategies(category)
trace = trace_pair(category, 'Sorafenib', 'Melanoma', strategies)
print(f"Evidence chains: {len(trace['paths'])}")
for path in trace['paths']:
    print(f"  {path['confidence']:.3f}: {path['description']}")
```

---

## Strategy API

### Adding a Custom Strategy

```python
from oracle.strategies import InferenceStrategy
from core.category import Category

class MyCustomStrategy(InferenceStrategy):
    name = "my_custom_strategy"

    def predict(self, source: str, target: str):
        # Return a list of oracle.prediction.Prediction objects.
        # See existing strategies in oracle/strategies.py for exact patterns.
        return []
```

### Strategy Signature

Benchmark strategies are classes with a `predict(source, target)` method:

```python
class StrategyName(InferenceStrategy):
    name = "strategy_name"

    def predict(self, source: str, target: str):
        return []  # list[Prediction]
```

---

## Enrichment API

### Adding Quantitative Data

```python
from data.store import KomposOSStore

store = KomposOSStore('data/drugs/tier1.db')

# Current workflow: add quantitative evidence through manifest/build scripts.
# Direct in-place update helpers are not a stable public API.
```

---

## Bridge/Plugin API

### Registering a Plugin

```python
from core.category import Category
from bridges.base import Bridge

class MyBridge(Bridge):
    def register(self, cat: Category):
        """Called when bridge is registered with Category"""
        cat.add_hook('morphism_created', self.on_morphism_created)

    def on_morphism_created(self, morphism):
        """Called whenever a morphism is created"""
        # Your enrichment logic here
        pass

# Use
bridge = MyBridge()
bridge.register(cat)
```

---

## Example: End-to-End Workflow

```python
from core.category import Category
from data.store import KomposOSStore
from validation.repurposing_benchmark import load_full_typed_view

# 1. Load existing database
print("Loading database...")
store = KomposOSStore('data/drugs/tier1.db')
cat, diseases = load_full_typed_view(store, view="full_typed")
print(f"Loaded {len(cat.objects())} objects (runtime view), {len(cat.morphisms())} morphisms")

# 2. Query a pair
print("\nScoring Sorafenib for Melanoma...")
from validation.repurposing_benchmark import make_strategies, score_pair
strategies = make_strategies(cat)
score, votes = score_pair(strategies, 'Sorafenib', 'Melanoma')
print(f"Score: {score:.3f}")

# 3. Find supporting paths
print("\nFinding mechanistic paths...")
paths = cat.find_paths('Sorafenib', 'Melanoma', max_length=3)
print(f"Found {len(paths)} paths:")
for i, path in enumerate(paths[:3], 1):
    hops = ' -> '.join(path.morphism_ids)
    print(f"  {i}. {hops} (weight: {path.weight:.3f})")

# 4. Trace evidence
from validation.trace_prediction import trace_pair
print("\nTracing evidence...")
trace = trace_pair(cat, 'Sorafenib', 'Melanoma', strategies)
print(f"Evidence chains: {len(trace['paths'])}")

# 5. Batch score all drugs for disease
print("\nScoring all drugs for Melanoma...")
drugs = [obj.name for obj in cat.objects() if obj.type_name == 'Drug']
scores = {drug: score_pair(strategies, drug, 'Melanoma')[0] for drug in drugs}

# 6. Rank and display
ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
print("\nTop 5 candidates:")
for rank, (drug, score) in enumerate(ranked[:5], 1):
    print(f"  {rank}. {drug}: {score:.3f}")
```

---

## Common Patterns

### Pattern 1: Find all drugs for a disease

```python
disease = 'Melanoma'
drugs = [obj.name for obj in cat.objects() if obj.type_name == 'Drug']

candidates = []
for drug in drugs:
    score = score_pair(strategies, drug, disease)[0]
    candidates.append((drug, score))

ranked = sorted(candidates, key=lambda x: x[1], reverse=True)
```

### Pattern 2: Find common targets for multiple drugs

```python
drugs = ['Sorafenib', 'Vemurafenib', 'Imatinib']

targets_sets = []
for drug in drugs:
    morphisms = cat.morphisms_from(drug)
    targets = {m.target for m in morphisms if m.name == 'inhibits'}
    targets_sets.append(targets)

common_targets = set.intersection(*targets_sets)
print(f"Common targets: {common_targets}")
```

### Pattern 3: Build evidence chain for a pair

```python
drug, disease = 'Sorafenib', 'Melanoma'

# Get all paths
paths = cat.find_paths(drug, disease, max_length=4)

# Extract evidence
evidence = []
for path in paths:
    for morphism_id in path.morphism_ids:
        morphism = cat.get_morphism(morphism_id)
        if morphism is None:
            continue
        evidence.append({
            'source': morphism.source,
            'target': morphism.target,
            'relation': morphism.name,
            'confidence': morphism.confidence,
            'provenance': morphism.provenance,
        })

# Display
for item in evidence:
    print(f"{item['source']} --{item['relation']}--> {item['target']} "
          f"({item['confidence']:.2f}, {item['provenance']})")
```

---

## Performance Tips

1. **Cache paths**: Use `@lru_cache` for repeated queries
2. **Use `limit=None`** in production to ensure complete results
3. **Batch operations**: Score all drugs at once, not in a loop
4. **Connection pooling**: Reuse KomposOSStore instances

---

## Error Handling

```python
try:
    if cat.get('UnknownDrug') is None:
        raise ValueError('Drug not in category')
    score, votes = score_pair(strategies, 'UnknownDrug', 'Melanoma')
except ValueError as e:
    print(e)
```

---

## See Also

- [ARCHITECTURE.md](ARCHITECTURE.md) — Design principles
- [STRATEGIES_IN_DEPTH.md](STRATEGIES_IN_DEPTH.md) — Strategy details
- [CONTRIBUTING.md](CONTRIBUTING.md) — Adding features

---

*Last updated: 2026-05-28 (API examples audited against current code names)*
