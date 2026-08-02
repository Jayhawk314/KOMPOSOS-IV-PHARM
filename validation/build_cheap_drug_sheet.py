#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""Cheap approved drugs with a mechanistic case for a cancer they are not used for.

THIS IS THE PRODUCT. Everything else in validation/ measures whether the ranking
works; this asks the question the project exists to answer.

WHY THE USUAL YARDSTICK IS WRONG HERE
-------------------------------------
The top-50 horn audit was adjudicated by asking "did the FDA approve this?" and
rows that failed were counted as misses. For a generic drug that question is
close to meaningless: nobody will ever fund an FDA approval for aspirin in
colorectal cancer, because there is no patent and therefore no sponsor. The
approval will never arrive however strong the evidence gets.

So a generic drug with a solid mechanism and no approval is not a failed
prediction. It is the intended output.

WHAT THE SHEET SHOWS
--------------------
Every unfilled inner horn -- Drug -> target -> Disease with no `treats` edge --
scored on two axes that are independent of each other:

  MECHANISM   does the chain end in a directed `driver_of` edge, or only in
              `associated_with` literature co-occurrence? Directed is far
              stronger. The current graph has 60 directed terminal edges.

  ATTENTION   how many PubMed papers mention this drug and this disease
              together. Queried live, NOT derived from the graph, because
              deriving novelty from the same graph that produced the ranking
              would be circular. A textbook pair returns thousands; an
              unexamined pair returns zero.

The target zone is DIRECTED MECHANISM + LOW ATTENTION: a real mechanistic route
that nobody has written about.

CALIBRATION - READ THIS BEFORE TRUSTING A ROW
---------------------------------------------
Two rows near the top are Aspirin -> Colorectal_Cancer and Celecoxib ->
Colorectal_Cancer, both through COX2 on directed edges. Both are real, famous,
and supported by decades of evidence. That is the point: the method recovers the
best-known cheap-drug findings in oncology by mechanism alone, which is the
reason to take the unfamiliar rows seriously.

It is also the reason to be careful. Low attention can mean unexamined, OR tried
and never published, OR an ambiguous drug name. This is a reading queue, not a
result.

Run:
    python -m validation.build_cheap_drug_sheet
    python -m validation.build_cheap_drug_sheet --offline     # skip PubMed
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
os.chdir(REPO)

from validation.repurposing_benchmark import (            # noqa: E402
    DB_PATH, DEFAULT_EXCLUDE_PROVENANCE, load_full_typed_view,
)
from validation.nonobvious import (                       # noqa: E402
    normalize_drug_name, pubmed_comentions, _load_cache, _save_cache,
)
from oracle.horns import inner_horns, best_fillers        # noqa: E402
from validation.direction_filter import (                 # noqa: E402
    load_edges, check as direction_check, REJECT as DIR_REJECT,
)

# Drugs that are off-patent and cheap. Hand-marked because no field in the graph
# records it and it materially changes how a row should be read. Absence of a
# mark means UNKNOWN, not "expensive".
CHEAP = {
    "aspirin", "metformin", "atorvastatin", "simvastatin", "propranolol",
    "doxycycline", "itraconazole", "mebendazole", "albendazole", "disulfiram",
    "chloroquine", "hydroxychloroquine", "celecoxib", "thalidomide",
    "valproic acid", "valproic_acid", "nitroglycerin", "cimetidine",
    "ivermectin", "niclosamide", "ritonavir", "auranofin", "verapamil",
    "methotrexate", "cisplatin", "carboplatin", "oxaliplatin", "doxorubicin",
    "etoposide", "daunorubicin", "idarubicin", "fluorouracil", "capecitabine",
    "cyclophosphamide", "tamoxifen", "letrozole", "anastrozole", "bicalutamide",
    "imatinib", "gemcitabine", "paclitaxel", "docetaxel", "vincristine",
    "hydroxyurea", "azacitidine", "decitabine", "dexamethasone", "prednisone",
    "spironolactone", "digoxin", "metronidazole", "clarithromycin",
}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--db", default=DB_PATH)
    ap.add_argument("--offline", action="store_true",
                    help="skip PubMed; mechanism columns only")
    ap.add_argument("--outdir", default=None)
    args = ap.parse_args()

    outdir = REPO / (args.outdir or f"reports/cheap_drug_sheet_{date.today()}")
    outdir.mkdir(parents=True, exist_ok=True)

    cat, _ = load_full_typed_view(args.db, exclude_provenance=DEFAULT_EXCLUDE_PROVENANCE)
    horns = inner_horns(cat, a_type="Drug", c_type="Disease")
    unfilled = [h for h in best_fillers(horns).values() if not h.filled_treats]
    unfilled.sort(key=lambda h: (h.g_name == "associated_with", -h.composite))

    # Direction check. A drug that ACTIVATES a protein driving the cancer would
    # be expected to worsen it -- estrogens for ER-driven breast cancer, androgens
    # for AR-driven prostate cancer. Sign errors are excluded outright, not
    # down-weighted.
    _types, _drug_rel, _term_rel = load_edges(args.db)

    cache = _load_cache()
    seen, rows = set(), []
    n_sign_rejected = 0
    for i, h in enumerate(unfilled, 1):
        inn = normalize_drug_name(h.a)
        key = (inn.lower(), h.c)
        if key in seen:
            continue                        # collapse salt/hydrate forms
        seen.add(key)
        _v, _why = direction_check(h.a, h.b, h.c, _drug_rel, _term_rel, _types)
        if _v == DIR_REJECT:
            n_sign_rejected += 1
            continue
        comention = None
        drug_cancer = None
        if not args.offline:
            comention = pubmed_comentions(h.a, h.c, cache)
            # SECOND ATTENTION AXIS, added 2026-08-01 after the first version
            # misled. "0 papers on mebendazole + kidney cancer" looked like an
            # untouched idea; mebendazole actually has hundreds of cancer papers
            # and active glioblastoma trials. Counting only the drug-disease
            # pair cannot tell "nobody has thought about this drug" apart from
            # "well-known candidate, this particular cancer untested". Those are
            # completely different products and were mixed together.
            drug_cancer = pubmed_comentions(h.a, "cancer", cache)
            if i % 60 == 0:
                _save_cache(cache)
                print(f"  ...{i}/{len(unfilled)} queried", flush=True)
        rows.append({
            "drug": h.a,
            "drug_inn": inn,
            "disease": h.c,
            "mechanism_target": h.b,
            "terminal_relation": h.g_name,
            "mechanism_strength": "DIRECTED" if h.g_name != "associated_with" else "co-occurrence",
            "composite_confidence": round(h.composite, 4),
            "pubmed_comentions": "" if comention is None else comention,
            "pubmed_drug_in_cancer": "" if drug_cancer is None else drug_cancer,
            "novelty_class": "",
            "known_cheap_generic": "YES" if inn.lower() in CHEAP else "",
            "any_trial_or_paper_found": "",
            "verdict_WORTH_READING_TRIED_WRONG": "",
            "direction": _v,
            "checker_note": "",
        })
    if not args.offline:
        _save_cache(cache)

    # The target zone: real mechanism, nobody looking.
    # Two attention axes give three genuinely different kinds of candidate.
    for r in rows:
        pair, drug = r["pubmed_comentions"], r["pubmed_drug_in_cancer"]
        if pair == "" or drug == "":
            r["novelty_class"] = ""
        elif int(drug) <= 50:
            # Nobody has looked at this drug in cancer AT ALL.
            r["novelty_class"] = "UNEXPLORED_DRUG"
        elif int(pair) <= 25:
            # Known cancer-repurposing candidate; this cancer untested.
            r["novelty_class"] = "KNOWN_DRUG_NEW_CANCER"
        else:
            r["novelty_class"] = "WELL_STUDIED_PAIR"
    def zone(r):
        c = r["pubmed_comentions"]
        if r["mechanism_strength"] != "DIRECTED" or c == "":
            return ""
        return "TARGET_ZONE" if int(c) <= 25 else ""
    for r in rows:
        r["target_zone"] = zone(r)

    out = outdir / "CHEAP_DRUG_CANDIDATES.csv"
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    directed = [r for r in rows if r["mechanism_strength"] == "DIRECTED"]
    cheap = [r for r in rows if r["known_cheap_generic"]]
    tz = [r for r in rows if r.get("target_zone")]
    import collections as _c
    print("  novelty classes:", dict(_c.Counter(r["novelty_class"] for r in rows if r["novelty_class"])))
    print(f"\nwrote {len(rows)} candidate pairs -> {out}")
    print(f"  with a DIRECTED mechanism        : {len(directed)}")
    print(f"  known cheap generic drug         : {len(cheap)}")
    print(f"  >>> TARGET ZONE (directed + <=25 papers): {len(tz)}")
    if tz:
        print(f"\n{'drug':<24}{'disease':<20}{'via':<10}{'papers':>7}{'  cheap'}")
        print("-" * 74)
        for r in sorted(tz, key=lambda r: (int(r['pubmed_comentions']), -r['composite_confidence']))[:30]:
            print(f"{r['drug_inn'][:23]:<24}{r['disease']:<20}{r['mechanism_target'][:9]:<10}"
                  f"{r['pubmed_comentions']:>7}  {r['known_cheap_generic']}")
    print("\nLow paper count can mean unexamined, tried-and-unpublished, or an")
    print("ambiguous drug name. This is a reading queue, not a result.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
