#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""Top unfilled inner horns, as a checkable worklist.

An unfilled inner horn Lambda^2_1 is a composable spine

    Drug --mechanism--> X --driver_of/associated_with--> Disease

for which NO Drug --treats--> Disease edge exists. Filling it IS a repurposing
prediction. `oracle/horns.py` builds these; this script turns the highest-
confidence unfilled ones into a table a human can check row by row.

WHY THIS EXISTS
---------------
Measured 2026-08-01: horn-filling and the composition strategy are the SAME
computation (Spearman 1.0000, identical AUROC 0.9952 -- see
`oracle/horns_vs_composition.py`). The categorical framing adds vocabulary, not
capability. What it DOES add is a clean way to enumerate the unfilled cases,
which is the discovery surface.

Of the first 50 rows, 10 were already confirmed as real FDA approvals during the
2026-07-31 label curation -- and they sit at ranks 1, 5, 7, 8, 13, 16, 19, 25,
30, 31, i.e. scattered through the list rather than clustered at the top. That is
what makes the UNCHECKED remainder worth checking: those rows sit in the same
confidence band as the confirmed ones.

READING THE OUTPUT
------------------
* SALT FORMS ARE COLLAPSED. "Dacomitinib" and "Dacomitinib Anhydrous" are one
  hypothesis. The raw horn ranking double-counts them and inflates precision.
* `already_verified_real` marks rows confirmed against FDA sources. EXCLUDE
  these when computing precision on the remainder, or the number is circular.
* `terminal` distinguishes a directed `driver_of` hop from `associated_with`
  co-occurrence. They are not equally strong.
* Order is raw composite confidence. Nothing is reranked or filtered.

KNOWN FAILURE MODE, VISIBLE IN THE OUTPUT
-----------------------------------------
The ranking proposes hypotheses that were tried and FAILED, because nothing in
the graph records failure. EGFR inhibitors for Glioblastoma occupy five rows in
the top 50; erlotinib, gefitinib and afatinib all failed in GBM trials. This is
the sharpest available argument for ingesting negative clinical evidence
(terminated/negative ClinicalTrials.gov records) rather than more drugs or more
targets.

Run:
    python -m validation.build_horn_worklist
    python -m validation.build_horn_worklist --top 100
"""
from __future__ import annotations

import argparse
import csv
import os
import sys
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
os.chdir(REPO)

from validation.repurposing_benchmark import (           # noqa: E402
    DB_PATH, DEFAULT_EXCLUDE_PROVENANCE, load_full_typed_view,
)
from validation.nonobvious import normalize_drug_name    # noqa: E402
from oracle.horns import inner_horns, best_fillers       # noqa: E402

# Confirmed against FDA primary sources during the 2026-07-31/08-01 curation.
# Keyed on (normalized INN lowercased, disease node name).
VERIFIED = {
    ("gilteritinib", "AML"), ("adagrasib", "Colorectal_Cancer"),
    ("sotorasib", "Colorectal_Cancer"), ("cabozantinib", "HCC"),
    ("fedratinib", "Myelofibrosis"), ("bosutinib", "CML"), ("asciminib", "CML"),
    ("trastuzumab_deruxtecan", "Breast_Cancer"), ("imatinib", "Soft_Tissue_Sarcoma"),
    ("selpercatinib", "HCC"), ("selpercatinib", "GIST"),
    ("selpercatinib", "Prostate_Cancer"), ("larotrectinib", "Prostate_Cancer"),
    ("larotrectinib", "Pancreatic_Cancer"), ("dacomitinib", "NSCLC"),
    ("lorlatinib", "NSCLC"), ("brigatinib", "NSCLC"), ("amivantamab", "NSCLC"),
    ("avapritinib", "GIST"),
}

FIELDS = ["rank", "drug", "drug_inn", "disease", "composite", "via", "hop1",
          "hop2", "terminal", "already_verified_real",
          "status_APPROVED_TRIAL_PRECLIN_FAILED_NONE", "source_url", "checker_note"]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--db", default=DB_PATH)
    ap.add_argument("--top", type=int, default=50)
    ap.add_argument("--outdir", default=None)
    args = ap.parse_args()

    outdir = REPO / (args.outdir or f"reports/horn_audit_{date.today()}")
    outdir.mkdir(parents=True, exist_ok=True)

    cat, _ = load_full_typed_view(args.db, exclude_provenance=DEFAULT_EXCLUDE_PROVENANCE)
    horns = inner_horns(cat, a_type="Drug", c_type="Disease")
    unfilled = sorted((h for h in best_fillers(horns).values() if not h.filled_treats),
                      key=lambda h: -h.composite)

    seen, rows = set(), []
    for h in unfilled:
        key = (normalize_drug_name(h.a).lower(), h.c)
        if key in seen:
            continue                     # collapse salt/hydrate duplicates
        seen.add(key)
        rows.append({
            "rank": len(rows) + 1,
            "drug": h.a,
            "drug_inn": normalize_drug_name(h.a),
            "disease": h.c,
            "composite": round(h.composite, 4),
            "via": h.b,
            "hop1": h.f_name,
            "hop2": h.g_name,
            "terminal": "DIRECTED" if h.g_name != "associated_with" else "co-occurrence",
            "already_verified_real": "YES" if key in VERIFIED else "",
            "status_APPROVED_TRIAL_PRECLIN_FAILED_NONE": "",
            "source_url": "",
            "checker_note": "",
        })
        if len(rows) == args.top:
            break

    out = outdir / f"HORN_TOP{args.top}.csv"
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)

    n_ver = sum(1 for r in rows if r["already_verified_real"])
    n_dir = sum(1 for r in rows if r["terminal"] == "DIRECTED")
    print(f"unfilled inner horns (salt-collapsed pool): {len(unfilled)} raw")
    print(f"wrote {len(rows)} rows -> {out}\n")
    print(f"  already verified real : {n_ver}")
    print(f"  UNCHECKED remainder   : {len(rows) - n_ver}   <- the experiment")
    print(f"  directed terminal hop : {n_dir}/{len(rows)}")
    print(f"  diseases covered      : {len({r['disease'] for r in rows})}")
    print("\nCheck EVERY unchecked row, including implausible ones. Checking only")
    print("the plausible ones biases precision upward and makes the number useless.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
