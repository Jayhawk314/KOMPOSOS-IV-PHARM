#!/usr/bin/env python3
"""
Import Protein->Disease edges from manifest into tier1.db
"""

import json, sqlite3
from pathlib import Path

manifest_path = Path('scripts/protein_disease_edges_manifest.json')
db_path = Path('data/drugs/tier1.db')

print('[1/3] Loading manifest...')
with open(manifest_path) as f:
    manifest = json.load(f)

print(f'[2/3] Connecting to {db_path}...')
conn = sqlite3.connect(str(db_path))
cur = conn.cursor()

print(f'[3/3] Importing {manifest["count"]} edges...')
inserted = 0
skipped = 0

for morph in manifest['morphisms']:
    try:
        # Insert edge with full provenance
        cur.execute('''
            INSERT INTO morphisms 
            (source_name, target_name, name, confidence, provenance, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            morph['source'],
            morph['target'],
            morph['name'],
            morph['confidence'],
            morph['provenance'],
            json.dumps(morph['metadata'])
        ))
        inserted += 1
    except sqlite3.IntegrityError as e:
        # Already exists
        skipped += 1

conn.commit()
conn.close()

print('')
print('Import complete:')
print(f'  Inserted: {inserted}')
print(f'  Skipped:  {skipped}')
print(f'  Total:    {inserted + skipped}')

# Verify
conn = sqlite3.connect(str(db_path))
cur = conn.cursor()
cur.execute('SELECT COUNT(*) FROM morphisms')
total = cur.fetchone()[0]
conn.close()
print('')
print(f'tier1.db now contains: {total} total edges')
