import csv
import hashlib
import json
import sqlite3
from pathlib import Path

import pytest

from evidence import EvidenceStore
from evidence.build import REVIEW_SHEET, build_database


REPO = Path(__file__).resolve().parent.parent
TIER1 = REPO / "data/drugs/tier1.db"


@pytest.fixture(scope="module")
def evidence_db(tmp_path_factory):
    path = tmp_path_factory.mktemp("evidence") / "evidence.db"
    before = hashlib.sha256(TIER1.read_bytes()).hexdigest()
    counts = build_database(path)
    after = hashlib.sha256(TIER1.read_bytes()).hexdigest()
    assert before == after, "building contextual evidence changed the scored graph"
    assert counts == {
        "receipts": 148,
        "claims": 60,
        "candidate_reviews": 60,
        "studies": 77,
        "study_roles": 3237,
        # 141 human-reviewed and registry-record outcomes, plus 19 recovered
        # registry-results outcomes from evidence/acquire_trial_results.py.
        # Recovered rows are RESULTS_AVAILABLE_NOT_ASSESSED / human_reviewed=0
        # and are asserted separately in tests/test_trial_results_recovery.py.
        "outcomes": 160,
        "claim_evidence": 179,
        "review_events": 60,
    }
    return path


def test_all_candidate_review_dimensions_round_trip_losslessly(evidence_db):
    with REVIEW_SHEET.open(encoding="utf-8-sig", newline="") as handle:
        expected = {row["review_id"]: row for row in csv.DictReader(handle)}
    with sqlite3.connect(evidence_db) as connection:
        actual = {
            review_id: json.loads(raw_json)
            for review_id, raw_json in connection.execute(
                "SELECT review_id, raw_json FROM candidate_reviews"
            )
        }
    assert actual == expected


@pytest.mark.parametrize(
    "drug,disease,state,testing,signal",
    [
        ("Cimetidine", "RCC", "TESTED_MIXED", "COMPLETED_SMALL_TRIALS", "MIXED"),
        ("Suramin", "RCC", "TESTED_INACTIVE_PUBLISHED", "COMPLETED_PHASE_2", "NEGATIVE"),
        ("Dacomitinib", "Glioblastoma", "TESTED_INACTIVE_PUBLISHED", "COMPLETED_PHASE_2", "NEGATIVE"),
        ("Amivantamab", "Glioblastoma", "ACTIVE_TRIAL_NO_RESULT", "RECRUITING_PHASE_1", "NOT_AVAILABLE"),
    ],
)
def test_decisive_pairs_remain_distinct(evidence_db, drug, disease, state, testing, signal):
    evidence = EvidenceStore(evidence_db).get_pair_evidence(drug, disease)
    assert evidence.reviewed
    review = evidence.reviews[0]
    assert review["evidence_state"] == state
    assert review["human_testing_status"] == testing
    assert review["result_signal"] == signal


def test_active_trial_is_not_rendered_as_negative(evidence_db):
    evidence = EvidenceStore(evidence_db).get_pair_evidence(
        "Amivantamab", "Glioblastoma"
    )
    assert evidence.active_studies
    assert evidence.reviews[0]["negative_evidence_found"] == "NO"
    assert evidence.reviews[0]["result_signal"] == "NOT_AVAILABLE"


def test_category_error_and_biomarker_context_are_preserved(evidence_db):
    store = EvidenceStore(evidence_db)
    category_error = store.get_pair_evidence("Cisplatin", "Li_Fraumeni_Syndrome")
    assert category_error.reviews[0]["candidate_assessment"] == "EXCLUDE_CATEGORY_ERROR"
    biomarker = store.get_pair_evidence("Sotorasib", "Melanoma")
    assert biomarker.reviews[0]["result_signal"] == "BIOMARKER_DEPENDENT"
    assert biomarker.reviews[0]["candidate_assessment"] == "EXCLUDE_DISEASE_LEVEL_ROUTE"


def test_real_candidate_does_not_repair_an_invalid_graph_receipt(evidence_db):
    evidence = EvidenceStore(evidence_db).get_pair_evidence("Cabozantinib", "GIST")
    review = evidence.reviews[0]
    assert review["result_signal"] == "POSITIVE_WITH_LIMITATIONS"
    assert review["candidate_assessment"] == "REAL_CANDIDATE_BAD_GRAPH_RECEIPT"
    assert [(r["external_id"], r["relevance_assessment"])
            for r in evidence.unresolved_receipts] == [("23177518", "UNRESOLVED")]


def test_unreviewed_pair_is_unknown_not_negative(evidence_db):
    evidence = EvidenceStore(evidence_db).get_pair_evidence("Aspirin", "RCC")
    assert not evidence.reviewed
    assert evidence.reviews == ()
    assert evidence.outcomes == ()


def test_fts_finds_reviewed_negative_and_active_trial_states(evidence_db):
    store = EvidenceStore(evidence_db)
    negative = store.search("suramin RCC inactive")
    assert any(row["record_id"] == "R46" for row in negative)
    active = store.search("amivantamab glioblastoma recruiting")
    assert any(row["record_id"] == "R18" for row in active)


def test_ui_uses_contextual_evidence_without_wiring_it_into_scoring():
    app = (REPO / "app.py").read_text(encoding="utf-8")
    assert "render_contextual_evidence" in app
    assert "Contextual evidence does not change the ranking score" in app
