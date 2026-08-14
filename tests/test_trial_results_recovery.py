# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""Trial-results recovery must retrieve, never infer.

These tests run offline. The network path is exercised by
`python -m evidence.acquire_trial_results --refresh`, not by the suite.
"""
import hashlib
import json
import sqlite3
from pathlib import Path

import pytest

from evidence import EvidenceStore
from evidence.acquire_trial_results import (
    CACHE_DIR,
    DISPOSITION_LABELS,
    DISPOSITION_NO_DATA,
    DISPOSITION_ONGOING,
    DISPOSITION_RESULTS_CTG,
    DISPOSITION_RESULTS_PUBLICATION,
    DISPOSITION_UNRESOLVED,
    RECORDS_NAME,
    disposition_for,
    summarize_study,
    tracked_nct_ids,
)
from evidence.build import build_database

REPO = Path(__file__).resolve().parent.parent
TIER1 = REPO / "data/drugs/tier1.db"
RECORDS = CACHE_DIR / RECORDS_NAME


def record(**overrides):
    base = {
        "status": "COMPLETED",
        "has_results": False,
        "result_pmids": [],
        "derived_pmids": [],
        "enrollment_count": None,
        "enrollment_type": "",
    }
    base.update(overrides)
    return base


def test_posted_results_outrank_publication_as_a_recovery_source():
    assert disposition_for(record(has_results=True)) == DISPOSITION_RESULTS_CTG
    assert (
        disposition_for(record(has_results=True, result_pmids=["1"]))
        == DISPOSITION_RESULTS_CTG
    )


def test_publication_only_is_still_a_recovery():
    assert (
        disposition_for(record(derived_pmids=["9"])) == DISPOSITION_RESULTS_PUBLICATION
    )


def test_running_trials_are_not_holes():
    for status in ("RECRUITING", "ACTIVE_NOT_RECRUITING", "NOT_YET_RECRUITING"):
        assert disposition_for(record(status=status)) == DISPOSITION_ONGOING


def test_withdrawn_with_zero_actual_enrolment_generated_no_data():
    assert (
        disposition_for(
            record(status="WITHDRAWN", enrollment_type="ACTUAL", enrollment_count=0)
        )
        == DISPOSITION_NO_DATA
    )


def test_withdrawn_with_only_an_estimate_is_not_settled():
    """An estimated enrolment of zero proves nothing; do not close the search."""
    assert (
        disposition_for(
            record(status="WITHDRAWN", enrollment_type="ESTIMATED", enrollment_count=0)
        )
        == DISPOSITION_UNRESOLVED
    )


def test_completed_with_nothing_found_stays_unresolved_not_negative():
    """Absence of a result is never recorded as a negative result."""
    assert disposition_for(record(status="COMPLETED")) == DISPOSITION_UNRESOLVED


def test_summarize_extracts_registry_facts_without_judging_them():
    study = {
        "hasResults": True,
        "protocolSection": {
            "identificationModule": {"nctId": "NCT00000001", "briefTitle": "A trial"},
            "statusModule": {
                "overallStatus": "TERMINATED",
                "whyStopped": "Inadequate accrual rate",
            },
            "designModule": {"enrollmentInfo": {"count": 12, "type": "ACTUAL"}},
            "referencesModule": {
                "references": [
                    {"type": "RESULT", "pmid": "111"},
                    {"type": "BACKGROUND", "pmid": "222"},
                ]
            },
        },
        "resultsSection": {
            "outcomeMeasuresModule": {
                "outcomeMeasures": [{"title": "Overall Survival"}]
            },
            "participantFlowModule": {"groups": []},
        },
    }
    summary = summarize_study(study)
    assert summary["nct_id"] == "NCT00000001"
    assert summary["why_stopped"] == "Inadequate accrual rate"
    assert summary["enrollment_count"] == 12
    assert summary["result_pmids"] == ["111"]
    assert summary["background_pmids"] == ["222"]
    assert summary["outcome_measure_titles"] == ["Overall Survival"]
    # No efficacy field is produced at any point.
    assert not any("signal" in key or "efficac" in key for key in summary)


def test_records_file_is_committed_so_the_build_is_reproducible():
    """A gitignored cache would give two people different databases."""
    assert RECORDS.exists(), f"{RECORDS} must be committed, not cached"
    assert "reports" in RECORDS.parts and "external" not in RECORDS.parts


def test_every_tracked_trial_has_a_disposition():
    report = json.loads(RECORDS.read_text(encoding="utf-8"))
    expected = set(tracked_nct_ids())
    assert report["returned"] == len(expected)
    for nct, entry in report["records"].items():
        assert entry["disposition"], f"{nct} has no disposition"


@pytest.fixture(scope="module")
def rebuilt(tmp_path_factory):
    path = tmp_path_factory.mktemp("recovery") / "evidence.db"
    before = hashlib.sha256(TIER1.read_bytes()).hexdigest()
    build_database(path)
    after = hashlib.sha256(TIER1.read_bytes()).hexdigest()
    assert before == after, "recovering trial results changed the scored graph"
    return path


def test_recovered_outcomes_never_assert_an_efficacy_signal(rebuilt):
    with sqlite3.connect(rebuilt) as connection:
        rows = connection.execute(
            "SELECT result_signal, human_reviewed FROM outcomes "
            "WHERE endpoint = 'REGISTRY_RESULTS'"
        ).fetchall()
    assert rows, "expected recovered registry outcomes"
    for signal, human_reviewed in rows:
        assert signal == "RESULTS_AVAILABLE_NOT_ASSESSED"
        assert human_reviewed == 0, "automated retrieval is not human review"


def test_recovered_outcomes_carry_a_resolvable_receipt(rebuilt):
    with sqlite3.connect(rebuilt) as connection:
        missing = connection.execute(
            """SELECT COUNT(*) FROM outcomes o
                LEFT JOIN receipts r ON r.receipt_id = o.receipt_id
                WHERE o.endpoint = 'REGISTRY_RESULTS'
                  AND (r.receipt_id IS NULL OR r.url = '')"""
        ).fetchone()[0]
    assert missing == 0


def test_human_reviewed_pair_outcomes_are_untouched(rebuilt):
    """The 60 curated pair-level reviews must not be diluted by automation."""
    with sqlite3.connect(rebuilt) as connection:
        reviewed = connection.execute(
            "SELECT COUNT(*) FROM outcomes "
            "WHERE endpoint = 'PAIR_LEVEL_REVIEW' AND human_reviewed = 1"
        ).fetchone()[0]
    assert reviewed == 60


def test_every_stored_disposition_has_a_display_label(rebuilt):
    """A new disposition must not silently render as "not checked" in the UI."""
    with sqlite3.connect(rebuilt) as connection:
        stored = {
            row[0]
            for row in connection.execute(
                "SELECT DISTINCT results_disposition FROM studies"
            )
        }
    missing = stored - set(DISPOSITION_LABELS)
    assert not missing, f"no display label for {sorted(missing)}"


def test_ui_can_distinguish_unpublished_recovered_results(rebuilt):
    """The pair view needs publication state to flag invisible evidence."""
    store = EvidenceStore(rebuilt)
    evidence = store.get_pair_evidence("Dacomitinib", "Glioblastoma")
    unpublished = [
        study for study in evidence.studies
        if study.get("results_publication_state") == "NOT_PUBLISHED"
    ]
    assert unpublished, "expected registry results with no publication"
    for study in unpublished:
        assert study["results_url"], "an unpublished result needs a link to read it"
        assert study["results_disposition"] == DISPOSITION_RESULTS_CTG


def test_dispositions_reach_the_studies_table(rebuilt):
    with sqlite3.connect(rebuilt) as connection:
        unset = connection.execute(
            "SELECT COUNT(*) FROM studies WHERE results_disposition = 'NOT_ASSESSED'"
        ).fetchone()[0]
        recovered = connection.execute(
            "SELECT COUNT(*) FROM studies WHERE results_disposition = ?",
            (DISPOSITION_RESULTS_CTG,),
        ).fetchone()[0]
    assert unset == 0, "every tracked study should carry a disposition"
    assert recovered > 0
