#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""Look up clinical-trial history for drug-disease pairs, and flag failures.

*** THE VERDICT THIS SCRIPT PRODUCES IS UNRELIABLE. DO NOT USE IT. ***

Measured 2026-08-01 against the known answers, it scored 0 for 4 on precision
and missed every true positive:

  FLAGGED, ALL WRONG
    Sotorasib -> NSCLC     "Futility" in one trial. Sotorasib IS APPROVED
                           for NSCLC. One arm failing is not a failed drug.
    Avelumab -> NSCLC      "terminated since there was no need for further
                           safety or efficacy data" -- that means they had
                           ENOUGH data. The keyword 'efficacy' matched a
                           success-adjacent closure.
    Cemiplimab -> NSCLC    approved; one trial missed its endpoint.
    Durvalumab -> NSCLC    stopped because the sponsor dropped a DIFFERENT
                           drug in the combination. A business decision.

  MISSED, ALL REAL FAILURES
    Erlotinib/Afatinib/Dacomitinib -> Glioblastoma. 19 of 24 erlotinib GBM
    trials COMPLETED. They were never terminated -- they ran to the end and
    the answer was no.

WHY THE APPROACH IS WRONG
-------------------------
A failed trial is not a failed drug-disease pair, and `whyStopped` is the wrong
field. Drugs fail in one setting and succeed in another; and the failures that
matter here are trials that FINISHED and were followed by silence, which leaves
no stop reason at all.

The right question is "did the field try this, complete late-phase work, and
then never seek approval?" -- completed phase 2/3 plus years elapsed plus no
approval. That is a rewrite of the classifier, not a new data source; the
downloaded trial history in reports/ is still good input for it.

Kept in the tree because the negative result is worth more than the code, and
because the CT.gov query layer below is correct and reusable.

WHY IT WAS BUILT
----------------
The graph has no way to record "this was tried and it did not work." So it keeps
proposing dead ends with full confidence. Measured 2026-08-01: six of the top 50
unfilled-horn predictions are EGFR-directed agents proposed for glioblastoma, a
combination the field tried repeatedly and abandoned. Erlotinib's phase II in
recurrent GBM reported PFS-6 of 3%.

That is not a scoring problem. It is missing data, and the data is free.

WHAT COUNTS AS A FAILURE - AND WHAT DOES NOT
--------------------------------------------
A terminated trial is NOT automatically a scientific failure. Trials stop for
money, staffing and recruitment all the time, and those say nothing about whether
the drug works. Treating them alike would replace one kind of wrong confidence
with another.

So `whyStopped` is classified into:

  SCIENTIFIC   futility, lack of efficacy, disease progression, toxicity, safety
               -> genuine negative evidence about the hypothesis
  OPERATIONAL  accrual, enrolment, funding, sponsor/business decisions
               -> says nothing about the biology; must NOT be read as a failure
  UNCLEAR      stopped, but the reason does not classify -> needs a human

The keyword classifier is a SCREEN, not a judgment. It is the same class of tool
as the lexical relation gate, which this project already measured and found to be
roughly 0.82 precision against human adjudication. Anything it flags SCIENTIFIC
should be read by a person before it is used to suppress a candidate.

WHAT THIS DELIBERATELY DOES NOT DO
----------------------------------
It does not write to tier1.db, and it does not change any score. Suppressing a
candidate because a trial failed is a real design decision with a real cost --
plenty of drugs failed in one setting and succeeded in another, at a different
dose, line of therapy, or biomarker-selected population. That decision needs to
be made deliberately, not as a side effect of an import script.

Run:
    python -m validation.fetch_negative_trials --worklist reports/horn_audit_2026-08-01/HORN_TOP50.csv
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
import time
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

API = "https://clinicaltrials.gov/api/v2/studies"

SCIENTIFIC = (
    "futility", "lack of efficacy", "no efficacy", "did not meet", "efficacy",
    "progression", "toxicity", "safety", "adverse", "did not demonstrate",
    "insufficient activity", "no benefit", "interim analysis", "lack of benefit",
)
OPERATIONAL = (
    "accrual", "enrollment", "enrolment", "recruitment", "funding", "financial",
    "business", "sponsor decision", "strategic", "administrative", "pi left",
    "investigator", "supply", "covid", "slow",
)


def classify(why: str) -> str:
    """Classify a whyStopped string. OPERATIONAL wins ties on purpose.

    'Insufficient accrual of population likely to benefit; progression in 6
    patients' contains both. Calling that SCIENTIFIC would overstate: the trial
    stopped because it could not recruit. A human should read it.
    """
    if not why:
        return "NO_REASON_GIVEN"
    w = why.lower()
    op = any(k in w for k in OPERATIONAL)
    sci = any(k in w for k in SCIENTIFIC)
    if op and sci:
        return "MIXED_NEEDS_HUMAN"
    if op:
        return "OPERATIONAL"
    if sci:
        return "SCIENTIFIC"
    return "UNCLEAR"


def query(drug: str, disease: str, page_size: int = 50) -> list[dict]:
    cond = disease.replace("_", " ")
    params = {
        "query.intr": drug, "query.cond": cond,
        "fields": "NCTId,BriefTitle,OverallStatus,WhyStopped,Phase,StartDate",
        "pageSize": str(page_size),
    }
    url = f"{API}?{urllib.parse.urlencode(params)}"
    try:
        with urllib.request.urlopen(url, timeout=45) as r:
            return json.loads(r.read().decode()).get("studies", [])
    except Exception as exc:                                  # pragma: no cover
        print(f"    ! query failed for {drug}/{disease}: {type(exc).__name__}")
        return []
    finally:
        time.sleep(0.4)                     # be polite to a public API


def summarise(studies: list[dict]) -> dict:
    status = Counter()
    stops = []
    for s in studies:
        p = s.get("protocolSection", {})
        st = p.get("statusModule", {})
        status[st.get("overallStatus", "?")] += 1
        why = st.get("whyStopped", "")
        if why:
            stops.append({
                "nct": p.get("identificationModule", {}).get("nctId", ""),
                "why": why,
                "class": classify(why),
                "title": p.get("identificationModule", {}).get("briefTitle", "")[:90],
            })
    sci = [s for s in stops if s["class"] == "SCIENTIFIC"]
    mixed = [s for s in stops if s["class"] == "MIXED_NEEDS_HUMAN"]
    return {
        "n_trials": len(studies),
        "status_counts": dict(status),
        "n_stopped_with_reason": len(stops),
        "n_scientific_stop": len(sci),
        "n_mixed_stop": len(mixed),
        "stops": stops,
        "verdict": ("NEGATIVE_EVIDENCE" if sci else
                    "NEEDS_HUMAN" if mixed else
                    "NO_NEGATIVE_SIGNAL" if studies else "NO_TRIALS_FOUND"),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--worklist", default="reports/horn_audit_2026-08-01/HORN_TOP50.csv")
    ap.add_argument("--out", default=None)
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    rows = list(csv.DictReader(open(REPO / args.worklist, encoding="utf-8-sig")))
    if args.limit:
        rows = rows[: args.limit]
    out_path = REPO / (args.out or
                       str(Path(args.worklist).parent / "TRIAL_HISTORY.json"))

    results = {}
    print(f"querying ClinicalTrials.gov for {len(rows)} pairs\n")
    for i, r in enumerate(rows, 1):
        drug, dis = r["drug_inn"], r["disease"]
        info = summarise(query(drug, dis))
        results[f"{drug}|{dis}"] = {
            "drug": drug, "disease": dis,
            "horn_rank": int(r["rank"]),
            "curated_status": r.get("status_APPROVED_TRIAL_PRECLIN_FAILED_NONE", ""),
            **info,
        }
        flag = {"NEGATIVE_EVIDENCE": "FAILED", "NEEDS_HUMAN": "mixed",
                "NO_NEGATIVE_SIGNAL": "", "NO_TRIALS_FOUND": "no trials"}[info["verdict"]]
        print(f"{i:>3}. {drug[:22]:<23}{dis:<22}{info['n_trials']:>4} trials  {flag}")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=1), encoding="utf-8")

    v = Counter(r["verdict"] for r in results.values())
    print(f"\nwrote {out_path}")
    print("\n=== SUMMARY ===")
    for k, n in v.most_common():
        print(f"  {k:<22}{n}")
    print("\nCross-check against the curated verdicts:")
    for r in results.values():
        if r["verdict"] == "NEGATIVE_EVIDENCE":
            print(f"  rank {r['horn_rank']:>2}  {r['drug']} -> {r['disease']}"
                  f"   (curated: {r['curated_status'] or 'unset'})")
            for s in r["stops"]:
                if s["class"] == "SCIENTIFIC":
                    print(f"        {s['nct']}: {s['why'][:88]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
