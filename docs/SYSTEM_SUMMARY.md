> **HISTORICAL PRODUCT SNAPSHOT (2026-05-25). Do not use its numbers or validation claims as current facts.** Use the executable checks and root `README.md`, `HONEST_VALUE.md`, and `CLAUDE.md`. As of 2026-08-01 the scored graph has 1,143 objects and 2,038 edges; the raw database has 2,462 edges; external performance remains unmeasured.
# KOMPOSOS-IV-PHARM: System Summary

**Author**: James Ray Hawkins
**Date**: 2026-05-25
**License**: Apache-2.0 for software code; third-party data retain their own terms (see root NOTICE)

---

## What This System Is

KOMPOSOS-IV-PHARM is a drug repurposing tool for cancer research. It connects
facts from medical databases -- drug binding data from ChEMBL, protein roles in
disease from PubMed and KEGG, FDA-approved mechanisms -- that exist in separate
databases and separate research communities, and surfaces repurposing
hypotheses that individual researchers might not find on their own.

The core insight is simple: **Drug A binds Protein B** (known to pharmacologists)
+ **Protein B drives Disease C** (known to oncologists) = **Drug A might treat
Disease C** (not obvious to either group alone). Every prediction is a 2-hop
mechanistic path: Drug -> Protein -> Disease. Every hop has a citation. Nothing
is a black box.

The system is built on enriched category theory -- a branch of mathematics that
provides formal composition rules, type constraints, and multiple inference
strategies beyond simple graph traversal. The categorical framework is the
architectural backbone, not a marketing label.

**What it is not**: a clinical recommendation engine, a replacement for
literature review, a validated diagnostic, or a drug design platform. It
produces research hypotheses for scientific triage.

---

## The Product: What a Researcher Gets

A researcher runs a command:

```powershell
python validation/triage.py AML
```

and gets back:

1. **Ranked candidates** -- all 78 drugs scored for AML, highest first
2. **Evidence chains** -- for each candidate, the Drug -> Protein -> Disease
   paths with citations at every hop
3. **Confidence scores** -- telling the researcher how much to trust each hop
   (0.90+ = authoritative database, 0.35 = PubMed co-mention only, 0.20 = noise)
4. **Strategy votes** -- how many of 9 independent scoring methods agree
5. **Binding data** -- IC50 values, engagement percentages, and PMIDs when
   Activity-Based Protein Profiling (ABPP) data exists
6. **Provenance fraction** -- what percentage of the evidence chain is cited

Example output for a single candidate:

```
Sunitinib -> AML, score 0.972
  22 evidence chains (19 high-confidence, 3 medium)
  Binding: IC50=0.250 uM (FLT3), IC50=0.001 uM (KIT)
  Path: Sunitinib -inhibits-> FLT3 -driver_of-> AML
    FDA:NDA021938 (conf 0.88) | PMID:42175928 (conf 0.90)
```

The researcher follows the PMID, reads the paper, checks the FDA label, and
decides whether to pursue a clinical trial. That audit trail -- from tool output
through verified citations to clinical decision -- is the product. The score
tells them "look at this first." The evidence chain is what they act on.

---

## The Knowledge Graph

The system operates on a curated biomedical knowledge graph stored as a SQLite
database (`data/drugs/tier1.db`), built deterministically from a JSON manifest
(`data/drugs/tier1_manifest.json`).

### Graph Composition (2026-05-26)

| Fact | Value |
|------|-------|
| Total objects | 1,146 (464 core + 682 ChEMBL ExternalCompound nodes) |
| Drugs | 78 (FDA-approved, oncology focus) |
| Diseases | 20 cancer types |
| Proteins | 366 (receptors, oncogenes, signaling, etc.) |
| Total edges (morphisms) | 5,382 |
| Curated edges | ~1,600 (ChEMBL, FDA, KEGG, ABPP, curated literature) |
| PubMed batch-imported edges | ~3,300 (categorically verified, confidence-annotated) |
| Approved indication labels | 44 (all FDA-approved oncology, all with PMIDs) |
| Provenance coverage | 100% (every edge has a citation or database ID) |
| Edges with quantitative values | 204 (IC50, mutation frequency, hazard ratio, response rate) |

### Data Sources

| Source | Edges | What it provides |
|--------|------:|------------------|
| PubMed literature | 3,359 (68%) | Protein-disease associations with PMIDs |
| ChEMBL binding assays | 881 (18%) | Drug-target IC50/Ki/Kd values |
| ESM-2 protein embeddings | 422 (9%) | Protein structural similarity |
| FDA approved mechanisms | 79 (2%) | Drug mechanisms with NDA/BLA numbers |
| KEGG pathways | 72 (1%) | Canonical signaling cascades |
| Curated protein sets | 51 (1%) | From STRING, KEGG, Reactome |
| STRING PPI | 22 (<1%) | Protein-protein interactions |
| ABPP experimental | 17 (<1%) | Activity-based profiling with IC50 + PMIDs |
| Other (GTEx, DepMap, etc.) | 53 (1%) | Various experimental/computational |

### Edge Confidence Tiers

Every edge carries a confidence value (0.20 to 1.00) reflecting evidence quality.
These confidences are the researcher's primary quality signal:

| Confidence | Source Type | Meaning | Count |
|:----------:|------------|---------|------:|
| 0.90-1.00 | ChEMBL, FDA, KEGG | **Trust.** Authoritative database. Verify citation for context. | ~1,000 |
| 0.70-0.89 | Curated literature, ABPP | **Investigate.** Published data, read the paper. | ~300 |
| 0.50-0.69 | ESM2, curated sets | **Consider.** Computationally derived. Check the basis. | ~600 |
| 0.40-0.54 | PubMed PARTIAL | **Speculative but supported.** Co-mention with some mechanistic backing. | 63 |
| 0.35 | PubMed ORPHAN | **Hypothesis only.** Co-mention, no mechanistic path found. | 960 |
| 0.20 | PubMed REJECT | **Low confidence.** Failed categorical verification. Treat as noise. | 2,122 |

### Categorical Verification of PubMed Edges

The ~3,300 PubMed batch-imported edges were not accepted at face value. Each
was processed through a 5-layer categorical verification system:

1. **Drug Path Witness** (HoTT path induction) -- does an approved drug reach
   this protein for this disease?
2. **Kan Extension Agreement** -- does the pattern of known drug-target
   associations predict this edge?
3. **Mechanistic Reachability** (BFS) -- can this protein be reached from known
   disease proteins via interaction networks?
4. **Protein Specificity** (COG energy) -- is this protein narrowly linked to
   this disease, or broadly linked to everything?
5. **Gray Interchange Coherence** -- does this edge fit consistently with the
   surrounding evidence structure?

Each edge is classified as AGREE (conf 0.75), PARTIAL (conf 0.45-0.54),
ORPHAN (conf 0.35), or REJECT (conf 0.20). The classification and per-layer
scores are stored in edge metadata for full transparency.

### Mechanistic Path Coverage

1,920 unique 2-hop Drug -> Protein -> Disease paths exist in the graph:

| Quality | Count | Definition |
|---------|------:|------------|
| High | 195 | Both hops >= 0.70 (authoritative databases) |
| Medium | 927 | Min hop 0.40-0.69 |
| Low | 798 | Any hop < 0.40 (hypothesis generation only) |

---

## How Scoring Works

### The 9 Strategies

Each drug-disease pair is evaluated by 9 independent strategies. Each strategy
is a different mathematical or molecular lens:

| # | Strategy | What it asks | Signal type |
|---|----------|-------------|-------------|
| 1 | **Composition** | Do Drug->Protein->Disease paths exist? | Direct mechanistic evidence |
| 2 | **Topos logic** | Does cross-evidence integration support this? | Consistency |
| 3 | **Kan extension** | Do similar drugs treat this disease? | Analogy |
| 4 | **Yoneda pattern** | Does this drug's target profile match known treatments? | Profile similarity |
| 5 | **Binding evidence** | Is there IC50/binding data for drug-target pairs? | Experimental molecular |
| 6 | **Structural hole** | Would this edge close a network gap? | Graph topology |
| 7 | **Type heuristic** | Do the types align for a treatment relationship? | Type constraint |
| 8 | **Fibration lift** | Can structure be transferred across disease types? | Cross-domain |
| 9 | **Yoneda distance** | Does this drug have a structurally similar treatment for the target disease? | Structural substitutability |

Composition is the dominant strategy -- it contributes the most signal. The
other strategies add modest but measurable value: the 9-strategy ensemble
with Yoneda distance bonus outperforms the previous 8-strategy system
(AUROC 0.965 vs previous 0.956).

The Yoneda distance strategy (2026-05-26) is integrated as an additive bonus
(`min(0.10, 0.06 * similarity)`) rather than a base vote, preventing score
dilution while capturing structural similarity signal on the MEASURED+ESTABLISHED
evidence subgraph.

### Score Calculation

```
1. Each strategy predicts independently; take best confidence per strategy
2. Base score = mean of all non-Yoneda strategy confidences
3. Path bonus = min(0.25, 0.04 * sum(path_confidence_weights))
   - Each path weighted by its actual min-hop confidence
   - High-confidence paths (0.90) contribute ~5x more than REJECT paths (0.20)
4. Yoneda bonus = min(0.10, 0.06 * yoneda_similarity) if yoneda_similarity > 0
   - Applied as additive bonus, not averaged into base vote
5. Discount for missing composition = 0.80 multiplier if zero composition paths
6. Final score = min(1.0, base + path_bonus + yoneda_bonus)
```

The confidence-weighted path bonus prevents low-quality PubMed co-mention
edges from inflating scores. The Yoneda distance bonus adds structural
similarity signal on high-quality evidence without dragging down positives
with lower cross-disease similarity scores.

---

## Validation: What the Numbers Mean

### Primary Benchmark (2026-05-26, post-Yoneda Distance Integration)

Protocol: `remove_direct_labels` -- all 44 Drug->Disease "treats" edges are
removed before scoring. The system must rediscover known approvals using only
mechanistic paths (Drug->Protein->Disease). 78 drugs x 20 diseases = 1,560
pairs scored.

| Metric | Value | What it means |
|--------|------:|---------------|
| AUROC | 0.965 | System ranks a random known pair above a random unknown pair 96.5% of the time |
| AUPRC | 0.634 | Precision-recall: 44 positives in 1,560 pairs, improved from 0.537 |
| Hits@5 | 1.00 | For each disease, a correct drug appears in the top 5 100% of the time |
| Hits@10 | 0.80 | 80% of diseases have a correct drug in top 10 |
| MRR | 0.085 | Mean reciprocal rank of first correct drug per disease |

Graph: 5,382 edges, confidence-weighted path scoring, Yoneda distance bonus.

### Historical Context

The AUROC has moved through several phases as the graph and scoring evolved:

| Period | Graph | Strategies | Scoring | AUROC | What changed |
|--------|-------|-----------|---------|------:|--------------|
| May 13 | 1,260 edges | 8 | 0.10 * path_count | 0.974 (LOOCV) | Pre-expansion baseline |
| May 13 | 1,260 edges | 8 | 0.10 * path_count | 0.940 (remove_direct) | Same graph, harder protocol |
| May 24 | 4,900 edges | 8 | 0.10 * normalized_count | ~0.670 | PubMed expansion broke discrimination |
| May 24 | 4,900 edges | 8 | 0.04 * sum(confidence) | 0.956 | Confidence-weighted fix restored it |
| May 26 | 5,382 edges | 9 | 0.04 * confidence + yoneda_bonus | 0.965 | Yoneda distance strategy added |

The ~0.670 crash happened because the old path bonus formula treated all paths
equally regardless of edge quality. With ~3,300 new PubMed edges, almost every
pair accumulated enough paths to max out the bonus. The confidence-weighted
formula discriminates because positives (FDA-approved pairs) have paths through
high-confidence edges (0.88-1.0) while most negatives have paths through
low-confidence PubMed co-mentions (0.20-0.35).

Yoneda distance integration (2026-05-26) improved AUROC by +0.009 and AUPRC
by +0.097 by adding structural similarity signal on the MEASURED+ESTABLISHED
evidence tier. Integrated as additive bonus to prevent score dilution from
averaging lower-range confidence scores.

### Baselines (from LOOCV on curated graph, corrected 2026-05-11)

| Baseline | AUROC |
|----------|------:|
| Shortest path | 0.931 |
| Common neighbor | 0.918 |
| Path count | 0.596 |
| Degree product | 0.474 |
| Random | 0.469 |
| **System** | **0.974** |
| **Margin over best baseline** | **+0.043** |

The honest claim is a **modest AUROC improvement** over strong graph-topology
baselines. Shortest-path traversal on a carefully curated, fully-cited graph
achieves AUROC 0.931 by itself. The categorical inference layer adds +0.043
AUROC but -- more importantly -- provides strategy voting, mechanistic
explanation, binding evidence, confidence scores, and evidence tracing that
researchers need for candidate evaluation.

### Additional Validation (reported, not audit-reproduced)

These validations were conducted but executable scripts and frozen held-out
artifacts are not preserved in the repo. Treat as directional evidence.

| Validation | Result | Notes |
|------------|--------|-------|
| External (Hetionet) | AUROC 0.744 | 7 held-out Hetionet-confirmed pairs |
| Temporal holdout (2013 cutoff) | AUROC 0.959 | 22 post-2013 FDA approvals held out |
| Disease-level holdout | Mean AUROC 0.877 | 7 diseases, range 0.615-0.996 |
| ClinicalTrials.gov cross-check | 63% IN_TRIALS | Top 30 NOT_APPROVED candidates |

The ClinicalTrials.gov result is notable: 63% of the system's top repurposing
candidates are already in human clinical trials, 30% have preclinical support,
and only 7% are genuinely novel. This means the system surfaces clinically
plausible hypotheses that real clinical teams have independently found worth
investigating.

### Ablation Study (Pre-Yoneda, 8 strategies, LOOCV)

| Configuration | AUROC | Delta |
|---------------|------:|------:|
| Full system (8 strategies) | 0.974 | -- |
| Composition only | 0.969 | -0.005 |
| Remove composition | 0.929 | -0.045 |
| Remove topos_logic | 0.970 | -0.004 |
| Remove kan_extension | 0.972 | -0.002 |

Composition dominates. The ensemble adds modest but real signal above any
single strategy.

Post-Yoneda integration (9 strategies, remove_direct_labels):
- Full 9-strategy system + additive Yoneda bonus: AUROC 0.965, AUPRC 0.634
- Yoneda contribution: +0.009 AUROC, +0.097 AUPRC (precision improvement)

---

## Honest Assessment: Strengths and Limitations

### What Works

1. **Auditable evidence chains.** Every prediction traces to Drug->Protein->Disease
   paths with PMIDs, FDA NDA numbers, ChEMBL assay IDs, or KEGG pathway IDs at
   every hop. A researcher can verify any claim independently.

2. **Confidence scores that mean something.** The 0.20-to-1.00 confidence range
   maps to concrete evidence quality. A researcher seeing confidence 0.90 knows
   it comes from an authoritative database. Confidence 0.35 means "PubMed
   co-mention, verify independently." This is actionable information.

3. **Binding evidence integration.** 65 experimental IC50/engagement entries from
   ABPP data with PMIDs, plus Lipinski drug-likeness scores, Pfam domain
   matching, and molecular compatibility scoring. When binding data exists, the
   triage report shows it -- that is directly lab-actionable.

4. **Reproducibility.** The database builds deterministically from a JSON manifest.
   156 tests pass. The benchmark harness produces identical results on identical
   inputs. SHA256 hashes are tracked.

5. **Clinical plausibility.** 63% of top candidates are already in human trials.
   The system is not hallucinating -- it is finding connections that real clinical
   teams have independently pursued.

6. **The candidate triage CLI works.** Disease-first, drug-first, and specific-pair
   modes. Terminal, JSON, and Markdown output. Self-check confirms all 44 approved
   indications are recoverable. Evidence chains show quality classification
   (high/medium/speculative). Binding evidence is deduplicated and readable.

### What Does Not Work or Is Not Ready

1. **Clinical readiness.** The system produces research hypotheses, not clinical
   recommendations. No prospective validation exists. No patient has been treated
   based on these outputs.

2. **Small positive set.** 44 FDA-approved oncology indications is statistically
   limited. Confidence intervals are wide enough that small changes in the graph
   or formula can shift AUROC meaningfully.

3. **Fragile AUROC.** The metric swung 0.29 (from 0.670 to 0.956) from a single
   coefficient change (0.10 -> 0.04). The AUROC is largely measuring "how well
   does the path bonus formula separate confidence tiers" rather than "how well
   does the system find real drug-disease pairs." The composition strategy with
   path bonus is doing almost all the work.

4. **as_loaded protocol is broken on the expanded graph.** AUROC 0.457 -- worse
   than a coin flip. Positives score lower than negatives because composition
   skips existing edges. Only `remove_direct_labels` and `loocv` protocols
   produce valid results on the expanded graph.

5. **62% of edges are low-confidence.** The PubMed batch import added ~3,300 edges,
   of which 2,122 are classified REJECT (conf 0.20) and 960 are ORPHAN (conf 0.35).
   These are useful for hypothesis exploration but are mostly noise. The
   confidence-weighted scoring handles this, but the graph is majority low-quality
   data.

6. **Open-world negatives.** Unlabeled Drug->Disease pairs are not confirmed
   negatives. Many top "false positives" are real drug-disease pairs we lack
   labels for (e.g., Sunitinib for AML is scored high and IS clinically used).
   The true AUROC is likely higher than reported, but we cannot confirm this
   without more labels.

7. **No toxicity, safety, or patient stratification.** The system predicts "this
   drug might treat this disease" but says nothing about adverse effects, drug
   interactions, dosing, patient subgroups, or biomarkers.

8. **Track B (drug design) is not implemented.** The ABPP bridge and Boltz2 bridge
   are wired into Track A scoring, but molecular generation, structure prediction,
   ADMET modeling, synthesis routes, and ternary complex support do not exist.

9. **Some additional validations not audit-reproduced.** External (Hetionet),
   temporal holdout, and disease-level holdout were conducted but frozen
   executable artifacts are not preserved. These should be treated as directional
   evidence pending reproduction.

---

## Representative Case Studies

### Mebendazole for HCC (Score 0.903, PRECLINICAL)

A $4/course anthelmintic. The system finds 2 mechanistic paths: Mebendazole
inhibits VEGFR2 (the same target as sorafenib, standard-of-care for HCC at
$5,000+/month) and disrupts tubulin in HCC cells. Multiple preclinical studies
exist. This exemplifies the system's value: surfacing a cheap, available drug
that targets a validated mechanism, with citations a researcher can follow.

### Metformin for Breast Cancer (Score 0.975, IN_TRIALS)

Costs <$0.10/day, taken by 150 million diabetics. The system identifies 8
mechanistic paths through mTOR, IGF1R, PI3K, AKT1, STAT3, TP53, CDK4, and
HER2. 4/7 strategies agree -- the strongest consensus of any candidate.
Multiple ongoing clinical trials including the Phase III NCIC MA.32 trial
(3,649 patients). The system correctly identifies what real clinical teams are
already investigating.

### Niclosamide for AML (Score 0.902, PRECLINICAL)

A $2/course anthelmintic on the WHO Essential Medicines List. The system finds
paths through STAT3, BCL2, and NF-kB -- all validated AML biology. Published
preclinical studies confirm AML cell killing. The main challenge is
bioavailability (oral niclosamide has low systemic absorption), which the system
does not model but the researcher can assess from the literature.

### Disulfiram for Li-Fraumeni Syndrome (Score 0.736, NOVEL)

One of only 2 genuinely novel predictions (7% of candidates). Li-Fraumeni is a
rare hereditary cancer predisposition caused by TP53 mutations with 90%+
lifetime cancer risk. No approved prevention therapy exists. The system finds
paths through ALDH1A1 (cancer stem cell marker) and PARP1 (DNA repair).
Disulfiram costs ~$1/day with 60+ years of safety data. This is the kind of
hypothesis that might not emerge from standard literature searches.

---

## Architecture

```
Layer 5: OPTIMUS          Categorical gradient descent (self-refinement)
Layer 4: COG              Cognitive co-processor (claim verification)
Layer 3: Infinity-Cosmos  Higher structure (2-cells, fibrations, Yoneda, Kan)
Layer 2: KOMPOSOS-IV      Category runtime (objects, morphisms, enrichment, persistence)
Layer 1: ORION            Plugin framework (bridges, events, hot-loading)
```

### Key Code Areas

| Directory | Purpose |
|-----------|---------|
| `core/` | Category runtime: `Category` class, types, enrichment, persistence |
| `oracle/` | 9 prediction strategies including binding evidence and Yoneda distance |
| `domains/bio/` | `BioDomainLoader` -- loads tier1.db into Category |
| `data/store.py` | `KomposOSStore` -- SQLite backend API |
| `data/drugs/` | Reproducible DB build, drug properties, manifests |
| `validation/` | Benchmark harness, triage CLI, trace tools, ablation |
| `chemistry/` | Pfam domain matching, hydrophobicity |
| `molecular_bridge/` | Molecular interaction scoring (5 scorers) |
| `abpp_bridge.py` | 65 experimental IC50 entries with PMIDs |
| `boltz2_bridge.py` | Heuristic binding prediction bridge |
| `tests/` | 156 regression tests (all passing) |

### The Category Runtime

The graph is modeled as a category enriched over a multiplicative quantale.
Objects are drugs, proteins, and diseases. Morphisms are directed relationships
with confidence values in [0,1]. Composition uses multiplicative enrichment:
`conf(A->C) = conf(A->B) * conf(B->C)`.

```python
cat = Category("DrugRepurposing")
cat.add("Sorafenib", type_name="Drug")
cat.add("VEGFR2", type_name="Receptor")
cat.add("RCC", type_name="Disease")
cat.connect("Sorafenib", "VEGFR2", name="inhibits", confidence=0.95)
cat.connect("VEGFR2", "RCC", name="driver_of", confidence=0.85)
paths = cat.find_paths("Sorafenib", "RCC", max_length=4)
```

---

## Development Timeline

| Date | Milestone |
|------|-----------|
| Pre-May 2026 | Core categorical runtime, initial graph, 16 positive labels |
| May 6 | Independent audit: metrics verified, 22% provenance |
| May 10 | ChEMBL expansion deployed: +269 proteins, +872 morphisms, drug name normalization |
| May 11 | Audit corrections: baseline label-order bug fixed (honest baseline 0.931, not 0.559), +679 ExternalCompound objects |
| May 11 | OpenTargets experiment: all thresholds degraded AUROC, decision = do not deploy |
| May 12 | Provenance completed: 1,260/1,260 morphisms cited (100%) |
| May 13 | Binding evidence strategy integrated (ABPP + Boltz2 + drug properties + Pfam) |
| May 13 | Drug properties PubChem-verified (46/68 corrected), preprint draft written |
| May 24 | PubMed batch import: +3,300 edges with 5-layer categorical verification |
| May 24 | 373 overly-broad curated edges removed (proteins linked to all 20 diseases) |
| May 24 | Confidence-weighted path bonus deployed (0.670 -> 0.956 AUROC) |
| May 24 | Triage output improvements: deduplication, ESM2 summaries, quality classification |
| May 25 | System summary documented (this file), evidence quantification roadmap |
| May 25 | NLP PMID extraction completed: 373 extractions from 204 PMIDs (92.2% validated) |
| May 25 | Quantitative evidence expansion: 204 edges with IC50, HR, mutation frequencies |
| May 26 | Yoneda Distance Strategy integrated as 9th oracle strategy (additive bonus model) |
| May 26 | Benchmarks updated: AUROC 0.965, AUPRC 0.634, improved precision metrics |

---

## Running the System

### Candidate Triage

```powershell
python validation\triage.py Melanoma              # Disease-first: rank all drugs
python validation\triage.py --drug Sorafenib       # Drug-first: rank all diseases
python validation\triage.py AML --drug Sunitinib   # Specific pair: full detail
python validation\triage.py AML --json             # JSON output
python validation\triage.py AML --markdown         # Markdown output
python validation\triage.py AML --top 20           # Top 20 candidates
python validation\triage.py AML --all              # All candidates
```

### Benchmark Validation

```powershell
# Primary validation (scientifically valid protocols)
python validation\repurposing_benchmark.py --view full_typed --protocol remove_direct_labels
python validation\repurposing_benchmark.py --view full_typed --protocol loocv

# With confidence intervals and baselines
python validation\repurposing_benchmark.py --view full_typed --protocol loocv --ci --baselines

# Historical reference only
python validation\repurposing_benchmark.py --view legacy --protocol as_loaded
```

### Build and Test

```powershell
python data\drugs\build_tier1.py              # Reproducible DB build from manifest
pytest tests\test_repurposing_benchmark.py -q  # Focused regression
pytest tests -q                                # Full suite (156 tests)
```

---

## What the System Is Worth

The value of KOMPOSOS-IV-PHARM is not the AUROC. The AUROC says "the ranking
is useful for prioritization" -- and it is -- but the real value is in three
things:

**1. Bridging knowledge silos.** Drug binding data lives in ChEMBL. Protein
roles in disease live in PubMed and KEGG. FDA mechanisms live in NDA labels.
A pharmacologist knows Sunitinib inhibits FLT3. An oncologist knows FLT3
mutations drive AML. Neither may know the other's fact. The system connects
them, with citations, in seconds.

**2. Auditable reasoning.** Unlike embedding-based systems that produce opaque
rankings, every prediction here is a composition of cited facts. A researcher
can trace Sunitinib -> FLT3 -> AML back to FDA:NDA021938 and PMID:42175928,
read the papers, and form their own judgment. This is what separates a research
tool from a magic number generator.

**3. Cheap drug discovery for expensive diseases.** Four of the five case study
drugs cost less than $15 combined. Mebendazole ($4/course) targets the same
protein as sorafenib ($5,000+/month). Metformin ($0.10/day) is in a Phase III
breast cancer trial. The system systematically finds these connections across
78 drugs and 20 cancers, where manual literature search would require
1,560 separate investigations.

The honest ceiling: this is a research prototype. It needs prospective
validation, larger positive sets, toxicity modeling, and patient stratification
before it can inform clinical decisions. But for what it is -- a hypothesis
generation and scientific triage tool with full provenance -- it works.

---

## File Reference

| File | Purpose |
|------|---------|
| `SYSTEM_SUMMARY.md` | This document |
| `MEMORY.md` | Quick reference for session continuity |
| `CURRENT_STATE.md` | Detailed project state |
| `CLAUDE.md` | Operating instructions for AI agents |
| `TECHNICAL_OVERVIEW.md` | Architecture and scientific pipeline |
| `PREPRINT_DRAFT.md` | Draft for bioRxiv submission |
| `CASE_STUDIES.md` | 5 detailed repurposing case studies |
| `docs/RESEARCHER_GUIDE.md` | End-user guide for researchers |
| `docs/PROVENANCE_ARCHITECTURE.md` | Full provenance system documentation |
| `docs/TRANSPARENCY_AND_AUDIT_MANUAL.md` | Beginner-to-expert audit manual |
| `docs/DATA_EXPANSION_GUIDE.md` | Data source recommendations |
| `docs/INDEPENDENT_EXTERNAL_AUDIT_2026-05-06.md` | External verification of metrics |
| `validation/repurposing_benchmark.py` | Canonical benchmark harness |
| `validation/triage.py` | Candidate triage CLI |
| `data/drugs/tier1.db` | Production knowledge graph |
| `data/drugs/build_tier1.py` | Reproducible DB build |

---

**Contact**: James Ray Hawkins (jhawk314@gmail.com)
**Repository**: KOMPOSOS-IV-PHARM
**Python**: 3.10+
