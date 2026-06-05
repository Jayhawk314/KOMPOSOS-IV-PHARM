
import json, sqlite3, uuid
from pathlib import Path

db_path = Path('data/drugs/tier1.db')
pubmed_path = Path('data/new_edges_pubmed.json')

with open(pubmed_path) as f:
    edges = json.load(f)

print(f'Importing {len(edges)} PubMed edges...')

conn = sqlite3.connect(str(db_path))
cur = conn.cursor()

inserted = 0
for e in edges:
    mid = f"associated_with:{e['source']}->{e['target']}"
    try:
        cur.execute('''
            INSERT INTO morphisms 
            (id, name, source_name, target_name, confidence, provenance, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            mid, 'associated_with', e['source'], e['target'],
            0.65, e['provenance'], json.dumps({'evidence_type': 'batch_extraction'})
        ))
        inserted += 1
    except sqlite3.IntegrityError:
        pass

conn.commit()
conn.close()
print(f'Inserted {inserted} edges.')
