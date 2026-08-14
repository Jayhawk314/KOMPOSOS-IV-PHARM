from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sqlite3
from pathlib import Path
from urllib.parse import urlparse

from .acquire_trial_results import (
    DISPOSITION_RESULTS_CTG as RESULTS_RECOVERED_CTG,
    load_cached as load_cached_trial_results,
)
from .store import DEFAULT_EVIDENCE_DB, EvidenceStore, REPO


REVIEW_DIR = REPO / "reports/candidate_review_2026-08-01"
REVIEW_SHEET = REVIEW_DIR / "CANDIDATE_REVIEW_60.csv"
TRIAL_INVENTORY = REVIEW_DIR / "TRIAL_EVIDENCE_60.json"
PMID_AUDIT = REVIEW_DIR / "TERMINAL_PMID_AUDIT.csv"
PMID_REVIEW = REVIEW_DIR / "TERMINAL_PMID_REVIEW.csv"
PMID_URL = re.compile(r"pubmed\.ncbi\.nlm\.nih\.gov/(\d+)")
PMC_URL = re.compile(r"ncbi\.nlm\.nih\.gov/articles/(PMC\d+)", re.I)
NCT_ID = re.compile(r"(NCT\d+)", re.I)


def stable_id(prefix: str, *parts: str) -> str:
    payload = "\x1f".join(parts).encode("utf-8")
    return f"{prefix}:{hashlib.sha256(payload).hexdigest()[:20]}"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def receipt_from_url(url: str) -> tuple[str, str, str]:
    url = url.strip()
    if match := PMID_URL.search(url):
        return f"PUBMED:{match.group(1)}", "PUBMED", match.group(1)
    if match := PMC_URL.search(url):
        external = match.group(1).upper()
        return f"PMC:{external}", "PMC", external
    if match := NCT_ID.search(url):
        external = match.group(1).upper()
        return f"CLINICALTRIALS:{external}", "CLINICALTRIALS", external
    host = urlparse(url).netloc.lower()
    source = "FDA" if host.endswith("fda.gov") else "WEB"
    external = hashlib.sha256(url.encode("utf-8")).hexdigest()[:20]
    return f"{source}:{external}", source, external


def insert_receipt(
    connection: sqlite3.Connection,
    *, receipt_id: str,
    source_type: str,
    external_id: str,
    title: str = "",
    url: str = "",
    resolves: int | None = None,
    relevance: str = "",
    review_note: str = "",
    retrieved_at: str = "",
) -> None:
    connection.execute(
        """INSERT INTO receipts(
               receipt_id, source_type, external_id, title, url, resolves,
               relevance_assessment, review_note, retrieved_at
           ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT(receipt_id) DO UPDATE SET
               title=CASE WHEN excluded.title<>'' THEN excluded.title ELSE receipts.title END,
               url=CASE WHEN excluded.url<>'' THEN excluded.url ELSE receipts.url END,
               resolves=COALESCE(excluded.resolves, receipts.resolves),
               relevance_assessment=CASE WHEN excluded.relevance_assessment<>''
                   THEN excluded.relevance_assessment ELSE receipts.relevance_assessment END,
               review_note=CASE WHEN excluded.review_note<>''
                   THEN excluded.review_note ELSE receipts.review_note END,
               retrieved_at=CASE WHEN excluded.retrieved_at<>''
                   THEN excluded.retrieved_at ELSE receipts.retrieved_at END""",
        (
            receipt_id, source_type, external_id, title, url, resolves,
            relevance, review_note, retrieved_at,
        ),
    )


def import_pmid_receipts(connection: sqlite3.Connection) -> None:
    manual = {row["pmid"]: row for row in read_csv(PMID_REVIEW)}
    for row in read_csv(PMID_AUDIT):
        reviewed = manual.get(row["pmid"], {})
        insert_receipt(
            connection,
            receipt_id=f"PUBMED:{row['pmid']}",
            source_type="PUBMED",
            external_id=row["pmid"],
            title=row["title"],
            url=f"https://pubmed.ncbi.nlm.nih.gov/{row['pmid']}/",
            resolves=1 if row["resolves"] == "YES" else 0,
            relevance=reviewed.get("relevance_assessment", ""),
            review_note=reviewed.get("review_note", ""),
            retrieved_at="2026-08-01",
        )


def evidence_relationship(row: dict[str, str]) -> str:
    """Never infer source-level support from a pair-level review summary."""
    if row["evidence_state"] == "INVALID_CANDIDATE":
        return "CATEGORY_OR_ROUTE_CONTEXT"
    return "REVIEWED_CONTEXT"


def import_candidate_reviews(connection: sqlite3.Connection) -> dict[str, str]:
    claim_by_review: dict[str, str] = {}
    for row in read_csv(REVIEW_SHEET):
        claim_id = f"CLAIM:{row['review_id']}"
        claim_by_review[row["review_id"]] = claim_id
        scope = {
            "mechanism_target": row["mechanism_target"],
            "terminal_relation": row["terminal_relation"],
            "direction": row["direction"],
        }
        connection.execute(
            """INSERT INTO claims(
                   claim_id, subject_name, predicate, object_name, scope_json,
                   polarity, source_text
               ) VALUES (?, ?, 'MAY_TREAT', ?, ?, 'UNRESOLVED', ?)""",
            (
                claim_id, row["drug"], row["disease"],
                json.dumps(scope, sort_keys=True), row["review_note"],
            ),
        )
        connection.execute(
            """INSERT INTO candidate_reviews(
                   review_id, claim_id, drug, disease, mechanism_target,
                   terminal_relation, terminal_tier, terminal_provenance,
                   terminal_receipt_assessment, direction, cheap_generic,
                   evidence_state, human_testing_status, result_signal,
                   candidate_assessment, review_note, negative_evidence_found,
                   negative_evidence_note, evidence_sources, reviewed_on, raw_json
               ) VALUES (
                   ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
               )""",
            (
                row["review_id"], claim_id, row["drug"], row["disease"],
                row["mechanism_target"], row["terminal_relation"],
                row["terminal_tier"], row["terminal_provenance"],
                row["terminal_receipt_assessment"], row["direction"],
                row["cheap_generic"], row["evidence_state"],
                row["human_testing_status"], row["result_signal"],
                row["candidate_assessment"], row["review_note"],
                row["negative_evidence_found"],
                row["what_kind_of_negative_evidence"], row["evidence_sources"],
                row["reviewed_on"], json.dumps(row, sort_keys=True),
            ),
        )
        connection.execute(
            """INSERT INTO outcomes(
                   outcome_id, claim_id, endpoint, result_signal, summary,
                   human_reviewed
               ) VALUES (?, ?, 'PAIR_LEVEL_REVIEW', ?, ?, 1)""",
            (
                f"REVIEW_OUTCOME:{row['review_id']}", claim_id,
                row["result_signal"], row["review_note"],
            ),
        )
        connection.execute(
            """INSERT INTO review_events VALUES (?, 'CLAIM', ?, ?, ?,
                   'project_review', ?)""",
            (
                f"REVIEW_EVENT:{row['review_id']}", claim_id,
                row["candidate_assessment"],
                row["what_kind_of_negative_evidence"], row["reviewed_on"],
            ),
        )
        for url in filter(None, (item.strip() for item in row["evidence_sources"].split(";"))):
            receipt_id, source_type, external_id = receipt_from_url(url)
            insert_receipt(
                connection,
                receipt_id=receipt_id,
                source_type=source_type,
                external_id=external_id,
                url=url,
            )
            connection.execute(
                """INSERT OR REPLACE INTO claim_evidence(
                       claim_id, receipt_id, relationship, review_note
                   ) VALUES (?, ?, ?, ?)""",
                (claim_id, receipt_id, evidence_relationship(row), row["review_note"]),
            )
        for pmid in re.findall(r"PMID:(\d+)", row["terminal_provenance"]):
            receipt_id = f"PUBMED:{pmid}"
            insert_receipt(
                connection,
                receipt_id=receipt_id,
                source_type="PUBMED",
                external_id=pmid,
                url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
            )
            connection.execute(
                """INSERT OR IGNORE INTO claim_evidence(
                       claim_id, receipt_id, relationship, review_note
                   ) VALUES (?, ?, 'GRAPH_TERMINAL_RECEIPT', ?)""",
                (claim_id, receipt_id, row["terminal_receipt_assessment"]),
            )
    return claim_by_review


def add_role(
    connection: sqlite3.Connection,
    study_id: str,
    role: str,
    literal_name: str,
    *,
    graph_object_name: str | None = None,
    attributes: dict | None = None,
) -> None:
    role_id = stable_id("ROLE", study_id, role, literal_name)
    connection.execute(
        """INSERT OR IGNORE INTO study_roles VALUES (?, ?, ?, ?, ?, ?)""",
        (
            role_id, study_id, role, graph_object_name, literal_name,
            json.dumps(attributes or {}, sort_keys=True),
        ),
    )


def import_trials(
    connection: sqlite3.Connection, claim_by_review: dict[str, str],
) -> None:
    inventory = json.loads(TRIAL_INVENTORY.read_text(encoding="utf-8"))
    for pair in inventory.values():
        review_id = pair["review_id"]
        claim_id = claim_by_review[review_id]
        for trial in pair["trials"]:
            study_id = trial["nct"]
            if not study_id:
                continue
            receipt_id = f"CLINICALTRIALS:{study_id}"
            insert_receipt(
                connection,
                receipt_id=receipt_id,
                source_type="CLINICALTRIALS",
                external_id=study_id,
                title=trial["title"],
                url=f"https://clinicaltrials.gov/study/{study_id}",
                resolves=1,
                retrieved_at="2026-08-01",
            )
            connection.execute(
                """INSERT INTO studies(
                       study_id, primary_receipt_id, title, phase_json,
                       recruitment_status, completion_date, has_posted_results,
                       why_stopped, stop_class, metadata_json
                   ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(study_id) DO UPDATE SET
                       title=excluded.title,
                       recruitment_status=excluded.recruitment_status,
                       completion_date=excluded.completion_date,
                       has_posted_results=excluded.has_posted_results,
                       metadata_json=excluded.metadata_json""",
                (
                    study_id, receipt_id, trial["title"],
                    json.dumps(trial["phases"], sort_keys=True), trial["status"],
                    trial["completion_date"], int(trial["has_posted_results"]),
                    trial["why_stopped"], trial["stop_class"],
                    json.dumps(trial, sort_keys=True),
                ),
            )
            add_role(
                connection, study_id, "INTERVENTION", pair["drug"],
                graph_object_name=pair["drug"],
                attributes={"canonical_pair_role": True},
            )
            add_role(
                connection, study_id, "DISEASE", pair["disease"],
                graph_object_name=pair["disease"],
                attributes={"canonical_pair_role": True},
            )
            for name in trial["interventions"]:
                add_role(connection, study_id, "INTERVENTION_REPORTED", name)
            for name in trial["conditions"]:
                add_role(connection, study_id, "CONDITION_REPORTED", name)
            connection.execute(
                """INSERT OR REPLACE INTO study_pair_links VALUES (?, ?, ?, ?)""",
                (study_id, claim_id, review_id, trial["pair_linkage"]),
            )
            connection.execute(
                """INSERT OR REPLACE INTO outcomes(
                       outcome_id, study_id, claim_id, endpoint, result_signal,
                       summary, receipt_id, human_reviewed
                   ) VALUES (?, ?, ?, 'TRIAL_RECORD', ?, ?, ?, 0)""",
                (
                    stable_id("TRIAL_OUTCOME", study_id, claim_id), study_id,
                    claim_id, trial["result_polarity"],
                    "Registry status only; outcome polarity was not automated.",
                    receipt_id,
                ),
            )
            connection.execute(
                """INSERT OR IGNORE INTO claim_evidence(
                       claim_id, receipt_id, relationship, review_note
                   ) VALUES (?, ?, 'TRIAL_REGISTRY_CONTEXT', ?)""",
                (claim_id, receipt_id, trial["pair_linkage"]),
            )
            for pmid in trial["result_pmids"]:
                pmid_receipt = f"PUBMED:{pmid}"
                insert_receipt(
                    connection,
                    receipt_id=pmid_receipt,
                    source_type="PUBMED",
                    external_id=pmid,
                    url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                )
                connection.execute(
                    """INSERT OR IGNORE INTO claim_evidence(
                           claim_id, receipt_id, relationship, review_note
                       ) VALUES (?, ?, 'TRIAL_RESULT_PUBLICATION', ?)""",
                    (claim_id, pmid_receipt, study_id),
                )


def import_recovered_results(connection: sqlite3.Connection) -> dict[str, int]:
    """Attach recovered registry results to studies already in the database.

    Retrieval only. This records that results exist and where to read them; it
    never asserts what they showed, so every outcome it writes is
    RESULTS_AVAILABLE_NOT_ASSESSED with human_reviewed = 0. A human reading the
    results section is what turns this into an efficacy statement.

    A missing cache is normal - the build must not require network access.
    """
    report = load_cached_trial_results()
    records = report.get("records", {})
    if not records:
        return {"recovered_outcomes": 0, "dispositions_set": 0}

    checked_on = report.get("generated_at", "")
    known = {row[0] for row in connection.execute("SELECT study_id FROM studies")}
    dispositions = 0
    recovered = 0

    for nct_id, record in sorted(records.items()):
        if nct_id not in known:
            continue
        published = bool(record.get("result_pmids") or record.get("derived_pmids"))
        # Only a trial with posted registry results can be "posted but never
        # published". A trial with no results at all is neither - leave it blank
        # rather than implying results exist somewhere unpublished.
        if record["disposition"] == RESULTS_RECOVERED_CTG:
            publication_state = "PUBLISHED" if published else "NOT_PUBLISHED"
        else:
            publication_state = ""
        connection.execute(
            """UPDATE studies
                  SET results_disposition = ?, results_url = ?,
                      results_checked_on = ?, has_posted_results = ?,
                      results_publication_state = ?
                WHERE study_id = ?""",
            (
                record["disposition"], record.get("results_url", ""), checked_on,
                int(bool(record.get("has_results"))), publication_state, nct_id,
            ),
        )
        dispositions += 1

        if record["disposition"] != RESULTS_RECOVERED_CTG:
            continue

        receipt_id = f"CLINICALTRIALS:{nct_id}"
        insert_receipt(
            connection,
            receipt_id=receipt_id,
            source_type="CLINICALTRIALS",
            external_id=nct_id,
            url=record.get("results_url", ""),
            resolves=1,
            relevance=(
                "RESULTS_POSTED_NOT_PUBLISHED" if not published
                else "RESULTS_POSTED_AND_PUBLISHED"
            ),
            review_note=(
                "Registry results section located by automated retrieval; "
                "not read or assessed."
            ),
            retrieved_at=checked_on,
        )

        titles = record.get("outcome_measure_titles") or []
        summary = (
            f"Registry results posted: {record.get('outcome_measure_count', 0)} "
            f"outcome measure(s)"
            + (f", enrolment {record['enrollment_count']}" if record.get("enrollment_count") is not None else "")
            + (
                ". No linked publication - not retrievable by literature search."
                if not published else "."
            )
            + (f" Measures include: {'; '.join(titles[:3])}." if titles else "")
        )
        for claim_row in connection.execute(
            "SELECT claim_id FROM study_pair_links WHERE study_id = ?", (nct_id,)
        ).fetchall():
            connection.execute(
                """INSERT OR REPLACE INTO outcomes(
                       outcome_id, study_id, claim_id, endpoint, result_signal,
                       summary, receipt_id, human_reviewed
                   ) VALUES (?, ?, ?, 'REGISTRY_RESULTS', ?, ?, ?, 0)""",
                (
                    stable_id("RECOVERED_RESULT", nct_id, claim_row[0]), nct_id,
                    claim_row[0], "RESULTS_AVAILABLE_NOT_ASSESSED", summary,
                    receipt_id,
                ),
            )
            recovered += 1

    return {"recovered_outcomes": recovered, "dispositions_set": dispositions}


def populate_fts(connection: sqlite3.Connection) -> None:
    """Build a local lexical baseline that any future vector index must beat."""
    connection.execute("DELETE FROM evidence_fts")
    connection.execute(
        """INSERT INTO evidence_fts(record_type, record_id, title, body)
           SELECT 'CANDIDATE_REVIEW', review_id, drug || ' - ' || disease,
                  drug || ' ' || disease || ' ' || mechanism_target || ' ' ||
                  evidence_state || ' ' || human_testing_status || ' ' ||
                  result_signal || ' ' || candidate_assessment || ' ' ||
                  review_note || ' ' || negative_evidence_note
           FROM candidate_reviews"""
    )
    connection.execute(
        """INSERT INTO evidence_fts(record_type, record_id, title, body)
           SELECT 'STUDY', study_id, title,
                  title || ' ' || recruitment_status || ' ' || stop_class || ' ' ||
                  why_stopped
           FROM studies"""
    )
    connection.execute(
        """INSERT INTO evidence_fts(record_type, record_id, title, body)
           SELECT 'RECEIPT', receipt_id,
                  CASE WHEN title<>'' THEN title ELSE source_type || ':' || external_id END,
                  title || ' ' || relevance_assessment || ' ' || review_note
           FROM receipts"""
    )


def build_database(output: str | Path = DEFAULT_EVIDENCE_DB) -> dict[str, int]:
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".tmp")
    if temporary.exists():
        temporary.unlink()
    store = EvidenceStore(temporary)
    store.initialize()
    with store.connect() as connection:
        import_pmid_receipts(connection)
        claim_by_review = import_candidate_reviews(connection)
        import_trials(connection, claim_by_review)
        recovered = import_recovered_results(connection)
        populate_fts(connection)
        connection.execute(
            "INSERT OR REPLACE INTO schema_meta(key, value) VALUES (?, ?)",
            ("built_on", "2026-08-01"),
        )
        connection.execute(
            "INSERT OR REPLACE INTO schema_meta(key, value) VALUES (?, ?)",
            ("candidate_review_rows", str(len(claim_by_review))),
        )
        connection.execute(
            "INSERT OR REPLACE INTO schema_meta(key, value) VALUES (?, ?)",
            ("recovered_result_outcomes", str(recovered["recovered_outcomes"])),
        )
    temporary.replace(output)
    return EvidenceStore(output).counts()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_EVIDENCE_DB)
    args = parser.parse_args()
    counts = build_database(args.out)
    print(f"built {args.out}")
    for table, count in counts.items():
        print(f"  {table:<20}{count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
