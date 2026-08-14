# Trial Results Recovery — 2026-08-12

Recovering trial results that exist but are not indexed by the literature.

## Why

Of the 77 trials tracked by the 60-candidate review, 75% never posted results,
and every recorded stop reason is operational or financial — low accrual, lost
funding, sponsor bankruptcy, drug supply — **never efficacy or safety**. So the
"no direct evidence found" verdict on 17 candidates cannot be read as "untested
idea." Part of that void is trials that ran and were never reported.

That matters for the tool: the novelty axis in `validation/nonobvious.py` counts
PubMed co-mentions, so a pair with a terminated Phase 2 and no publication looks
identical to a pair nobody ever tried.

## Result

Every tracked trial now carries a retrieval-only disposition:

| Disposition | Count | Meaning |
|---|---:|---|
| `UNRESOLVED_NO_SOURCE_FOUND` | 22 | Search not yet exhausted; see Phase 3 |
| `RESULTS_RECOVERED_CTG` | 19 | Results posted on ClinicalTrials.gov |
| `ONGOING_NO_RESULTS_YET` | 18 | Still running — not a hole |
| `RESULTS_RECOVERED_PUBLICATION` | 12 | Linked result or derived publication |
| `NO_DATA_EVER_GENERATED` | 6 | Withdrawn with confirmed actual enrolment of 0 |

**13 of the 19 recovered trials have posted results and no publication at all.**
No literature search will surface them. Examples include `NCT00536601`
(progression-free survival, 174 enrolled) and `NCT01520870` (dacomitinib).

`NO_DATA_EVER_GENERATED` is a complete answer, not a failed search — a withdrawn
trial that enrolled nobody produced nothing to find.

## The hard boundary

**Fill by retrieval. Never by inference.**

These records say results **exist** and **where to read them**. They do not say
what the results showed. Every recovered outcome row is written as
`result_signal = 'RESULTS_AVAILABLE_NOT_ASSESSED'` with `human_reviewed = 0`.
Reading a results section and judging efficacy is human work that has not
happened yet.

None of this enters the scored graph path. `app.py` is the only module that
imports `evidence`, and nothing in `oracle/`, `core/`, `validation/`, or `data/`
does. Recovered results are **labels, not features** — folding them into the
ranker would destroy the project's only route to an honest external validation.
See `docs/PLAN_TRIAL_RESULTS_RECOVERY_2026-08-12.md` section 4a.

## Files

- `RECOVERED_RESULTS.json` — distilled per-trial registry facts and dispositions.
  **Committed on purpose.** The build reads it, so keeping it in gitignored
  `data/external/` would give two people different databases.
- `PROVENANCE.json` — request URLs, SHA-256 of each raw response, timestamps.
- `RECON_REPORT.json` — the 2026-08-12 feasibility reconnaissance.
- `recon.py` — reproduces `RECON_REPORT.json`.

## Two denominators, deliberately

`RECON_REPORT.json` covers **82** NCT identifiers taken from the `receipts`
table of a built `evidence.db`. `RECOVERED_RESULTS.json` covers **77** taken
from `TRIAL_EVIDENCE_60.json`, the review inventory the database is built from.
The five extra identifiers are referenced by receipts without being trials in
the inventory. Acquisition reads the inventory so it does not depend on a built
database, which would be circular.

## Reproduce

```powershell
python -m evidence.acquire_trial_results --refresh   # re-fetch from CTG v2
python -m evidence.build                             # rebuild with recovery
python -m pytest tests/test_trial_results_recovery.py -q
python reports/trial_recovery_2026-08-12/recon.py    # the original recon
```

## Next

Phases 2–4 in `docs/PLAN_TRIAL_RESULTS_RECOVERY_2026-08-12.md`: chase the 22
unresolved trials through EU CTR/CTIS, FDA and EMA documents, and ASCO/AACR/ESMO
abstracts, then surface dispositions in the UI. The 11 completed-and-vanished
trials are the highest-value targets.
