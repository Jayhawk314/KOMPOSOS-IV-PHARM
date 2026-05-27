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

##### `add(name: str, type_name: str, confidence: float = 1.0, metadata: dict = None) → Object`

Add an object to the category.

```python
drug = cat.add('Sorafenib', type_name='Drug',
               metadata={'smiles': 'CC(C)Nc1cc(I)c(Nc2ccc(F)c(Cl)c2)cc1F'})
protein = cat.add('BRAF', type_name='Protein')
disease = cat.add('Melanoma', type_name='Disease')
```

**Parameters**:
- `name`: Unique identifier (string)
- `type_name`: Object type ('Drug', 'Protein', 'Disease', custom)
- `confidence`: Prior confidence [0, 1] (default 1.0)
- `metadata`: Dict with optional properties (SMILES, molecular weight, etc.)

**Returns**: Object instance

---

##### `connect(source: str, target: str, name: str, confidence: float, provenance: str = None) → Morphism`

Add a morphism (relationship) between objects.

```python
m1 = cat.connect('Sorafenib', 'BRAF', name='inhibits',
                 confidence=0.95, provenance='PMID:12829955')

m2 = cat.connect('BRAF', 'Melanoma', name='mutated_in',
                 confidence=0.91, provenance='PMID:15184864')
```

**Parameters**:
- `source`: Source object name
- `target`: Target object name
- `name`: Morphism type ('inhibits', 'mutated_in', 'treats', etc.)
- `confidence`: Relationship strength [0, 1]
- `provenance`: PMID, ChEMBL ID, or reference

**Returns**: Morphism instance

---

##### `find_paths(source: str, target: str, max_length: int = 4) → List[Path]`

Find all paths between two objects.

```python
paths = cat.find_paths('Sorafenib', 'Melanoma', max_length=4)

for path in paths:
    print(f"Confidence: {path.confidence:.3f}")
    print(f"Morphisms: {[m.name for m in path.morphisms]}")
    print(f"Objects: {' → '.join([m.source.name + '(' + m.target.name + ')' for m in path.morphisms])}")
```

**Parameters**:
- `source`: Start object name
- `target`: End object name
- `max_length`: Maximum path length (default 4)

**Returns**: List of Path objects (ordered by confidence, descending)

**Path properties**:
```python
path.morphisms   # List of Morphism objects in order
path.confidence  # Product of morphism confidences
path.hops        # Number of edges in path
path.objects     # List of objects along path
```

---

##### `score_pair(drug: str, disease: str) → float`

Score a Drug-Disease pair using all 9 strategies.

```python
score = cat.score_pair('Sorafenib', 'Melanoma')
print(f"Score: {score:.3f} (threshold: 0.50)")
```

**Returns**: Float [0, 1] (0.50 is decision threshold)

---

##### `get_object(name: str) → Object`

Retrieve an object by name.

```python
drug = cat.get_object('Sorafenib')
print(f"Type: {drug.type_name}, Confidence: {drug.confidence}")
```

---

##### `list_objects(type_name: str = None, limit: int = 100) → List[Object]`

List all objects (optionally filtered by type).

```python
all_drugs = cat.list_objects(type_name='Drug', limit=None)  # All drugs
drugs_subset = cat.list_objects(type_name='Drug', limit=10)  # First 10

print(f"Total drugs: {len(all_drugs)}")
```

**Important**: Always specify `limit=None` for production queries (default limit=100 is safety measure).

---

##### `list_morphisms(source: str = None, target: str = None, limit: int = 100) → List[Morphism]`

List morphisms (optionally filtered).

```python
# All morphisms from Sorafenib
morphisms_from_drug = cat.list_morphisms(source='Sorafenib', limit=None)

# All morphisms to Melanoma
morphisms_to_disease = cat.list_morphisms(target='Melanoma', limit=None)
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

##### `get_object(name: str) → Object`

Retrieve object from database.

```python
drug = store.get_object('Sorafenib')
```

---

##### `add_object(obj: Object) → Object`

Write object to database.

```python
obj = Object(name='NewDrug', type_name='Drug', confidence=0.9)
store.add_object(obj)
```

---

##### `list_objects(type_name: str = None, limit: int = 100) → List[Object]`

Query objects with pagination.

```python
# Safe for production: always use limit=None for full results
all_objects = store.list_objects(limit=None)
```

---

##### `list_morphisms(source_id: int = None, target_id: int = None, limit: int = 100) → List[Morphism]`

Query morphisms.

```python
morphisms = store.list_morphisms(limit=None)
```

---

## Validation API

### Benchmark Harness

```python
from validation.repurposing_benchmark import (
    load_view, evaluate_protocol, report_metrics
)

# Load database
view = load_view('full_typed')

# Evaluate protocol
results = evaluate_protocol(view, protocol='remove_direct_labels')

# Report metrics
print(f"AUROC: {results['auroc']:.3f}")
print(f"AUPRC: {results['auprc']:.3f}")
print(f"Hits@10: {results['hits_at_10']:.2f}")
```

---

### Triage CLI

```bash
python validation/triage.py Melanoma --top 10 --json
```

Programmatic access:

```python
from validation.triage import run_triage

results = run_triage(disease='Melanoma', top=10, output_format='json')
print(results)
```

---

### Trace Prediction

```bash
python validation/trace_prediction.py Melanoma Sorafenib
```

Programmatic access:

```python
from validation.trace_prediction import trace_pair

trace = trace_pair('Melanoma', 'Sorafenib')
print(f"Evidence chains: {len(trace['paths'])}")
for path in trace['paths']:
    print(f"  {path['confidence']:.3f}: {path['description']}")
```

---

## Strategy API

### Adding a Custom Strategy

```python
from oracle import STRATEGIES
from core.category import Category

def my_custom_strategy(cat: Category, drug: str, disease: str) -> float:
    """
    Custom scoring strategy.

    Args:
        cat: Category instance
        drug: Drug name (string)
        disease: Disease name (string)

    Returns:
        Score [0, 1]
    """
    # Your logic here
    paths = cat.find_paths(drug, disease, max_length=4)
    if not paths:
        return 0.0

    # Example: average confidence of top 3 paths
    top_paths = sorted(paths, key=lambda p: p.confidence, reverse=True)[:3]
    score = sum(p.confidence for p in top_paths) / len(top_paths) if top_paths else 0.0

    return max(0.0, min(1.0, score))  # Clamp to [0, 1]

# Register strategy
STRATEGIES['my_custom_strategy'] = my_custom_strategy
```

### Strategy Signature

All strategies must have this signature:

```python
def strategy_score(cat: Category, drug: str, disease: str) -> float:
    """Returns score [0, 1]"""
    pass
```

---

## Enrichment API

### Adding Quantitative Data

```python
from data.store import KomposOSStore

store = KomposOSStore('data/drugs/tier1.db')

# Add IC50 data to morphism
morphism = store.get_morphism_by_names('Sorafenib', 'BRAF')
morphism.metadata['ic50_nm'] = 25.8
morphism.provenance = 'PMID:12829955'
store.update_morphism(morphism)
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
from domains.bio.loader import BioDomainLoader
from data.store import KomposOSStore

# 1. Load existing database
print("Loading database...")
loader = BioDomainLoader()
cat = loader.load('data/drugs/tier1.db')
print(f"Loaded {len(cat.objects)} objects, {len(cat.morphisms)} morphisms")

# 2. Query a pair
print("\nScoring Sorafenib for Melanoma...")
score = cat.score_pair('Sorafenib', 'Melanoma')
print(f"Score: {score:.3f}")

# 3. Find supporting paths
print("\nFinding mechanistic paths...")
paths = cat.find_paths('Sorafenib', 'Melanoma', max_length=3)
print(f"Found {len(paths)} paths:")
for i, path in enumerate(paths[:3], 1):
    hops = ' → '.join([m.name for m in path.morphisms])
    print(f"  {i}. {hops} (confidence: {path.confidence:.3f})")

# 4. Trace evidence
from validation.trace_prediction import trace_pair
print("\nTracing evidence...")
trace = trace_pair('Melanoma', 'Sorafenib')
print(f"Top PMIDs: {trace['pmids'][:3]}")

# 5. Batch score all drugs for disease
print("\nScoring all drugs for Melanoma...")
drugs = [obj.name for obj in cat.list_objects(type_name='Drug', limit=None)]
scores = {drug: cat.score_pair(drug, 'Melanoma') for drug in drugs}

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
drugs = [obj.name for obj in cat.list_objects(type_name='Drug', limit=None)]

candidates = []
for drug in drugs:
    score = cat.score_pair(drug, disease)
    candidates.append((drug, score))

ranked = sorted(candidates, key=lambda x: x[1], reverse=True)
```

### Pattern 2: Find common targets for multiple drugs

```python
drugs = ['Sorafenib', 'Vemurafenib', 'Imatinib']

targets_sets = []
for drug in drugs:
    morphisms = cat.list_morphisms(source=drug, limit=None)
    targets = {m.target.name for m in morphisms if m.name == 'inhibits'}
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
    for morphism in path.morphisms:
        evidence.append({
            'source': morphism.source.name,
            'target': morphism.target.name,
            'relation': morphism.name,
            'confidence': morphism.confidence,
            'pmid': morphism.provenance
        })

# Display
for item in evidence:
    print(f"{item['source']} --{item['relation']}--> {item['target']} "
          f"({item['confidence']:.2f}, {item['pmid']})")
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
    score = cat.score_pair('UnknownDrug', 'Melanoma')
except ObjectNotFoundError as e:
    print(f"Drug not in database: {e}")

try:
    paths = cat.find_paths('Sorafenib', 'UnknownDisease')
except ObjectNotFoundError as e:
    print(f"Disease not in database: {e}")
```

---

## See Also

- [ARCHITECTURE.md](ARCHITECTURE.md) — Design principles
- [STRATEGIES_IN_DEPTH.md](STRATEGIES_IN_DEPTH.md) — Strategy details
- [CONTRIBUTING.md](CONTRIBUTING.md) — Adding features

---

*Last updated: 2026-05-26*
