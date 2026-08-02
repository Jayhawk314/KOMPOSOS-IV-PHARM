import csv

from validation.audit_terminal_pmids import (
    DEFAULT_DB,
    DEFAULT_SHEET,
    summary_resolves,
    terminal_edges,
)
from validation.enrich_candidate_review import (
    DEFAULT_EVIDENCE_REVIEW,
    DEFAULT_PMID_REVIEW,
    enriched_rows,
)


def _rows(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def test_ncbi_error_object_is_not_a_resolving_pubmed_record():
    assert summary_resolves({
        "uid": "23177518", "error": "cannot get document summary", "title": ""
    }) is False
    assert summary_resolves({"uid": "28575464", "title": "A real paper"}) is True


def test_all_terminal_pmids_have_manual_relevance_review():
    rows, uses = terminal_edges(DEFAULT_SHEET, DEFAULT_DB)
    reviewed = {row["pmid"] for row in _rows(DEFAULT_PMID_REVIEW)}
    assert len(rows) == 60
    assert len(uses) == 21
    assert set(uses) == reviewed


def test_every_candidate_has_complete_multiaxis_evidence_review():
    reviews = _rows(DEFAULT_EVIDENCE_REVIEW)
    assert len(reviews) == 60
    assert len({row["review_id"] for row in reviews}) == 60
    required = {
        "evidence_state", "human_testing_status", "result_signal",
        "candidate_assessment", "review_note", "negative_evidence_found",
        "what_kind_of_negative_evidence", "reviewed_on",
    }
    for row in reviews:
        assert all(row[field] for field in required), row["review_id"]


def test_enriched_sheet_is_reconstructible_from_database_and_review_files():
    fields, rows = enriched_rows(
        DEFAULT_SHEET, DEFAULT_DB, DEFAULT_PMID_REVIEW, DEFAULT_EVIDENCE_REVIEW
    )
    assert len(rows) == 60
    assert "VERDICT" not in fields
    assert "why" not in fields
    assert {row["terminal_tier"] for row in rows} == {
        "ESTABLISHED", "HYPOTHESIS", "SPECULATIVE"
    }
    for row in rows:
        assert row["terminal_provenance"]
        assert row["terminal_receipt_assessment"]
        assert row["evidence_state"]
