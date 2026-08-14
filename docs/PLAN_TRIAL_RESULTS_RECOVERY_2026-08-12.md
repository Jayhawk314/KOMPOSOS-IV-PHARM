# PLAN — Trial Results Recovery

Written 2026-08-12. **Phase 1 is implemented and passing** — see
`reports/trial_recovery_2026-08-12/README.md` for what it recovered. The
reconnaissance and all receipts are in that same directory. Start at Phase 2;
do not re-litigate whether this is worth doing.

## 0. Why this exists

The 60-candidate audit found 17 candidates with "no direct evidence found." The
evidence database shows why that bucket is untrustworthy: of the 77 trials it
tracks, 75% never posted results, and every recorded stop reason is operational
or financial — low accrual, lost funding, sponsor bankruptcy, drug supply —
never efficacy or safety. So `nonobvious.py`'s novelty axis cannot distinguish
"nobody tried this" from "somebody tried it and ran out of money."

This is a known problem with a name and a literature: restoring abandoned
trials (Cochrane, AllTrials, the RIAT initiative). It is meta-research, it needs
no wet lab and no experimental collaborator, and it is the one line of genuinely
novel work this repository can complete on its own.

## 1. The hard boundary

**Fill by retrieval. Never by inference.**

Recovering a result that exists but is not indexed is allowed and is the point.
Imputing a missing outcome is not — no mechanism score, no plausibility, no
"probably positive." A trial that vanished with nothing recoverable is recorded
as irrecoverable after a documented search. That is the same discipline as
absence-never-renders-as-a-pass, applied one level up.

No dosing language, per the project hard rule.

## 2. Reconnaissance result (2026-08-12, complete)

All 82 `NCT` identifiers in `data/evidence/evidence.db` were queried against the
ClinicalTrials.gov v2 API. 82 of 82 resolved; none were missing.

| Class | Count | Meaning |
|---|---:|---|
| `NO_RESULTS_NO_PUBLICATION` | 48 | No posted results, no linked publication |
| `RESULTS_POSTED_NOT_PUBLISHED` | **15** | **Results on CTG, no paper — free recovery** |
| `PUBLISHED_ONLY` | 12 | Publication exists, no posted results |
| `RESULTS_POSTED_AND_PUBLISHED` | 7 | Both |

**27 of 82 trials (33%) carry recoverable evidence that the database does not
currently represent as an outcome** — every `TRIAL_RECORD` outcome row is still
`NOT_ASSESSED_BY_AUTOMATION`.

The 48 "no results" trials break down by status, and this matters:

| Status | Count | Reading |
|---|---:|---|
| RECRUITING | 10 | Not a hole — ongoing |
| ACTIVE_NOT_RECRUITING | 9 | Not a hole — ongoing |
| **COMPLETED** | **11** | **Ran, finished, reported nothing. The real targets.** |
| WITHDRAWN | 7 | May have zero enrollment — nothing to recover is a complete answer |
| UNKNOWN | 6 | Sponsor stopped updating; the silence is itself a finding |
| TERMINATED | 4 | Check why_stopped |
| NO_LONGER_AVAILABLE | 1 | |

So 19 of the 48 are simply not finished. **True unresolved holes: 29.** The
worst and most valuable subset is the 11 COMPLETED trials that vanished:

```
NCT01112527  NCT00002733  NCT00006473  NCT00101270  NCT00083109  NCT00091182
NCT02386826  NCT02071862  NCT03009201  NCT02705859  NCT02013492
```

**Staleness is already proven.** CTG now reports 22 trials with posted results;
`evidence.db` records 19. Three trials posted results since the 2026-08-01
build. This must be a maintained pipeline, not a one-off import.

## 3. Design constraint discovered

`evidence/build.py` rebuilds the database from scratch into a temporary file and
replaces it (`build_database`, `temporary.unlink()`). **Hand-editing
`evidence.db` will be silently wiped on the next `python -m evidence.build`.**

Therefore: acquisition must cache raw responses to disk with checksums, and an
importer must run inside the build. Follow the pattern already proven in
`validation/build_alphafold_coherence_cohort.py` — cached, resumable, URLs and
SHA-256 recorded, large payloads under `data/external/` and gitignored.

## 4. Phased work

### Phase 1 — the free recovery — **DONE 2026-08-12**

Implemented as `evidence/acquire_trial_results.py`, imported by
`evidence/build.py:import_recovered_results`, covered by
`tests/test_trial_results_recovery.py` (13 tests, offline). Suite: 225 passed,
1 skipped.

Recovered: 19 trials with posted registry results, **13 of them with no
publication of any kind**; 12 with result publications; 6 withdrawn trials
confirmed to have generated no data; 18 correctly excluded as still running; 22
still unresolved and handed to Phase 3. Outcomes went 141 to 160.

Schema gained `studies.results_disposition`, `results_url`, and
`results_checked_on`. Distilled records are **committed** under
`reports/trial_recovery_2026-08-12/` rather than cached in gitignored
`data/external/`, so the build is reproducible for everyone.

Original plan for this phase, retained for context:

Harvest the CTG results modules for the 22 trials with posted results, and link
publications for the 12 `PUBLISHED_ONLY` trials.

- `evidence/acquire_trial_results.py`: fetch and cache CTG v2 results sections
  and `referencesModule` for every tracked NCT; record URL, timestamp, SHA-256.
  Resumable, `--refresh` to re-pull.
- Import into `outcomes` with a real `result_signal` and a `receipt_id`, and set
  `human_reviewed = 0` — automated extraction is not review.
- Set `relevance_assessment` on the receipts it creates. 127 of 148 existing
  receipts have this field empty; do not add to that pile.

Deliverable: the 15 no-paper trials get outcomes nothing else in the world
indexes. Measure how many change a candidate's standing in the 60-candidate
audit — that number is the headline.

### Phase 2 — disposition every trial

Give each trial exactly one disposition, with a receipt:

`RESULTS_RECOVERED_CTG` · `RESULTS_RECOVERED_PUBLICATION` ·
`RESULTS_RECOVERED_REGULATORY` · `RESULTS_RECOVERED_ABSTRACT` ·
`ONGOING_NO_RESULTS_YET` · `NO_DATA_EVER_GENERATED` ·
`IRRECOVERABLE_DOCUMENTED_SEARCH`

`NO_DATA_EVER_GENERATED` is a complete answer, not a failure — one trial in the
current set stopped with "No participants enrolled." There is nothing to find.

### Phase 3 — the remaining holes, cheapest source first

1. **EU CTR / CTIS and the WHO ICTRP** — EU trials must post summary results;
   many oncology trials are dual-registered.
2. **Drugs@FDA reviews, AdComm briefing documents, EMA EPARs** — 54 of the 60
   candidates are `KNOWN_DRUG_NEW_CANCER`, so the drugs are approved and
   sponsors submitted data they never published. The classic RIAT route.
3. **ASCO / AACR / ESMO abstracts** — frequently the only report of a small
   terminated trial, and poorly indexed in PubMed. Best yield for the
   accrual-failure trials.
4. Investigator and sponsor contact. Slow, low yield, last.

### Phase 4 — surface it, without touching the scored path

Show the disposition and the stop reason next to every candidate: prior trial
exists, what happened to it, why it stopped, and a link to the CTG results. A
candidate whose only prior trial closed for low accrual is a **better** lead,
not a discarded one — the science was never tested. No other repurposing tool
outputs this distinction.

**Annotate. Do not blend.** See section 4a; this is a hard boundary, not a
preference.

## 4a. Where recovered evidence may and may not go

**UI: yes. Scoring: no. This boundary already exists in code — keep it.**

`app.py` is the only module that imports `evidence`, via `load_evidence_store()`
("*Read-only contextual evidence; deliberately separate from graph scoring*").
Nothing in `oracle/`, `core/`, `validation/`, or `data/` imports it. Recovered
trial results inherit that isolation unchanged.

**Why scoring is off limits — the decisive reason.** `HONEST_VALUE.md` and
`CLAUDE.md` record that external precision is undetermined because no complete
label set exists. Trial outcomes are exactly the missing labels. **These are
labels, not features.** The moment they feed the ranker, they can never serve as
an independent test of it, and the project permanently loses its only route to
an honest external validation number. That is the leaky-temporal-holdout error
repeated, with the last clean evidence available.

Two further reasons: outcomes about a candidate feeding the ranking of that same
candidate is circular; and automated extraction from a CTG results module is
error prone and carries `human_reviewed = 0`, which must never move a score.

**Why the novelty term must be annotated, not adjusted.** It is tempting to
correct `nonobvious = support * novelty` with trial existence, since a
registered trial is prior discussion the PubMed count missed. Do not fold it
into the product. Choosing that weight would reproduce precisely the pattern
that put `oracle/score_combination.py` in quarantine — "hand-set coefficients,
blend weights, not learned calibration." Report the PubMed-only novelty
unchanged, so rankings stay comparable to history, and show the trial
disposition beside it. Let the reader do the weighing; that is what glass-box
means.

**The benchmark must not move.** `validation/repurposing_benchmark.py` continues
to run on the graph as-is, so the 2026-08-01 core-cohort figures stay
comparable. If a future session wants recovered outcomes as evaluation labels,
that is a *separate, pre-registered* experiment against a frozen candidate set —
never a quiet change to the scored graph.

## 5. Go/no-go

Phase 1 is already justified: 27 recoverable trials, 15 of them invisible to any
literature search. If Phase 1 recovers those and none of them moves a single
candidate's standing in the audit, stop and report that — it would mean the
holes are real but inconsequential, which is still a result worth writing down.

## 6. Honest limits

- 77 trials selected by this system's own top-60 candidates is a small,
  non-random sample. The 75%-unreported figure is illustrative of this cohort,
  **not** an epidemiological estimate. Do not publish it as one.
- Trial results non-reporting is a well-studied phenomenon. The contribution
  here is not discovering it; it is quantifying how it corrupts a repurposing
  triage signal, with receipts, and fixing the tool accordingly.
- Automated extraction of `result_signal` from a CTG results module is error
  prone. Mark it `human_reviewed = 0` and keep the 60 human-reviewed pair-level
  outcomes distinct from it.

## 7. Reproduce the reconnaissance

```powershell
python -m evidence.acquire_trial_results --refresh   # re-fetch from CTG v2
python -m evidence.build                             # rebuild with recovery
python -m pytest tests/test_trial_results_recovery.py -q
python reports/trial_recovery_2026-08-12/recon.py    # the original recon
```

`recon.py` reads NCT identifiers from `data/evidence/evidence.db` and is
read-only. `acquire_trial_results` reads them from the review inventory instead,
so acquisition never depends on a database built from its own output.
