#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""Freeze the PRISM adjudication before any outcome is read.

This module writes `reports/prism_2026-08-14/PREREGISTRATION.json`: the frozen
candidate set, every numeric threshold, the statistic, the multiplicity
correction, and the verdict vocabulary. It is step 2 of the execution order in
`docs/PLAN_PRISM_ADJUDICATION_2026-08-14.md`, and it must be COMMITTED before
`evidence/acquire_prism.py` exists.

Why it is safe to run before pre-registration
---------------------------------------------
It reads only metadata: the review CSV, the hand-written disease
correspondence, and PRISM's treatment-info tables (compound name, broad_id,
SMILES). It never opens a viability matrix or a dose-response parameter, so the
candidate set is frozen blind. `secondary-screen-dose-response-curve-parameters.csv`
must not be read here.

Nothing in this module may be imported by `oracle/`, `core/`, `validation/`, or
`data/`. PRISM is a label surface, not a feature source.

Usage:
    python -m evidence.prism_prereg
    python -m evidence.prism_prereg --check   # verify the frozen file still matches
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import date
from pathlib import Path

from .store import REPO

REVIEW = REPO / "reports/candidate_review_2026-08-01/CANDIDATE_REVIEW_60.csv"
REPORT_DIR = REPO / "reports/prism_2026-08-14"
CORRESPONDENCE = REPORT_DIR / "DISEASE_CORRESPONDENCE.json"
PREREGISTRATION = REPORT_DIR / "PREREGISTRATION.json"
RAW = REPO / "data/external/prism_repurposing_2026-08-14"

SECONDARY_TREATMENTS = "secondary-screen-replicate-collapsed-treatment-info.csv"
PRIMARY_TREATMENTS = "primary-screen-replicate-collapsed-treatment-info.csv"

#: Frozen decision thresholds. Chosen a priori on 2026-08-14 with no outcome
#: data in hand. A threshold that turns out badly chosen is a finding to report,
#: never a file to edit after scoring.
THRESHOLDS = {
    "tier_a_min_cell_lines": 15,
    "curve_r2_floor": 0.5,
    "require_curve_convergence": True,
    "require_passed_str_profiling": True,
    "min_target_lines_after_qc": 8,
    "pan_lineage_cytotoxic_max_median_auc": 0.80,
    "selectivity_delta_min_auc": 0.05,
    "bh_q_max": 0.10,
    "single_dose_pan_cytotoxic_max_median_logfold": -1.0,
    "single_dose_selectivity_delta_min_logfold": 0.25,
}

STATISTIC = {
    "primary_endpoint": "dose_response_auc",
    "primary_source": "secondary-screen-dose-response-curve-parameters.csv",
    "screen_preference": ["MTS010", "MTS006", "MTS005"],
    "screen_preference_rationale": (
        "The dataset readme recommends MTS010 where available; it post-dates the "
        "Corsello analysis and includes technical redos of 147 oncology "
        "compounds. The screen actually used is recorded on every row."
    ),
    "selectivity_delta": "median(AUC outside target lineage) - median(AUC in target lineage)",
    "delta_sign_convention": "positive means the target lineage is MORE sensitive",
    "test": "two-sided Mann-Whitney U, target lineage versus all other lineages",
    "test_rationale": "AUC is bounded and non-normal; a rank test makes no distributional assumption.",
    "multiplicity_correction": "Benjamini-Hochberg across the TIER_A_HEADLINE pairs only",
    "secondary_endpoint": "primary_screen_replicate_collapsed_logfold_change",
    "secondary_source": "primary-screen-replicate-collapsed-logfold-change.csv",
    "secondary_note": (
        "Single-dose only. Reported separately and never pooled with "
        "dose-response AUC results."
    ),
}

#: The control on the control. Pan-lineage cytotoxicity is the built-in negative
#: control; these expectations test whether the threshold itself is sane. If the
#: platinums do not trip it, the threshold is wrong and the run is INVALID -
#: which is a pre-registered outcome, not a licence to retune.
CONTROL_PANEL = {
    "expected_pan_lineage_cytotoxic": ["cisplatin", "carboplatin", "oxaliplatin"],
    "expected_not_pan_lineage_cytotoxic": ["cimetidine", "propranolol"],
    "rule": (
        "If none of the expected cytotoxics trips pan_lineage_cytotoxic, or if "
        "every expected non-cytotoxic trips it, the run is reported INVALID and "
        "the thresholds are reported as mis-chosen. Thresholds are not retuned."
    ),
}

VERDICTS = {
    "LINEAGE_SELECTIVE_ACTIVITY": "Target lineage more sensitive, BH q below threshold, and not pan-lineage cytotoxic.",
    "PAN_LINEAGE_CYTOTOXIC": "Broadly active across lineages. The built-in negative control fired; this disconfirms selectivity.",
    "NO_LINEAGE_SELECTIVITY": "Screened and fit, but no target-lineage preference.",
    "SCREENED_INCONCLUSIVE": "Too few target-lineage lines survived quality control.",
    "NOT_SCREENED_BIOLOGIC": "A small-molecule viability screen cannot test this agent.",
    "NOT_SCREENED_POST_DATING_RELEASE": "Approved after the 19Q4 release; absent for vintage reasons.",
    "NOT_SCREENED_UNKNOWN_REASON": "Absent from the library for reasons not established.",
    "NO_LINEAGE_CORRESPONDENCE": "No adjudication surface exists for this disease.",
    "UNDERPOWERED_REPORTED": "Tier B lineage; effect size reported, excluded from the headline.",
    "AMBIGUOUS_MATCH": "Name matched but structure disagreed; excluded rather than guessed.",
}

STRATA = [
    "TIER_A_HEADLINE",
    "TIER_B_UNDERPOWERED",
    "SECONDARY_SINGLE_DOSE_ONLY",
    "REFUSED_DRUG_NOT_SCREENED",
    "REFUSED_NO_CORRESPONDENCE",
]

#: Biologics a pooled small-molecule viability screen cannot test at all. This is
#: an assay-capability fact, not an absence-of-evidence inference.
BIOLOGICS = {"amivantamab", "ramucirumab", "beperminogene perplasmid"}


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _treatment_rows(name: str) -> list[dict]:
    with (RAW / name).open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def compound_index(filename: str) -> dict[str, dict]:
    """Map lowercased compound name to its broad_ids and distinct SMILES.

    Structure is carried so a name match can be verified rather than trusted. A
    lowercase string match alone is not a correspondence.
    """
    index: dict[str, dict] = {}
    for row in _treatment_rows(filename):
        name = (row.get("name") or "").strip()
        if not name:
            continue
        entry = index.setdefault(
            name.lower(), {"name": name, "broad_ids": set(), "smiles": set()}
        )
        if row.get("broad_id"):
            entry["broad_ids"].add(row["broad_id"])
        smiles = (row.get("smiles") or "").strip()
        if smiles and smiles.upper() != "NA":
            entry["smiles"].add(smiles)
    return index


def resolve_compound(drug: str, index: dict[str, dict]) -> dict | None:
    """Resolve a candidate drug to PRISM compound records, verifying structure."""
    entry = index.get(drug.strip().lower())
    if entry is None:
        return None
    # Salt and formulation batches legitimately share a name and differ by
    # broad_id suffix. Genuinely different structures under one name do not.
    return {
        "prism_name": entry["name"],
        "broad_ids": sorted(entry["broad_ids"]),
        "distinct_smiles": len(entry["smiles"]),
        "smiles": sorted(entry["smiles"])[:1],
        "structure_check": "OK" if len(entry["smiles"]) <= 1 else "AMBIGUOUS_MATCH",
    }


def not_screened_verdict(drug: str) -> str:
    if drug.strip().lower() in BIOLOGICS:
        return "NOT_SCREENED_BIOLOGIC"
    # Vintage versus library composition is asserted per compound at scoring
    # time against recorded approval dates, never from memory. Until then the
    # honest label is that the reason is not established.
    return "NOT_SCREENED_UNKNOWN_REASON"


def build_preregistration() -> dict:
    correspondence = json.loads(CORRESPONDENCE.read_text(encoding="utf-8"))
    by_disease = {d["pharm_disease"]: d for d in correspondence["diseases"]}

    secondary = compound_index(SECONDARY_TREATMENTS)
    primary = compound_index(PRIMARY_TREATMENTS)

    review = list(csv.DictReader(REVIEW.open(encoding="utf-8-sig")))
    pairs = []
    for row in review:
        drug, disease = row["drug"], row["disease"]
        entry = by_disease.get(disease)
        in_secondary = resolve_compound(drug, secondary)
        in_primary = resolve_compound(drug, primary)
        resolved = in_secondary or in_primary

        if entry is None or entry["correspondence_type"] == "REFUSED":
            stratum, verdict = "REFUSED_NO_CORRESPONDENCE", "NO_LINEAGE_CORRESPONDENCE"
        elif resolved is None:
            stratum, verdict = "REFUSED_DRUG_NOT_SCREENED", not_screened_verdict(drug)
        elif resolved["structure_check"] == "AMBIGUOUS_MATCH":
            stratum, verdict = "REFUSED_DRUG_NOT_SCREENED", "AMBIGUOUS_MATCH"
        elif in_secondary is None:
            stratum, verdict = "SECONDARY_SINGLE_DOSE_ONLY", None
        elif entry["power_tier"] == "B":
            stratum, verdict = "TIER_B_UNDERPOWERED", None
        else:
            stratum, verdict = "TIER_A_HEADLINE", None

        pairs.append(
            {
                "review_id": row["review_id"],
                "drug": drug,
                "disease": disease,
                "novelty_class": row["novelty_class"],
                "stratum": stratum,
                # Set now only for strata that can never be scored. Scorable
                # pairs carry null until the measurement is actually made.
                "predetermined_verdict": verdict,
                "prism_lineage": entry["prism_lineage"] if entry else None,
                "correspondence_type": entry["correspondence_type"] if entry else "REFUSED",
                "power_tier": entry["power_tier"] if entry else "none",
                "n_cell_lines": entry["n_cell_lines"] if entry else 0,
                "compound": resolved,
                "has_dose_response": in_secondary is not None,
            }
        )

    counts = {s: sum(1 for p in pairs if p["stratum"] == s) for s in STRATA}
    return {
        "_about": (
            "Pre-registration for the PRISM adjudication. Frozen before any "
            "viability or dose-response data was read. Nothing here may be "
            "edited after the commit that introduces it."
        ),
        "frozen_on": date.today().isoformat(),
        "plan": "docs/PLAN_PRISM_ADJUDICATION_2026-08-14.md",
        "correspondence_file": "reports/prism_2026-08-14/DISEASE_CORRESPONDENCE.json",
        "correspondence_sha256": sha256_of(CORRESPONDENCE),
        "review_file": "reports/candidate_review_2026-08-01/CANDIDATE_REVIEW_60.csv",
        "review_sha256": sha256_of(REVIEW),
        "prism_release": "PRISM Repurposing 19Q4",
        "prism_doi": "10.6084/m9.figshare.9393293.v4",
        "thresholds": THRESHOLDS,
        "statistic": STATISTIC,
        "control_panel": CONTROL_PANEL,
        "verdict_vocabulary": VERDICTS,
        "strata_counts": counts,
        "boundaries": [
            "Labels, not features. app.py is the only module that may import this.",
            "Absence is never scored as a negative.",
            "Cell lines are not patients; no result here supports an efficacy claim.",
            "Do not compute AUROC, AUPRC or a precision estimate against these labels.",
            "human_reviewed = 0 on every row; automated extraction is not review.",
        ],
        "pairs": pairs,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Freeze the PRISM adjudication")
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify the committed pre-registration still matches its inputs",
    )
    args = parser.parse_args()

    report = build_preregistration()
    serialized = json.dumps(report, indent=1)

    if args.check:
        if not PREREGISTRATION.exists():
            print("no pre-registration on disk")
            return 1
        existing = PREREGISTRATION.read_text(encoding="utf-8")
        if existing.strip() != serialized.strip():
            print("MISMATCH: the frozen pre-registration differs from its inputs")
            return 1
        print(f"pre-registration matches its inputs")
        print(f"  sha256 {sha256_of(PREREGISTRATION)}")
        return 0

    PREREGISTRATION.write_text(serialized, encoding="utf-8")
    print(f"froze {PREREGISTRATION.relative_to(REPO)}")
    print(f"  sha256 {sha256_of(PREREGISTRATION)}")
    print()
    for stratum, count in report["strata_counts"].items():
        print(f"  {count:3d}  {stratum}")
    ambiguous = [p for p in report["pairs"] if p["predetermined_verdict"] == "AMBIGUOUS_MATCH"]
    if ambiguous:
        print()
        print(f"structure-check failures: {len(ambiguous)}")
        for pair in ambiguous:
            print(f"  {pair['review_id']}  {pair['drug']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
