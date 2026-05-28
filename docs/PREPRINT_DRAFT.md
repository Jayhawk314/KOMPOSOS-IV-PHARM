> **Legacy/historical notice (2026-05-27):** This file is retained for background or session history. It is not the current source of truth for Track A metrics or provenance. Current docs are in `truedocs/`, especially `truedocs/VALIDATION_AND_BENCHMARKS.md` and `truedocs/REPRODUCIBILITY_PROTOCOL.md`. Current strict run: AUROC 0.974694 [0.9606, 0.9855], AUPRC 0.551698 [0.4067, 0.6983], Hits@5/10/20 1.0000/0.6000/0.6000; LOOCV AUROC 0.975916 and AUPRC 0.553703; Hetionet external AUROC 0.634479 and AUPRC 0.009255. Source strings exist on all 5,382 morphisms with 610 PMID identifiers; this is not 100% edge-specific citation validation. Retired or superseded claims in this file should be read as historical.
# Auditable Drug Repurposing via Categorical Knowledge Graphs with Full Provenance

**James Ray Hawkins**

**Correspondence**: jhawk314@gmail.com

---

## Abstract

We present KOMPOSOS-IV-PHARM, an auditable drug repurposing system that
combines a fully-cited biomedical knowledge graph with categorical inference
strategies to generate mechanistically explainable repurposing hypotheses.
Unlike embedding-based approaches that produce opaque rankings, every
prediction in our system is traceable to Drug->Protein->Disease evidence
chains with primary literature citations (PMIDs and ChEMBL IDs). On a curated
oncology graph of 78 drugs, 366 proteins, and 20 diseases (5,382 morphisms,
100% provenance coverage, 204 with quantitative evidence), the system achieves LOOCV AUROC 0.9616 [AUPRC 0.5668] on 44 FDA-approved indications,
and remove_direct_labels AUROC 0.965 [AUPRC 0.634, +0.097 improvement]. The system integrates
9 oracle strategies (composition, topos logic, Kan extensions, Yoneda pattern, binding evidence,
structural hole, type heuristic, fibration lift, Yoneda distance) with mechanistic path bonuses,
Yoneda distance bonuses, and quantitative evidence (204 edges with IC50, mutation frequency,
hazard ratio, response rate from NLP extraction of 204 PMIDs). The curated graph backbone achieves
AUROC 0.931 via shortest-path traversal -- demonstrating that careful curation of a small,
high-quality graph can match or exceed larger, noisier knowledge graphs. The categorical inference
layer combined with molecular binding evidence (ABPP IC50 data, drug-likeness, Pfam domain matching)
and structural similarity metrics adds significant ranking improvement (+0.034 AUROC, +0.154 AUPRC)
and crucially provides strategy voting, mechanistic explanation, binding evidence, quantitative
validation, and type-safe reasoning that researchers need for candidate evaluation. A ClinicalTrials.gov
cross-check found that 63% of top repurposing candidates are already in human clinical trials, 30% have
preclinical support, and 7% are genuinely novel hypotheses. The system is designed for hypothesis
generation and scientific triage, not clinical deployment.

**Keywords**: drug repurposing, category theory, knowledge graphs, Kan
extensions, topos logic, oncology

---

## 1. Introduction

Drug repurposing -- finding new therapeutic uses for existing approved drugs --
offers a faster, cheaper path to treatment than de novo drug discovery.
Computational approaches using knowledge graphs have shown promise, with
systems like Rephetio (Himmelstein et al., 2017) and others achieving strong
predictive performance. However, most systems rely on embedding-based or
machine learning approaches that function as black boxes, providing rankings
without mechanistic explanations.

**For non-computational readers**: A knowledge graph is a network where drugs,
proteins, and diseases are nodes connected by directed relationships (edges)
with confidence scores. Example: "Mebendazole -inhibits-> VEGFR2" and "VEGFR2
-drives-> HCC" form a Drug→Protein→Disease mechanistic path. Our system uses
seven different mathematical strategies to evaluate whether such paths are
biologically plausible, then combines their votes into a final score.

We present a fundamentally different approach: using enriched category theory
as the computational framework for drug repurposing. Category theory provides
a principled mathematical foundation for reasoning about relationships, with
operations like Kan extensions (colimit-based inference), Yoneda lemma
(structural similarity), and topos logic (intuitionistic evidence reasoning)
that have natural interpretations in the biomedical domain.

Our contributions:

1. **A categorical inference framework** with 8 strategies grounded in
   different mathematical and molecular lenses, each producing interpretable
   predictions
2. **Full provenance**: every edge in the knowledge graph is traceable to a
   PMID or ChEMBL identifier (1260/1260, 100%)
3. **Mechanistic explainability**: every prediction comes with Drug->Protein->
   Disease evidence chains
4. **Rigorous validation**: LOOCV, bootstrap CIs, 5 graph baselines, ablation
   studies, and clinical trial cross-checks
5. **An open-source triage tool** for scientists to inspect and audit
   predictions

---

## 2. Methods

### 2.1 Knowledge Graph Construction

The knowledge graph was built from curated sources:

- **Drugs**: 78 FDA-approved drugs (oncology focus), sourced from DrugBank and
  manual curation
- **Proteins**: 366 proteins including receptors, oncogenes, tumor suppressors,
  and signaling molecules, sourced from ChEMBL drug_mechanism table
- **Diseases**: 20 cancer types
- **ExternalCompound nodes**: 679 ChEMBL supporting compounds
- **Morphisms**: 1260 directed edges with confidence scores:
  - Drug->Protein (inhibits, activates, modulates): from ChEMBL drug mechanisms
  - Protein->Disease (driver_of, associated_with): from literature curation
  - Drug->Disease (treats): 44 FDA-approved oncology indications
- **Provenance**: 1260/1260 morphisms (100%) have PMIDs or ChEMBL IDs

The graph is stored as a SQLite database (`tier1.db`) built deterministically
from a JSON manifest via `build_tier1.py`. The database SHA256 is
`0BA4A7E01BBA3E1E52A03CD7765A3E6523618F439AB8A90ED4BD6B4BD95BC8E6`.

### 2.2 Categorical Framework

The graph is modeled as a category enriched over a multiplicative quantale:
objects are drugs, proteins, and diseases; morphisms are directed relationships
with confidence values in [0,1]. Composition uses multiplicative enrichment:
conf(A->C) = conf(A->B) * conf(B->C).

### 2.3 Inference Strategies

Eight strategies predict missing Drug->Disease morphisms. Seven use graph
topology; the eighth aggregates molecular binding evidence:

1. **KanExtensionStrategy**: Left Kan extension via colimit over comma
   category. If objects similar to the source connect to the target, predict
   the source should too.

2. **CompositionStrategy**: Transitive closure -- if Drug->Protein->Disease
   paths exist via protein intermediates, predict Drug->Disease. For Drug->
   Disease pairs, requires protein intermediates (type filtering).

3. **YonedaPatternStrategy**: The Yoneda lemma implies objects with identical
   morphism profiles (Hom(A,-) = Hom(B,-)) are structurally equivalent. If
   drug B treats disease D and drug A has a similar morphism profile, predict
   A treats D.

4. **ToposLogicStrategy**: Intuitionistic logic via Heyting algebra and
   presheaf topos. For Drug->Disease pairs, uses ONLY pathway-based evidence
   (no direct edge lookup) to prevent label leakage.

5. **FibrationLiftStrategy**: Uses fibration structure (fibers = object types)
   for Cartesian lifts: transfers relationships across type fibers.

6. **StructuralHoleStrategy**: Triangle closure -- if Drug->Protein and
   Protein->Disease exist, predict Drug->Disease.

7. **TypeHeuristicStrategy**: Type-constrained rules based on domain knowledge
   (e.g., Drug + Disease -> "treats" prediction).

8. **BindingEvidenceStrategy**: Aggregates molecular/chemistry binding evidence
   from 5 bridges: ABPP experimental IC50 data (65 entries with PMIDs),
   Boltz2 heuristic binding, Lipinski drug-likeness, drug-target molecular
   compatibility (logP/H-bond matching), molecular bridge scorers
   (solubility/steric/reactivity), and Pfam domain matching. Drug molecular
   properties (MW, logP, HBD, HBA) verified against PubChem PUG REST API
   (46/68 drugs corrected).

### 2.4 Scoring

For each Drug-Disease pair, all 8 strategies are queried. Scores are combined:

```
base = mean(strategy_confidences)
path_bonus = min(0.25, 0.10 * composition_path_count)
score = min(1.0, base + path_bonus)
```

Strategy weights are uniform (confirmed optimal by LOOCV grid search via
`calibrate_loocv.py`). The path bonus rewards mechanistic Drug->Protein->
Disease chains and was tuned via LOOCV grid search (`tune_path_bonus.py`).

**Note**: Individual morphism confidences in evidence chains (e.g., "Drug inhibits
Protein" = 0.65) reflect the plausibility of single relationships. The final
candidate score aggregates across multiple strategies and paths, which is why
high scores (0.9+) can have moderate edge confidences (0.6-0.8). This is
expected: multiple moderate-confidence paths provide stronger evidence than a
single high-confidence path.

### 2.5 Evaluation Protocol

**Primary metric**: Leave-One-Out Cross-Validation (LOOCV). For each of the 44
positive Drug->Disease pairs, the direct edge is removed from the graph, the
pair is scored using the remaining graph, and AUROC is computed over all
Drug x Disease combinations (1560 pairs: 44 positives, 1516 negatives).

**Additional metrics**: AUPRC, Hits@5, MRR, bootstrap 95% confidence intervals
(1000 resamples, seed 42).

**Baselines**: Random, degree product, common neighbor, shortest path (BFS
depth 3), path count -- all computed on the same graph and label set.

**Open-world caveat**: Unlabeled Drug->Disease pairs are treated as negatives
for ranking, but they are open-world unknowns, not confirmed non-treatments.
This is standard practice (Himmelstein et al., 2017) but means AUROC measures
ranking ability, not clinical prediction accuracy.

---

## 3. Results

### 3.1 Primary Validation

| View | Protocol | AUROC | 95% CI | AUPRC | Hits@5 | MRR |
|------|----------|------:|--------|------:|-------:|----:|
| full_typed | loocv | 0.974 | [0.965, 0.983] | 0.530 | 1.00 | 0.080 |
| full_typed | remove_direct_labels | 0.940 | — | 0.431 | 0.60 | -- |
| legacy | as_loaded | 0.931 | — | 0.465 | -- | -- |

### 3.2 Baselines (LOOCV)

| Baseline | AUROC | Margin |
|----------|------:|-------:|
| Random | 0.562 | +0.412 |
| Degree product | 0.701 | +0.273 |
| Common neighbor | 0.918 | +0.056 |
| Shortest path | 0.931 | +0.043 |
| Path count | 0.826 | +0.148 |

The system exceeds all graph-topology baselines. The margin over the strongest
baseline (shortest path) is modest at +0.043 AUROC, indicating that the
categorical strategies add value beyond simple graph traversal but the bulk of
predictive signal comes from graph connectivity.

### 3.3 Ablation Study

| Configuration | AUROC | Delta |
|---------------|------:|------:|
| Full system (8 strategies) | 0.974 | -- |
| Remove composition | 0.929 | -0.045 |
| Remove topos_logic | 0.970 | -0.004 |
| Remove kan_extension | 0.972 | -0.002 |
| Composition only | 0.969 | -0.005 |

Composition is the dominant strategy, contributing the most to AUROC.
However, the ensemble of all 8 strategies outperforms any single strategy,
confirming the value of mathematical and molecular diversity.

### 3.4 Additional Validation (Reported)

- **External (Hetionet)**: AUROC 0.744 on 7 held-out Hetionet-confirmed pairs
- **Temporal holdout (2013 cutoff)**: AUROC 0.959 on 22 post-2013 FDA approvals
- **Disease-level holdout**: Mean AUROC 0.877 across 7 diseases (range 0.615-0.996)

These results are reported but not yet fully audit-reproduced with frozen
executable scripts and graph artifacts.

### 3.5 ClinicalTrials.gov Cross-Check

The top repurposing candidates (30 NOT_APPROVED predictions with highest
scores) were cross-checked against ClinicalTrials.gov and PubMed:

- **63% IN_TRIALS**: Already in active or completed human clinical trials
- **30% PRECLINICAL**: Published preclinical evidence (in vitro or animal models)
- **7% NOVEL**: No significant prior evidence found

This suggests the system surfaces clinically plausible hypotheses that real
clinical teams have independently found worth investigating.

---

## 4. Discussion

### 4.1 What Category Theory Adds

The categorical framework's primary contribution is architectural, not
performance-based. The AUROC lift over baselines is modest (+0.043). The value
is in what the framework provides beyond a score:

1. **Auditable explanations**: Each strategy has a precise mathematical
   definition (e.g., Kan extension = colimit over comma category). A
   researcher can inspect WHY a prediction was made, not just that it scored
   high.
2. **Typed composition with confidence**: Enriched category composition
   naturally handles multi-hop inference with confidence propagation and
   type constraints (e.g., Drug->Disease predictions REQUIRE protein
   intermediates).
3. **Strategy voting**: Eight independent lenses (7 mathematical + 1 molecular)
   produce consensus or disagreement, giving researchers a richer signal than
   a single score.
4. **Principled data integration**: Functorial imports from ChEMBL, STRING,
   and other sources preserve graph structure and provenance.

### 4.2 The Value of Curation Over Scale

Our strongest result may be the baseline: shortest-path traversal on 1260
carefully curated, fully-cited edges achieves AUROC 0.931. Published systems
using graphs 40x larger with millions of edges typically report AUROC
0.85-0.95 using black-box embeddings. This suggests that a small, high-quality
graph with complete provenance can match or exceed larger, noisier
alternatives -- while remaining fully auditable.

This has practical implications: a researcher using our system can trace any
prediction to primary literature in seconds. Embedding-based systems cannot
offer this.

### 4.3 Limitations

**Small graph**: 1143 objects and 1260 morphisms is small compared to systems
like Rephetio (47k nodes, 2.25M edges). Statistical power is limited.

**Oncology only**: The current graph covers 20 cancer types. Generalization to
other therapeutic areas requires expansion with appropriate data sources.

**Modest margin**: +0.043 AUROC over shortest-path baseline. Most predictive
signal comes from graph connectivity, not categorical math per se.

**Open-world negatives**: Unlabeled pairs are unknowns, not confirmed
negatives. AUROC measures ranking ability in a specific graph context.

**Path bonus tuning**: The path bonus parameters (min(0.25, 0.10 * n)) were
tuned on the same LOOCV protocol used for evaluation. The grid was small (9
configurations) and the improvement is mechanistically interpretable, but this
is a potential source of optimistic bias.

**No prospective validation**: All results are retrospective. Clinical utility
requires prospective validation.

### 4.4 Comparison to Published Systems

| System | AUROC | Positives | Graph Size |
|--------|------:|----------:|-----------:|
| Rephetio (Himmelstein 2017) | 0.97 | 755 | 47k nodes, 2.25M edges |
| KOMPOSOS-IV-PHARM (this work) | 0.974 | 44 | 1143 objects, 1260 edges |

Direct comparison is not valid due to different graphs, label sets, and
protocols. Our graph is ~40x smaller with ~17x fewer positives.

---

## 5. Availability

The system is open-source (Apache 2.0 / Commercial dual license):

- **Triage CLI**: `python validation/triage.py <Disease>`
- **Web demo**: `streamlit run app.py`
- **Benchmark**: `python validation/repurposing_benchmark.py --view full_typed --protocol loocv --ci --baselines`
- **Case studies**: See `CASE_STUDIES.md`

---

## References

1. Himmelstein DS, et al. Systematic integration of biomedical knowledge
   prioritizes drugs for repurposing. *eLife*. 2017;6:e26726.
2. Tanoli Z, et al. Validation approaches for computational drug repurposing.
   *Brief Bioinform*. 2024;25(1). PMC10785886.
3. Lobentanzer S, et al. Knowledge Graphs for drug repurposing: a review.
   *Brief Bioinform*. 2024;25(6):bbae461. PMC11426166.
4. Bittner DM, et al. Strategies for robust benchmarking of drug discovery
   platforms. *Bioinformatics*. 2025;41(11):btaf604.
5. Hanley JA, McNeil BJ. The meaning and use of the area under a ROC curve.
   *Radiology*. 1982;143(1):29-36.
6. Mac Lane S. Categories for the Working Mathematician. Springer, 1978.
7. Riehl E. Category Theory in Context. Dover, 2016.

---

*Draft prepared for bioRxiv submission. 2026-05-13.*
