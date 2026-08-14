# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""Tests for the PRISM adjudication surface.

Offline by construction: nothing here touches the network or the 264 MB raw
dose-response file. Statistics and verdict logic run against small fixtures.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from evidence import acquire_prism, prism_prereg

REPO = Path(__file__).resolve().parents[1]
REPORT_DIR = REPO / "reports/prism_2026-08-14"
SCORED_PACKAGES = ("oracle", "core", "validation", "data", "komposos_kg")


# ---------------------------------------------------------------------------
# The boundary: labels, not features
# ---------------------------------------------------------------------------


def test_no_scored_path_module_imports_prism():
    """PRISM must never reach the ranker.

    The moment measured viability feeds scoring, it is destroyed as an
    independent test of the ranker and the project loses its only route to an
    honest external number. app.py is the only permitted importer.
    """
    offenders = []
    for package in SCORED_PACKAGES:
        root = REPO / package
        if not root.is_dir():
            continue
        for path in root.rglob("*.py"):
            text = path.read_text(encoding="utf-8", errors="ignore")
            if "acquire_prism" in text or "prism_observations" in text:
                offenders.append(str(path.relative_to(REPO)))
    assert offenders == [], (
        "PRISM is a label surface, not a feature source; these scored-path "
        f"modules reference it: {offenders}"
    )


def test_evidence_build_is_the_only_importer_outside_app():
    """Within evidence/, only the build and the acquirer may read observations."""
    permitted = {"build.py", "acquire_prism.py", "prism_prereg.py"}
    offenders = [
        path.name
        for path in (REPO / "evidence").glob("*.py")
        if path.name not in permitted
        and "acquire_prism" in path.read_text(encoding="utf-8", errors="ignore")
    ]
    assert offenders == []


# ---------------------------------------------------------------------------
# The pre-registration is frozen
# ---------------------------------------------------------------------------


def test_preregistration_exists_and_pins_its_inputs():
    prereg = json.loads((REPORT_DIR / "PREREGISTRATION.json").read_text(encoding="utf-8"))
    assert prereg["correspondence_sha256"] == prism_prereg.sha256_of(
        REPORT_DIR / "DISEASE_CORRESPONDENCE.json"
    ), "the frozen pre-registration no longer matches the correspondence it pinned"
    assert prereg["frozen_on"] <= prereg.get("frozen_on")
    for key in ("curve_r2_floor", "bh_q_max", "pan_lineage_cytotoxic_max_median_auc"):
        assert key in prereg["thresholds"]


def test_refused_diseases_have_no_lineage():
    """A refusal must never carry a lineage; that is how a silent join starts."""
    correspondence = json.loads(
        (REPORT_DIR / "DISEASE_CORRESPONDENCE.json").read_text(encoding="utf-8")
    )
    for disease in correspondence["diseases"]:
        if disease["correspondence_type"] == "REFUSED":
            assert disease["prism_lineage"] is None
            assert disease["n_cell_lines"] == 0
        else:
            assert disease["prism_lineage"] is not None
            assert disease["justification"]
            assert disease["known_discrepancy"]


def test_gist_is_refused_not_joined_to_gastric():
    """GIST and gastric adenocarcinoma are different cells of origin."""
    correspondence = json.loads(
        (REPORT_DIR / "DISEASE_CORRESPONDENCE.json").read_text(encoding="utf-8")
    )
    gist = next(d for d in correspondence["diseases"] if d["pharm_disease"] == "GIST")
    assert gist["correspondence_type"] == "REFUSED"
    assert gist["prism_lineage"] is None


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------


def test_mann_whitney_separates_clearly_different_groups():
    _, p = acquire_prism.mann_whitney_u([0.1] * 8, [0.9] * 8)
    assert p < 0.01


def test_mann_whitney_finds_nothing_in_identical_groups():
    _, p = acquire_prism.mann_whitney_u([0.5] * 8, [0.5] * 8)
    assert p > 0.5


def test_benjamini_hochberg_is_monotone_and_never_below_raw_p():
    raw = [0.001, 0.01, 0.04, 0.2, 0.9]
    adjusted = acquire_prism.benjamini_hochberg(raw)
    assert all(q >= p - 1e-12 for p, q in zip(raw, adjusted))
    assert adjusted == sorted(adjusted)


def test_benjamini_hochberg_handles_empty_input():
    assert acquire_prism.benjamini_hochberg([]) == []


# ---------------------------------------------------------------------------
# Quality gate and lineage membership
# ---------------------------------------------------------------------------


THRESHOLDS = {
    "curve_r2_floor": 0.5,
    "require_curve_convergence": True,
    "require_passed_str_profiling": True,
}


def _row(**overrides):
    row = {"r2": "0.9", "auc": "0.8", "convergence": "TRUE", "passed_str_profiling": "TRUE"}
    row.update(overrides)
    return row


def test_quality_gate_rejects_low_r2_and_failed_str():
    assert acquire_prism.passes_quality(_row(), THRESHOLDS)
    assert not acquire_prism.passes_quality(_row(r2="0.2"), THRESHOLDS)
    assert not acquire_prism.passes_quality(_row(passed_str_profiling="FALSE"), THRESHOLDS)
    assert not acquire_prism.passes_quality(_row(auc="NA"), THRESHOLDS)


def test_absent_convergence_column_is_waived_not_silently_failed():
    """The shipped file has no `convergence` column though the readme claims one.

    Enforcing it would fail 100% of rows. The waiver is declared in the output;
    here we only check it does not silently zero the dataset.
    """
    row = _row()
    del row["convergence"]
    assert not acquire_prism.passes_quality(row, THRESHOLDS)
    assert acquire_prism.passes_quality(row, THRESHOLDS, has_convergence=False)


@pytest.mark.parametrize(
    "line,lineage,expected",
    [
        ({"primary_tissue": "kidney", "secondary_tissue": ""},
         {"primary_tissue": "kidney", "secondary_tissue": None}, True),
        ({"primary_tissue": "gastric", "secondary_tissue": "gastric_adenocarcinoma"},
         {"primary_tissue": "kidney", "secondary_tissue": None}, False),
        ({"primary_tissue": "central_nervous_system", "secondary_tissue": "medulloblastoma"},
         {"primary_tissue": "central_nervous_system", "secondary_tissue": "glioma"}, False),
        ({"primary_tissue": "central_nervous_system", "secondary_tissue": "glioma"},
         {"primary_tissue": "central_nervous_system", "secondary_tissue": "glioma"}, True),
    ],
)
def test_lineage_membership_requires_exact_correspondence(line, lineage, expected):
    assert acquire_prism.in_target_lineage(line, lineage) is expected


def test_screen_preference_is_honoured_then_falls_back():
    rows = [{"screen_id": "HTS002"}, {"screen_id": "MTS010"}]
    assert acquire_prism.select_screen(rows, ["MTS010", "MTS006"]) == "MTS010"
    assert acquire_prism.select_screen([{"screen_id": "HTS002"}], ["MTS010"]) == "HTS002"
    assert acquire_prism.select_screen([], ["MTS010"]) == ""


# ---------------------------------------------------------------------------
# Scored output, if it has been produced
# ---------------------------------------------------------------------------


def _observations():
    path = REPORT_DIR / "PRISM_OBSERVATIONS.json"
    if not path.exists():
        pytest.skip("PRISM scoring has not been run in this checkout")
    return json.loads(path.read_text(encoding="utf-8"))


def test_every_observation_is_unreviewed_and_has_a_known_verdict():
    report = _observations()
    prereg = json.loads((REPORT_DIR / "PREREGISTRATION.json").read_text(encoding="utf-8"))
    known = set(prereg["verdict_vocabulary"]) | {"SECONDARY_SINGLE_DOSE_ONLY_NOT_RUN"}
    for observation in report["observations"]:
        assert observation["human_reviewed"] == 0, "automated extraction is not review"
        assert observation["verdict"] in known, observation["verdict"]


def test_selectivity_claims_require_the_right_direction_and_significance():
    """A significant result in the wrong direction is not selective activity."""
    report = _observations()
    prereg = json.loads((REPORT_DIR / "PREREGISTRATION.json").read_text(encoding="utf-8"))
    thresholds = prereg["thresholds"]
    for observation in report["observations"]:
        if observation["verdict"] != "LINEAGE_SELECTIVE_ACTIVITY":
            continue
        assert observation["selectivity_delta"] >= thresholds["selectivity_delta_min_auc"]
        assert observation["bh_q"] <= thresholds["bh_q_max"]
        assert observation["pan_lineage_cytotoxic"] is False


def test_refused_pairs_are_never_scored_as_negative():
    """Absence is not evidence of inactivity."""
    report = _observations()
    inactive_verdicts = {"NO_LINEAGE_SELECTIVITY", "PAN_LINEAGE_CYTOTOXIC"}
    for observation in report["observations"]:
        if observation["stratum"].startswith("REFUSED"):
            assert observation["verdict"] not in inactive_verdicts
            assert observation.get("endpoint") in (None, "")


def test_declared_deviations_are_recorded_rather_than_hidden():
    report = _observations()
    for deviation in report["deviations"]:
        assert deviation["status"] == "WAIVED_COLUMN_ABSENT"
        assert deviation["pre_registered_rule"]
        assert deviation["consequence_if_enforced"]
