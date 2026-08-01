# Candidate review — 60 target-zone candidates

**The question this answers:** does the target zone contain a genuinely useful,
inexpensive, non-approved cancer candidate once mechanism, direction, prior
trials and existing literature are checked by a person?

Nothing else in this project answers that. It needs a human reading papers.

## Read every row, including the obviously wrong ones

Ten rows are known-bad and deliberately left in: six EGFR→glioblastoma (a class
that repeatedly failed) and four routing through `Li_Fraumeni_Syndrome` (a
germline predisposition syndrome, not a tumour type).

Skipping them makes the resulting number worthless. The previous session checked
only plausible-looking candidates, got 14 of 14, and that figure could not be
used for anything because the sample was chosen after the fact.

## Order is deliberately not by score

Rows are interleaved across cheap generics, other drugs, and known-bad cases.
Sorting by confidence would front-load the plausible ones and let an early
impression set the standard for everything after.

## Columns

| column | meaning |
|---|---|
| `mechanism_target` | the protein the chain runs through |
| `terminal_relation` | `driver_of` = mechanism; `associated_with` = co-occurrence |
| `direction` | whether the drug pushes the target the right way (see `validation/direction_filter.py`) |
| `papers_drug_plus_cancer` | PubMed hits for this drug **with this cancer** |
| `papers_drug_in_cancer_overall` | PubMed hits for this drug **in cancer at all** |
| `novelty_class` | `UNEXPLORED_DRUG` = nobody has looked at this drug in cancer; `KNOWN_DRUG_NEW_CANCER` = known candidate, this cancer untested |

The two paper columns must be read together. Mebendazole shows **0** for kidney
cancer and **149** for cancer generally: a well-known repurposing candidate with
one untested indication, not a discovery.

## Fill in

- `VERDICT` — one of `WORTH_READING` / `ALREADY_TRIED` / `WRONG` / `UNCLEAR`
- `why` — one line is plenty
- `negative_evidence_found` — yes/no: did you find evidence it was tried and failed?
- `what_kind_of_negative_evidence` — **this field matters most.** Free text.
  Completed trial with no approval? Terminated for futility? A negative paper?
  A guideline that says not to? Nothing written but everyone knows?

## Why that last column matters

The failed-trial detector (`validation/fetch_negative_trials.py`) scored **0 for
4** and missed every true failure, because it read `whyStopped` while the real
failures had trials that *completed* and were simply never approved.

Rather than guess at a second proxy, the rewrite should be driven by what you
actually find. Your notes in that column define what the detector must detect.

## Known defect in this sample

**R05 — Venetoclax → Ruxolitinib → Myelofibrosis** routes through a *drug*, not a
protein. The graph holds five `Drug→Drug` edges (`synergizes_with`) and the horn
enumeration does not exclude them, so a drug can appear as an intermediate. That
is not a mechanism and the row is not a real candidate. Left in place so the
count stays honest; mark it `WRONG` with the reason.

The fix — constrain horn intermediates to protein types — is small and belongs
with whoever next touches `oracle/horns.py`.
