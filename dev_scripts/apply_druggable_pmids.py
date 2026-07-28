#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

import sqlite3

DB_PATH = "data/drugs/tier1.db"

# Read verification results - only YES entries
verified_pmids = {}
with open('druggable_verification_results.txt') as f:
    for line in f:
        if line.startswith('#') or not line.strip():
            continue
        parts = line.strip().split('|')
        if len(parts) >= 5 and parts[4] == 'YES':
            rowid = parts[0]
            pmid = parts[3]
            protein = parts[1]
            disease = parts[2]
            verified_pmids[rowid] = (pmid, protein, disease)

print(f"Found {len(verified_pmids)} verified PMIDs to add")

# Connect to database
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Update each edge
for rowid, (pmid, protein, disease) in verified_pmids.items():
    cur.execute("SELECT provenance FROM morphisms WHERE rowid = ?", (rowid,))
    row = cur.fetchone()
    if not row:
        print(f"WARNING: rowid {rowid} not found")
        continue

    current_prov = row[0] or ""

    # Add PMID if not already present
    if f"PMID:{pmid}" not in current_prov:
        if current_prov and not current_prov.endswith(';'):
            new_prov = f"{current_prov}; PMID:{pmid}"
        elif current_prov:
            new_prov = f"{current_prov} PMID:{pmid}"
        else:
            new_prov = f"PMID:{pmid}"

        cur.execute("UPDATE morphisms SET provenance = ? WHERE rowid = ?", (new_prov, rowid))
        print(f"Updated {rowid}: {protein}->{disease} with PMID:{pmid}")

conn.commit()
print(f"\nCommitted {len(verified_pmids)} PMID updates")

# Show final stats
cur.execute("SELECT COUNT(*) FROM morphisms WHERE provenance LIKE '%PMID:%'")
pmid_count = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM morphisms")
total_count = cur.fetchone()[0]

print(f"\nDatabase now has:")
print(f"  {pmid_count} morphisms with PMIDs ({100*pmid_count/total_count:.1f}%)")
print(f"  {total_count - pmid_count} morphisms without PMIDs")

conn.close()
