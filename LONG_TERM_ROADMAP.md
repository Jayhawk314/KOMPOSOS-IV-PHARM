# KOMPOSOS-IV-PHARM Long-Term Roadmap

**Working strategy, July 31, 2026. Revised July 31, 2026 after an independent technical audit.**

This document is a direction for PHARM, not a promise that every idea below will ship. It should be revised when experiments, users, or collaborators contradict it.

**Revision note.** An independent audit reproduced the benchmark, queried the database directly, and checked the licensing and regulatory claims against primary sources. Six corrections were accepted and are now folded into the text below: external precision is *undetermined*, not weak; AML is chosen for Beat AML rather than internal readiness; Phase 0 is an engineering phase, not a documentation phase; label completeness is a gate ahead of any precision claim; the minimum provenance schema moves into the first collaborator workflow; and combination research restarts from close to zero. Several measured numbers carried forward from earlier documents were also wrong and are corrected in place.

The source-of-truth order is:

1. executable code, tests, and dated result files;
2. `CLAUDE.md` and `HONEST_VALUE.md`;
3. this roadmap;
4. older plans and concept documents.

If an older document or a future demo makes a stronger claim than the sources above support, the stronger claim is not valid.

## Executive verdict

PHARM should grow from an oncology repurposing demo into a **collaborator-grade, evidence-bounded research workbench**. Its first job is not to recommend a treatment or interpret an entire patient genome. Its first job is:

> Reduce a cancer researcher’s candidate set to a reviewable shortlist while preserving the source, biological context, relation type, uncertainty, conflicts, and missing evidence behind every result.

The long-term patient-centered vision can remain. The disciplined route to it is:

1. make the existing prototype installable, reproducible, and factually accurate, and make its evaluation labels complete enough that a precision claim means something;
2. make the drug-target-disease triage trustworthy and usable on a collaborator's question, carrying a minimum provenance record from the first day;
3. extend that record into a full claim-and-provenance backbone strong enough to accept new evidence types;
4. add cohort and multi-gene context;
5. add drug combinations and toxicity evidence;
6. add tumor microenvironment and multi-omics context;
7. only then consider a secure, research-only patient case workspace based on established genomic standards;
8. treat clinical decision support as a separate future program requiring clinical, regulatory, security, and validation partners.

This route does not abandon the desire to help people with cancer. It is how the project avoids giving a medically important appearance to outputs that have not earned it.

## The north star

PHARM should help a human researcher answer four questions:

1. **Why did this candidate appear?**
2. **What kind of evidence supports or contradicts it?**
3. **What was not measured or could not be assessed?**
4. **What is the next experiment, source, or expert review needed to change its standing?**

PHARM should not claim to “show truth” in an absolute sense. A useful scientific system shows the state of a claim:

- `SUPPORTED_FOR_REVIEW`: relevant evidence supports inspection, not clinical use;
- `CONFLICTED`: material evidence points in different directions;
- `WEAK`: only indirect, low-tier, or context-mismatched evidence exists;
- `NOT_ASSESSED`: the required source or modality was unavailable;
- `OUT_OF_SCOPE`: the system is not built or validated for the question;
- `REFUSED`: a required provenance, context, or validation condition is missing.

Every result should say which of those states it is in and why. A numerical score without that standing is incomplete.

## What PHARM is now

As of the July 2026 integrity review, PHARM is an honest glass-box triage accelerator over known oncology pharmacology.

Its defensible strengths are:

- inspectable Drug -> Protein -> Disease paths;
- provenance and evidence tiers on graph edges;
- strong recovery of known labels within the small curated `core` cohort under direct-label removal;
- explicit abstention and coverage gaps;
- negative controls and ablations that have removed methods that did not help;
- an interface and CLI that can already show a ranked, cited research hypothesis.

The canonical strict `core` result is AUROC 0.9784, AUPRC 0.6128, and approximately +0.24 AUROC over the included common-neighbor baseline. Those numbers describe a 78-drug curated cohort and an internal graph-label recovery task. They are not a prospective discovery hit rate.

Three qualifications belong beside that number every time it is quoted:

- **The reported "Hits@k" is precision@k.** `validation/repurposing_benchmark.py` computes `hits / min(total_positives, k)`, which is why the run prints Hits@5 1.00 and Hits@10 0.70 — a true Hits@k cannot fall as k grows. Report it as precision@k or rename the metric.
- **603 of 1,560 pairs are abstentions scored 0.0 and are included in the AUROC.** Restricted to the 957 scored pairs the AUROC is **0.9642**; AUPRC is unchanged at 0.6128. Report the scored-only figure alongside the headline.
- **The terminal Protein -> Disease layer is smaller than earlier documents claimed.** On the default ESMC-excluded graph: **107** non-drug/non-disease nodes carry a disease edge, **783** terminal edges exist, of which **37 are directed (`driver_of`) across 28 sources** and the rest are `associated_with`. **1,206** drug-disease pairs are reachable through any complete path; only **138** are reachable through a directed terminal edge. That 138 is the true size of the mechanistically grounded surface.

On external performance, the honest statement is now:

> PHARM performs strong internal recovery on its curated graph. Its external precision is currently undetermined because external data, temporal provenance, and label completeness are inadequate.

This replaces the earlier claim that external precision is weak. The Hetionet inputs are absent from the repository (`data/external/` does not exist and is gitignored), the temporal holdout leaves post-cutoff literature in the graph and runs on the forbidden `all` cohort, and the negative set contains approved indications scored as false positives — Dacomitinib -> NSCLC, approved 2018-09-27, currently ranks first among the temporal holdout's "negatives." None of that proves precision is strong. It means the present evaluation cannot answer the question, and no precision claim in either direction should be made until it can.

Important negative findings are part of the product's scientific identity:

- ESMC similarity-transfer edges reduced performance and are excluded from default scoring.
- Post-hoc PubMed grounding did not show statistically reliable signal over scrambled pairings.
- Higher categorical machinery has not been shown to be uniquely responsible for the performance; classical typed path composition earns most of the measured value.

These results are not embarrassments. They are examples of the behavior PHARM should preserve: test a plausible idea, publish the boundary, and remove or downgrade what does not earn its claim.

## The first user and the first product

### First user

The first plausible user is a computational biologist, translational oncology researcher, pharmacology researcher, or scientific-ML builder with a real candidate-review problem.

The first user is not:

- a patient choosing treatment;
- a clinician expecting a validated decision-support product;
- a pharmaceutical procurement group buying an enterprise platform;
- a scientist expecting de novo molecule generation;
- someone asking PHARM to replace CIViC, OncoKB, Open Targets, DepMap, or a molecular tumor board.

### First product surface

The first product should be a **collaborator workbench**, not a larger public dashboard. It should accept:

- a disease or cancer subtype;
- a supplied list of drugs, targets, genes, or candidate relationships;
- an optional public cohort-derived gene or alteration table;
- a precise research question;

and return:

- a ranked but non-clinical shortlist;
- the few strongest evidence paths rather than every possible path;
- supporting and contradicting evidence kept separate;
- an evidence standing and coverage statement;
- a machine-readable and human-readable evidence bundle;
- explicit next checks that a researcher could perform.

The public Streamlit application can remain an explorer and demonstration. The collaborator workbench is where PHARM learns whether it solves a real workflow.

## Product architecture: four surfaces, introduced gradually

### 1. Public Explorer

The existing Streamlit surface demonstrates disease-first, drug-first, disease-specific, and pair-level inspection. It should remain safe for public data and clearly labeled research-only.

### 2. Collaborator Workbench

A focused workflow for a researcher to bring a candidate list or public cohort question. This is the adoption surface and should be prioritized over new speculative modules.

### 3. Evidence Bundle

A stable JSON plus Markdown/HTML representation of one claim or shortlist. The bundle should preserve identifiers, source versions, provenance, contexts, conflicts, missing fields, scorer version, and a reproducible input hash.

This may later become an interoperable receipt format, but it is not a standard until independent systems produce or consume it.

### 4. Secure Case Workspace

A possible later surface for de-identified research cases. It must not begin as a public upload box. It requires a threat model, explicit data lifecycle, access controls, provenance, deletion behavior, and partners who are qualified to assess genomic and clinical output.

## Non-negotiable design principles

### Evidence before breadth

No module is accepted because it sounds biologically relevant. It must serve a named user decision and be evaluated on data independent of its construction.

### Observed, curated, inferred, and generated are different things

PHARM must never flatten these into one confidence number:

- observed experimental or clinical result;
- expert-curated assertion;
- relation extracted from a source;
- graph-derived inference;
- model-generated hypothesis;
- absence of evidence;
- evidence of absence.

### Context belongs to the claim

A drug-response claim is incomplete without relevant context such as cancer type, subtype, model system, species, assay, dose, schedule, combination partner, treatment line, variant state, and source date. Missing context must be visible.

### Conflicts remain visible

Conflict must become a **first-class field on the claim**, not a by-product of a fusion rule.

State the current position plainly: **PHARM has no working conflict representation.** `oracle/evidence_combination.py` encodes every strategy as a simple support function — `m({exists}) = c`, `m(Theta) = 1 - c` — and never assigns mass to `not_exists`. Dempster conflict is therefore structurally zero for all inputs. Two maximally disagreeing strategies (0.9 and 0.1) combine to conflict `K = 0.0` and a pignistic score of **0.955**, higher than either input. The module docstring claims the opposite; it is wrong. `combine_predictions()` in the same file is dead code and raises `TypeError` on two separate lines. The strategy is not wired into the scored path, so no benchmark number is affected.

Do not describe Dempster-Shafer, or any other fusion rule, as summarizing disagreement until a representation exists that can encode evidence *against* a claim. Building that representation is Phase 2 work, not a caption on existing code.

### No magic composite score

Efficacy evidence, mechanism, toxicity, pharmacokinetics, evidence quality, and patient or cohort fit should first appear as separate dimensions. If a combined rank is later useful, its weights must be explicit and sensitivity-tested. A Pareto frontier or tiered filters may be more honest than one number.

### Missing means not assessed

Do not substitute convenient constants or invented defaults for missing expression, phenotype, assay, or structural data. Older patient-stratification code used placeholder values; those patterns must not migrate into PHARM.

Named, verified instances in the LAMBDA prototype that must never be reused as patient interpretation:

- `oracle/patient_stratification.py` returns `0.7` when a mutation is present but expression is unknown, `0.5` for any unknown subtype or missing response record, and substitutes a default of `5.0` log2 TPM for absent expression.
- `oracle/toxicity_assessment.py` is the more dangerous file and was previously unnamed here. It emits **dosing instructions** — `'CAUTION - high toxicity risk. Start with reduced doses.'` and `'SAFE - low toxicity risk. Standard dosing appropriate.'` — from an uncalibrated expression-ratio heuristic with hardcoded thresholds and empty default data dictionaries.
- `oracle/clinical_validation_pipeline.py` is on the same do-not-resurrect list.

**Hard rule: no PHARM output may contain dosing language.** Not "reduced dose," not "standard dosing," not "start low," in any module, at any phase, including Phase 6. This constraint does not depend on evidence quality; it is a boundary on the kind of statement PHARM is permitted to make at all.

### Category theory is conditional infrastructure

Typed composition is useful. Category theory may continue to guide design, but public scientific claims should use ordinary language and any claimed advantage must survive a matched ablation against a simpler implementation.

### The system never outranks a qualified human

PHARM can organize evidence and generate research hypotheses. It does not authorize treatment, dosing, trial enrollment, or discontinuation of care.

## The module admission gate: how PHARM resists bloat

Before implementation, every proposed module should answer all ten questions:

1. Who is the named user?
2. What decision or research task changes because of the output?
3. What independent data supports evaluation?
4. What is the simplest meaningful baseline?
5. What held-out, temporal, or external test will be used?
6. What output is allowed, and what wording is forbidden?
7. What does `NOT_ASSESSED` mean for this module?
8. What provenance, version, and licensing obligations follow the data?
9. What maintenance burden will the module create?
10. What result would cause the module to be removed, quarantined, or left experimental?

A feature that cannot answer these questions remains a research note. It does not enter the default scoring path or public product claim.

## Phase roadmap

The phases below use evidence gates, not promised dates. More than one research experiment may run at a time, but the default product should advance only when the prior gate is met.

### Phase 0: Make it installable, reproducible, and factually correct

**Purpose:** make the existing prototype understandable, installable, and reproducible before broadening it.

This is an **engineering and evidence-integrity phase, not a documentation phase.** Documentation cleanup alone cannot make PHARM externally usable. The phase has three tracks; the first is a hard blocker on the exit gate.

#### Track A — the repository must install and run from a clean clone

Verified defects, all of which currently break the exit gate:

- `pyproject.toml` declares `build-backend = "setuptools.backends._legacy:_Backend"`. **That module does not exist in any version of setuptools**; a build fails immediately with `ModuleNotFoundError: No module named 'setuptools.backends'`.
- `[tool.setuptools.packages.find]` sets `include = ["core*"]`, so even a successful build would ship only `core/` — not `oracle`, `validation`, `data`, or `komposos_kg`.
- `requirements.txt` is four lines and omits `scipy`, `scikit-learn`, and `pytest`.
- There is no continuous integration of any kind (`.github/` is absent), so nothing detects the above.
- `data/external/` is absent and gitignored, so `validation/external_validation.py` raises `FileNotFoundError` for anyone who clones the repository.

This track is a **separate engineering change**, sequenced after the factual document corrections and after the first reviewer exercise (see "What to build next"). It should not be interleaved with scientific work.

#### Track B — quarantine, do not delete

Research files retain historical and dependency value. The policy is **explicit quarantine first; deletion or archival only after a dependency and historical-value review.** A quarantined file must carry a header stating that it is non-product, excluded from validation, and not permitted to support any claim; it must be excluded from the default scored path and from every public surface; and it must be listed here.

Currently quarantined:

- `validation/spatial_biology_metrics.py` — returns hardcoded placeholder L-R metrics (`0.65 / 0.45 / 0.30`), hardcoded baselines (`0.62 / 0.68`), and a TDA "overlap" that is a non-empty-list check. Imported by no module.
- `spatial_biology/generate_validation_data.py` — generates synthetic spatial data and asserts it is "better than public datasets for validation because we KNOW the answer," seeding tumor cores with the high curvature the method is meant to discover. **Circular by construction**, and a more serious hazard than the placeholder metrics file because its output looks like a result.
- `scripts/mutation_impact.py` — tracked in this repository, not external legacy. Reconstructs 3D coordinates by MDS over a fabricated distance matrix (contact = 7 A, non-contact = 15 A) with a random-normal fallback, then prints `kcal/mol`. Pseudo-coordinates cannot support physical-energy claims.
- `oracle/evidence_combination.py` — see "Conflicts remain visible."
- `oracle/score_combination.py` — hand-set "reasonable defaults" for the logistic coefficients, **and** hand-set blend weights (0.3/0.7, 0.7/0.3) and a hand-set variance-to-agreement map. Outputs are not learned calibration.

Not quarantined, and correctly written: `oracle/explain_combination.py` states that its combination results are directional hypotheses, not potency or patient-response predictions.

#### Track C — factual and evidence integrity

- correct the measured numbers in `CLAUDE.md` and `HONEST_VALUE.md` (terminal-hop counts, reachable pairs, stale AUPRC);
- correct `README.md`, which describes the Hetionet result as executable when it is not, and `docs_current/VALIDATION.md`, which still displays the retired AUROC 0.970549;
- keep the `core` and `all` cohorts visibly separate;
- report score coverage, abstentions, and the scored-only AUROC beside performance;
- restore or retire the external evaluation path, and rebuild the temporal holdout on the `core` cohort with a design that does not leave post-cutoff literature in the graph;
- make one compact evidence view: three strongest paths, conflicting evidence, missing evidence, and standing;
- audit displayed citations so a retrieved PMID is not visually confused with a validated relation;
- record that the disease set is not purely oncological — it contains `Type2_Diabetes` and `Li_Fraumeni_Syndrome`, and `Metformin -> Type2_Diabetes` is one of the 44 positives — and that **6 of the 20 diseases carry zero positives**, so disease-specific performance is undefined for 30% of the graph.

**Exit gate:** a technically skeptical stranger can clone the repository, install it, reproduce the bounded result, inspect one evidence bundle, and understand every major limitation without reading 133 documents. Until the packaging defects in Track A are fixed, this gate is unreachable by construction.

### Phase 0.5: Label completeness

**Purpose:** make precision measurable at all. This is a gate, not a task.

Every Phase 1 evaluation metric — proportion of top claims judged relevant, candidates safely removed, citation-to-assertion precision — is uninterpretable while the negative set contains approved indications. The temporal holdout's top-ranked "negatives" include Dacomitinib, Lorlatinib, Brigatinib and Amivantamab in NSCLC and Avapritinib in GIST, all approved.

Work:

- build a versioned, dated evaluation label set from Drugs@FDA oncology approvals plus registered active trials, covering **every drug in the cohort**, not only the 78 curated ones;
- record, per pair, whether it is approved, in trial, preclinically supported, unknown, or a screened negative — an unlabeled pair is *unknown*, never a confirmed negative;
- version the label set independently of the graph, so a scoring change and a label change are never confounded;
- re-derive AUPRC, precision at reviewable `k`, and the external and temporal results against it.

**Exit gate:** a precision statement about PHARM can be made in either direction and defended. Until then, no claim about external precision — strong or weak — enters any document or conversation.

### Phase 1: Collaborator-grade custom triage

**Purpose:** move from “James can demo it” to “another researcher can bring a question.”

Work:

- **ship the minimum provenance schema here, not in Phase 2.** The evidence bundle cannot be built without it, and retrofitting provenance onto a finished workbench produces two incompatible schemas and a migration. The minimum record is: subject, predicate, object; disease and model-system context; source identifier, source version, source date, and exact support location; whether the support is independent of the hypothesis-generation path; and a content hash. The full claim model in Phase 2 extends this record; it does not replace it;
- accept user-supplied candidate drug, protein, gene, and disease identifiers;
- normalize identifiers against stable authorities (UNII or ChEMBL ID for drugs, HGNC ID for genes) and record unresolved mappings instead of guessing. Two failure modes are already documented and must be fixed here: salt-form duplication, where "Dacomitinib" and "Dacomitinib Anhydrous" occupy separate ranks with identical scores, and gene-symbol sense collision, where `AR` grounded on a sentence about the beta-2 adrenergic receptor;
- define a compact research-question schema;
- produce JSON, CSV, and readable evidence bundles;
- expose source versions and reproducibility hashes;
- build a reviewer annotation store — accept, reject, comment, mark irrelevant — with persistence. Reviewer-agreement metrics are undefined without it;
- add a comparison view against a simple baseline and an established resource such as Open Targets where appropriate;
- support a local/offline run on public or collaborator-approved data. Note that `validation/nonobvious.py` calls NCBI E-utilities live and must send the `tool` and `email` parameters NCBI's usage policy requires.

Evaluation:

- time required to reach a reviewable shortlist;
- proportion of top claims judged relevant by a domain reviewer;
- precision of citation-to-assertion support under manual audit;
- reviewer agreement and reasons for disagreement;
- how many candidates are safely removed, not merely re-ranked;
- how often the same user returns with another question.

**Exit gate:** at least two external domain reviewers use PHARM on real or public research questions, and at least one asks to repeat the workflow. Compliments, stars, and demo traffic do not satisfy this gate.

### Phase 2: Claim and provenance backbone

**Purpose:** build the evidence substrate required for every later biological module.

Each claim should carry, where applicable:

- subject, predicate, object;
- **relation sign and therapeutic direction as two separate fields.** CIViC separates evidence direction ("supports" / "does not support") from clinical significance ("sensitivity" / "resistance"); collapsing them into one "direction and sign" makes resistance evidence unrepresentable;
- **variant-level identity**: GA4GH VRS identifier, HGVS, transcript and reference build, variant class, and a Cat-VRS categorical variant where the claim is about a class. Without this the model can express "erlotinib - EGFR - NSCLC" but not "EGFR exon 19 deletion," which is the level real precision-oncology evidence is written at;
- **whether the gene is the target, the biomarker, or neither** in this claim;
- disease, subtype, species, tissue, cell line, cohort, and assay context;
- **model-system fidelity as a field distinct from species**: patient, PDX, organoid, primary specimen, or immortalized line;
- drug, dose, schedule, route, combination context, and **line of therapy / prior-treatment state**;
- **endpoint type and effect size with units**: IC50, GI50, ex vivo AUC, ORR, PFS, OS; the value, its confidence interval, and the comparator arm. The roadmap previously specified sample size and evidence level but never the number itself. This is exactly what the empty `quantitative_value` and `sample_size` columns were for — both currently read NULL for all 2,439 edges;
- source identifier, source version, source date, and exact support location;
- **retraction and erratum status** on every cited PMID;
- study type, sample size, evidence level, and curation status;
- **negative and null results as first-class claims.** A failed trial is evidence. Nothing in the current graph can represent one;
- **a provenance chain rather than an independence boolean.** Two sources that appear independent often trace to the same primary; only the chain reveals it;
- contradiction or resistance evidence;
- **claim lifecycle**: stable claim identifier, `valid_from`, `valid_to`, and `superseded_by`. Source version alone does not let a claim be retired;
- **curator identity and recorded disagreement**, without which Phase 1's reviewer-agreement metric has nowhere to live;
- license and redistribution restrictions;
- extraction method, reviewer status, software version, and content hash.

Contradiction detection also needs a **data source**, which PHARM does not have. Nothing currently in the graph records a negative or failed result. The candidates are CIViC "does not support" evidence and terminated or negative ClinicalTrials.gov records; one of them must be ingested before "contradiction detection rate" is a measurable quantity rather than an aspiration.

Candidate sources should be added only after license and use review. CIViC is especially compatible with PHARM's goals because it exposes a structured, public-domain evidence model with evidence direction, significance, level, source, disease, and therapy. OncoKB is valuable for comparison and licensed research use, but its programmatic, commercial, clinical, and model-training terms must be respected. Open Targets is a useful comparator and upstream evidence source; PHARM should not pretend to replace its broad target-disease integration.

This phase should also create an explicit evidence hierarchy:

- regulatory/guideline or validated clinical association;
- clinical evidence;
- case evidence;
- preclinical evidence;
- inferential evidence;
- generated hypothesis.

The hierarchy should not imply that all claims in a tier are equally reliable. It gives the reviewer a starting point.

**Exit gate:** PHARM can reconstruct why a claim was shown, with which data version and context, and can distinguish support, contradiction, inference, and missing assessment without relying on a prose explanation from the developer.

### Phase 3: Multi-gene and cohort context

**Purpose:** move beyond one drug-one target-one disease while remaining in public, retrospective research.

This is a higher priority than full genome upload because cancers are shaped by interacting alterations and pathway states, but a raw genome adds enormous interpretation and governance burdens.

Start with one disease, and that disease should be AML — but the earlier rationale was wrong and is corrected here.

> AML is intentionally chosen despite weak internal graph support because Beat AML offers an external, specimen-level genomics and ex vivo response benchmark. Success there would be more meaningful than recovering PHARM's existing AML knowledge.

The internal picture is the opposite of a head start. **AML has zero `treats` positives in the graph** — not one of the 44 FDA labels is an AML indication. Only two proteins, FLT3 and TOP2A, reach AML through a directed edge; every other terminal hop to AML is `associated_with`. What PHARM "already contains" is `data/proteins/aml_proteins.py`, roughly 50 hand-typed protein entries with string literals such as `"mutation_freq": "30%"` and no per-entry citation or version. It provides concepts, not evidence, and no internal label to validate against.

The reason to choose AML is therefore entirely external. **Beat AML 2.0** pairs per-patient genomics with per-patient *ex vivo* drug sensitivity at a scale no other public oncology cohort matches: 805 patients and 942 specimens, with inhibitor AUC values, WES and targeted mutation calls, normalized expression, and clinical annotation. The processed tiers are openly downloadable under CC-BY-4.0; raw FASTQ is controlled-access through GDC/dbGaP and is neither needed nor to be ingested.

TCGA-LAML remains useful as a secondary source for cytogenetics and methylation, but it must not be the primary dataset: **it carries no drug-response data**, so an experiment built on it would be forced back onto internal `treats` labels, of which AML has none.

Capabilities:

- ingest a curated gene set or alteration table, not an unrestricted genome;
- distinguish somatic variant, copy-number alteration, fusion, expression change, methylation, and cytogenetic event;
- reason over pathways, complexes, signed regulation, co-mutation, mutual exclusivity, and known synthetic-lethal relationships;
- compare a cohort or subgroup with a defined reference group;
- show which alterations have independent evidence and which are graph compositions;
- report subgroup sample size and missingness;
- preserve disease and tissue context;
- use DepMap dependencies as cell-line evidence, not as patient efficacy evidence.

Evaluation:

- pre-specified public AML questions;
- conventional statistical or knowledge-graph baselines;
- held-out cohorts where available;
- pathway and gene-set permutation controls;
- **a degree-preserving rewiring null.** Common-neighbor and degree-product are feature baselines, not null models. A configuration-model rewiring answers the question the hub-drug bias actually raises: would a random graph with this degree sequence compose these paths anyway? This is the direct methodological transfer from KOMPOSOS-evolve, whose drift-excess and PTP randomization tests are the strongest null-model apparatus in the portfolio;
- stability under identifier and cohort changes;
- domain review of top multi-gene explanations.

#### The first AML experiment, pre-specified

**Question.** In retrospective AML specimens, does adding the specimen's mutation context to PHARM's curated drug-protein evidence improve the ranking of *ex vivo*-sensitive inhibitors for that specimen, relative to a specimen-independent baseline?

This deliberately replaces the earlier copy-number/fusion question, which had no label source because AML has no internal positives.

**Dataset.** Beat AML 2.0 processed tiers (CC-BY-4.0): inhibitor AUC, WES/targeted mutation calls, normalized expression, clinical annotation.

**Inputs.** Per specimen, the mutated-gene set restricted to genes present in `tier1.db`. Per drug, PHARM's Drug -> Protein edges for the subset of Beat AML inhibitors resolvable to ChEMBL identifiers. Expect substantial mapping loss; report it rather than silently dropping.

**Labels.** Per (specimen, inhibitor): sensitive = AUC in the bottom quartile **of that inhibitor's own distribution across specimens**. Per-drug standardization is non-negotiable — without it the task degenerates into "which drugs are generally potent" and any model will look excellent.

**Baselines.** (1) Drug-mean sensitivity, specimen-independent — this is the one to beat and it is genuinely strong in *ex vivo* screens. (2) "Does the drug target a mutated gene," a single boolean. (3) Common-neighbor on the PHARM graph. (4) Degree-preserving rewiring null.

**Splits.** By **patient**, never by specimen; repeat specimens exist. External test: hold out one Beat AML wave entirely, giving a genuine batch and temporal shift.

**Success.** Mean per-specimen AUPRC or NDCG@10 beats baseline 1, with a patient-level bootstrap CI excluding zero, and the gain keeps its sign on the held-out wave.

**Failure, pre-declared.** No gain over drug-mean. This is the most likely outcome and will be published. A second pre-declared failure mode: a gain over baseline 1 that vanishes under baseline 2, which would mean the graph added nothing over a one-line boolean.

**Allowed claim.** "Adding specimen mutation context to a curated pharmacology graph did or did not improve *ex vivo* inhibitor prioritization in retrospective AML specimens, on patient-held-out and wave-held-out splits."

**Forbidden wording.** Response prediction, patient benefit, treatment selection, therapy recommendation, or "would have helped this patient." *Ex vivo* AUC is not clinical response. The principle that DepMap is cell-line evidence and never patient efficacy applies here with equal force.

Avoid immediately forcing all modalities into one graph score. Use late fusion first: separate evidence panels whose agreement and conflicts are visible.

**Exit gate:** PHARM improves a real cohort-level candidate-review task over a transparent baseline and retains its gain on data not used to create the relations.

### Phase 4: Drug combinations, interactions, and toxicity evidence

**Purpose:** evaluate combinations without pretending that pathway logic predicts safe or effective regimens.

**Treat combination research as starting from close to zero.** The existing code is conceptual scaffolding, not validated combination prediction, and three facts about it were previously omitted here:

- It runs on a **different graph entirely** — `data/omnipath_signed.tsv`, an 85,000-row OmniPath signed causal network — not on `tier1.db`. Nothing connects the two substrates, so no combination result inherits any of PHARM's measured performance.
- Its "8/8 validated for direction" is **eight author-chosen perturbations whose expected signs are written by the author in the same file**, against an unsigned baseline that provably cannot represent inhibition. That is a sanity check, not a validation.
- Its **only labeled external test scores below chance**: AUROC 0.36 against the CEGv2/NEGv1 essentiality standard. The source file states this honestly; this roadmap previously did not.

What *is* worth preserving is the honesty of the framing: `oracle/explain_combination.py` separates exact additive behavior in a linear model from a non-linear conduit-ablation hypothesis and states plainly that the output is directional, not calibrated potency. Keep that discipline and rebuild the substance on dose-matrix screen data.

Build three separate layers:

#### A. Combination efficacy evidence

- known clinical or guideline-supported combinations;
- clinical-trial evidence;
- preclinical combination screens such as NCI-ALMANAC or NCATS matrix screens;
- model-specific synergy measurements with the metric, dose matrix, schedule, and cell line preserved;
- PHARM-generated mechanistic or structural hypotheses, clearly lowest in standing.

Synergy is not a property of two drug names alone. It depends on dose, response model, timing, assay, and biological context. Different synergy metrics can disagree. Never label an uncalibrated graph interaction “synergistic treatment.”

#### B. Pharmacokinetic and known drug-drug interactions

- FDA labeling and documented CYP/transporter roles;
- substrate, inhibitor, and inducer strength;
- direction of exposure change;
- known contraindications and warnings;
- evidence source and date.

Licensed resources such as the University of Washington Drug Interaction Database may be appropriate in a partnership, but their data cannot simply be copied into an open repository.

**Defer this sub-layer.** Efficacy evidence (A) and toxicity evidence (C) share PHARM's substrate; pharmacokinetic DDI does not. It is a curated lookup table over CYP and transporter roles, with a permanent maintenance tail and a licensed best-in-class source. It is a different product and should not be built on the critical path.

#### C. Toxicity and safety signals

- regulatory labels and boxed warnings;
- organ and mechanism-specific known toxicities;
- overlapping toxicity evidence for a combination;
- preclinical safety or ADMET evidence, separately labeled;
- spontaneous adverse-event reports only as safety signals.

FDA FAERS/openFDA reports cannot establish causality or incidence and often contain multiple drugs and reactions. PHARM must never transform report counts into a patient risk probability.

Two additional constraints on this layer:

- **Disproportionality statistics are also excluded**, not only raw counts. PRR, ROR and EBGM are signal-detection tools that read as risk to non-specialists; publishing them would recreate exactly the misreading the count prohibition is meant to prevent.
- **Name the adverse-event vocabulary now, because it constrains what is buildable.** Use CTCAE terms, which are freely usable, and avoid MedDRA, which is subscription-licensed. An "overlapping toxicity" feature that assumes MedDRA will be blocked at implementation time.

The dosing-language prohibition in "Missing means not assessed" governs this entire layer.

Output should be a multi-dimensional card, for example:

- mechanistic support;
- combination-screen support;
- clinical evidence;
- pharmacokinetic interaction concern;
- overlapping toxicity concern;
- context match;
- evidence completeness;
- standing and reasons for refusal.

**Exit gate:** on a retrospective, versioned combination benchmark, PHARM adds useful prioritization over single-drug and simple network baselines, and a pharmacology-qualified reviewer agrees that its evidence cards do not overstate safety or efficacy.

### Phase 5: Tumor context, inflammation, and multi-omics

**Purpose:** model the environment in which a candidate might matter, instead of treating a tumor as a gene list.

“Inflammation” should not become a single universal score. Reframe it as tumor-microenvironment context:

- immune and stromal cell composition;
- cytokine and chemokine signaling;
- ligand-receptor interactions;
- pathway activity;
- tumor purity and clonal composition;
- immune evasion or exhaustion evidence;
- spatial neighborhood and temporal state where measured.

Modalities can include:

- mutation and structural variation;
- copy number;
- RNA expression;
- protein abundance and phosphoproteomics;
- epigenetic measurements;
- single-cell expression;
- spatial transcriptomics or imaging-derived cell neighborhoods.

The NCI GDC, Proteomic Data Commons/CPTAC, and Human Tumor Atlas Network provide relevant public resources. Each modality has different samples, measurement errors, access conditions, and missingness. An unmeasured modality must produce `NOT_ASSESSED`, not a neutral default.

Be honest about the size of this phase. It is not a module; it is a new data layer plus new assay expertise. PHARM currently contains **one cytokine-adjacent node (IL6)** and no immune-cell composition data of any kind. Two dependencies must be named before any of it is scheduled: cell-type deconvolution tooling such as CIBERSORTx is free for academic use with registration but is **not redistributable**, and ligand-receptor "interaction" calls derived from spatial data are high-false-discovery hypothesis generators, not measurements.

PHARM's current spatial validation code is not ready for this phase, and the reason is worse than placeholders. `validation/spatial_biology_metrics.py` returns hardcoded metrics and simplified overlap checks; more seriously, `spatial_biology/generate_validation_data.py` **generates synthetic data seeded with the very pattern the method is supposed to discover** and describes this as better than public datasets "because we KNOW the answer." Both are quarantined under Phase 0 Track B. Any result produced by the second file is circular and cannot be cited.

Start by reproducing one published public spatial or proteogenomic task with classical baselines. Only then test whether PHARM's typed composition, geometry, or topology adds anything.

**Exit gate:** one pre-specified multi-omic or tumor-microenvironment task shows stable value on independent samples and has been reviewed by someone who works with the underlying assay.

### Phase 6: Research-only patient case workspace

**Purpose:** allow a qualified collaborator to inspect how public evidence relates to a de-identified case without producing a treatment recommendation.

This phase should begin with a **schema and local sandbox**, not a scoring feature.

Use established representations:

- GA4GH Phenopackets for phenotype and clinical context;
- GA4GH VRS/Cat-VRS for precise variation representation;
- HL7 FHIR Genomics Reporting patterns for linking patient, specimen, study, findings, and therapeutic implications.

Initial input should be a de-identified, already-processed somatic alteration table, MAF, or carefully constrained VCF plus specimen and assay metadata. Do not begin with FASTQ, BAM, consumer germline files, or unrestricted whole-genome upload. Raw sequencing interpretation requires variant calling, quality control, reference-build handling, germline/somatic separation, tumor purity, clonality, coverage and detection limits, structural variation, and clinical-grade validation that PHARM does not provide.

Minimum case metadata:

- research pseudonym, consent/use status, and data origin;
- cancer type, subtype, disease state, and specimen site;
- collection time and relation to treatment;
- tumor/normal status and tumor purity where known;
- assay, laboratory, panel, reference genome, pipeline, and quality metrics;
- somatic variants, fusions, copy-number and structural events;
- prior therapies and known resistance context;
- phenotype and performance-status fields only when legitimately sourced;
- missing fields and their effect on assessment.

Minimum safeguards:

- local-only or institution-controlled deployment;
- **storage disabled by default**, not merely "no retention by default" — and deletion behavior proved by a test, not asserted. Note that a Streamlit file uploader buffers to the server even when nothing is persisted, so the upload surface exists whether or not retention does;
- encryption in transit and at rest where storage is enabled;
- access log and deletion confirmation;
- no hidden third-party model or analytics transmission, and platform usage statistics explicitly disabled;
- explicit controlled-data and licensing review;
- threat model and incident plan;
- clinical genomicist, oncologist, privacy/security, and IRB or equivalent governance involvement before real patient data is used.

Three constraints that the cited policies imply but that must be stated operationally:

- **HIPAA Safe Harbor does not de-identify a genome.** Its eighteen identifiers do not include sequence, yet germline sequence is inherently re-identifiable. Citing the HHS de-identification guidance without this caveat would imply a protection that does not exist.
- **Controlled-access tiers cannot be placed in this repository or in any hosted deployment.** This is the operational consequence of the NIH Genomic Data Sharing policy and dbGaP Data Use Certification, and it applies to the controlled tiers of both TCGA and Beat AML. Only the open, processed tiers are usable here.
- **State genetic-privacy statutes** must be added to the licensing and governance review; they are not preempted by HIPAA and several impose consent and deletion duties beyond it.

Output must be called a **research evidence dossier**, not a treatment plan. It can state that a case feature matches, conflicts with, or falls outside public evidence. It should route findings to qualified review and preserve all reasons for abstention.

The older LAMBDA patient profile is useful as a list of possible concepts - mutations, expression, AML subtype, prior therapies, resistance, cytogenetics, age, and performance status - but its heuristic scores and placeholder defaults must not be reused as patient interpretation.

**Exit gate:** a governed, de-identified retrospective case study is reviewed by qualified partners, all data handling is approved, and the dossier is shown to be accurate as an evidence summary. This still does not make PHARM clinical decision support.

### Phase 7: Optional clinical translation program

**Purpose:** define the additional work required if a clinical partner eventually wants to use PHARM in care.

This is not simply another feature phase. It would require a distinct intended use, risk analysis, quality system, software lifecycle controls, cybersecurity, human-factors testing, analytical and clinical validation, change control, post-deployment monitoring, and regulatory assessment.

FDA's current Clinical Decision Support Software final guidance was issued January 6, 2026 and re-issued January 29, 2026, replacing the September 28, 2022 version. Three details matter and correct an earlier summary here:

- The exclusion of **patient- and caregiver-directed** software from the non-device CDS criteria is **statutory** — section 520(o)(1)(E) requires a health care professional — not something this guidance introduced. The January 2026 revision did not address patient- or consumer-facing CDS at all.
- FDA **relaxed** the earlier position on **singular recommendations**, extending enforcement discretion to tools offering a single recommendation where clinically appropriate. The prior framing here implied the opposite.
- The **time-critical** limitation moved from Criterion 3 to Criterion 4, on the reasoning that a clinician cannot independently review a recommendation under time pressure.

Do not paraphrase this guidance from memory in any public claim; read the current version at the time of the claim.

Do not enter this phase solo. It needs an oncology institution, qualified clinical investigators, regulatory counsel, security expertise, representative data, and prospective evaluation. A separate repository or controlled product boundary may be appropriate so open research experimentation cannot silently alter a clinical system.

**Exit gate:** defined jointly with clinical and regulatory partners, not by this roadmap.

## Decisions on the proposed ideas

| Idea | Decision | Placement | Reason |
|---|---|---|---|
| Patient profile | Yes, cautiously | Schema concepts in Phase 3; case workspace in Phase 6 | Context matters, but old scores are heuristic and not validated. |
| Genome upload and interpretation | Conditional, much later | Phase 6, processed somatic data first | Raw genomes create interpretation, privacy, quality, and regulatory burdens far beyond current PHARM. |
| Multi-drug interaction | Yes, from near zero | Phase 4A | Aligned, but the existing code is scaffolding on a separate graph whose only labeled test is AUROC 0.36. |
| Pharmacokinetic DDI layer | Defer | Off critical path | A curated lookup table with a permanent maintenance tail and a licensed best source. Different product. |
| Toxicity | Yes, evidence-first | Phase 4 | Show labels, known mechanisms, interaction concerns, and signals; do not predict personal safety. |
| Multi-gene relationships | Yes, high priority | Phase 3 | More scientifically realistic and reachable with public cohort data. AML chosen for Beat AML, not for internal readiness. |
| Label completeness | Yes, gate | Phase 0.5 | Without it no precision statement, in either direction, is defensible. |
| Retained higher-categorical packages | Archive | Phase 0 Track B review | `hott/`, `cubical/`, `topology/`, `geometry/`, `game/`, `foundation/`, `cog/`, `zfc/` carry zero measured contribution and permanent test-maintenance cost. Quarantine and review; do not delete on sight. |
| Portfolio integrations (haloa, nlock, SirNlock, Noesi) | No, for now | Not scheduled | Pure surface area against no current user need. |
| “Chromosomal collapse” | Reframe | Research track after Phase 3 | Use established phenomena: chromosomal instability, aneuploidy, CNV, structural variation, whole-genome doubling, chromothripsis, and ecDNA. |
| Inflammation and cancer | Yes, as context | Phase 5 | Model immune/stromal pathways and measured tumor microenvironment, not a vague inflammation score. |
| AlphaFold/Boltz/ESM interpretation | Conditional evidence annotation | Structural research track | Useful only when structural quality and a benchmark add value beyond graph pharmacology. |
| Category theory | Keep as conditional design language | Across phases | Typed composition is useful; unique empirical advantage is unproven. |
| De novo drug design | Separate Track B | Not on the present critical path | Different data, validation, chemistry, and users; do not blur repurposing with molecule generation. |
| Direct patient treatment advice | No | Out of scope | It would outrun the evidence and create unacceptable risk. |

## Research track: chromosomal instability, not “chromosomal collapse”

The original phrase points toward a real and important family of cancer phenomena, but it is too ambiguous for a module name or claim. Separate at least:

- aneuploidy and chromosome-arm gains/losses;
- focal copy-number amplifications and deletions;
- structural variants and fusions;
- chromothripsis/chromoplexy;
- whole-genome doubling;
- extrachromosomal DNA;
- homologous-recombination deficiency and other genome-instability processes.

An honest first experiment could ask a bounded question such as:

> Does adding versioned copy-number and karyotype context improve *ex vivo* inhibitor prioritization in Beat AML specimens, over mutation-plus-pathway evidence, on a patient-held-out split?

That is testable. “Chromosomal collapse predicts healing” is not. Note the retargeting: the earlier version of this question used "AML candidate prioritization on a held-out cohort," which has no label source, because AML carries no internal positives. Beat AML supplies the labels.

Possible inputs include GDC CNV/SV data and published PCAWG-derived events. One caveat on scope: **ecDNA does not sit at the same level of accessibility as the other phenomena in this list.** Detecting it requires whole-genome-based tooling of the AmpliconArchitect class; GDC's harmonized masked copy-number output will not support it. Listing ecDNA beside arm-level aneuploidy implies a parity of effort that does not exist.

Outputs should be alteration and pathway context, not a single collapse score. If a future composite instability measure is used, PHARM should name its components and validate it independently.

## Research track: structural biology

Protein models should enter PHARM as evidence objects, not authority.

Useful bounded questions include:

- Is a variant near a known binding pocket or interface?
- Is the relevant region structured with adequate confidence?
- Does an experimental or predicted structure contradict a proposed interaction geometry?
- Does a structure-derived feature improve held-out ranking beyond graph degree, known targets, and sequence similarity?

Required metadata includes model source/version, sequence, structure identifier, experimental versus predicted status, per-residue confidence, PAE where available, ligand state, chain mapping, and unresolved residues.

Do not reuse the older pseudo-coordinate mutation-energy pipeline. Pseudo positions or randomly initialized coordinates cannot support kcal/mol or physical-stability claims. Do not repeat the ESMC mistake by transferring disease evidence through similarity without a pre-specified external test.

## Research track: combinations and resistance evolution

The strongest combination story may eventually connect:

- an oncogenic dependency;
- a compensatory survival route;
- a drug pair that targets both;
- evidence from dose-matrix screens;
- toxicity and pharmacokinetic constraints;
- known or emerging resistance mechanisms.

KOMPOSOS-evolve's most useful transfer is methodological: null models, negative controls, and willingness to publish a failed biological analogy. Convergent evolution may help frame repeated resistance mechanisms only when longitudinal tumor or model-system data actually supports that analysis. It should not be added as a metaphorical score.

## What to build next - the narrow sequence

The next work after event preparation is these seven items, in this order:

1. **Correct the factual documents.** This roadmap, `CLAUDE.md`, `HONEST_VALUE.md`, `README.md`, and `docs_current/VALIDATION.md`. Cheapest possible step and everything downstream cites them.
2. **Run the 50-pair human evidence and label-completeness audit.** See below. This is the single most important next scientific step.
3. **Determine whether researchers find the evidence bundles useful**, by revising once from the reviewer's objections and rerunning the same 50 pairs.
4. **Repair packaging and establish a clean-clone test**, as a separate engineering change not interleaved with scientific work.
5. **Construct the complete, versioned evaluation label set** (Phase 0.5).
6. **Only then design the Beat AML experiment.**
7. **Defer combinations, toxicity, multi-omics, and patient cases** until those gates pass.

Do not implement patient uploads, spatial topology, genomic instability scoring, or a broad toxicity predictor before these items. Their dependencies are the evidence backbone, a defensible label set, and external human feedback — not more scaffolding.

### The 50-pair reviewer exercise

This is item 2 and it deserves its own specification, because it simultaneously tests three things no module can test: whether the citations support the claims, whether the apparent false positives are merely missing labels, and whether a real researcher values PHARM's evidence presentation.

Budget **90 minutes of the collaborator's time in total.** Anything longer will not earn a second session.

1. **Pre-work.** Choose one disease with real label density — Melanoma or NSCLC, nine positives each. Freeze the graph, scorer version, and a content hash. Produce the top 50 ranked pairs.
2. **Send one page, not a repository.** For each pair: score, the three strongest paths, per-edge tier and PMID, and an explicit "what is missing" line. One framing sentence: *"I am not asking whether these are good drugs. I am asking whether the evidence shown is what you would need to reject them quickly."*
3. **Task one, 45 minutes.** For each pair the reviewer assigns one code: **A** approved indication I failed to label · **B** in active clinical trial · **C** published preclinical rationale · **D** plausible but undocumented · **E** wrong, or the cited evidence does not support the edge.
4. **Task two, 20 minutes.** For ten pairs, blind: does the cited sentence actually support the stated relation — yes, partially, or no? This is the citation-to-assertion precision number.
5. **Debrief, 25 minutes**, recording objections verbatim and defending nothing. One question: *"What would have to be on this page for you to spend an afternoon on the D-list?"*

Codes A and B measure the label-completeness gap directly and feed Phase 0.5. Code E measures evidence integrity. Nothing here requires the workbench, the backbone, or any new data.

Do **not** open with the Streamlit application. A single pair currently emits 86 chains, which spends the reviewer's attention on the wrong thing.

## Evaluation system

PHARM needs a scorecard larger than AUROC but smaller than a marketing dashboard.

### Scientific performance

- AUPRC and precision at a reviewable `k`;
- recall/enrichment at a fixed review budget;
- calibration where probabilities are claimed;
- coverage and abstention rate;
- temporal and external performance;
- subgroup and disease-specific performance;
- margin over degree, common-neighbor, path-count, and domain-relevant baselines;
- ablation of every added modality.

### Evidence integrity

- citation-to-assertion precision under blind manual review;
- proportion of claims with exact context and source version;
- contradiction detection rate;
- reviewer agreement;
- identifier mapping error rate;
- independent versus post-hoc support;
- reproducibility from an evidence bundle.

### Workflow value

- time to shortlist;
- number and fraction of candidates eliminated safely;
- reviewer effort per accepted or rejected hypothesis;
- whether the output changed the next experiment or search;
- repeat use by the same collaborator.

### Safety and governance

- inappropriate clinical-language rate;
- sensitive-data incidents;
- unlogged external transmissions;
- false certainty when a modality is missing;
- refusal correctness;
- removal/deletion verification for governed case data.

### Adoption

- independent installations or runs;
- external datasets successfully processed;
- repeat users;
- substantive issues, reviews, or contributions;
- collaborators willing to inspect another result.

Stars, page views, and event compliments are secondary. They do not validate a scientific workflow.

## Data-source strategy

PHARM should be an evidence integrator with strong boundaries, not a smaller copy of every existing platform.

Use sources according to their role:

- **ChEMBL/FDA labels:** drug-target and regulatory evidence;
- **CIViC:** openly structured cancer-variant evidence and an evidence-model example;
- **OncoKB:** valuable curated comparison/annotation subject to licensing and use restrictions;
- **Open Targets:** target-disease evidence and broad prioritization comparator;
- **GDC/TCGA:** harmonized cohort genomics, expression, CNV/SV, and clinical context — but no drug response;
- **Beat AML 2.0:** the only public oncology resource pairing per-patient genomics with per-patient *ex vivo* drug sensitivity at scale. 805 patients, 942 specimens; processed tiers CC-BY-4.0 and openly downloadable; raw sequence controlled-access via GDC/dbGaP and out of scope. This is the Phase 3 primary dataset;
- **DepMap:** cancer cell-line dependencies and compound sensitivity, never direct patient response;
- **NCI-ALMANAC/NCATS screens:** preclinical combination data with dose and model context;
- **PDC/CPTAC:** proteomics and phosphoproteomics;
- **HTAN:** single-cell, spatial, temporal, and tumor-microenvironment research;
- **openFDA/FAERS:** safety signal exploration with explicit non-causality limitations;
- **Phenopackets/VRS/FHIR Genomics:** interoperability schemas for a later governed case workspace.

Before importing any dataset, record its version, retrieval date, license, permitted uses, update process, identifiers, and whether derived data can be redistributed.

### Licensing review is overdue for data already in the repository

This obligation was written as forward-looking. It is not. `NOTICE` covers PubChem, FDA labels, and DrugBank only, while the repository tracks several other sources with materially different terms:

- **ChEMBL — CC BY-SA 3.0.** Share-alike, and ChEMBL is the strongest layer in the graph. Redistributing derived data under an Apache-2.0-only NOTICE is a conflict that must be resolved, not annotated.
- **KEGG.** Listed as a source in `CLAUDE.md` and used in `data/proteins/aml_proteins.py`. KEGG states it is not a public database and that non-academic use requires a commercial license; Apache-2.0 grants downstream commercial use.
- **OmniPath** (`data/omnipath_signed.tsv`, tracked). OmniPath imposes no unified license — each constituent resource carries its own, and a `license='commercial'` query filter exists precisely because many are restricted. There is no evidence that filter was applied to the vendored file.
- **STRING** — CC BY 4.0, attribution required.
- **DrugBank.** The current NOTICE reasons from *the author's* non-commercial intent, which does not bind downstream Apache-2.0 recipients who have been granted commercial rights. The carve-out is internally inconsistent and needs rewriting or the data needs removing.

Additionally: **OncoKB's terms forbid using its content to train AI/ML models, academic or commercial**, and even benchmarking against it requires explicit permission. The earlier line that OncoKB is "valuable for comparison" should not be read as permission to benchmark without asking.

A **data refresh path** is also missing. `tier1.db` is a frozen artifact; ChEMBL, FDA labels, and PubMed all move. A collaborator's second question will be how current the graph is, and there is currently no answer.

## Relationship to the rest of James's verification portfolio

PHARM should remain usable without forcing users to understand the entire portfolio.

Possible later integrations are narrow:

- **haloa:** record whether cited evidence was actually accessed, without claiming the evidence is true;
- **nlock:** require data-version, benchmark, provenance, or privacy preconditions before a result is exported;
- **SirNlock:** gate an external research action or durable export and record what was authorized and what an adapter reported;
- **Noesi Assurance:** potentially review evidence bundles in an assurance workflow.

These are optional boundaries, not reasons to complicate PHARM now. PHARM's primary output is a biological research evidence bundle. None of these tools should authorize a clinical act.

## Collaboration and adoption roadmap

The binding constraint is still external use, not idea supply.

The ideal first collaboration is small:

1. a researcher supplies a public dataset, candidate list, or previously completed question;
2. James runs a pre-agreed PHARM workflow;
3. the researcher marks useful, wrong, missing, and obvious results;
4. James records the objections rather than defending the system;
5. the same question is rerun after one bounded revision;
6. both decide whether a second question is worth doing.

A good outreach statement is:

> I built a transparent oncology repurposing triage prototype. It performs well at recovering known relationships inside its curated graph. Its performance on genuinely novel pairs I cannot currently claim in either direction — my negative labels are incomplete and my holdouts leak, and I would rather say that than quote a number I cannot defend. I am looking for one real candidate-review question or public dataset where a domain researcher can tell me exactly where its evidence helps and where it fails.

The useful exchange is not “please use my product.” It is “let us jointly test whether this reduces your review burden without hiding uncertainty.”

## Stop conditions and strategic pivots

PHARM should pivot or narrow if:

- reviewers do not value path-level auditability enough to tolerate lower novelty;
- a conventional tool performs the same task with less effort and equal evidence traceability;
- custom datasets cannot be normalized without extensive per-project engineering;
- manual citation audits show unacceptable assertion error;
- external precision, **once it is validly measured against a complete label set**, remains too low to create a useful review budget;
- no external researcher returns for a second use after several serious trials.

Possible honest pivots include:

- an evidence-audit and benchmark harness for other drug-repurposing systems;
- a claim/provenance layer consumed by existing platforms;
- an AML-specific evidence workbench rather than pan-oncology software;
- a research service in which James performs evidence-bounded analyses with collaborators rather than selling a self-serve product.

Subtraction is allowed. A smaller system that is repeatedly useful is closer to helping people than a universal system no one trusts.

## Long-term definition of success

PHARM succeeds first when an outside researcher says:

> This removed enough candidates, preserved enough evidence, and admitted enough uncertainty that I would use it on another question.

It succeeds scientifically when the result survives independent data, simple baselines, manual evidence review, and a domain expert's objections.

It succeeds as a patient-adjacent research system only when qualified partners can use a governed case dossier without mistaking it for treatment advice.

It succeeds clinically, if that path is ever chosen, only after a separate program earns the analytical, clinical, regulatory, and operational evidence required for the intended use.

The guiding sentence is:

> **Make the evidence more useful before making the claim larger.**

## Authoritative resources consulted

Checked July 31, 2026. These are inputs to the roadmap, not endorsements of PHARM.

### Evidence and target/variant knowledge

- Open Targets Platform: https://platform.opentargets.org/
- Open Targets evidence model: https://platform-docs.opentargets.org/evidence
- Open Targets target prioritisation: https://platform-docs.opentargets.org/web-interface/target-prioritisation
- CIViC introduction and knowledge model: https://docs.civicdb.org/en/latest/
- CIViC evidence levels: https://docs.civicdb.org/en/latest/model/evidence/level.html
- CIViC use and licensing: https://docs.civicdb.org/en/latest/about.html
- OncoKB API introduction: https://api.oncokb.org/
- OncoKB licensing and usage restrictions: https://faq.oncokb.org/licensing

### Cohort, dependency, combination, safety, and multi-omics data

- NCI Genomic Data Commons data types: https://gdc.cancer.gov/about-data
- TCGA-LAML cohort: https://gdc.cancer.gov/about-data/publications/laml_2012
- DepMap CRISPR dependency resources: https://depmap.org/portal/resources?subcategory=depmap-pipelines&topic=crispr-pipeline-and-analysis
- Beat AML 2.0 data portal (processed tiers, CC-BY-4.0): https://biodev.github.io/BeatAML2/
- Beat AML 2.0 catalog entry (805 patients, 942 specimens): https://datacatalog.ccdi.cancer.gov/dataset/Vizome-BEATAML2.0
- Beat AML original study, Tyner et al., Nature 2018: https://www.nature.com/articles/s41586-018-0623-z
- NCI-ALMANAC: https://dtp.cancer.gov/ncialmanac
- NCATS matrix combination screening: https://ncats.nih.gov/research/research-activities/matrix
- FDA drug-interaction tables: https://www.fda.gov/drugs/drug-interactions-labeling/drug-development-and-drug-interactions-table-substrates-inhibitors-and-inducers
- FDA M12 drug-interaction guidance: https://www.fda.gov/regulatory-information/search-fda-guidance-documents/m12-drug-interaction-studies
- openFDA adverse-event limitations: https://open.fda.gov/apis/drug/event/
- NCI Proteomic Data Commons: https://proteomic.datacommons.cancer.gov/
- NCI Human Tumor Atlas Network: https://www.cancer.gov/about-nci/organization/dcb/research-programs/htan

### Genomics, patient representation, privacy, and clinical boundary

- GA4GH Phenopackets: https://www.ga4gh.org/product/phenopackets/
- GA4GH Variation Representation Specification: https://www.ga4gh.org/product/variation-representation/
- GA4GH Cat-VRS and VA-Spec: https://www.ga4gh.org/news_item/ga4gh-approves-two-new-products-categorical-variation-representation-specification-cat-vrs-and-va-spec/
- HL7 FHIR Genomics Reporting, somatic testing: https://www.hl7.org/fhir/uv/genomics-reporting/STU3/somatics.html
- NIH Genomic Data Sharing policy: https://sharing.nih.gov/genomic-data-sharing-policy/about-genomic-data-sharing
- NIH security practices for controlled genomic data: https://sharing.nih.gov/sites/default/files/flmngr/NIH_Best_Practices_for_Controlled-Access_Data_Subject_to_the_NIH_GDS_Policy.pdf
- HHS de-identification guidance: https://www.hhs.gov/hipaa/for-professionals/special-topics/de-identification/index.html
- FDA Clinical Decision Support Software guidance (issued January 6, 2026; re-issued January 29, 2026): https://www.fda.gov/regulatory-information/search-fda-guidance-documents/clinical-decision-support-software
- FDA CDS final-guidance town hall, confirming issuance and re-issuance dates: https://www.fda.gov/medical-devices/medical-devices-news-and-events/town-hall-clinical-decision-support-software-final-guidance-03112026

### Licensing terms verified for sources already in use

- ChEMBL data licence (CC BY-SA 3.0): https://chembl.gitbook.io/chembl-interface-documentation/about
- KEGG licensing: https://www.genome.jp/kegg/legal.html
- OmniPath licensing (per-resource, `license='commercial'` filter): https://omnipathdb.org/
- CIViC licensing (CC0 1.0): https://civic.readthedocs.io/en/latest/about/faq.html
- OncoKB licensing, including the prohibition on AI/ML training: https://faq.oncokb.org/licensing
- FDA approval of dacomitinib for metastatic NSCLC, 2018-09-27 (the label-completeness example): https://www.fda.gov/Drugs/InformationOnDrugs/ApprovedDrugs/ucm621967.htm

### Chromosomal and tumor-context research

- NCI DNA and chromosome aberrations research: https://www.cancer.gov/about-nci/organization/dcb/research-portfolio/dcar
- GDC copy-number and structural-variant data: https://gdc.cancer.gov/about-data
- PCAWG pan-cancer whole-genome analysis summary: https://edrn.cancer.gov/data-and-resources/publications/32025007-2919-pan-cancer-analysis-of-whole-genomes/
- NCI tumor biology and microenvironment research: https://www.cancer.gov/about-nci/organization/dcb/research-portfolio/tbmr

