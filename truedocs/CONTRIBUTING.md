# Contributing

**Purpose**: Guidelines for contributing code, data, and documentation.

**Audience**: Developers, data scientists, researchers

---

## Code Standards

### Style Guide

- **PEP 8** (enforced by flake8)
- **Type hints** (Python 3.10+): All function signatures must have type hints
- **Docstrings**: Google style, mandatory for all public functions
- **Line length**: 100 characters

### Example

```python
def compose_morphisms(
    source: Object,
    target: Object,
    max_depth: int = 4
) -> List[Morphism]:
    """
    Compose morphisms between source and target objects.

    Args:
        source: Starting object
        target: Ending object
        max_depth: Maximum morphism chain depth

    Returns:
        List of composed morphisms (sorted by confidence, descending)

    Raises:
        ValueError: If source or target not in category
    """
    # Implementation
    pass
```

### Pre-commit Checklist

Before committing:

```bash
# Format code
black oracle/my_strategy.py

# Type check
mypy oracle/my_strategy.py

# Lint
flake8 oracle/my_strategy.py

# Run tests
pytest tests/test_oracle_strategies.py -k my_strategy
```

---

## Git Workflow

### Branch naming

```
feature/my_new_feature
bugfix/issue_number
enhancement/improvement_name
```

### Commit messages

```
[type] Short description (present tense, imperative)

Optional longer explanation:
- Point 1
- Point 2

Closes #123 (if closing an issue)

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
```

**Types**: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`

### Pull Request

1. Create feature branch: `git checkout -b feature/my_feature`
2. Commit changes: `git commit -m "[feat] Add my feature"`
3. Push: `git push origin feature/my_feature`
4. Open PR with description of changes
5. Pass all CI tests and code review
6. Merge to main

---

## Adding a New Strategy

**6-step template**:

### Step 1: Create file

```python
# oracle/my_new_strategy.py
"""My new strategy description"""

from oracle.prediction import Prediction
from oracle.strategies import InferenceStrategy

class MyNewStrategy(InferenceStrategy):
    name = "my_new_strategy"

    def predict(self, source: str, target: str) -> list[Prediction]:
        """Return predictions for a source-target pair."""
        # Your logic here
        return []
```

### Step 2: Register strategy

Wire it into the active profile in `validation/repurposing_benchmark.py`:

```python
from oracle.my_new_strategy import MyNewStrategy

def make_strategies(category):
    strategies = [
        # existing runtime modules...
        MyNewStrategy(category),
    ]
    return strategies
```

### Step 3: Write tests

```python
# tests/test_my_new_strategy.py
import pytest
from oracle.my_new_strategy import MyNewStrategy

def test_score_range():
    """Score must be [0, 1]"""
    predictions = MyNewStrategy(cat).predict('Sorafenib', 'Melanoma')
    assert all(0.0 <= pred.confidence <= 1.0 for pred in predictions)

def test_known_pairs():
    """Test on known approvals"""
    predictions = MyNewStrategy(cat).predict('Sorafenib', 'Melanoma')
    assert predictions
```

### Step 4: Run regression test

```bash
pytest tests/test_repurposing_benchmark.py
```

Verify:
- 44/44 self-check passes
- AUROC ≥ 0.96 (remove_direct_labels protocol)

### Step 5: Ablation test

```bash
python validation/ablation_study.py
```

Verify:
- Your strategy contributes positively (or is minor)
- No negative AUROC impact

### Step 6: Document

Add to `truedocs/STRATEGIES_IN_DEPTH.md`:
- Purpose
- Mathematical formula
- Code location
- Performance impact

---

## Adding Data

### Updating the manifest

Edit `data/drugs/tier1_manifest.json`:

```json
{
  "version": "2.1",
  "build_date": "2026-06-01",
  "objects": {
    "drugs": [
      {"name": "NewDrug", "chembl_id": "CHEMBL999", "cas": "..."}
    ],
    "proteins": [
      {"name": "NewTarget", "uniprot_id": "P12345"}
    ]
  },
  "sources": {
    "custom_source": "version 1.0"
  }
}
```

### Implement importer

```python
# data/drugs/importers/custom_importer.py
from data.store import KomposOSStore

def import_custom_source(store: KomposOSStore, data_file: str):
    """Import custom data source"""
    with open(data_file) as f:
        for line in f:
            # Parse line
            # Add object or morphism to store
            pass
```

### Integrate into build

Edit `data/drugs/build_tier1.py`:

```python
from data.drugs.importers.custom_importer import import_custom_source

# In build() function:
import_custom_source(store, 'data/external/custom_data.txt')
```

### Rebuild and validate

```bash
python data/drugs/build_tier1.py --manifest data/drugs/tier1_manifest.json
python validation/audit_provenance.py
python validation/repurposing_benchmark.py --view full_typed --protocol remove_direct_labels
```

---

## Validation Checklist

Before submitting PR:

- [ ] Code style: `flake8` passes
- [ ] Type hints: `mypy` passes
- [ ] Tests pass: `pytest tests/`
- [ ] Self-check: 44/44 FDA pairs recoverable
- [ ] AUROC ≥ 0.96: (remove_direct_labels protocol)
- [ ] Zero new orphaned morphisms: `audit_provenance.py`
- [ ] source strings on all 2,329 morphisms remain populated; new edges have source/provenance strings
- [ ] Metrics reported correctly: Specify view, protocol, pair count
- [ ] Documentation updated: Code comments, truedocs/ docs, or docstrings

---

## Metrics to Report

When reporting AUROC or other metrics, always include:

```
AUROC: 0.9705
  View: full_typed
  Protocol: remove_direct_labels
  Positives: 44
  Negatives/unlabeled pairs: 1516
  95% CI: [0.9519, 0.9844]
  Label policy: Direct Drug→Disease edges removed during scoring
```

---

## Code Review Standards

### What we look for

- [ ] Correctness: Does code do what it claims?
- [ ] Tests: Are there tests? Do they cover edge cases?
- [ ] Performance: Is it efficient? Will it scale?
- [ ] Clarity: Can someone else understand and modify this?
- [ ] Honesty: Are claims accurate? Are limitations documented?

### Example feedback

```
✓ Looks good. Tests cover main cases. Minimal and clear.

? Does this handle the case where no paths exist?
  Consider adding a test for empty path set.

⚠ Consider memoizing path_finding() to avoid recomputation
  in tight loops. See Issue #42 for performance target.

✗ Claiming "100% accuracy" contradicts previous work.
  Suggest: "Improved ranking AUROC to 0.96 (from 0.89)."
```

---

## Reporting Issues

### Bug report template

```
Title: [BUG] Brief description

Description:
- What I did: ...
- What I expected: ...
- What happened: ...

Reproducible example:
python validation/triage.py Melanoma  # Shows error X

Environment:
- Python version: 3.10.x
- OS: macOS / Linux / Windows
```

### Feature request template

```
Title: [FEATURE] Brief description

Description:
- What problem does this solve?
- Why is it needed?

Proposed solution:
- Describe your idea
- Are there alternatives?

Impact:
- How does this affect AUROC?
- How does this affect users?
```

---

## Documentation

### When to document

- New public API: Add docstring
- New strategy: Add to STRATEGIES_IN_DEPTH.md
- New data source: Add to EVIDENCE_AND_PROVENANCE.md
- Architecture change: Update ARCHITECTURE.md
- Bug fix: Document in commit message

### Documentation checklist

- [ ] Docstrings for all public functions
- [ ] Code comments for non-obvious logic
- [ ] README updated if API changes
- [ ] Examples provided for new features
- [ ] Links cross-reference related docs

---

## Communication

### Honest claims

We value accuracy over optimism. Example:

```
❌ Bad: "Our system achieves 97.47% accuracy"
   (Misleading: AUROC ≠ accuracy, and on a 50% base rate)

✓ Good: "AUROC 0.9705 (full_typed view, remove_direct_labels
   protocol, 44 FDA pairs, 1516 unlabeled comparison pairs, 95% CI
   [0.9519, 0.9844]). Current strict profile uses 7 active modules."
```

### Limitations

Always document what your code/strategy doesn't do:

```python
def predict(self, source: str, target: str):
    """
    Score Drug-Disease pairs using [method].

    Returns:
        Score [0, 1]

    Limitations:
    - Doesn't account for patient genomics
    - Relies on [external data source]
    - Performance untested on [domain]
    """
    pass
```

---

## Performance Optimization

### Profiling

```bash
python -m cProfile -s cumulative validation/triage.py Melanoma
```

Look for:
- Repeated path finding (cache!)
- Repeated database queries (batch!)
- Slow strategy scoring (vectorize!)

### Common bottlenecks

1. **Path finding**: O(n × m^h). Solution: memoize or limit path depth.
2. **Strategy voting**: O(n × strategies). Solution: parallelize.
3. **Database queries**: Solution: Use indexes, batch queries.

---

## Releasing

### Version numbering

`MAJOR.MINOR.PATCH`

- MAJOR: Architecture/conceptual changes (breaking changes)
- MINOR: New features (backward-compatible)
- PATCH: Bug fixes

### Release checklist

- [ ] Bump version in `__init__.py`
- [ ] Update CHANGELOG.md
- [ ] Run full test suite: `pytest tests/`
- [ ] Run benchmark: `python validation/repurposing_benchmark.py ... --ci`
- [ ] Tag release: `git tag v2.0.0`
- [ ] Push: `git push && git push --tags`

---

## Code of Conduct

We're committed to a welcoming, respectful community. Please:
- Be inclusive and respectful
- Focus on the code, not the person
- Assume good intent
- Resolve conflicts respectfully

---

## Questions?

Open an issue on GitHub or email the maintainers.

---

*Last updated: 2026-05-28*
