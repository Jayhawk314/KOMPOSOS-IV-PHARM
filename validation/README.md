# KOMPOSOS-III Validation Framework

Multi-layer validation system to ensure physical validity and catch interpretation errors in protein structure predictions.

## Purpose

Prevents the same mistake made in the climate CO2 analysis:
- **Climate problem**: Computed λ₁ correctly, but interpreted it as "physical coupling" ❌
- **Protein problem**: Computing Ricci curvature correctly, but interpreting as "folding mechanism" ❓

**The validation framework catches these errors BEFORE publication.**

---

## Architecture

### Four Validation Layers

```
┌──────────────────────────────────────────────────────────────┐
│                    INPUT: Structure + Interpretation         │
└──────────────────────┬───────────────────────────────────────┘
                       │
           ┌───────────┴───────────┐
           │                       │
    ┌──────▼──────┐        ┌──────▼──────┐
    │ Layer 1:    │        │ Layer 2:    │
    │ Structural  │        │ Chemical    │
    │ Validation  │        │ Constraints │
    └──────┬──────┘        └──────┬──────┘
           │                       │
           └───────────┬───────────┘
                       │
           ┌───────────┴───────────┐
           │                       │
    ┌──────▼──────┐        ┌──────▼──────┐
    │ Layer 3:    │        │ Layer 4:    │
    │ Semantic    │        │ Experimental│
    │ Validation  │        │ Validation  │
    └──────┬──────┘        └──────┬──────┘
           │                       │
           └───────────┬───────────┘
                       │
           ┌───────────▼───────────┐
           │  Validation Report    │
           │  + Confidence Score   │
           └───────────────────────┘
```

### Layer 1: Structural Validation
**File**: `protein_structure_validator.py`

Checks basic geometric properties:
- ✓ Coordinate completeness
- ✓ Bond lengths (CA-CA distances)
- ✓ Atomic clashes (distance violations)
- ✓ Compactness (radius of gyration)
- ✓ Ramachandran angles (approximate)

**Example Issues Caught:**
```
✗ CRITICAL: 15.2% of CA-CA bonds outside normal range
⚠  WARNING: Structure unusually extended (Rg ratio = 2.3)
```

### Layer 2: Chemical Validation
**File**: `chemical_constraint_validator.py`

Checks physical chemistry properties:
- ✓ Hydrophobic core burial
- ✓ Hydrogen bonding patterns (approximate)
- ✓ Electrostatic interactions (salt bridges)
- ✓ Disulfide bonds
- ✓ Secondary structure propensities
- ✓ Confidence-based warnings (pLDDT)

**Example Issues Caught:**
```
⚠  WARNING: Only 35% of hydrophobic residues are buried
⚠  WARNING: Low hydrogen bonding: 45 detected vs 120 expected
ℹ  INFO: 8 cysteines present but no disulfide bonds detected
```

### Layer 3: Semantic Validation
**File**: `semantic_validator.py`

Uses sentence embeddings to catch interpretation errors:
- ✓ Terminology consistency (is "Ricci curvature" used correctly?)
- ✓ Mathematical vs physical confusion (curvature ≠ mechanism)
- ✓ Overclaiming (claiming causation from correlation)
- ✓ Confidence matching evidence quality

**Example Issues Caught:**
```
✗ CRITICAL: Mathematical metric interpreted as physical mechanism
  Sentence: "Ricci curvature determines folding mechanism"
  Recommendation: Use "correlates with" instead of causal language

⚠  WARNING: Strong claims detected: proves, demonstrates
  Recommendation: Soften with "suggests", "consistent with"

⚠  WARNING: Low structure confidence (pLDDT=62.3) not acknowledged
```

### Layer 4: Experimental Validation
**File**: `experimental_validator.py`

Validates against experimental ground truth (when available):
- ✓ Structure comparison (RMSD, TM-score vs PDB)
- ✓ Folding kinetics (predicted vs measured rates)
- ✓ Stability (predicted vs measured ΔG, Tm)
- ✓ Mutation effects (ΔΔG vs deep mutational scans)

**Example Results:**
```
✓ PASS - structure
  RMSD: 3.2Å (< 5.0Å threshold)
  TM-score: 0.78 (> 0.5 threshold)
  Good agreement with experimental structure

✗ FAIL - folding_kinetics
  Predicted: 1.2e-3 s⁻¹
  Experimental: 5.6e-5 s⁻¹
  Poor folding rate prediction
```

---

## Installation

### Basic Installation (Layers 1, 2, 4)
```bash
pip install numpy
```

### Full Installation (All Layers Including Embeddings)
```bash
pip install numpy sentence-transformers
```

**Note**: Layer 3 (semantic validation) gracefully falls back to rule-based checking if `sentence-transformers` is not installed.

---

## Usage

### Quick Start: Complete Validation

```python
from validation import CompleteProteinValidator
import numpy as np

# Your structure data
sequence = "MKFLKFSLLTAVLLSVVFAFSSCGDDDDTGYLPPSQAIQDLLKRM..."
coords = np.array([...])  # Nx3 CA coordinates
confidence = np.array([...])  # pLDDT scores

# Your interpretation
interpretation = """
The Ricci curvature analysis reveals...
"""

# Run complete validation
validator = CompleteProteinValidator()
report = validator.validate_full_pipeline(
    sequence=sequence,
    predicted_coords=coords,
    interpretation=interpretation,
    confidence=confidence
)

# Print results
print(validator.generate_detailed_report(report))

# Check if passed
if report.overall['passed']:
    print(f"✓ Validation passed (confidence: {report.overall['confidence_score']:.2%})")
else:
    print(f"✗ Validation failed: {report.recommendation}")
```

### Validate PDB File Directly

```python
from validation import validate_protein_interpretation

interpretation = "..."

report = validate_protein_interpretation(
    pdb_path="data/proteins/structures/AF-P00533-F1-model_v6.pdb",
    interpretation=interpretation
)
```

### Individual Validators

```python
from validation import (
    ProteinStructureValidator,
    ChemicalConstraintValidator,
    ProteinInterpretationValidator
)

# Layer 1: Structural
struct_validator = ProteinStructureValidator()
is_valid, issues = struct_validator.validate_structure(coords, sequence)

# Layer 2: Chemical
chem_validator = ChemicalConstraintValidator()
issues = chem_validator.validate_chemistry(coords, sequence, confidence)

# Layer 3: Semantic
semantic_validator = ProteinInterpretationValidator()
issues = semantic_validator.validate_interpretation(structure_data, interpretation)
```

---

## Integration with KOMPOSOS-III

### Validate After Interpretation

```python
from interpret_structure import interpret_structure
from validation import CompleteProteinValidator

# Run KOMPOSOS-III interpretation
result = interpret_structure("path/to/protein.pdb")

# Extract interpretation text
interpretation = f"""
WHAT (AlphaFold):
  Structure: {result['structure']['num_residues']} residues
  Quality: {result['structure']['mean_plddt']:.1f} pLDDT

WHY/HOW (KOMPOSOS-III):
  Geometry: {result['frameworks']['ricci']['mean_curvature']:.4f} curvature
  ... [your interpretation text] ...
"""

# Validate interpretation
validator = CompleteProteinValidator()
report = validator.validate_full_pipeline(
    sequence=result['structure']['sequence'],
    predicted_coords=result['structure']['coords'],
    interpretation=interpretation,
    confidence=result['structure']['confidence'],
    frameworks_results=result['frameworks']
)

# Only proceed if validated
if report.overall['passed']:
    print("✓ Interpretation validated - safe to publish")
else:
    print(f"✗ Issues detected: {report.recommendation}")
```

### Batch Validation

Validate all 34 proteins in batch test:

```python
from test_all_proteins import get_all_structures
from interpret_structure import interpret_structure
from validation import CompleteProteinValidator

validator = CompleteProteinValidator()

for pdb_path in get_all_structures():
    # Interpret
    result = interpret_structure(pdb_path)

    # Generate interpretation (example)
    interpretation = generate_interpretation(result)

    # Validate
    report = validator.validate_full_pipeline(
        sequence=result['structure']['sequence'],
        predicted_coords=result['structure']['coords'],
        interpretation=interpretation,
        confidence=result['structure']['confidence']
    )

    # Log issues
    if not report.overall['passed']:
        print(f"{pdb_path.stem}: {report.overall['critical_issues']} critical issues")
```

---

## Validation Report Format

### JSON Structure

```json
{
  "timestamp": "2026-02-13T10:30:45",
  "sequence_length": 189,
  "validation_layers": {
    "structural": {
      "passed": true,
      "issues": [...]
    },
    "chemical": {
      "issues": [...]
    },
    "semantic": {
      "issues": [...]
    },
    "experimental": {
      "structure": {
        "metric": "structure",
        "predicted": 3.2,
        "experimental": 0.78,
        "passed": true
      }
    }
  },
  "overall": {
    "passed": true,
    "critical_issues": 0,
    "warning_count": 2,
    "confidence_score": 0.87
  },
  "recommendation": "PROCEED: Validation passed"
}
```

### Confidence Score Calculation

```
Confidence = 0.3 × Structural + 0.2 × Chemical + 0.3 × Semantic + 0.2 × Experimental

Where each component is scored 0-1 based on:
- Critical issues → 0.0
- Warnings → max(0.5, 1.0 - 0.15 × warning_count)
- No issues → 1.0
```

---

## Common Issues and Fixes

### Issue 1: Math-Physics Confusion

**Bad**:
```
"Ricci curvature determines the folding mechanism"
```

**Good**:
```
"Ricci curvature correlates with hierarchical structure organization"
```

**Validator catches:**
```
✗ CRITICAL: Mathematical metric interpreted as physical mechanism
  Recommendation: Use "correlates with" instead of "determines"
```

---

### Issue 2: Overclaiming

**Bad**:
```
"These results prove the folding mechanism and definitively
establish the stability properties."
```

**Good**:
```
"These results suggest a hierarchical folding pattern and are
consistent with stable structures. Experimental validation is
needed to confirm mechanistic interpretations."
```

**Validator catches:**
```
⚠  WARNING: Strong claims detected: proves, definitively
  Recommendation: Soften with "suggests", "consistent with"
```

---

### Issue 3: Low Confidence Not Acknowledged

**Bad**:
```
"The structure shows a complex domain architecture with
multiple functional sites."
(when pLDDT = 45)
```

**Good**:
```
"Note: This structure has low confidence (pLDDT 45.2).
The suggested domain architecture should be considered
tentative pending experimental validation."
```

**Validator catches:**
```
⚠  WARNING: Low structure confidence (pLDDT=45.2) not acknowledged
  Recommendation: Add warning about low structure quality
```

---

## Testing

Run the test suite:

```bash
python test_validation_framework.py
```

This will:
1. Test each validator independently
2. Test on real protein structures (if available)
3. Compare interpretations with/without issues
4. Generate example reports

---

## Files

```
validation/
├── __init__.py                           # Package initialization
├── protein_structure_validator.py        # Layer 1: Structural
├── chemical_constraint_validator.py      # Layer 2: Chemical
├── semantic_validator.py                 # Layer 3: Semantic
├── experimental_validator.py             # Layer 4: Experimental
├── complete_validator.py                 # Integrated validator
└── README.md                             # This file

test_validation_framework.py              # Test suite
```

---

## Future Enhancements

### High Priority
1. **Full backbone atoms**: Currently uses CA-only (simplified)
   - Add N, C, O, H atoms for accurate H-bond detection
   - Real Ramachandran validation with phi/psi angles

2. **Rotamer libraries**: Amino acid-specific conformations
   - Load from Dunbrack database
   - Validate side-chain conformations

3. **Energy functions**: Physical force fields
   - Amber/CHARMM energy terms
   - Rosetta score function
   - Solvation energy

### Medium Priority
4. **ML-based validation**: Train on known errors
   - Learn patterns of common interpretation mistakes
   - Calibrate confidence scores on experimental data

5. **Expanded experimental database**:
   - Collect PDB structures for comparison
   - Folding kinetics from literature
   - Deep mutational scan datasets

### Low Priority
6. **Interactive reports**: Web-based visualization
7. **Continuous validation**: Real-time checks during interpretation
8. **Custom validation rules**: User-defined checks

---

## References

### Structural Validation
- **Ramachandran plots**: Ramachandran et al. (1963)
- **Clash detection**: Word et al. (1999) - Probe/Reduce
- **Radius of gyration**: Kohn et al. (2004)

### Chemical Validation
- **Hydrophobic effect**: Dill (1990)
- **H-bond geometry**: Baker & Hubbard (1984)
- **Disulfide bonds**: Thornton (1981)

### Semantic Validation
- **Sentence embeddings**: Reimers & Gurevych (2019) - Sentence-BERT
- **Semantic similarity**: Mikolov et al. (2013) - Word2Vec foundations

### Experimental Validation
- **TM-score**: Zhang & Skolnick (2004)
- **Folding kinetics**: Plaxco et al. (1998) - Contact order
- **Mutation effects**: Tokuriki & Tawfik (2009)

---

## Citation

If you use this validation framework, please cite:

```bibtex
@software{komposos_validation,
  title={KOMPOSOS-III Protein Structure Validation Framework},
  author={James Ray Hawkins},
  year={2026},
  url={https://github.com/your-repo/KOMPOSOS-III-LAMBDA}
}
```

---

## License

SPDX-License-Identifier: Apache-2.0

Copyright (c) 2024-2026 James Ray Hawkins
