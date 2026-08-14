#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""PRISM Repurposing feasibility reconnaissance.

Answers one question: how much of the 60-candidate review can PRISM adjudicate
at all? The answer constrains every later design decision, so it is measured
before any schema is written.

WHY THIS CANNOT CONTAMINATE THE PRE-REGISTRATION
------------------------------------------------
This script reads only *metadata*: which compounds were screened, and which
lineage each cell line belongs to. It never opens a viability matrix, a
log-fold-change file, or a dose-response parameter. Coverage is therefore
knowable without seeing a single outcome, and freezing the candidate set after
running this is still a blind pre-registration.

Reading `secondary-screen-dose-response-curve-parameters.csv` WOULD contaminate
it. Do not add that here.

Raw inputs live under gitignored `data/external/`; this distilled report is
committed under `reports/` so the finding survives without the 1 GB download.

Usage:
    python reports/prism_2026-08-14/recon.py
"""
from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
RAW = REPO / "data/external/prism_repurposing_2026-08-14"
REVIEW = REPO / "reports/candidate_review_2026-08-01/CANDIDATE_REVIEW_60.csv"
OUT = Path(__file__).resolve().parent / "RECON_REPORT.json"

#: PRISM Repurposing 19Q4, Corsello et al. 2020 Nature Cancer.
#: Reachable without authentication; the DepMap portal itself is behind a
#: Cloudflare human-verification challenge, so figshare is the automatable route.
FIGSHARE_ARTICLE = "https://api.figshare.com/v2/articles/9393293"
DATASET_DOI = "10.6084/m9.figshare.9393293.v4"

#: Minimum cell lines in a target lineage for a lineage-selectivity contrast to
#: be worth calling a measurement. Below this the comparison is reported with an
#: explicit UNDERPOWERED label rather than discarded or quietly included.
TIER_A_MIN_LINES = 15


def _load(name: str) -> list[dict]:
    with (RAW / name).open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def compound_names(name: str) -> set[str]:
    """Distinct screened compound names, lowercased for matching only."""
    return {
        row["name"].strip().lower()
        for row in _load(name)
        if row.get("name", "").strip()
    }


def cell_lines() -> list[dict]:
    """Real cell lines only; control barcodes are dropped."""
    return [
        row
        for row in _load("secondary-screen-cell-line-info.csv")
        if row["depmap_id"].startswith("ACH")
    ]


def lineage_sizes(lines: list[dict]) -> dict[str, int]:
    return dict(Counter(row["primary_tissue"] for row in lines))


def build_report() -> dict:
    review = list(csv.DictReader(REVIEW.open(encoding="utf-8-sig")))
    secondary = compound_names("secondary-screen-replicate-collapsed-treatment-info.csv")
    primary = compound_names("primary-screen-replicate-collapsed-treatment-info.csv")
    lines = cell_lines()
    sizes = lineage_sizes(lines)

    haematological = sorted(
        tissue
        for tissue in sizes
        if any(
            key in tissue
            for key in ("haem", "hema", "blood", "lymph", "plasma", "myelo", "leuk")
        )
    )

    per_pair = []
    for row in review:
        drug = row["drug"].strip().lower()
        disease = row["disease"]
        in_secondary = drug in secondary
        in_primary = drug in primary
        per_pair.append(
            {
                "review_id": row["review_id"],
                "drug": row["drug"],
                "disease": disease,
                "novelty_class": row["novelty_class"],
                "drug_in_secondary_screen": in_secondary,
                "drug_in_primary_screen": in_primary,
            }
        )

    drugs = sorted({row["drug"] for row in review})
    return {
        "generated_on": date.today().isoformat(),
        "purpose": (
            "Feasibility only. Reads screened-compound names and cell-line "
            "lineages; never reads viability or dose-response data."
        ),
        "source": {
            "dataset": "PRISM Repurposing 19Q4",
            "doi": DATASET_DOI,
            "figshare_api": FIGSHARE_ARTICLE,
            "citation": "Corsello et al., Nature Cancer 2020",
            "note": (
                "Newer PRISM Repurposing Public releases are distributed only "
                "through the DepMap portal, which serves a Cloudflare "
                "human-verification interstitial to automated clients. The "
                "DepMap 24Q2 figshare deposit carries CRISPR and omics files "
                "but no Repurposing matrices. 19Q4 is the automatable release."
            ),
        },
        "screen_scale": {
            "primary_compounds": len(primary),
            "secondary_compounds": len(secondary),
            "cell_lines": len(lines),
            "lineages": len(sizes),
        },
        "lineage_sizes": dict(sorted(sizes.items(), key=lambda kv: -kv[1])),
        "tier_a_min_lines": TIER_A_MIN_LINES,
        "haematological_lineages_present": haematological,
        "candidate_drugs": {
            "total": len(drugs),
            "in_secondary_screen": sorted(d for d in drugs if d.lower() in secondary),
            "primary_screen_only": sorted(
                d for d in drugs if d.lower() in primary and d.lower() not in secondary
            ),
            "not_screened": sorted(
                d
                for d in drugs
                if d.lower() not in primary and d.lower() not in secondary
            ),
        },
        "pairs": per_pair,
    }


def main() -> int:
    report = build_report()
    OUT.write_text(json.dumps(report, indent=1), encoding="utf-8")

    scale = report["screen_scale"]
    print(f"PRISM Repurposing 19Q4 - {report['generated_on']}")
    print(
        f"  {scale['secondary_compounds']} dose-response compounds, "
        f"{scale['primary_compounds']} single-dose, "
        f"{scale['cell_lines']} cell lines, {scale['lineages']} lineages"
    )
    haem = report["haematological_lineages_present"]
    print(f"  haematological lineages: {haem if haem else 'NONE'}")

    drugs = report["candidate_drugs"]
    print()
    print(f"candidate drugs: {drugs['total']}")
    print(f"  {len(drugs['in_secondary_screen']):3d}  dose-response screened")
    print(f"  {len(drugs['primary_screen_only']):3d}  single-dose only")
    print(f"  {len(drugs['not_screened']):3d}  not screened at all")
    print()
    print(f"wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
