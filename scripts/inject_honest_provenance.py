#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""
Honest, tiered provenance injection (supersedes inject_verified_provenance.py).

Tags reflect exactly what was done, not aspiration:
  [RELATION-VERIFIED]    edge whose proof sentence an agent confirmed asserts the
                         directed, signed relation (see relation_extraction_verdicts.json)
  [LEXICAL-COOCCURRENCE] proof sentence passed lexical co-occurrence + polarity
                         screening only (Source, Target, action keyword in one
                         sentence, no opposite-polarity cue) -- NOT verified

Non-destructive:
  - All stale '[ACTION-VERIFIED]' tags are relabelled to '[LEXICAL-COOCCURRENCE]'.
  - Edges in the regenerated proof set get their re-derived PMID + honest tier.
  - Existing base provenance (ChEMBL, ABPP, STRING, KEGG, ...) is preserved.
Backs up tier1.db before writing. Scoring is unaffected (scoring reads the
evidence_tier column, never the provenance string).
"""

import sqlite3
import json
import shutil
import datetime
from pathlib import Path

DB_PATH = "data/drugs/tier1.db"
MANIFEST_PATH = "data/drugs/tier1_manifest.json"
PROOFS_PATH = "data/action_verified_provenance.json"
VERDICTS_PATH = "data/relation_extraction_verdicts.json"

OUR_TAGS = ("[ACTION-VERIFIED]", "[LEXICAL-COOCCURRENCE]", "[RELATION-VERIFIED]")


def strip_pmids_and_tags(prov: str) -> str:
    if not prov or prov == "unknown":
        return ""
    parts = [p.strip() for p in prov.split(";")]
    keep = [p for p in parts if p and not p.startswith("PMID:") and p not in OUR_TAGS]
    return "; ".join(keep)


def build_new_prov(base: str, pmid: str, tag: str) -> str:
    piece = f"PMID:{pmid}; [{tag}]"
    return f"{base}; {piece}" if base else piece


def main():
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = f"{DB_PATH}.BACKUP_{ts}"
    shutil.copy(DB_PATH, backup)
    print(f"DB backed up -> {backup}")

    proofs = json.load(open(PROOFS_PATH))
    verdicts = json.load(open(VERDICTS_PATH))["verdicts"]

    # (source, target, relation) -> pmid for the regenerated proof set
    proof_map = {(p["source"], p["target"], p["relation"]): p["pmid"] for p in proofs}
    # keys the agent confirmed as directed+signed
    verified_keys = {(v["source"], v["target"], v["relation"])
                     for v in verdicts if v["verdict"] == "VERIFIED"}

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, source_name, target_name, name, provenance FROM morphisms")
    rows = cur.fetchall()

    n_verified = n_lexical = n_relabel = 0
    for mid, src, tgt, rel, prov in rows:
        key = (src, tgt, rel)
        if key in proof_map:
            base = strip_pmids_and_tags(prov)
            tag = "RELATION-VERIFIED" if key in verified_keys else "LEXICAL-COOCCURRENCE"
            new = build_new_prov(base, proof_map[key], tag)
            cur.execute("UPDATE morphisms SET provenance = ? WHERE id = ?", (new, mid))
            if tag == "RELATION-VERIFIED":
                n_verified += 1
            else:
                n_lexical += 1
        elif prov and "[ACTION-VERIFIED]" in prov:
            # old lexical edge not in regenerated set: relabel tag, keep its PMID
            new = prov.replace("[ACTION-VERIFIED]", "[LEXICAL-COOCCURRENCE]")
            cur.execute("UPDATE morphisms SET provenance = ? WHERE id = ?", (new, mid))
            n_relabel += 1

    conn.commit()

    # sanity: no stale tag remains
    cur.execute("SELECT COUNT(*) FROM morphisms WHERE provenance LIKE '%[ACTION-VERIFIED]%'")
    stale = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM morphisms WHERE provenance LIKE '%[RELATION-VERIFIED]%'")
    rv = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM morphisms WHERE provenance LIKE '%[LEXICAL-COOCCURRENCE]%'")
    lx = cur.fetchone()[0]
    conn.close()

    # update manifest
    manifest = json.load(open(MANIFEST_PATH))
    m_v = m_l = m_r = 0
    for m in manifest["morphisms"]:
        key = (m["source"], m["target"], m.get("edge_type"))
        prov = m.get("provenance", "")
        if key in proof_map:
            base = strip_pmids_and_tags(prov)
            tag = "RELATION-VERIFIED" if key in verified_keys else "LEXICAL-COOCCURRENCE"
            m["provenance"] = build_new_prov(base, proof_map[key], tag)
            if tag == "RELATION-VERIFIED":
                m_v += 1
            else:
                m_l += 1
        elif prov and "[ACTION-VERIFIED]" in prov:
            m["provenance"] = prov.replace("[ACTION-VERIFIED]", "[LEXICAL-COOCCURRENCE]")
            m_r += 1
    json.dump(manifest, open(MANIFEST_PATH, "w"), indent=2)

    print("=" * 60)
    print("HONEST PROVENANCE INJECTION COMPLETE")
    print(f"DB:       RELATION-VERIFIED set {n_verified}, LEXICAL refreshed {n_lexical}, relabelled {n_relabel}")
    print(f"Manifest: RELATION-VERIFIED set {m_v}, LEXICAL refreshed {m_l}, relabelled {m_r}")
    print(f"DB now has: {rv} RELATION-VERIFIED, {lx} LEXICAL-COOCCURRENCE, {stale} stale ACTION-VERIFIED")
    assert stale == 0, "stale [ACTION-VERIFIED] tags remain!"


if __name__ == "__main__":
    main()
