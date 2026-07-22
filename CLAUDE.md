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

## Canonical current numbers (2026-07-21)

Strict `remove_direct_labels`, **`core` cohort (78 curated drugs)**, **ESMC-excluded
default graph**:

- **AUROC 0.9784** [0.9667–0.9883], **AUPRC 0.6128** [0.4728–0.7480]
- Hits@5 1.00, Hits@10 0.70, Hits@20 0.70
- **Margin over best trivial baseline: +0.24** (common-neighbor 0.7429). This is the
  honest advantage; do not quote the older +0.36.
- Funnel: top 5% of pairs catches 73% of known hits (~14.5× enrichment).

Reproduce: `python validation/repurposing_benchmark.py --view full_typed --protocol remove_direct_labels --cohort core --baselines --ci`

**Two cohorts, not comparable.** `core` = 78 curated drugs (quote this). `all` = 757
drugs (core + 679 materialized ChEMBL); its AUROC reads ~0.99 but that is an
artifact of ~13,500 easy negatives — AUPRC falls and the baseline margin collapses to
~+0.05. Use `all` only as a discovery surface, never as a benchmark.

## The graph

- 757 drug nodes; **128 have a complete Drug→Protein→Disease path** (the rest are
  stranded — see terminal-hop limitation). 20 oncology diseases. 44 FDA `treats`
  positives.
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

3. **The terminal Protein→Disease hop is the binding constraint.** Only 158 proteins
   carry a disease edge, and most such edges are `associated_with` (co-occurrence,
   not mechanism). This is why 629 drugs are stranded and why novelty is limited.

## Honest limitations (full version: `HONEST_VALUE.md`)

- Oncology only, 20 diseases, curated graph. External generalization is weak
  (Hetionet AUPRC ~0.01).
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

## Run it

```powershell
streamlit run app.py                     # the UI; modes in the left sidebar
python -m pytest tests/ -q               # 166 pass, 1 skip
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
