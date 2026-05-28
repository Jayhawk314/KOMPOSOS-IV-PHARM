# Strategies In Depth

**Purpose**: Detailed explanation of the current runtime strategy profiles, historical strategy experiments, mathematics, code locations, and audit caveats.

**Audience**: Researchers, developers extending the system

---

## Overview

The current drug-repurposing runtime does not use the older fixed-count ensemble described in early notes. Strict `remove_direct_labels` validation uses 7 active modules; live/as-loaded triage can use 8 when Yoneda comparators are visible. Some sections below describe historical or development modules and should not be quoted as current active benchmark components unless they appear in `validation/repurposing_benchmark.py::make_strategies`.

| Runtime module | Active profile | Role |
|----------------|----------------|------|
| `kan_extension` | strict + live | Analogy/extension over typed graph neighborhoods |
| `structural_hole` | strict + live | Graph-structure bridge signal |
| `composition` | strict + live | Mechanistic Drug→...→Disease paths |
| `yoneda_pattern` | strict + live | Local categorical fingerprint patterning |
| `fibration_lift` | strict + live | Typed lifting over related objects |
| `topos_logic` | strict + live | Logic-style support from graph evidence |
| `binding_evidence` | strict + live | IC50 + drug/target compatibility |
| `yoneda_distance` | live only when direct labels are visible | Comparator similarity bonus |

**Ablation note**: Historical development runs showed composition as the dominant signal. Current strict full-system run is AUROC 0.9747 with 7 active modules; per-strategy ablations should be rerun under the corrected loader before being quoted as current.

---

## Strategy 1: Composition (Dominant)

**Purpose**: Find all Drug→Disease paths, weight by confidence.

**Formula**:

```
score = weighted_mean(path_confidences)
where path_confidence = ∏(edge_confidence)
```

**Code location**: `oracle/strategies.py::CompositionStrategy`

**Algorithm**:

```python
def composition_score(cat: Category, drug: str, disease: str) -> float:
    """Find all paths, weight by confidence"""
    paths = cat.find_paths(drug, disease, max_length=4)
    if not paths:
        return 0.0

    # Weight each path by its confidence (multiplicative)
    confidences = [path.weight for path in paths]

    # Favor drugs with many high-confidence paths
    if len(confidences) == 0:
        return 0.0
    if len(confidences) == 1:
        return confidences[0]

    # Weighted mean: sum(conf) / count, capped at 1.0
    return min(1.0, sum(confidences) / len(confidences))
```

**Example**:
- Drug→Protein→Disease path: confidence = 0.95 × 0.91 = 0.865
- Drug→Protein→Pathway→Disease path: confidence = 0.85 × 0.88 × 0.80 = 0.597
- Weighted mean = (0.865 + 0.597) / 2 = 0.731

**Performance**: Ablation shows -0.153 AUROC if removed (most important strategy).

**Interpretation**: Mechanistic paths are the core signal. Short, high-confidence paths (Drug → Protein → Disease) dominate.

---

## Strategy 2: Path Bonus

**Purpose**: Add small bonus for unusually high-confidence paths.

**Formula**:

```
bonus = min(0.25, 0.04 × sum(path_confidence))
final_score = composition_score + bonus
```

**Code location**: `validation/repurposing_benchmark.py::score_pair`

**Algorithm**:

```python
def path_bonus_score(cat: Category, drug: str, disease: str) -> float:
    """Add bonus for high-confidence paths"""
    paths = cat.find_paths(drug, disease, max_length=4)
    composition_weight = sum(p.weight for p in paths)
    return min(0.25, 0.04 * composition_weight)
```

**Hyperparameter**: Coefficient 0.04 was tuned via LOOCV grid search over [0.0, 0.20].

**Example**:
- Composition score: 0.88
- Path sum: 0.865 + 0.597 = 1.462
- Bonus: min(0.25, 0.04 × 1.462) = min(0.25, 0.058) = 0.058
- Final: 0.88 + 0.058 = 0.938

**Performance**: Ablation shows -0.015 AUROC if removed (tuning).

---

## Strategy 3: Binding Evidence

**Purpose**: Integrate IC50 data, drug properties, molecular compatibility.

**Formula**:

```
score = weighted_mean([
    abpp_score × 0.30,
    boltz2_score × 0.10,
    lipinski_score × 0.10,
    molecular_compat_score × 0.10,
    pfam_match_score × 0.10,
    morphism_confidence × 0.20
])
```

**Code location**: `oracle/binding_strategy.py`

**Components**:

### 1. ABPP Bridge (0.30 weight)

Experimental IC50 data (65 entries):

```python
# 1 if IC50 < 100 nM (tight binding)
# 0.8 if 100 nM < IC50 < 1000 nM
# 0.5 if 1000 nM < IC50 < 10000 nM
# 0 if IC50 >= 10000 nM (weak/no binding)
abpp_score = sigmoid((100 - ic50) / 100)
```

### 2. Boltz2 Bridge (0.10 weight)

Heuristic binding prediction (fallback):

```python
# Checks: Drug name similarity, target class (kinase inhibitor → kinase, etc.)
boltz2_score = 0.6 if target_has_kinase_domain and drug_inhibitor else 0.3
```

### 3. Lipinski Drug-Likeness (0.10 weight)

```python
# Count violations: MW > 500, logP > 5, HBD > 5, HBA > 10
violations = sum([
    drug.mw > 500,
    drug.logp > 5,
    drug.hbd > 5,
    drug.hba > 10
])
lipinski_score = 1.0 - (0.2 * violations)
```

### 4. Molecular Compatibility (0.10 weight)

Solubility, steric, reactivity scoring:

```python
solubility = score_solubility(drug, target)
steric = score_steric_compatibility(drug, target)
reactivity = score_reactivity_risk(drug, target)
molecular_score = mean([solubility, steric, 1 - reactivity])
```

### 5. Pfam Domain Matching (0.10 weight)

```python
# If drug is kinase inhibitor and target is kinase: 0.9
# If drug is GPCR agonist and target is GPCR: 0.9
# Otherwise: 0.5
domain_match = 0.9 if drug_class_matches_target_domain else 0.5
```

### 6. Morphism Confidence (0.20 weight)

Graph confidence from Category edge:

```python
morphism_conf = morphism.confidence  # 0.0–1.0
```

**Performance**: Ablation shows -0.045 AUROC if removed (moderate).

---

## Strategy 4: Yoneda Distance (conditional live triage)

**Purpose**: Structural similarity via presheaf fingerprints.

**Formula**:

```
score = 1 - jaccard_distance(drug_presheaf, reference_drug_presheaf)
where reference_drug = most similar approved drug for that disease
```

**Code location**: `oracle/yoneda_strategy.py`

**Algorithm**:

```python
def yoneda_distance_score(cat: Category, drug: str, disease: str) -> float:
    """Presheaf-based structural similarity"""

    # Build presheaf for drug (neighbors + relation weights)
    drug_presheaf = {}
    morphisms = cat.morphisms_from(drug)
    for m in morphisms:
        key = (m.target, m.name)
        drug_presheaf[key] = m.confidence

    # Find reference drugs (already approved for this disease)
    approved_for_disease = [m.source for m in cat.morphisms_to(disease)
                           if m.name == 'treats']

    if not approved_for_disease:
        return 0.0

    # Find most similar approved drug
    max_similarity = 0.0
    for ref_drug in approved_for_disease:
        ref_presheaf = build_presheaf(ref_drug)
        similarity = jaccard_similarity(drug_presheaf, ref_presheaf)
        max_similarity = max(max_similarity, similarity)

    return max_similarity
```

**Example**:

Sorafenib presheaf:
```python
{
    ('BRAF', 'inhibits'): 0.95,
    ('VEGFR2', 'inhibits'): 0.85,
    ('FLT3', 'inhibits'): 0.80,
    ('MEK1', 'activates'): 0.70,
}
```

Vemurafenib presheaf (reference drug):
```python
{
    ('BRAF', 'inhibits'): 0.97,
    ('VEGFR2', 'inhibits'): 0.88,
    ('KIT', 'inhibits'): 0.75,
}
```

Jaccard distance: |union| / |intersection| = 5 / 3 = 1.67, similarity = 1 - (1.67 - 1) = 0.60

**Integration**: Not averaged into the strict benchmark. In live/as-loaded triage, it is added as a small bonus (weight 0.06, capped 0.10) only when visible known-treatment comparators exist.

**Performance**: Historical development ablations suggested AUROC/AUPRC lift. Under the corrected strict `remove_direct_labels` loader, Yoneda distance has no comparators and is inactive, so those old deltas should not be quoted as current strict-benchmark impact.

**Drug equivalence classes discovered**:
- Binimetinib ≈ Cobimetinib (both MEK inhibitors)
- Encorafenib ≈ Vemurafenib (both BRAF inhibitors)
- Carboplatin ≈ Oxaliplatin (both platinum compounds)

---

## Historical/Experimental Module: Coherence

**Purpose**: Logical consistency via verdict lattices.

**Code location**: historical notes; not an active current module

**Idea**: Check if paths support or contradict each other.

```python
def coherence_score(cat: Category, drug: str, disease: str) -> float:
    """Measure logical consistency"""
    paths = cat.find_paths(drug, disease, max_length=4)

    # All paths should point to same conclusion
    # If one path says treatment works, another says it doesn't: lower score

    consensus = mean([path.weight for path in paths])
    variance = std([path.weight for path in paths])

    # Lower variance = more coherent
    coherence = 1.0 - (variance / 1.0)  # Normalize variance
    return max(0.0, min(1.0, coherence))
```

**Performance**: Historical only. Do not quote as current strict-benchmark impact without rerunning ablation.

---

## Historical/Experimental Module: Conjecture (Rule Learning)

**Purpose**: Learn inductive rules from data patterns.

**Code location**: `oracle/conjecture_strategy.py`

**Example rule**: "If drug inhibits BRAF, then it treats Melanoma with high confidence"

```python
def conjecture_score(cat: Category, drug: str, disease: str) -> float:
    """Rule-based prediction"""

    # Extract rules from all approved pairs
    rules = learn_rules(cat)  # [Rule, Rule, ...]

    # Match drug against rules
    matches = [rule for rule in rules if rule.matches(drug, disease)]

    if not matches:
        return 0.0

    # Average confidence of matching rules
    return mean([rule.confidence for rule in matches])
```

**Performance**: Ablation shows -0.002 AUROC if removed (negligible).

**Status**: Sparse (few rules generalize), experimental.

---

## Historical/Experimental Module: Natural Transformation

**Purpose**: Morphism alignment (category-theoretic concept).

**Code location**: `oracle/natural_transformation.py`

**Idea**: Do morphism patterns align across different drugs?

Example: If Sorafenib→BRAF and Vemurafenib→BRAF, they have aligned morphisms.

```python
def natural_transform_score(cat: Category, drug: str, disease: str) -> float:
    """Measure morphism alignment with reference drugs"""
    # Compare morphism patterns with approved drugs for the disease
    approved = [m.source for m in cat.morphisms_to(disease) if m.name == 'treats']

    if not approved:
        return 0.0

    # Count morphism overlaps
    drug_targets = set([m.target for m in cat.morphisms_from(drug)])
    approved_targets = set([m.target for m in cat.morphisms_from(approved[0])])

    overlap = len(drug_targets & approved_targets)
    union = len(drug_targets | approved_targets)

    return overlap / union if union > 0 else 0.0
```

**Performance**: Ablation shows ~0.0 AUROC impact (negligible).

---

## Historical/Experimental Module: Game Theory

**Purpose**: Equilibrium analysis of biological interactions.

**Code location**: `oracle/game_strategy.py`

**Idea**: Model drug-protein-disease as a game; compute equilibrium.

```python
def game_theory_score(cat: Category, drug: str, disease: str) -> float:
    """Compute equilibrium strategies"""

    # Simplified: are paths aligned toward favorable equilibrium?
    paths = cat.find_paths(drug, disease, max_length=3)

    if not paths:
        return 0.0

    # Paths with > 2 hops are weaker (more unstable)
    stability = mean([1.0 / path.hops for path in paths])

    return min(1.0, stability)
```

**Performance**: Ablation shows ~0.0 AUROC impact (negligible).

---

## Historical/Experimental Module: Bayesian

**Purpose**: Probabilistic scoring.

**Code location**: historical notes; no active `oracle/bayesian_strategy.py` module in the current runtime profile

**Idea**: Treat confidence scores as probabilities.

```python
def bayesian_score(cat: Category, drug: str, disease: str) -> float:
    """Bayesian inference"""

    paths = cat.find_paths(drug, disease, max_length=4)

    if not paths:
        return 0.0

    # Prior: P(drug treats disease)
    prior = 0.5

    # Likelihood: Product of path confidences
    likelihoods = [path.confidence for path in paths]
    likelihood = prod(likelihoods) ** (1 / len(likelihoods))

    # Posterior: Bayes rule (simplified)
    posterior = (likelihood * prior) / (likelihood * prior + (1 - likelihood) * (1 - prior))

    return posterior
```

**Performance**: Ablation shows ~0.0 AUROC impact (negligible).

---

## Strategy Aggregation

```python
def score_pair(strategies, source: str, target: str) -> tuple[float, list[tuple[str, float]]]:
    """Aggregate the active runtime strategy profile."""

    votes = []
    composition_weight = 0.0
    yoneda_similarity = 0.0

    for strategy in strategies:
        preds = strategy.predict(source, target)
        if not preds:
            continue
        best = max(preds, key=lambda pred: pred.confidence)
        votes.append((strategy.name, best.confidence))
        if strategy.name == "composition":
            composition_weight = sum(pred.confidence for pred in preds)
        if strategy.name == "yoneda_distance":
            yoneda_similarity = best.confidence

    base_votes = [(name, conf) for name, conf in votes if name != "yoneda_distance"]
    base = sum(conf for _, conf in base_votes) / len(base_votes) if base_votes else 0.0
    path_bonus = min(0.25, 0.04 * composition_weight)
    yoneda_bonus = min(0.10, 0.06 * yoneda_similarity) if yoneda_similarity > 0 else 0.0
    return min(1.0, base + path_bonus + yoneda_bonus), votes
```

**Weights**: Current production scoring uses the calibrated strategy combiner. Ranking-score calibration is tracked separately from strategy signal scores.

---

## Hyperparameter Tuning

### Path Bonus Coefficient

Tuned via LOOCV grid search:
- Grid: [0.0, 0.01, 0.02, ..., 0.20]
- Metric: LOOCV AUROC
- Result: 0.04 is the current production value; rerun calibration before changing it.

### Strategy Weights

Tested uniform vs. composition-dominant weights during development:
- Uniform/current combiner: strict AUROC 0.9747 in the current full run
- Composition-heavy: historical AUROC 0.943 (slightly worse)
- Result: keep the current combiner unless a fresh calibration run improves both ranking metrics and auditability

---

## Performance Per Strategy

Historical median contribution to AUROC (via development ablation; rerun before quoting as current):

```
Composition:         -0.153 (dominant)
Binding Evidence:    -0.045 (moderate)
Coherence:           -0.005 (minor)
Conjecture:          -0.002 (minor)
Path Bonus:          -0.015 (tuning)
Yoneda Distance:     historical live-triage bonus; inactive in strict remove_direct_labels
Natural Transform:   -0.000 (none)
Game Theory:         -0.000 (none)
Bayesian:            -0.000 (none)
```

Sum of contributions: ~0.23 (less than full system 0.9747, due to non-additivity and baseline ~0.75 from random).

---

## Adding a New Strategy

See [ARCHITECTURE.md](ARCHITECTURE.md) for 6-step template.

Key checklist:
- [ ] Score range [0, 1]
- [ ] No external dependencies (or optional)
- [ ] Performance on 44 self-check (all recoverable)
- [ ] Ablation test (AUROC impact)
- [ ] Documentation

---

## See Also

- [ARCHITECTURE.md](ARCHITECTURE.md) — System design
- [VALIDATION_AND_BENCHMARKS.md](VALIDATION_AND_BENCHMARKS.md) — Metrics
- [CONTRIBUTING.md](CONTRIBUTING.md) — Contributing code

---

*Last updated: 2026-05-28 (runtime strategy profiles and conditional Yoneda clarified)*
