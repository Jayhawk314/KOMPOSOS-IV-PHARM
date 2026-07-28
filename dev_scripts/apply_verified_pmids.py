#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

import sqlite3
import re

DB_PATH = "data/drugs/tier1.db"
VERIF_FILE = "final_verification_results.txt"

# Read verification results - only the YES entries
verified_pmids = []
with open(VERIF_FILE) as f:
    for line in f:
        if line.startswith('#') or not line.strip():
            continue
        parts = line.strip().split('|')
        if len(parts) >= 5 and parts[4] == 'YES':
            protein = parts[1]
            disease = parts[2]
            pmid = parts[3]
            verified_pmids.append((protein, disease, pmid))

print(f"Found {len(verified_pmids)} verified PMIDs in {VERIF_FILE}")

# Connect to database
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

updated_count = 0
for protein, disease, pmid in verified_pmids:
    # Find the edge
    cur.execute(
        "SELECT id, provenance FROM morphisms WHERE source_name = ? AND target_name = ?",
        (protein, disease)
    )
    rows = cur.fetchall()
    
    if not rows:
        # Try finding by protein in the target (some edges are directed differently)
        cur.execute(
            "SELECT id, provenance FROM morphisms WHERE source_name = ? AND target_name = ?",
            (disease, protein)
        )
        rows = cur.fetchall()

    if not rows:
        # print(f"  [-] {protein} -> {disease} not found in DB")
        continue

    for morph_id, current_prov in rows:
        # Add PMID to provenance if not already there
        if f"PMID:{pmid}" not in (current_prov or ""):
            new_prov = current_prov if current_prov and current_prov != "unknown" else ""
            if new_prov:
                if not new_prov.endswith(';'):
                    new_prov += ";"
                new_prov += f" PMID:{pmid}"
            else:
                new_prov = f"PMID:{pmid}"
            
            cur.execute("UPDATE morphisms SET provenance = ? WHERE id = ?", (new_prov, morph_id))
            updated_count += 1
            print(f"  [+] Updated {protein}->{disease} with PMID:{pmid}")

# Commit changes
conn.commit()
print(f"\nApplied {updated_count} PMID updates to database")

# Show summary
cur.execute("SELECT COUNT(*) FROM morphisms WHERE provenance LIKE '%PMID:%'")
pmid_count = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM morphisms")
total_count = cur.fetchone()[0]

print(f"\nDatabase now has:")
print(f"  {pmid_count} morphisms with PMIDs")
print(f"  {total_count - pmid_count} morphisms without PMIDs")

conn.close()
