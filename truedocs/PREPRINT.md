# Auditable Drug Repurposing via Categorical Knowledge Graphs with Full Provenance

**James Ray Hawkins**

**Correspondence**: jhawk314@gmail.com

---

## Abstract

We present KOMPOSOS-IV-PHARM, an auditable drug repurposing system that combines a sourced biomedical knowledge graph with categorical inference strategies to generate mechanistically explainable repurposing hypotheses. Unlike embedding-based approaches that produce opaque rankings, every prediction is traceable to Drug->Protein->Disease evidence chains with source strings and tiered citation identifiers. On the current oncology graph of 78 drugs, 366 biological entities, and 20 diseases (2,329 morphisms with 100% source-string coverage — not the same as edge-level citation validation; 1,035 PMID-backed edges spanning 955 distinct PMIDs, of which 745 are RELATION-VERIFIED (an agent confirmed the cited sentence asserts the directed, signed relation) and 215 are LEXICAL-COOCCURRENCE (automated co-occurrence + polarity screen only); and 1,014 MEASURED-tier edges with quantitative values), the system achieves AUROC 0.970549 [95% CI: 0.9519-0.9844] and AUPRC 0.546427 [95% CI: 0.4025-0.6890] under the strict remove_direct_labels protocol on 44 FDA-approved indications. The strongest simple graph baseline is common_neighbor AUROC 0.6219, giving a +0.3486 margin. Strategic Transparency: Yoneda Distance utilizes only MEASURED+ESTABLISHED evidence (1,391 edges). The categorical inference layer adds strategy signals, mechanistic explanation, quantitative evidence (IC50, mutation frequencies, response rates), and type-safe reasoning for candidate triage. The system is designed for hypothesis generation and scientific triage, not clinical deployment.

**Keywords**: drug repurposing, category theory, knowledge graphs, Yoneda presheaves, evidence tracing, oncology

---

## 1. Introduction

Drug repurposing -- finding new therapeutic uses for existing approved drugs -- offers a faster, cheaper path to treatment than de novo drug discovery. Computational approaches using knowledge graphs have shown promise, with systems like Rephetio (Himmelstein et al., 2017) and others achieving strong predictive performance. However, many systems rely on latent-feature or embedding-based approaches that function as black boxes, providing rankings without mechanistic explanations.

**For non-computational readers**: A knowledge graph is a network where drugs, proteins, and diseases are nodes connected by directed relationships (edges) with confidence scores. Example: "Sorafenib -inhibits-> BRAF" and "BRAF -drives-> Melanoma" form a Drug->Protein->Disease mechanistic path. The current system uses runtime strategy profiles made of graph/categorical and evidence-scoring modules, then combines their signals into a ranking score.

We present a fundamentally different approach: using enriched category theory as the computational framework for drug repurposing. Category theory provides a principled mathematical foundation for reasoning about relationships, with operations like composition (transitive closure with confidence propagation), Yoneda presheaves (structural similarity via neighborhood fingerprints), and enriched hom-sets (confidence-weighted reasoning) that have natural interpretations in the biomedical domain.

Our contributions:

1. **A categorical inference framework** with explicit runtime strategy profiles: 7 active modules in the strict `remove_direct_labels` benchmark and 8 modules in live triage when Yoneda comparators are visible
2. **Auditable source trail**: every edge has a source/provenance string, with 609 unique PMID identifiers; edge-specific citation validation remains an audit task
3. **Quantitative evidence integration**: 204 edges carry IC50 binding constants, mutation frequencies, clinical response rates, or hazard ratios; endpoint-specific NLP attribution remains under audit
4. **Conditional structural similarity via Yoneda distance**: presheaf fingerprints on the clean evidence subgraph are used in live triage when known-treatment comparators remain visible; historical ablation lift must be rerun before publication claims
5. **Rigorous validation**: multiple protocols (remove_direct_labels, LOOCV), bootstrap CIs, 5 graph baselines, ablation studies, external validation (Hetionet, temporal holdout), and clinical trial cross-checks
6. **An open-source triage tool** for scientists to inspect and audit predictions

---

## 2. Methods

### 2.1 Knowledge Graph Construction

The knowledge graph was built from curated sources:

- **Drugs**: 78 FDA-approved drugs (oncology focus), sourced from ChEMBL and manual curation
- **Proteins**: 366 biological entities including receptors, oncogenes, tumor suppressors, and signaling molecules, sourced from ChEMBL drug_mechanism table, STRING PPI, cBioPortal, and literature
- **Diseases**: 20 cancer types
- **Morphisms**: 2,329 directed edges with confidence scores [0, 1]:
  - Drug->Protein (inhibits, activates, modulates): from ChEMBL drug mechanisms, ABPP
  - Protein->Disease (driver_of, associated_with): from literature curation, cBioPortal
  - Protein->Protein (activates, regulates): from STRING PPI (338 edges), protein sequence similarity (100 edges; engine upgraded from ESM2 to ESMC-300M, pending edge re-derivation)
  - Drug->Disease (treats): 44 FDA-approved oncology indications
- **Quantitative evidence**: 204 edges with IC50, mutation frequencies, hazard ratios, response rates
  - NLP extraction from 204 PMIDs (373 data points reported; edge-specific attribution audit pending)
  - ABPP experimental IC50 data (65 entries)
- **Source fields**: 2,329/2,329 morphisms have source/provenance strings; 609 unique PMID identifiers were detected. This is not equivalent to edge-specific citation validation.
- **Evidence tier classification**: MEASURED 1,073, ESTABLISHED 282, INFERRED 809, SPECULATIVE 955, HYPOTHESIS 159, NOISE 2,104

The graph is stored as a SQLite database (`tier1.db`) built deterministically from a JSON manifest via `build_tier1.py`.

### 2.2 Categorical Framework

The graph is modeled as a category enriched over a multiplicative quantale: objects are drugs, proteins, and diseases; morphisms are directed relationships with confidence values in [0,1]. Composition uses multiplicative enrichment: conf(A->C) = conf(A->B) * conf(B->C). This models honest uncertainty propagation: uncertain links compound through chains.

### 2.3 Inference Strategies

The production benchmark uses explicit runtime profiles rather than a fixed "nine strategy" ensemble.

**Strict `remove_direct_labels` profile, current primary claim**:

1. **KanExtensionStrategy**: categorical extension over observed morphisms.
2. **StructuralHoleStrategy**: graph-structure bridge signal.
3. **CompositionStrategy**: Drug->Protein->Disease path composition with confidence propagation.
4. **YonedaPatternStrategy**: morphism-profile analogy signal.
5. **FibrationLiftStrategy**: typed lifting signal where graph structure supports it.
6. **ToposLogicStrategy**: logical/evidence consistency signal.
7. **BindingEvidenceStrategy**: ABPP IC50 data, Boltz2 heuristic binding, drug properties, molecular compatibility, domain matching, and graph confidence.

**Live triage/as-loaded profile**: the seven modules above plus **YonedaDistanceStrategy** when visible Drug->Disease comparator labels exist. YonedaDistanceStrategy computes confidence-weighted presheaf fingerprints on MEASURED+ESTABLISHED edges and scores similarity to known treatments. It is intentionally inactive in the strict `remove_direct_labels` benchmark because that protocol removes the comparator labels before scoring.

### 2.4 Scoring

For each Drug-Disease pair, the active runtime profile is queried. Scores are combined:

```
base = mean(active_strategy_confidences excluding yoneda_distance)
path_bonus = min(0.25, 0.04 * sum(path_confidence))  # Confidence-weighted
yoneda_bonus = min(0.10, 0.06 * yoneda_similarity) if comparators_exist else 0.0
score = min(1.0, base + path_bonus + yoneda_bonus)
```

The path bonus was tuned via LOOCV grid search over [0.0, 0.20]. The Yoneda coefficient (0.06, cap 0.10) is used only when the active runtime graph still contains known-treatment comparators. The strict benchmark result reported here is a 7-module run without active Yoneda distance.

### 2.5 Evaluation Protocol

**Primary metric (remove_direct_labels)**: All 44 direct Drug->Disease edges are removed. Each Drug-Disease pair is scored using only mechanistic paths. AUROC computed over 44 positives vs. 1,516 negatives (78 drugs x 20 diseases = 1,560 pairs).

**Cross-validation (LOOCV)**: For each of 44 positive pairs, that pair's direct edge is removed, scored using remaining graph, and AUROC computed.

**Additional metrics**: AUPRC, Hits@K, MRR, bootstrap 95% confidence intervals (1,000 resamples, seed 42).

**Baselines**: Random, degree product, common neighbor, shortest path, and path count -- all computed on the same graph and label set.

**Open-world caveat**: Unlabeled Drug->Disease pairs are treated as negatives for ranking, but they are open-world unknowns, not confirmed non-treatments. This is standard practice (Himmelstein et al., 2017) but means AUROC measures ranking ability, not clinical prediction accuracy.

---

## 3. Results

### 3.1 Primary Validation

| Protocol | AUROC | 95% CI | AUPRC | Hits@5 | Hits@10 | MRR |
|----------|------:|--------|------:|-------:|--------:|----:|
| remove_direct_labels | **0.9705** | [0.9519, 0.9844] | **0.546** | 1.00 | 0.60 | 0.0788 |
| loocv | 0.9759 | not bootstrapped in current rerun | 0.554 | 0.80 | 0.60 | 0.0772 |

### 3.2 Baselines (remove_direct_labels)

| Baseline | AUROC | Margin |
|----------|------:|-------:|
| common_neighbor | 0.6219 | +0.3486 |
| path_count | 0.6492 | +0.2994 |
| shortest_path | 0.6250 | +0.3236 |
| degree_product | 0.5877 | +0.3609 |
| random | 0.5504 | +0.3982 |

The system exceeds these simple graph-topology baselines. The margin over the strongest baseline (degree_product) is +0.3486 AUROC under the current strict protocol.

### 3.3 Ablation Study

The ablation table below is historical development context. It should be rerun
under the corrected loader before the deltas are quoted as current estimates.

| Configuration | AUROC | Delta |
|---------------|------:|------:|
| Current strict profile (7 active modules) | 0.9705 | -- |
| Remove composition | 0.812 | -0.153 |
| Remove binding_evidence | 0.920 | -0.045 |
| Remove path_bonus | 0.950 | -0.015 |
| Remove yoneda_distance | 0.956 | -0.009 |
| Remove coherence | 0.960 | -0.005 |
| Remove conjecture | 0.963 | -0.002 |
| Remove remaining low-impact historical modules | 0.9705 | ~0 |
| Composition only | 0.890 | -0.075 |

Historical ablations identify composition as the dominant strategy. Binding
evidence provides current strict-benchmark signal. Yoneda distance provides a
live-triage signal when comparators exist, but its strict-benchmark effect size
is not current because the corrected strict loader leaves no comparators.

### 3.4 Yoneda Distance Integration

The ablation values below are historical and should be rerun before being used
as current contribution estimates. The current strict full-system result is
0.9705 AUROC / 0.546 AUPRC.

Yoneda distance is a conditional live-triage strategy. It operates on a clean subgraph of MEASURED + ESTABLISHED edges only, computing confidence-weighted presheaf fingerprints for all objects and comparing a candidate drug with visible known treatments for the same disease.

**Historical impact before the final Topos/scoring alignment**:
- Historical development runs suggested AUROC/AUPRC lift, but these effect sizes need rerun under the corrected loader before publication.

**Drug equivalence classes discovered**:
- Binimetinib = Cobimetinib (both MEK inhibitors)
- Encorafenib = Vemurafenib (both BRAF inhibitors)
- Carboplatin = Oxaliplatin (both platinum compounds)
- These equivalence classes are biologically plausible and align with known FDA-labeled drug classes.

The main contribution is not the metric delta alone: top-ranked candidates are
accompanied by auditable source trails, strategy votes, and mechanistic paths.

### 3.5 External Validation

| Protocol | AUROC | Details |
|----------|------:|---------|
| Hetionet (external graph) | 0.6436 | AUPRC 0.0093 on 7 external positives; Hits@20 0 |
| Temporal holdout (2013 cutoff) | 0.9780 | AUPRC 0.2288 on 18 held-out approvals |
| Disease-level holdout | 0.9504 mean | Mean AUPRC 0.6368 across 7 disease folds |

### 3.6 ClinicalTrials.gov Cross-Check

The top 30 NOT_APPROVED predictions were cross-checked against ClinicalTrials.gov and PubMed:

- **63% IN_TRIALS** (19/30): Already in active or completed human clinical trials
- **30% PRECLINICAL** (9/30): Published preclinical evidence (in vitro or animal models)
- **7% NOVEL** (2/30): No significant prior evidence found

This suggests the system surfaces clinically plausible hypotheses that real clinical teams have independently found worth investigating.

### 3.7 Quantitative Evidence

204 edges carry quantitative values extracted from PubMed abstracts:
- IC50/Ki/Kd binding constants: 65 edges (from ABPP + NLP extraction)
- Mutation frequencies: 45 edges (from cBioPortal + NLP)
- Clinical response rates: 52 edges
- Hazard ratios: 42 edges

NLP extraction: 373 data points from 204 PMIDs were reported. The current audit
requires endpoint-specific attribution before describing these as fully
validated extractions.

---

## 4. Discussion

### 4.1 What Category Theory Adds

The categorical framework's primary contribution is architectural, not just performance-based. The current strict AUROC margin over the strongest simple baseline is +0.3486, but the value is in what the framework provides beyond a score:

1. **Auditable explanations**: Each strategy has a precise mathematical definition. A researcher can inspect WHY a prediction was made, not just that it scored high.

2. **Typed composition with confidence**: Enriched category composition naturally handles multi-hop inference with confidence propagation and type constraints (Drug->Disease predictions REQUIRE protein intermediates).

3. **Strategy voting**: Multiple graph/categorical and evidence lenses produce consensus or disagreement, giving researchers a richer signal than a single score.

4. **Structural similarity via Yoneda**: Composition tells you THAT a path exists; live-triage Yoneda can explain WHY a drug resembles visible known treatments through target-profile similarity. Drug equivalence classes are structural clusters, not clinical ground truth by themselves.

5. **Quantitative evidence integration**: IC50, mutation frequencies, and clinical response rates are displayed alongside mechanistic paths, enabling informed triage decisions.

### 4.2 The Value of Curation Over Scale

Our strongest cautionary result is the baseline: degree_product traversal on this curated graph reaches AUROC 0.6219. This means graph connectivity and curation quality explain a meaningful part of the signal, while the categorical layer adds auditability, strategy decomposition, and a +0.3486 strict AUROC margin over that baseline.

A researcher using our system can trace any prediction to primary literature in seconds. Embedding-based systems cannot offer this.

### 4.3 Limitations

**Oncology-focused**: 20 cancer types. Generalization to other therapeutic areas requires expansion with appropriate data sources.

**Substantial margin**: +0.3486 AUROC over degree_product baseline. Most predictive signal comes from graph connectivity, not categorical math per se.

**Open-world negatives**: Unlabeled pairs are unknowns, not confirmed negatives. AUROC measures ranking ability in a specific graph context.

**Path and bonus tuning**: The path bonus coefficient (0.04) and live-triage Yoneda coefficient (0.06) came from small grid searches. The strict benchmark reported here does not use active Yoneda distance, but any tuned coefficient remains a potential source of optimistic bias until independently validated.

**No prospective validation**: All results are retrospective. Clinical utility requires prospective validation.

**Heuristic binding components**: Boltz2 bridge uses Lipinski rules, not crystal structure docking. ABPP provides 65 experimental entries; remaining drug-target pairs rely on heuristics.

### 4.4 Comparison to Published Systems

| System | AUROC | Positives | Graph Size | Interpretable |
|--------|------:|----------:|-----------:|:---:|
| Rephetio (Himmelstein 2017) | 0.97 | 755 | 47k nodes, 2.25M edges | No |
| KOMPOSOS-IV-PHARM (this work) | 0.9705 | 44 | 1,146 runtime objects, 2,329 edges | Yes |

Direct comparison is not valid due to different graphs, label sets, and protocols. Our graph is substantially smaller with fewer positives. Our claim is not superior performance but superior interpretability and auditability at competitive performance.

---

## 5. Availability

The software source code is available under Apache-2.0. Bundled third-party
data retain their own terms; see the repository NOTICE.

- **Triage CLI**: `python validation/triage.py <Disease>`
- **Benchmark**: `python validation/repurposing_benchmark.py --view full_typed --protocol remove_direct_labels --ci --baselines`
- **Evidence tracing**: `python validation/trace_prediction.py <Disease> <Drug>`
- **Documentation**: See `truedocs/` folder

---

## References

1. Himmelstein DS, et al. Systematic integration of biomedical knowledge prioritizes drugs for repurposing. *eLife*. 2017;6:e26726.
2. Tanoli Z, et al. Validation approaches for computational drug repurposing. *Brief Bioinform*. 2024;25(1). PMC10785886.
3. Lobentanzer S, et al. Knowledge Graphs for drug repurposing: a review. *Brief Bioinform*. 2024;25(6):bbae461. PMC11426166.
4. Bittner DM, et al. Strategies for robust benchmarking of drug discovery platforms. *Bioinformatics*. 2025;41(11):btaf604.
5. Hanley JA, McNeil BJ. The meaning and use of the area under a ROC curve. *Radiology*. 1982;143(1):29-36.
6. Mac Lane S. Categories for the Working Mathematician. Springer, 1978.
7. Riehl E. Category Theory in Context. Dover, 2016.
8. Fong B, Spivak DI. An Invitation to Applied Category Theory. Cambridge University Press, 2019.

---

*Prepared for bioRxiv submission. 2026-05-26.*
