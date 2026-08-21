# Documentation index

> **Status note (2026-08-21): this page previously said the opposite.** Until
> today it carried a 2026-05-27 notice declaring `docs/` a historical archive
> and pointing at `truedocs/` as the current source of truth. That relationship
> has since reversed — `docs/` now holds the newest plans and results
> (PRISM 2026-08-14, trial recovery 2026-08-12), while `truedocs/` has not been
> updated since. The old notice also quoted figures that are now retired:
> AUROC 0.974694, AUPRC 0.551698, a Hetionet external AUROC of 0.634479, and a
> graph of 5,382 morphisms. **None of those are current** — the graph has 2,462
> edges and the Hetionet result is retired entirely. Recorded here rather than
> silently deleted, so the reversal is visible.

This repository has 145 markdown files. Most are working records, not
maintained references, and some quote numbers that later measurements
superseded. **This page says which is which**, so a reader arriving cold does
not quote a stale figure in good faith.

## The rule

> **Trust the code, the tests, and the reproduce commands over any document,
> including this one.** Every number that matters can be regenerated. When a doc
> and a measurement disagree, the measurement wins and the doc is the bug.

Always name the **cohort** and **protocol** when quoting an AUROC from this
project. `core` (78 curated drugs) and `all` (757 drugs) are not comparable.

## Start here — current and maintained

| Document | What it is |
|---|---|
| [`../README.md`](../README.md) | Orientation, headline result, quickstart |
| [`../HONEST_VALUE.md`](../HONEST_VALUE.md) | **Read before believing anything.** Deliberately self-critical account of what this is and is not worth |
| [`../CLAUDE.md`](../CLAUDE.md) | Canonical current numbers, graph inventory, limitations, quarantine list |
| [`../NOTICE`](../NOTICE) | Third-party data inventory and terms, per source |
| [`PUBLIC_RELEASE_READINESS_2026-08-21.md`](PUBLIC_RELEASE_READINESS_2026-08-21.md) | Release audit; what is fixed, what needs a decision |
| [`TECHNICAL_OVERVIEW.md`](TECHNICAL_OVERVIEW.md) | Architecture, strategies, validation design |
| [`RESEARCHER_GUIDE.md`](RESEARCHER_GUIDE.md) | For an external researcher evaluating the tool |

## Measured results — the actual contribution

Each is a committed result with its own reproduce command. These are the files
to read if you want to know whether this system works.

| Result | Finding |
|---|---|
| [`../data/ESMC_ABLATION_RESULT.json`](../data/ESMC_ABLATION_RESULT.json) | Removing a 422-edge protein-embedding layer **improved** the ranker (0.9691 → 0.9784). Those edges are excluded by default |
| [`../data/GROUNDING_NEGATIVE_CONTROL.json`](../data/GROUNDING_NEGATIVE_CONTROL.json) | Post-hoc PubMed grounding measures corpus density, not biology. Real 12.5% vs scrambled 7.5%, Fisher p=0.28 |
| [`../reports/prism_2026-08-14/README.md`](../reports/prism_2026-08-14/README.md) | Pre-registered external adjudication against PRISM cell-line viability. **No lineage-selective activity for any candidate**; zero of 60 standings changed |
| [`../reports/trial_recovery_2026-08-12/README.md`](../reports/trial_recovery_2026-08-12/README.md) | 75% of tracked trials never posted results; **13 have registry results and no publication at all** |
| [`../reports/candidate_review_2026-08-01/README.md`](../reports/candidate_review_2026-08-01/README.md) | Human audit of 60 top candidates: 1 lead, 12 structurally invalid, 16 already clinically tested, 17 with nothing findable |
| [`ALPHAFOLD_COHERENCE_AUDITOR.md`](ALPHAFOLD_COHERENCE_AUDITOR.md) | Structural-coherence auditor and its null result |

## Plans — current work, with status stated inside

| Document | Status |
|---|---|
| [`PLAN_PRISM_ADJUDICATION_2026-08-14.md`](PLAN_PRISM_ADJUDICATION_2026-08-14.md) | **Implemented and scored.** Read the report above for the result |
| [`PLAN_TRIAL_RESULTS_RECOVERY_2026-08-12.md`](PLAN_TRIAL_RESULTS_RECOVERY_2026-08-12.md) | Phase 1 done; phases 2–4 open |
| [`LOCAL_COMPLETION_AND_EXTERNAL_VALIDATION.md`](LOCAL_COMPLETION_AND_EXTERNAL_VALIDATION.md) | Stopping rationale and outreach protocol |
| [`EVIDENCE_GRAPH_ARCHITECTURE.md`](EVIDENCE_GRAPH_ARCHITECTURE.md) | Evidence-layer design; still accurate |

## Historical records — do not quote for numbers

Working session logs and dated handoffs. They are accurate accounts of *what was
believed on that date* and are kept so the project's reasoning is auditable,
including where it was wrong. Several contain figures that later measurements
superseded.

- `../WORKING_SESSION_2026-07-31.md`, `../WORKING_SESSION_2026-08-14.md`
- `HANDOFF_*.md`, and any file with a date in its name
- `../AI_X_BIO_EVENT_READINESS_2026-08-11.md`

## Aged — treat as archive

`truedocs/` (19 files) and much of the rest of `docs/` (73 files) predate the
2026-07-31 audit that retired several headline claims — including the Hetionet
external number and the temporal holdout, both of which appear in older files as
though they were valid. **Do not cite a number from these without re-running the
measurement.**

Known specific traps in aged material:

- The **Hetionet external AUROC 0.644** is retired: its inputs are absent from
  the repo and it silently ran on the forbidden `all` cohort.
- The **temporal holdout** leaks post-cutoff literature and its negative set
  contains approved indications.
- Any **AUPRC 0.57** figure predates the ESMC exclusion; the current value is
  0.5920.
- Any claim that the graph is **all oncology** is wrong: 20 diseases include
  `Type2_Diabetes` and `Li_Fraumeni_Syndrome`, and 6 carry zero positives.

## Regenerate anything

```powershell
python validation/repurposing_benchmark.py --view full_typed --protocol remove_direct_labels --cohort core --baselines --ci
python -m validation.esmc_ablation --cohort core
python scripts/grounding_negative_control.py
python -m evidence.build
python -m pytest tests/ -q        # expect 249 passed, 1 skipped
```
