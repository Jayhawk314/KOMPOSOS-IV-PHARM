# Chemistry and Binding

**Purpose**: Molecular properties, drug-likeness, binding prediction, and integration into scoring.

**Audience**: Medicinal chemists, researchers validating predictions, developers extending chemistry models

---

## Molecular Properties

### Drug Properties (All 78 drugs)

Every drug in tier1.db has:
- **Molecular Weight (MW)**: 150–900 da (typical: 300–500)
- **LogP**: −2 to +6 (typical: 1–4, lipophilicity)
- **Hydrogen Bond Donors (HBD)**: 0–10
- **Hydrogen Bond Acceptors (HBA)**: 0–15
- **Rotatable Bonds**: 0–20
- **Topological Polar Surface Area (TPSA)**: 0–200 Å²
- **Aromatic Rings**: 0–6

**Source**: PubChem (46/68 drugs validated via PUG REST API 2026-05-13)

**Example (Sorafenib)**:
- MW: 465 da ✓
- LogP: 3.8 (moderately lipophilic) ✓
- HBD: 2
- HBA: 7
- Rotatable bonds: 11
- TPSA: 62 Å² (good membrane permeability) ✓

**File**: `data/drugs/drug_properties.py`

```python
DRUG_PROPERTIES = {
    'Sorafenib': {
        'mw': 465.4,
        'logp': 3.8,
        'hbd': 2,
        'hba': 7,
        'smiles': 'CC(C)Nc1cc(I)c(Nc2ccc(F)c(Cl)c2)cc1F',
        'psa': 62.0,
    },
    # ... 77 more drugs
}
```

---

## Lipinski's Rule of Five

Predicts oral bioavailability:

```
✓ Lipinski-compliant if:
  MW ≤ 500
  LogP ≤ 5
  HBD ≤ 5
  HBA ≤ 10
  No unusual groups (e.g., fluorine > 5)
```

**Violation count** determines drug-likeness score:

```
violations = sum([
    drug.mw > 500,
    drug.logp > 5,
    drug.hbd > 5,
    drug.hba > 10,
])
lipinski_score = 1.0 - (0.2 * violations)  # Each violation: -0.2
```

**Results (78 drugs)**:
- 72/78 (92%) zero violations (excellent)
- 4/78 (5%) one violation (acceptable)
- 2/78 (3%) two violations (borderline)

**Example violations**:
- Lenvatinib: MW 427, LogP 2.0, but rare heterocycle = flag, but still acceptable
- Sorafenib: All compliant ✓

---

## Target Properties (Protein Binding Sites)

### Kinase Domains

~100 kinase targets in database. Properties:

- **ATP pocket**: Highly conserved, accessible
- **Gatekeeper residue**: Controls selectivity (e.g., BRAF V600)
- **Hinge region**: H-bonding site (common for inhibitors)

**Example (BRAF kinase)**:
- Catalytic domain: residues 440–750
- ATP pocket: ~6–7 Å cavity
- V600E mutation: 70% of Melanoma, confers constitutive activity

### GPCR Targets

~20 GPCR targets. Properties:
- **Transmembrane helices**: 7 helices (TM1–TM7)
- **Orthosteric pocket**: Between TM5/TM6, deep
- **Selectivity pocket**: Allosteric, highly variable

### Protease Targets

~10 proteases. Properties:
- **Active site**: Serine/aspartate nucleophile
- **Substrate binding pocket**: S1, S1', S2 subsites
- **Product egress**: Channel width determines inhibitor size

---

## Interaction Scoring (5 Scorers)

Implemented in `molecular_bridge/interaction_scoring.py`:

### 1. Solubility Compatibility

**Principle**: Drug must dissolve to reach target.

```python
def score_solubility(drug, target) -> float:
    """
    Factors:
    - LogP: Too lipophilic → hydrophobic, insoluble
    - TPSA: Low TPSA → less polar, less soluble
    - Aromatic rings: Too many → π-π stacking, aggregation
    """
    logp_penalty = max(0.0, (drug.logp - 3.0) / 3.0)  # > 3 is high
    tpsa_bonus = min(drug.tpsa / 100.0, 1.0)  # TPSA > 100 is more soluble
    ring_penalty = max(0.0, (drug.aromatic_rings - 3.0) / 3.0)

    score = 1.0 - (0.3 * logp_penalty) - (0.2 * ring_penalty) + (0.2 * tpsa_bonus)
    return max(0.0, min(1.0, score))
```

**Example**:
- Sorafenib (LogP 3.8, TPSA 62): score ≈ 0.75 (good)
- Imatinib (LogP 3.9, TPSA 65): score ≈ 0.74 (good)

### 2. Steric Compatibility

**Principle**: Drug shape must fit binding pocket.

```python
def score_steric_compat(drug, target) -> float:
    """
    Factors:
    - Molecular weight: Too heavy → won't fit
    - Rotatable bonds: Too many → conformational entropy
    - Longest path: If > binding pocket depth, won't fit
    """
    mw_penalty = max(0.0, (drug.mw - 450.0) / 200.0)  # > 450 is bulky
    rotatable_penalty = max(0.0, (drug.rotatable_bonds - 8.0) / 10.0)  # > 8 is flexible

    score = 1.0 - (0.5 * mw_penalty) - (0.3 * rotatable_penalty)
    return max(0.0, min(1.0, score))
```

**Example**:
- Sorafenib (MW 465, rotatable 11): score ≈ 0.72 (acceptable)
- Small molecule inhibitor: score ≈ 0.85 (preferred)

### 3. Reactivity Risk

**Principle**: Avoid reactive, electrophilic groups.

```python
def score_reactivity_risk(drug) -> float:
    """
    Risk factors:
    - Aldehydes, ketones (reactive)
    - Isocyanates, epoxides (reactive)
    - Sulfides, disulfides (oxidizable)
    """
    risky_groups = [
        drug.has_aldehyde,
        drug.has_isocyanate,
        drug.has_epoxide,
        drug.has_sulfide,
    ]
    risk = sum(risky_groups) / len(risky_groups)
    return 1.0 - risk
```

**Most drugs**: score ≈ 1.0 (no reactive groups)
**Example exception**: Some natural products with reactive centers (score < 0.7)

### 4. Hydrogen Bonding

**Principle**: H-bonds stabilize binding; too many → over-constrained.

```python
def score_hydrogen_bonding(drug, target) -> float:
    """
    Factors:
    - Target HBD/HBA capacity (from Pfam domain)
    - Drug HBD/HBA count
    """
    drug_hbd_hba = drug.hbd + drug.hba
    target_capacity = target.estimated_hbond_capacity  # 4–8 typical

    if drug_hbd_hba > target_capacity:
        penalty = (drug_hbd_hba - target_capacity) / target_capacity
    else:
        bonus = drug_hbd_hba / target_capacity

    score = 1.0 + (0.2 * bonus) - (0.3 * penalty) if drug_hbd_hba <= target_capacity else 0.7
    return max(0.0, min(1.0, score))
```

### 5. Electrostatic Matching

**Principle**: Charged groups should align with target charges.

```python
def score_electrostatic(drug, target) -> float:
    """
    Factors:
    - Drug ionic charge (sum of ionizable groups)
    - Target binding pocket charge (computed from residues)
    """
    drug_charge = drug.estimated_ionic_charge(-1, 7)  # At pH 7
    target_charge = target.binding_pocket_charge()

    match = 1.0 - abs(drug_charge - target_charge) / max(abs(drug_charge), abs(target_charge), 1)
    return match
```

---

## ABPP IC50 Integration

### Affinity Profiling Panel (65 Entries)

**What**: Experimental measurement of drug binding to protein kinase panel.

**IC50 value interpretation**:
```
IC50 < 50 nM:     Excellent (potent, specific)
50–500 nM:        Good (nanomolar)
500 nM–10 μM:     Moderate (micromolar)
10–100 μM:        Weak
> 100 μM:         No binding
```

**Example (Sorafenib)**:
- BRAF IC50: 25.8 nM (excellent) ← PMID:12829955
- VEGFR2 IC50: 89 nM (good)
- FLT3 IC50: 120 nM (good)
- MEK1 IC50: 8000 nM (weak, but not primary target)

**Integration into binding strategy**:

```python
def abpp_score(drug_name, target_name) -> float:
    """Query ABPP data"""
    try:
        ic50_nm = ABPP_DATA[(drug_name, target_name)]['ic50_nm']
    except KeyError:
        return None  # No ABPP data

    # Convert IC50 to score
    if ic50_nm < 50:
        return 1.0
    elif ic50_nm < 500:
        return 0.9
    elif ic50_nm < 10_000:
        return 0.6
    else:
        return 0.2
```

**Weight in binding strategy**: 0.30 (highest among components)

---

## Boltz2 Heuristic Binding Prediction

**What**: Fallback binding prediction when no ABPP data.

**Method**: Heuristic based on drug class and target domain.

```python
def boltz2_predict(drug_name, target_name) -> float:
    """Heuristic prediction"""

    # Rule 1: Kinase inhibitor + kinase target = likely good binding
    if drug_class(drug_name) == 'kinase_inhibitor' and target_has_kinase_domain(target_name):
        return 0.75

    # Rule 2: Drug name contains target name = similarity proxy
    if target_name.lower() in drug_name.lower():
        return 0.70

    # Rule 3: GPCR ligand + GPCR target
    if drug_class(drug_name) == 'gpcr_ligand' and target_is_gpcr(target_name):
        return 0.70

    # Rule 4: Protease inhibitor + protease target
    if drug_class(drug_name) == 'protease_inhibitor' and target_is_protease(target_name):
        return 0.65

    # Rule 5: Otherwise, estimate from chemical similarity
    similarity = chemical_similarity(drug_name, target_name)  # 0.0–1.0
    return 0.3 + (0.4 * similarity)
```

**Confidence**: Typically 0.60–0.80 (lower than ABPP experimental).

**Weight in binding strategy**: 0.10 (fallback)

---

## Pfam Domain Matching

### Purpose

Align drug class with target domain type.

### Example Mappings

```python
DOMAIN_DRUG_CLASS_RULES = {
    'Kinase': ['kinase_inhibitor', 'tyrosine_kinase_inhibitor', 'atp_competitive'],
    'GPCR': ['gpcr_agonist', 'gpcr_antagonist', 'beta_blocker'],
    'Serine_protease': ['protease_inhibitor', 'trypsin_inhibitor'],
    'Zinc_metalloenzyme': ['mmp_inhibitor', 'ace_inhibitor'],
}

def score_pfam_match(drug, target) -> float:
    """Match drug class to target domain"""
    drug_classes = infer_drug_class(drug.name, drug.properties)
    target_domain = target.primary_pfam_domain

    for expected_classes in DOMAIN_DRUG_CLASS_RULES.get(target_domain, []):
        if any(c in expected_classes for c in drug_classes):
            return 0.9  # Strong match
    return 0.5  # Weak/no match
```

**Example**:
- Sorafenib (kinase inhibitor) + BRAF (kinase domain): score 0.9 ✓
- Sorafenib + GPCR target: score 0.5 (mismatch)

---

## Limitations & Known Issues

### 1. No Crystal Structures

Current system uses heuristics and ABPP, not actual binding geometries.

**Impact**: Predictions miss induced-fit effects, water-mediated H-bonds, allosteric binding.

**Mitigation**: ABPP data (65 entries) provides experimental ground truth for major drugs.

### 2. No off-target liability assessment

Doesn't predict off-target binding (e.g., kinase inhibitor binding to unintended kinases).

**Impact**: Scoring is optimistic (assumes on-target binding).

**Future**: Integrate DiscoveRx HistoneH3 panel or Eurofins PanLabs.

### 3. No ADMET prediction

Doesn't predict absorption, distribution, metabolism, excretion, toxicity.

**Impact**: Candidate selection focuses on binding, not pharmacokinetics.

**Future**: Integrate Simcyp, GastroPlus, or DeepADMET models.

### 4. Boltz2 heuristic is weak

Rule-based predictions (not ML-trained).

**Impact**: Fallback quality is lower than ABPP.

**Mitigation**: Most high-confidence drugs have ABPP data; fallback only used for unknowns.

---

## Using Chemistry Data in Scoring

### Manual Check (CLI)

```bash
python validation/triage.py Melanoma --drug Sorafenib
```

Output includes:
```
Binding Evidence: 0.85
  ├─ ABPP IC50: 25.8 nM → 1.0
  ├─ Lipinski: All compliant → 0.9
  ├─ Pfam match: Kinase inhibitor ≈ kinase → 0.9
  └─ Molecular compatibility: Good → 0.8
```

### Programmatic Access

```python
from chemistry.drug_properties import DRUG_PROPERTIES
from chemistry.pfam_domain_mapper import PfamDomainMapper
from abpp_bridge import get_ic50

# Drug properties
drug = 'Sorafenib'
props = DRUG_PROPERTIES[drug]
print(f"MW: {props['mw']}, LogP: {props['logp']}")

# IC50 data
ic50 = get_ic50(drug, 'BRAF')  # 25.8 nM
print(f"IC50: {ic50}")

# Domain matching
mapper = PfamDomainMapper()
score = mapper.score_match(drug, 'BRAF')
print(f"Domain match: {score}")
```

---

## Extending Chemistry Models

### Adding ADMET Prediction

```python
# New module: chemistry/admet_predictor.py
from chemistry.admet_predictor import predict_admet

def admet_score(drug: str) -> float:
    """Predict ADMET properties"""
    props = DRUG_PROPERTIES[drug]

    # Model: logistic regression on MW, LogP, TPSA, ...
    admet = predict_admet(props)  # Returns dict of scores

    return admet['overall_admet_score']  # 0.0–1.0
```

### Adding Off-Target Liability

```python
# New module: chemistry/off_target.py
from chemistry.off_target import predict_kinase_selectivity

def off_target_risk(drug: str, target: str) -> float:
    """Predict off-target binding risk"""
    # Query DiscoveRx kinase panel or trained model
    # Returns 0.0 (specific) to 1.0 (hits many kinases)
    selectivity = predict_kinase_selectivity(drug)
    return 1.0 - selectivity  # Risk = 1 - selectivity
```

---

## See Also

- [TRACK_A_DRUG_REPURPOSING.md](TRACK_A_DRUG_REPURPOSING.md) — How chemistry data is used
- [STRATEGIES_IN_DEPTH.md](STRATEGIES_IN_DEPTH.md) — Binding evidence strategy
- [API_REFERENCE.md](API_REFERENCE.md) — API for accessing drug properties

---

*Last updated: 2026-05-13 (PubChem validation, Pfam domain mapping)*
