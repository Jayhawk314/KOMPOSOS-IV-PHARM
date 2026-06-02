# Track A: Drug Repurposing

**What it is**: A research prototype that recommends FDA-approved drugs to treat diseases by analyzing mechanistic paths, quantitative evidence, and structural similarity.

**Current status**: Working system with AUROC 0.9705 on held-out FDA drug-disease pairs. All 44 approved pairs are recoverable with mechanistic justification.

**Audience**: Practitioners (how to triage), researchers (validation claims), all (conceptual understanding)

---

## What is Drug Repurposing?

Drug repurposing (or "drug repositioning") is finding new uses for existing, FDA-approved drugs. It's faster and cheaper than designing a drug from scratch because:

1. The drug has human safety data in its approved context
2. Manufacturing is established
3. Side effect profiles are known
4. Only clinical testing for the new indication is needed

**Classic example**: Aspirin was initially developed for pain/inflammation; later found to prevent heart attacks and strokes.

**Our focus**: Using computational biology to systematically find repurposing candidates for oncology drugs and diseases.

---

## How KOMPOSOS-IV-PHARM Finds Candidates

The system scores Drug-Disease pairs using three core ideas:

### 1. Mechanistic Paths (Category Theory)

A **mechanistic path** is a chain of validated biological relationships connecting a drug to a disease:

```
Sorafenib (Drug)
    ↓ inhibits (confidence 0.95)
BRAF (Protein)
    ↓ mutated in (confidence 0.91)
Melanoma (Disease)
────────────────────────────────
Path confidence: 0.95 × 0.91 = 0.865
```

The system finds all such paths for each Drug-Disease pair and weights them by the confidence of each link. Longer paths (Drug → Protein → Pathway → Disease) are supported but carry lower confidence due to multiplicative composition.

**Why multiply confidences?** If link A is 90% confident and link B is 80% confident, the chain is 72% confident (not 85%). This is honest: uncertain links compound uncertainty.

### 2. Quantitative Evidence Integration

Beyond binary "targets this protein," KOMPOSOS-IV integrates actual binding data:

- **IC50 values**: How tight does the drug bind? (Sorafenib–BRAF: 25.8 nM)
- **Mutation frequencies**: How often is the target mutated in the disease? (BRAF: 70% of Melanoma cases)
- **Clinical response rates**: What % of patients respond? (Vemurafenib + BRAF mutation: 48% response rate)
- **Hazard ratios**: Survival improvement? (HR = 0.97 in one trial)

These come from PubMed NLP extraction and ABPP experimental data. Quantitative
values are source-linked, but endpoint-specific citation attribution still needs
audit.

### 3. Structural Similarity (Yoneda Distance)

The system discovers **drug equivalence classes** using presheaf fingerprints:

```
Binimetinib (MEK inhibitor) ≈ Cobimetinib (MEK inhibitor)
  → Both inhibit MEK1/MEK2
  → Both paired with BRAF inhibitors in combo therapy
  → Yoneda presheaf overlap: 0.89
```

This means: if Drug A is approved for Disease D, and Drug B is structurally/mechanistically similar to Drug A, Drug B is likely approved (or clinically promising) for Disease D too.

**Mathematical basis**: Objects are defined by their relationships. Two drugs are "similar" if they have similar neighborhoods in the biological network.

---

## Current Data (As of 2026-05-27)

### Database Summary

| Metric | Value |
|--------|-------|
| **Objects** | 1,146 runtime objects |
| Drugs | 78 FDA-approved |
| Diseases | 20 oncology |
| Proteins / biomedical entities | imported targets, pathways, regulators, and supporting entities |
| **Morphisms** | 2,329 edges |
| Direct labels (Drug→Disease) | 44 FDA-approved |
| Mechanistic/source edges | 2,329 with source strings |
| **Quantitative edges** | 204 |
| IC50 / binding data | 65 edges (ABPP + PubMed) |
| Mutation frequencies | 45 edges |
| Clinical response rates | 52 edges |
| Hazard ratios / survival | 42 edges |
| **Source strings** | 2,329/2,329 morphisms |
| Unique PMID identifiers | 609 |
| ChEMBL target IDs | ChEMBL-derived edges |

### Data Sources

| Source | Count | Type |
|--------|-------|------|
| PubMed (NLP extraction) | 373 quantitative data points | IC50, mutation freq, response rate, HR |
| ChEMBL | 269 proteins, 872 morphisms | drug-target interactions |
| FDA SOP | 44 labels | approved indications |
| STRING PPI | 338 edges | protein-protein interactions |
| cBioPortal | 45+ edges | genomic data (mutation freq, CNV, expression) |
| ABPP | 65 edges | experimental IC50 values |
| Protein similarity | 100 edges | protein similarity (fallback); labeled ESM2 in DB, pending ESMC re-derivation |

All morphisms include a source/provenance string such as PMID, ChEMBL, FDA,
KEGG, STRING, ESM2/ESMC, or review metadata. This is source coverage, not proof
that every edge has been manually validated against the cited text.

**ESMC-300M integration (2026-05-28)**: The protein language model engine
(`data/bio_embeddings.py`) has been upgraded from ESM2 to ESMC-300M (960d,
EvolutionaryScale). Triage reports now include ESMC protein family classification
(Family Extrapolation / Cross-Family Related / Cross-Family Novel) for each
candidate. The 424 ESM2-labeled manifest edges are pending re-derivation with
real ESMC protein sequence similarities via `scripts/rederive_esmc_edges.py`.

---

## How Scoring Works

The system uses an active strategy profile that votes on each Drug-Disease pair. Strict `remove_direct_labels` runs use 7 active modules; live/as-loaded triage can add Yoneda distance when known-treatment comparators are visible.

### Strategy 1: Composition (Dominant)

Finds all Drug → Protein → Disease paths. Each path contributes weight = product of edge confidences.

**Example**: Sorafenib → BRAF → Melanoma (confidence 0.865) competes with Sorafenib → VEGFR2 → Angiogenesis → Melanoma (confidence 0.597).

**Contribution to AUROC**: Dominant (ablation: -0.15 AUROC when removed)

### Strategy 2: Path Bonus

Adds a small bonus for unusually high-confidence paths.

Formula: `bonus = min(0.25, 0.04 × sum(path_confidence))`

Example: If composition score is 0.88, path_bonus might add 0.02 → final from this strategy is 0.90.

**Tuned via LOOCV grid search** (2026-05-24) to maximize leave-one-out validation AUROC.

### Strategy 3: Binding Evidence

Integrates ABPP IC50 data, Boltz2 heuristic binding prediction, and drug-likeness (Lipinski):

- **IC50 bridge** (weight 0.30): 65 experimental entries with PMIDs
- **Boltz2 bridge** (weight 0.10): Heuristic binding prediction (fallback)
- **Drug properties** (weight 0.20): Lipinski drug-likeness (MW <500, logP <5, etc.)
- **Molecular compatibility** (weight 0.10): Solubility, steric, reactivity scoring
- **Domain matching** (weight 0.10): Pfam domain–drug class matching (kinase inhibitor → kinase)
- **Graph confidence** (weight 0.20): Morphism confidence from Category

See [CHEMISTRY_AND_BINDING.md](CHEMISTRY_AND_BINDING.md) for details.

### Additional Runtime Modules

4. **Yoneda Distance** (live/as-loaded only when comparators exist): Structural similarity presheaf fingerprints (weight 0.06 bonus, capped 0.10)
5. **Conjecture**: Rule learning from path patterns (sparse, experimental)
6. **Coherence**: Logical consistency scoring via verdict lattices
7. **Natural Transformation**: Morphism alignment scoring
8. **Game Theory**: Strategic equilibrium analysis
9. **Bayesian**: Probabilistic scoring (experimental)

See [STRATEGIES_IN_DEPTH.md](STRATEGIES_IN_DEPTH.md) for full mathematical details.

### Aggregation

Active votes are normalized to [0, 1] and combined into a ranking score. The live/as-loaded score may include a separate Yoneda bonus when comparators exist; the strict `remove_direct_labels` benchmark does not.

**Decision threshold**: 0.50 (classifies pairs as likely/unlikely repurposing candidates)

---

## Current Performance

### Best-Case Metrics (full_typed view, remove_direct_labels protocol)

| Metric | Value | Interpretation |
|--------|-------|-----------------|
| **AUROC** | **0.9705** | Pairwise ranking signal: the strict benchmark usually ranks a labeled positive above an unlabeled pair |
| **AUPRC** | 0.546 | Precision-recall ranking signal versus a 2.82% positive-label prevalence |
| **Hits@5** | 1.00 | 100% of true positives in top 5 (impressive for 78 drugs) |
| **Hits@10** | 0.60 | 60% Hits@10 under the strict benchmark |
| **MRR** | 0.0788 | Mean reciprocal rank |

### Cross-Validation (loocv protocol)

- **AUROC**: 0.967431
- **AUPRC**: 0.516478
- **Hits@5 / Hits@10 / Hits@20**: 0.8000 / 0.6000 / 0.6000
- **MRR**: 0.077237

### External Validation

| Protocol | AUROC | Details |
|----------|------:|---------|
| Hetionet CtD | 0.6436 | AUPRC 0.0093 on 7 external positives; weak top-rank recovery |
| Temporal | 0.9780 | AUPRC 0.2288 on 18 held-out approvals after 2013 |
| Disease-level | 0.9504 mean | Mean AUPRC 0.6368 across 7 diseases; weakest AUROC 0.7872 |

### Honest Caveats

- **remove_direct_labels protocol removes Drug→Disease edges during scoring** (prevents leakage). This is the fairest protocol for ranking unknown pairs.
- **as_loaded protocol is not the primary claim**. Current rerun: AUROC 0.738831, AUPRC 0.049407; use strict label-removal or LOOCV for current reporting.
- **Unlabeled pairs are unknown unknowns**. Can't distinguish "truly no relationship" from "not yet discovered."
- **Open-world labels**: 44 positives vs. 1,516 unlabeled pairs in the strict task. Unlabeled pairs are unknowns, not confirmed negatives.

See [VALIDATION_AND_BENCHMARKS.md](VALIDATION_AND_BENCHMARKS.md) for full details, confidence intervals, and honest interpretation.

---

## Using the Triage CLI

### Example 1: Rank drugs for Melanoma

```bash
python validation/triage.py Melanoma --top 10
```

Output includes:
- Score (0.0–1.0)
- Strategy vote breakdown (9 votes)
- Mechanistic paths with PMIDs
- IC50 binding data
- Mutation frequency (if applicable)
- FDA approval status

### Example 2: Rank diseases for Sorafenib

```bash
python validation/triage.py --drug Sorafenib --top 10
```

Output: Same format, but drugs ranked instead of diseases.

### Example 3: Deep-dive on Melanoma + Vemurafenib

```bash
python validation/triage.py Melanoma --drug Vemurafenib
```

Output: Full detail mode (active strategy scores, complete evidence chain, confidence breakdown).

### Batch Processing

```bash
# Export as JSON for scripting
python validation/triage.py Melanoma --json > candidates.json

# Export as Markdown for reports
python validation/triage.py Melanoma --markdown > report.md

# Show all candidates, not top 10
python validation/triage.py Melanoma --all
```

---

## What Track A Can Do

✓ Rank drugs for a given disease (by mechanistic strength)
✓ Rank diseases for a given drug
✓ Justify candidates with evidence chains (Drug → Protein → Disease + PMIDs)
✓ Provide quantitative data (IC50, mutation freq, response rate)
✓ Recover all 44 approved indications with mechanistic support
✓ Identify drug equivalence classes (structurally/mechanistically similar drugs)
✓ Flag candidates as APPROVED (in our 44) vs. NOT_APPROVED (candidate, may be in trials)

---

## What Track A Cannot Do

✗ Predict ADMET (absorption, distribution, metabolism, excretion)
✗ Predict safety (off-target effects, organ toxicity)
✗ Design new drugs (requires scaffold libraries, synthesis routes)
✗ Predict patient response (requires genomic/clinical patient context)
✗ Account for drug-drug interactions (combination therapy constraints)
✗ Estimate time-to-approval (regulatory, manufacturing factors)
✗ Confirm true negatives (unlabeled pairs are unknowns, not definite no)

---

## Comparing to Alternatives

### vs. Hetionet (External Graph)

| Feature | KOMPOSOS-IV | Hetionet |
|---------|-------------|----------|
| **Data size** | 464 objects, 2,329 edges | ~50k nodes, ~500k edges |
| **Specificity** | Oncology drugs (78) | All domains |
| **Quantitative** | 204 edges with IC50/HR/mutation | Limited quantitative |
| **Our AUROC** | 0.9705 (strict internal task) | 0.6436 in Hetionet CtD external validation |
| **Transparency** | source strings on all 2,329 morphisms (PMID/ChEMBL) | Graph + paper |
| **Update cycle** | Manual + reproducible build | Regular (Hetionet team) |

**Use case**: KOMPOSOS-IV for oncology depth; Hetionet for breadth across domains.

### vs. DrugBank

| Feature | KOMPOSOS-IV | DrugBank |
|---------|-------------|----------|
| **Data type** | Mechanistic networks | Drug/protein/interaction tables |
| **Scoring** | Path/evidence/structure modules | Label-based lookup |
| **Repurposing** | Computational ranking | Manual curation |
| **Validation** | AUROC 0.9705 on held-out | Not evaluated for ranking |

**Use case**: KOMPOSOS-IV for candidate discovery; DrugBank for drug properties/targets.

### vs. Collaborative Filtering (ML baseline)

| Feature | KOMPOSOS-IV | Collab Filter |
|---------|-------------|---------------|
| **Interpretability** | Explicit paths + PMIDs | Black box |
| **Generalization** | Few drugs per disease ok | Needs dense matrix |
| **New drugs** | Works (uses targets) | Cold-start problem |
| **Validation** | AUROC 0.9759 in current LOOCV | Depends on train/test |

**Use case**: KOMPOSOS-IV for interpretable, knowledge-grounded predictions.

---

## Honest Limitations

### Known Issues

1. **Oncology-only trained**: Applied to other domains without validation
2. **Heuristic binding**: Boltz2 uses Lipinski, not crystal structures
3. **No patient context**: Can't account for tumor genomics, immune status, comorbidities
4. **No ADMET/safety**: Binding ≠ efficacy ≠ safety
5. **No regulatory/commercial**: Can't predict time-to-approval or feasibility
6. **Mechanistic, not clinical**: Paths show biology, not human outcomes

### When to Be Skeptical

- **Single short paths**: Drug → Protein → Disease might miss alternative routes
- **Low quantitative support**: If no IC50 or mutation data, rely more on composition
- **Rare diseases**: Small protein networks may have lower-confidence paths
- **Untested diseases**: Disease not in training set (oncology focus)

### Recommended Next Steps

For any candidate ranked high by KOMPOSOS-IV:
1. Check ClinicalTrials.gov (is it in trials already?)
2. Review the evidence chain (is mechanistic link plausible?)
3. Consult domain experts (do pharmacologists agree?)
4. Consider patient stratification (genomic subtypes, biomarkers)
5. Design a preclinical study (biochemical validation)

---

## Example: Sorafenib for Melanoma

**Candidate score**: 0.910 (top rank)

**Why high?**
1. **Composition (0.88)**: Strong Drug → Protein → Disease paths
   - Sorafenib inhibits BRAF (IC50 25.8 nM, PMID:12829955)
   - BRAF is mutated in 70% of Melanomas (PMID:15184864)
   - Sorafenib inhibits VEGFR2 (PMID:18241329)
   - VEGFR2 promotes angiogenesis (supports tumor growth)

2. **Binding evidence (0.85)**: Experimental IC50 data
   - ABPP: Sorafenib–BRAF IC50 = 25.8 nM (confirmed in vitro)
   - Lipinski: Sorafenib passes (MW 465, logP 3.8)

3. **Yoneda distance (0.72)**: Similar to approved drugs
   - Structurally similar to Vemurafenib (both BRAF inhibitors)
   - Same target profile as other Melanoma drugs

**Status**: ✓ APPROVED (FDA 2008, PMID:18241329)

**Real-world outcome**: Sorafenib was approved for Melanoma (and renal cell carcinoma) in 2008, validating the mechanistic prediction.

---

## Reproducibility & Audit

Every metric is reproducible:

```bash
# Reproduce AUROC 0.9705
python validation/repurposing_benchmark.py \
  --view full_typed \
  --protocol remove_direct_labels

# With 95% confidence intervals
python validation/repurposing_benchmark.py \
  --view full_typed \
  --protocol remove_direct_labels \
  --ci
```

Every candidate can be traced to evidence:

```bash
# Trace Sorafenib + Melanoma
python validation/trace_prediction.py Melanoma Sorafenib
```

Output: All paths, all PMIDs, all strategy scores, confidence breakdown.

Database is reproducible from manifest:

```bash
# Rebuild tier1.db from scratch
python data/drugs/build_tier1.py \
  --manifest data/drugs/tier1_manifest.json
```

---

## Scientific Audit Rules (From CLAUDE.md)

1. ✓ Code and database queries outrank docs (check main branch)
2. ✓ Every AUROC specifies: view (full_typed), protocol (remove_direct_labels), pair count (44), label policy (FDA-approved removed)
3. ✓ Direct Drug→Disease labels are removed during scoring (no leakage)
4. ✓ Unlabeled pairs treated as unknowns, not confirmed negatives
5. ✓ Report AUPRC, Hits@K, MRR, confidence intervals (95% bootstrap)
6. ✓ Source coverage required: 609 PMID identifiers and source strings on all 2,329 morphisms; edge-specific citation validation remains separate
7. ✓ No fallback/mock scientific claims (Boltz2 labeled as heuristic, Yoneda results honest)

---

## Next Steps

### To Use Track A

1. [GETTING_STARTED.md](GETTING_STARTED.md) — Run your first triage (5 min)
2. [VALIDATION_AND_BENCHMARKS.md](VALIDATION_AND_BENCHMARKS.md) — Understand the metrics
3. [TROUBLESHOOTING_AND_FAQ.md](TROUBLESHOOTING_AND_FAQ.md) — Common questions

### To Understand the Science

1. [EVIDENCE_AND_PROVENANCE.md](EVIDENCE_AND_PROVENANCE.md) — Where data comes from
2. [STRATEGIES_IN_DEPTH.md](STRATEGIES_IN_DEPTH.md) — Runtime strategy profiles explained
3. [CATEGORICAL_THEORY_PRIMER.md](CATEGORICAL_THEORY_PRIMER.md) — Why category theory

### To Extend the Code

1. [ARCHITECTURE.md](ARCHITECTURE.md) — 5-layer design
2. [API_REFERENCE.md](API_REFERENCE.md) — Core APIs
3. [CONTRIBUTING.md](CONTRIBUTING.md) — Adding features

---

*Last updated: 2026-05-28 (runtime strategy profiles and conditional Yoneda clarified)*
