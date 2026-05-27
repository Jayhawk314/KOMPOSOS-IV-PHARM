# KOMPOSOS-IV-PHARM

**Categorical AI for pharmaceutical discovery: drug repurposing via mechanistic paths and structural similarity.**

KOMPOSOS-IV-PHARM applies a categorical AI runtime to drug discovery, focusing on finding existing drugs that can treat new diseases through computational analysis of biological networks. It combines path-based scoring (via category theory), machine learning strategies, and quantitative evidence tracing to recommend drug-disease pairs with mechanistic justification.

**Current Status**: Track A (drug repurposing) is a working research prototype with **AUROC 0.965** on held-out FDA drug-disease pairs. Track B (de novo drug design) is a long-term goal, not yet scientifically validated.

---

## Quick Start

**Prerequisites**: Python 3.10+, SQLite (included with Python)

```bash
# 1. Clone and install
git clone https://github.com/your-repo/KOMPOSOS-IV-PHARM.git
cd KOMPOSOS-IV-PHARM
pip install -r requirements.txt

# 2. Run your first triage (disease-first ranking)
python validation/triage.py Melanoma

# 3. Or rank all diseases for a drug
python validation/triage.py --drug Sorafenib

# 4. Or dive into a specific pair
python validation/triage.py Melanoma --drug Vemurafenib --markdown
```

For detailed setup, see **[GETTING_STARTED.md](GETTING_STARTED.md)**.

---

## What It Does

### Track A: Drug Repurposing (Working)

Recommends FDA-approved drugs to treat diseases by analyzing:

1. **Mechanistic paths**: Drug → Protein → Disease chains with confidence scores
2. **Quantitative evidence**: IC50 binding data, clinical response rates, mutation frequencies (204 edges)
3. **Structural similarity**: Yoneda distance (are other drugs treating this disease with similar targets?)
4. **Confidence-weighted composition**: How certain are the biological connections?

**Example**: For Melanoma, the system ranks BRAF/MEK inhibitors first (correct) and can justify them with:
- Sorafenib → BRAF/VEGFR2 → Melanoma (mutated BRAF pathway)
- IC50 = 25.8 nM from PMID:12829955
- Structural match to Vemurafenib (both inhibit BRAF)
- FDA indication: 2008, PMID:18241329

### Track B: Drug Design (Long-term)

Planned capability: generate novel compounds with predicted binding, ADMET, and safety. Not yet implemented.

---

## Key Metrics

| Metric | Value | Details |
|--------|-------|---------|
| **AUROC** | **0.965** | Full-typed view, remove_direct_labels protocol, 44 FDA pairs |
| **AUPRC** | 0.634 | Top candidates more likely real |
| **Hits@10** | 0.80 | 80% of true positives in top 10 |
| **Provenance** | 100% | All 5,382 edges cite PMIDs or ChEMBL IDs |
| **Data points** | 5,382 morphisms | 464 objects (78 drugs, 20 diseases, 366 proteins) |

See **[VALIDATION_AND_BENCHMARKS.md](VALIDATION_AND_BENCHMARKS.md)** for full metrics, confidence intervals, and external validation (Hetionet AUROC 0.744, temporal AUROC 0.959).

---

## Core Concepts

**Objects** = Drugs, Proteins, Diseases
**Morphisms** = Biological relationships (Drug inhibits Protein, Protein regulates Pathway, etc.) with confidence scores
**Paths** = Mechanistic chains (Drug → Protein → Pathway → Disease) with multiplicative confidence
**Strategies** = 9 scoring methods (composition, binding evidence, Yoneda distance, etc.) that vote on Drug-Disease pairs

Why category theory? It naturally models composition (mechanistic paths), supports extensibility (adding new object types and strategies), and provides honesty (confidence propagation through multiplicative rules).

See **[CATEGORICAL_THEORY_PRIMER.md](CATEGORICAL_THEORY_PRIMER.md)** for intuition without heavy math.

---

## Documentation Roadmap

### For Different Audiences

**I want to use it to triage candidates**
→ Start: [GETTING_STARTED.md](GETTING_STARTED.md) → [TRACK_A_DRUG_REPURPOSING.md](TRACK_A_DRUG_REPURPOSING.md) → [TROUBLESHOOTING_AND_FAQ.md](TROUBLESHOOTING_AND_FAQ.md)

**I want to validate the science**
→ Start: [TRACK_A_DRUG_REPURPOSING.md](TRACK_A_DRUG_REPURPOSING.md) → [VALIDATION_AND_BENCHMARKS.md](VALIDATION_AND_BENCHMARKS.md) → [EVIDENCE_AND_PROVENANCE.md](EVIDENCE_AND_PROVENANCE.md)

**I want to understand the architecture**
→ Start: [ARCHITECTURE.md](ARCHITECTURE.md) → [API_REFERENCE.md](API_REFERENCE.md) → [STRATEGIES_IN_DEPTH.md](STRATEGIES_IN_DEPTH.md)

**I want to contribute code**
→ Start: [ARCHITECTURE.md](ARCHITECTURE.md) → [CONTRIBUTING.md](CONTRIBUTING.md) → [STRATEGIES_IN_DEPTH.md](STRATEGIES_IN_DEPTH.md)

---

## File Structure

```
KOMPOSOS-IV-PHARM/
├── truedocs/                          # Fresh documentation (this folder)
│   ├── README.md                      # You are here
│   ├── GETTING_STARTED.md             # Installation & first run
│   ├── TRACK_A_DRUG_REPURPOSING.md    # How repurposing works
│   ├── VALIDATION_AND_BENCHMARKS.md   # Metrics, protocols, validation
│   ├── EVIDENCE_AND_PROVENANCE.md     # Data sources, traceability
│   ├── ARCHITECTURE.md                # 5-layer stack, design decisions
│   ├── API_REFERENCE.md               # Core API, examples
│   ├── DATA_AND_DATABASE.md           # Schema, stats, reproducible build
│   ├── STRATEGIES_IN_DEPTH.md         # All 9 strategies explained
│   ├── CHEMISTRY_AND_BINDING.md       # Molecular properties, Lipinski
│   ├── CATEGORICAL_THEORY_PRIMER.md   # Intuitive category theory
│   ├── CONTRIBUTING.md                # Code standards, adding strategies
│   └── TROUBLESHOOTING_AND_FAQ.md     # Common issues & Q&A
├── core/                              # Category runtime (objects, morphisms)
├── oracle/                            # Scoring strategies (9 total)
├── validation/                        # Benchmark harness, triage CLI
├── data/
│   └── drugs/                         # Drug repurposing data (tier1.db)
├── chemistry/                         # Molecular properties, domain matching
├── molecular_bridge/                  # Binding interaction scoring
└── ...other modules
```

---

## Data at a Glance

**Track A Database**: `data/drugs/tier1.db` (3.67 MB, reproducible build from manifest)

- **Objects**: 78 FDA-approved drugs, 20 oncology diseases, 366 proteins (targets, pathways, regulators)
- **Edges**: 5,382 morphisms with full provenance (581 unique PMIDs, ChEMBL IDs)
- **Quantitative**: 204 edges with IC50 binding data, hazard ratios, mutation frequencies
- **Labels**: 44 FDA-approved Drug→Disease pairs (all mechanistically supported)
- **100% provenance**: Every edge cites a PubMed ID or ChEMBL compound/target ID

Build your own: `python data/drugs/build_tier1.py --manifest data/drugs/tier1_manifest.json`

See **[DATA_AND_DATABASE.md](DATA_AND_DATABASE.md)** for schema, sources, and expansion options.

---

## Typical Workflow

### 1. Triage candidates for a disease

```bash
python validation/triage.py Melanoma --top 10
```

Output: Ranked drugs, strategy votes, evidence chains with PMIDs, FDA label status.

### 2. Deep dive on a specific pair

```bash
python validation/triage.py Melanoma --drug Vemurafenib
```

Output: Full detail on why it scores high (paths, quantitative evidence, structural similarity).

### 3. Validate the ranking

```bash
python validation/repurposing_benchmark.py --view full_typed --protocol remove_direct_labels --ci
```

Output: AUROC 0.965 ± 0.02 (95% CI), AUPRC, Hits@K, confidence intervals.

### 4. Trace a prediction to evidence

```bash
python validation/trace_prediction.py Melanoma Vemurafenib
```

Output: All supporting evidence chains, PMIDs, confidence breakdown per strategy.

---

## Validation Summary

The system recovers all 44 FDA-approved oncology drug-disease pairs with mechanistic justification. External validation confirms modest improvement over graph-topology baselines:

| Protocol | AUROC | Details |
|----------|-------|---------|
| remove_direct_labels | 0.965 | Strongest; tests ranking of unknown pairs |
| loocv | 0.945 | Leave-one-out cross-validation |
| Hetionet (external) | 0.744 | 7 held-out pairs confirmed in external DB |
| Temporal holdout | 0.959 | 22 FDA approvals post-2013 |
| Mean disease holdout | 0.877 | Per-disease AUROC (range 0.615–0.996) |

**Important**: Unlabeled Drug-Disease pairs are unknowns, not confirmed negatives. AUROC measures ranking quality on a balanced test set, not true prevalence.

See **[VALIDATION_AND_BENCHMARKS.md](VALIDATION_AND_BENCHMARKS.md)** for protocol details, confidence intervals, and honest interpretation.

---

## Honest Limitations

- **Track B not ready**: Drug design requires molecular generation, synthesis routes, and structure prediction (not yet implemented).
- **Oncology-focused**: Database emphasizes cancer drugs/diseases; applicability to other domains untested.
- **Heuristic binding**: Binding predictions use Lipinski/ABPP/Boltz2, not crystal structures.
- **Unknown pairs are unknowns**: Can't distinguish "truly no relationship" from "not yet discovered."
- **Mechanistic, not clinical**: Paths show biology, not whether patients will respond.

---

## Citation

If you use KOMPOSOS-IV-PHARM in research, please cite:

```bibtex
@software{komposos_iv_pharm_2026,
  author = {Hawkins, James Ray},
  title = {KOMPOSOS-IV-PHARM: Categorical AI for Drug Repurposing},
  year = {2026},
  url = {https://github.com/your-repo/KOMPOSOS-IV-PHARM},
  note = {Track A working; Track B planned}
}
```

---

## License

Apache 2.0 (open source) / Commercial (dual license available)

---

## Getting Help

- **Installation issues**: See [GETTING_STARTED.md](GETTING_STARTED.md) and [TROUBLESHOOTING_AND_FAQ.md](TROUBLESHOOTING_AND_FAQ.md)
- **How to triage**: See [TRACK_A_DRUG_REPURPOSING.md](TRACK_A_DRUG_REPURPOSING.md)
- **Validating claims**: See [VALIDATION_AND_BENCHMARKS.md](VALIDATION_AND_BENCHMARKS.md) and [EVIDENCE_AND_PROVENANCE.md](EVIDENCE_AND_PROVENANCE.md)
- **Extending code**: See [ARCHITECTURE.md](ARCHITECTURE.md), [API_REFERENCE.md](API_REFERENCE.md), and [CONTRIBUTING.md](CONTRIBUTING.md)
- **Common Q&A**: See [TROUBLESHOOTING_AND_FAQ.md](TROUBLESHOOTING_AND_FAQ.md)

---

## Author & Acknowledgments

**Author**: James Ray Hawkins
**Validation**: See [EVIDENCE_AND_PROVENANCE.md](EVIDENCE_AND_PROVENANCE.md) for 581 unique PMIDs and 100% edge provenance.

---

*Last updated: 2026-05-26 (Yoneda distance strategy integration, evidence quantification expansion)*
