#!/usr/bin/env python3
"""apply_replacements.py — Apply the 81 verified REPLACE_OK PMID swaps to tier1.db.

Precise per-edge_id swap: replaces PMID:<original> with PMID:<final> in the
morphism's provenance string. Keeps the [LEXICAL-COOCCURRENCE] tier tag
(these remain co-occurrence-level citations, just better-sourced).

Backs up the DB first; prints a before/after diff for every edge.
"""
import sqlite3, json, shutil, datetime, sys

DB = "data/drugs/tier1.db"
VERIF = "data/REPLACEMENT_VERIFICATION.json"

def main():
    rows = json.load(open(VERIF, encoding="utf-8"))
    oks = [x for x in rows if x["status"] == "REPLACE_OK" and x.get("edge_id")]
    print(f"REPLACE_OK with valid edge_id: {len(oks)}")
    print("POLICY: only swap edges currently tagged [LEXICAL-COOCCURRENCE].")
    print("        RELATION-VERIFIED edges keep their agent-adjudicated PMID.\n")

    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = f"{DB}.BACKUP_{ts}"
    shutil.copy2(DB, backup)
    print(f"Backup -> {backup}\n")

    conn = sqlite3.connect(DB); cur = conn.cursor()
    applied = skipped = 0
    diffs = []
    for x in oks:
        eid = x["edge_id"]; orig = str(x["original_pmid"]); new = str(x["final_pmid"])
        cur.execute("SELECT provenance FROM morphisms WHERE id = ?", (eid,))
        r = cur.fetchone()
        if not r:
            print(f"  [SKIP] edge not in DB: {eid}"); skipped += 1; continue
        prov = r[0] or ""
        if "LEXICAL-COOCCURRENCE" not in prov:
            skipped += 1; continue   # protect RELATION-VERIFIED edges
        token_old = f"PMID:{orig}"
        if token_old not in prov:
            print(f"  [SKIP] {eid}: original PMID:{orig} not in provenance ('{prov[:60]}')")
            skipped += 1; continue
        new_prov = prov.replace(token_old, f"PMID:{new}")
        cur.execute("UPDATE morphisms SET provenance = ? WHERE id = ?", (new_prov, eid))
        applied += 1
        diffs.append((eid, prov, new_prov, x["new_title"]))

    conn.commit()
    print(f"\n{'='*78}\nBEFORE / AFTER DIFF ({applied} edges)\n{'='*78}")
    for eid, before, after, title in diffs:
        safe = title.encode("ascii", "replace").decode("ascii")
        print(f"\n{eid}")
        print(f"  - {before}")
        print(f"  + {after}")
        print(f"    ({safe})")

    print(f"\n{'='*78}")
    print(f"APPLIED: {applied}   SKIPPED: {skipped}")
    # sanity: tier counts unchanged
    cur.execute("SELECT count(*) FROM morphisms WHERE provenance LIKE '%RELATION-VERIFIED%'"); rv=cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM morphisms WHERE provenance LIKE '%LEXICAL-COOCCURRENCE%'"); lx=cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM morphisms WHERE provenance LIKE '%PMID%'"); pm=cur.fetchone()[0]
    print(f"Tier check  RELATION-VERIFIED={rv}  LEXICAL-COOCCURRENCE={lx}  PMID-bearing={pm}")
    print(f"Backup at: {backup}")
    conn.close()

if __name__ == "__main__":
    main()
