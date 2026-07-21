#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""
Merge the 207 adjudicated protein->disease discoveries into tier1.db.

Provenance policy (deliberately conservative)
---------------------------------------------
These candidates passed the COG content gate AND in-session adjudication, but
`DISCOVERY_ADJUDICATION.json` itself says they are "ready for promotion toward
RELATION-VERIFIED (pending additional audit)". The standing repo rule is that a
gate verdict never publishes as RELATION-VERIFIED. So they land as:

    provenance    PMID:<pmid>; [RELATION-SCREENED]
    evidence_tier INFERRED        (not ESTABLISHED - no independent audit yet)
    confidence    0.65            (below every existing RELATION-VERIFIED assoc edge,
                                   which range 0.72-0.95)

Honest limitation
-----------------
Every one of these is `associated_with`, the same co-occurrence-grade relation that
`validation/nonobvious.py` flags as `assoc`. Merging them widens path COVERAGE - more
proteins gain a disease link, so more drugs become scoreable - but it does NOT improve
terminal-hop QUALITY. Do not read this merge as strengthening the mechanistic layer.

Existing edges are never overwritten. Only new (source, relation, target) triples insert.

Usage:
    python scripts/merge_adjudicated_discoveries.py --dry-run
    python scripts/merge_adjudicated_discoveries.py --apply
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "drugs" / "tier1.db"
ADJ_PATH = ROOT / "data" / "DISCOVERY_ADJUDICATION.json"

TIER = "INFERRED"
CONFIDENCE = 0.65
TAG = "[RELATION-SCREENED]"


def load_verified(path: Path) -> list[dict]:
    payload = json.loads(path.read_text())
    return [v for v in payload["verdicts"] if v.get("adjudicated_verdict") == "VERIFIED"]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--db", default=str(DB_PATH))
    ap.add_argument("--adjudication", default=str(ADJ_PATH))
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    if not args.apply:
        args.dry_run = True

    conn = sqlite3.connect(args.db)
    verified = load_verified(Path(args.adjudication))

    objects = {r[0] for r in conn.execute("SELECT name FROM objects")}
    existing = {
        (s, n, t)
        for s, n, t in conn.execute("SELECT source_name, name, target_name FROM morphisms")
    }

    to_insert, dup, missing_obj, no_pmid = [], [], [], []
    for v in verified:
        src, rel, tgt, pmid = v["source"], v["relation"], v["target"], v.get("pmid")
        if not pmid:
            no_pmid.append(f"{src}->{tgt}")
            continue
        if (src, rel, tgt) in existing:
            dup.append(f"{src}->{tgt}")
            continue
        # An edge to a node that does not exist would recreate the orphan bug.
        if src not in objects or tgt not in objects:
            missing_obj.append(f"{src}->{tgt}")
            continue
        to_insert.append(v)

    print(f"VERIFIED verdicts:        {len(verified)}")
    print(f"  already in graph:       {len(dup)}")
    print(f"  endpoint missing:       {len(missing_obj)}")
    print(f"  no PMID:                {len(no_pmid)}")
    print(f"  -> to insert:           {len(to_insert)}")
    if missing_obj:
        print(f"     missing-endpoint examples: {missing_obj[:6]}")

    before = conn.execute("SELECT COUNT(*) FROM morphisms").fetchone()[0]

    if args.dry_run:
        print(f"\nmorphisms now: {before}. DRY RUN - nothing written.")
        return 0

    rows = []
    for v in to_insert:
        src, rel, tgt = v["source"], v["relation"], v["target"]
        rows.append((
            f"{rel}:{src}->{tgt}",
            rel, src, tgt,
            json.dumps({
                "discovery": True,
                "gate_verdict": v.get("gate_verdict"),
                "adjudicated_verdict": v.get("adjudicated_verdict"),
                "adjudication_reason": v.get("reason"),
                "proof_sentence": v.get("proof_sentence"),
                "merged_by": "scripts/merge_adjudicated_discoveries.py",
            }),
            CONFIDENCE,
            f"PMID:{v['pmid']}; {TAG}",
            TIER,
        ))

    conn.executemany(
        "INSERT OR IGNORE INTO morphisms "
        "(id, name, source_name, target_name, metadata, confidence, provenance, evidence_tier) "
        "VALUES (?,?,?,?,?,?,?,?)",
        rows,
    )
    conn.commit()

    after = conn.execute("SELECT COUNT(*) FROM morphisms").fetchone()[0]
    dangling = conn.execute(
        "SELECT COUNT(*) FROM morphisms WHERE source_name NOT IN (SELECT name FROM objects)"
        "   OR target_name NOT IN (SELECT name FROM objects)"
    ).fetchone()[0]
    print(f"\nmorphisms: {before} -> {after}  (+{after - before})")
    print(f"dangling edges: {dangling} (must stay 0)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
