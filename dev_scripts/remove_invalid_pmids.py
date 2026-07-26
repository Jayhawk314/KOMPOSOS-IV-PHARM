#!/usr/bin/env python3
"""Remove invalid PMIDs from tier1.db provenance fields"""

import sqlite3
import json
import re
from pathlib import Path

# Invalid PMIDs to remove
INVALID_PMIDS = {
    "10698507", "17081993", "17089045", "22282679", "26309782",
    "27141380", "27347159", "27708678", "34714908", "36551764",
    "36814396", "38460364", "40613620", "41489242", "41730847"
}

DB_PATH = "data/drugs/tier1.db"

# Backup first
backup_path = "data/drugs/tier1_backup_before_pmid_cleanup.db"
import shutil
shutil.copy2(DB_PATH, backup_path)
print(f"Created backup: {backup_path}\n")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Find morphisms with invalid PMIDs
cursor.execute("SELECT id, source_name, target_name, provenance FROM morphisms")
all_morphisms = cursor.fetchall()

morphisms_to_update = []
for morph_id, source, target, prov in all_morphisms:
    if not prov or prov == "unknown":
        continue

    # Check if any invalid PMID is in this provenance
    found_invalid = []
    for pmid in INVALID_PMIDS:
        if f"PMID:{pmid}" in prov or f"pmid:{pmid}" in prov.lower():
            found_invalid.append(pmid)

    if found_invalid:
        morphisms_to_update.append({
            "id": morph_id,
            "source": source,
            "target": target,
            "old_prov": prov,
            "invalid_pmids": found_invalid
        })

print(f"Found {len(morphisms_to_update)} morphisms with invalid PMIDs:\n")

updates_made = 0
for morph in morphisms_to_update:
    print(f"{morph['source']} -> {morph['target']}")
    print(f"  Invalid PMIDs: {', '.join(morph['invalid_pmids'])}")
    print(f"  Old provenance: {morph['old_prov'][:100]}...")

    # Remove invalid PMID references
    new_prov = morph['old_prov']
    for pmid in morph['invalid_pmids']:
        # Remove PMID:xxxxx patterns
        new_prov = re.sub(rf'PMID:{pmid}\b', '', new_prov, flags=re.IGNORECASE)
        new_prov = re.sub(rf'pmid:{pmid}\b', '', new_prov, flags=re.IGNORECASE)

    # Clean up extra whitespace and punctuation
    new_prov = re.sub(r'\s+', ' ', new_prov).strip()
    new_prov = re.sub(r',\s*,', ',', new_prov)
    new_prov = re.sub(r',\s*$', '', new_prov)
    new_prov = re.sub(r'^\s*,', '', new_prov)

    # If provenance is now empty, set to unknown
    if not new_prov or new_prov.strip() in [',', '', 'PMID:', 'pmid:']:
        new_prov = "unknown"

    print(f"  New provenance: {new_prov[:100]}...")

    # Update the database
    cursor.execute(
        "UPDATE morphisms SET provenance = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (new_prov, morph['id'])
    )
    updates_made += 1
    print()

conn.commit()
print(f"\nUpdated {updates_made} morphisms")

# Verify
cursor.execute("SELECT COUNT(*) FROM morphisms WHERE provenance = 'unknown'")
unknown_count = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM morphisms")
total_morphisms = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM morphisms WHERE provenance != 'unknown'")
with_prov_count = cursor.fetchone()[0]

# Count unique valid PMIDs remaining
cursor.execute("SELECT provenance FROM morphisms WHERE provenance != 'unknown'")
all_prov = cursor.fetchall()
valid_pmids = set()
for (prov,) in all_prov:
    if prov:
        pmids = re.findall(r'PMID:(\d+)', prov, flags=re.IGNORECASE)
        valid_pmids.update(pmids)

print(f"\nFinal statistics:")
print(f"  Total morphisms: {total_morphisms}")
print(f"  With provenance: {with_prov_count}")
print(f"  Unknown provenance: {unknown_count}")
print(f"  Unique valid PMIDs: {len(valid_pmids)}")

conn.close()
print(f"\nDone! Database updated. Backup saved to {backup_path}")
