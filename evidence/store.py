from __future__ import annotations

import json
import re
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from .models import PairEvidence


REPO = Path(__file__).resolve().parent.parent
DEFAULT_EVIDENCE_DB = REPO / "data/evidence/evidence.db"
DEFAULT_SCHEMA = REPO / "data/evidence/schema.sql"


class EvidenceStore:
    """Read/query API for the contextual evidence database."""

    def __init__(self, path: str | Path = DEFAULT_EVIDENCE_DB):
        self.path = Path(path)

    @contextmanager
    def connect(self, *, readonly: bool = False) -> Iterator[sqlite3.Connection]:
        if readonly:
            connection = sqlite3.connect(f"file:{self.path}?mode=ro", uri=True)
        else:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            yield connection
            if not readonly:
                connection.commit()
        except Exception:
            if not readonly:
                connection.rollback()
            raise
        finally:
            connection.close()

    def initialize(self, schema_path: str | Path = DEFAULT_SCHEMA) -> None:
        schema = Path(schema_path).read_text(encoding="utf-8")
        with self.connect() as connection:
            connection.executescript(schema)
            connection.execute(
                "INSERT OR REPLACE INTO schema_meta(key, value) VALUES (?, ?)",
                ("schema_version", "1"),
            )

    def exists(self) -> bool:
        return self.path.is_file()

    @staticmethod
    def _decode(row: sqlite3.Row) -> dict:
        item = dict(row)
        for key in (
            "scope_json", "raw_json", "phase_json", "metadata_json",
            "attributes_json",
        ):
            if key in item and isinstance(item[key], str):
                try:
                    item[key] = json.loads(item[key])
                except json.JSONDecodeError:
                    pass
        return item

    def get_pair_evidence(self, drug: str, disease: str) -> PairEvidence:
        if not self.exists():
            return PairEvidence(drug=drug, disease=disease)
        with self.connect(readonly=True) as connection:
            review_rows = connection.execute(
                """SELECT * FROM candidate_reviews
                   WHERE lower(drug)=lower(?) AND disease=?
                   ORDER BY review_id""",
                (drug, disease),
            ).fetchall()
            reviews = tuple(self._decode(row) for row in review_rows)
            claim_ids = [row["claim_id"] for row in review_rows]
            if not claim_ids:
                return PairEvidence(drug=drug, disease=disease)
            placeholders = ",".join("?" for _ in claim_ids)
            study_rows = connection.execute(
                f"""SELECT s.*, p.claim_id, p.review_id, p.pair_linkage
                    FROM studies s
                    JOIN study_pair_links p ON p.study_id=s.study_id
                    WHERE p.claim_id IN ({placeholders})
                    ORDER BY s.completion_date DESC, s.study_id""",
                claim_ids,
            ).fetchall()
            outcome_rows = connection.execute(
                f"""SELECT * FROM outcomes
                    WHERE claim_id IN ({placeholders})
                    ORDER BY human_reviewed DESC, outcome_id""",
                claim_ids,
            ).fetchall()
            receipt_rows = connection.execute(
                f"""SELECT DISTINCT r.* FROM receipts r
                    LEFT JOIN claim_evidence ce ON ce.receipt_id=r.receipt_id
                    LEFT JOIN studies s ON s.primary_receipt_id=r.receipt_id
                    LEFT JOIN study_pair_links p ON p.study_id=s.study_id
                    WHERE ce.claim_id IN ({placeholders})
                       OR p.claim_id IN ({placeholders})
                    ORDER BY r.source_type, r.external_id""",
                [*claim_ids, *claim_ids],
            ).fetchall()
        return PairEvidence(
            drug=drug,
            disease=disease,
            reviews=reviews,
            studies=tuple(self._decode(row) for row in study_rows),
            outcomes=tuple(self._decode(row) for row in outcome_rows),
            receipts=tuple(self._decode(row) for row in receipt_rows),
        )

    def disease_review_summary(self, disease: str) -> list[dict]:
        if not self.exists():
            return []
        with self.connect(readonly=True) as connection:
            rows = connection.execute(
                """SELECT review_id, drug, disease, evidence_state,
                          human_testing_status, result_signal,
                          candidate_assessment, negative_evidence_found
                   FROM candidate_reviews
                   WHERE disease=? ORDER BY drug""",
                (disease,),
            ).fetchall()
        return [dict(row) for row in rows]

    def counts(self) -> dict[str, int]:
        if not self.exists():
            return {}
        tables = (
            "receipts", "claims", "candidate_reviews", "studies",
            "study_roles", "outcomes", "claim_evidence", "review_events",
        )
        with self.connect(readonly=True) as connection:
            return {
                table: connection.execute(
                    f"SELECT COUNT(*) FROM {table}"
                ).fetchone()[0]
                for table in tables
            }

    def search(self, query: str, *, limit: int = 20) -> list[dict]:
        """Search the reviewed local corpus with a safe FTS5 AND query."""
        if not self.exists():
            return []
        terms = re.findall(r"[A-Za-z0-9]+", query)
        if not terms:
            return []
        expression = " AND ".join(f'"{term}"' for term in terms)
        with self.connect(readonly=True) as connection:
            rows = connection.execute(
                """SELECT record_type, record_id, title,
                          snippet(evidence_fts, 3, '[', ']', '...', 24) AS excerpt,
                          bm25(evidence_fts) AS rank
                   FROM evidence_fts
                   WHERE evidence_fts MATCH ?
                   ORDER BY rank LIMIT ?""",
                (expression, limit),
            ).fetchall()
        return [dict(row) for row in rows]
