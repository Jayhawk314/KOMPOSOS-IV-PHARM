#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""Adjudicate frozen candidates against measured PRISM viability data.

Step 4 of `docs/PLAN_PRISM_ADJUDICATION_2026-08-14.md`. Runs ONLY against the
pre-registration committed in the preceding commit; every threshold, the
statistic, the correction and the verdict vocabulary come from that file and are
never recomputed here.

What this measures
------------------
**Selectivity, not potency.** A drug that kills every lineage is nonspecific
cytotoxicity; a drug that kills only the predicted lineage is signal. The
pan-lineage cytotoxicity check is the built-in negative control, and the
control panel in the pre-registration is the control on that control.

What this cannot support
------------------------
Cell lines are not patients. No verdict here is an efficacy claim in either
direction. Absence from the screen is recorded as absence, never as inactivity.
Every row carries `human_reviewed = 0`.

Labels, not features. Nothing in `oracle/`, `core/`, `validation/` or `data/`
may import this module.

Usage:
    python -m evidence.acquire_prism --download   # fetch raw files (~310 MB)
    python -m evidence.acquire_prism              # score against the freeze
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path
from statistics import median

from .prism_prereg import (
    PREREGISTRATION,
    PRIMARY_TREATMENTS,
    RAW,
    REPORT_DIR,
    SECONDARY_TREATMENTS,
    compound_index,
    sha256_of,
)
from .store import REPO

FIGSHARE_ARTICLE = "https://api.figshare.com/v2/articles/9393293"
OBSERVATIONS = REPORT_DIR / "PRISM_OBSERVATIONS.json"
PROVENANCE = REPORT_DIR / "PROVENANCE.json"

DOSE_RESPONSE = "secondary-screen-dose-response-curve-parameters.csv"
CELL_LINE_INFO = "secondary-screen-cell-line-info.csv"

#: Everything the adjudication reads. The two large matrices are gitignored
#: under data/external/; only distilled records are committed.
REQUIRED_FILES = [
    CELL_LINE_INFO,
    "primary-screen-cell-line-info.csv",
    SECONDARY_TREATMENTS,
    PRIMARY_TREATMENTS,
    DOSE_RESPONSE,
]

csv.field_size_limit(min(sys.maxsize, 2**31 - 1))

#: The dose-response table is 264 MB; the sensitivity analysis re-scores the
#: same rows under a different quality floor, so parsing is memoized.
_DOSE_RESPONSE_CACHE: dict[frozenset, tuple[dict, list[str]]] = {}


# --------------------------------------------------------------------------
# Acquisition
# --------------------------------------------------------------------------


def download(*, refresh: bool = False, verbose: bool = True) -> list[dict]:
    """Fetch raw PRISM files from figshare, recording URL, size and SHA-256.

    figshare rather than the DepMap portal: the portal serves a Cloudflare
    human-verification interstitial to automated clients.
    """
    RAW.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(FIGSHARE_ARTICLE, timeout=60) as response:
        article = json.loads(response.read())

    provenance: list[dict] = []
    by_name = {f["name"]: f for f in article["files"]}
    for name in REQUIRED_FILES:
        target = RAW / name
        remote = by_name[name]
        if target.exists() and not refresh:
            if verbose:
                print(f"  cached  {name}")
        else:
            if verbose:
                print(f"  fetching {name} ({remote['size'] / 1e6:.0f} MB)", flush=True)
            urllib.request.urlretrieve(remote["download_url"], target)
        provenance.append(
            {
                "file": name,
                "url": remote["download_url"],
                "bytes": target.stat().st_size,
                "sha256": sha256_of(target),
                "figshare_supplied_md5": remote.get("computed_md5", ""),
                "retrieved_at": datetime.now(timezone.utc).isoformat(),
            }
        )

    PROVENANCE.write_text(
        json.dumps(
            {
                "source": "PRISM Repurposing 19Q4",
                "doi": "10.6084/m9.figshare.9393293.v4",
                "citation": "Corsello et al., Nature Cancer 2020",
                "figshare_api": FIGSHARE_ARTICLE,
                "files": provenance,
            },
            indent=1,
        ),
        encoding="utf-8",
    )
    return provenance


# --------------------------------------------------------------------------
# Statistics - implemented explicitly so the frozen rule is auditable
# --------------------------------------------------------------------------


def mann_whitney_u(a: list[float], b: list[float]) -> tuple[float, float]:
    """Two-sided Mann-Whitney U with tie correction and a normal approximation.

    Returns (U, p). scipy is a declared dependency and is used when importable;
    the explicit fallback keeps the frozen statistic readable and testable.
    """
    try:
        from scipy.stats import mannwhitneyu

        result = mannwhitneyu(a, b, alternative="two-sided")
        return float(result.statistic), float(result.pvalue)
    except ImportError:  # pragma: no cover - scipy is a declared dependency
        pass

    import math

    combined = sorted([(v, 0) for v in a] + [(v, 1) for v in b])
    ranks: list[float] = [0.0] * len(combined)
    index = 0
    tie_term = 0.0
    while index < len(combined):
        stop = index
        while stop + 1 < len(combined) and combined[stop + 1][0] == combined[index][0]:
            stop += 1
        average = (index + stop) / 2.0 + 1.0
        for position in range(index, stop + 1):
            ranks[position] = average
        size = stop - index + 1
        tie_term += size**3 - size
        index = stop + 1

    rank_a = sum(r for r, (_, group) in zip(ranks, combined) if group == 0)
    n_a, n_b = len(a), len(b)
    u_a = rank_a - n_a * (n_a + 1) / 2.0
    mean = n_a * n_b / 2.0
    total = n_a + n_b
    variance = n_a * n_b * (total + 1 - tie_term / (total * (total - 1))) / 12.0
    if variance <= 0:
        return u_a, 1.0
    z = (abs(u_a - mean) - 0.5) / math.sqrt(variance)
    p = math.erfc(z / math.sqrt(2.0))
    return u_a, min(1.0, max(0.0, p))


def benjamini_hochberg(pvalues: list[float]) -> list[float]:
    """BH step-up adjusted q-values, order preserved."""
    total = len(pvalues)
    if total == 0:
        return []
    order = sorted(range(total), key=lambda i: pvalues[i])
    adjusted = [0.0] * total
    previous = 1.0
    for rank, index in enumerate(reversed(order), start=1):
        position = total - rank + 1
        value = min(previous, pvalues[index] * total / position)
        adjusted[index] = value
        previous = value
    return adjusted


# --------------------------------------------------------------------------
# Scoring
# --------------------------------------------------------------------------


def load_cell_lines() -> dict[str, dict]:
    with (RAW / CELL_LINE_INFO).open(encoding="utf-8") as handle:
        return {
            row["depmap_id"]: row
            for row in csv.DictReader(handle)
            if row["depmap_id"].startswith("ACH")
        }


def load_dose_response(broad_ids: set[str]) -> tuple[dict[str, list[dict]], list[str]]:
    """Stream the 264 MB parameter table, keeping only compounds of interest.

    Returns the rows and the file's actual column names. The columns matter:
    the dataset readme documents a `convergence` field that the shipped file
    does not contain, and the pre-registration requires it.
    """
    key = frozenset(broad_ids)
    if key in _DOSE_RESPONSE_CACHE:
        return _DOSE_RESPONSE_CACHE[key]

    wanted: dict[str, list[dict]] = {}
    with (RAW / DOSE_RESPONSE).open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = list(reader.fieldnames or [])
        for row in reader:
            broad_id = row.get("broad_id", "")
            if broad_id in broad_ids:
                wanted.setdefault(broad_id, []).append(row)
    _DOSE_RESPONSE_CACHE[key] = (wanted, fieldnames)
    return wanted, fieldnames


def _float(value: str) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return None if result != result else result  # drop NaN


def passes_quality(row: dict, thresholds: dict, *, has_convergence: bool = True) -> bool:
    """Frozen quality gate.

    `has_convergence` is False when the shipped file lacks the column the
    pre-registration requires. The requirement is then unenforceable rather
    than failing, and the waiver is recorded as a declared deviation - never
    applied silently. See `deviations` in the output.
    """
    if thresholds["require_curve_convergence"] and has_convergence:
        if (row.get("convergence") or "").strip().upper() != "TRUE":
            return False
    if thresholds["require_passed_str_profiling"]:
        if (row.get("passed_str_profiling") or "").strip().upper() != "TRUE":
            return False
    r2 = _float(row.get("r2", ""))
    if r2 is None or r2 < thresholds["curve_r2_floor"]:
        return False
    return _float(row.get("auc", "")) is not None


def select_screen(rows: list[dict], preference: list[str]) -> str:
    available = {row.get("screen_id", "") for row in rows}
    for screen in preference:
        if screen in available:
            return screen
    return sorted(available)[0] if available else ""


def in_target_lineage(line: dict, lineage: dict) -> bool:
    """Lineage membership by the correspondence, never by string similarity."""
    if line.get("primary_tissue") != lineage.get("primary_tissue"):
        return False
    secondary = lineage.get("secondary_tissue")
    if secondary is None:
        return True
    return line.get("secondary_tissue") == secondary


def measure(
    rows: list[dict],
    lineage: dict,
    cell_lines: dict[str, dict],
    thresholds: dict,
    preference: list[str],
    has_convergence: bool = True,
) -> dict:
    """One compound against one lineage. Returns raw measurement, no verdict."""
    screen = select_screen(rows, preference)
    usable = [
        row
        for row in rows
        if row.get("screen_id") == screen
        and row.get("depmap_id") in cell_lines
        and passes_quality(row, thresholds, has_convergence=has_convergence)
    ]

    target: list[float] = []
    other: list[float] = []
    for row in usable:
        auc = _float(row["auc"])
        line = cell_lines[row["depmap_id"]]
        (target if in_target_lineage(line, lineage) else other).append(auc)

    all_auc = target + other
    result = {
        "screen_id": screen,
        "n_rows_before_qc": len([r for r in rows if r.get("screen_id") == screen]),
        "n_target_lines": len(target),
        "n_other_lines": len(other),
        "median_auc_target": round(median(target), 4) if target else None,
        "median_auc_other": round(median(other), 4) if other else None,
        "median_auc_all_lineages": round(median(all_auc), 4) if all_auc else None,
        "selectivity_delta": None,
        "mannwhitney_u": None,
        "mannwhitney_p": None,
        "pan_lineage_cytotoxic": None,
    }
    if all_auc:
        result["pan_lineage_cytotoxic"] = bool(
            median(all_auc) < thresholds["pan_lineage_cytotoxic_max_median_auc"]
        )
    if len(target) >= 1 and len(other) >= 1:
        result["selectivity_delta"] = round(median(other) - median(target), 4)
        u, p = mann_whitney_u(target, other)
        result["mannwhitney_u"] = round(u, 2)
        result["mannwhitney_p"] = p
    return result


def run_control_panel(
    dose_response: dict[str, list[dict]],
    controls: dict[str, list[str]],
    cell_lines: dict[str, dict],
    thresholds: dict,
    preference: list[str],
    has_convergence: bool = True,
) -> dict:
    """The control on the control: is the cytotoxicity threshold itself sane?"""
    observed: dict[str, dict] = {}
    for name, broad_ids in controls.items():
        rows = [row for bid in broad_ids for row in dose_response.get(bid, [])]
        if not rows:
            observed[name] = {"screened": False}
            continue
        # Lineage is irrelevant for a pan-lineage question; use an empty
        # correspondence so every line counts as "other".
        stats = measure(
            rows, {"primary_tissue": None}, cell_lines, thresholds, preference,
            has_convergence,
        )
        observed[name] = {
            "screened": True,
            "median_auc_all_lineages": stats["median_auc_all_lineages"],
            "pan_lineage_cytotoxic": stats["pan_lineage_cytotoxic"],
            "n_lines": stats["n_other_lines"],
        }
    return observed


def score(r2_floor_override: float | None = None) -> dict:
    """Adjudicate the frozen set.

    `r2_floor_override` exists only for the sensitivity analysis reported
    alongside the headline. The headline result always uses the frozen floor.
    """
    prereg = json.loads(PREREGISTRATION.read_text(encoding="utf-8"))
    thresholds = dict(prereg["thresholds"])
    if r2_floor_override is not None:
        thresholds["curve_r2_floor"] = r2_floor_override
    preference = prereg["statistic"]["screen_preference"]
    cell_lines = load_cell_lines()

    scorable = [
        pair
        for pair in prereg["pairs"]
        if pair["stratum"] in ("TIER_A_HEADLINE", "TIER_B_UNDERPOWERED")
    ]
    broad_ids = {bid for pair in scorable for bid in pair["compound"]["broad_ids"]}

    secondary = compound_index(SECONDARY_TREATMENTS)
    control_names = (
        prereg["control_panel"]["expected_pan_lineage_cytotoxic"]
        + prereg["control_panel"]["expected_not_pan_lineage_cytotoxic"]
    )
    controls = {
        name: sorted(secondary[name]["broad_ids"])
        for name in control_names
        if name in secondary
    }
    broad_ids |= {bid for ids in controls.values() for bid in ids}

    dose_response, columns = load_dose_response(broad_ids)
    source_sha = sha256_of(RAW / DOSE_RESPONSE)

    # Declared deviations. A pre-registered rule that cannot be executed as
    # written is recorded here, never quietly dropped and never repaired by
    # editing the frozen file. This one was found in the file's header, before
    # any verdict was computed, which is what makes waiving it defensible.
    deviations: list[dict] = []
    has_convergence = "convergence" in columns
    if thresholds["require_curve_convergence"] and not has_convergence:
        deviations.append(
            {
                "pre_registered_rule": "require_curve_convergence = true",
                "status": "WAIVED_COLUMN_ABSENT",
                "found": (
                    "The shipped secondary-screen dose-response file has no "
                    "'convergence' column, although the dataset readme documents "
                    "one. Columns present: " + ", ".join(columns)
                ),
                "consequence_if_enforced": (
                    "100% of rows fail quality control and every pair returns "
                    "SCREENED_INCONCLUSIVE, which is not a measurement."
                ),
                "action": (
                    "Requirement treated as unenforceable. The r2 floor and the "
                    "STR-profiling requirement are still enforced."
                ),
                "discovered": "from the file header, before any verdict was computed",
                "declared_on": date.today().isoformat(),
            }
        )

    observations: list[dict] = []
    for pair in scorable:
        rows = [
            row
            for bid in pair["compound"]["broad_ids"]
            for row in dose_response.get(bid, [])
        ]
        record = {
            "review_id": pair["review_id"],
            "drug": pair["drug"],
            "disease": pair["disease"],
            "stratum": pair["stratum"],
            "prism_lineage": pair["prism_lineage"],
            "correspondence_type": pair["correspondence_type"],
            "broad_ids": pair["compound"]["broad_ids"],
            "endpoint": "dose_response_auc",
            "source_file": DOSE_RESPONSE,
            "source_sha256": source_sha,
            "human_reviewed": 0,
        }
        if not rows:
            record.update(
                {"verdict": "SCREENED_INCONCLUSIVE", "note": "no dose-response rows"}
            )
        else:
            record.update(
                measure(
                    rows, pair["prism_lineage"], cell_lines, thresholds, preference,
                    has_convergence,
                )
            )
        observations.append(record)

    # BH across TIER_A pairs that produced a p-value, per the frozen rule.
    tier_a = [
        obs
        for obs in observations
        if obs["stratum"] == "TIER_A_HEADLINE" and obs.get("mannwhitney_p") is not None
    ]
    for obs, q in zip(tier_a, benjamini_hochberg([o["mannwhitney_p"] for o in tier_a])):
        obs["bh_q"] = q

    for obs in observations:
        if "verdict" in obs:
            continue
        if obs["n_target_lines"] < thresholds["min_target_lines_after_qc"]:
            obs["verdict"] = "SCREENED_INCONCLUSIVE"
        elif obs["stratum"] == "TIER_B_UNDERPOWERED":
            obs["verdict"] = "UNDERPOWERED_REPORTED"
        elif obs.get("pan_lineage_cytotoxic"):
            obs["verdict"] = "PAN_LINEAGE_CYTOTOXIC"
        elif (
            obs.get("bh_q") is not None
            and obs["bh_q"] <= thresholds["bh_q_max"]
            and obs["selectivity_delta"] is not None
            and obs["selectivity_delta"] >= thresholds["selectivity_delta_min_auc"]
        ):
            obs["verdict"] = "LINEAGE_SELECTIVE_ACTIVITY"
        else:
            obs["verdict"] = "NO_LINEAGE_SELECTIVITY"

    # Unscorable strata carry the verdict the pre-registration already fixed.
    for pair in prereg["pairs"]:
        if pair["stratum"] in ("TIER_A_HEADLINE", "TIER_B_UNDERPOWERED"):
            continue
        observations.append(
            {
                "review_id": pair["review_id"],
                "drug": pair["drug"],
                "disease": pair["disease"],
                "stratum": pair["stratum"],
                "prism_lineage": pair["prism_lineage"],
                "correspondence_type": pair["correspondence_type"],
                "endpoint": None,
                "verdict": pair["predetermined_verdict"]
                or "SECONDARY_SINGLE_DOSE_ONLY_NOT_RUN",
                "human_reviewed": 0,
            }
        )

    control_results = run_control_panel(
        dose_response, controls, cell_lines, thresholds, preference, has_convergence
    )
    expected_toxic = prereg["control_panel"]["expected_pan_lineage_cytotoxic"]
    expected_clean = prereg["control_panel"]["expected_not_pan_lineage_cytotoxic"]
    toxic_fired = [
        n for n in expected_toxic if control_results.get(n, {}).get("pan_lineage_cytotoxic")
    ]
    clean_fired = [
        n for n in expected_clean if control_results.get(n, {}).get("pan_lineage_cytotoxic")
    ]
    control_valid = bool(toxic_fired) and len(clean_fired) < len(expected_clean)

    counts: dict[str, int] = {}
    for obs in observations:
        counts[obs["verdict"]] = counts.get(obs["verdict"], 0) + 1

    return {
        "_about": (
            "Measured PRISM adjudication of the frozen candidate set. Selectivity, "
            "not potency. Cell lines are not patients; no row is an efficacy claim."
        ),
        "scored_on": date.today().isoformat(),
        "preregistration_sha256": sha256_of(PREREGISTRATION),
        "prism_release": prereg["prism_release"],
        "prism_doi": prereg["prism_doi"],
        "control_panel": {
            "expected_pan_lineage_cytotoxic": expected_toxic,
            "expected_not_pan_lineage_cytotoxic": expected_clean,
            "observed": control_results,
            "valid": control_valid,
            "rule": prereg["control_panel"]["rule"],
        },
        "run_valid": control_valid,
        "curve_r2_floor_used": thresholds["curve_r2_floor"],
        "deviations": deviations,
        "verdict_counts": counts,
        "observations": observations,
    }


def load_observations() -> dict:
    """Return scored observations, or an empty result when scoring has not run.

    The build must not require network access, so a missing file is normal.
    """
    if not OBSERVATIONS.exists():
        return {"observations": [], "verdict_counts": {}, "run_valid": None}
    return json.loads(OBSERVATIONS.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Adjudicate candidates against PRISM")
    parser.add_argument("--download", action="store_true", help="fetch raw files first")
    parser.add_argument("--refresh", action="store_true", help="re-download raw files")
    args = parser.parse_args()

    if args.download or args.refresh:
        print("acquiring PRISM Repurposing 19Q4")
        download(refresh=args.refresh)
        print()

    missing = [name for name in REQUIRED_FILES if not (RAW / name).exists()]
    if missing:
        print("missing raw files; run with --download")
        for name in missing:
            print(f"  {name}")
        return 1

    report = score()

    # Sensitivity analysis. NOT the result: the headline is always the frozen
    # floor. This exists because the frozen r2 >= 0.5 keeps only about a quarter
    # of curves, and keeps them non-randomly - a flat curve (inactive compound,
    # resistant line) has low r2 by construction, so the filter preferentially
    # retains lines where the drug did something. Reporting how conclusions move
    # is honest; moving the frozen floor to get a better answer is not.
    report["sensitivity_analysis"] = {
        "_about": (
            "Alternative quality floors, reported for transparency. The "
            "pre-registered result is curve_r2_floor = "
            f"{report['curve_r2_floor_used']} and stands regardless of these."
        ),
        "runs": [
            {
                "curve_r2_floor": floor,
                "verdict_counts": score(r2_floor_override=floor)["verdict_counts"],
            }
            for floor in (0.0, 0.3)
        ],
    }

    OBSERVATIONS.write_text(json.dumps(report, indent=1), encoding="utf-8")
    print(f"wrote {OBSERVATIONS.relative_to(REPO)}")
    print()

    for deviation in report["deviations"]:
        print(f"DECLARED DEVIATION: {deviation['pre_registered_rule']}")
        print(f"  {deviation['status']} - {deviation['action']}")
        print()

    control = report["control_panel"]
    print(f"control panel valid: {control['valid']}")
    for name, observed in sorted(control["observed"].items()):
        if observed.get("screened"):
            print(
                f"  {name:14s} median AUC {observed['median_auc_all_lineages']}"
                f"  pan-cytotoxic {observed['pan_lineage_cytotoxic']}"
            )
    print()
    print(f"PRE-REGISTERED RESULT (curve_r2_floor = {report['curve_r2_floor_used']})")
    for verdict, count in sorted(report["verdict_counts"].items(), key=lambda kv: -kv[1]):
        print(f"  {count:3d}  {verdict}")

    print()
    print("sensitivity analysis - NOT the result, reported for transparency")
    for run in report["sensitivity_analysis"]["runs"]:
        summary = ", ".join(
            f"{count} {verdict}"
            for verdict, count in sorted(run["verdict_counts"].items(), key=lambda kv: -kv[1])
            if verdict in ("LINEAGE_SELECTIVE_ACTIVITY", "NO_LINEAGE_SELECTIVITY",
                           "PAN_LINEAGE_CYTOTOXIC", "SCREENED_INCONCLUSIVE",
                           "UNDERPOWERED_REPORTED")
        )
        print(f"  r2 >= {run['curve_r2_floor']}: {summary}")
    return 0 if report["run_valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
