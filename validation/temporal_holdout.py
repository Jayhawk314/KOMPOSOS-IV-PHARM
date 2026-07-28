#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""Temporal holdout validation for approved Drug->Disease labels.

Default approval years are a versioned local table for the current 44-label
benchmark. Pass --year-csv to override with an audited external table containing
columns: drug,disease,year.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from validation.holdout_utils import evaluate_holdout, print_metrics
from validation.repurposing_benchmark import DB_PATH, drug_disease_pairs, load_full_typed_view


VERSION = "2026-05-27"

APPROVAL_YEARS: dict[tuple[str, str], int] = {
    ("Afatinib", "NSCLC"): 2013,
    ("Alectinib", "NSCLC"): 2015,
    ("Atezolizumab", "NSCLC"): 2016,
    ("Bevacizumab", "Colorectal_Cancer"): 2004,
    ("Binimetinib", "Melanoma"): 2018,
    ("Cetuximab", "Colorectal_Cancer"): 2004,
    ("Cobimetinib", "Melanoma"): 2015,
    ("Crizotinib", "NSCLC"): 2011,
    ("Dabrafenib", "Melanoma"): 2013,
    ("Encorafenib", "Melanoma"): 2018,
    ("Erlotinib", "NSCLC"): 2004,
    ("Erlotinib", "Pancreatic_Cancer"): 2005,
    ("Everolimus", "RCC"): 2009,
    ("Gefitinib", "NSCLC"): 2003,
    ("Imatinib", "CML"): 2001,
    ("Imatinib", "GIST"): 2002,
    ("Ipilimumab", "Melanoma"): 2011,
    ("Lapatinib", "Breast_Cancer"): 2007,
    ("Metformin", "Type2_Diabetes"): 1995,
    ("Nivolumab", "Melanoma"): 2014,
    ("Nivolumab", "NSCLC"): 2015,
    ("Nivolumab", "RCC"): 2015,
    ("Olaparib", "Breast_Cancer"): 2018,
    ("Olaparib", "Ovarian_Cancer"): 2014,
    ("Osimertinib", "NSCLC"): 2015,
    ("Palbociclib", "Breast_Cancer"): 2015,
    ("Pembrolizumab", "Melanoma"): 2014,
    ("Pembrolizumab", "NSCLC"): 2015,
    ("Ramucirumab", "Colorectal_Cancer"): 2015,
    ("Regorafenib", "Colorectal_Cancer"): 2012,
    ("Regorafenib", "GIST"): 2013,
    ("Regorafenib", "HCC"): 2017,
    ("Ribociclib", "Breast_Cancer"): 2017,
    ("Ruxolitinib", "Myelofibrosis"): 2011,
    ("Sorafenib", "HCC"): 2007,
    ("Sorafenib", "RCC"): 2005,
    ("Sunitinib", "GIST"): 2006,
    ("Sunitinib", "RCC"): 2006,
    ("Temsirolimus", "RCC"): 2007,
    ("Thalidomide", "Multiple_Myeloma"): 2006,
    ("Trametinib", "Melanoma"): 2013,
    ("Trastuzumab", "Breast_Cancer"): 1998,
    ("Vemurafenib", "Melanoma"): 2011,
    ("Venetoclax", "CLL"): 2016,
}


def load_years(csv_path: str | None) -> dict[tuple[str, str], int]:
    if not csv_path:
        return dict(APPROVAL_YEARS)
    years: dict[tuple[str, str], int] = {}
    with open(csv_path, encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            years[(row["drug"], row["disease"])] = int(row["year"])
    return years


def main() -> int:
    parser = argparse.ArgumentParser(description="Run temporal Drug->Disease holdout validation.")
    parser.add_argument("--db", default=DB_PATH, help="Path to tier1 SQLite database.")
    parser.add_argument("--cutoff", type=int, default=2013, help="Hold out approvals after this year.")
    parser.add_argument(
        "--include-cutoff",
        action="store_true",
        help="Hold out approvals with year >= cutoff instead of year > cutoff.",
    )
    parser.add_argument("--year-csv", default=None, help="Optional audited approval year CSV.")
    args = parser.parse_args()

    base_category, _ = load_full_typed_view(args.db)
    drugs, diseases, positives = drug_disease_pairs(base_category)
    years = load_years(args.year_csv)

    missing = sorted(positives - set(years))
    if missing:
        raise SystemExit(f"Missing approval years for {len(missing)} labels: {missing}")

    if args.include_cutoff:
        heldout = {pair for pair in positives if years[pair] >= args.cutoff}
        policy = f"year >= {args.cutoff}"
    else:
        heldout = {pair for pair in positives if years[pair] > args.cutoff}
        policy = f"year > {args.cutoff}"

    if not heldout:
        raise SystemExit(f"No held-out labels for policy {policy}")

    train_category, _ = load_full_typed_view(args.db, skip_pairs=heldout)
    candidate_pairs = [(drug, disease) for drug in drugs for disease in diseases]
    metrics = evaluate_holdout(
        train_category,
        heldout,
        candidate_pairs,
        name=f"temporal_holdout_{policy.replace(' ', '')}_v{VERSION}",
        exclude_pairs=positives - heldout,
    )

    print(f"Version:    {VERSION}")
    print(f"Policy:     {policy}")
    print(f"Held out:   {len(heldout)} labels")
    print_metrics(metrics)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
