# CLAUDE.md — KOMPOSOS-IV-PHARM

> **Read this first. It is the orientation file every session auto-reads.**
> If a number here disagrees with an older doc, this file and the code win.
> **Golden rule:** trust the code, the tests, and `HONEST_VALUE.md` over any other
> doc. Always name the **cohort** and **protocol** when you quote an AUROC.

## What this is, in one paragraph

An honest, glass-box **triage accelerator** over *known* oncology pharmacology. It
ranks drug→disease repurposing candidates, and each ranking IS its evidence: a set
of Drug→Protein→Disease paths, every edge carrying its provenance, citations, and an
evidence tier you can click through to PubMed. Its value is auditability and speed,
**not** novelty. It recombines *published* drug-target and target-disease facts into
a cited shortlist of hypotheses; it does **not** discover biology absent from the
literature, and it cannot certify which of its novel compositions are real. Pitch it
as a fast, transparent hypothesis-triage tool that knows its own limits — never as
"AI that finds new cures."

## Canonical current numbers (2026-07-21, re-verified 2026-07-31)

Strict `remove_direct_labels`, **`core` cohort (78 curated drugs)**, **ESMC-excluded
default graph**:

- **AUROC 0.9784** [0.9667–0.9883], **AUPRC 0.6128** [0.4728–0.7480]
- **precision@5 1.00, precision@10 0.70, precision@20 0.70.** The code prints these
  as "Hits@k" but computes `hits / min(total_positives, k)` — that is precision@k,
  which is why the value *falls* from k=5 to k=10. Say precision@k.
- **Scored-only AUROC 0.9642.** 603 of 1,560 pairs are abstentions scored 0.0 and
  are included in the headline AUROC; all are negatives. AUPRC is unaffected.
  Quote both numbers.
- **Margin over best trivial baseline: +0.24** (common-neighbor 0.7429). This is the
  honest advantage; do not quote the older +0.36.
- Funnel: top 5% of pairs catches 73% of known hits (~14.5× enrichment).
- **External precision is undetermined, not weak.** The Hetionet inputs are missing
  from the repo and the temporal holdout leaks and runs on the wrong cohort; its
  negative set contains approved indications (Dacomitinib→NSCLC, approved
  2018-09-27, ranks first among its "negatives"). Make no precision claim in
  either direction until a complete label set exists. See `HONEST_VALUE.md`.

Reproduce: `python validation/repurposing_benchmark.py --view full_typed --protocol remove_direct_labels --cohort core --baselines --ci`

**Two cohorts, not comparable.** `core` = 78 curated drugs (quote this). `all` = 757
drugs (core + 679 materialized ChEMBL); its AUROC reads ~0.99 but that is an
artifact of ~13,500 easy negatives — AUPRC falls and the baseline margin collapses to
~+0.05. Use `all` only as a discovery surface, never as a benchmark.

## The graph

- 757 drug nodes; **128 have a complete Drug→Protein→Disease path** over **1,206
  reachable pairs** on the default graph (the rest are stranded — see terminal-hop
  limitation). 20 diseases — **not all oncology**: the set includes `Type2_Diabetes`
  and `Li_Fraumeni_Syndrome`, and 6 of the 20 carry **zero positives** (AML,
  Glioblastoma, Ewing_Sarcoma, Prostate_Cancer, Soft_Tissue_Sarcoma, Li_Fraumeni).
  44 FDA `treats` positives, one of which is `Metformin → Type2_Diabetes`.
- **AML has no `treats` label at all**, and only FLT3 and TOP2A reach it through a
  directed edge. Any AML work must bring its own external labels.
- **2,439 edges in the DB; 2,015 scored.** The 424 ESMC protein-embedding
  similarity-transfer edges are tagged `[EMBEDDING-INFERRED]` and **excluded from
  scoring** — see below.
- Sources: ChEMBL (881, the strong Drug→Protein layer), PMID literature, curated
  cancer-protein lists, KEGG, FDA labels, ABPP (65 IC50s), STRING, tiny DepMap/CosMx.

## Three measured findings that define what to believe

1. **ESMC similarity-transfer edges are noise.** Ablation
   (`python -m validation.esmc_ablation --cohort core`) showed removing all 422
   *improves* the ranker (AUROC 0.9691→0.9784). They are excluded from the default
   scored graph (`load_full_typed_view` defaults to `exclude_provenance="ESMC"`;
   restore with `--include-inferred`). See `data/ESMC_ABLATION_RESULT.json`.

2. **Post-hoc PubMed grounding carries no signal.** Permutation negative control
   (`scripts/grounding_negative_control.py`): real protein-disease pairings ground at
   12.5%, randomly scrambled ones at 7.5% — indistinguishable (Fisher p=0.28). A PMID
   on a Protein→Disease edge means "not absurd, start reading here," **not**
   "validated." Drug→Protein citations (ChEMBL/FDA) are independently derived and
   unaffected. See `data/GROUNDING_NEGATIVE_CONTROL.json`.

3. **The terminal Protein→Disease hop is the binding constraint.** Re-measured
   2026-07-31 (the earlier "158 proteins" was wrong): only **107** non-drug/
   non-disease nodes carry a disease edge on the default graph, over **783**
   terminal edges — **746 `associated_with`** versus **37 directed `driver_of`
   across 28 sources**. Through a directed terminal hop only **76 drugs and 138
   pairs** are reachable. **138 is the true size of the mechanistically grounded
   surface.** This is why 629 drugs are stranded and why novelty is limited.

## Honest limitations (full version: `HONEST_VALUE.md`)

- 20 diseases, curated graph, oncology-dominated but not oncology-only. **External
  generalization is unmeasured, not weak** — the Hetionet number is retired
  (inputs absent from the repo) and the temporal holdout is leaky and mis-cohorted.
- **The repository does not `pip install`.** `pyproject.toml` names a build backend
  that does not exist, and `packages.find` ships only `core*`. The benchmark runs
  fine from a checkout; packaging is what is broken.
- **No conflict representation exists.** `oracle/evidence_combination.py` cannot
  produce non-zero Dempster conflict by construction. Not in the scored path.
- **The combination layer runs on a different graph** (OmniPath) and its one
  labelled external test scores AUROC 0.36. It inherits none of the numbers above.
- Hub-drug bias: Imatinib tops 14/20 diseases. Use the **Disease-specific** view.
- Empty `quantitative_value` columns (schema implies data that reads NULL).
- Research prototype. Not clinical, translational, or regulatory validation.
- A rules-based directed-relation extractor was tried and did **not** beat the
  lexical gate on held-out data (`komposos_kg/directed_extractor.py`, marked
  EXPERIMENTAL). Fixing directed extraction needs a model, not more rules.

## Where the real code and data live (disk hazards)

- **Canonical tree: this folder, `KOMPOSOS-IV-PHARM-master`.** It is now a proper git
  working copy tracking `origin/master` at github.com/Jayhawk314/KOMPOSOS-IV-PHARM.
- The default cwd `komposos-iv-pharm` is an **empty shell** (`.claude/` + a stray
  `nul`). The sibling `... - Copy (4)/(5)/(16)` folders are **pre-integrity-audit**
  and carry a *worse* database (half unverified co-mention noise). **Never analyze or
  share from a Copy folder.**
- Docs are sprawled (133 .md files; `docs/` and `truedocs/` hold aged material).
  `HONEST_VALUE.md`, this file, and the JSON result files above are the current
  source of truth. When in doubt, run the reproduce commands.

## Quarantined — non-product, excluded from validation

These files remain in the tree for dependency and historical review. **None may
support a claim, appear on a public surface, or enter the scored path.** Do not
delete them without a dependency and historical-value review.

- `validation/spatial_biology_metrics.py` — hardcoded placeholder L-R metrics
  (0.65/0.45/0.30) and baselines (0.62/0.68); imported by nothing.
- `spatial_biology/generate_validation_data.py` — synthetic data seeded with the
  pattern the method is meant to discover ("better than public datasets because we
  KNOW the answer"). **Circular by construction**; its output is not a result.
- `scripts/mutation_impact.py` — reconstructs 3D coordinates by MDS over a
  fabricated distance matrix, then prints `kcal/mol`. Pseudo-coordinates cannot
  support physical-energy claims.
- `oracle/evidence_combination.py` — conflict is structurally zero; see above.
- `oracle/score_combination.py` — hand-set coefficients, blend weights, and
  variance-to-agreement map. Not learned calibration.

Also do-not-resurrect, in the sibling LAMBDA prototype:
`oracle/patient_stratification.py` (invented defaults for missing data),
`oracle/toxicity_assessment.py` (**emits dosing instructions** from an
uncalibrated heuristic), `oracle/clinical_validation_pipeline.py`.

**Hard rule: no PHARM output may contain dosing language**, in any module, at any
phase.

## Current work in flight

`WORKING_SESSION_2026-07-31.md` is the live log. The approved sequence is:
correct documents (done) -> **50-pair reviewer exercise (packet built, awaiting a
reviewer)** -> judge whether the bundles are useful -> packaging (done) -> complete
the label set (seeded only) -> only then design the Beat AML experiment.

- `reports/reviewer_audit_2026-07-31/` — the packet. **`MANIFEST.json` is the
  answer key; never send it to a reviewer.** Send the two `.md` files and the two
  blank `.csv` files only.
- `data/labels/evaluation_labels_v1.csv` — the Phase 0.5 label set. **A seed**:
  50 of 15,140 pairs, 44 of them inherited without any citation. Do not compute
  AUPRC or precision against it and present the result as a measurement.

## Run it

```powershell
streamlit run app.py                     # the UI; modes in the left sidebar
python -m pytest tests/ -q               # 166 pass, 1 skip
python -m validation.check_label_set     # label-set structure + how incomplete it is
python -m validation.build_reviewer_packet   # regenerate the 50-pair packet
python validation/triage.py Melanoma --drug Sorafenib   # one audited candidate
python -m validation.nonobvious --disease Melanoma      # under-discussed real compositions
```

## Architecture (reference)

- `core/`: fused Category runtime (objects, morphisms, persistence, enrichment).
- `oracle/`: prediction/scoring strategies (binding_evidence, yoneda_distance, etc.).
- `validation/`: benchmark harnesses, triage CLI, ablation, negative control, nonobvious.
- `komposos_kg/`: honesty/gate infrastructure + the experimental directed extractor.
- `data/store.py`: SQLite API. `data/drugs/tier1.db`: the graph. `data/bio_embeddings.py`: ESMC-300M.
- `app.py`: the Streamlit UI. Higher categorical layers (infinity-cosmos, HoTT, topos)
  are intellectual scaffolding; ablation shows a classical path-composition core earns
  the metric — judge the system on that core.
