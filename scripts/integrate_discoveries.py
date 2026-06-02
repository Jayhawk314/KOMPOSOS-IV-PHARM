"""Integrate the GENUINELY re-adjudicated grounded discoveries into tier1.db.

Source: data/DISCOVERY_REAUDIT.json (verdicts with agent_verdict == "VERIFIED").
This supersedes data/DISCOVERY_ADJUDICATION.json, whose verdicts came from a
keyword classifier (adjudicate_discoveries.py) that overclaimed. The re-audit
(scripts/reaudit_207.py) is genuine in-session agent reading and already:
  - dropped 76 disease->disease edges (invalid; gap-generator artifact),
  - dropped 2 drug->disease edges (leakage-prone),
  - rejected 32 protein->disease candidates (glossary/null/aim/spurious),
leaving 97 agent-verified protein->disease `associated_with` edges.

Tagging policy (honest tiering):
  - evidence_tier = INFERRED   (single-PMID literature association; not measured/established)
  - confidence    = 0.60       (matches existing associated_with INFERRED cohort)
  - provenance    = "PMID:{pmid}; discovery-grounded; agent-adjudicated; [RELATION-VERIFIED]"
    (markers keep this cohort traceable; agent adjudication is the standard that
     minted the existing 594 RELATION-VERIFIED edges)

Idempotent: skips any morphism id already present. Run with --dry-run to preview.

Usage:
    python scripts/integrate_discoveries.py --dry-run
    python scripts/integrate_discoveries.py --commit
"""
import argparse
import json
import sqlite3
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DB = REPO / "data" / "drugs" / "tier1.db"
DEFAULT_SOURCE = REPO / "data" / "DISCOVERY_REAUDIT.json"

EVIDENCE_TIER = "INFERRED"
CONFIDENCE = 0.60


def load_verified(source_path):
    data = json.loads(Path(source_path).read_text(encoding="utf-8"))
    return [v for v in data["verdicts"] if v["agent_verdict"] == "VERIFIED"]


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry-run", action="store_true", help="preview, write nothing")
    g.add_argument("--commit", action="store_true", help="write to tier1.db")
    ap.add_argument("--source", default=str(DEFAULT_SOURCE),
                    help="re-audit JSON to integrate (default: DISCOVERY_REAUDIT.json)")
    args = ap.parse_args()

    print(f"source: {args.source}")
    verified = load_verified(args.source)
    print(f"VERIFIED verdicts loaded: {len(verified)}")

    db = sqlite3.connect(DB)
    c = db.cursor()
    existing_ids = {r[0] for r in c.execute("SELECT id FROM morphisms")}
    existing_objs = {r[0] for r in c.execute("SELECT name FROM objects")}

    to_insert = []
    skipped_existing = []
    missing_objs = []
    for v in verified:
        eid = v["edge_id"]
        if eid in existing_ids:
            skipped_existing.append(eid)
            continue
        if v["source"] not in existing_objs or v["target"] not in existing_objs:
            missing_objs.append(eid)
            continue
        if not v.get("pmid"):
            print(f"  WARN no pmid, skipping: {eid}")
            continue
        prov = f"PMID:{v['pmid']}; discovery-grounded; agent-adjudicated; [RELATION-VERIFIED]"
        meta = json.dumps({
            "discovery_proof": v.get("proof_sentence", ""),
            "adjudication_reason": v.get("agent_reason", ""),
        })
        to_insert.append((
            eid, v["relation"], v["source"], v["target"], meta,
            CONFIDENCE, prov, EVIDENCE_TIER,
        ))

    print(f"to insert:        {len(to_insert)}")
    print(f"skipped existing: {len(skipped_existing)}")
    print(f"missing objects:  {len(missing_objs)}")
    if missing_objs:
        print("  ", missing_objs[:10])

    if args.dry_run:
        for row in to_insert[:5]:
            print("  SAMPLE:", row[0], "| tier", row[7], "| conf", row[5], "|", row[6])
        print("dry-run: no writes")
        return

    c.executemany(
        """INSERT INTO morphisms
           (id, name, source_name, target_name, metadata, confidence, provenance, evidence_tier)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        to_insert,
    )
    db.commit()
    total = c.execute("SELECT COUNT(*) FROM morphisms").fetchone()[0]
    rv = c.execute(
        "SELECT COUNT(*) FROM morphisms WHERE provenance LIKE '%RELATION-VERIFIED%'"
    ).fetchone()[0]
    print(f"COMMITTED {len(to_insert)} morphisms.")
    print(f"total morphisms now: {total}")
    print(f"RELATION-VERIFIED now: {rv}")


if __name__ == "__main__":
    main()
